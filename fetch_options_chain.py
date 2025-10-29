"""
Schwab API Options Chain Fetcher - FIXED v2 (400 Error Resolution)
GEX Level Finder - Step 2: Fetch Options Data

FIXES:
1. Removed fromDate/toDate parameters (Schwab API doesn't like them)
2. Using range="ALL" to get all available strikes
3. Simplified parameter set
4. Added auto token refresh support
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
    """
    print("\n📊 Fetching NQ futures price...")
    
    # Try different NQ symbols
    symbols_to_try = ["/NQZ25", "/NQ", "NQ", "/NQH25"]
    
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
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if symbol in data:
                    quote = data[symbol].get('quote', {})
                    last_price = quote.get('lastPrice') or quote.get('mark')
                    
                    if last_price:
                        print(f"✅ NQ Price: {last_price:,.2f} (from {symbol})")
                        return last_price
        except:
            continue
    
    print("⚠️  Could not fetch NQ price, using approximate ratio")
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
    
    # FIXED: Simplified parameters - removed fromDate/toDate
    params = {
        "symbol": symbol,
        "contractType": "ALL",  # Both calls and puts
        "includeUnderlyingQuote": "true",
        "strategy": "SINGLE",
        "range": "ALL"  # Get all strikes
        # Removed: fromDate and toDate (these cause 400 errors)
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
    print("\n🚀 Starting Options Chain Fetch - FIXED v2...")
    print("⚠️  FIX: Removed fromDate/toDate parameters that caused 400 error")
    
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
