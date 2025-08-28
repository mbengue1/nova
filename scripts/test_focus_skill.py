#!/usr/bin/env python3
"""
Test script for Focus Skill

This script tests the FocusSkill class to verify it can properly
process natural language commands related to focus modes.
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
from core.services.app_control_service import AppControlService
from core.skills.focus_skill import FocusSkill

def test_focus_skill():
    """Test the FocusSkill functionality"""
    print("\n===== Testing Focus Skill =====\n")
    
    # Create the necessary services and skill
    app_control = AppControlService()
    focus_skill = FocusSkill(app_control)
    
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
        
        # Check if the skill matches the command
        matches = focus_skill.matches(command)
        print(f"Matches: {matches}")
        
        if matches:
            # Process the command
            response = focus_skill.process(command)
            print(f"Response: \"{response}\"")
        else:
            print("Skill does not match this command")
        
        print()
    
    print("===== Focus Skill Testing Complete =====")

if __name__ == "__main__":
    test_focus_skill()
