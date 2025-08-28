"""
Time-Based Focus Mode Controller for Nova

This module provides functionality for automatically changing Focus modes
based on time of day and other contextual factors.
"""
import time
import datetime
import logging
import threading
from typing import Dict, Any, Optional, Callable

from core.services.focus_controller import FocusController

class TimeBasedFocusController:
    """Controller for time-based focus mode changes"""
    
    def __init__(self, focus_controller: Optional[FocusController] = None):
        """
        Initialize the time-based focus controller
        
        Args:
            focus_controller: The focus controller to use, or None to create a new one
        """
        self.logger = logging.getLogger("nova.time_based_focus")
        self.focus_controller = focus_controller or FocusController()
        self.running = False
        self.thread = None
        self.rules = []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Set up default time-based rules"""
        # Rule for evening/night (after 4 PM) - Enable Do Not Disturb
        self.add_rule(
            name="evening_dnd",
            condition=lambda: datetime.datetime.now().hour >= 16,
            action=lambda: self.focus_controller.set_do_not_disturb(True),
            description="Enable Do Not Disturb during evening hours (after 4 PM)"
        )
        
        # Keep Do Not Disturb on at all times (user preference)
        self.add_rule(
            name="maintain_dnd",
            condition=lambda: True,
            action=lambda: self.focus_controller.set_do_not_disturb(True),
            description="Maintain Do Not Disturb mode at all times (user preference)"
        )
    
    def add_rule(self, name: str, condition: Callable[[], bool], action: Callable[[], Any], description: str = ""):
        """
        Add a time-based rule
        
        Args:
            name: The name of the rule
            condition: A function that returns True when the rule should be applied
            action: The action to take when the condition is met
            description: A description of the rule
        """
        self.rules.append({
            "name": name,
            "condition": condition,
            "action": action,
            "description": description,
            "last_triggered": None
        })
        self.logger.info(f"Added time-based focus rule: {name} - {description}")
    
    def start(self):
        """Start the time-based focus controller"""
        if self.running:
            self.logger.warning("Time-based focus controller is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.logger.info("Started time-based focus controller")
    
    def stop(self):
        """Stop the time-based focus controller"""
        if not self.running:
            self.logger.warning("Time-based focus controller is not running")
            return
        
        self.logger.info("Stopping time-based focus controller...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            try:
                self.thread.join(timeout=3.0)  # Give more time for graceful shutdown
                if self.thread.is_alive():
                    self.logger.warning("Thread did not stop gracefully within timeout")
                else:
                    self.logger.info("Thread stopped gracefully")
            except Exception as e:
                self.logger.error(f"Error joining thread: {e}")
        
        self.thread = None
        self.logger.info("Stopped time-based focus controller")
    
    def _run_loop(self):
        """Main loop for checking and applying rules"""
        check_interval = 60  # Check rules every 60 seconds
        
        while self.running:
            try:
                self._check_rules()
                # Sleep in smaller intervals to allow for graceful shutdown
                for _ in range(check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in time-based focus loop: {e}")
                # Continue running unless explicitly stopped
                if not self.running:
                    break
    
    def _check_rules(self):
        """Check all rules and apply actions for matching conditions"""
        current_time = datetime.datetime.now()
        
        for rule in self.rules:
            try:
                # Check if the condition is met
                if rule["condition"]():
                    # Only trigger once per hour to avoid excessive changes
                    last_triggered = rule["last_triggered"]
                    if last_triggered is None or (current_time - last_triggered).total_seconds() >= 3600:
                        self.logger.info(f"Applying rule: {rule['name']} - {rule['description']}")
                        rule["action"]()
                        rule["last_triggered"] = current_time
            except Exception as e:
                self.logger.error(f"Error applying rule {rule['name']}: {str(e)}")
    
    def get_active_rules(self):
        """
        Get the currently active rules
        
        Returns:
            list: List of active rule names
        """
        active_rules = []
        for rule in self.rules:
            try:
                if rule["condition"]():
                    active_rules.append(rule["name"])
            except Exception:
                pass
        return active_rules
    
    def get_all_rules(self):
        """
        Get all configured rules
        
        Returns:
            list: List of rule dictionaries
        """
        return [{
            "name": rule["name"],
            "description": rule["description"],
            "last_triggered": rule["last_triggered"]
        } for rule in self.rules]
