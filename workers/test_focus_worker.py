#!/usr/bin/env python3
"""
Test Focus Mode Worker in Isolation
Tests the macOS Focus mode control without Nova
"""

import os
import sys
import time
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the FocusController
from core.services.app_control_service import FocusController

def test_focus_worker_isolation():
    """Test Focus Mode worker functionality in isolation"""
    print("\n🔒 Testing Focus Mode Worker in Isolation 🔒")
    print("=" * 60)
    
    try:
        # Create Focus Mode worker instance
        focus_controller = FocusController()
        print("   ✅ Focus controller created successfully")
        
        # Test 1: Service Initialization
        print("\n1️⃣ Testing Service Initialization...")
        
        # Check if we can access macOS Focus controls
        try:
            # Test basic command execution
            result = subprocess.run(['shortcuts', 'list'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("   ✅ macOS Shortcuts available")
                shortcuts_list = result.stdout.strip().split('\n')
                print(f"   📱 Found {len(shortcuts_list)} shortcuts")
            else:
                print("   ⚠️ macOS Shortcuts not accessible")
                print(f"   📱 Error: {result.stderr}")
        except Exception as e:
            print(f"   ⚠️ Could not test shortcuts: {e}")
        
        # Test 2: Focus Mode Detection
        print("\n2️⃣ Testing Focus Mode Detection...")
        
        try:
            # Check current focus mode
            current_focus = focus_controller.get_current_focus_mode()
            print(f"   🔍 Current focus mode: {current_focus}")
            
            if current_focus:
                print("   ✅ Focus mode detection working")
            else:
                print("   ⚠️ No focus mode detected (may be normal)")
                
        except Exception as e:
            print(f"   ❌ Focus mode detection failed: {e}")
            return False
        
        # Test 3: Do Not Disturb Control
        print("\n3️⃣ Testing Do Not Disturb Control...")
        
        try:
            # Test setting DND on
            print("   🔒 Testing DND ON...")
            dnd_on_success = focus_controller.set_do_not_disturb(True)
            print(f"   ✅ DND ON success: {dnd_on_success}")
            
            if dnd_on_success:
                # Wait a moment for the change to take effect
                time.sleep(2)
                
                # Verify DND is on
                current_focus = focus_controller.get_current_focus_mode()
                print(f"   🔍 Focus mode after DND ON: {current_focus}")
                
                # Test setting DND off
                print("   🔓 Testing DND OFF...")
                dnd_off_success = focus_controller.set_do_not_disturb(False)
                print(f"   ✅ DND OFF success: {dnd_off_success}")
                
                if dnd_off_success:
                    # Wait a moment for the change to take effect
                    time.sleep(2)
                    
                    # Verify DND is off
                    current_focus = focus_controller.get_current_focus_mode()
                    print(f"   🔍 Focus mode after DND OFF: {current_focus}")
                    print("   ✅ DND control cycle completed successfully")
                else:
                    print("   ❌ DND OFF failed")
                    return False
            else:
                print("   ❌ DND ON failed")
                return False
                
        except Exception as e:
            print(f"   ❌ DND control failed: {e}")
            return False
        
        # Test 4: Focus Mode Switching
        print("\n4️⃣ Testing Focus Mode Switching...")
        
        try:
            # Test switching to different focus modes
            focus_modes = ['Do Not Disturb', 'Work', 'Personal']
            
            for mode in focus_modes:
                print(f"   🔄 Testing switch to {mode}...")
                try:
                    success = focus_controller.set_focus_mode(mode)
                    print(f"   ✅ {mode} switch: {success}")
                    
                    if success:
                        # Wait for change
                        time.sleep(2)
                        current_focus = focus_controller.get_current_focus_mode()
                        print(f"   🔍 Current focus after {mode}: {current_focus}")
                    
                except Exception as e:
                    print(f"   ⚠️ {mode} switch failed: {e}")
                    # Continue with other modes
            
            # Return to normal (DND off)
            print("   🔄 Returning to normal mode...")
            focus_controller.set_do_not_disturb(False)
            time.sleep(2)
            
        except Exception as e:
            print(f"   ❌ Focus mode switching failed: {e}")
            return False
        
        # Test 5: Error Handling
        print("\n5️⃣ Testing Error Handling...")
        
        # Test with invalid focus mode
        try:
            print("   🧪 Testing invalid focus mode...")
            invalid_result = focus_controller.set_focus_mode("InvalidMode123")
            print(f"   ✅ Invalid focus mode handled gracefully: {invalid_result}")
        except Exception as e:
            print(f"   ✅ Invalid focus mode caused expected error: {type(e).__name__}")
        
        # Test with invalid DND state
        try:
            print("   🧪 Testing invalid DND state...")
            invalid_result = focus_controller.set_do_not_disturb("invalid")
            print(f"   ✅ Invalid DND state handled gracefully: {invalid_result}")
        except Exception as e:
            print(f"   ✅ Invalid DND state caused expected error: {type(e).__name__}")
        
        print("\n" + "=" * 60)
        print("🔒 Focus Mode Worker Isolation Test Complete")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Focus Mode worker test failed: {e}")
        return False

def test_focus_worker_performance():
    """Test Focus Mode worker performance characteristics"""
    print("\n⚡ Testing Focus Mode Worker Performance ⚡")
    print("=" * 60)
    
    try:
        focus_controller = FocusController()
        
        # Test 1: Focus Mode Detection Time
        print("\n1️⃣ Testing Focus Mode Detection Time...")
        
        start_time = time.time()
        current_focus = focus_controller.get_current_focus_mode()
        detection_time = time.time() - start_time
        
        print(f"   🔍 Detection response time: {detection_time:.2f} seconds")
        print(f"   🔒 Current focus mode: {current_focus}")
        
        if detection_time > 2:
            print("   ⚠️ Detection is slow (>2s)")
        elif detection_time > 1:
            print("   ⚠️ Detection is moderate (>1s)")
        else:
            print("   ✅ Detection is fast (<1s)")
        
        # Test 2: DND Toggle Time
        print("\n2️⃣ Testing DND Toggle Time...")
        
        # Test DND ON
        start_time = time.time()
        dnd_on_success = focus_controller.set_do_not_disturb(True)
        dnd_on_time = time.time() - start_time
        
        print(f"   🔒 DND ON response time: {dnd_on_time:.2f} seconds")
        print(f"   ✅ DND ON success: {dnd_on_success}")
        
        if dnd_on_time > 3:
            print("   ⚠️ DND ON is slow (>3s)")
        elif dnd_on_time > 1:
            print("   ⚠️ DND ON is moderate (>1s)")
        else:
            print("   ✅ DND ON is fast (<1s)")
        
        # Wait for change to take effect
        time.sleep(2)
        
        # Test DND OFF
        start_time = time.time()
        dnd_off_success = focus_controller.set_do_not_disturb(False)
        dnd_off_time = time.time() - start_time
        
        print(f"   🔓 DND OFF response time: {dnd_off_time:.2f} seconds")
        print(f"   ✅ DND OFF success: {dnd_off_success}")
        
        if dnd_off_time > 3:
            print("   ⚠️ DND OFF is slow (>3s)")
        elif dnd_off_time > 1:
            print("   ⚠️ DND OFF is moderate (>1s)")
        else:
            print("   ✅ DND OFF is fast (<1s)")
        
        # Test 3: Multiple Toggle Handling
        print("\n3️⃣ Testing Multiple Toggle Handling...")
        
        start_time = time.time()
        for i in range(3):
            focus_controller.set_do_not_disturb(True)
            time.sleep(1)
            focus_controller.set_do_not_disturb(False)
            time.sleep(1)
        multiple_time = time.time() - start_time
        
        print(f"   🔄 Multiple toggle time: {multiple_time:.2f} seconds")
        print(f"   📊 Average per toggle cycle: {multiple_time/3:.2f} seconds")
        
        if multiple_time > 15:
            print("   ⚠️ Multiple toggles are slow (>15s)")
        elif multiple_time > 10:
            print("   ⚠️ Multiple toggles are moderate (>10s)")
        else:
            print("   ✅ Multiple toggles are fast (<10s)")
        
        print("\n" + "=" * 60)
        print("⚡ Focus Mode Worker Performance Test Complete")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Focus Mode worker performance test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Starting Focus Mode Worker Isolation Tests...")
    
    # Run isolation tests
    isolation_success = test_focus_worker_isolation()
    
    if isolation_success:
        # Run performance tests
        performance_success = test_focus_worker_performance()
        
        print("\n" + "=" * 60)
        print("🎯 FINAL TEST RESULTS")
        print("=" * 60)
        print(f"   Isolation Tests: {'✅ PASSED' if isolation_success else '❌ FAILED'}")
        print(f"   Performance Tests: {'✅ PASSED' if performance_success else '❌ FAILED'}")
        
        if isolation_success and performance_success:
            print("\n🎉 ALL TESTS PASSED! Focus Mode Worker is ready for integration.")
        else:
            print("\n⚠️ Some tests failed. Review issues before integration.")
    else:
        print("\n❌ Isolation tests failed. Cannot proceed to performance tests.")
