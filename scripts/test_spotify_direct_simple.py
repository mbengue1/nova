#!/usr/bin/env python3
"""
Simplified test script for direct Spotify control via AppleScript.
This script focuses on just playing the Nightmode playlist.
"""

import os
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the SpotifyAppleScript class
from core.services.spotify_applescript import SpotifyAppleScript

def test_play_nightmode():
    """Test playing the Nightmode playlist directly"""
    print("\n🎵 Testing Direct Nightmode Playback 🎵")
    print("=" * 50)
    
    # Create a SpotifyAppleScript instance
    spotify = SpotifyAppleScript()
    
    # Check if Spotify is available
    print("\n1. Checking if Spotify is available...")
    if not spotify.is_available():
        print("❌ Spotify is not available on this system")
        return False
    print("✅ Spotify is available")
    
    # Use the ensure_ready_and_play_nightmode method
    print("\n2. Starting full Nightmode sequence...")
    success = spotify.ensure_ready_and_play_nightmode()
    
    if success:
        print("✅ Nightmode playlist is now playing")
        
        # Get current track info
        track_info = spotify.get_current_track_info()
        if track_info:
            print(f"🎵 Now playing: {track_info['track']} by {track_info['artist']}")
        
        # Get player state
        state = spotify.get_player_state()
        print(f"🎮 Player state: {state}")
        
        return True
    else:
        print("❌ Failed to play Nightmode playlist")
        return False

if __name__ == "__main__":
    result = test_play_nightmode()
    print("\n" + "=" * 50)
    print(f"🎵 Test result: {'SUCCESS ✅' if result else 'FAILED ❌'}")
    print("=" * 50)
