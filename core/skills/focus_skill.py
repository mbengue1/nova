"""
Focus Mode Skill for Nova

This skill allows Nova to control macOS Focus modes through natural language commands.
It handles commands related to Do Not Disturb and other focus modes.
"""
import re
import logging
from typing import Optional, Tuple, Dict, Any

from core.services.app_control_service import AppControlService

class FocusSkill:
    """Skill for handling focus mode commands"""
    
    def __init__(self, app_control_service: AppControlService):
        """
        Initialize the focus skill
        
        Args:
            app_control_service: The app control service to use for controlling focus modes
        """
        self.logger = logging.getLogger("nova.skills.focus")
        self.app_control = app_control_service
        
        # Patterns for matching focus mode commands
        self.patterns = {
            'enable_dnd': re.compile(r'^(?:.*)?(?:enable|turn on|activate|set).*(?:do not disturb|dnd)(?:\s|$|\.)', re.IGNORECASE),
            'disable_dnd': re.compile(r'^(?:.*)?(?:disable|turn off|deactivate).*(?:do not disturb|dnd)(?:\s|$|\.)', re.IGNORECASE),
            'toggle_dnd': re.compile(r'^(?:.*)?(?:toggle|switch).*(?:do not disturb|dnd)(?:\s|$|\.)', re.IGNORECASE),
            'get_focus': re.compile(r'^(?:.*)?(?:what(?:\'s)?|which|get|check|is).*(?:my|the|if)?.*(?:focus mode|current focus|do not disturb|dnd).*(?:active|enabled|on|current|now|mode)?(?:\s|$|\.)', re.IGNORECASE),
            'set_focus': re.compile(r'^(?:.*)?(?:set|change|switch).*(?:my|the).*focus.*(?:to|mode)(?:\s|$|\.)', re.IGNORECASE),
            'private_mode': re.compile(r'^(?:.*)?(?:set|enable|turn on).*(?:private mode|privacy mode|home to private)(?:\s|$|\.)', re.IGNORECASE),
            'disable_all_focus': re.compile(r'^(?:.*)?(?:disable|turn off|deactivate).*(?:all|every).*(?:focus|mode)(?:\s|$|\.)', re.IGNORECASE),
            'set_dnd_mode': re.compile(r'^(?:.*)?(?:set).*(?:home|mode|mac|macbook).*(?:to).*(?:do not disturb|dnd)(?:\s|$|\.)', re.IGNORECASE),
        }
        
        # Map of focus mode names for recognition
        self.focus_modes = {
            'do not disturb': 'Do Not Disturb',
            'dnd': 'Do Not Disturb',
            'work': 'Work',
            'personal': 'Personal',
            'sleep': 'Sleep',
            'driving': 'Driving',
            'fitness': 'Fitness',
            'gaming': 'Gaming',
            'mindfulness': 'Mindfulness',
            'reading': 'Reading',
            'none': 'None',
        }
    
    def matches(self, text: str) -> bool:
        """
        Check if the given text matches any focus mode command patterns
        
        Args:
            text: The text to check
            
        Returns:
            bool: True if the text matches a focus mode command pattern, False otherwise
        """
        return any(pattern.search(text) for pattern in self.patterns.values())
    
    def process(self, text: str) -> str:
        """
        Process a focus mode command
        
        Args:
            text: The command text to process
            
        Returns:
            str: The response to the command
        """
        self.logger.info(f"Processing focus mode command: {text}")
        
        # Check for enable DND command
        if self.patterns['enable_dnd'].search(text):
            success, message = self.app_control.set_do_not_disturb(True)
            return "I've turned on Do Not Disturb mode." if success else f"Sorry, I couldn't turn on Do Not Disturb: {message}"
        
        # Check for specific "set home/mode to DND" command
        if self.patterns['set_dnd_mode'].search(text):
            success, message = self.app_control.set_do_not_disturb(True)
            return "I've set your home to private mode." if success else f"Sorry, I couldn't set private mode: {message}"
        
        # Check for disable DND command
        if self.patterns['disable_dnd'].search(text):
            success, message = self.app_control.set_do_not_disturb(False)
            return "I've turned off Do Not Disturb mode." if success else f"Sorry, I couldn't turn off Do Not Disturb: {message}"
        
        # Check for disable all focus modes command
        if self.patterns['disable_all_focus'].search(text):
            success, message = self.app_control.set_do_not_disturb(False)
            return "I've turned off all focus modes." if success else f"Sorry, I couldn't turn off focus modes: {message}"
        
        # Check for toggle DND command
        if self.patterns['toggle_dnd'].search(text):
            success, message = self.app_control.toggle_do_not_disturb()
            return f"I've toggled Do Not Disturb mode." if success else f"Sorry, I couldn't toggle Do Not Disturb: {message}"
        
        # Check for get focus command
        if self.patterns['get_focus'].search(text):
            success, mode = self.app_control.get_current_focus_mode()
            if success:
                if not mode or mode.lower() == "none":
                    return "You don't have any focus mode active right now."
                return f"Your current focus mode is {mode}."
            else:
                return f"Sorry, I couldn't check your focus mode: {mode}"
        
        # Check for set focus command
        if self.patterns['set_focus'].search(text) or self.patterns['private_mode'].search(text):
            # Extract the focus mode from the command
            focus_mode = self._extract_focus_mode(text)
            
            if focus_mode:
                success, message = self.app_control.set_focus_mode(focus_mode)
                return f"I've set your focus mode to {focus_mode}." if success else f"Sorry, I couldn't set the focus mode: {message}"
            else:
                return "Sorry, I couldn't determine which focus mode you want to set."
        
        # Default response if no specific command matched
        return "Sorry, I don't understand that focus mode command."
    
    def _extract_focus_mode(self, text: str) -> Optional[str]:
        """
        Extract the focus mode from the command text
        
        Args:
            text: The command text to extract the focus mode from
            
        Returns:
            Optional[str]: The extracted focus mode, or None if no focus mode was found
        """
        # Special case for private mode
        if self.patterns['private_mode'].search(text):
            return "Do Not Disturb"
        
        # Check for each focus mode in the text
        text_lower = text.lower()
        for key, mode in self.focus_modes.items():
            if key in text_lower:
                return mode
        
        return None
