#!/usr/bin/env python3
"""
Debug Google Calendar Authentication

This is a simplified script to debug Google Calendar authentication issues.
"""
import os
import sys
import json
import pickle
from pathlib import Path
import webbrowser

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
except ImportError:
    print("⚠️  Required Google packages not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                         "google-api-python-client", "google-auth-httplib2", "google-auth-oauthlib"])
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials

# Define the scopes needed for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def debug_auth():
    """Debug Google Calendar authentication"""
    print("\n🔍 Debugging Google Calendar authentication...\n")
    
    # Use the credentials file directly
    # Look for any client_secret file in the credentials directory
    credentials_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'credentials')
    client_secret_files = [f for f in os.listdir(credentials_dir) if f.startswith('client_secret') and f.endswith('.json')]
    if not client_secret_files:
        print("❌ No client_secret*.json file found in credentials directory")
        return False
    
    credentials_path = os.path.join(credentials_dir, client_secret_files[0])
    print(f"✅ Using credentials file: {credentials_path}")
    token_path = os.path.join(credentials_dir, 'google_token.pickle')
    
    # Check if credentials file exists
    if not os.path.exists(credentials_path):
        print(f"⚠️  Credentials file not found at: {credentials_path}")
        return False
    
    # Print credentials file content for debugging
    try:
        with open(credentials_path, 'r') as f:
            creds_data = json.load(f)
            print("📄 Credentials file structure:")
            if "installed" in creds_data:
                print("  - Type: Installed application")
                print(f"  - Client ID: {creds_data['installed']['client_id'][:15]}...")
                print(f"  - Project ID: {creds_data['installed']['project_id']}")
            elif "web" in creds_data:
                print("  - Type: Web application")
                print(f"  - Client ID: {creds_data['web']['client_id'][:15]}...")
                print(f"  - Project ID: {creds_data['web']['project_id']}")
    except Exception as e:
        print(f"⚠️  Error reading credentials file: {e}")
        return False
    
    # Try authentication with more debugging info
    print("\n🔑 Attempting authentication with more debug info...")
    
    try:
        # Enable more verbose OAuth logging
        import logging
        logging.basicConfig(level=logging.DEBUG)
        
        # Create the flow with more debugging options
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_path, 
            SCOPES,
            redirect_uri_trailing_slash=True
        )
        
        # Run the local server with more debugging
        print("\n🌐 Opening browser for authentication...")
        print("⚠️  IMPORTANT: If you see an 'unverified app' warning, click 'Continue'")
        print("⚠️  IMPORTANT: Make sure to log in with the same Google account that owns the project")
        
        # Use a specific port for debugging
        creds = flow.run_local_server(port=8080)
        
        # Save the credentials for future use
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
        
        print("✅ Authentication successful!")
        return True
    except Exception as e:
        print(f"⚠️  Authentication error: {e}")
        print("\n🔍 Debugging suggestions:")
        print("  1. Make sure you've completed the OAuth consent screen setup")
        print("  2. Add your email as a test user in the OAuth consent screen")
        print("  3. Make sure the Google Calendar API is enabled")
        print("  4. Try creating new OAuth credentials in the Google Cloud Console")
        return False

if __name__ == "__main__":
    success = debug_auth()
    if success:
        print("\n🎉 Authentication successful! You can now use Google Calendar with Nova.")
    else:
        print("\n⚠️  Authentication failed. Please review the debugging suggestions above.")
