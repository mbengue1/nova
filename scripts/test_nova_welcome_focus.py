#!/usr/bin/env python3
"""
Test script for Nova's Focus Mode and Welcome Greeting

This script tests Nova's welcome greeting with focus mode integration.
"""
import sys
import os
import logging
import datetime

# Add the parent directory to the path so we can import the core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import the necessary classes
from core.services.focus_controller import FocusController
from core.services.time_based_focus import TimeBasedFocusController

def simulate_greeting(hour):
    """Simulate Nova's greeting at a specific hour"""
    print(f"\n===== Simulating greeting at {hour}:00 =====")
    
    # Create focus controller
    focus_controller = FocusController()
    
    # Create time-based focus controller
    time_controller = TimeBasedFocusController(focus_controller)
    
    # Check if it's evening (after 4 PM)
    is_evening = hour >= 16
    
    # Generate appropriate greeting based on time
    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    
    # Base welcome message
    welcome_message = f"{greeting}, sir! Welcome home."
    
    # Add focus mode information for evening hours
    if is_evening:
        welcome_message += " I've set your home to private mode."
        
        # Check if Do Not Disturb would be enabled
        print("Checking if Do Not Disturb would be enabled...")
        active_rules = time_controller.get_active_rules()
        print(f"Active rules at {hour}:00: {', '.join(active_rules) if active_rules else 'None'}")
        
        # Simulate enabling Do Not Disturb
        print("Simulating enabling Do Not Disturb...")
    
    # Complete the greeting
    welcome_message += " How may I serve you today?"
    
    print(f"Nova would say: \"{welcome_message}\"")

def test_welcome_greetings():
    """Test Nova's welcome greeting at different times of day"""
    print("\n===== Testing Nova Welcome Greeting with Focus Mode =====\n")
    
    # Test morning greeting (8 AM)
    simulate_greeting(8)
    
    # Test afternoon greeting (2 PM)
    simulate_greeting(14)
    
    # Test evening greeting (6 PM)
    simulate_greeting(18)
    
    # Test late night greeting (11 PM)
    simulate_greeting(23)
    
    print("\n===== Welcome Greeting Testing Complete =====")

if __name__ == "__main__":
    test_welcome_greetings()
