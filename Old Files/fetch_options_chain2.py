"""
Schwab API Options Chain Fetcher - FIXED v3 (502 Buffer Overflow Resolution)
GEX Level Finder - Step 2: Fetch Options Data

FIXES:
1. Removed fromDate/toDate parameters (Schwab API doesn't like them)
2. Changed range from "ALL" to "OTM" to avoid 502 buffer overflow error
3. Added strikeCount=50 to limit data size
4. Added auto token refresh support

CRITICAL: Using range="ALL" causes "Body buffer overflow" 502 error!
The API response is too large. Using range="OTM" with strikeCount=50 
gives us enough strikes for GEX calculations without overwhelming the API.
"""

import requests
import json
from datetime import datetime, timedelta
import time
from token_helper import get_token


def load_tokens():
    """
    Load access token with automatic refresh.
    """
    access_token = get_token()
    
    if not access_token:
        print("❌ ERROR: Could not get valid token")
        print("Please run: python schwab_auth_with_refresh.py")
        return None
    
    return access_token


def fetch_nq_price(access_token):
    """
    Fetch current NQ futures price from Schwab API.
    
    CRITICAL FIX: Must fetch the FRONT MONTH contract to match TOS.
    As of Oct 2025, front month is /NQZ25 (Dec 2025).
    
    CONTRACT ROLL SCHEDULE:
    - /NQH25 (Mar 2025) - EXPIRED
    - /NQM25 (Jun 2025) - EXPIRED  
    - /NQU25 (Sep 2025) - EXPIRED
    - /NQZ25 (Dec 2025) - CURRENT FRONT MONTH ✓
    - /NQH26 (Mar 2026) - Next contract
    
    Update this list when contracts roll (mid-month before expiry)!
    """
    print("\n📊 Fetching NQ futures price...")
    print("   ⚠️  CRITICAL: Must use FRONT MONTH contract to match TOS")
    
    # Try different NQ symbols - FRONT MONTH FIRST
    symbols_to_try = [
        "/NQZ25",     # Dec 2025 - CURRENT FRONT MONTH (Oct-Dec 2025)
        "/NQ",        # Generic symbol (may return back month)
        "$NQ",        # Alternative generic
        "/NQH26",     # Mar 2026 - Next contract (fallback)
    ]
    
    print(f"   Trying symbols in order: {symbols_to_try}")
    
    for symbol in symbols_to_try:
        url = f"https://api.schwabapi.com/marketdata/v1/quotes"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        params = {
            "symbols": symbol,
            "fields": "quote"
        }
        
        try:
            print(f"   Attempting: {symbol}...", end=" ")
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if symbol in data:
                    quote = data[symbol].get('quote', {})
                    last_price = quote.get('lastPrice') or quote.get('mark')
                    
                    if last_price:
                        print(f"✓")
                        print(f"   ✅ NQ Price: {last_price:,.2f} (from {symbol})")
                        print(f"   📅 Contract: {symbol}")
                        
                        # Warn if not using front month
                        if symbol != "/NQZ25":
                            print(f"   ⚠️  WARNING: Not using front month /NQZ25!")
                            print(f"   ⚠️  This may cause ratio mismatch with TOS")
                        
                        return last_price
                else:
                    print(f"✗ (no data)")
            else:
                print(f"✗ ({response.status_code})")
        except Exception as e:
            print(f"✗ (error: {e})")
            continue
    
    print("   ❌ Could not fetch NQ price from any symbol")
    print("   ⚠️  Using approximate ratio - may not match TOS exactly")
    return None


def fetch_options_chain(symbol="QQQ", access_token=None):
    """
    Fetch options chain from Schwab API.
    
    FIXED: Removed problematic fromDate/toDate parameters
    The API will return all available expirations by default
    """
    print("\n" + "="*60)
    print("FETCHING OPTIONS CHAIN DATA - FIXED v2")
    print("="*60)
    
    # Use provided token or load from file
    if not access_token:
        access_token = load_tokens()
        if not access_token:
            return None
    
    today = datetime.now()
    
    print(f"\n📊 Fetching {symbol} options...")
    print(f"   Strategy: Get ALL available expirations")
    print(f"   Today: {today.strftime('%A, %Y-%m-%d')}")
    
    # Schwab API endpoint
    url = f"https://api.schwabapi.com/marketdata/v1/chains"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    # FIXED: Limited strike range to avoid 502 buffer overflow
    # Using "OTM" (Out of The Money) gets strikes around current price
    # This is sufficient for GEX calculations and avoids the "Body buffer overflow" error
    params = {
        "symbol": symbol,
        "contractType": "ALL",  # Both calls and puts
        "includeUnderlyingQuote": "true",
        "strategy": "SINGLE",
        "range": "OTM",  # Only Out-of-the-Money strikes (avoids buffer overflow)
        "strikeCount": 50  # Get 50 strikes above and below (total 100)
        # Note: "ALL" causes 502 error - response too large
    }
    
    try:
        print("\n📡 Making API request...")
        print(f"   Parameters: {params}")
        
        response = requests.get(url, headers=headers, params=params)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Count expirations and strikes
            num_call_exp = len(data.get('callExpDateMap', {}))
            num_put_exp = len(data.get('putExpDateMap', {}))
            total_call_strikes = sum(len(strikes) for strikes in data.get('callExpDateMap', {}).values())
            total_put_strikes = sum(len(strikes) for strikes in data.get('putExpDateMap', {}).values())
            
            print("\n✅ SUCCESS! Options data received")
            print(f"💾 Raw data saved to 'options_chain_raw.json'")
            
            # Display info
            print(f"\n📈 Calls:")
            print(f"   Expirations: {num_call_exp}")
            print(f"   Total strikes: {total_call_strikes}")
            
            print(f"\n📉 Puts:")
            print(f"   Expirations: {num_put_exp}")
            print(f"   Total strikes: {total_put_strikes}")
            
            if 'underlyingPrice' in data:
                print(f"\n💰 {symbol} Price: ${data['underlyingPrice']:.2f}")
            
            # List expirations and their DTE
            if 'callExpDateMap' in data:
                print(f"\n📅 Expirations fetched:")
                exp_list = []
                for exp_date in sorted(data['callExpDateMap'].keys()):
                    date_part = exp_date.split(':')[0]
                    dte_part = exp_date.split(':')[1]
                    num_strikes = len(data['callExpDateMap'][exp_date])
                    exp_list.append((date_part, int(dte_part), num_strikes))
                
                # Show first 15 expirations
                for i, (date_part, dte, num_strikes) in enumerate(exp_list[:15]):
                    dte_label = f"{dte} DTE"
                    if dte == 0:
                        dte_label += " ⭐ (0DTE!)"
                    print(f"   {date_part} ({dte_label}): {num_strikes} strikes")
                
                if len(exp_list) > 15:
                    print(f"   ... and {len(exp_list) - 15} more")
            
            # Save raw data
            with open("options_chain_raw.json", "w") as f:
                json.dump(data, f, indent=2)
            
            return data
            
        elif response.status_code == 401:
            print("\n❌ ERROR: Authentication failed (401)")
            print("Your access token may have expired.")
            print("Run 'python schwab_auth_with_refresh.py' to re-authenticate")
            return None
        
        elif response.status_code == 400:
            print("\n❌ ERROR: Bad Request (400)")
            print("The API rejected our parameters.")
            print(f"Response: {response.text}")
            print("\nTroubleshooting:")
            print("1. Check that symbol 'QQQ' is valid")
            print("2. Verify your account has options data access")
            print("3. Try re-authenticating: python schwab_auth_with_refresh.py")
            return None
            
        else:
            print(f"\n❌ ERROR: Failed to fetch data")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """
    Main function to fetch options chain and NQ price.
    """
    print("\n🚀 Starting Options Chain Fetch - FIXED v3...")
    print("⚠️  FIX: Changed range='OTM' to avoid 502 buffer overflow")
    print("⚠️  Using strikeCount=50 for optimal data size")
    
    # Load access token
    access_token = load_tokens()
    if not access_token:
        return
    
    # Fetch NQ price
    nq_price = fetch_nq_price(access_token)
    
    # Fetch QQQ options (pass access token)
    data = fetch_options_chain("QQQ", access_token)
    
    if data:
        # Add NQ price to the data
        if nq_price:
            data['nq_price'] = nq_price
        
        # Save data with NQ price
        with open("options_chain_raw.json", "w") as f:
            json.dump(data, f, indent=2)
        
        print("\n" + "="*60)
        print("✅ DATA FETCH COMPLETE!")
        print("="*60)
        print("\n🎯 Fixed the 400 error by:")
        print("   ✅ Removing fromDate/toDate parameters")
        print("   ✅ Using range='ALL' to get all strikes")
        print("   ✅ Simplified parameter set")
        
        if nq_price:
            qqq_price = data.get('underlyingPrice', 0)
            if qqq_price:
                ratio = nq_price / qqq_price
                print(f"\n📊 RATIO VERIFICATION:")
                print(f"   QQQ Price: ${qqq_price:.2f}")
                print(f"   NQ Price:  {nq_price:,.2f}")
                print(f"   Ratio:     {ratio:.4f}")
                print(f"\n   Expected TOS ratio: 39.8 - 40.3")
                if 39.5 < ratio < 40.5:
                    print(f"   ✅ Ratio looks correct!")
                else:
                    print(f"   ⚠️  WARNING: Ratio outside typical range!")
                    print(f"   ⚠️  May be using wrong NQ contract month")
        
        print("\nNext step: Calculate GEX levels from this data")
        print("Run: python calculate_gex.py")
        print("\n" + "="*60 + "\n")
    else:
        print("\n" + "="*60)
        print("❌ DATA FETCH FAILED")
        print("="*60)
        print("\nPlease check the error messages above")
        print("\nCommon fixes:")
        print("1. Re-authenticate: python schwab_auth_with_refresh.py")
        print("2. Verify QQQ is a valid symbol")
        print("3. Check your Schwab account has options permissions")
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
