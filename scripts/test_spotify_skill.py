#!/usr/bin/env python3
"""
Test Script for Spotify Skill

This script tests the Spotify skill's ability to:
1. Recognize different types of music commands
2. Process commands and return appropriate responses
3. Handle various command formats
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path so we can import the core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_spotify_skill():
    """Test the Spotify skill's command recognition and processing"""
    print("===== Testing Spotify Skill =====\n")
    
    try:
        # Import required components
        print("🔍 Testing imports...")
        from core.skills.spotify_skill import SpotifySkill
        from core.services.spotify_service import SpotifyService
        print("✅ All components imported successfully")
        
        # Initialize services
        print("\n🔍 Initializing services...")
        spotify_service = SpotifyService()
        spotify_skill = SpotifySkill(spotify_service)
        print("✅ Services initialized")
        
        # Test commands
        test_commands = [
            # Basic music commands
            "Play some music",
            "Start playing music",
            "Play my nightmode playlist",
            "Start the nightmode playlist",
            
            # Playback control
            "Pause the music",
            "Stop the music",
            "Next track",
            "Previous song",
            "Resume the music",
            
            # Volume control
            "Turn up the volume",
            "Lower the volume",
            "Set volume to 50%",
            
            # Information requests
            "What's currently playing?",
            "What song is this?",
            "What playlists do I have?",
            "Show me my playlists",
            
            # Context commands
            "Play something relaxing",
            "Play music for studying",
            "I need some background music",
            
            # Edge cases
            "Can you play music?",
            "Do you know how to control Spotify?",
            "Help me with music"
        ]
        
        print(f"\n🔍 Testing {len(test_commands)} commands...")
        print("=" * 60)
        
        # Test each command
        for i, command in enumerate(test_commands, 1):
            print(f"\n{i:2d}. Testing: '{command}'")
            print("-" * 40)
            
            try:
                # Test if skill recognizes the command
                if spotify_skill.matches(command):
                    print("✅ Command recognized by Spotify skill")
                    
                    # Process the command (this won't actually play music)
                    response = spotify_skill.process(command)
                    print(f"   Response: {response}")
                else:
                    print("❌ Command NOT recognized by Spotify skill")
                    
            except Exception as e:
                print(f"   ⚠️ Error processing command: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 Spotify Skill Test Complete!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_spotify_skill()
    sys.exit(0 if success else 1)
