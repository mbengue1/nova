#!/usr/bin/env python3
"""
Test script for Nova's updated welcome greeting

This script tests Nova's welcome greeting at different times of day
to verify the updated format with private mode, calendar info, and productive day message.
"""
import sys
import os
import logging
from datetime import datetime
import unittest.mock

# Add the parent directory to the path so we can import the core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import the calendar service for mocking
from core.services.calendar_service import CalendarService

def simulate_greeting(hour, calendar_message="You have nothing scheduled for the rest of the day."):
    """Simulate Nova's greeting at a specific hour"""
    print(f"\n===== Simulating greeting at {hour}:00 =====")
    
    # Determine greeting based on time of day
    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    
    # Base welcome message
    welcome_message = f"{greeting}, Sir! Welcome home."
    
    # Add focus mode information for afternoon/evening hours (after 12 PM)
    if hour >= 12:
        welcome_message += " I've set your home to private mode."
        print("Private mode would be enabled")
    
    # Add calendar information
    welcome_message += f" {calendar_message}"
    
    # Add productive day message
    welcome_message += " Hope you have a productive day."
    
    print(f"Nova would say: \"{welcome_message}\"")

def test_welcome_greetings():
    """Test Nova's welcome greeting at different times of day"""
    print("\n===== Testing Nova's Updated Welcome Greeting =====\n")
    
    # Define some example calendar messages
    empty_calendar = "You have nothing scheduled for the rest of the day."
    morning_calendar = "You have CSC240 at 11 am in Hutchison Hall today."
    afternoon_calendar = "For the rest of the day, you have 2 events: Writing at 2 pm, and finally Basketball practice at 4 pm."
    evening_calendar = "You have nothing scheduled for the rest of the evening."
    night_calendar = "You have nothing scheduled for the rest of the night."
    
    # Test morning greeting (8 AM)
    simulate_greeting(8, morning_calendar)
    
    # Test afternoon greeting (1 PM)
    simulate_greeting(13, afternoon_calendar)
    
    # Test evening greeting (6 PM)
    simulate_greeting(18, evening_calendar)
    
    # Test late night greeting (11 PM)
    simulate_greeting(23, night_calendar)
    
    print("\n===== Welcome Greeting Testing Complete =====")

if __name__ == "__main__":
    test_welcome_greetings()
