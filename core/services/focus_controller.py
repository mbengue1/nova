"""
Nova Focus Mode Controller

This module provides functionality for controlling macOS Focus modes.
It allows Nova to toggle Do Not Disturb and other Focus modes through
macOS Shortcuts and AppleScript.
"""
import subprocess
import logging
from typing import Tuple, Optional

class FocusController:
    """Service for controlling macOS Focus modes"""
    
    def __init__(self):
        """Initialize the focus controller service"""
        self.logger = logging.getLogger("nova.focus_control")
    
    def set_focus_mode(self, mode: str) -> Tuple[bool, str]:
        """
        Set a specific focus mode (Do Not Disturb, Work, Personal, etc.)
        
        Args:
            mode: The name of the focus mode to set
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        # First try using Shortcuts
        shortcut_name = f"Enable {mode}"
        success, message = self._run_shortcut(shortcut_name)
        
        if success:
            return True, f"Successfully set focus mode to {mode}"
        
        # If Shortcuts fails, log the error
        self.logger.warning(f"Failed to set focus mode using Shortcuts: {message}")
        self.logger.info("Attempting to use AppleScript fallback")
        
        # Fallback to AppleScript for Do Not Disturb
        if mode.lower() == "do not disturb":
            return self.set_do_not_disturb(True)
        
        return False, f"Failed to set focus mode to {mode}: {message}"
    
    def get_current_focus_mode(self) -> Tuple[bool, str]:
        """
        Get the currently active focus mode
        
        Returns:
            Tuple[bool, str]: Success status and current focus mode or error message
        """
        # Try using Shortcuts first
        success, message = self._run_shortcut("Get Current Focus Mode")
        
        if success:
            return True, message.strip()
        
        # Fallback to checking Do Not Disturb status
        self.logger.warning(f"Failed to get current focus mode using Shortcuts: {message}")
        self.logger.info("Checking Do Not Disturb status only")
        
        try:
            # AppleScript to check Do Not Disturb status
            script = '''
            tell application "System Events"
                tell process "Control Center"
                    set dndEnabled to exists (first menu bar item whose title contains "Focus" and value of attribute "AXMenuItemMarkChar" is "✓")
                    if dndEnabled then
                        return "Do Not Disturb"
                    else
                        return "None"
                    end if
                end tell
            end tell
            '''
            
            result = self._run_applescript(script)
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, f"Failed to get focus mode: {result.stderr}"
                
        except Exception as e:
            self.logger.error(f"Error getting focus mode: {str(e)}")
            return False, f"Error getting focus mode: {str(e)}"
    
    def toggle_do_not_disturb(self) -> Tuple[bool, str]:
        """
        Toggle Do Not Disturb mode on/off
        
        Returns:
            Tuple[bool, str]: Success status and message
        """
        # Check current status first
        success, current_mode = self.get_current_focus_mode()
        
        if not success:
            return False, f"Failed to toggle Do Not Disturb: {current_mode}"
        
        # Toggle based on current status
        if "do not disturb" in current_mode.lower():
            return self.set_do_not_disturb(False)
        else:
            return self.set_do_not_disturb(True)
    
    def set_do_not_disturb(self, enabled: bool) -> Tuple[bool, str]:
        """
        Set Do Not Disturb mode to a specific state
        
        Args:
            enabled: True to enable Do Not Disturb, False to disable
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        # First try using Shortcuts
        shortcut_name = "Enable Do Not Disturb" if enabled else "Disable Do Not Disturb"
        success, message = self._run_shortcut(shortcut_name)
        
        if success:
            status = "enabled" if enabled else "disabled"
            return True, f"Successfully {status} Do Not Disturb mode"
        
        # If Shortcuts fails, try AppleScript
        self.logger.warning(f"Failed to set Do Not Disturb using Shortcuts: {message}")
        self.logger.info("Attempting to use AppleScript fallback")
        
        try:
            # AppleScript to toggle Do Not Disturb
            script = f'''
            tell application "System Events"
                tell application process "Control Center"
                    click menu bar item "Control Center" of menu bar 1
                    delay 0.5
                    click button "Focus" of group 1 of window "Control Center"
                    delay 0.5
                    click checkbox 1 of window "Control Center"
                end tell
            end tell
            '''
            
            # Check current status first to determine if we need to toggle
            success, current_mode = self.get_current_focus_mode()
            
            if not success:
                return False, f"Failed to set Do Not Disturb: {current_mode}"
            
            is_dnd_active = "do not disturb" in current_mode.lower()
            
            # Only toggle if the current state doesn't match the desired state
            if (enabled and not is_dnd_active) or (not enabled and is_dnd_active):
                result = self._run_applescript(script)
                
                if result.returncode == 0:
                    status = "enabled" if enabled else "disabled"
                    return True, f"Successfully {status} Do Not Disturb mode"
                else:
                    return False, f"Failed to set Do Not Disturb: {result.stderr}"
            else:
                # Already in the desired state
                status = "enabled" if enabled else "disabled"
                return True, f"Do Not Disturb is already {status}"
                
        except Exception as e:
            self.logger.error(f"Error setting Do Not Disturb: {str(e)}")
            return False, f"Error setting Do Not Disturb: {str(e)}"
    
    def _run_applescript(self, script: str) -> subprocess.CompletedProcess:
        """
        Run an AppleScript command
        
        Args:
            script: The AppleScript to run
            
        Returns:
            subprocess.CompletedProcess: The result of the command
        """
        return subprocess.run(['osascript', '-e', script], 
                           capture_output=True, text=True)
    
    def _run_shortcut(self, shortcut_name: str) -> Tuple[bool, str]:
        """
        Run a macOS Shortcut by name
        
        Args:
            shortcut_name: The name of the shortcut to run
            
        Returns:
            Tuple[bool, str]: Success status and message or output
        """
        try:
            # Escape quotes in shortcut name
            shortcut_name_escaped = shortcut_name.replace('"', '\\"')
            
            # Run the shortcut
            result = subprocess.run(['shortcuts', 'run', shortcut_name_escaped], 
                                 capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, f"Shortcut error: {result.stderr}"
                
        except Exception as e:
            return False, f"Error running shortcut: {str(e)}"
