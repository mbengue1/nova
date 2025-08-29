#!/usr/bin/env python3
"""
Test Nova State Machine
Tests the complete state machine logic for Home Starter Mode
"""

import os
import sys
import time
import logging
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class NovaStateMachine:
    """Nova State Machine for Home Starter Mode"""
    
    # State definitions
    STATES = {
        "STARTUP": "System starting up",
        "GREETING_ONCE": "Running one-time greeting sequence",
        "BACKGROUND_IDLE": "Silent background mode, wake word only",
        "WAKE_WORD_DETECTED": "Wake word heard, transitioning to active",
        "ACTIVE_REQUEST": "Processing user request",
        "SPEAKING": "Speaking response to user",
        "RECOVER": "Error recovery mode"
    }
    
    # Valid transitions
    VALID_TRANSITIONS = {
        "STARTUP": ["GREETING_ONCE", "RECOVER"],
        "GREETING_ONCE": ["BACKGROUND_IDLE", "RECOVER"],
        "BACKGROUND_IDLE": ["WAKE_WORD_DETECTED", "RECOVER"],
        "WAKE_WORD_DETECTED": ["ACTIVE_REQUEST", "RECOVER"],
        "ACTIVE_REQUEST": ["SPEAKING", "RECOVER"],
        "SPEAKING": ["BACKGROUND_IDLE", "RECOVER"],
        "RECOVER": ["BACKGROUND_IDLE", "STARTUP"]
    }
    
    def __init__(self):
        self.current_state = "STARTUP"
        self.previous_state = None
        self.state_history = []
        self.transition_count = 0
        self.last_transition_time = None
        self.greeting_completed = False
        self.greeting_timestamp = None
        self.lockfile_path = "/tmp/nova_greeting.lock"
        self.error_count = 0
        self.max_errors = 3
        
        # Initialize state (don't record initial state as a transition)
        self.state_history.append({
            "timestamp": time.time(),
            "from": None,
            "to": "STARTUP",
            "reason": "System initialization",
            "transition_number": 0
        })
    
    def _record_state_change(self, new_state: str, reason: str):
        """Record a state change with metadata"""
        timestamp = time.time()
        
        # Validate transition
        if not self._is_valid_transition(new_state):
            raise ValueError(f"Invalid transition: {self.current_state} → {new_state}")
        
        # Record the change
        self.previous_state = self.current_state
        self.current_state = new_state
        self.transition_count += 1
        self.last_transition_time = timestamp
        
        state_record = {
            "timestamp": timestamp,
            "from": self.previous_state,
            "to": new_state,
            "reason": reason,
            "transition_number": self.transition_count
        }
        
        self.state_history.append(state_record)
        
        print(f"🔄 State Transition: {self.previous_state} → {new_state} ({reason})")
        print(f"   📊 Transition #{self.transition_count} at {datetime.fromtimestamp(timestamp)}")
    
    def _is_valid_transition(self, new_state: str) -> bool:
        """Check if a state transition is valid"""
        if self.current_state not in self.VALID_TRANSITIONS:
            return False
        
        return new_state in self.VALID_TRANSITIONS[self.current_state]
    
    def transition_to(self, new_state: str, reason: str = "No reason specified"):
        """Transition to a new state"""
        try:
            self._record_state_change(new_state, reason)
            return True
        except ValueError as e:
            print(f"❌ State transition failed: {e}")
            self.error_count += 1
            return False
    
    def get_current_state_info(self) -> Dict[str, Any]:
        """Get detailed information about current state"""
        return {
            "current_state": self.current_state,
            "state_description": self.STATES.get(self.current_state, "Unknown"),
            "previous_state": self.previous_state,
            "transition_count": self.transition_count,
            "last_transition_time": self.last_transition_time,
            "greeting_completed": self.greeting_completed,
            "error_count": self.error_count,
            "state_history_length": len(self.state_history)
        }
    
    def check_greeting_lockfile(self) -> bool:
        """Check if greeting has already been completed this session"""
        try:
            if os.path.exists(self.lockfile_path):
                # Check if lockfile is from today
                stat = os.stat(self.lockfile_path)
                lock_time = datetime.fromtimestamp(stat.st_mtime)
                current_time = datetime.now()
                
                # Check if lockfile is from current session (within last 30 minutes)
                # This allows for fresh greeting on each login while preventing spam
                time_diff = current_time - lock_time
                if time_diff.total_seconds() < 1800:  # 30 minutes
                    print(f"🔒 Greeting already completed this session at {lock_time}")
                    return True
                else:
                    print(f"🔄 Lockfile is from {lock_time}, removing old lock for fresh greeting")
                    os.remove(self.lockfile_path)
                    return False
            return False
        except Exception as e:
            print(f"⚠️ Error checking lockfile: {e}")
            return False
    
    def create_greeting_lockfile(self):
        """Create lockfile to mark greeting as completed"""
        try:
            with open(self.lockfile_path, 'w') as f:
                f.write(f"Nova greeting completed at {datetime.now()}\n")
            self.greeting_completed = True
            self.greeting_timestamp = time.time()
            print(f"🔒 Greeting lockfile created at {datetime.now()}")
        except Exception as e:
            print(f"❌ Failed to create lockfile: {e}")
    
    def run_startup_sequence(self) -> bool:
        """Run the startup sequence"""
        print("\n🚀 Running Startup Sequence...")
        
        # Check if we should run greeting
        if self.check_greeting_lockfile():
            print("   ✅ Greeting already completed for this session, skipping to background")
            # Must go through GREETING_ONCE first, then immediately to BACKGROUND_IDLE
            if self.transition_to("GREETING_ONCE", "Greeting already completed"):
                return self.transition_to("BACKGROUND_IDLE", "Greeting already completed")
            return False
        
        # Run greeting sequence
        print("   🎯 Greeting not completed for this session, running greeting sequence")
        return self.transition_to("GREETING_ONCE", "Starting greeting sequence")
    
    def run_greeting_sequence(self) -> bool:
        """Run the one-time greeting sequence"""
        print("\n🎉 Running Greeting Sequence...")
        
        try:
            # Simulate greeting steps
            steps = [
                "Welcome home message",
                "Set private mode (Do Not Disturb)",
                "Start Spotify Nightmode playlist",
                "Read calendar schedule",
                "Productive day message"
            ]
            
            for i, step in enumerate(steps, 1):
                print(f"   {i}. {step}")
                time.sleep(0.5)  # Simulate step execution
            
            # Mark greeting as completed
            self.create_greeting_lockfile()
            
            print("   ✅ Greeting sequence completed successfully")
            return self.transition_to("BACKGROUND_IDLE", "Greeting sequence completed")
            
        except Exception as e:
            print(f"   ❌ Greeting sequence failed: {e}")
            return self.transition_to("RECOVER", f"Greeting sequence error: {e}")
    
    def handle_wake_word(self) -> bool:
        """Handle wake word detection"""
        print("\n👂 Wake Word Detected...")
        
        if self.current_state != "BACKGROUND_IDLE":
            print(f"   ⚠️ Unexpected wake word in state: {self.current_state}")
            return False
        
        return self.transition_to("WAKE_WORD_DETECTED", "Wake word detected")
    
    def begin_request_processing(self) -> bool:
        """Begin processing user request"""
        print("\n🎯 Beginning Request Processing...")
        
        if self.current_state != "WAKE_WORD_DETECTED":
            print(f"   ⚠️ Cannot begin request processing in state: {self.current_state}")
            return False
        
        return self.transition_to("ACTIVE_REQUEST", "Starting request processing")
    
    def begin_speaking(self) -> bool:
        """Begin speaking response"""
        print("\n🗣️ Beginning Response...")
        
        if self.current_state != "ACTIVE_REQUEST":
            print(f"   ⚠️ Cannot begin speaking in state: {self.current_state}")
            return False
        
        return self.transition_to("SPEAKING", "Starting response")
    
    def finish_request(self) -> bool:
        """Finish request and return to background"""
        print("\n✅ Finishing Request...")
        
        if self.current_state != "SPEAKING":
            print(f"   ⚠️ Cannot finish request in state: {self.current_state}")
            return False
        
        return self.transition_to("BACKGROUND_IDLE", "Request completed, returning to background")
    
    def handle_error(self, error: str) -> bool:
        """Handle errors and transition to recovery"""
        print(f"\n❌ Error occurred: {error}")
        
        self.error_count += 1
        print(f"   ⚠️ Error count: {self.error_count}/{self.max_errors}")
        
        if self.error_count >= self.max_errors:
            print(f"   🚨 Max errors reached ({self.max_errors}), transitioning to recovery")
            return self.transition_to("RECOVER", f"Max errors reached: {error}")
        else:
            return False
    
    def recover_from_error(self) -> bool:
        """Attempt to recover from error state"""
        print("\n🔧 Attempting Recovery...")
        
        if self.current_state != "RECOVER":
            print(f"   ⚠️ Not in recovery state: {self.current_state}")
            return False
        
        try:
            # Reset error count
            self.error_count = 0
            
            # Try to return to background
            print("   🔄 Attempting to return to background mode")
            return self.transition_to("BACKGROUND_IDLE", "Recovery successful")
            
        except Exception as e:
            print(f"   ❌ Recovery failed: {e}")
            return False
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of the state machine"""
        return {
            "current_state": self.current_state,
            "total_transitions": self.transition_count,
            "greeting_completed": self.greeting_completed,
            "error_count": self.error_count,
            "state_history": self.state_history[-5:],  # Last 5 transitions
            "uptime": time.time() - (self.state_history[0]["timestamp"] if self.state_history else time.time())
        }

def test_state_machine_basic():
    """Test basic state machine functionality"""
    print("\n🧪 Testing Basic State Machine Functionality")
    print("=" * 60)
    
    sm = NovaStateMachine()
    
    # Test 1: Initial State
    print("\n1️⃣ Testing Initial State...")
    info = sm.get_current_state_info()
    print(f"   📊 Current state: {info['current_state']}")
    print(f"   📝 Description: {info['state_description']}")
    print(f"   🔢 Transition count: {info['transition_count']}")
    
    if info['current_state'] == "STARTUP":
        print("   ✅ Initial state correct")
    else:
        print("   ❌ Initial state incorrect")
        return False
    
    # Test 2: Valid Transitions
    print("\n2️⃣ Testing Valid Transitions...")
    
    transitions = [
        ("GREETING_ONCE", "Starting greeting sequence"),
        ("BACKGROUND_IDLE", "Greeting completed"),
        ("WAKE_WORD_DETECTED", "Wake word heard"),
        ("ACTIVE_REQUEST", "Processing request"),
        ("SPEAKING", "Speaking response"),
        ("BACKGROUND_IDLE", "Request completed")
    ]
    
    for new_state, reason in transitions:
        success = sm.transition_to(new_state, reason)
        if success:
            print(f"   ✅ {new_state}: {reason}")
        else:
            print(f"   ❌ {new_state}: {reason}")
            return False
    
    # Test 3: State History
    print("\n3️⃣ Testing State History...")
    history = sm.state_history
    print(f"   📊 Total transitions: {len(history)}")
    print(f"   🕐 First transition: {datetime.fromtimestamp(history[0]['timestamp'])}")
    print(f"   🕐 Last transition: {datetime.fromtimestamp(history[-1]['timestamp'])}")
    
    if len(history) == len(transitions) + 1:  # +1 for initial state
        print("   ✅ State history correct")
    else:
        print("   ❌ State history incorrect")
        return False
    
    print("\n✅ Basic state machine tests PASSED")
    return True

def test_state_machine_flow():
    """Test complete state machine flow"""
    print("\n🧪 Testing Complete State Machine Flow")
    print("=" * 60)
    
    sm = NovaStateMachine()
    
    # Test 1: Startup Sequence
    print("\n1️⃣ Testing Startup Sequence...")
    
    # Simulate startup
    startup_success = sm.run_startup_sequence()
    if not startup_success:
        print("   ❌ Startup sequence failed")
        return False
    
    print("   ✅ Startup sequence successful")
    
    # Test 2: Greeting Sequence
    print("\n2️⃣ Testing Greeting Sequence...")
    
    if sm.current_state == "GREETING_ONCE":
        greeting_success = sm.run_greeting_sequence()
        if not greeting_success:
            print("   ❌ Greeting sequence failed")
            return False
        print("   ✅ Greeting sequence successful")
    else:
        print("   ⚠️ Skipped greeting (already completed)")
    
    # Test 3: Background Mode
    print("\n3️⃣ Testing Background Mode...")
    
    if sm.current_state != "BACKGROUND_IDLE":
        print(f"   ❌ Not in background mode: {sm.current_state}")
        return False
    
    print("   ✅ Background mode active")
    
    # Test 4: Wake Word Flow
    print("\n4️⃣ Testing Wake Word Flow...")
    
    # Simulate wake word
    wake_success = sm.handle_wake_word()
    if not wake_success:
        print("   ❌ Wake word handling failed")
        return False
    
    # Begin request processing
    request_success = sm.begin_request_processing()
    if not request_success:
        print("   ❌ Request processing failed")
        return False
    
    # Begin speaking
    speak_success = sm.begin_speaking()
    if not speak_success:
        print("   ❌ Speaking failed")
        return False
    
    # Finish request
    finish_success = sm.finish_request()
    if not finish_success:
        print("   ❌ Request finishing failed")
        return False
    
    print("   ✅ Complete wake word flow successful")
    
    # Test 5: Return to Background
    print("\n5️⃣ Testing Return to Background...")
    
    if sm.current_state == "BACKGROUND_IDLE":
        print("   ✅ Successfully returned to background mode")
    else:
        print(f"   ❌ Failed to return to background: {sm.current_state}")
        return False
    
    print("\n✅ Complete state machine flow tests PASSED")
    return True

def test_state_machine_error_handling():
    """Test state machine error handling"""
    print("\n🧪 Testing State Machine Error Handling")
    print("=" * 60)
    
    # Test 1: Invalid Transitions
    print("\n1️⃣ Testing Invalid Transitions...")
    
    # Create a fresh state machine for invalid transition testing
    sm1 = NovaStateMachine()
    
    # Try invalid transition from STARTUP
    try:
        invalid_success = sm1.transition_to("SPEAKING", "Invalid transition")
        if not invalid_success:
            print("   ✅ Invalid transition properly rejected")
        else:
            print("   ❌ Invalid transition should have been rejected")
            return False
    except ValueError as e:
        print(f"   ✅ Invalid transition properly caught: {e}")
    
    # Test 2: Error Handling
    print("\n2️⃣ Testing Error Handling...")
    
    # Create a completely fresh state machine for error testing
    sm2 = NovaStateMachine()
    sm2.error_count = 0  # Ensure clean error count
    
    # Simulate errors
    for i in range(3):
        error_msg = f"Test error {i+1}"
        error_success = sm2.handle_error(error_msg)
        print(f"   ⚠️ Error {i+1}: {error_msg}")
        
        if i < 2:  # First two errors should not trigger recovery
            if error_success:
                print("   ❌ Error should not have triggered recovery")
                return False
        else:  # Third error should trigger recovery
            if not error_success:
                print("   ❌ Error should have triggered recovery")
                return False
    
    # Test 3: Recovery
    print("\n3️⃣ Testing Recovery...")
    
    if sm2.current_state == "RECOVER":
        print("   ✅ Successfully entered recovery state")
        
        recovery_success = sm2.recover_from_error()
        if recovery_success:
            print("   ✅ Recovery successful")
        else:
            print("   ❌ Recovery failed")
            return False
    else:
        print(f"   ❌ Not in recovery state: {sm2.current_state}")
        return False
    
    print("\n✅ Error handling tests PASSED")
    return True

def test_state_machine_lockfile():
    """Test lockfile functionality"""
    print("\n🧪 Testing Lockfile Functionality")
    print("=" * 60)
    
    # Clean up any existing lockfile first
    lockfile_path = "/tmp/nova_greeting.lock"
    if os.path.exists(lockfile_path):
        try:
            os.remove(lockfile_path)
            print("   🧹 Cleaned up existing lockfile")
        except Exception as e:
            print(f"   ⚠️ Warning: Could not clean up existing lockfile: {e}")
    
    sm = NovaStateMachine()
    
    # Test 1: No Lockfile
    print("\n1️⃣ Testing No Lockfile...")
    
    has_lock = sm.check_greeting_lockfile()
    if not has_lock:
        print("   ✅ No lockfile detected (expected)")
    else:
        print("   ❌ Lockfile detected when none should exist")
        return False
    
    # Test 2: Create Lockfile
    print("\n2️⃣ Testing Lockfile Creation...")
    
    sm.create_greeting_lockfile()
    
    # Check if lockfile was created
    if os.path.exists(sm.lockfile_path):
        print("   ✅ Lockfile created successfully")
    else:
        print("   ❌ Lockfile not created")
        return False
    
    # Test 3: Check Lockfile
    print("\n3️⃣ Testing Lockfile Detection...")
    
    has_lock = sm.check_greeting_lockfile()
    if has_lock:
        print("   ✅ Lockfile detected (expected)")
    else:
        print("   ❌ Lockfile not detected")
        return False
    
    # Test 4: Cleanup
    print("\n4️⃣ Testing Lockfile Cleanup...")
    
    try:
        os.remove(sm.lockfile_path)
        print("   ✅ Lockfile cleaned up")
    except Exception as e:
        print(f"   ⚠️ Lockfile cleanup warning: {e}")
    
    print("\n✅ Lockfile tests PASSED")
    return True

def main():
    """Run all state machine tests"""
    print("🧪 Starting Nova State Machine Comprehensive Tests")
    print("=" * 60)
    
    tests = [
        ("Basic Functionality", test_state_machine_basic),
        ("Complete Flow", test_state_machine_flow),
        ("Error Handling", test_state_machine_error_handling),
        ("Lockfile Functionality", test_state_machine_lockfile)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 STATE MACHINE TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL STATE MACHINE TESTS PASSED!")
        print("🎯 State machine is ready for integration!")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Review issues before integration.")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    main()
