#!/usr/bin/env python3
"""
Test the SpotifyAppleScript class.
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

def test_spotify_applescript():
    """Test the SpotifyAppleScript class"""
    print("\n🎵 Testing SpotifyAppleScript 🎵")
    print("=" * 50)
    
    # Create a SpotifyAppleScript instance
    spotify = SpotifyAppleScript()
    
    # Check if Spotify is available
    print("\n1. Checking if Spotify is available...")
    available = spotify.is_available()
    print(f"✅ Spotify available: {available}")
    
    if not available:
        print("❌ Spotify is not available on this system")
        return False
    
    # Check if Spotify is running
    print("\n2. Checking if Spotify is running...")
    running = spotify.is_running()
    print(f"✅ Spotify running: {running}")
    
    # Launch Spotify if not running
    if not running:
        print("\n3. Launching Spotify...")
        launched = spotify.launch()
        print(f"✅ Spotify launched: {launched}")
        time.sleep(3)  # Give it time to start
    
    # Activate Spotify
    print("\n4. Activating Spotify...")
    activated = spotify.activate()
    print(f"✅ Spotify activated: {activated}")
    time.sleep(1)
    
    # Get player state
    print("\n5. Getting player state...")
    state = spotify.get_player_state()
    print(f"✅ Player state: {state}")
    
    # Play Nightmode playlist
    print("\n6. Playing Nightmode playlist...")
    played = spotify.play_nightmode()
    print(f"✅ Nightmode playlist played: {played}")
    time.sleep(2)
    
    # Get current track info
    print("\n7. Getting current track info...")
    track_info = spotify.get_current_track_info()
    if track_info:
        print(f"✅ Now playing: {track_info['track']} by {track_info['artist']} from {track_info['album']}")
    else:
        print("❌ Could not get track info")
    
    # Set volume
    print("\n8. Setting volume to 50%...")
    volume_set = spotify.set_volume(50)
    print(f"✅ Volume set: {volume_set}")
    
    # Test full sequence
    print("\n9. Testing full sequence...")
    success = spotify.ensure_ready_and_play_nightmode()
    print(f"✅ Full sequence success: {success}")
    
    print("\n" + "=" * 50)
    print("🎵 SpotifyAppleScript test completed")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    test_spotify_applescript()
