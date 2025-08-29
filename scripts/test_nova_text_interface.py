#!/usr/bin/env python3
"""
Nova Text Interface - Comprehensive Testing

This script allows you to interact with Nova directly through text input.
Test all of Nova's capabilities including the new text processor.
"""

import sys
import os

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """Main text interface for Nova"""
    print("🧠 NOVA ASSISTANT - COMPREHENSIVE TEXT INTERFACE")
    print("=" * 60)
    print("✅ Initializing Nova...")
    
    try:
        from core.brain.router import NovaBrain
        
        # Initialize Nova
        brain = NovaBrain()
        print("✅ Nova is ready!")
        print("\n💬 Type your commands below (or type 'exit' to quit):")
        print("\n🎯 Test Categories:")
        print("  📅 Calendar:")
        print("    - What's on my schedule today?")
        print("    - What do I have tomorrow?")
        print("    - Show me my week schedule")
        print("    - What's on my calendar for Friday?")
        print("  🎵 Spotify:")
        print("    - Play some music")
        print("    - Start my nightmode playlist")
        print("    - What is currently playing?")
        print("    - Pause the music")
        print("  🌙 Focus Modes:")
        print("    - Set my home to private mode")
        print("    - Turn on study mode")
        print("    - Turn off do not disturb")
        print("  🧮 Math:")
        print("    - What is 15 times 23?")
        print("    - Calculate 45 divided by 7")
        print("    - Solve 2x + 5 = 15")
        print("  📝 Notes:")
        print("    - Take a note about my meeting")
        print("    - Show me my recent notes")
        print("\n" + "=" * 60)
        
        # Main command loop
        while True:
            try:
                # Get user input
                user_input = input("\n🎤 You: ").strip()
                
                # Check for exit
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Goodbye! Nova signing off...")
                    break
                
                if not user_input:
                    continue
                
                # Process command through Nova
                print("🧠 Nova: Processing...")
                response = brain.process_input(user_input)
                
                # Display response
                print(f"🤖 Nova: {response}")
                
                # Test text processor on the response
                try:
                    from core.utils.text_processor import make_speakable
                    processed_response = make_speakable(response)
                    if processed_response != response:
                        print(f"🔧 Text Processed: {processed_response}")
                    else:
                        print("✅ Text already in optimal format")
                except ImportError:
                    print("⚠️ Text processor not available")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Nova signing off...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Please try again or type 'exit' to quit.")
                
    except Exception as e:
        print(f"❌ Failed to initialize Nova: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
