#!/usr/bin/env python3
"""
Test script for Nova Smart Scheduling System
Tests different time scenarios to ensure scheduling works correctly
"""

import sys
import os
from datetime import datetime, time

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.scheduling.class_scheduler import ClassScheduler
from core.scheduling.schedule_validator import ScheduleValidator

def test_scheduling_scenarios():
    """Test different scheduling scenarios"""
    print("🧪 Testing Nova Smart Scheduling System")
    print("=" * 60)
    
    # Initialize scheduler
    scheduler = ClassScheduler('config/class_schedule.yaml')
    
    if not scheduler.is_configured():
        print("❌ Class scheduler not properly configured")
        return False
    
    print("✅ Class scheduler initialized successfully")
    print(f"   Buffer time: {scheduler.buffer_minutes} minutes")
    print(f"   University hours: {scheduler.university_hours.get('enabled', False)}")
    print()
    
    # Test scenarios
    test_cases = [
        {
            "name": "Current Time",
            "description": "Test with actual current time",
            "test_func": lambda: scheduler.should_nova_run_now()
        },
        {
            "name": "Tuesday 11:00 AM",
            "description": "During History of Islam class (should be silent)",
            "test_func": lambda: test_specific_time(scheduler, 1, 11, 0)
        },
        {
            "name": "Monday 2:30 PM", 
            "description": "During Film History class (should be silent)",
            "test_func": lambda: test_specific_time(scheduler, 0, 14, 30)
        },
        {
            "name": "Friday 3:00 PM",
            "description": "No classes scheduled (should be available)",
            "test_func": lambda: test_specific_time(scheduler, 4, 15, 0)
        },
        {
            "name": "Saturday 2:00 PM",
            "description": "Weekend (should be available)",
            "test_func": lambda: test_specific_time(scheduler, 5, 14, 0)
        },
        {
            "name": "Tuesday 3:30 PM",
            "description": "During Data Mining class (should be silent)",
            "test_func": lambda: test_specific_time(scheduler, 1, 15, 30)
        },
        {
            "name": "Wednesday 4:00 PM",
            "description": "During Computer Organization class (should be silent)",
            "test_func": lambda: test_specific_time(scheduler, 2, 16, 0)
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"🕐 Testing: {test_case['name']}")
        print(f"   Description: {test_case['description']}")
        
        try:
            should_run, reason = test_case['test_func']()
            status = "✅ PASS" if should_run == get_expected_result(test_case['name']) else "❌ FAIL"
            
            print(f"   Result: {should_run} ({reason})")
            print(f"   Status: {status}")
            print()
            
            results.append({
                "name": test_case['name'],
                "passed": should_run == get_expected_result(test_case['name']),
                "result": should_run,
                "reason": reason
            })
            
        except Exception as e:
            print(f"   Error: {e}")
            print(f"   Status: ❌ ERROR")
            print()
            
            results.append({
                "name": test_case['name'],
                "passed": False,
                "result": None,
                "reason": f"Error: {e}"
            })
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{status} {result['name']}: {result['reason']}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Smart scheduling is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the scheduling logic.")
        return False

def test_specific_time(scheduler, weekday, hour, minute):
    """Test scheduler with a specific time"""
    # Create a mock datetime for testing
    test_datetime = datetime(2024, 1, 1 + weekday, hour, minute)
    
    # Test the scheduler by directly checking the logic
    current_time = test_datetime.time()
    current_weekday = test_datetime.weekday()
    
    # Check if Nova behavior is enabled
    if not scheduler.nova_behavior.get('respect_class_schedule', True):
        return True, "Class schedule protection disabled"
    
    # Check university hours first
    if scheduler.university_hours.get('enabled', False):
        if not scheduler._is_within_university_hours(current_time, current_weekday):
            return False, f"Outside university hours ({current_time.strftime('%H:%M')})"
    
    # Check class schedule
    if current_weekday in scheduler.schedule_data.get('class_schedule', {}):
        classes = scheduler.schedule_data['class_schedule'][current_weekday]
        
        for class_info in classes:
            if scheduler._is_time_in_class_period(current_time, class_info):
                return False, f"During class: {class_info.get('name', 'Unknown')}"
    
    return True, "Available time - no classes scheduled"

def get_expected_result(test_name):
    """Get expected result for each test case"""
    expected_results = {
        "Tuesday 11:00 AM": False,      # During class - should be silent
        "Monday 2:30 PM": False,        # During class - should be silent  
        "Friday 3:00 PM": True,         # No classes - should be available
        "Saturday 2:00 PM": True,       # Weekend - should be available
        "Tuesday 3:30 PM": False,       # During class - should be silent
        "Wednesday 4:00 PM": False      # During class - should be silent
    }
    
    return expected_results.get(test_name, True)

def test_schedule_validation():
    """Test schedule validation"""
    print("🔍 Testing Schedule Validation")
    print("=" * 40)
    
    config_path = 'config/class_schedule.yaml'
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    is_valid, errors = ScheduleValidator.validate_yaml_file(config_path)
    
    if is_valid:
        print("✅ Configuration file is valid!")
        return True
    else:
        print("❌ Configuration validation failed:")
        for error in errors:
            print(f"   - {error}")
        return False

def main():
    """Main test function"""
    print("🚀 Nova Smart Scheduling Test Suite")
    print("=" * 60)
    print()
    
    # Test 1: Schedule validation
    validation_passed = test_schedule_validation()
    print()
    
    if not validation_passed:
        print("❌ Schedule validation failed. Cannot proceed with scheduling tests.")
        return False
    
    # Test 2: Scheduling scenarios
    scheduling_passed = test_scheduling_scenarios()
    
    print()
    print("🎯 Final Results:")
    print(f"   Schedule Validation: {'✅ PASS' if validation_passed else '❌ FAIL'}")
    print(f"   Scheduling Logic: {'✅ PASS' if scheduling_passed else '❌ FAIL'}")
    
    return validation_passed and scheduling_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
