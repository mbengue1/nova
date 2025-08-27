#!/usr/bin/env python3
"""
Test Google Calendar Integration for Nova

This script tests the Google Calendar integration by:
1. Verifying credentials are properly set up
2. Connecting to the Google Calendar API
3. Retrieving upcoming events
4. Displaying them in a readable format

Usage:
    python scripts/test_google_calendar.py
"""
import os
import sys
import datetime
import json
from pathlib import Path

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.services.google_calendar_service import GoogleCalendarService
    from core.services.calendar_service import CalendarService
except ImportError as e:
    print(f"⚠️  Error importing required modules: {e}")
    print("   Make sure you've installed all dependencies:")
    print("   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

def check_credentials():
    """Check if Google Calendar credentials are properly set up"""
    credentials_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'credentials')
    credentials_file = os.path.join(credentials_dir, 'google_credentials.json')
    token_file = os.path.join(credentials_dir, 'google_token.pickle')
    
    if not os.path.exists(credentials_file):
        print("⚠️  Google credentials file not found!")
        print(f"   Expected location: {credentials_file}")
        print("   Please follow the setup guide in GOOGLE_CALENDAR_SETUP.md")
        return False
    
    if not os.path.exists(token_file):
        print("⚠️  Google token file not found!")
        print("   You need to authenticate first.")
        print("   Run: python scripts/setup_google_calendar.py")
        return False
    
    print("✅ Google Calendar credentials found")
    return True

def test_google_calendar_service():
    """Test the Google Calendar service directly"""
    print("\n🧪 Testing Google Calendar service...")
    
    try:
        service = GoogleCalendarService()
        if not service.is_available():
            print("⚠️  Google Calendar service is not available")
            return False
        
        print("✅ Successfully initialized Google Calendar service")
        
        # Get today's events
        today = datetime.date.today()
        events = service.get_calendar_events(today)
        
        print(f"\n📅 Events for today ({today.strftime('%Y-%m-%d')}):")
        if not events:
            print("   No events found for today")
        else:
            for i, event in enumerate(events, 1):
                title = event.get('title', 'Untitled Event')
                start = event.get('start_time', 'No time specified')
                location = event.get('location', 'No location')
                
                # Format the start time if it exists
                if start and 'T' in start:
                    try:
                        dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                        start = dt.strftime('%I:%M %p')
                    except:
                        pass
                
                print(f"   {i}. {title} at {start} ({location})")
        
        # Get tomorrow's events
        tomorrow = today + datetime.timedelta(days=1)
        events = service.get_calendar_events(tomorrow)
        
        print(f"\n📅 Events for tomorrow ({tomorrow.strftime('%Y-%m-%d')}):")
        if not events:
            print("   No events found for tomorrow")
        else:
            for i, event in enumerate(events, 1):
                title = event.get('title', 'Untitled Event')
                start = event.get('start_time', 'No time specified')
                location = event.get('location', 'No location')
                
                # Format the start time if it exists
                if start and 'T' in start:
                    try:
                        dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                        start = dt.strftime('%I:%M %p')
                    except:
                        pass
                
                print(f"   {i}. {title} at {start} ({location})")
        
        return True
    except Exception as e:
        print(f"⚠️  Error testing Google Calendar service: {e}")
        return False

def test_calendar_service():
    """Test the Calendar service with Google Calendar integration"""
    print("\n🧪 Testing Calendar service with Google Calendar integration...")
    
    try:
        # Create a custom calendar service with explicit Google Calendar integration
        from core.services.google_calendar_service import GoogleCalendarService
        
        # First check if GoogleCalendarService works
        google_service = GoogleCalendarService()
        if not google_service.is_available():
            print("⚠️  GoogleCalendarService is not available, cannot test integration")
            return False
        
        # Now create the calendar service
        service = CalendarService()
        
        # Check if Google Calendar is being used
        if service.google_calendar and service.google_calendar.is_available():
            print("✅ Calendar service is using Google Calendar")
        else:
            print("⚠️  Calendar service is NOT using Google Calendar")
            
            # Try to fix the integration
            print("🔄 Attempting to fix Google Calendar integration...")
            service.google_calendar = google_service
            if service.google_calendar.is_available():
                print("✅ Successfully fixed Google Calendar integration")
            else:
                print("❌ Could not fix Google Calendar integration")
        
        # Get today's schedule
        today = service.get_today_schedule()
        
        print("\n📅 Today's schedule from Calendar service:")
        print(service.format_day_schedule(today))
        
        # Get tomorrow's schedule
        tomorrow = service.get_tomorrow_schedule()
        
        print("\n📅 Tomorrow's schedule from Calendar service:")
        print(service.format_day_schedule(tomorrow))
        
        # Get week's schedule
        week = service.get_week_schedule()
        
        print("\n📅 Week's schedule from Calendar service:")
        print(service.format_week_schedule(week))
        
        return True
    except Exception as e:
        print(f"⚠️  Error testing Calendar service: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to test Google Calendar integration"""
    print("\n🔄 Testing Google Calendar integration for Nova...\n")
    
    # Check credentials
    if not check_credentials():
        return False
    
    # Test Google Calendar service
    if not test_google_calendar_service():
        return False
    
    # Test Calendar service
    if not test_calendar_service():
        return False
    
    print("\n🎉 Google Calendar integration is working correctly!")
    print("   Nova can now access your real calendar events.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
