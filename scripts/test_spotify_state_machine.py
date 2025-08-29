#!/usr/bin/env python3
"""
Test script for the new Spotify state machine.
This script tests the robust Spotify playback state machine.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Import required modules
from core.services.spotify_auth import SpotifyAuth
from core.services.spotify_service import SpotifyService

def test_spotify_state_machine():
    """Test the Spotify state machine flow"""
    print("\n🎵 Testing Spotify State Machine Flow 🎵")
    print("=" * 50)
    
    # Initialize Spotify service
    print("\n1. Initializing Spotify service...")
    spotify = SpotifyService()
    
    # Define the playlist to play
    playlist_name = "Nightmode"
    
    # Define the state machine flow
    def play_spotify_with_state_machine(playlist_name, max_timeout=40):
        """
        Robust state machine for playing Spotify with proper state transitions.
        
        States:
        1. AUTH_READY - Check if Spotify auth is valid
        2. APP_READY - Check if Spotify app is running and responsive
        3. DEVICE_READY - Ensure we have an active device
        4. PLAYBACK_READY - Prepare playback settings
        5. PLAYING - Successfully playing music
        """
        import subprocess
        
        start_time = time.time()
        
        # STATE 1: AUTH_READY - Verify Spotify auth
        print("\n2. 🔑 Checking Spotify authentication...")
        if not spotify.is_available():
            print("❌ Spotify authentication not available")
            return "auth_error"
        print("✅ Spotify authentication is valid")
            
        # STATE 2: APP_READY - Check if app is running
        print("\n3. 🔍 Checking if Spotify app is running...")
        
        # Check if Spotify is running using AppleScript
        try:
            result = subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to (name of processes) contains "Spotify"'],
                capture_output=True, text=True, check=True
            )
            app_running = result.stdout.strip().lower() == "true"
            
            if not app_running:
                print("🚀 Launching Spotify...")
                # Launch Spotify
                subprocess.run(["open", "-a", "Spotify"], check=True)
                print("✅ Spotify launch command sent")
                
                # Wait for app to start (up to 15 seconds)
                app_ready = False
                for attempt in range(15):
                    if time.time() - start_time > max_timeout:
                        print(f"⏰ Overall timeout reached ({max_timeout}s)")
                        return "timeout"
                        
                    time.sleep(1)
                    try:
                        # Check if app is responding via API
                        devices = spotify.get_available_devices()
                        if devices:
                            print(f"✅ Spotify app ready after {attempt + 1} seconds")
                            app_ready = True
                            break
                    except Exception as e:
                        print(f"⏳ Waiting for Spotify app... ({attempt + 1}s)")
                
                if not app_ready:
                    # Try to prod the app by opening a URI
                    print("🔄 Prodding Spotify app with URI...")
                    subprocess.run(["open", "spotify:app"], check=True)
                    
                    # Wait another 10 seconds
                    for attempt in range(10):
                        if time.time() - start_time > max_timeout:
                            print(f"⏰ Overall timeout reached ({max_timeout}s)")
                            return "timeout"
                            
                        time.sleep(1)
                        try:
                            devices = spotify.get_available_devices()
                            if devices:
                                print(f"✅ Spotify app ready after prod ({attempt + 1}s)")
                                app_ready = True
                                break
                        except Exception:
                            print(f"⏳ Still waiting for Spotify... ({attempt + 1}s)")
                    
                    if not app_ready:
                        print("❌ Spotify app failed to respond")
                        return "app_not_ready"
            else:
                print("✅ Spotify app is already running")
                app_ready = True
        except Exception as e:
            print(f"❌ Error checking Spotify app: {e}")
            # Try to continue anyway
            app_ready = True
            
        # STATE 3: DEVICE_READY - Ensure we have an active device
        print("\n4. 🎮 Checking for available Spotify devices...")
        try:
            devices = spotify.get_available_devices()
            if not devices:
                print("❌ No Spotify devices found")
                return "no_devices"
                
            print(f"📱 Found {len(devices)} devices:")
            for i, device in enumerate(devices):
                print(f"   Device {i+1}: {device.get('name', 'Unknown')} - Active: {device.get('is_active', False)} - Type: {device.get('type', 'Unknown')}")
            
            # Find the best device to use (prefer Computer type)
            target_device = None
            
            # First, look for an already active device
            active_devices = [d for d in devices if d.get('is_active', False)]
            if active_devices:
                target_device = active_devices[0]
                print(f"✅ Using already active device: {target_device.get('name')}")
            else:
                # Next, prefer Computer type devices (likely this machine)
                computer_devices = [d for d in devices if d.get('type') == 'Computer']
                if computer_devices:
                    target_device = computer_devices[0]
                    print(f"✅ Using computer device: {target_device.get('name')}")
                else:
                    # Fall back to first available device
                    target_device = devices[0]
                    print(f"✅ Using available device: {target_device.get('name')}")
            
            # If device is not active, activate it
            if not target_device.get('is_active', False):
                print(f"🔧 Activating device: {target_device.get('name')}")
                device_id = target_device.get('id')
                
                # Retry up to 4 times with backoff
                backoff_times = [0.25, 0.5, 1, 2]
                activated = False
                
                for attempt, backoff in enumerate(backoff_times):
                    if time.time() - start_time > max_timeout:
                        print(f"⏰ Overall timeout reached ({max_timeout}s)")
                        return "timeout"
                        
                    try:
                        # Transfer playback to this device
                        spotify._make_request('PUT', 'https://api.spotify.com/v1/me/player', 
                                             data={'device_ids': [device_id], 'play': False})
                        print(f"✅ Device activated on attempt {attempt + 1}")
                        activated = True
                        break
                    except Exception as e:
                        print(f"⚠️ Activation attempt {attempt + 1} failed: {e}")
                        time.sleep(backoff)
                
                if not activated:
                    print("❌ Failed to activate device after multiple attempts")
                    # Try to continue anyway
            
            # STATE 4: PLAYBACK_READY - Prepare playback settings
            print("\n5. 🎵 Preparing to play playlist...")
            
            # Find the playlist
            playlist = spotify.find_playlist_by_name(playlist_name)
            if not playlist:
                print(f"❌ Playlist '{playlist_name}' not found")
                return "playlist_not_found"
            
            print(f"✅ Found playlist: {playlist.get('name')} (ID: {playlist.get('id')})")
            
            # Configure player settings (optional)
            try:
                # Set shuffle off
                spotify._make_request('PUT', 'https://api.spotify.com/v1/me/player/shuffle?state=false')
                print("✅ Shuffle turned off")
            except Exception as e:
                print(f"⚠️ Could not set shuffle: {e}")
            
            # STATE 5: PLAYING - Start playback
            print("\n6. ▶️ Starting playlist...")
            
            # Try up to 2 times to start playback
            for attempt in range(2):
                if time.time() - start_time > max_timeout:
                    print(f"⏰ Overall timeout reached ({max_timeout}s)")
                    return "timeout"
                    
                try:
                    # Start the playlist
                    spotify.start_playlist(playlist_name)
                    
                    # Verify playback started
                    print("🔍 Verifying playback...")
                    playback_verified = False
                    
                    # Poll player state up to 10 times
                    for verify_attempt in range(10):
                        if time.time() - start_time > max_timeout:
                            print(f"⏰ Overall timeout reached ({max_timeout}s)")
                            return "timeout"
                            
                        time.sleep(1)
                        try:
                            # Check current playback
                            player_state = spotify._make_request('GET', 'https://api.spotify.com/v1/me/player')
                            
                            # Check if playing
                            if player_state and player_state.get('is_playing'):
                                print(f"✅ Playback verified after {verify_attempt + 1}s")
                                playback_verified = True
                                break
                        except Exception as e:
                            print(f"⏳ Waiting for playback confirmation... ({verify_attempt + 1}s)")
                    
                    if playback_verified:
                        print(f"\n🎉 Successfully playing {playlist_name} playlist")
                        return "playing"
                    else:
                        print("⚠️ Playback not confirmed, retrying...")
                        
                except Exception as e:
                    print(f"❌ Playback attempt {attempt + 1} failed: {e}")
                    time.sleep(1)
            
            print("❌ Failed to start playback after multiple attempts")
            return "playback_failed"
            
        except Exception as e:
            print(f"❌ Device error: {e}")
            return "device_error"
            
        # If we reach here, something went wrong
        print("❌ Unknown error in Spotify state machine")
        return "unknown_error"
    
    # Run the state machine
    result = play_spotify_with_state_machine(playlist_name)
    
    # Print final result
    print("\n" + "=" * 50)
    print(f"🎵 Final result: {result}")
    print("=" * 50)
    
    # Ask user for confirmation
    if result == "playing":
        input("\nIs music playing? Press Enter to continue...")
    
    return result

if __name__ == "__main__":
    test_spotify_state_machine()
