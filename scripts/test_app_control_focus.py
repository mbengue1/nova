#!/usr/bin/env python3
"""
Test script for Focus Mode control via AppControlService

This script tests the AppControlService's focus mode control functionality.
"""
import sys
import os
import time
import logging

# Add the parent directory to the path so we can import the core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import the AppControlService
from core.services.app_control_service import AppControlService

def test_app_control_focus():
    """Test the AppControlService focus control functionality"""
    print("\n===== Testing AppControlService Focus Control =====\n")
    
    # Create an AppControlService instance
    service = AppControlService()
    
    # Test 1: Get current focus mode
    print("Test 1: Getting current focus mode...")
    success, current_mode = service.get_current_focus_mode()
    print(f"Current focus mode: {current_mode}" if success else f"Error: {current_mode}")
    
    # Test 2: Toggle Do Not Disturb
    print("\nTest 2: Toggling Do Not Disturb...")
    success, message = service.toggle_do_not_disturb()
    print(f"Result: {message}")
    
    # Wait a moment to let the system update
    time.sleep(2)
    
    # Test 3: Get current focus mode again to verify the change
    print("\nTest 3: Verifying focus mode changed...")
    success, new_mode = service.get_current_focus_mode()
    print(f"New focus mode: {new_mode}" if success else f"Error: {new_mode}")
    
    # Test 4: Toggle back to original state
    print("\nTest 4: Toggling back to original state...")
    success, message = service.toggle_do_not_disturb()
    print(f"Result: {message}")
    
    # Test 5: Try setting a specific focus mode
    print("\nTest 5: Setting specific focus mode (Do Not Disturb)...")
    success, message = service.set_focus_mode("Do Not Disturb")
    print(f"Result: {message}")
    
    # Wait a moment
    time.sleep(2)
    
    # Test 6: Disable Do Not Disturb
    print("\nTest 6: Disabling Do Not Disturb...")
    success, message = service.set_do_not_disturb(False)
    print(f"Result: {message}")
    
    print("\n===== AppControlService Focus Control Testing Complete =====")

if __name__ == "__main__":
    test_app_control_focus()
