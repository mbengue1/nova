#!/usr/bin/env python3
"""
Test script for Time-Based Focus Mode Controller

This script tests the TimeBasedFocusController class to verify it can properly
apply focus mode rules based on time of day.
"""
import sys
import os
import time
import datetime
import logging

# Add the parent directory to the path so we can import the core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import the TimeBasedFocusController
from core.services.time_based_focus import TimeBasedFocusController
from core.services.focus_controller import FocusController

def test_time_based_focus():
    """Test the TimeBasedFocusController functionality"""
    print("\n===== Testing Time-Based Focus Controller =====\n")
    
    # Create a FocusController instance
    focus_controller = FocusController()
    
    # Create a TimeBasedFocusController instance
    time_controller = TimeBasedFocusController(focus_controller)
    
    # Test 1: List default rules
    print("Test 1: Listing default rules...")
    rules = time_controller.get_all_rules()
    for rule in rules:
        print(f"- {rule['name']}: {rule['description']}")
    
    # Test 2: Check active rules based on current time
    print("\nTest 2: Checking active rules based on current time...")
    current_hour = datetime.datetime.now().hour
    print(f"Current hour: {current_hour}")
    
    active_rules = time_controller.get_active_rules()
    if active_rules:
        print(f"Active rules: {', '.join(active_rules)}")
    else:
        print("No active rules at this time")
    
    # Test 3: Add a custom rule for testing
    print("\nTest 3: Adding a custom rule...")
    
    # Rule that's always active for testing
    time_controller.add_rule(
        name="test_rule",
        condition=lambda: True,
        action=lambda: print("Test rule action executed"),
        description="Test rule that's always active"
    )
    
    # Check if the new rule is active
    active_rules = time_controller.get_active_rules()
    print(f"Active rules after adding test rule: {', '.join(active_rules)}")
    
    # Test 4: Start the controller and let it run briefly
    print("\nTest 4: Starting the controller...")
    time_controller.start()
    
    # Wait for a moment to allow the controller to check rules
    print("Waiting for 3 seconds...")
    time.sleep(3)
    
    # Stop the controller
    print("Stopping the controller...")
    time_controller.stop()
    
    print("\n===== Time-Based Focus Controller Testing Complete =====")

if __name__ == "__main__":
    test_time_based_focus()
