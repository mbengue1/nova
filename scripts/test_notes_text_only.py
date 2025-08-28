"""
test script for notes app integration with text-only input

this script bypasses the audio components and directly tests the nova brain's
ability to process notes-related commands through text input.
"""
import sys
import os
import time

# add the project root to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import the brain directly
from core.brain import NovaBrain

def test_notes_with_text():
    """test notes functionality with direct text input"""
    print("\n=== testing notes app integration with text-only input ===\n")
    
    # initialize the brain
    brain = NovaBrain()
    
    # test commands
    test_commands = [
        "Create a new note called Project Ideas",
        "Create a new grocery shopping list",
        "Add milk, eggs, and bread to my grocery shopping list",
        "Add bananas and apples to my grocery shopping list",
        "Create a new to-do list",
        "Add 'Call John at 3pm' to my to-do list",
        "Add 'Finish report by Friday' to my to-do list",
        "Show me all my notes",
        "Find notes about grocery"
    ]
    
    # process each command
    for command in test_commands:
        print(f"\n> user: {command}")
        
        # process the command
        response = brain.process_input(command)
        
        # display the response
        print(f"< nova: {response}")
        
        # pause between commands
        time.sleep(1)
    
    print("\n=== test complete ===\n")

if __name__ == "__main__":
    test_notes_with_text()