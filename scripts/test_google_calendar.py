#!/usr/bin/env python3
"""
Test script to debug Google Calendar authentication

This script tests the Google Calendar service to see why it's not connecting.
"""
import sys
import os
import logging

# Add the parent directory to the path so we can import the core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_google_calendar_auth():
    """Test Google Calendar authentication"""
    print("===== Testing Google Calendar Authentication =====")
    
    try:
        from core.services.google_calendar_service import GoogleCalendarService
        
        print("\n🔍 Initializing Google Calendar service...")
        service = GoogleCalendarService()
        
        print(f"\n🔍 Service available: {service.is_available()}")
        print(f"🔍 Service object: {service.service}")
        
        if service.service:
            print("✅ Google Calendar service is working!")
            
            # Try to get today's events
            print("\n🔍 Testing calendar access...")
            try:
                events = service.get_today_events()
                print(f"Found {len(events)} events for today")
                for event in events:
                    print(f"  • {event.get('title', 'Untitled')}")
            except Exception as e:
                print(f"❌ Error getting events: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("❌ Google Calendar service failed to initialize")
            
            # Check credentials
            print("\n🔍 Checking credentials...")
            credentials_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'credentials')
            print(f"Credentials directory: {credentials_dir}")
            
            if os.path.exists(credentials_dir):
                files = os.listdir(credentials_dir)
                print(f"Files in credentials directory: {files}")
                
                # Check specific files
                token_file = os.path.join(credentials_dir, 'google_token.pickle')
                creds_file = os.path.join(credentials_dir, 'google_credentials.json')
                
                print(f"Token file exists: {os.path.exists(token_file)}")
                print(f"Credentials file exists: {os.path.exists(creds_file)}")
                
                if os.path.exists(token_file):
                    print(f"Token file size: {os.path.getsize(token_file)} bytes")
                if os.path.exists(creds_file):
                    print(f"Credentials file size: {os.path.getsize(creds_file)} bytes")
            else:
                print("❌ Credentials directory does not exist")
        
    except Exception as e:
        print(f"❌ Error testing Google Calendar: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_google_calendar_auth()
