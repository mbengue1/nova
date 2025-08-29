#!/usr/bin/env python3
"""
Test direct Spotify control via AppleScript.
This bypasses the Spotify API and uses macOS AppleScript to control Spotify directly.
"""

import os
import sys
import time
import subprocess

def test_spotify_applescript():
    """Test Spotify control via AppleScript"""
    print("\n🎵 Testing Spotify Control via AppleScript 🎵")
    print("=" * 50)
    
    # Check if Spotify is running
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
    
    # Activate Spotify (bring to front)
    print("\n2. Activating Spotify...")
    try:
        subprocess.run(["osascript", "-e", 'tell application "Spotify" to activate'], check=True)
        print("✅ Spotify activated")
        time.sleep(1)
    except Exception as e:
        print(f"❌ Error activating Spotify: {e}")
        return False
    
    # Get current track info
    print("\n3. Getting current track info...")
    try:
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
        
        print(f"🎵 Current track: {current_track} by {current_artist}")
    except Exception as e:
        print(f"⚠️ Could not get track info: {e}")
    
    # Get player state
    print("\n4. Getting player state...")
    try:
        result = subprocess.run(
            ["osascript", "-e", 'tell application "Spotify" to player state as string'],
            capture_output=True, text=True, check=True
        )
        player_state = result.stdout.strip()
        print(f"🎮 Player state: {player_state}")
    except Exception as e:
        print(f"❌ Error getting player state: {e}")
    
    # Search for Nightmode playlist
    print("\n5. Searching for Nightmode playlist...")
    try:
        # The search command is different in AppleScript for Spotify
        # We'll try to play a specific playlist instead
        # Get playlist URI from environment variable or use default
        playlist_uri = os.getenv('NIGHTMODE_PLAYLIST_URI', 'spotify:playlist:1x7x1Q7CWyodqzTiiSMNKC')
        search_cmd = f'tell application "Spotify" to play track "{playlist_uri}"'
        subprocess.run(["osascript", "-e", search_cmd], check=True)
        print("✅ Play Nightmode playlist command sent")
        time.sleep(2)  # Wait for search results
    except Exception as e:
        print(f"❌ Error playing playlist: {e}")
        
        # Fallback to just playing whatever is currently loaded
        try:
            play_cmd = 'tell application "Spotify" to play'
            subprocess.run(["osascript", "-e", play_cmd], check=True)
            print("✅ Generic play command sent as fallback")
        except Exception as e:
            print(f"❌ Fallback play failed: {e}")
    
    # Prime device with play/pause cycle
    print("\n6. Priming device with play/pause cycle...")
    try:
        # Play
        play_cmd = 'tell application "Spotify" to play'
        subprocess.run(["osascript", "-e", play_cmd], check=True)
        print("✅ Play command sent")
        time.sleep(2)
        
        # Pause
        pause_cmd = 'tell application "Spotify" to pause'
        subprocess.run(["osascript", "-e", pause_cmd], check=True)
        print("✅ Pause command sent")
        time.sleep(1)
        
        # Play again
        play_cmd = 'tell application "Spotify" to play'
        subprocess.run(["osascript", "-e", play_cmd], check=True)
        print("✅ Second play command sent")
        time.sleep(1)
    except Exception as e:
        print(f"❌ Error during device priming: {e}")
    
    # Verify playback
    print("\n7. Verifying playback...")
    try:
        result = subprocess.run(
            ["osascript", "-e", 'tell application "Spotify" to player state as string'],
            capture_output=True, text=True, check=True
        )
        player_state = result.stdout.strip()
        print(f"🎮 Player state: {player_state}")
        
        if player_state.lower() == "playing":
            print("✅ Music is playing!")
            
            # Get current track info again
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
        else:
            print("❌ Music is not playing")
    except Exception as e:
        print(f"❌ Error verifying playback: {e}")
    
    # Set volume
    print("\n8. Setting volume to 50%...")
    try:
        volume_cmd = 'tell application "Spotify" to set sound volume to 50'
        subprocess.run(["osascript", "-e", volume_cmd], check=True)
        print("✅ Volume set to 50%")
    except Exception as e:
        print(f"❌ Error setting volume: {e}")
    
    print("\n" + "=" * 50)
    print("🎵 AppleScript test completed")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    test_spotify_applescript()
