"""
Schwab API Authentication Script with PKCE and Auto Token Refresh
GEX Level Finder - Enhanced Authentication with Auto-Refresh
"""

import requests
import base64
import webbrowser
from urllib.parse import urlencode, parse_qs, urlparse, unquote
import time
import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta

# Your Schwab API Credentials
APP_KEY = "NrdW3LGd07hQk4dfI3pJjsGU544kIOGGne3V3bYlJZ6X52Iv"
SECRET_KEY = "tAOjIWuTAaaZLCiimX0UQWCBOlQxKhKC591OhEGVP4NwC0RUgBjwZGFPOBUoz3Rz"
REDIRECT_URI = "https://127.0.0.1"

# Schwab API URLs
AUTH_URL = "https://api.schwabapi.com/v1/oauth/authorize"
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"

# Token file location
TOKEN_FILE = "tokens.json"


class SchwabAuth:
    """
    Manages Schwab API authentication with automatic token refresh.
    """
    
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.load_tokens()
    
    
    def load_tokens(self):
        """
        Load tokens from file if they exist and are valid.
        """
        if not os.path.exists(TOKEN_FILE):
            return False
        
        try:
            with open(TOKEN_FILE, 'r') as f:
                token_data = json.load(f)
            
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            # Parse expiry time
            expiry_str = token_data.get('token_expiry')
            if expiry_str:
                self.token_expiry = datetime.fromisoformat(expiry_str)
            
            print(f"✅ Loaded tokens from {TOKEN_FILE}")
            
            # Check if tokens are still valid
            if self.is_access_token_valid():
                print(f"✅ Access token is valid until {self.token_expiry.strftime('%I:%M:%S %p')}")
                return True
            elif self.refresh_token:
                print(f"⚠️  Access token expired, but refresh token available")
                return True
            else:
                print(f"❌ Both tokens expired - need new authentication")
                return False
                
        except Exception as e:
            print(f"⚠️  Error loading tokens: {e}")
            return False
    
    
    def save_tokens(self, token_data):
        """
        Save tokens to file with expiration timestamp.
        """
        # Calculate expiry time (access tokens last 30 minutes)
        expires_in = token_data.get('expires_in', 1800)  # Default 30 min
        expiry_time = datetime.now() + timedelta(seconds=expires_in)
        
        save_data = {
            'access_token': token_data['access_token'],
            'refresh_token': token_data['refresh_token'],
            'token_type': token_data['token_type'],
            'expires_in': expires_in,
            'token_expiry': expiry_time.isoformat(),
            'saved_at': datetime.now().isoformat()
        }
        
        with open(TOKEN_FILE, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        self.access_token = token_data['access_token']
        self.refresh_token = token_data['refresh_token']
        self.token_expiry = expiry_time
        
        print(f"💾 Tokens saved to '{TOKEN_FILE}'")
        print(f"   Access token expires: {expiry_time.strftime('%I:%M:%S %p')}")
    
    
    def is_access_token_valid(self):
        """
        Check if access token is still valid (with 2 minute buffer).
        """
        if not self.access_token or not self.token_expiry:
            return False
        
        # Add 2 minute buffer to avoid using expired tokens
        buffer = timedelta(minutes=2)
        return datetime.now() < (self.token_expiry - buffer)
    
    
    def get_valid_access_token(self):
        """
        Get a valid access token, refreshing if necessary.
        This is the main method you'll call from other scripts.
        """
        # If access token is valid, return it
        if self.is_access_token_valid():
            return self.access_token
        
        # If we have a refresh token, try to refresh
        if self.refresh_token:
            print("\n⏳ Access token expired - refreshing automatically...")
            if self.refresh_access_token():
                return self.access_token
        
        # If refresh failed or no refresh token, need new auth
        print("\n⚠️  Cannot refresh token - need new authentication")
        print("Please run the full authentication flow.")
        return None
    
    
    def refresh_access_token(self):
        """
        Use refresh token to get a new access token.
        """
        print("🔄 Refreshing access token...")
        
        # Encode credentials for Basic Auth
        credentials = f"{APP_KEY}:{SECRET_KEY}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": APP_KEY
        }
        
        try:
            response = requests.post(TOKEN_URL, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.save_tokens(token_data)
                print("✅ Access token refreshed successfully!")
                return True
            else:
                print(f"❌ Token refresh failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error refreshing token: {e}")
            return False
    
    
    def generate_pkce_codes(self):
        """
        Generate PKCE code verifier and challenge.
        """
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
        code_verifier = code_verifier.replace('=', '').replace('+', '-').replace('/', '_')
        
        code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
        code_challenge = code_challenge.replace('=', '').replace('+', '-').replace('/', '_')
        
        return code_verifier, code_challenge
    
    
    def get_authorization_code(self):
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
        code_verifier, code_challenge = self.generate_pkce_codes()
        
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
            
            return auth_code, code_verifier
            
        except Exception as e:
            print(f"\n❌ ERROR parsing URL: {e}")
            return None, None
    
    
    def get_access_token_from_auth_code(self, auth_code, code_verifier):
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
            response = requests.post(TOKEN_URL, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                print("\n✅ SUCCESS! Access token received!")
                print(f"\n📊 Token Details:")
                print(f"   - Access Token: {token_data['access_token'][:20]}...")
                print(f"   - Refresh Token: {token_data['refresh_token'][:20]}...")
                print(f"   - Expires in: {token_data['expires_in']} seconds ({token_data['expires_in']//60} minutes)")
                
                # Save tokens
                self.save_tokens(token_data)
                
                return True
            else:
                print(f"\n❌ ERROR: Failed to get token")
                print(f"   Status Code: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    
    def authenticate(self):
        """
        Full authentication flow - only needed once or when tokens expire.
        """
        print("\n🚀 Starting Schwab API Authentication (PKCE Flow)...")
        
        # Step 1: Get authorization code with PKCE
        auth_code, code_verifier = self.get_authorization_code()
        if not auth_code or not code_verifier:
            print("\n❌ Authentication failed. Please try again.")
            return False
        
        # Step 2: Get access token with PKCE
        success = self.get_access_token_from_auth_code(auth_code, code_verifier)
        if not success:
            print("\n❌ Failed to get access token. Please try again.")
            return False
        
        print("\n" + "="*60)
        print("🎉 AUTHENTICATION COMPLETE!")
        print("="*60)
        print("\nTokens saved and ready to use!")
        print("Access token will be automatically refreshed when needed.")
        print("\n" + "="*60 + "\n")
        
        return True


def main():
    """
    Main entry point - run this to authenticate or refresh tokens.
    """
    auth = SchwabAuth()
    
    # Check if we have valid tokens
    token = auth.get_valid_access_token()
    
    if token:
        print("\n✅ You already have valid tokens!")
        print("No need to re-authenticate.")
        print("\nYour scripts will automatically use and refresh these tokens.")
    else:
        print("\n⚠️  No valid tokens found. Starting authentication...")
        auth.authenticate()


if __name__ == "__main__":
    main()
