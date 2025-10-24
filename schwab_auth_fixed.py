"""
Schwab API Authentication Script with PKCE and Fixed Base64 Handling
GEX Level Finder - Step 1: Authentication
"""

import requests
import base64
import webbrowser
from urllib.parse import urlencode, parse_qs, urlparse, unquote
import time
import hashlib
import secrets

# Your Schwab API Credentials
APP_KEY = "NrdW3LGd07hQk4dfI3pJjsGU544kIOGGne3V3bYlJZ6X52Iv"
SECRET_KEY = "tAOjIWuTAaaZLCiimX0UQWCBOlQxKhKC591OhEGVP4NwC0RUgBjwZGFPOBUoz3Rz"
REDIRECT_URI = "https://127.0.0.1"

# Schwab API URLs
AUTH_URL = "https://api.schwabapi.com/v1/oauth/authorize"
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"


def generate_pkce_codes():
    """
    Generate PKCE code verifier and challenge.
    """
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
    code_verifier = code_verifier.replace('=', '').replace('+', '-').replace('/', '_')
    
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
    code_challenge = code_challenge.replace('=', '').replace('+', '-').replace('/', '_')
    
    return code_verifier, code_challenge


def get_authorization_code():
    """
    Step 1: Open browser for user to log in to Schwab and authorize the app.
    Returns the authorization code and code verifier.
    """
    print("\n" + "="*60)
    print("SCHWAB API AUTHENTICATION (PKCE FLOW)")
    print("="*60)
    print("\nStep 1: Getting Authorization Code...")
    print("\nA browser window will open. Please:")
    print("  1. Log in with your Schwab credentials")
    print("  2. Authorize the application")
    print("  3. You'll be redirected to a blank page (this is normal)")
    print("  4. Copy the ENTIRE URL from the address bar")
    print("\n" + "="*60)
    
    # Generate PKCE codes
    code_verifier, code_challenge = generate_pkce_codes()
    
    # Build authorization URL with PKCE
    params = {
        "client_id": APP_KEY,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    auth_url = f"{AUTH_URL}?{urlencode(params)}"
    
    # Open browser
    print(f"\nOpening browser...")
    webbrowser.open(auth_url)
    
    print("\n" + "="*60)
    print("After authorizing, you'll see a security warning page.")
    print("THIS IS NORMAL - it's because we're using localhost.")
    print("\nCopy the ENTIRE URL from your browser's address bar and paste it below.")
    print("="*60 + "\n")
    
    # Get the redirect URL from user
    redirect_url = input("Paste the full URL here: ").strip()
    
    # Extract authorization code
    try:
        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)
        auth_code = query_params.get('code', [None])[0]
        
        if not auth_code:
            print("\n❌ ERROR: Could not find authorization code in URL")
            print("Make sure you copied the complete URL from the address bar.")
            return None, None
        
        # URL decode the authorization code
        auth_code = unquote(auth_code)
        print(f"\n✅ Authorization code received!")
        print(f"[DEBUG] Code length: {len(auth_code)}")
        
        return auth_code, code_verifier
        
    except Exception as e:
        print(f"\n❌ ERROR parsing URL: {e}")
        return None, None


def get_access_token(auth_code, code_verifier):
    """
    Step 2: Exchange authorization code for access token using PKCE.
    """
    print("\nStep 2: Exchanging authorization code for access token (with PKCE)...")
    
    # Encode credentials for Basic Auth
    credentials = f"{APP_KEY}:{SECRET_KEY}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
        "client_id": APP_KEY
    }
    
    try:
        print(f"[DEBUG] Making token request...")
        print(f"[DEBUG] Code verifier length: {len(code_verifier)}")
        
        response = requests.post(TOKEN_URL, headers=headers, data=data)
        
        print(f"[DEBUG] Response status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("\n✅ SUCCESS! Access token received!")
            print(f"\n📊 Token Details:")
            print(f"   - Access Token: {token_data['access_token'][:20]}...")
            print(f"   - Refresh Token: {token_data['refresh_token'][:20]}...")
            print(f"   - Expires in: {token_data['expires_in']} seconds ({token_data['expires_in']//60} minutes)")
            
            # Save tokens to file
            save_tokens(token_data)
            
            return token_data
        else:
            print(f"\n❌ ERROR: Failed to get token")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_tokens(token_data):
    """
    Save tokens to a file for future use.
    """
    with open("tokens.txt", "w") as f:
        f.write(f"access_token={token_data['access_token']}\n")
        f.write(f"refresh_token={token_data['refresh_token']}\n")
        f.write(f"expires_in={token_data['expires_in']}\n")
        f.write(f"token_type={token_data['token_type']}\n")
        f.write(f"timestamp={int(time.time())}\n")
    
    print(f"\n💾 Tokens saved to 'tokens.txt'")


def main():
    """
    Main authentication flow with PKCE.
    """
    print("\n🚀 Starting Schwab API Authentication (PKCE Flow)...")
    print("This is a one-time setup (tokens last 7 days)")
    
    # Step 1: Get authorization code with PKCE
    auth_code, code_verifier = get_authorization_code()
    if not auth_code or not code_verifier:
        print("\n❌ Authentication failed. Please try again.")
        return
    
    # Step 2: Get access token with PKCE
    token_data = get_access_token(auth_code, code_verifier)
    if not token_data:
        print("\n❌ Failed to get access token. Please try again.")
        return
    
    print("\n" + "="*60)
    print("🎉 AUTHENTICATION COMPLETE!")
    print("="*60)
    print("\nYou're now ready to fetch options data from Schwab!")
    print("Next step: Run the options chain fetcher script.")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
