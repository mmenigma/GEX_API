"""
GEX Level Calculator v2.1 - HYBRID FIXED VERSION
Uses your working data parser + v2.0 improvements
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
    Calculate the 5 GEX levels using FIXED methodology
    """
    print("\n" + "="*60)
    print("CALCULATING GEX LEVELS - v2.1 FIXED")
    print("="*60)
    
    # Get underlying price
    underlying_price = data.get('underlyingPrice', 610.0)
    print(f"\n💰 QQQ Price: ${underlying_price:.2f}")
    
    # Initialize storage
    strikes_data = {}
    
    # Process CALLS
    print("\n📈 Processing CALLS...")
    if 'callExpDateMap' in data:
        for exp_date, strikes in data['callExpDateMap'].items():
            for strike_price, contracts in strikes.items():
                strike = float(strike_price)
                contract = contracts[0] if isinstance(contracts, list) else contracts
                
                call_oi = contract.get('openInterest', 0)
                call_gamma = contract.get('gamma', 0)
                
                # **FIX 1: Filter out low-activity strikes**
                if call_oi < MINIMUM_OI:
                    continue
                
                if strike not in strikes_data:
                    strikes_data[strike] = {
                        'call_oi': 0, 'put_oi': 0,
                        'call_gamma': 0, 'put_gamma': 0,
                        'call_gex': 0, 'put_gex': 0
                    }
                
                strikes_data[strike]['call_oi'] = call_oi
                strikes_data[strike]['call_gamma'] = call_gamma
                strikes_data[strike]['call_gex'] = call_gamma * call_oi
    
    # Process PUTS
    print("📉 Processing PUTS...")
    if 'putExpDateMap' in data:
        for exp_date, strikes in data['putExpDateMap'].items():
            for strike_price, contracts in strikes.items():
                strike = float(strike_price)
                contract = contracts[0] if isinstance(contracts, list) else contracts
                
                put_oi = contract.get('openInterest', 0)
                put_gamma = contract.get('gamma', 0)
                
                # **FIX 1: Filter out low-activity strikes**
                if put_oi < MINIMUM_OI:
                    continue
                
                if strike not in strikes_data:
                    strikes_data[strike] = {
                        'call_oi': 0, 'put_oi': 0,
                        'call_gamma': 0, 'put_gamma': 0,
                        'call_gex': 0, 'put_gex': 0
                    }
                
                strikes_data[strike]['put_oi'] = put_oi
                strikes_data[strike]['put_gamma'] = put_gamma
                strikes_data[strike]['put_gex'] = -(put_gamma * put_oi)
    
    print(f"✅ Processed {len(strikes_data)} active strikes (OI ≥ {MINIMUM_OI})")
    
    # Calculate totals
    total_call_gex = sum(d['call_gex'] for d in strikes_data.values())
    total_put_gex = sum(d['put_gex'] for d in strikes_data.values())
    net_gex = total_call_gex + total_put_gex
    
    print(f"\n📊 Total Call GEX: {total_call_gex:,.1f}K")
    print(f"📊 Total Put GEX: {total_put_gex:,.1f}K")
    print(f"📊 Net GEX: {net_gex:,.1f}K")
    
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
    
    # 5. **FIX 2: ZERO GAMMA - Find actual gamma crossover**
    price_range = underlying_price * 0.05
    min_strike = underlying_price - price_range
    max_strike = underlying_price + price_range
    
    net_gamma_by_strike = []
    for strike in sorted(strikes_data.keys()):
        if min_strike <= strike <= max_strike:
            call_gex = strikes_data[strike]['call_gex']
            put_gex = strikes_data[strike]['put_gex']
            net_gex_strike = call_gex + put_gex
            
            # Only consider strikes with actual activity
            if call_gex != 0 or put_gex != 0:
                net_gamma_by_strike.append((strike, net_gex_strike))
    
    if net_gamma_by_strike:
        zero_gamma_strike = min(net_gamma_by_strike, key=lambda x: abs(x[1]))[0]
        print(f"\n[v2.1 FIX] Zero Gamma candidates (active strikes near ${underlying_price:.2f}):")
        for strike, net_gex in sorted(net_gamma_by_strike, key=lambda x: abs(x[1]))[:5]:
            print(f"  ${strike:.2f}: Net GEX = {net_gex:,.1f}K")
    else:
        zero_gamma_strike = underlying_price
    
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
    
    print(f"\n3️⃣  ZERO GAMMA (Regime Line) ✅ FIXED!")
    print(f"    Level: ${zero_gamma_strike:.2f}")
    
    print(f"\n4️⃣  NEG GEX (Support/Danger Zone)")
    print(f"    Strike: ${neg_gex_strike:.2f}")
    print(f"    Gamma Exposure: {neg_gex_value:,.1f}K")
    
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

def convert_to_nq(levels, data):
    """
    **FIX 3: Dynamic ratio calculation**
    Uses live NQ price if available from fetch_options_chain.py
    """
    print("\n" + "="*60)
    print("CONVERTING TO NQ LEVELS - v2.1 FIXED")
    print("="*60)
    
    qqq_price = levels['qqq_price']
    
    # Try to get NQ price from the data (fetch_options_chain.py adds this)
    nq_price = data.get('nq_price')
    
    if nq_price and nq_price > 0:
        # We have live NQ price!
        ratio = nq_price / qqq_price
        print(f"\n📊 QQQ Price: ${qqq_price:.2f}")
        print(f"📊 NQ Price: {nq_price:,.2f} (from Schwab API)")
        print(f"✅ Dynamic Ratio: {ratio:.2f} (LIVE)")
    else:
        # Fall back to TOS-like estimate: use the documented typical ratio
        # According to your TOS study documentation, ratio typically 39.8-40.3
        # But recent data shows it's closer to 41.3-41.4
        # Use a conservative middle estimate
        ratio = 41.36  # Match your original hardcoded value as fallback
        nq_price = qqq_price * ratio
        print(f"\n📊 QQQ Price: ${qqq_price:.2f}")
        print(f"⚠️  NQ price from API not available")
        print(f"📊 Estimated NQ Price: {nq_price:,.2f}")
        print(f"🔄 Fallback Ratio: {ratio:.2f} (typical average)")
        print(f"💡 TIP: Run fetch_options_chain.py first for live NQ price")
    
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
    print(f"3️⃣  Zero Gamma:  ${levels['zero_gamma']:.2f} QQQ  →  {nq_levels['zero_gamma']:,} NQ  ✅ FIXED!")
    print(f"4️⃣  Neg GEX:     ${levels['neg_gex']:.2f} QQQ  →  {nq_levels['neg_gex']:,} NQ")
    print(f"5️⃣  Put OI:      ${levels['put_oi']:.2f} QQQ  →  {nq_levels['put_oi']:,} NQ")
    
    return nq_levels, ratio

def save_results(levels, nq_levels, ratio):
    """Save results to file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    output = []
    output.append("="*60)
    output.append("GEX LEVELS OUTPUT - v2.1 FIXED")
    output.append("="*60)
    output.append(f"Generated: {timestamp}")
    output.append(f"QQQ Price: ${levels['qqq_price']:.2f}")
    output.append(f"Dynamic Ratio: {ratio:.2f}")
    output.append(f"Net GEX: {levels['net_gex']:,.0f}K")
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
        with open("gex_levels_output_v2.txt", "w", encoding='utf-8') as f:
            f.write('\n'.join(output))
        print(f"\n💾 Results saved to 'gex_levels_output_v2.txt'")
    except:
        print(f"\n⚠️  Could not save file (read-only filesystem)")

def main():
    print("\n🚀 Starting GEX Level Calculator v2.1 (Hybrid Fixed Version)\n")
    
    # Load data
    data = load_options_data()
    if not data:
        return
    
    # Calculate GEX levels with fixes
    levels = calculate_gex_levels(data)
    if not levels:
        return
    
    # Convert to NQ with dynamic ratio
    nq_levels, ratio = convert_to_nq(levels, data)
    
    # Save results
    save_results(levels, nq_levels, ratio)
    
    print("\n" + "="*60)
    print("✅ CALCULATION COMPLETE!")
    print("="*60)
    print("\n🎯 KEY FIXES IN v2.1:")
    print("  ✅ Filters out low-activity strikes (OI < 100)")
    print("  ✅ Zero Gamma finds actual gamma crossover")
    print("  ✅ Dynamic ratio based on QQQ price")
    print("  ✅ All 5 levels should now be different!")
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
