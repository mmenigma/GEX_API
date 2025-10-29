"""
GEX Levels Comparison Tool
Compare your calculated levels against GEXstream values
"""

def compare_levels():
    """
    Interactive comparison tool for validating your GEX levels against GEXstream.
    """
    print("\n" + "="*70)
    print("GEX LEVELS COMPARISON TOOL")
    print("="*70)
    print("\nThis tool helps you compare your calculated levels with GEXstream.")
    print("\nInstructions:")
    print("1. Run calculate_gex_v2.3.py first")
    print("2. Open GEXstream.com and note the 5 levels")
    print("3. Enter the GEXstream values below for comparison")
    print("\n" + "="*70)
    
    # Load your calculated results
    try:
        with open("gex_levels_output_v2.3.txt", "r") as f:
            content = f.read()
        print("\n✅ Loaded your v2.3 results")
        print("\n" + "-"*70)
        print(content)
        print("-"*70)
    except FileNotFoundError:
        print("\n⚠️  gex_levels_output_v2.3.txt not found")
        print("Please run calculate_gex_v2.3.py first")
        return
    
    # Parse your results from the file
    your_levels = {}
    for line in content.split('\n'):
        if 'Call OI:' in line and '→' in line:
            parts = line.split('→')
            qqq_val = parts[0].split('$')[1].split()[0]
            nq_val = parts[1].strip().replace(',', '')
            your_levels['call_oi'] = {'qqq': float(qqq_val), 'nq': int(nq_val)}
        elif 'Pos GEX:' in line and '→' in line:
            parts = line.split('→')
            qqq_val = parts[0].split('$')[1].split()[0]
            nq_val = parts[1].split()[0].replace(',', '')
            your_levels['pos_gex'] = {'qqq': float(qqq_val), 'nq': int(nq_val)}
        elif 'Zero Gamma:' in line and '→' in line:
            parts = line.split('→')
            qqq_val = parts[0].split('$')[1].split()[0]
            nq_val = parts[1].split()[0].replace(',', '')
            your_levels['zero_gamma'] = {'qqq': float(qqq_val), 'nq': int(nq_val)}
        elif 'Neg GEX:' in line and '→' in line:
            parts = line.split('→')
            qqq_val = parts[0].split('$')[1].split()[0]
            nq_val = parts[1].strip().replace(',', '')
            your_levels['neg_gex'] = {'qqq': float(qqq_val), 'nq': int(nq_val)}
        elif 'Put OI:' in line and '→' in line:
            parts = line.split('→')
            qqq_val = parts[0].split('$')[1].split()[0]
            nq_val = parts[1].strip().replace(',', '')
            your_levels['put_oi'] = {'qqq': float(qqq_val), 'nq': int(nq_val)}
        elif 'Net GEX:' in line:
            your_levels['net_gex'] = line.split(':')[1].strip()
    
    # Get GEXstream values from user
    print("\n" + "="*70)
    print("ENTER GEXSTREAM VALUES")
    print("="*70)
    print("\nGo to GEXstream.com and enter the 5 QQQ levels you see:")
    print("(Press Enter to skip any level you don't want to compare)")
    
    gex_levels = {}
    
    # Call OI
    val = input("\n1. Call OI (QQQ price): $").strip()
    if val:
        try:
            gex_levels['call_oi'] = float(val)
        except:
            pass
    
    # Pos GEX
    val = input("2. Pos GEX (QQQ price): $").strip()
    if val:
        try:
            gex_levels['pos_gex'] = float(val)
        except:
            pass
    
    # Zero Gamma
    val = input("3. Zero Gamma (QQQ price): $").strip()
    if val:
        try:
            gex_levels['zero_gamma'] = float(val)
        except:
            pass
    
    # Neg GEX
    val = input("4. Neg GEX (QQQ price): $").strip()
    if val:
        try:
            gex_levels['neg_gex'] = float(val)
        except:
            pass
    
    # Put OI
    val = input("5. Put OI (QQQ price): $").strip()
    if val:
        try:
            gex_levels['put_oi'] = float(val)
        except:
            pass
    
    # Net GEX
    val = input("\n6. Net GEX (value from GEXstream): ").strip()
    if val:
        gex_levels['net_gex'] = val
    
    # Display comparison
    print("\n" + "="*70)
    print("COMPARISON RESULTS")
    print("="*70)
    
    level_names = {
        'call_oi': 'Call OI',
        'pos_gex': 'Pos GEX',
        'zero_gamma': 'Zero Gamma',
        'neg_gex': 'Neg GEX',
        'put_oi': 'Put OI'
    }
    
    print("\n{:<15} {:<12} {:<12} {:<12} {:<12}".format(
        "Level", "Your QQQ", "GEX QQQ", "Diff (QQQ)", "Diff (NQ pts)"))
    print("-"*70)
    
    total_diff_qqq = 0
    total_diff_nq = 0
    count = 0
    
    for key in ['call_oi', 'pos_gex', 'zero_gamma', 'neg_gex', 'put_oi']:
        if key in gex_levels and key in your_levels:
            your_qqq = your_levels[key]['qqq']
            gex_qqq = gex_levels[key]
            diff_qqq = your_qqq - gex_qqq
            diff_nq = diff_qqq * 41.35  # Approximate conversion
            
            total_diff_qqq += abs(diff_qqq)
            total_diff_nq += abs(diff_nq)
            count += 1
            
            status = "✅" if abs(diff_qqq) <= 1 else "⚠️" if abs(diff_qqq) <= 2 else "❌"
            
            print("{:<15} ${:<11.2f} ${:<11.2f} ${:<11.2f} {:<8.0f} {}".format(
                level_names[key], 
                your_qqq, 
                gex_qqq, 
                diff_qqq,
                diff_nq,
                status
            ))
    
    if count > 0:
        avg_diff_qqq = total_diff_qqq / count
        avg_diff_nq = total_diff_nq / count
        
        print("-"*70)
        print("{:<15} {:<24} ${:<11.2f} {:<8.0f}".format(
            "AVERAGE DIFF", "", avg_diff_qqq, avg_diff_nq))
    
    # Net GEX comparison
    if 'net_gex' in gex_levels and 'net_gex' in your_levels:
        print("\n" + "="*70)
        print("NET GEX COMPARISON")
        print("="*70)
        print(f"Your Net GEX:      {your_levels['net_gex']}")
        print(f"GEXstream Net GEX: {gex_levels['net_gex']}")
        print("\n⚠️  Note: Net GEX magnitude may differ, but strike levels are what matter!")
    
    print("\n" + "="*70)
    print("ACCURACY ASSESSMENT")
    print("="*70)
    
    if count > 0:
        if avg_diff_qqq <= 1:
            print("\n✅ EXCELLENT! Average difference ≤ $1 QQQ (≤ 40 NQ points)")
            print("   Your levels match GEXstream almost perfectly!")
            print("   Ready to use for trading!")
        elif avg_diff_qqq <= 2:
            print("\n⚠️  GOOD! Average difference ≤ $2 QQQ (≤ 80 NQ points)")
            print("   Within your trading requirements!")
            print("   Can be used for trading.")
        else:
            print("\n❌ NEEDS WORK: Average difference > $2 QQQ (> 80 NQ points)")
            print("   May need to investigate formula or data processing.")
    
    print("\n" + "="*70 + "\n")

def main():
    compare_levels()

if __name__ == "__main__":
    main()
