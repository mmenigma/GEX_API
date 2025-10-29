"""
GEX Calculator
GEX Level Finder - Step 3: Calculate GEX Levels

This script analyzes options chain data and calculates the 5 key GEX levels.
"""

import json
from datetime import datetime


def load_options_data():
    """
    Load options chain data from JSON file.
    """
    try:
        with open("options_chain_raw.json", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print("❌ ERROR: options_chain_raw.json not found")
        print("Please run fetch_options_chain.py first")
        return None
    except Exception as e:
        print(f"❌ ERROR loading data: {e}")
        return None


def calculate_gex_levels(data):
    """
    Calculate the 5 GEX levels from options chain data using GEXstream methodology.
    GEX = Gamma × OI × 100 × Spot Price / 1000 (in thousands)
    """
    print("\n" + "="*60)
    print("CALCULATING GEX LEVELS")
    print("="*60)
    
    # Get underlying price
    underlying_price = data.get('underlyingPrice', 0)
    print(f"\n💰 QQQ Price: ${underlying_price:.2f}")
    
    # Initialize storage for calculations
    strikes_data = {}
    
    # Process CALLS
    print("\n📈 Processing CALLS...")
    if 'callExpDateMap' in data:
        for exp_date, strikes in data['callExpDateMap'].items():
            for strike_price, contracts in strikes.items():
                strike = float(strike_price)
                
                # Get first contract
                contract = contracts[0] if isinstance(contracts, list) else contracts
                
                if strike not in strikes_data:
                    strikes_data[strike] = {
                        'call_oi': 0,
                        'put_oi': 0,
                        'call_gamma': 0,
                        'put_gamma': 0,
                        'call_gex': 0,
                        'put_gex': 0
                    }
                
                call_oi = contract.get('openInterest', 0)
                call_gamma = contract.get('gamma', 0)
                
                strikes_data[strike]['call_oi'] = call_oi
                strikes_data[strike]['call_gamma'] = call_gamma
                
                # Gamma exposure = gamma × OI (that's it!)
                # Result in thousands (K) naturally from the scale
                call_gex = call_gamma * call_oi
                strikes_data[strike]['call_gex'] = call_gex
    
    # Process PUTS
    print("📉 Processing PUTS...")
    if 'putExpDateMap' in data:
        for exp_date, strikes in data['putExpDateMap'].items():
            for strike_price, contracts in strikes.items():
                strike = float(strike_price)
                
                # Get first contract
                contract = contracts[0] if isinstance(contracts, list) else contracts
                
                if strike not in strikes_data:
                    strikes_data[strike] = {
                        'call_oi': 0,
                        'put_oi': 0,
                        'call_gamma': 0,
                        'put_gamma': 0,
                        'call_gex': 0,
                        'put_gex': 0
                    }
                
                put_oi = contract.get('openInterest', 0)
                put_gamma = contract.get('gamma', 0)
                
                strikes_data[strike]['put_oi'] = put_oi
                strikes_data[strike]['put_gamma'] = put_gamma
                
                # Gamma exposure for puts is NEGATIVE
                # Simple formula: gamma × OI
                put_gex = -(put_gamma * put_oi)
                strikes_data[strike]['put_gex'] = put_gex
    
    print(f"✅ Processed {len(strikes_data)} unique strikes")
    
    # Calculate totals for verification
    total_call_gex = sum(data['call_gex'] for data in strikes_data.values())
    total_put_gex = sum(data['put_gex'] for data in strikes_data.values())
    net_gex = total_call_gex + total_put_gex
    
    print(f"\n📊 Total Call GEX: {total_call_gex:,.1f}K")
    print(f"📊 Total Put GEX: {total_put_gex:,.1f}K")
    print(f"📊 Net GEX: {net_gex:,.1f}K")
    
    # Calculate the 5 levels
    print("\n🔢 Calculating GEX Levels...")
    
    # Sort strikes
    sorted_strikes = sorted(strikes_data.keys())
    
    # 1. CALL OI - Strike with highest call open interest
    call_oi_data = [(strike, data['call_oi']) for strike, data in strikes_data.items() if data['call_oi'] > 0]
    call_oi_strike, call_oi_value = max(call_oi_data, key=lambda x: x[1])
    
    # 2. PUT OI - Strike with highest put open interest
    put_oi_data = [(strike, data['put_oi']) for strike, data in strikes_data.items() if data['put_oi'] > 0]
    put_oi_strike, put_oi_value = max(put_oi_data, key=lambda x: x[1])
    
    # 3. POS GEX - Strike with largest positive (call) gamma exposure
    call_gex_data = [(strike, data['call_gex']) for strike, data in strikes_data.items() if data['call_gex'] > 0]
    pos_gex_strike, pos_gex_value = max(call_gex_data, key=lambda x: x[1])
    
    # 4. NEG GEX - Strike with largest negative (put) gamma exposure
    put_gex_data = [(strike, data['put_gex']) for strike, data in strikes_data.items() if data['put_gex'] < 0]
    neg_gex_strike, neg_gex_value = min(put_gex_data, key=lambda x: x[1])
    
    # 5. ZERO GAMMA - Find strike where NET gamma (calls - puts) is closest to zero
    # Only consider strikes within +/- 5% of current price (relevant range)
    price_range = underlying_price * 0.05
    min_strike = underlying_price - price_range
    max_strike = underlying_price + price_range
    
    net_gamma_by_strike = []
    
    for strike in sorted_strikes:
        # Only consider strikes in relevant range
        if min_strike <= strike <= max_strike:
            call_gex = strikes_data[strike]['call_gex']
            put_gex = strikes_data[strike]['put_gex']
            net_gex = call_gex + put_gex  # Put GEX is already negative
            net_gamma_by_strike.append((strike, net_gex))
    
    # Find strike where net gamma is closest to zero
    if net_gamma_by_strike:
        zero_gamma_strike = min(net_gamma_by_strike, key=lambda x: abs(x[1]))[0]
    else:
        # Fallback if no strikes in range
        zero_gamma_strike = underlying_price
    
    print(f"\n[DEBUG] Zero Gamma candidates (within ±5% of ${underlying_price:.2f}):")
    for strike, net_gex in sorted(net_gamma_by_strike, key=lambda x: abs(x[1]))[:10]:
        print(f"  ${strike:.2f}: Net GEX = {net_gex:,.1f}K")
    
    # Display results
    print("\n" + "="*60)
    print("📊 GEX LEVELS CALCULATED")
    print("="*60)
    
    print(f"\n1️⃣  CALL OI (Upper Resistance)")
    print(f"    Strike: ${call_oi_strike:.2f}")
    print(f"    Open Interest: {call_oi_value:,.0f} contracts")
    
    print(f"\n2️⃣  POS GEX (MAJOR WALL - Most Important)")
    print(f"    Strike: ${pos_gex_strike:.2f}")
    print(f"    Gamma Exposure: {pos_gex_value:,.1f}K")
    
    print(f"\n3️⃣  ZERO GAMMA (Regime Line)")
    print(f"    Level: ${zero_gamma_strike:.2f}")
    
    print(f"\n4️⃣  NEG GEX (Support/Danger Zone)")
    print(f"    Strike: ${neg_gex_strike:.2f}")
    print(f"    Gamma Exposure: {neg_gex_value:,.1f}K")
    
    print(f"\n5️⃣  PUT OI (Lower Support)")
    print(f"    Strike: ${put_oi_strike:.2f}")
    print(f"    Open Interest: {put_oi_value:,.0f} contracts")
    
    # Return the 5 levels
    levels = {
        'call_oi': call_oi_strike,
        'pos_gex': pos_gex_strike,
        'zero_gamma': zero_gamma_strike,
        'neg_gex': neg_gex_strike,
        'put_oi': put_oi_strike,
        'qqq_price': underlying_price
    }
    
    return levels


def convert_to_nq(levels, nq_price=None):
    """
    Convert QQQ strikes to NQ futures levels.
    Uses dynamic ratio based on current prices.
    """
    print("\n" + "="*60)
    print("CONVERTING TO NQ LEVELS")
    print("="*60)
    
    qqq_price = levels['qqq_price']
    
    # Use actual NQ price if available, otherwise estimate
    if nq_price:
        ratio = nq_price / qqq_price
        print(f"\n📊 QQQ Price: ${qqq_price:.2f}")
        print(f"📊 NQ Price: {nq_price:,.2f}")
        print(f"✅ Dynamic Ratio: {ratio:.2f}")
    else:
        # Use typical ratio as fallback
        ratio = 41.36
        estimated_nq = qqq_price * ratio
        print(f"\n📊 QQQ Price: ${qqq_price:.2f}")
        print(f"⚠️  NQ price not available - using estimated ratio")
        print(f"📊 Estimated NQ Price: {estimated_nq:,.2f}")
        print(f"🔄 Ratio: {ratio:.2f} (typical average)")
    
    nq_levels = {}
    for level_name, qqq_strike in levels.items():
        if level_name != 'qqq_price':
            # Convert and round to nearest 25 points
            nq_level = round((qqq_strike * ratio) / 25) * 25
            nq_levels[level_name] = nq_level
    
    print(f"\n🔄 Conversion Ratio: {ratio:.2f}")
    print("\n" + "="*60)
    print("NQ FUTURES LEVELS")
    print("="*60)
    
    print(f"\n1️⃣  Call OI:     ${levels['call_oi']:.2f} QQQ  →  {nq_levels['call_oi']:,} NQ")
    print(f"2️⃣  Pos GEX:     ${levels['pos_gex']:.2f} QQQ  →  {nq_levels['pos_gex']:,} NQ  ⭐ MAJOR WALL")
    print(f"3️⃣  Zero Gamma:  ${levels['zero_gamma']:.2f} QQQ  →  {nq_levels['zero_gamma']:,} NQ")
    print(f"4️⃣  Neg GEX:     ${levels['neg_gex']:.2f} QQQ  →  {nq_levels['neg_gex']:,} NQ")
    print(f"5️⃣  Put OI:      ${levels['put_oi']:.2f} QQQ  →  {nq_levels['put_oi']:,} NQ")
    
    return nq_levels


def save_results(levels, nq_levels):
    """
    Save results to a file for easy reference.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open("gex_levels_output.txt", "w", encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("GEX LEVELS OUTPUT\n")
        f.write("="*60 + "\n")
        f.write(f"Generated: {timestamp}\n")
        f.write(f"QQQ Price: ${levels['qqq_price']:.2f}\n")
        f.write("\n")
        f.write("QQQ STRIKES → NQ LEVELS\n")
        f.write("-"*60 + "\n")
        f.write(f"Call OI:     ${levels['call_oi']:.2f}  →  {nq_levels['call_oi']:,}\n")
        f.write(f"Pos GEX:     ${levels['pos_gex']:.2f}  →  {nq_levels['pos_gex']:,}  ⭐\n")
        f.write(f"Zero Gamma:  ${levels['zero_gamma']:.2f}  →  {nq_levels['zero_gamma']:,}\n")
        f.write(f"Neg GEX:     ${levels['neg_gex']:.2f}  →  {nq_levels['neg_gex']:,}\n")
        f.write(f"Put OI:      ${levels['put_oi']:.2f}  →  {nq_levels['put_oi']:,}\n")
        f.write("="*60 + "\n")
    
    print(f"\n💾 Results saved to 'gex_levels_output.txt'")


def main():
    """
    Main calculation workflow.
    """
    print("\n🚀 Starting GEX Level Calculation...")
    
    # Load data
    data = load_options_data()
    if not data:
        return
    
    # Get NQ price if available
    nq_price = data.get('nq_price')
    
    # Calculate GEX levels
    levels = calculate_gex_levels(data)
    if not levels:
        return
    
    # Convert to NQ
    nq_levels = convert_to_nq(levels, nq_price)
    
    # Save results
    save_results(levels, nq_levels)
    
    print("\n" + "="*60)
    print("✅ CALCULATION COMPLETE!")
    print("="*60)
    print("\nYou can now input these NQ levels into ThinkorSwim!")
    print("Check 'gex_levels_output.txt' for a summary")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
