"""
Test script for the Notes app integration with Nova

This script tests the ability to:
1. Create new notes
2. Add content to existing notes
3. Find notes by title

Usage:
    python -m scripts.test_notes_app
"""
import sys
import os
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the app control service
from core.services.app_control_service import AppControlService
from core.skills.notes_skill import NotesSkill

def test_app_control_service():
    """Test the AppControlService directly"""
    print("\n=== Testing AppControlService ===")
    
    app_control = AppControlService()
    
    # Test creating a note
    print("\nTesting create_note...")
    success, message = app_control.create_note("Test Note", "This is a test note created by Nova.")
    print(f"Create note result: {success}, {message}")
    
    # Wait a moment for the note to be created
    time.sleep(1)
    
    # Test adding to the note
    print("\nTesting add_to_note...")
    success, message = app_control.add_to_note("Test Note", "Adding more content to the test note.")
    print(f"Add to note result: {success}, {message}")
    
    # Test listing notes
    print("\nTesting list_notes...")
    success, notes = app_control.list_notes()
    if success:
        print(f"Found {len(notes)} notes:")
        for note in notes[:10]:  # Show up to 10 notes
            print(f"  - {note}")
        if len(notes) > 10:
            print(f"  ... and {len(notes) - 10} more")
    else:
        print("Failed to list notes")
    
    # Test finding notes
    print("\nTesting find_note...")
    success, notes = app_control.find_note("Test")
    if success:
        print(f"Found {len(notes)} notes matching 'Test':")
        for note in notes:
            print(f"  - {note}")
    else:
        print("Failed to find notes")

def test_notes_skill():
    """Test the NotesSkill with various queries"""
    print("\n=== Testing NotesSkill ===")
    
    notes_skill = NotesSkill()
    
    # Test queries
    test_queries = [
        "Create a new note called Meeting Minutes",
        "Create a new grocery list",
        "Add milk, eggs, and bread to my grocery shopping list",
        "Find my notes about meetings",
        "Show me all my notes",
        "Create a note for project ideas with content 'AI assistant improvements'",
        "Add 'Call John at 3pm' to my To-Do List"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        response = notes_skill.handle_query(query)
        print(f"Response: {response}")
        
        # Wait a moment between queries
        time.sleep(1)

def main():
    """Main test function"""
    print("=== Notes App Integration Test ===")
    
    # Test the AppControlService directly
    test_app_control_service()
    
    # Test the NotesSkill
    test_notes_skill()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
