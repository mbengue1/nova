"""
nova app control service

this module provides functionality for controlling applications beyond just opening them.
currently supports:
- creating new notes in the notes app
- adding content to existing notes
- controlling macOS focus modes
- more app control features can be added in the future

the service uses applescript via osascript to interact with macos applications.
"""
import subprocess
import os
import logging
from typing import Optional, Dict, Any, List, Tuple

from core.services.focus_controller import FocusController

class AppControlService:
    """service for controlling macos applications via applescript"""
    
    def __init__(self):
        """initialize the app control service"""
        self.logger = logging.getLogger("nova.app_control")
        self.focus_controller = FocusController()
    
    def create_note(self, title: str, content: Optional[str] = None) -> Tuple[bool, str]:
        """
        create a new note in the notes app with optional content
        
        args:
            title: the title for the new note
            content: optional content for the note
            
        returns:
            tuple[bool, str]: success status and message
        """
        try:
            # escape quotes in title and content for applescript
            title_escaped = title.replace('"', '\\"')
            content_escaped = content.replace('"', '\\"') if content else ""
            
            # applescript to create a new note
            script = f'''
            tell application "Notes"
                activate
                tell account "iCloud"
                    make new note with properties {{name:"{title_escaped}"}}
                end tell
            end tell
            '''
            
            # run the applescript
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to create note: {result.stderr}")
                return False, f"Failed to create note: {result.stderr}"
            
            # if content was provided, add it to the note
            if content:
                # format the content properly with a title and items
                formatted_content = f"# {title}\n\n"
                
                # format the content as a bulleted list if it's a comma-separated list
                if ',' in content and not content.startswith('-') and not content.startswith('•'):
                    items = [item.strip() for item in content.split(',')]
                    formatted_content += '\n'.join([f"• {item}" for item in items if item])
                else:
                    # if not comma-separated, just use the content as is
                    formatted_content += content
                
                content_escaped = formatted_content.replace('"', '\\"')
                
                script_content = f'''
                tell application "Notes"
                    tell account "iCloud"
                        set noteList to notes whose name is "{title_escaped}"
                        if length of noteList > 0 then
                            set targetNote to item 1 of noteList
                            set body of targetNote to "{content_escaped}"
                        end if
                    end tell
                end tell
                '''
                
                result_content = subprocess.run(['osascript', '-e', script_content], 
                                             capture_output=True, text=True)
                
                if result_content.returncode != 0:
                    self.logger.error(f"Failed to add content to note: {result_content.stderr}")
                    return True, f"Note created, but failed to add content: {result_content.stderr}"
            
            return True, f"Successfully created note: {title}"
            
        except Exception as e:
            self.logger.error(f"Error creating note: {str(e)}")
            return False, f"Error creating note: {str(e)}"
    
    def add_to_note(self, title: str, content: str) -> Tuple[bool, str]:
        """
        add content to an existing note in the notes app
        
        args:
            title: the title of the existing note
            content: the content to add to the note
            
        returns:
            tuple[bool, str]: success status and message
        """
        try:
            # format the content properly
            formatted_content = ""
            
            # format the content as a bulleted list if it's a comma-separated list
            if ',' in content and not content.startswith('-') and not content.startswith('•'):
                items = [item.strip() for item in content.split(',')]
                formatted_content = '\n'.join([f"• {item}" for item in items if item])
                content = formatted_content
            
            # escape quotes in title and content for applescript
            title_escaped = title.replace('"', '\\"')
            content_escaped = content.replace('"', '\\"')
            
            # applescript to append content to an existing note
            script = f'''
            tell application "Notes"
                tell account "iCloud"
                    set noteList to notes whose name is "{title_escaped}"
                    if length of noteList > 0 then
                        set targetNote to item 1 of noteList
                        set body of targetNote to (body of targetNote) & "\\n{content_escaped}"
                        return true
                    else
                        return false
                    end if
                end tell
            end tell
            '''
            
            # run the applescript
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to add content to note: {result.stderr}")
                return False, f"Failed to add content to note: {result.stderr}"
            
            # check if the note was found
            if result.stdout.strip() == "false":
                # note doesn't exist, create it
                return self.create_note(title, content)
            
            return True, f"Successfully added content to note: {title}"
            
        except Exception as e:
            self.logger.error(f"Error adding content to note: {str(e)}")
            return False, f"Error adding content to note: {str(e)}"
    
    def list_notes(self) -> Tuple[bool, List[str]]:
        """
        list all notes in the notes app
        
        returns:
            tuple[bool, list[str]]: success status and list of note titles
        """
        try:
            # applescript to list all notes
            script = '''
            tell application "Notes"
                tell account "iCloud"
                    set noteList to name of every note
                    return noteList
                end tell
            end tell
            '''
            
            # run the applescript
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to list notes: {result.stderr}")
                return False, []
            
            # parse the output
            notes = result.stdout.strip().split(", ")
            return True, notes
            
        except Exception as e:
            self.logger.error(f"Error listing notes: {str(e)}")
            return False, []
    
    def find_note(self, search_term: str) -> Tuple[bool, List[str]]:
        """
        find notes matching a search term
        
        args:
            search_term: the term to search for in note titles
            
        returns:
            tuple[bool, list[str]]: success status and list of matching note titles
        """
        try:
            # escape quotes in search term for applescript
            search_term_escaped = search_term.replace('"', '\\"')
            
            # applescript to find notes matching the search term
            script = f'''
            tell application "Notes"
                tell account "iCloud"
                    set matchingNotes to name of every note where name contains "{search_term_escaped}"
                    return matchingNotes
                end tell
            end tell
            '''
            
            # run the applescript
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to find notes: {result.stderr}")
                return False, []
            
            # parse the output
            notes = result.stdout.strip().split(", ")
            if notes == [""]:  # no matches
                return True, []
            return True, notes
            
        except Exception as e:
            self.logger.error(f"Error finding notes: {str(e)}")
            return False, []
            
    def set_focus_mode(self, mode: str) -> Tuple[bool, str]:
        """
        Set a specific focus mode (Do Not Disturb, Work, Personal, etc.)
        
        Args:
            mode: The name of the focus mode to set
            
        Returns:
            tuple[bool, str]: Success status and message
        """
        return self.focus_controller.set_focus_mode(mode)
        
    def get_current_focus_mode(self) -> Tuple[bool, str]:
        """
        Get the currently active focus mode
        
        Returns:
            tuple[bool, str]: Success status and current focus mode or error message
        """
        return self.focus_controller.get_current_focus_mode()
        
    def toggle_do_not_disturb(self) -> Tuple[bool, str]:
        """
        Toggle Do Not Disturb mode on/off
        
        Returns:
            tuple[bool, str]: Success status and message
        """
        return self.focus_controller.toggle_do_not_disturb()
        
    def set_do_not_disturb(self, enabled: bool) -> Tuple[bool, str]:
        """
        Set Do Not Disturb mode to a specific state
        
        Args:
            enabled: True to enable Do Not Disturb, False to disable
            
        Returns:
            tuple[bool, str]: Success status and message
        """
        return self.focus_controller.set_do_not_disturb(enabled)