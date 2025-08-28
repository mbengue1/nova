"""
verify note formatting in the notes app

this script creates a note with specific formatting and then displays how it would appear.
"""
import sys
import os
import subprocess

# add the project root to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import the app control service
from core.services.app_control_service import AppControlService

def main():
    """create a test note and verify its formatting"""
    print("\n=== testing note formatting ===\n")
    
    # initialize the app control service
    app_control = AppControlService()
    
    # define the note title
    title = "Computer Parts"
    
    # define the note content
    content = "gpu, monitor, disk, keyboard, mouse"
    
    # create the note
    print(f"creating note '{title}' with content: '{content}'")
    success, message = app_control.create_note(title, content)
    
    if success:
        print(f"✅ successfully created note: '{title}'")
        
        # show how the note would be formatted
        formatted_content = f"# {title}\n\n"
        
        # format the content as a bulleted list
        items = [item.strip() for item in content.split(',')]
        formatted_content += '\n'.join([f"• {item}" for item in items if item])
        
        print("\nnote formatting preview:")
        print("-" * 40)
        print(formatted_content)
        print("-" * 40)
    else:
        print(f"❌ failed to create note: {message}")
    
    print("\n=== test complete ===\n")

if __name__ == "__main__":
    main()