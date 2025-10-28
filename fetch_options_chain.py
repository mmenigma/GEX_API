"""
Schwab API Options Chain Fetcher - FIXED VERSION
GEX Level Finder - Step 2: Fetch Options Data

CRITICAL FIX: Now fetches MULTIPLE expirations (0-30 DTE) instead of just one
This matches what GEXstream does and will give accurate GEX levels
"""

import requests
import json
from datetime import datetime, timedelta
import time


def load_tokens():
    """
    Load access token from tokens.txt file.
    """
    try:
        with open("tokens.txt", "r") as f:
            lines = f.readlines()
            token_data = {}
            for line in lines:
                key, value = line.strip().split('=', 1)
                token_data[key] = value
        
        # Check if token is expired
        token_timestamp = int(token_data.get('timestamp', 0))
        expires_in = int(token_data.get('expires_in', 0))
        current_time = int(time.time())
        
        if current_time - token_timestamp > expires_in:
            print("⚠️  WARNING: Access token may be expired")
            print("You may need to re-authenticate using schwab_auth_fixed.py")
        
        return token_data.get('access_token')
        
    except FileNotFoundError:
        print("❌ ERROR: tokens.txt not found")
        print("Please run schwab_auth_fixed.py first to authenticate")
        return None
    except Exception as e:
        print(f"❌ ERROR loading tokens: {e}")
        return None


def fetch_nq_price(access_token):
    """
    Fetch current NQ futures price from Schwab API.
    """
    print("\n📊 Fetching NQ futures price...")
    
    # Try different NQ symbols
    symbols_to_try = ["/NQ", "NQ", "/NQH25", "/NQZ25"]
    
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
    
    FIXED: Now fetches ALL expirations from today through next 30 days
    This matches GEXstream methodology
    """
    print("\n" + "="*60)
    print("FETCHING OPTIONS CHAIN DATA - FIXED VERSION")
    print("="*60)
    
    # Use provided token or load from file
    if not access_token:
        access_token = load_tokens()
        if not access_token:
            return None
    
    # Get date range: today through +30 days
    today = datetime.now()
    from_date = today.strftime('%Y-%m-%d')
    to_date = (today + timedelta(days=30)).strftime('%Y-%m-%d')
    
    print(f"\n📊 Fetching {symbol} options...")
    print(f"   Date Range: {from_date} to {to_date}")
    print(f"   This includes: All expirations within next 30 days")
    print(f"   Today: {today.strftime('%A, %Y-%m-%d')}")
    
    # Schwab API endpoint
    url = f"https://api.schwabapi.com/marketdata/v1/chains"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    params = {
        "symbol": symbol,
        "contractType": "ALL",  # Both calls and puts
        "includeUnderlyingQuote": "true",
        "strategy": "SINGLE",
        "range": "ALL",
        "fromDate": from_date,
        "toDate": to_date
    }
    
    try:
        print("\n🔄 Making API request...")
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
            
            # List expirations
            if 'callExpDateMap' in data:
                print(f"\n📅 Expirations fetched:")
                for exp_date in sorted(data['callExpDateMap'].keys())[:10]:  # Show first 10
                    date_part = exp_date.split(':')[0]
                    dte_part = exp_date.split(':')[1]
                    num_strikes = len(data['callExpDateMap'][exp_date])
                    print(f"   {date_part} ({dte_part} DTE): {num_strikes} strikes")
                if num_call_exp > 10:
                    print(f"   ... and {num_call_exp - 10} more")
            
            # Save raw data
            with open("options_chain_raw.json", "w") as f:
                json.dump(data, f, indent=2)
            
            return data
            
        elif response.status_code == 401:
            print("\n❌ ERROR: Authentication failed (401)")
            print("Your access token may have expired.")
            print("Run 'python schwab_auth_fixed.py' to re-authenticate")
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
    print("\n🚀 Starting Options Chain Fetch - FIXED VERSION...")
    print("⚠️  CRITICAL FIX: Now fetching MULTIPLE expirations (0-30 DTE)")
    print("   This matches GEXstream methodology and will improve accuracy")
    
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
        print("\n🎯 IMPORTANT:")
        print("   This fixed version fetches ALL near-term expirations")
        print("   Your GEX calculations should now match GEXstream much better")
        print("\nNext step: Calculate GEX levels from this data")
        print("Run: python calculate_gex_v2.1.py")
        print("\n" + "="*60 + "\n")
    else:
        print("\n" + "="*60)
        print("❌ DATA FETCH FAILED")
        print("="*60)
        print("\nPlease check the error messages above")
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()