#!/usr/bin/env python3
"""
Direct Spotify control via AppleScript.
This bypasses the Spotify Web API and uses macOS AppleScript to control Spotify directly.
"""

import os
import subprocess
import time
import logging

logger = logging.getLogger(__name__)

class SpotifyAppleScript:
    """Direct Spotify control via AppleScript"""
    
    def __init__(self):
        """Initialize the SpotifyAppleScript controller"""
        self.is_macos = self._is_macos()
        
    def _is_macos(self):
        """Check if running on macOS"""
        return os.name == 'posix' and os.uname().sysname == 'Darwin'
    
    def is_available(self):
        """Check if Spotify is available on this system"""
        if not self.is_macos:
            return False
        
        try:
            # Check if Spotify app exists in Applications folder
            import os
            return os.path.exists("/Applications/Spotify.app")
        except Exception as e:
            logger.error(f"Error checking Spotify availability: {e}")
            return False
    
    def is_running(self):
        """Check if Spotify is currently running"""
        if not self.is_macos:
            return False
        
        try:
            result = subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to (name of processes) contains "Spotify"'],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip().lower() == "true"
        except Exception as e:
            logger.error(f"Error checking if Spotify is running: {e}")
            return False
    
    def launch(self):
        """Launch Spotify application"""
        if not self.is_macos:
            return False
        
        try:
            if not self.is_running():
                subprocess.run(["open", "-a", "Spotify"], check=True)
                logger.info("Spotify launch command sent")
                return True
            else:
                logger.info("Spotify is already running")
                return True
        except Exception as e:
            logger.error(f"Error launching Spotify: {e}")
            return False
    
    def activate(self):
        """Bring Spotify to the foreground"""
        if not self.is_macos:
            return False
        
        try:
            subprocess.run(["osascript", "-e", 'tell application "Spotify" to activate'], check=True)
            logger.info("Spotify activated")
            return True
        except Exception as e:
            logger.error(f"Error activating Spotify: {e}")
            return False
    
    def play(self):
        """Play current track"""
        if not self.is_macos:
            return False
        
        try:
            subprocess.run(["osascript", "-e", 'tell application "Spotify" to play'], check=True)
            logger.info("Play command sent")
            return True
        except Exception as e:
            logger.error(f"Error playing: {e}")
            return False
    
    def pause(self):
        """Pause playback"""
        if not self.is_macos:
            return False
        
        try:
            subprocess.run(["osascript", "-e", 'tell application "Spotify" to pause'], check=True)
            logger.info("Pause command sent")
            return True
        except Exception as e:
            logger.error(f"Error pausing: {e}")
            return False
    
    def next_track(self):
        """Skip to next track"""
        if not self.is_macos:
            return False
        
        try:
            subprocess.run(["osascript", "-e", 'tell application "Spotify" to next track'], check=True)
            logger.info("Next track command sent")
            return True
        except Exception as e:
            logger.error(f"Error skipping to next track: {e}")
            return False
    
    def previous_track(self):
        """Go back to previous track"""
        if not self.is_macos:
            return False
        
        try:
            subprocess.run(["osascript", "-e", 'tell application "Spotify" to previous track'], check=True)
            logger.info("Previous track command sent")
            return True
        except Exception as e:
            logger.error(f"Error going to previous track: {e}")
            return False
    
    def _get_current_volume(self):
        """Get current volume (0-100)"""
        if not self.is_macos:
            return None
        
        try:
            result = subprocess.run(
                ["osascript", "-e", 'tell application "Spotify" to get sound volume'],
                capture_output=True, text=True, check=True
            )
            volume = int(result.stdout.strip())
            return volume
        except Exception as e:
            logger.error(f"Error getting current volume: {e}")
            return None
    
    def set_volume(self, volume_percent):
        """Set volume (0-100)"""
        if not self.is_macos:
            return False
        
        try:
            # Ensure volume is between 0-100
            volume = max(0, min(100, volume_percent))
            subprocess.run(["osascript", "-e", f'tell application "Spotify" to set sound volume to {volume}'], check=True)
            logger.info(f"Volume set to {volume}%")
            return True
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return False
    
    def get_current_track_info(self):
        """Get information about the current track"""
        if not self.is_macos:
            return None
        
        try:
            # Get track name
            result = subprocess.run(
                ["osascript", "-e", 'tell application "Spotify" to name of current track as string'],
                capture_output=True, text=True, check=True
            )
            track_name = result.stdout.strip()
            
            # Get artist name
            result = subprocess.run(
                ["osascript", "-e", 'tell application "Spotify" to artist of current track as string'],
                capture_output=True, text=True, check=True
            )
            artist_name = result.stdout.strip()
            
            # Get album name
            result = subprocess.run(
                ["osascript", "-e", 'tell application "Spotify" to album of current track as string'],
                capture_output=True, text=True, check=True
            )
            album_name = result.stdout.strip()
            
            return {
                "track": track_name,
                "artist": artist_name,
                "album": album_name
            }
        except Exception as e:
            logger.error(f"Error getting track info: {e}")
            return None
    
    def get_player_state(self):
        """Get current player state (playing, paused, stopped)"""
        if not self.is_macos:
            return None
        
        try:
            result = subprocess.run(
                ["osascript", "-e", 'tell application "Spotify" to player state as string'],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip().lower()
        except Exception as e:
            logger.error(f"Error getting player state: {e}")
            return None
    
    def play_playlist(self, playlist_uri):
        """Play a specific playlist by URI"""
        if not self.is_macos:
            return False
        
        try:
            # Ensure Spotify is running and activated
            self.launch()
            time.sleep(1)
            self.activate()
            time.sleep(1)
            
            # Play the playlist
            play_uri_cmd = f'tell application "Spotify" to play track "{playlist_uri}"'
            subprocess.run(["osascript", "-e", play_uri_cmd], check=True)
            logger.info(f"Play playlist command sent: {playlist_uri}")
            return True
        except Exception as e:
            logger.error(f"Error playing playlist: {e}")
            
            # Try fallback - just play whatever is loaded
            try:
                self.play()
                return True
            except:
                return False
    
    def play_nightmode(self):
        """Play the Nightmode playlist"""
        # Get playlist URI from environment variable or use default
        import os
        playlist_uri = os.getenv('NIGHTMODE_PLAYLIST_URI', 'spotify:playlist:1x7x1Q7CWyodqzTiiSMNKC')
        return self.play_playlist(playlist_uri)
    
    def ensure_ready_and_play_nightmode(self):
        """Full sequence to ensure Spotify is ready and play Nightmode playlist"""
        try:
            # 1. Launch Spotify if not running
            if not self.is_running():
                logger.info("Spotify not running, launching...")
                self.launch()
                time.sleep(3)  # Give it time to start
            
            # 2. Activate Spotify (bring to front)
            self.activate()
            time.sleep(1)
            
            # 3. Play Nightmode playlist
            success = self.play_nightmode()
            
            # 4. Don't change volume - respect user's current setting
            # Only set volume if it's extremely low (below 20%)
            if success:
                try:
                    # Get current volume and only adjust if it's too low
                    current_volume = self._get_current_volume()
                    if current_volume is not None and current_volume < 20:
                        self.set_volume(80)  # Set to 80% only if it was very low
                        logger.info(f"Volume was very low ({current_volume}%), adjusted to 80%")
                    else:
                        logger.info(f"Volume left at current level ({current_volume}%)")
                except Exception as e:
                    logger.warning(f"Could not check/adjust volume: {e}")
            
            # 5. Verify playback
            time.sleep(2)  # Give it a moment to start playing
            player_state = self.get_player_state()
            
            if player_state == "playing":
                track_info = self.get_current_track_info()
                if track_info:
                    logger.info(f"Now playing: {track_info['track']} by {track_info['artist']}")
                return True
            else:
                logger.warning(f"Player state after play attempt: {player_state}")
                # Try one more time with direct play command
                self.play()
                return True
                
        except Exception as e:
            logger.error(f"Error in ensure_ready_and_play_nightmode: {e}")
            return False
