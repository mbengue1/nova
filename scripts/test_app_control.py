#!/usr/bin/env python3
"""
Test script for Nova's app control functionality
Tests opening applications without using voice
"""
import os
import sys
import time

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Nova components
from core.brain.router import NovaBrain

def test_app_control():
    """Test app control functionality"""
    print("\n" + "="*60)
    print("🌟 Nova App Control Test")
    print("="*60)
    
    # Initialize brain
    brain = NovaBrain()
    
    # Test commands to open various applications
    test_commands = [
        "Open VS Code",
        "Launch Chrome",
        "Open Calculator",
        "Start Safari",
        "Open Finder"
    ]
    
    for command in test_commands:
        print(f"\n👤 Testing: '{command}'")
        response = brain.process_input(command)
        print(f"🤖 Nova: {response}")
        time.sleep(1)  # Give time to see the app open
    
    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)

if __name__ == "__main__":
    test_app_control()
