#!/usr/bin/env python3
"""
Test script to verify Nova is reading REAL calendar data

This script tests the actual calendar service to ensure it's pulling
real data from Google Calendar and personal_config.py, not just
placeholder information.
"""
import sys
import os
import logging
from datetime import datetime, date

# Add the parent directory to the path so we can import the core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_real_calendar_data():
    """Test that Nova is reading real calendar data"""
    print("===== Testing Real Calendar Data =====")
    
    try:
        from core.services.calendar_service import CalendarService
        
        # Initialize the calendar service
        calendar_service = CalendarService()
        
        # Get today's date
        today = date.today()
        print(f"\n📅 Today's date: {today.strftime('%A, %B %d, %Y')}")
        
        # Test 1: Get today's schedule
        print("\n🔍 Test 1: Getting today's schedule...")
        today_schedule = calendar_service.get_today_schedule()
        print(f"Found {len(today_schedule.events)} events for today")
        
        if today_schedule.events:
            print("Today's events:")
            for event in today_schedule.events:
                print(f"  • {event.title} at {event.format_time()}")
                if event.location:
                    print(f"    Location: {event.location}")
                print(f"    Type: {event.event_type}")
        else:
            print("No events scheduled for today")
        
        # Test 2: Get rest of day schedule
        print("\n🔍 Test 2: Getting rest of day schedule...")
        rest_of_day = calendar_service.get_rest_of_day_schedule()
        print(f"Found {len(rest_of_day)} upcoming events for the rest of today")
        
        if rest_of_day:
            print("Upcoming events for the rest of today:")
            for event in rest_of_day:
                print(f"  • {event.title} at {event.format_time()}")
                if event.location:
                    print(f"    Location: {event.location}")
        else:
            print("No upcoming events for the rest of today")
        
        # Test 3: Format the rest of day schedule (what Nova actually says)
        print("\n🔍 Test 3: What Nova would actually say...")
        formatted_message = calendar_service.format_rest_of_day_schedule()
        print(f"Nova would say: \"{formatted_message}\"")
        
        # Test 4: Check if Google Calendar is available
        print("\n🔍 Test 4: Google Calendar availability...")
        if hasattr(calendar_service, 'google_calendar'):
            if calendar_service.google_calendar and calendar_service.google_calendar.is_available():
                print("✅ Google Calendar is available and connected")
                
                # Try to get some Google Calendar events
                try:
                    google_events = calendar_service.google_calendar.get_calendar_events(today)
                    print(f"Found {len(google_events)} Google Calendar events for today")
                    for event in google_events:
                        print(f"  • {event.get('title', 'Untitled')} at {event.get('start_time', 'No time')}")
                except Exception as e:
                    print(f"⚠️ Error getting Google Calendar events: {e}")
            else:
                print("❌ Google Calendar is not available")
        else:
            print("❌ Google Calendar service not found")
        
        # Test 5: Check personal config data
        print("\n🔍 Test 5: Personal config data...")
        from core.personal_config import COURSES, ACTIVITIES
        
        print(f"Personal config has {len(COURSES)} courses and {len(ACTIVITIES)} activities")
        
        # Check if today's courses are in the schedule
        weekday = today.strftime("%A")
        print(f"Today is {weekday}")
        
        today_courses = [course for course in COURSES if weekday in course.get("days", [])]
        print(f"Personal config shows {len(today_courses)} courses for {weekday}:")
        for course in today_courses:
            print(f"  • {course['name']} ({course['code']}) at {course['time']}")
        
        print("\n===== Calendar Data Testing Complete =====")
        
    except Exception as e:
        print(f"❌ Error testing calendar data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_calendar_data()
