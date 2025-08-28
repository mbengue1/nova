#!/usr/bin/env python3
"""
Test script for Focus Mode commands

This script tests various focus mode commands to ensure they're properly recognized.
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
from core.skills.focus_skill import FocusSkill
from core.services.app_control_service import AppControlService

def test_focus_commands():
    """Test various focus mode commands"""
    print("\n===== Testing Focus Mode Commands =====\n")
    
    # Create the necessary services and skill
    app_control = AppControlService()
    focus_skill = FocusSkill(app_control)
    
    # Test commands to process
    test_commands = [
        "Turn on Do Not Disturb",
        "Set Do Not Disturb",
        "Set home to private mode",
        "Set my home to Do Not Disturb",
        "Set my Mac to Do Not Disturb",
        "Set my mode to Do Not Disturb",
        "Enable private mode",
        "Turn off Do Not Disturb",
        "Check if DND is active",
        "What's my current focus mode?",
        "Toggle Do Not Disturb mode",
        "Set my focus mode to Work",
        "Disable all focus modes"
    ]
    
    # Process each command and print the result
    for command in test_commands:
        print(f"Command: \"{command}\"")
        
        # Check if the skill matches the command
        matches = focus_skill.matches(command)
        print(f"Matches: {matches}")
        
        if matches:
            # Process the command (but don't actually execute it)
            print(f"Would respond with: \"{focus_skill.process(command)}\"")
        else:
            print("Skill does not match this command")
        
        print()
    
    print("===== Focus Commands Testing Complete =====")

if __name__ == "__main__":
    test_focus_commands()
