#!/usr/bin/env python3
"""
Simple Google Calendar Authentication

This script provides a simplified approach to Google Calendar authentication.
"""
import os
import sys
import json
import pickle
import webbrowser
from pathlib import Path

try:
    import google.auth
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                         "google-api-python-client", "google-auth-httplib2", "google-auth-oauthlib"])
    import google.auth
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

# Define the scopes needed for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def simple_auth():
    """Simple Google Calendar authentication"""
    print("\n🔑 Simple Google Calendar Authentication\n")
    
    # Paths for credentials and token
    credentials_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'credentials')
    # Look for any client_secret file in the credentials directory
    client_secret_files = [f for f in os.listdir(credentials_dir) if f.startswith('client_secret') and f.endswith('.json')]
    if not client_secret_files:
        print("❌ No client_secret*.json file found in credentials directory")
        return False
    
    credentials_file = os.path.join(credentials_dir, client_secret_files[0])
    print(f"✅ Using credentials file: {credentials_file}")
    token_file = os.path.join(credentials_dir, 'google_token.pickle')
    
    # Check if credentials file exists
    if not os.path.exists(credentials_file):
        print(f"⚠️  Credentials file not found at: {credentials_file}")
        return False
    
    creds = None
    
    # Check if token file exists and is valid
    if os.path.exists(token_file):
        print("📄 Found existing token file, trying to use it...")
        try:
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
                
            if creds and creds.valid:
                print("✅ Existing token is valid!")
            elif creds and creds.expired and creds.refresh_token:
                print("🔄 Token expired, refreshing...")
                creds.refresh(Request())
                print("✅ Token refreshed successfully!")
            else:
                print("⚠️  Token invalid or expired without refresh token")
                creds = None
        except Exception as e:
            print(f"⚠️  Error loading token: {e}")
            creds = None
    
    # If no valid credentials, start the OAuth flow
    if not creds:
        print("🔄 Starting new authentication flow...")
        
        # Enable OAuth out-of-band mode (manual copy-paste of code)
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # For development only
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            
            # Try different authentication approaches
            print("\n📋 Choose authentication method:")
            print("1. Browser-based authentication (recommended)")
            print("2. Console-based authentication (if browser doesn't work)")
            choice = input("Enter choice (1 or 2): ").strip()
            
            if choice == "2":
                # Console-based authentication with proper redirect
                auth_url, _ = flow.authorization_url(
                    prompt='consent',
                    access_type='offline',
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # This is the special redirect URI for OOB flow
                )
                print(f"\n🔗 Open this URL in your browser:\n{auth_url}\n")
                print("After authorizing, you'll get a code. Copy it and paste it here:")
                code = input("Enter the authorization code: ").strip()
                flow.fetch_token(code=code, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
                creds = flow.credentials
            else:
                # Browser-based authentication (default)
                print("\n🌐 Opening browser for authentication...")
                print("⚠️  If you see an 'unverified app' warning, click 'Continue'")
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for future use
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
                print("✅ Token saved successfully!")
        except Exception as e:
            print(f"⚠️  Authentication error: {e}")
            print("\n🔍 Debugging suggestions:")
            print("  1. Make sure you've completed the OAuth consent screen setup")
            print("  2. Add your email as a test user in the OAuth consent screen")
            print("  3. Make sure the Google Calendar API is enabled")
            return False
    
    # Test the connection
    print("\n🧪 Testing connection to Google Calendar...")
    try:
        service = build('calendar', 'v3', credentials=creds)
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        if not calendars:
            print("✅ Connection successful! No calendars found.")
        else:
            print(f"✅ Connection successful! Found {len(calendars)} calendars:")
            for calendar in calendars:
                print(f"  • {calendar['summary']}")
        
        return True
    except Exception as e:
        print(f"⚠️  Error connecting to Google Calendar: {e}")
        return False

if __name__ == "__main__":
    success = simple_auth()
    if success:
        print("\n🎉 Authentication successful! You can now use Google Calendar with Nova.")
    else:
        print("\n⚠️  Authentication failed. Please review the debugging suggestions above.")
