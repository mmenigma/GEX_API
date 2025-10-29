"""
Example: How to Update Your Existing Scripts for Auto Token Refresh

This shows you how to modify fetch_options_chain.py and calculate_gex.py
to use the new automatic token refresh system.
"""

# =============================================================================
# OLD WAY (your current scripts):
# =============================================================================
"""
import requests

# Read token from tokens.txt
with open("tokens.txt", "r") as f:
    lines = f.readlines()
    access_token = lines[0].split("=")[1].strip()

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Make API call
response = requests.get(url, headers=headers)
"""

# =============================================================================
# NEW WAY (with automatic token refresh):
# =============================================================================
"""
import requests
from token_helper import get_token

# Get valid token (automatically refreshes if needed!)
access_token = get_token()
if not access_token:
    print("❌ No valid token. Please run: python schwab_auth_with_refresh.py")
    exit()

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Make API call (same as before)
response = requests.get(url, headers=headers)
"""

# =============================================================================
# FULL EXAMPLE: Modified fetch_options_chain.py
# =============================================================================

import requests
from token_helper import get_token
import json
from datetime import datetime

def fetch_options_chain():
    """
    Fetch QQQ options chain with automatic token refresh.
    """
    print("\n" + "="*60)
    print("FETCHING QQQ OPTIONS CHAIN FROM SCHWAB API")
    print("="*60)
    
    # Get valid token (handles refresh automatically!)
    print("\n🔑 Getting access token...")
    access_token = get_token()
    
    if not access_token:
        print("\n❌ Could not get valid token!")
        print("Please run: python schwab_auth_with_refresh.py")
        return None
    
    print("✅ Valid token obtained!")
    
    # Schwab API endpoint
    symbol = "QQQ"
    url = f"https://api.schwabapi.com/marketdata/v1/chains"
    
    # Set up parameters (0DTE options)
    params = {
        "symbol": symbol,
        "contractType": "ALL",
        "includeUnderlyingQuote": True,
        "strikeCount": 140,
        "optionType": "S"  # Standard options
    }
    
    # Set up headers with the valid token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"\n📡 Fetching options chain for {symbol}...")
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Successfully fetched options chain!")
            
            # Save raw data
            with open("options_chain_raw.json", "w") as f:
                json.dump(data, f, indent=2)
            
            print(f"💾 Raw data saved to 'options_chain_raw.json'")
            return data
            
        else:
            print(f"\n❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return None


if __name__ == "__main__":
    # Run the fetch
    data = fetch_options_chain()
    
    if data:
        print("\n" + "="*60)
        print("✅ OPTIONS CHAIN FETCH COMPLETE!")
        print("="*60)
        print("\nNext step: Run calculate_gex.py to process this data")
    else:
        print("\n❌ Failed to fetch options chain")

# =============================================================================
# KEY CHANGES TO MAKE IN YOUR SCRIPTS:
# =============================================================================
"""
1. REPLACE this:
   with open("tokens.txt", "r") as f:
       access_token = lines[0].split("=")[1].strip()

   WITH this:
   from token_helper import get_token
   access_token = get_token()
   if not access_token:
       print("Run: python schwab_auth_with_refresh.py")
       exit()

2. That's it! The rest of your script stays exactly the same.

3. The token will automatically refresh when needed (every 30 minutes).

4. You never have to manually re-authenticate unless the refresh token 
   expires (which happens after 7 days of not using the system).
"""
