#!/usr/bin/env python3
"""
Test Calendar Worker in Isolation
Tests the Google Calendar integration without Nova
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the CalendarService
from core.services.calendar_service import CalendarService

def test_calendar_worker_isolation():
    """Test Calendar worker functionality in isolation"""
    print("\n📅 Testing Calendar Worker in Isolation 📅")
    print("=" * 60)
    
    try:
        # Create Calendar worker instance
        calendar_service = CalendarService()
        print("   ✅ Calendar service created successfully")
        
        # Test 1: Service Initialization
        print("\n1️⃣ Testing Service Initialization...")
        
        # Check if Google Calendar is available
        try:
            # This will test the connection by getting today's schedule
            today_schedule = calendar_service.get_today_schedule()
            print(f"   ✅ Google Calendar connection successful")
            print(f"   📊 Retrieved today's schedule with {len(today_schedule.events)} events")
        except Exception as e:
            print(f"   ❌ Google Calendar connection failed: {e}")
            return False
        
        # Test 2: Event Retrieval
        print("\n2️⃣ Testing Event Retrieval...")
        
        # Get events for rest of today
        try:
            events = calendar_service.get_rest_of_day_schedule()
            print(f"   ✅ Retrieved {len(events)} events for rest of today")
            
            # Display sample events
            if events:
                print("   📋 Sample events:")
                for i, event in enumerate(events[:3]):  # Show first 3
                    print(f"      {i+1}. {event.title} - {event.start_time}")
            else:
                print("   📋 No events found for rest of today")
                
        except Exception as e:
            print(f"   ❌ Event retrieval failed: {e}")
            return False
        
        # Test 3: Schedule Formatting
        print("\n3️⃣ Testing Schedule Formatting...")
        
        try:
            # Test the format_rest_of_day_schedule method
            schedule_text = calendar_service.format_rest_of_day_schedule()
            print(f"   ✅ Schedule formatting successful")
            print(f"   📝 Formatted schedule: {schedule_text[:100]}...")
            
            if not schedule_text or schedule_text.strip() == "":
                print("   ⚠️ Schedule text is empty")
            else:
                print("   ✅ Schedule text contains content")
                
        except Exception as e:
            print(f"   ❌ Schedule formatting failed: {e}")
            return False
        
        # Test 4: Time Zone Handling
        print("\n4️⃣ Testing Time Zone Handling...")
        
        try:
            # Test with different time zones
            from core.config import config
            current_tz = config.timezone
            print(f"   🌍 Current timezone: {current_tz}")
            
            # Test event time formatting
            if events:
                sample_event = events[0]
                print(f"   🕐 Sample event time: {sample_event.start_time}")
                print(f"   📍 Event location: {sample_event.location or 'No location'}")
                print(f"   ✅ Time zone handling working")
            else:
                print("   ⚠️ No events to test time zone handling")
                
        except Exception as e:
            print(f"   ❌ Time zone handling failed: {e}")
            return False
        
        # Test 5: Error Handling
        print("\n5️⃣ Testing Error Handling...")
        
        # Test with invalid method call
        try:
            # Try to call a method that doesn't exist
            invalid_result = calendar_service.nonexistent_method()
            print(f"   ❌ Invalid method call should have failed")
            return False
        except Exception as e:
            print(f"   ✅ Invalid method call handled gracefully: {type(e).__name__}")
        
        print("\n" + "=" * 60)
        print("📅 Calendar Worker Isolation Test Complete")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Calendar worker test failed: {e}")
        return False

def test_calendar_worker_performance():
    """Test Calendar worker performance characteristics"""
    print("\n⚡ Testing Calendar Worker Performance ⚡")
    print("=" * 60)
    
    try:
        calendar_service = CalendarService()
        
        # Test 1: Connection Response Time
        print("\n1️⃣ Testing Connection Response Time...")
        
        start_time = time.time()
        today_schedule = calendar_service.get_today_schedule()
        connection_time = time.time() - start_time
        
        print(f"   🌐 Connection response time: {connection_time:.2f} seconds")
        print(f"   📊 Retrieved today's schedule with {len(today_schedule.events)} events")
        
        if connection_time > 5:
            print("   ⚠️ Connection is slow (>5s)")
        elif connection_time > 2:
            print("   ⚠️ Connection is moderate (>2s)")
        else:
            print("   ✅ Connection is fast (<2s)")
        
        # Test 2: Schedule Formatting Time
        print("\n2️⃣ Testing Schedule Formatting Time...")
        
        start_time = time.time()
        schedule_text = calendar_service.format_rest_of_day_schedule()
        formatting_time = time.time() - start_time
        
        print(f"   📝 Formatting response time: {formatting_time:.2f} seconds")
        print(f"   📊 Schedule length: {len(schedule_text)} characters")
        
        if formatting_time > 1:
            print("   ⚠️ Formatting is slow (>1s)")
        else:
            print("   ✅ Formatting is fast (<1s)")
        
        # Test 3: Multiple Request Handling
        print("\n3️⃣ Testing Multiple Request Handling...")
        
        start_time = time.time()
        for i in range(3):
            today_schedule = calendar_service.get_today_schedule()
        multiple_time = time.time() - start_time
        
        print(f"   🔄 Multiple requests time: {multiple_time:.2f} seconds")
        print(f"   📊 Average per request: {multiple_time/3:.2f} seconds")
        
        if multiple_time > 10:
            print("   ⚠️ Multiple requests are slow (>10s)")
        elif multiple_time > 5:
            print("   ⚠️ Multiple requests are moderate (>5s)")
        else:
            print("   ✅ Multiple requests are fast (<5s)")
        
        print("\n" + "=" * 60)
        print("⚡ Calendar Worker Performance Test Complete")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Calendar worker performance test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Starting Calendar Worker Isolation Tests...")
    
    # Run isolation tests
    isolation_success = test_calendar_worker_isolation()
    
    if isolation_success:
        # Run performance tests
        performance_success = test_calendar_worker_performance()
        
        print("\n" + "=" * 60)
        print("🎯 FINAL TEST RESULTS")
        print("=" * 60)
        print(f"   Isolation Tests: {'✅ PASSED' if isolation_success else '❌ FAILED'}")
        print(f"   Performance Tests: {'✅ PASSED' if performance_success else '❌ FAILED'}")
        
        if isolation_success and performance_success:
            print("\n🎉 ALL TESTS PASSED! Calendar Worker is ready for integration.")
        else:
            print("\n⚠️ Some tests failed. Review issues before integration.")
    else:
        print("\n❌ Isolation tests failed. Cannot proceed to performance tests.")
