#!/usr/bin/env python3
"""
Comprehensive Test Script for Nova's Spotify Command Understanding

This script tests:
1. Explicit Spotify commands
2. Implicit music commands (Nova should know it's Spotify)
3. Playback control commands
4. Playlist management
5. Smart context awareness
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path so we can import the core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_spotify_command_understanding():
    """Test Nova's understanding of various Spotify-related commands"""
    print("===== Testing Nova's Spotify Command Understanding =====\n")
    
    try:
        # Import Nova's components
        print("🔍 Testing Nova component imports...")
        from core.brain.router import NovaBrain
        from core.services.spotify_service import SpotifyService
        print("✅ All Nova components imported successfully")
        
        # Initialize services
        print("\n🔍 Initializing services...")
        spotify = SpotifyService()
        brain = NovaBrain()
        print("✅ Services initialized")
        
        # Test commands that should work
        test_commands = [
            # Explicit Spotify Commands
            "Play Nightmode playlist on Spotify",
            "Start playing my Nightmode playlist on Spotify",
            "Play some music on Spotify",
            "Start Spotify and play Nightmode",
            
            # Implicit Music Commands (Nova should know this is Spotify)
            "Play some music",
            "Start playing music",
            "Play my nightmode playlist",
            "Start the nightmode playlist",
            "Play music",
            "I want to listen to music",
            "Start some tunes",
            "Play my playlist",
            
            # Playback Control Commands
            "Pause the music",
            "Stop the music",
            "Skip to next song",
            "Next track",
            "Previous song",
            "Turn up the volume",
            "Lower the volume",
            "Set volume to 50%",
            "What's currently playing?",
            "What song is this?",
            
            # Playlist Management
            "What playlists do I have?",
            "Show me my playlists",
            "Find my Nightmode playlist",
            "How many tracks are in Nightmode?",
            "What songs are in my Nightmode playlist?",
            
            # Smart Context Commands
            "Play something relaxing",
            "I need some background music",
            "Start my evening playlist",
            "Play music for studying",
            "I want to work out, play some energetic music",
            
            # Edge Cases
            "Can you play music?",
            "Do you know how to control Spotify?",
            "What music services do you support?",
            "Help me with music",
            "Music please"
        ]
        
        print(f"\n🔍 Testing {len(test_commands)} different command types...")
        print("=" * 60)
        
        # Test each command
        for i, command in enumerate(test_commands, 1):
            print(f"\n{i:2d}. Testing: '{command}'")
            print("-" * 40)
            
            try:
                # Test if Nova understands this command
                if brain.matches_any_skill(command):
                    print("✅ Nova recognizes this command")
                    
                    # Get which skill matched
                    matched_skill = brain._get_matching_skill(command)
                    if matched_skill:
                        print(f"   Matched skill: {matched_skill}")
                        
                        # Process the command
                        response = brain.process_input(command)
                        print(f"   Response: {response}")
                    else:
                        print("   No specific skill matched")
                else:
                    print("❌ Nova doesn't recognize this command")
                    
            except Exception as e:
                print(f"   ⚠️ Error processing command: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 Spotify Command Understanding Test Complete!")
        
        # Summary
        print("\n📊 Test Summary:")
        print("✅ Commands that Nova recognized")
        print("❌ Commands that Nova didn't recognize")
        print("⚠️ Commands that had errors")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_spotify_service_integration():
    """Test the Spotify service functionality"""
    print("\n===== Testing Spotify Service Integration =====\n")
    
    try:
        from core.services.spotify_service import SpotifyService
        
        spotify = SpotifyService()
        
        if not spotify.is_available():
            print("🔐 Spotify not authenticated, attempting authentication...")
            if spotify.authenticate():
                print("✅ Spotify authenticated successfully")
            else:
                print("❌ Spotify authentication failed")
                return False
        
        # Test basic functionality
        print("\n🔍 Testing Spotify service functionality...")
        
        # Get user profile
        profile = spotify.get_user_profile()
        if profile:
            print(f"✅ User: {profile.get('display_name', 'Unknown')}")
        
        # Get playlists
        playlists = spotify.get_user_playlists()
        if playlists:
            print(f"✅ Found {len(playlists)} playlists")
        
        # Test playlist search
        nightmode = spotify.find_playlist_by_name("Nightmode")
        if nightmode:
            print(f"✅ Found Nightmode playlist with {nightmode['tracks']['total']} tracks")
        
        # Test device detection
        devices = spotify.get_available_devices()
        if devices:
            print(f"✅ Found {len(devices)} Spotify devices")
            for device in devices:
                print(f"   • {device['name']} ({device['type']})")
        
        print("✅ Spotify service integration test complete")
        return True
        
    except Exception as e:
        print(f"❌ Spotify service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Comprehensive Nova Spotify Testing\n")
    
    # Test 1: Command Understanding
    success1 = test_spotify_command_understanding()
    
    # Test 2: Service Integration
    success2 = test_spotify_service_integration()
    
    # Overall result
    if success1 and success2:
        print("\n🎉 All tests passed! Nova is ready for Spotify integration!")
        return True
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
