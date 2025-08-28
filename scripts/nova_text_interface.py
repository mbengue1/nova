#!/usr/bin/env python3
"""
Nova Text Interface - Direct Command Testing

This script allows you to interact with Nova directly through text input.
Type your commands and see Nova's responses in real-time.
"""

import sys
import os

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """Main text interface for Nova"""
    print("🎵 NOVA SPOTIFY ASSISTANT - TEXT INTERFACE")
    print("=" * 50)
    print("✅ Initializing Nova...")
    
    try:
        from core.brain.router import NovaBrain
        
        # Initialize Nova
        brain = NovaBrain()
        print("✅ Nova is ready!")
        print("\n💬 Type your music commands below (or type 'exit' to quit):")
        print("\n🎵 Examples:")
        print("  - Play some music")
        print("  - Start my nightmode playlist") 
        print("  - What is currently playing?")
        print("  - Show me my playlists")
        print("  - Pause the music")
        print("  - Play run")
        print("  - I need background music")
        print("\n" + "=" * 50)
        
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
                print(f"🎵 Nova: {response}")
                
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
