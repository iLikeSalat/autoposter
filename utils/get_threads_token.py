"""
Threads Token Generator
Helps you get a Threads API access token through the OAuth flow.

Follow these steps:
1. Create a Threads app at https://developers.facebook.com/apps/
2. Set up your app credentials in .env file
3. Run this script and follow the prompts
"""
import os
import requests
from dotenv import load_dotenv
from urllib.parse import urlencode, parse_qs, urlparse
import webbrowser

# Load environment variables
load_dotenv()

def get_threads_token():
    """Get Threads API access token through OAuth flow."""
    
    # Get credentials from environment
    CLIENT_ID = os.getenv('THREADS_CLIENT_ID')
    CLIENT_SECRET = os.getenv('THREADS_CLIENT_SECRET')
    REDIRECT_URI = os.getenv('THREADS_REDIRECT_URI', 'https://localhost/')
    
    # Required scopes for Threads API
    # threads_read_replies: Required to read comments/replies
    # threads_manage_replies: Required to post replies
    SCOPES = 'threads_basic,threads_content_publish,threads_read_replies,threads_manage_replies'
    
    # Validate required credentials
    if not CLIENT_ID:
        print("❌ Error: THREADS_CLIENT_ID not found in .env file")
        print("   Please add your App ID from https://developers.facebook.com/apps/")
        return None
    
    if not CLIENT_SECRET:
        print("❌ Error: THREADS_CLIENT_SECRET not found in .env file")
        print("   Please add your App Secret from https://developers.facebook.com/apps/")
        return None
    
    print("=" * 60)
    print("Threads API Token Generator")
    print("=" * 60)
    print(f"\nApp ID: {CLIENT_ID}")
    print(f"Redirect URI: {REDIRECT_URI}")
    print(f"Scopes: {SCOPES}\n")
    
    # Step 1: Generate Authorization URL
    # Use Threads OAuth to get short-lived token, then exchange using Threads endpoint
    print("Step 1: Generating authorization URL...")
    auth_params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
        'response_type': 'code'
    }
    auth_url = f"https://threads.net/oauth/authorize?{urlencode(auth_params)}"
    
    print(f"\n📋 Visit this URL to authorize the app:")
    print(f"   {auth_url}\n")
    
    # Try to open in browser
    try:
        webbrowser.open(auth_url)
        print("✓ Opened authorization URL in your default browser")
    except:
        print("⚠ Could not open browser automatically")
    
    print("\n" + "-" * 60)
    print("After authorizing, you'll be redirected to your redirect URI")
    print("Copy the full redirect URL (including the 'code' parameter)")
    print("-" * 60 + "\n")
    
    # Step 2: Get authorization code from user
    redirect_url = input("Enter the full redirect URL (or just the authorization code): ").strip()
    
    # Extract code from URL if full URL provided
    auth_code = None
    if redirect_url.startswith('http'):
        parsed = urlparse(redirect_url)
        params = parse_qs(parsed.query)
        if 'code' in params:
            auth_code = params['code'][0]
        else:
            print("❌ Error: No 'code' parameter found in redirect URL")
            return None
    else:
        auth_code = redirect_url
    
    if not auth_code:
        print("❌ Error: Could not extract authorization code")
        return None
    
    print(f"\n✓ Authorization code received: {auth_code[:20]}...\n")
    
    # Step 3: Exchange Authorization Code for Short-Lived Access Token
    print("Step 2: Exchanging authorization code for access token...")
    token_url = 'https://graph.threads.net/oauth/access_token'
    token_data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'code': auth_code
    }
    
    try:
        token_response = requests.post(token_url, data=token_data, timeout=30)
        token_response.raise_for_status()
        token_info = token_response.json()
        
        if 'error' in token_info:
            print(f"❌ Error: {token_info.get('error', {}).get('message', 'Unknown error')}")
            return None
        
        short_lived_token = token_info.get('access_token')
        user_id = token_info.get('user_id')
        
        if not short_lived_token:
            print("❌ Error: No access token in response")
            print(f"Response: {token_info}")
            return None
        
        print(f"✓ Short-lived access token received")
        print(f"✓ User ID: {user_id}\n")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error exchanging authorization code: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response text: {e.response.text}")
        return None
    
    # Step 4: Exchange Short-Lived Token for Long-Lived Access Token
    print("Step 3: Exchanging for long-lived access token...")
    
    # Use Threads API endpoint for token exchange
    # Format: GET https://graph.threads.net/access_token
    #         ?grant_type=th_exchange_token
    #         &client_secret=THREADS_APP_SECRET
    #         &access_token=SHORT_LIVED_TOKEN
    long_token_url = 'https://graph.threads.net/access_token'
    long_token_params = {
        'grant_type': 'th_exchange_token',  # Threads-specific grant type
        'client_secret': CLIENT_SECRET,
        'access_token': short_lived_token
    }
    
    long_lived_token = None
    expires_in = 3600
    
    try:
        print("   Using Threads API endpoint for token exchange...")
        long_token_response = requests.get(long_token_url, params=long_token_params, timeout=30)
        long_token_response.raise_for_status()
        long_token_info = long_token_response.json()
        
        if 'error' in long_token_info:
            error_msg = long_token_info.get('error', {}).get('message', 'Unknown error')
            error_code = long_token_info.get('error', {}).get('code', 'Unknown')
            print(f"   ❌ Threads API error ({error_code}): {error_msg}")
        else:
            long_lived_token = long_token_info.get('access_token')
            expires_in = long_token_info.get('expires_in', 3600)
            
            if long_lived_token and long_lived_token != short_lived_token:
                days = int(expires_in) // 86400
                print(f"   ✓ Long-lived access token received!")
                print(f"   ✓ Expires in: {expires_in} seconds ({days} days)")
                print(f"   🎉 Your token is now valid for 60 days!\n")
            else:
                print("   ⚠ No long-lived token returned")
                long_lived_token = None
        
    except requests.exceptions.RequestException as e:
        print(f"   ⚠ Threads API exchange failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"   Error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            except:
                print(f"   Response: {e.response.text[:200]}")
    
    # If exchange failed, use short-lived token
    if not long_lived_token:
        print("   ⚠ Could not exchange for long-lived token")
        print("   Using short-lived token (valid for 1 hour)")
        print("   You'll need to regenerate tokens periodically\n")
        long_lived_token = short_lived_token
        expires_in = 3600
    
    # Step 5: Verify token and get user info
    print("Step 4: Verifying token...")
    try:
        verify_url = f'https://graph.threads.net/v1.0/{user_id}'
        verify_params = {
            'access_token': long_lived_token,
            'fields': 'username'
        }
        verify_response = requests.get(verify_url, params=verify_params, timeout=30)
        verify_response.raise_for_status()
        user_info = verify_response.json()
        
        if 'username' in user_info:
            print(f"✓ Token verified! Authenticated as: @{user_info['username']}")
        else:
            print("✓ Token verified!")
            
    except requests.exceptions.RequestException as e:
        print(f"⚠ Warning: Could not verify token: {e}")
        print("   Token may still be valid, but verification failed")
    
    # Return token info
    result = {
        'access_token': long_lived_token,
        'user_id': user_id,
        'token_type': 'long-lived' if long_lived_token != short_lived_token else 'short-lived',
        'expires_in': expires_in
    }
    
    # Calculate expiration display
    if isinstance(expires_in, (int, float)) and expires_in > 0:
        days = int(expires_in) // 86400
        hours = (int(expires_in) % 86400) // 3600
        if days > 0:
            expires_display = f"{days} days, {hours} hours"
        else:
            expires_display = f"{hours} hours"
    else:
        expires_display = f"{expires_in} seconds"
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS! Your Threads API credentials:")
    print("=" * 60)
    print(f"\nAccess Token: {long_lived_token}")
    print(f"User ID: {user_id}")
    print(f"Token Type: {result['token_type']}")
    print(f"Expires In: {expires_display} ({expires_in} seconds)")
    print("\n" + "-" * 60)
    print("📝 Add these to your .env file:")
    print("-" * 60)
    print(f"THREADS_ACCESS_TOKEN={long_lived_token}")
    print(f"THREADS_USER_ID={user_id}")
    print("=" * 60 + "\n")
    
    return result


if __name__ == "__main__":
    try:
        get_threads_token()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

