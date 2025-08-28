#!/usr/bin/env python3
"""
Test script to debug import issues
"""
import sys
import os

# Add the parent directory to the path so we can import the core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test various imports"""
    print("===== Testing Imports =====")
    
    # Test 1: Basic imports
    try:
        from core.config import config
        print("✅ core.config imported successfully")
    except Exception as e:
        print(f"❌ core.config import failed: {e}")
    
    # Test 2: Google Calendar service import
    try:
        from core.services.google_calendar_service import GoogleCalendarService
        print("✅ GoogleCalendarService imported successfully")
        
        # Try to instantiate it
        try:
            service = GoogleCalendarService()
            print(f"✅ GoogleCalendarService instantiated successfully")
            print(f"   Service available: {service.is_available()}")
            print(f"   Service object: {service.service}")
        except Exception as e:
            print(f"❌ GoogleCalendarService instantiation failed: {e}")
            
    except Exception as e:
        print(f"❌ GoogleCalendarService import failed: {e}")
    
    # Test 3: Calendar service import
    try:
        from core.services.calendar_service import CalendarService
        print("✅ CalendarService imported successfully")
        
        # Try to instantiate it
        try:
            service = CalendarService()
            print(f"✅ CalendarService instantiated successfully")
            print(f"   Google Calendar: {service.google_calendar}")
            if service.google_calendar:
                print(f"   Google Calendar available: {service.google_calendar.is_available()}")
        except Exception as e:
            print(f"❌ CalendarService instantiation failed: {e}")
            
    except Exception as e:
        print(f"❌ CalendarService import failed: {e}")

if __name__ == "__main__":
    test_imports()
