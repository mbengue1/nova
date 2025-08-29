#!/usr/bin/env python3
"""
Test direct Spotify control via AppleScript.
This bypasses the Spotify API and uses macOS AppleScript to control Spotify directly.
"""

import os
import sys
import time
import subprocess

def test_spotify_direct():
    """Test direct Spotify control via AppleScript"""
    print("\n🎵 Testing Direct Spotify Control 🎵")
    print("=" * 50)
    
    # Get playlist URI from environment variable or use default
    playlist_uri = os.getenv('NIGHTMODE_PLAYLIST_URI', 'spotify:playlist:1x7x1Q7CWyodqzTiiSMNKC')
    
    # 1. Check if Spotify is running, if not launch it
    print("\n1. Checking if Spotify is running...")
    try:
        result = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to (name of processes) contains "Spotify"'],
            capture_output=True, text=True, check=True
        )
        app_running = result.stdout.strip().lower() == "true"
        
        if not app_running:
            print("🚀 Launching Spotify...")
            subprocess.run(["open", "-a", "Spotify"], check=True)
            print("✅ Spotify launch command sent")
            time.sleep(3)  # Wait for Spotify to start
        else:
            print("✅ Spotify is already running")
    except Exception as e:
        print(f"❌ Error checking/launching Spotify: {e}")
        return False
    
    # 2. Activate Spotify (bring to front)
    print("\n2. Activating Spotify...")
    try:
        subprocess.run(["osascript", "-e", 'tell application "Spotify" to activate'], check=True)
        print("✅ Spotify activated")
        time.sleep(1)
    except Exception as e:
        print(f"❌ Error activating Spotify: {e}")
        return False
    
    # 3. Direct play the Nightmode playlist
    print("\n3. Playing Nightmode playlist directly...")
    try:
        # Method 1: Try direct URI play
        play_uri_cmd = f'tell application "Spotify" to play track "{playlist_uri}"'
        subprocess.run(["osascript", "-e", play_uri_cmd], check=True)
        print("✅ Direct URI play command sent")
    except Exception as e:
        print(f"❌ Error playing playlist directly: {e}")
        
        # Method 2: Try opening the URI with the open command
        try:
            print("🔄 Trying alternative method...")
            subprocess.run(["open", playlist_uri], check=True)
            print("✅ Open URI command sent")
            time.sleep(2)
            
            # Try to play
            subprocess.run(["osascript", "-e", 'tell application "Spotify" to play'], check=True)
            print("✅ Play command sent")
        except Exception as e:
            print(f"❌ Alternative method failed: {e}")
            return False
    
    # 4. Verify playback
    print("\n4. Verifying playback...")
    time.sleep(2)  # Give it a moment to start playing
    try:
        # Check player state
        result = subprocess.run(
            ["osascript", "-e", 'tell application "Spotify" to player state as string'],
            capture_output=True, text=True, check=True
        )
        player_state = result.stdout.strip()
        print(f"🎮 Player state: {player_state}")
        
        if player_state.lower() == "playing":
            print("✅ Music is playing!")
            
            # Get current track info
            result = subprocess.run(
                ["osascript", "-e", 'tell application "Spotify" to name of current track as string'],
                capture_output=True, text=True, check=True
            )
            current_track = result.stdout.strip()
            
            result = subprocess.run(
                ["osascript", "-e", 'tell application "Spotify" to artist of current track as string'],
                capture_output=True, text=True, check=True
            )
            current_artist = result.stdout.strip()
            
            print(f"🎵 Now playing: {current_track} by {current_artist}")
            
            # Set volume
            volume_cmd = 'tell application "Spotify" to set sound volume to 50'
            subprocess.run(["osascript", "-e", volume_cmd], check=True)
            print("✅ Volume set to 50%")
            
            return True
        else:
            print("❌ Music is not playing")
            return False
    except Exception as e:
        print(f"❌ Error verifying playback: {e}")
        return False

if __name__ == "__main__":
    success = test_spotify_direct()
    print("\n" + "=" * 50)
    print(f"🎵 Test result: {'SUCCESS ✅' if success else 'FAILED ❌'}")
    print("=" * 50)
