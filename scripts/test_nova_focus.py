#!/usr/bin/env python3
"""
Test script for Nova's Focus Mode integration

This script tests the integration of Focus Mode control with Nova's brain.
"""
import sys
import os
import logging

# Add the parent directory to the path so we can import the core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import the necessary classes
from core.brain.router import NovaBrain

def test_nova_focus_integration():
    """Test the Focus Mode integration with Nova's brain"""
    print("\n===== Testing Nova Focus Mode Integration =====\n")
    
    # Create a NovaBrain instance
    brain = NovaBrain()
    
    # Test commands to process
    test_commands = [
        "What's my current focus mode?",
        "Turn on Do Not Disturb",
        "Check if DND is active",
        "Turn off Do Not Disturb",
        "Toggle Do Not Disturb mode",
        "Set my focus mode to Work",
        "Set home to private mode",
        "Disable all focus modes",
        "This is not a focus mode command"
    ]
    
    # Process each command and print the result
    for command in test_commands:
        print(f"Command: \"{command}\"")
        
        # Process the command
        response = brain.process_input(command)
        print(f"Response: \"{response}\"\n")
    
    print("===== Nova Focus Mode Integration Testing Complete =====")

if __name__ == "__main__":
    test_nova_focus_integration()
