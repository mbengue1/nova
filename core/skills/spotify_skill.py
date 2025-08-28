"""
Spotify Skill for Nova

This skill handles all Spotify-related commands including:
- Playing music and playlists
- Playback control (play, pause, skip, volume)
- Playlist management and information
- Smart music requests
"""
import re
import logging
from typing import Optional, List, Dict, Any
from core.services.spotify_service import SpotifyService

class SpotifySkill:
    """Skill for handling Spotify music commands"""
    
    def __init__(self, spotify_service: SpotifyService):
        """Initialize Spotify skill with service"""
        self.spotify = spotify_service
        self.logger = logging.getLogger("nova.spotify_skill")
        
        # Command patterns for different types of requests
        self.patterns = {
            # Play music commands
            'play_music': [
                r'play\s+(?:some\s+)?music',
                r'start\s+(?:playing\s+)?music',
                r'play\s+(?:some\s+)?tunes?',
                r'start\s+(?:some\s+)?tunes?',
                r'i\s+want\s+to\s+listen\s+to\s+music',
                r'i\s+need\s+(?:some\s+)?music',
                r'start\s+music',
                r'music\s+please',
                r'play\s+something',
                r'start\s+something'
            ],
            
            # Play specific playlist
            'play_playlist': [
                r'play\s+(?:my\s+)?(?:playlist\s+)?([a-zA-Z0-9\s\-_]+?)(?:\s+playlist)?(?:\s+on\s+spotify)?$',
                r'start\s+(?:playing\s+)?(?:my\s+)?(?:playlist\s+)?([a-zA-Z0-9\s\-_]+?)(?:\s+playlist)?(?:\s+on\s+spotify)?$',
                r'play\s+(?:the\s+)?([a-zA-Z0-9\s\-_]+?)(?:\s+playlist)?(?:\s+on\s+spotify)?$',
                r'start\s+(?:the\s+)?([a-zA-Z0-9\s\-_]+?)(?:\s+playlist)?(?:\s+on\s+spotify)?$',
                r'play\s+([a-zA-Z0-9\s\-_]+?)\s+on\s+spotify$',
                r'start\s+([a-zA-Z0-9\s\-_]+?)\s+on\s+spotify$'
            ],
            
            # Playback control
            'pause_music': [
                r'pause\s+(?:the\s+)?music',
                r'stop\s+(?:the\s+)?music',
                r'pause\s+music',
                r'stop\s+music',
                r'pause\s+playback',
                r'stop\s+playback'
            ],
            
            'resume_music': [
                r'resume\s+(?:the\s+)?music',
                r'unpause\s+(?:the\s+)?music',
                r'continue\s+(?:the\s+)?music',
                r'play\s+(?:the\s+)?music\s+again'
            ],
            
            'next_track': [
                r'next\s+(?:track|song)',
                r'skip\s+(?:to\s+)?next\s+(?:track|song)',
                r'skip\s+track',
                r'next\s+music'
            ],
            
            'previous_track': [
                r'previous\s+(?:track|song)',
                r'last\s+(?:track|song)',
                r'go\s+back\s+(?:one\s+)?(?:track|song)',
                r'previous\s+music'
            ],
            
            # Volume control
            'volume_up': [
                r'turn\s+up\s+(?:the\s+)?volume',
                r'increase\s+(?:the\s+)?volume',
                r'volume\s+up',
                r'louder'
            ],
            
            'volume_down': [
                r'turn\s+down\s+(?:the\s+)?volume',
                r'decrease\s+(?:the\s+)?volume',
                r'lower\s+(?:the\s+)?volume',
                r'volume\s+down',
                r'quieter',
                r'softer'
            ],
            
            'set_volume': [
                r'set\s+volume\s+to\s+(\d+)%?',
                r'volume\s+(\d+)%?',
                r'set\s+volume\s+(\d+)%?'
            ],
            
            # Information requests
            'whats_playing': [
                r'what(?:\'s|\s+is)\s+currently\s+playing',
                r'what(?:\'s|\s+is)\s+playing',
                r'what\s+song\s+(?:is\s+)?this',
                r'current\s+track',
                r'now\s+playing'
            ],
            
            'playlist_info': [
                r'what\s+playlists?\s+do\s+i\s+have',
                r'show\s+me\s+my\s+playlists?',
                r'list\s+my\s+playlists?',
                r'my\s+playlists?'
            ],
            
            'playlist_details': [
                r'how\s+many\s+tracks?\s+in\s+([a-zA-Z0-9\s\-_]+)',
                r'what\s+songs?\s+in\s+([a-zA-Z0-9\s\-_]+)',
                r'tracks?\s+in\s+([a-zA-Z0-9\s\-_]+)',
                r'info\s+about\s+([a-zA-Z0-9\s\-_]+)\s+playlist'
            ],
            
            # Smart context commands
            'context_music': [
                r'play\s+something\s+relaxing',
                r'play\s+something\s+energetic',
                r'play\s+music\s+for\s+studying',
                r'play\s+music\s+for\s+working\s+out',
                r'play\s+background\s+music',
                r'play\s+evening\s+music',
                r'play\s+morning\s+music',
                r'i\s+need\s+(?:some\s+)?background\s+music',
                r'background\s+music\s+please',
                r'play\s+something\s+calm',
                r'play\s+something\s+chill'
            ],
            
            # Help and general music patterns
            'music_help': [
                r'can\s+you\s+play\s+music\?',
                r'do\s+you\s+know\s+how\s+to\s+control\s+spotify\?',
                r'what\s+music\s+services\s+do\s+you\s+support\?',
                r'help\s+me\s+with\s+music',
                r'music\s+please',
                r'how\s+do\s+i\s+control\s+music\?',
                r'what\s+can\s+you\s+do\s+with\s+music\?',
                r'music\s+help'
            ]
        }
        
        # Compile all patterns for efficiency
        self.compiled_patterns = {}
        for category, patterns in self.patterns.items():
            self.compiled_patterns[category] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def matches(self, text: str) -> bool:
        """Check if the text matches any Spotify command pattern"""
        text = text.strip().lower()
        
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    return True
        
        return False
    
    def process(self, text: str) -> str:
        """Process Spotify command and return response"""
        text = text.strip()
        
        try:
            # Check if Spotify is available
            if not self.spotify.is_available():
                return "I'm sorry, but I can't access Spotify right now. Please make sure you're authenticated with Spotify first."
            
            # Determine command type and execute
            if self._matches_pattern(text, 'play_music'):
                return self._handle_play_music()
            
            elif self._matches_pattern(text, 'play_playlist'):
                playlist_name = self._extract_playlist_name(text)
                return self._handle_play_playlist(playlist_name)
            
            elif self._matches_pattern(text, 'pause_music'):
                return self._handle_pause_music()
            
            elif self._matches_pattern(text, 'resume_music'):
                return self._handle_resume_music()
            
            elif self._matches_pattern(text, 'next_track'):
                return self._handle_next_track()
            
            elif self._matches_pattern(text, 'previous_track'):
                return self._handle_previous_track()
            
            elif self._matches_pattern(text, 'volume_up'):
                return self._handle_volume_up()
            
            elif self._matches_pattern(text, 'volume_down'):
                return self._handle_volume_down()
            
            elif self._matches_pattern(text, 'set_volume'):
                volume = self._extract_volume(text)
                return self._handle_set_volume(volume)
            
            elif self._matches_pattern(text, 'whats_playing'):
                return self._handle_whats_playing()
            
            elif self._matches_pattern(text, 'playlist_info'):
                return self._handle_playlist_info()
            
            elif self._matches_pattern(text, 'playlist_details'):
                playlist_name = self._extract_playlist_name(text)
                return self._handle_playlist_details(playlist_name)
            
            elif self._matches_pattern(text, 'context_music'):
                return self._handle_context_music(text)
            
            elif self._matches_pattern(text, 'music_help'):
                return self._handle_music_help()
            
            else:
                return "I'm not sure what you'd like me to do with Spotify. You can ask me to play music, control playback, or get information about your playlists."
        
        except Exception as e:
            self.logger.error(f"Error processing Spotify command: {e}")
            return f"I encountered an error while processing your Spotify request: {str(e)}"
    
    def _matches_pattern(self, text: str, category: str) -> bool:
        """Check if text matches a specific pattern category"""
        if category not in self.compiled_patterns:
            return False
        
        text_lower = text.lower()
        for pattern in self.compiled_patterns[category]:
            if pattern.search(text_lower):
                return True
        return False
    
    def _extract_playlist_name(self, text: str) -> Optional[str]:
        """Extract playlist name from command text"""
        for pattern in self.compiled_patterns['play_playlist']:
            match = pattern.search(text)
            if match and match.groups():
                return match.group(1).strip()
        return None
    
    def _extract_volume(self, text: str) -> Optional[int]:
        """Extract volume percentage from command text"""
        for pattern in self.compiled_patterns['set_volume']:
            match = pattern.search(text)
            if match and match.groups():
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        return None
    
    def _handle_play_music(self) -> str:
        """Handle generic play music command"""
        try:
            # Use the smart method that checks current state
            response = self.spotify.smart_start_music()
            return response
        except Exception as e:
            return f"Error starting music: {str(e)}"
    
    def _handle_play_playlist(self, playlist_name: str) -> str:
        """Handle playing a specific playlist"""
        if not playlist_name:
            return "I didn't catch which playlist you'd like me to play. Could you please specify the playlist name?"
        
        try:
            if self.spotify.start_playlist(playlist_name):
                return f"Perfect! I've started playing your '{playlist_name}' playlist."
            else:
                return f"I'm sorry, but I couldn't find or start the '{playlist_name}' playlist. Please check the name and try again."
        except Exception as e:
            return f"Error playing playlist: {str(e)}"
    
    def _handle_pause_music(self) -> str:
        """Handle pausing music"""
        try:
            if self.spotify.pause():
                return "Music paused. You can ask me to resume when you're ready."
            else:
                return "I couldn't pause the music. It might not be playing right now."
        except Exception as e:
            return f"Error pausing music: {str(e)}"
    
    def _handle_resume_music(self) -> str:
        """Handle resuming music"""
        try:
            if self.spotify.play():
                return "Music resumed! Enjoy your tunes."
            else:
                return "I couldn't resume the music. There might not be anything to resume."
        except Exception as e:
            return f"Error resuming music: {str(e)}"
    
    def _handle_next_track(self) -> str:
        """Handle skipping to next track"""
        try:
            if self.spotify.skip_to_next():
                return "Skipped to the next track!"
            else:
                return "I couldn't skip to the next track. There might not be anything playing."
        except Exception as e:
            return f"Error skipping track: {str(e)}"
    
    def _handle_previous_track(self) -> str:
        """Handle going to previous track"""
        try:
            if self.spotify.skip_to_previous():
                return "Went back to the previous track!"
            else:
                return "I couldn't go back to the previous track. There might not be anything playing."
        except Exception as e:
            return f"Error going to previous track: {str(e)}"
    
    def _handle_volume_up(self) -> str:
        """Handle increasing volume"""
        try:
            # Get current playback to check current volume
            current_playback = self.spotify.get_current_playback()
            if current_playback and 'device' in current_playback:
                current_volume = current_playback['device'].get('volume_percent', 50)
                new_volume = min(100, current_volume + 20)  # Increase by 20%
                
                if self.spotify.set_volume(new_volume):
                    return f"Volume increased to {new_volume}%!"
                else:
                    return "I couldn't change the volume. Please check your Spotify device."
            else:
                return "I can't see what's currently playing to adjust the volume."
        except Exception as e:
            return f"Error adjusting volume: {str(e)}"
    
    def _handle_volume_down(self) -> str:
        """Handle decreasing volume"""
        try:
            current_playback = self.spotify.get_current_playback()
            if current_playback and 'device' in current_playback:
                current_volume = current_playback['device'].get('volume_percent', 50)
                new_volume = max(0, current_volume - 20)  # Decrease by 20%
                
                if self.spotify.set_volume(new_volume):
                    return f"Volume decreased to {new_volume}%!"
                else:
                    return "I couldn't change the volume. Please check your Spotify device."
            else:
                return "I can't see what's currently playing to adjust the volume."
        except Exception as e:
            return f"Error adjusting volume: {str(e)}"
    
    def _handle_set_volume(self, volume: int) -> str:
        """Handle setting specific volume"""
        if not volume or not 0 <= volume <= 100:
            return "Please specify a volume between 0 and 100 percent."
        
        try:
            if self.spotify.set_volume(volume):
                return f"Volume set to {volume}%!"
            else:
                return "I couldn't set the volume. Please check your Spotify device."
        except Exception as e:
            return f"Error setting volume: {str(e)}"
    
    def _handle_whats_playing(self) -> str:
        """Handle what's currently playing request"""
        try:
            track_info = self.spotify.get_current_track_info()
            if track_info and track_info != "No track currently playing":
                return f"Currently playing: {track_info}"
            else:
                return "Nothing is currently playing on Spotify."
        except Exception as e:
            return f"Error getting current track: {str(e)}"
    
    def _handle_playlist_info(self) -> str:
        """Handle playlist information request"""
        try:
            playlists = self.spotify.get_user_playlists()
            if playlists:
                playlist_names = [p['name'] for p in playlists[:10]]  # Show first 10
                return f"You have {len(playlists)} playlists. Here are some: {', '.join(playlist_names)}"
            else:
                return "I couldn't find any playlists in your Spotify account."
        except Exception as e:
            return f"Error getting playlists: {str(e)}"
    
    def _handle_playlist_details(self, playlist_name: str) -> str:
        """Handle specific playlist details request"""
        if not playlist_name:
            return "I didn't catch which playlist you'd like information about."
        
        try:
            playlist_info = self.spotify.get_playlist_info(playlist_name)
            if playlist_info:
                track_count = playlist_info['tracks']['total']
                description = playlist_info.get('description', 'No description')
                return f"'{playlist_name}' playlist has {track_count} tracks. {description}"
            else:
                return f"I couldn't find the '{playlist_name}' playlist."
        except Exception as e:
            return f"Error getting playlist details: {str(e)}"
    
    def _handle_context_music(self, text: str) -> str:
        """Handle context-based music requests"""
        text_lower = text.lower()
        
        if 'relaxing' in text_lower or 'calm' in text_lower:
            return "I'd recommend starting your Nightmode playlist for some relaxing music."
        elif 'energetic' in text_lower or 'workout' in text_lower:
            return "For energetic music, I'd suggest starting your Nightmode playlist - it has some great upbeat tracks!"
        elif 'studying' in text_lower or 'background' in text_lower:
            return "Perfect for studying! I'll start your Nightmode playlist as background music."
        elif 'evening' in text_lower:
            return "Great choice for evening vibes! Starting your Nightmode playlist now."
        else:
            return "I'll start some music that fits your mood. Starting your default playlist!"
    
    def _handle_music_help(self) -> str:
        """Handle music help requests"""
        return """I can help you with music! Here's what I can do:

🎵 **Play Music**: "Play some music", "Start my Nightmode playlist"
⏸️ **Control Playback**: "Pause music", "Next track", "Previous song"
🔊 **Volume Control**: "Turn up volume", "Set volume to 50%"
📱 **Playlist Info**: "What playlists do I have?", "Show me my playlists"
🎯 **Smart Requests**: "Play something relaxing", "Music for studying"

Just ask me naturally - I'll understand what you want!"""
    
    def cleanup(self) -> None:
        """Clean up Spotify skill resources"""
        try:
            if hasattr(self, 'spotify'):
                self.spotify = None
            print("🔇 Spotify skill cleanup complete")
        except Exception as e:
            print(f"⚠️ Error during Spotify skill cleanup: {e}")
