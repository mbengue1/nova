#!/usr/bin/env python3
"""
Test script for Nova's personalization
Simulates conversation without audio input/output
"""
import os
import sys
import time
from datetime import datetime

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Nova components
from core.config import config
from core.brain.router import NovaBrain

def simulate_conversation():
    """Simulate a conversation with Nova"""
    print("\n" + "="*60)
    print("🌟 Nova Personalization Test")
    print("="*60)
    
    # Initialize brain
    brain = NovaBrain()
    
    # Get current time for greeting
    now = datetime.now()
    hour = now.hour
    
    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 17:
        greeting = "Good afternoon"
    elif 17 <= hour < 21:
        greeting = "Good evening"
    else:
        greeting = "Good night"
    
    # Simulate Nova's welcome message
    welcome_message = f"{greeting}, {config.user_title}! Welcome home. How may I serve you today?"
    print(f"🤖 Nova: {welcome_message}")
    
    # Show enhanced persona details
    print("\n" + "-"*60)
    print("📋 Enhanced Persona Details:")
    print("-"*60)
    
    # Get personal context
    context = config.get_personal_context()
    
    # Display today's schedule
    print(f"📅 Today is {context['current_day']}, {context['current_time']}")
    
    if context['todays_classes']:
        print("\n📚 Today's Classes:")
        for course in context['todays_classes']:
            print(f"  • {course['name']} ({course['code']}) at {course['time']} in {course['location']}")
            print(f"    Professor: {course['professor']}")
    else:
        print("\n📚 No classes scheduled for today.")
    
    if context['todays_activities']:
        print("\n🏀 Today's Activities:")
        for activity in context['todays_activities']:
            print(f"  • {activity['name']} at {activity['time']} in {activity['location']}")
    
    # Start conversation loop
    print("\n" + "-"*60)
    print("💬 Conversation Simulator")
    print("-"*60)
    print("Type your messages to Nova (type 'exit' to quit)")
    
    while True:
        # Get user input
        user_input = input("\n👤 You: ")
        
        if user_input.lower() in ['exit', 'quit', 'goodbye']:
            print("\n🤖 Nova: Goodbye, Sir! It was a pleasure serving you.")
            break
        
        # Process through brain
        print("\n🧠 Processing...")
        response = brain.process_input(user_input)
        
        # Display Nova's response
        print(f"🤖 Nova: {response}")
    
    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)

if __name__ == "__main__":
    simulate_conversation()
