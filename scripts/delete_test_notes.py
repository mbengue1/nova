"""
delete test notes created during development

this script deletes test notes created during development to clean up the notes app.
"""
import sys
import os
import subprocess

# add the project root to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def delete_note(note_title):
    """delete a note with the specified title"""
    # applescript to delete a note
    script = f'''
    tell application "Notes"
        tell account "iCloud"
            set noteList to notes whose name is "{note_title}"
            repeat with aNote in noteList
                delete aNote
            end repeat
        end tell
    end tell
    '''
    
    # run the applescript
    try:
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ deleted note: {note_title}")
        else:
            print(f"❌ failed to delete note: {note_title}")
            print(f"   error: {result.stderr}")
    except Exception as e:
        print(f"❌ error deleting note: {note_title}")
        print(f"   exception: {e}")

def main():
    """delete test notes"""
    print("\n=== deleting test notes ===\n")
    
    # list of notes to delete
    test_notes = [
        "Test Note",
        "Project Ideas",
        "Grocery Shopping List",
        "To-Do List",
        "Meeting Minutes",
        "My Computer",
        "Computer Parts",
        "Basketball Notes",
        "My Favorute Basketball Players",
        "Top 5 Basketball Players of All Time"
    ]
    
    # delete each note
    for note in test_notes:
        delete_note(note)
    
    print("\n=== cleanup complete ===\n")

if __name__ == "__main__":
    main()