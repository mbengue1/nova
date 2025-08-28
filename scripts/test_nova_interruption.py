#!/usr/bin/env python3
"""
Test script for Nova's interruption handling

This script tests Nova's ability to handle interruptions during speech output
and process the interruption audio correctly.
"""

import sys
import os
import time
import threading
import argparse

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Nova components
from core.main import HeyNova
from core.tts import SpeechSynthesizer
from core.stt import SpeechTranscriber
from core.audio.interruption_monitor import InterruptionMonitor

def test_interruption_monitor():
    """Test the interruption monitor in isolation"""
    print("\n" + "="*60)
    print("🧪 TESTING INTERRUPTION MONITOR")
    print("="*60)
    
    # Create an interruption monitor
    monitor = InterruptionMonitor(
        sample_rate=16000,
        energy_threshold=0.015,
        min_duration_ms=50,
        consecutive_frames=2
    )
    
    # Define a simple callback
    def on_interrupt():
        print("🛑 INTERRUPTION DETECTED!")
    
    # Start monitoring
    print("👂 Starting interruption monitor...")
    print("🗣️ Please speak to test interruption detection")
    monitor.start_monitoring(on_interruption=on_interrupt)
    
    # Wait for interruption or timeout
    timeout = 10  # seconds
    start_time = time.time()
    while not monitor.was_interrupted and time.time() - start_time < timeout:
        print("⏳ Waiting for interruption... (speak now)")
        time.sleep(1)
    
    # Stop monitoring
    monitor.stop_monitoring()
    
    # Check results
    if monitor.was_interrupted:
        print("✅ Interruption detected successfully!")
        audio_file = monitor.get_interruption_audio_file()
        if audio_file:
            print(f"✅ Interruption audio captured: {audio_file}")
        else:
            print("❌ Failed to capture interruption audio")
    else:
        print("❌ No interruption detected within timeout")
    
    return monitor.was_interrupted

def test_tts_interruption():
    """Test interruption during TTS output"""
    print("\n" + "="*60)
    print("🧪 TESTING TTS INTERRUPTION")
    print("="*60)
    
    # Create TTS and STT components
    tts = SpeechSynthesizer()
    stt = SpeechTranscriber()
    
    # Define a long text to speak
    long_text = """
    I'm going to keep talking for a while so you have time to interrupt me.
    This is a test of Nova's interruption handling capability.
    The system should detect when you start speaking and immediately stop my speech.
    Then it should capture what you said and process it as a new request.
    This makes the conversation feel more natural and responsive.
    Please try interrupting me at any point while I'm speaking.
    I'll keep talking until you interrupt me or until I finish this long message.
    """
    
    # Set up interruption callback
    was_interrupted = False
    def on_interrupt():
        nonlocal was_interrupted
        was_interrupted = True
        print("🛑 TTS INTERRUPTED!")
    
    # Set the interrupt callback
    stt.set_interrupt_callback(on_interrupt)
    
    # Start speaking with interruption capability
    print("🗣️ Starting speech... (interrupt at any time)")
    result = tts.speak_with_interruption(long_text, stt)
    
    # Check results
    if was_interrupted or tts.was_interrupted:
        print("✅ Speech was interrupted successfully!")
        
        # Check if we have audio
        if hasattr(tts, 'interruption_monitor') and tts.interruption_monitor:
            audio_file = tts.interruption_monitor.get_interruption_audio_file()
            if audio_file and os.path.exists(audio_file):
                print(f"✅ Interruption audio captured: {audio_file}")
                
                # Try to transcribe
                try:
                    text = stt.transcribe_file(audio_file)
                    if text:
                        print(f"✅ Transcription: '{text}'")
                    else:
                        print("❌ Failed to transcribe interruption audio")
                except Exception as e:
                    print(f"❌ Error transcribing: {e}")
            else:
                print("❌ No interruption audio captured")
        
        # Return success
        return True
    else:
        print("❌ Speech was not interrupted")
        return False

def test_full_nova_interruption():
    """Test interruption in the full Nova system"""
    print("\n" + "="*60)
    print("🧪 TESTING FULL NOVA INTERRUPTION")
    print("="*60)
    
    # Create Nova instance
    nova = HeyNova()
    
    # Directly test the _process_interruption method
    print("🎤 Testing _process_interruption method...")
    
    # Set initial state
    nova.conversation_state["interruption_count"] = 0
    nova.conversation_state["last_interruption"] = None
    
    # Call the method with a test interruption
    test_interruption = "This is a test interruption"
    nova._process_interruption(test_interruption)
    
    # Check results
    if nova.conversation_state["interruption_count"] > 0:
        print("✅ Nova handled interruption successfully!")
        print(f"✅ Interruption count: {nova.conversation_state['interruption_count']}")
        if nova.conversation_state["last_interruption"]:
            print(f"✅ Last interruption: '{nova.conversation_state['last_interruption']}'")
        return True
    else:
        print("❌ Nova did not handle interruption")
        return False

def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test Nova's interruption handling")
    parser.add_argument("--test", choices=["monitor", "tts", "nova", "all"], default="all",
                        help="Which test to run (default: all)")
    args = parser.parse_args()
    
    # Run selected tests
    results = {}
    
    if args.test in ["monitor", "all"]:
        results["monitor"] = test_interruption_monitor()
    
    if args.test in ["tts", "all"]:
        results["tts"] = test_tts_interruption()
    
    if args.test in ["nova", "all"]:
        results["nova"] = test_full_nova_interruption()
    
    # Print summary
    print("\n" + "="*60)
    print("🧪 TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    # Overall result
    if all(results.values()):
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
