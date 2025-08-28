"""
Test script for creating a basketball players note

This script directly uses the AppControlService to create a note
about the top 5 basketball players of all time.
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the app control service
from core.services.app_control_service import AppControlService

def main():
    """Create a note about top 5 basketball players"""
    print("\n=== Creating Basketball Players Note ===\n")
    
    # Initialize the app control service
    app_control = AppControlService()
    
    # Define the note title
    title = "Top 5 Basketball Players of All Time"
    
    # Define the note content
    content = """# Top 5 Basketball Players of All Time

1. **Michael Jordan** - Six NBA championships, five MVP awards, and widely considered the greatest of all time.

2. **LeBron James** - Four NBA championships across three different franchises, four MVP awards, and remarkable longevity at the top level.

3. **Kareem Abdul-Jabbar** - Six NBA championships, six MVP awards, and the NBA's all-time leading scorer for nearly 40 years.

4. **Magic Johnson** - Five NBA championships, three MVP awards, and revolutionized the point guard position with his size and passing ability.

5. **Kobe Bryant** - Five NBA championships, one MVP award, and known for his scoring ability and "Mamba Mentality."

This list was created by Nova for Sir on request.
"""
    
    # Create the note
    print(f"Creating note: '{title}'")
    success, message = app_control.create_note(title, content)
    
    if success:
        print(f"\n✅ Successfully created note: '{title}'")
        print("\nNote content:")
        print("-" * 40)
        print(content)
        print("-" * 40)
    else:
        print(f"\n❌ Failed to create note: {message}")
    
    print("\n=== Done ===\n")

if __name__ == "__main__":
    main()
