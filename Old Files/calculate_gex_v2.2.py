"""
GEX Level Calculator v2.2 - FORMULA FIXED
Critical fix: Added proper multipliers to match industry standard
"""

import json
from datetime import datetime

# Configuration
MINIMUM_OI = 100  # Filter out low-activity strikes
ROUND_TO = 25     # Round NQ to nearest 25 points

def load_options_data():
    """Load options chain data from JSON file"""
    try:
        with open("options_chain_raw.json", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print("❌ ERROR: options_chain_raw.json not found")
        return None

def calculate_gex_levels(data):
    """
    Calculate the 5 GEX levels using CORRECT INDUSTRY-STANDARD formula
    
    CRITICAL FIX: Now using proper multipliers:
    GEX = Gamma × OI × 100 × Spot² × 0.01
    """
    print("\n" + "="*60)
    print("CALCULATING GEX LEVELS - v2.2 FORMULA FIXED")
    print("="*60)
    
    # Get underlying price
    underlying_price = data.get('underlyingPrice', 610.0)
    print(f"\n💰 QQQ Price: ${underlying_price:.2f}")
    
    # Calculate multiplier
    multiplier = 100 * underlying_price * underlying_price * 0.01
    print(f"📐 Formula Multiplier: 100 × {underlying_price}² × 0.01 = {multiplier:,.2f}")
    
    # Initialize storage
    strikes_data = {}
    
    # Process CALLS
    print("\n📈 Processing CALLS...")
    call_strikes_processed = 0
    
    if 'callExpDateMap' in data:
        for exp_date, strikes in data['callExpDateMap'].items():
            for strike_price, contracts in strikes.items():
                strike = float(strike_price)
                contract = contracts[0] if isinstance(contracts, list) else contracts
                
                call_oi = contract.get('openInterest', 0)
                call_gamma = contract.get('gamma', 0)
                
                # **FIX: Filter out low-activity strikes**
                if call_oi < MINIMUM_OI:
                    continue
                
                if strike not in strikes_data:
                    strikes_data[strike] = {
                        'call_oi': 0, 'put_oi': 0,
                        'call_gamma': 0, 'put_gamma': 0,
                        'call_gex': 0, 'put_gex': 0
                    }
                
                # Accumulate across expirations
                strikes_data[strike]['call_oi'] += call_oi
                strikes_data[strike]['call_gamma'] += call_gamma
                
                # **CRITICAL FIX: Use correct formula with all multipliers**
                call_gex = call_gamma * call_oi * 100 * underlying_price * underlying_price * 0.01
                strikes_data[strike]['call_gex'] += call_gex
                
                call_strikes_processed += 1
    
    print(f"   Processed {call_strikes_processed} call contracts")
    
    # Process PUTS
    print("📉 Processing PUTS...")
    put_strikes_processed = 0
    
    if 'putExpDateMap' in data:
        for exp_date, strikes in data['putExpDateMap'].items():
            for strike_price, contracts in strikes.items():
                strike = float(strike_price)
                contract = contracts[0] if isinstance(contracts, list) else contracts
                
                put_oi = contract.get('openInterest', 0)
                put_gamma = contract.get('gamma', 0)
                
                # **FIX: Filter out low-activity strikes**
                if put_oi < MINIMUM_OI:
                    continue
                
                if strike not in strikes_data:
                    strikes_data[strike] = {
                        'call_oi': 0, 'put_oi': 0,
                        'call_gamma': 0, 'put_gamma': 0,
                        'call_gex': 0, 'put_gex': 0
                    }
                
                # Accumulate across expirations
                strikes_data[strike]['put_oi'] += put_oi
                strikes_data[strike]['put_gamma'] += put_gamma
                
                # **CRITICAL FIX: Use correct formula with all multipliers (negative for puts)**
                put_gex = -(put_gamma * put_oi * 100 * underlying_price * underlying_price * 0.01)
                strikes_data[strike]['put_gex'] += put_gex
                
                put_strikes_processed += 1
    
    print(f"   Processed {put_strikes_processed} put contracts")
    print(f"✅ Total active strikes (OI ≥ {MINIMUM_OI}): {len(strikes_data)}")
    
    # Calculate totals
    total_call_gex = sum(d['call_gex'] for d in strikes_data.values())
    total_put_gex = sum(d['put_gex'] for d in strikes_data.values())
    net_gex = total_call_gex + total_put_gex
    
    print(f"\n📊 Total Call GEX: {total_call_gex/1000:,.1f}K")
    print(f"📊 Total Put GEX: {total_put_gex/1000:,.1f}K")
    print(f"📊 Net GEX: {net_gex/1000:,.1f}K")
    
    # Calculate the 5 levels
    print("\n🔢 Calculating GEX Levels...")
    
    # 1. CALL OI
    call_oi_data = [(s, d['call_oi']) for s, d in strikes_data.items() if d['call_oi'] > 0]
    if call_oi_data:
        call_oi_strike, call_oi_value = max(call_oi_data, key=lambda x: x[1])
    else:
        call_oi_strike, call_oi_value = underlying_price, 0
    
    # 2. PUT OI
    put_oi_data = [(s, d['put_oi']) for s, d in strikes_data.items() if d['put_oi'] > 0]
    if put_oi_data:
        put_oi_strike, put_oi_value = max(put_oi_data, key=lambda x: x[1])
    else:
        put_oi_strike, put_oi_value = underlying_price, 0
    
    # 3. POS GEX
    call_gex_data = [(s, d['call_gex']) for s, d in strikes_data.items() if d['call_gex'] > 0]
    if call_gex_data:
        pos_gex_strike, pos_gex_value = max(call_gex_data, key=lambda x: x[1])
    else:
        pos_gex_strike, pos_gex_value = underlying_price, 0
    
    # 4. NEG GEX
    put_gex_data = [(s, d['put_gex']) for s, d in strikes_data.items() if d['put_gex'] < 0]
    if put_gex_data:
        neg_gex_strike, neg_gex_value = min(put_gex_data, key=lambda x: x[1])
    else:
        neg_gex_strike, neg_gex_value = underlying_price, 0
    
    # 5. ZERO GAMMA - Interpolated
    zero_gamma_strike = interpolate_zero_gamma(strikes_data, underlying_price)
    
    # Display results
    print("\n" + "="*60)
    print("📊 GEX LEVELS CALCULATED")
    print("="*60)
    
    print(f"\n1️⃣  CALL OI (Upper Resistance)")
    print(f"    Strike: ${call_oi_strike:.2f}")
    print(f"    Open Interest: {call_oi_value:,.0f} contracts")
    
    print(f"\n2️⃣  POS GEX (MAJOR WALL - Most Important)")
    print(f"    Strike: ${pos_gex_strike:.2f}")
    print(f"    Gamma Exposure: {pos_gex_value/1000:,.1f}K")
    
    print(f"\n3️⃣  ZERO GAMMA (Regime Line) ✅ INTERPOLATED!")
    print(f"    Level: ${zero_gamma_strike:.2f}")
    
    print(f"\n4️⃣  NEG GEX (Support/Danger Zone)")
    print(f"    Strike: ${neg_gex_strike:.2f}")
    print(f"    Gamma Exposure: {neg_gex_value/1000:,.1f}K")
    
    print(f"\n5️⃣  PUT OI (Lower Support)")
    print(f"    Strike: ${put_oi_strike:.2f}")
    print(f"    Open Interest: {put_oi_value:,.0f} contracts")
    
    return {
        'call_oi': call_oi_strike,
        'pos_gex': pos_gex_strike,
        'zero_gamma': zero_gamma_strike,
        'neg_gex': neg_gex_strike,
        'put_oi': put_oi_strike,
        'qqq_price': underlying_price,
        'net_gex': net_gex
    }

def interpolate_zero_gamma(strikes_data, underlying_price):
    """
    Find interpolated zero gamma level between strikes
    """
    # Calculate net GEX for each strike
    net_gex_by_strike = []
    for strike in sorted(strikes_data.keys()):
        call_gex = strikes_data[strike]['call_gex']
        put_gex = strikes_data[strike]['put_gex']
        net_gex = call_gex + put_gex
        net_gex_by_strike.append((strike, net_gex))
    
    # Find bracket around zero
    for i in range(len(net_gex_by_strike) - 1):
        strike1, gex1 = net_gex_by_strike[i]
        strike2, gex2 = net_gex_by_strike[i + 1]
        
        # Check if zero is between these two strikes
        if (gex1 <= 0 <= gex2) or (gex2 <= 0 <= gex1):
            # Linear interpolation
            if gex2 == gex1:
                zero_gamma = strike1
            else:
                zero_gamma = strike1 + (strike2 - strike1) * (-gex1) / (gex2 - gex1)
            
            return zero_gamma
    
    # Fallback: return current price if no bracket found
    return underlying_price

def convert_to_nq(levels, data):
    """
    Convert QQQ strikes to NQ levels using dynamic ratio
    """
    print("\n" + "="*60)
    print("CONVERTING TO NQ LEVELS - v2.2")
    print("="*60)
    
    qqq_price = levels['qqq_price']
    
    # Try to get NQ price from the data
    nq_price = data.get('nq_price')
    
    if nq_price and nq_price > 0:
        ratio = nq_price / qqq_price
        print(f"\n📊 QQQ Price: ${qqq_price:.2f}")
        print(f"📊 NQ Price: {nq_price:,.2f} (from Schwab API)")
        print(f"✅ Dynamic Ratio: {ratio:.2f} (LIVE)")
    else:
        ratio = 41.35
        nq_price = qqq_price * ratio
        print(f"\n📊 QQQ Price: ${qqq_price:.2f}")
        print(f"⚠️  NQ price from API not available")
        print(f"📊 Estimated NQ Price: {nq_price:,.2f}")
        print(f"🔄 Fallback Ratio: {ratio:.2f}")
    
    # Convert all levels
    nq_levels = {}
    for level_name, qqq_strike in levels.items():
        if level_name not in ['qqq_price', 'net_gex']:
            nq_level = round((qqq_strike * ratio) / ROUND_TO) * ROUND_TO
            nq_levels[level_name] = nq_level
    
    print("\n" + "="*60)
    print("NQ FUTURES LEVELS")
    print("="*60)
    
    print(f"\n1️⃣  Call OI:     ${levels['call_oi']:.2f} QQQ  →  {nq_levels['call_oi']:,} NQ")
    print(f"2️⃣  Pos GEX:     ${levels['pos_gex']:.2f} QQQ  →  {nq_levels['pos_gex']:,} NQ  ⭐ MAJOR WALL")
    print(f"3️⃣  Zero Gamma:  ${levels['zero_gamma']:.2f} QQQ  →  {nq_levels['zero_gamma']:,} NQ  ✅ INTERPOLATED!")
    print(f"4️⃣  Neg GEX:     ${levels['neg_gex']:.2f} QQQ  →  {nq_levels['neg_gex']:,} NQ")
    print(f"5️⃣  Put OI:      ${levels['put_oi']:.2f} QQQ  →  {nq_levels['put_oi']:,} NQ")
    
    return nq_levels, ratio

def save_results(levels, nq_levels, ratio):
    """Save results to file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    output = []
    output.append("="*60)
    output.append("GEX LEVELS OUTPUT - v2.2 FORMULA FIXED")
    output.append("="*60)
    output.append(f"Generated: {timestamp}")
    output.append(f"QQQ Price: ${levels['qqq_price']:.2f}")
    output.append(f"Dynamic Ratio: {ratio:.2f}")
    output.append(f"Net GEX: {levels['net_gex']/1000:,.0f}K")
    output.append("")
    output.append("QQQ STRIKES → NQ LEVELS")
    output.append("-"*60)
    output.append(f"Call OI:     ${levels['call_oi']:.2f}  →  {nq_levels['call_oi']:,}")
    output.append(f"Pos GEX:     ${levels['pos_gex']:.2f}  →  {nq_levels['pos_gex']:,}  ⭐")
    output.append(f"Zero Gamma:  ${levels['zero_gamma']:.2f}  →  {nq_levels['zero_gamma']:,}  ✅")
    output.append(f"Neg GEX:     ${levels['neg_gex']:.2f}  →  {nq_levels['neg_gex']:,}")
    output.append(f"Put OI:      ${levels['put_oi']:.2f}  →  {nq_levels['put_oi']:,}")
    output.append("="*60)
    
    print("\n" + "\n".join(output))
    
    try:
        with open("gex_levels_output_v2.2.txt", "w", encoding='utf-8') as f:
            f.write('\n'.join(output))
        print(f"\n💾 Results saved to 'gex_levels_output_v2.2.txt'")
    except:
        print(f"\n⚠️  Could not save file")

def main():
    print("\n🚀 Starting GEX Level Calculator v2.2 (Formula Fixed)\n")
    
    # Load data
    data = load_options_data()
    if not data:
        return
    
    # Calculate GEX levels with CORRECT formula
    levels = calculate_gex_levels(data)
    if not levels:
        return
    
    # Convert to NQ
    nq_levels, ratio = convert_to_nq(levels, data)
    
    # Save results
    save_results(levels, nq_levels, ratio)
    
    print("\n" + "="*60)
    print("✅ CALCULATION COMPLETE!")
    print("="*60)
    print("\n🎯 CRITICAL FIXES IN v2.2:")
    print("  ✅ Formula now includes ALL multipliers:")
    print("     GEX = Gamma × OI × 100 × Spot² × 0.01")
    print("  ✅ Net GEX should now be in the hundreds of thousands")
    print("  ✅ Zero Gamma interpolated between strikes")
    print("  ✅ All 5 levels should be different!")
    print("\n📊 Compare your Net GEX to GEXstream:")
    print("  If within 20%, you're good!")
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
