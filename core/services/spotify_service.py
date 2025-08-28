"""
Spotify Service for Nova

This module provides comprehensive Spotify control functionality:
- Playback control (play, pause, skip, volume)
- Playlist management
- Track information
- Integration with Nova's greeting system
"""
import os
import requests
import time
from typing import Optional, Dict, Any, List, Tuple
from .spotify_auth import SpotifyAuth

class SpotifyService:
    """Main service for controlling Spotify playback and managing music"""
    
    def __init__(self):
        """Initialize Spotify service"""
        self.auth = SpotifyAuth()
        self.base_url = "https://api.spotify.com/v1"
        self.current_device_id = None
        
        # Default playlist for private mode (configurable)
        self.default_playlist = os.getenv('SPOTIFY_DEFAULT_PLAYLIST', 'Nightmode')
        
        print("🎵 Spotify service initialized")
    
    def is_available(self) -> bool:
        """Check if Spotify service is available and authenticated"""
        return self.auth.is_authenticated()
    
    def authenticate(self) -> bool:
        """Authenticate with Spotify if not already authenticated"""
        if self.is_available():
            print("✅ Spotify already authenticated")
            return True
        
        print("🔐 Spotify authentication required...")
        return self.auth.authenticate()
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to Spotify API"""
        if not self.is_available():
            print("❌ Spotify not authenticated")
            return None
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.auth.get_access_token()}',
            'Content-Type': 'application/json'
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            else:
                print(f"❌ Unsupported HTTP method: {method}")
                return None
            
            if response.status_code in [200, 201, 204]:
                # 200: OK, 201: Created, 204: No Content (success for PUT requests)
                if response.status_code == 204:
                    return {"success": True, "status": "no_content"}  # Consistent response format
                try:
                    return response.json()
                except ValueError:
                    # Response is not JSON, return success indicator
                    return {"success": True, "status": "non_json"}
            elif response.status_code == 401:
                # Token expired, try to refresh
                if self.auth.is_authenticated():
                    # Retry the request with new token
                    headers['Authorization'] = f'Bearer {self.auth.get_access_token()}'
                    if method.upper() == 'GET':
                        response = requests.get(url, headers=headers)
                    elif method.upper() == 'POST':
                        response = requests.post(url, headers=headers, json=data)
                    elif method.upper() == 'PUT':
                        response = requests.put(url, headers=headers, json=data)
                    
                    if response.status_code == 200:
                        return response.json()
                
                print("❌ Spotify authentication expired")
                return None
            else:
                print(f"❌ Spotify API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error making Spotify request: {e}")
            return None
    
    def get_user_profile(self) -> Optional[Dict]:
        """Get current user's Spotify profile"""
        return self._make_request('GET', '/me')
    
    def get_available_devices(self) -> List[Dict]:
        """Get list of available Spotify devices"""
        response = self._make_request('GET', '/me/player/devices')
        if response and 'devices' in response:
            return response['devices']
        return []
    
    def get_current_playback(self) -> Optional[Dict]:
        """Get current playback information"""
        return self._make_request('GET', '/me/player')
    
    def get_user_playlists(self) -> List[Dict]:
        """Get user's playlists"""
        response = self._make_request('GET', '/me/playlists?limit=50')
        if response and 'items' in response:
            return response['items']
        return []
    
    def find_playlist_by_name(self, playlist_name: str) -> Optional[Dict]:
        """Find a playlist by name (case-insensitive)"""
        playlists = self.get_user_playlists()
        
        for playlist in playlists:
            if playlist['name'].lower() == playlist_name.lower():
                return playlist
        
        return None
    
    def start_playlist(self, playlist_name: str = None) -> bool:
        """Start playing a specific playlist"""
        if not playlist_name:
            playlist_name = self.default_playlist
        
        # Find the playlist
        playlist = self.find_playlist_by_name(playlist_name)
        if not playlist:
            print(f"❌ Playlist '{playlist_name}' not found")
            return False
        
        # Check what's currently playing
        current_playback = self.get_current_playback()
        if current_playback and current_playback.get('context'):
            current_uri = current_playback['context'].get('uri', '')
            current_playlist_id = current_playback['context'].get('external_urls', {}).get('spotify', '')
            
            # Check if the requested playlist is already playing
            if current_uri == playlist['uri']:
                if current_playback.get('is_playing', False):
                    print(f"🎵 Playlist '{playlist_name}' is already playing!")
                    return True  # Success - it's already playing what you want
                else:
                    print(f"⏸️ Playlist '{playlist_name}' is loaded but paused. Resuming...")
                    return self.play()  # Resume the already-loaded playlist
            else:
                print(f"🔄 Different playlist currently loaded. Switching to '{playlist_name}'...")
        
        # Get available devices
        devices = self.get_available_devices()
        if not devices:
            print("❌ No Spotify devices available")
            return False
        
        # Use the first available device (usually the most recently active)
        device_id = devices[0]['id']
        
        # Start the playlist
        data = {
            'context_uri': playlist['uri'],
            'device_id': device_id
        }
        
        response = self._make_request('PUT', '/me/player/play', data)
        if response is not None:
            print(f"✅ Started playing playlist: {playlist['name']}")
            self.current_device_id = device_id
            return True
        else:
            print(f"❌ Failed to start playlist: {playlist['name']}")
            return False
    
    def start_default_playlist(self) -> bool:
        """Start the default playlist (used in private mode)"""
        return self.start_playlist(self.default_playlist)
    
    def smart_start_music(self) -> str:
        """Smart method to start music with intelligent responses"""
        current_playback = self.get_current_playback()
        
        if not current_playback:
            # Nothing loaded, start default playlist
            if self.start_playlist(self.default_playlist):
                return f"Started playing your {self.default_playlist} playlist!"
            else:
                return "I couldn't start playing music. Please check if Spotify is running."
        
        # Check if default playlist is already playing
        if current_playback.get('context') and current_playback['context'].get('uri'):
            current_uri = current_playback['context']['uri']
            default_playlist = self.find_playlist_by_name(self.default_playlist)
            
            if default_playlist and current_uri == default_playlist['uri']:
                if current_playback.get('is_playing', False):
                    return f"Your {self.default_playlist} playlist is already playing!"
                else:
                    if self.play():
                        return f"Resumed your {self.default_playlist} playlist!"
                    else:
                        return "I couldn't resume the music. Please check Spotify."
            else:
                # Different playlist playing, switch to default
                if self.start_playlist(self.default_playlist):
                    return f"Switched to your {self.default_playlist} playlist!"
                else:
                    return "I couldn't switch playlists. Please check Spotify."
        
        # Fallback
        if self.start_playlist(self.default_playlist):
            return f"Started playing your {self.default_playlist} playlist!"
        else:
            return "I couldn't start playing music. Please check Spotify."
    
    def play(self) -> bool:
        """Resume playback"""
        data = {}
        if self.current_device_id:
            data['device_id'] = self.current_device_id
        
        response = self._make_request('PUT', '/me/player/play', data)
        if response is not None:
            print("✅ Playback resumed")
            return True
        else:
            print("❌ Failed to resume playback")
            return False
    
    def pause(self) -> bool:
        """Pause playback"""
        response = self._make_request('PUT', '/me/player/pause')
        if response is not None:
            print("⏸️ Playback paused")
            return True
        else:
            print("❌ Failed to pause playback")
            return False
    
    def skip_to_next(self) -> bool:
        """Skip to next track"""
        response = self._make_request('POST', '/me/player/next')
        if response is not None:
            print("⏭️ Skipped to next track")
            return True
        else:
            print("❌ Failed to skip to next track")
            return False
    
    def skip_to_previous(self) -> bool:
        """Skip to previous track"""
        response = self._make_request('POST', '/me/player/previous')
        if response is not None:
            print("⏮️ Skipped to previous track")
            return True
        else:
            print("❌ Failed to skip to previous track")
            return False
    
    def set_volume(self, volume_percent: int) -> bool:
        """Set playback volume (0-100)"""
        if not 0 <= volume_percent <= 100:
            print("❌ Volume must be between 0 and 100")
            return False
        
        endpoint = f'/me/player/volume?volume_percent={volume_percent}'
        if self.current_device_id:
            endpoint += f'&device_id={self.current_device_id}'
        
        response = self._make_request('PUT', endpoint)
        if response is not None:
            print(f"🔊 Volume set to {volume_percent}%")
            return True
        else:
            print(f"❌ Failed to set volume to {volume_percent}%")
            return False
    
    def get_current_track(self) -> Optional[Dict]:
        """Get information about the currently playing track"""
        playback = self.get_current_playback()
        if playback and playback['is_playing'] and 'item' in playback:
            return playback['item']
        return None
    
    def get_current_track_info(self) -> str:
        """Get formatted information about the current track"""
        track = self.get_current_track()
        if track:
            artist = track['artists'][0]['name'] if track['artists'] else 'Unknown Artist'
            title = track['name']
            album = track['album']['name'] if track['album'] else 'Unknown Album'
            return f"{title} by {artist} from {album}"
        return "No track currently playing"
    
    def is_playing(self) -> bool:
        """Check if music is currently playing"""
        playback = self.get_current_playback()
        return playback and playback.get('is_playing', False)
    
    def stop_playback(self) -> bool:
        """Stop playback (pause and reset to beginning)"""
        # First pause
        if not self.pause():
            return False
        
        # Then seek to beginning
        response = self._make_request('PUT', '/me/player/seek?position_ms=0')
        if response is not None:
            print("⏹️ Playback stopped")
            return True
        else:
            print("❌ Failed to stop playback")
            return False
    
    def set_default_playlist(self, playlist_name: str) -> bool:
        """Set the default playlist for private mode"""
        # Verify the playlist exists
        playlist = self.find_playlist_by_name(playlist_name)
        if not playlist:
            print(f"❌ Playlist '{playlist_name}' not found")
            return False
        
        self.default_playlist = playlist_name
        print(f"✅ Default playlist set to: {playlist_name}")
        return True
    
    def get_playlist_info(self, playlist_name: str = None) -> Optional[Dict]:
        """Get detailed information about a playlist"""
        if not playlist_name:
            playlist_name = self.default_playlist
        
        playlist = self.find_playlist_by_name(playlist_name)
        if not playlist:
            return None
        
        # Get detailed playlist information
        playlist_id = playlist['id']
        response = self._make_request('GET', f'/playlists/{playlist_id}')
        return response
    
    def get_playlist_tracks(self, playlist_name: str = None) -> List[Dict]:
        """Get tracks from a specific playlist"""
        playlist = self.get_playlist_info(playlist_name)
        if not playlist or 'tracks' not in playlist:
            return []
        
        tracks = []
        for item in playlist['tracks']['items']:
            if item['track']:
                track_info = {
                    'name': item['track']['name'],
                    'artist': item['track']['artists'][0]['name'] if item['track']['artists'] else 'Unknown',
                    'album': item['track']['album']['name'] if item['track']['album'] else 'Unknown',
                    'duration_ms': item['track']['duration_ms']
                }
                tracks.append(track_info)
        
        return tracks
    
    def cleanup(self) -> None:
        """Clean up Spotify service resources"""
        try:
            # Clear current device reference
            self.current_device_id = None
            
            # Clear auth reference
            if hasattr(self, 'auth'):
                self.auth = None
            
            print("🔇 Spotify service cleanup complete")
        except Exception as e:
            print(f"⚠️ Error during Spotify service cleanup: {e}")
