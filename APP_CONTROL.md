# Nova App Control System

This document outlines Nova's app control capabilities, which allow it to not just open applications but also interact with them to perform specific tasks.

## Current Capabilities

### 1. Application Opening

Nova can open various macOS applications using voice commands. Examples:
- "Nova, open Chrome"
- "Nova, launch Calculator"
- "Nova, start Safari"

### 2. Notes App Integration

Nova can now create and manage notes in the Apple Notes app:

#### Creating Notes
- "Nova, create a new note called Meeting Minutes"
- "Nova, make a new grocery shopping list"
- "Nova, start a new note for project ideas"

#### Adding to Notes
- "Nova, add milk, eggs, and bread to my grocery shopping list"
- "Nova, add 'Call John at 3pm' to my To-Do List"
- "Nova, update my meeting notes with 'Action items for marketing team'"

#### Finding Notes
- "Nova, find my notes about meetings"
- "Nova, show me all my notes"
- "Nova, search for grocery in my notes"

## Technical Implementation

### App Control Service

The `AppControlService` class in `core/services/app_control_service.py` provides the core functionality for controlling applications. It uses AppleScript via Python's `subprocess` module to interact with macOS applications.

Key methods:
- `create_note(title, content)`: Creates a new note with the specified title and optional content
- `add_to_note(title, content)`: Adds content to an existing note
- `list_notes()`: Lists all notes in the Notes app
- `find_note(search_term)`: Finds notes matching a search term

### Notes Skill

The `NotesSkill` class in `core/skills/notes_skill.py` handles natural language processing for notes-related commands. It:
1. Recognizes notes-related intents using regex patterns
2. Extracts relevant information (note titles, content, search terms)
3. Calls the appropriate `AppControlService` methods
4. Generates user-friendly responses

### Integration with Nova's Brain

The `NovaBrain` router in `core/brain/router.py` has been updated to:
1. Recognize notes-related commands using regex patterns
2. Route these commands to the `NotesSkill`
3. Return the response to the user

## Testing

You can test the Notes app integration using:
```bash
python -m scripts.test_notes_app
```

This script tests:
- Creating new notes
- Adding content to existing notes
- Finding notes by title
- Processing natural language queries

## Future Enhancements

Planned enhancements for app control include:
1. Support for more applications (Calendar, Reminders, Mail, etc.)
2. More advanced interactions (e.g., creating calendar events, setting reminders)
3. Better natural language understanding for complex commands
4. Error handling and recovery for failed interactions
5. User feedback mechanisms for confirming actions

## Limitations

Current limitations include:
1. Requires macOS (uses AppleScript)
2. Limited to the Notes app for now
3. May require specific note titles for reliable operation
4. Cannot handle complex formatting or attachments
