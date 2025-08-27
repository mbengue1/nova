#!/usr/bin/env python3
"""
Test App Control for Nova

This script tests the app control functionality by simulating voice commands
that might be misheard by the speech-to-text system.

Usage:
    python scripts/test_app_control.py
"""
import os
import sys
import re

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.brain.router import NovaBrain
except ImportError as e:
    print(f"Error importing NovaBrain: {e}")
    sys.exit(1)

def test_app_control():
    """Test app control functionality"""
    print("\n🧪 Testing App Control functionality\n")
    
    # Initialize Nova's brain
    brain = NovaBrain()
    
    # Test phrases - common voice transcription variations
    test_phrases = [
        "open Chrome",
        "open chrome",
        "open Chrome browser",
        "launch Chrome",
        "start Chrome",
        "can you open Chrome",
        "could you open Chrome please",
        "please open Chrome",
        "open crome",  # Common misspelling
        "open crime",  # Common voice transcription error
        "open from",   # Common voice transcription error
        "open the browser",
        "launch browser",
        "open calculator",
        "open calc",
        "open calendar",
        "open terminal",
        "open term",
        "open finder",
        "open settings",
        "open system preferences",
        "open visual studio code",
        "open vs code",
        "open code",
        "open safari",
        "open firefox"
    ]
    
    # Test each phrase
    print("📋 Testing phrases:")
    print("------------------")
    
    for phrase in test_phrases:
        print(f"\n🔍 Testing: '{phrase}'")
        
        # Check if app control patterns match
        app_control_match = False
        for pattern in brain.skill_patterns['app_control']:
            if re.search(pattern, phrase.lower()):
                app_control_match = True
                print(f"  ✅ Matched pattern: {pattern}")
                break
        
        if not app_control_match:
            print(f"  ❌ No pattern match")
            
            # Check if fallback detection would work
            words = phrase.lower().split()
            app_keywords = ['open', 'launch', 'start', 'run']
            for i, word in enumerate(words):
                if word in app_keywords and i < len(words) - 1:
                    potential_app = words[i+1]
                    print(f"  🔍 Potential app name detected: '{potential_app}'")
                    if potential_app in ['chrome', 'safari', 'firefox', 'browser', 'finder', 'terminal', 'calculator', 'calendar']:
                        print(f"  ✅ Fallback detection would match: '{potential_app}'")
                        app_control_match = True
                        break
        
        # Process the input through Nova's brain
        print(f"  🧠 Nova's response: ", end="")
        response = brain.process_input(phrase)
        print(f"'{response}'")
        
        if "opening" in response.lower() or "open" in response.lower():
            print("  ✅ App control successful")
        else:
            print("  ❌ App control failed")
    
    print("\n🏁 App control testing complete\n")

if __name__ == "__main__":
    test_app_control()