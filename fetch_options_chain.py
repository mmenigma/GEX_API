"""
Schwab API Options Chain Fetcher
GEX Level Finder - Step 2: Fetch Options Data

This script fetches QQQ options chain data from Schwab API.
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
    symbols_to_try = ["/NQ", "NQ", "/NQH25", "/NQZ24"]
    
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


def get_next_expiration():
    """
    Determine the next options expiration date.
    For 0DTE: Returns today if Wed/Fri, otherwise returns next Wed/Fri
    """
    today = datetime.now()
    day_of_week = today.weekday()  # Monday=0, Sunday=6
    
    # Wednesday = 2, Friday = 4
    if day_of_week == 2 or day_of_week == 4:
        # Today is Wed or Fri - use 0DTE
        expiration = today
        is_0dte = True
    elif day_of_week < 2:
        # Monday or Tuesday - next is Wednesday
        days_until_wed = 2 - day_of_week
        expiration = today + timedelta(days=days_until_wed)
        is_0dte = False
    elif day_of_week == 3:
        # Thursday - next is Friday
        expiration = today + timedelta(days=1)
        is_0dte = False
    else:
        # Friday after market or weekend - next is Monday->Wednesday
        days_until_wed = (7 - day_of_week + 2) % 7
        if days_until_wed == 0:
            days_until_wed = 7
        expiration = today + timedelta(days=days_until_wed)
        is_0dte = False
    
    return expiration.strftime('%Y-%m-%d'), is_0dte


def fetch_options_chain(symbol="QQQ", access_token=None):
    """
    Fetch options chain from Schwab API.
    """
    print("\n" + "="*60)
    print("FETCHING OPTIONS CHAIN DATA")
    print("="*60)
    
    # Use provided token or load from file
    if not access_token:
        access_token = load_tokens()
        if not access_token:
            return None
    
    # Get expiration date
    expiration_date, is_0dte = get_next_expiration()
    
    print(f"\n📊 Fetching {symbol} options...")
    print(f"   Expiration: {expiration_date}")
    print(f"   Type: {'0DTE (same day)' if is_0dte else 'Weekly expiration'}")
    print(f"   Today: {datetime.now().strftime('%A, %Y-%m-%d')}")
    
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
        "fromDate": expiration_date,
        "toDate": expiration_date
    }
    
    try:
        print("\n🔄 Making API request...")
        response = requests.get(url, headers=headers, params=params)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Save raw data for inspection
            with open("options_chain_raw.json", "w") as f:
                json.dump(data, f, indent=2)
            
            print("\n✅ SUCCESS! Options data received")
            print(f"💾 Raw data saved to 'options_chain_raw.json'")
            
            # Display some basic info
            if 'callExpDateMap' in data:
                num_call_strikes = sum(len(strikes) for strikes in data['callExpDateMap'].values())
                print(f"\n📈 Calls: {num_call_strikes} strikes")
            
            if 'putExpDateMap' in data:
                num_put_strikes = sum(len(strikes) for strikes in data['putExpDateMap'].values())
                print(f"📉 Puts: {num_put_strikes} strikes")
            
            if 'underlyingPrice' in data:
                print(f"💰 {symbol} Price: ${data['underlyingPrice']:.2f}")
            
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
    print("\n🚀 Starting Options Chain Fetch...")
    
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
        print("\nNext step: Calculate GEX levels from this data")
        print("Check 'options_chain_raw.json' to see the full data structure")
        print("\n" + "="*60 + "\n")
    else:
        print("\n" + "="*60)
        print("❌ DATA FETCH FAILED")
        print("="*60)
        print("\nPlease check the error messages above")
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
