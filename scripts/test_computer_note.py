"""
test script for creating a computer parts note

this script directly tests the notesskill's ability to extract content
from a query about computer parts.
"""
import sys
import os

# add the project root to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import the notesskill
from core.skills.notes_skill import NotesSkill

def main():
    """test creating a computer parts note"""
    print("\n=== testing computer parts note creation ===\n")
    
    # initialize the notesskill
    notes_skill = NotesSkill()
    
    # test query with "it should contain" pattern
    query = "can you make a new note of the items i need for my computer, it should contain a gpu, and monitor and finally a disk"
    
    print(f"query: '{query}'")
    
    # extract content from the query
    content = notes_skill._extract_note_content(query)
    print(f"extracted content: '{content}'")
    
    # handle the query
    response = notes_skill.handle_query(query)
    print(f"response: '{response}'")
    
    print("\n=== test complete ===\n")

if __name__ == "__main__":
    main()