#!/usr/bin/env python3
"""
Test Calendar Response Formatting

This script tests the calendar response formatting without requiring audio input.
It simulates a user asking about their calendar and shows how Nova would respond.
"""
import os
import sys
import datetime

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.services.calendar_service import CalendarService
    from core.services.google_calendar_service import GoogleCalendarService
    from core.brain.router import NovaBrain
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

def test_calendar_responses():
    """Test calendar response formatting"""
    print("\n🧪 Testing Calendar Response Formatting\n")
    
    # Initialize the brain
    brain = NovaBrain()
    
    # Test queries
    test_queries = [
        "What's on my schedule today?",
        "What do I have tomorrow?",
        "What's my schedule for this week?",
        "Do I have any classes on Friday?",
        "What's on my calendar for Monday?",
        "What's my next meeting?",
        "What's my busiest day this week?"
    ]
    
    # Process each query
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        print("🤖 Nova's response:")
        
        # Process the query through the brain
        response = brain.process_input(query)
        
        # Print the response
        print(f"   {response}")
        print("-" * 80)
    
    print("\n✅ Calendar response formatting test complete")

if __name__ == "__main__":
    test_calendar_responses()
