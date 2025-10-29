"""
Token Helper - Easy access to valid Schwab API tokens
Use this in your fetch_options_chain.py and calculate_gex.py scripts
"""

from schwab_auth_with_refresh import SchwabAuth


def get_token():
    """
    Simple function to get a valid access token.
    Automatically handles token refresh.
    
    Returns:
        str: Valid access token, or None if authentication needed
    
    Usage in your scripts:
        from token_helper import get_token
        
        token = get_token()
        if not token:
            print("Please run: python schwab_auth_with_refresh.py")
            exit()
        
        # Use token in your API calls
        headers = {"Authorization": f"Bearer {token}"}
    """
    auth = SchwabAuth()
    return auth.get_valid_access_token()


def check_token_status():
    """
    Check and display token status without using them.
    Useful for debugging.
    """
    auth = SchwabAuth()
    
    if auth.access_token:
        if auth.is_access_token_valid():
            print(f"✅ Access token valid until: {auth.token_expiry.strftime('%I:%M:%S %p')}")
            return True
        elif auth.refresh_token:
            print(f"⚠️  Access token expired, but can be refreshed")
            return True
        else:
            print(f"❌ All tokens expired - need new authentication")
            return False
    else:
        print(f"❌ No tokens found - need authentication")
        return False


if __name__ == "__main__":
    # Test the token system
    print("Testing token system...\n")
    check_token_status()
    
    print("\nAttempting to get valid token...")
    token = get_token()
    
    if token:
        print(f"✅ Got valid token: {token[:20]}...")
    else:
        print("❌ No valid token available")
        print("Run: python schwab_auth_with_refresh.py")
