#!/usr/bin/env python3
"""
Google Calendar Setup Script for Nova

This script helps users set up Google Calendar integration with Nova:
1. Guides the user through creating a Google Cloud project
2. Assists with enabling the Google Calendar API
3. Helps create OAuth credentials
4. Tests the connection to Google Calendar
5. Saves the credentials in the right location

Usage:
    python scripts/setup_google_calendar.py
"""
import os
import sys
import json
import pickle
from pathlib import Path
import webbrowser
import time

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

def create_credentials_dir():
    """Create credentials directory if it doesn't exist"""
    credentials_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'credentials')
    os.makedirs(credentials_dir, exist_ok=True)
    return credentials_dir

def setup_google_calendar():
    """Set up Google Calendar integration"""
    print("\n🔄 Setting up Google Calendar integration for Nova...\n")
    
    # Step 1: Create credentials directory
    credentials_dir = create_credentials_dir()
    credentials_file = os.path.join(credentials_dir, 'google_credentials.json')
    token_file = os.path.join(credentials_dir, 'google_token.pickle')
    
    # Step 2: Guide user to create credentials
    print("📝 To set up Google Calendar integration, you need to:")
    print("  1. Create a Google Cloud project")
    print("  2. Enable the Google Calendar API")
    print("  3. Create OAuth 2.0 credentials")
    print("  4. Download the credentials JSON file")
    print("\n🌐 Would you like to open the Google Cloud Console to set this up? (y/n)")
    
    if input().lower() == 'y':
        print("\n🔗 Opening Google Cloud Console...")
        webbrowser.open("https://console.cloud.google.com/apis/dashboard")
        
        print("\n📋 Follow these steps:")
        print("  1. Create a new project or select an existing one")
        print("  2. Go to 'APIs & Services' > 'Library'")
        print("  3. Search for 'Google Calendar API' and enable it")
        print("  4. Go to 'APIs & Services' > 'Credentials'")
        print("  5. Click 'Create Credentials' > 'OAuth client ID'")
        print("  6. Set Application type to 'Desktop app'")
        print("  7. Name it 'Nova Assistant'")
        print("  8. Click 'Create'")
        print("  9. Download the JSON file by clicking the download icon")
        
        print("\n⬇️  Once downloaded, please enter the path to the credentials JSON file:")
        creds_path = input().strip()
        
        # Handle ~ in path
        if creds_path.startswith('~'):
            creds_path = os.path.expanduser(creds_path)
        
        # Check if file exists
        if not os.path.exists(creds_path):
            print(f"⚠️  File not found: {creds_path}")
            return False
        
        # Copy credentials to the right location
        try:
            with open(creds_path, 'r') as f:
                creds_data = json.load(f)
            
            with open(credentials_file, 'w') as f:
                json.dump(creds_data, f)
            
            print(f"✅ Credentials saved to {credentials_file}")
        except Exception as e:
            print(f"⚠️  Error saving credentials: {e}")
            return False
    else:
        print("\n⚠️  You need to set up Google Cloud credentials to use Google Calendar integration.")
        print("   You can run this script again later to complete setup.")
        return False
    
    # Step 3: Authenticate with Google Calendar API
    print("\n🔑 Now we'll authenticate with Google Calendar...")
    
    try:
        # Create the flow from client secrets file
        flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save the credentials for future use
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
        
        print("✅ Authentication successful!")
    except Exception as e:
        print(f"⚠️  Error authenticating with Google Calendar: {e}")
        return False
    
    # Step 4: Test the connection
    print("\n🧪 Testing connection to Google Calendar...")
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        # Get upcoming events
        now = time.strftime('%Y-%m-%dT%H:%M:%S%z')
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=5,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        
        if not events:
            print("✅ Connection successful! No upcoming events found.")
        else:
            print(f"✅ Connection successful! Found {len(events)} upcoming events.")
            print("\n📅 Next few events:")
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"  • {start}: {event['summary']}")
    except Exception as e:
        print(f"⚠️  Error connecting to Google Calendar: {e}")
        return False
    
    print("\n🎉 Google Calendar integration is now set up for Nova!")
    print("   Nova will now be able to access your calendar events.")
    return True

if __name__ == "__main__":
    setup_google_calendar()
