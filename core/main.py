"""
Hey Nova - Main Entry Point

This module orchestrates the complete voice assistant pipeline:
1. Wake word detection ("Hey Nova") using Porcupine
2. Speech-to-Text (STT) with Whisper and VAD for natural conversation
3. Command routing via NovaBrain to skills or LLM
4. Text-to-Speech (TTS) with Azure's British voice

The system supports continuous conversation, barge-in interruption,
streaming responses, and personalized interactions.

Future enhancements:
- Full interrupt handling during TTS output
- Proactive notifications based on context
- Cross-device synchronization
- Enhanced app control and system integration
"""
import signal
import sys
import time
import subprocess
import os
from typing import Optional, Dict, Any

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from wakeword import WakeWordDetector, PushToTalkDetector
from stt import SpeechTranscriber
from tts import SpeechSynthesizer
from brain import NovaBrain
from nova_logger import logger
from core.services.time_based_focus import TimeBasedFocusController
from core.services.spotify_service import SpotifyService

class HeyNova:
    """Main Nova assistant class"""
    
    def __init__(self):
        print("🚀 Initializing Hey Nova...")
        
        # initialize core components
        self.brain = NovaBrain()
        self.tts = SpeechSynthesizer()
        self.stt = SpeechTranscriber()
        
        # setup interrupt handling between STT and TTS
        self.stt.set_interrupt_callback(self._interrupt_speech)
        
        # initialize wake word detection systems
        self.wake_detector = WakeWordDetector(self._on_wake_word)
        self.push_to_talk = PushToTalkDetector(self._on_push_to_talk)
        
        # initialize time-based focus controller
        self.time_based_focus = TimeBasedFocusController()
        
        # initialize spotify services
        self.spotify = SpotifyService()
        
        # Import and initialize direct AppleScript control for Spotify
        from core.services.spotify_applescript import SpotifyAppleScript
        self.spotify_direct = SpotifyAppleScript()
        
        # Set default playlist for welcome greeting
        self.default_playlist = "Nightmode"
        
        # system state variables
        self.is_running = False
        self.current_mode = "wake_word"  # or "push_to_talk"
        
        # Conversation state tracking
        self.conversation_state = {
            "active": False,
            "last_input": None,
            "last_response": None,
            "interruption_count": 0,
            "last_interruption": None,
            "greeting_given": False
        }
        
        # Configure logging verbosity
        self.verbose_logging = False  # Set to True for detailed logs
        
        # setup system signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def start(self):
        """Start Nova assistant"""
        print("\n" + "="*50)
        print("🌟 Hey Nova is now active!")
        print("="*50)
        print("🎧 Audio config (global): sr=16000, dtype=int16, ch=1")
        print("🔔 Wakeword: frame=512 samples (Porcupine)")
        print("🧠 VAD/STT:  frame=480 samples (30 ms @ 16 kHz)")
        print("📝 Verbose logging: " + ("Enabled" if self.verbose_logging else "Disabled"))
        print("💬 Starting in conversation mode - speak directly after greeting")
        
        # validate system configuration
        config.validate_config()
        
        # Initialize wake word detection in background
        try:
            self.wake_detector.start_listening()
            print("✅ Wake word detection initialized (for use after timeout)")
        except Exception as e:
            print(f"⚠️  Wake word detection failed: {e}")
            print("⚠️  Conversation mode will not be able to return to wake word mode")
        
        # Start time-based focus controller
        try:
            self.time_based_focus.start()
            print("✅ Time-based focus controller started")
        except Exception as e:
            print(f"⚠️  Time-based focus controller failed: {e}")
        
        # Set initial mode to conversation
        self.current_mode = "conversation"
        self.is_running = True
        
        # give welcome greeting
        self._welcome_greeting()
        
        # Clean up old audio files to prevent disk space issues
        try:
            if hasattr(self.tts, 'interruption_monitor') and self.tts.interruption_monitor:
                print("🧹 Cleaning up old audio files...")
                deleted_count = self.tts.interruption_monitor.auto_cleanup()
                if deleted_count > 0:
                    print(f"✅ Cleaned up {deleted_count} old audio files")
                else:
                    print("✅ No old audio files to clean up")
        except Exception as e:
            print(f"⚠️ Audio cleanup failed: {e}")
        
        # Start in conversation mode immediately
        print("\n🔊 Nova is ready and listening...")
        print("   (Press Ctrl+C to exit)")
        
        # Process first input directly without wake word
        self._process_user_input(use_streaming=True, first_interaction=True)
        
        # main system loop - after first interaction, system will be in wake word mode
        try:
            print("\n🔊 Nova is now in wake word mode - say 'Hey Nova' to activate")
            print("   (Press Ctrl+C to exit)")
            
            # Track time for periodic cleanup
            last_cleanup_time = time.time()
            cleanup_interval = 3600  # Clean up every hour
            
            while self.is_running:
                current_time = time.time()
                
                # Periodic cleanup every hour
                if current_time - last_cleanup_time > cleanup_interval:
                    try:
                        if hasattr(self.tts, 'interruption_monitor') and self.tts.interruption_monitor:
                            print("🧹 Periodic audio cleanup...")
                            deleted_count = self.tts.interruption_monitor.auto_cleanup()
                            if deleted_count > 0:
                                print(f"✅ Periodic cleanup: {deleted_count} files removed")
                    except Exception as e:
                        print(f"⚠️ Periodic cleanup failed: {e}")
                    last_cleanup_time = current_time
                
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down Nova...")
            self.is_running = False
        finally:
            self.cleanup()
    
    def _on_wake_word(self):
        """Called when wake word is detected"""
        print("\n🔔 Wake word detected!")
        print("💬 Entering conversation mode...")
        self.current_mode = "conversation"
        self._process_user_input()
    
    def _on_push_to_talk(self):
        """Called when push-to-talk is activated"""
        print("\n🎤 Push-to-talk activated!")
        print("💬 Entering conversation mode...")
        self.current_mode = "conversation"
        self._process_user_input()
    
    def _interrupt_speech(self):
        """Called when user starts speaking (interrupts current speech)"""
        if self.tts.is_currently_speaking():
            print("🛑 User interrupted speech - stopping TTS")
            self.tts.stop_speaking()
            
            # Check if we have captured audio from the interruption
            interruption_audio = None
            if hasattr(self.tts, 'interruption_monitor') and self.tts.interruption_monitor:
                interruption_audio = self.tts.interruption_monitor.get_interruption_audio_file()
            
            if interruption_audio and os.path.exists(interruption_audio):
                print(f"🎤 Processing interruption audio: {interruption_audio}")
                
                # Process the interruption audio with our transcriber
                try:
                    # Try up to 2 times to get a valid transcription
                    max_attempts = 2
                    interruption_text = None
                    
                    # First attempt - use faster transcription for responsiveness
                    print("🎧 Fast-transcribing interruption audio...")
                    interruption_text = self.stt.transcribe_file(interruption_audio)
                    
                    # If first attempt failed, try again with more careful transcription
                    if not interruption_text or len(interruption_text.strip()) == 0:
                        print(f"⚠️ Empty transcription on first attempt, retrying with more careful processing...")
                        time.sleep(0.1)  # Very short delay
                        interruption_text = self.stt.transcribe_file(interruption_audio)
                    
                    if interruption_text and len(interruption_text.strip()) > 0:
                        print(f"👤 Interruption: '{interruption_text}'")
                        
                        # Process the interruption text immediately
                        print("🧠 Processing interruption...")
                        self._process_interruption(interruption_text)
                    else:
                        print("⚠️ Empty transcription from interruption audio after multiple attempts")
                        # Give shorter response for better flow
                        self._speak_with_fallback("I heard you, but couldn't understand. Could you repeat that?", allow_interruption=True)
                        # Continue with standard listening
                        print("🎤 Continuing with standard listening...")
                        self.stt.reset_state()
                        self._process_user_input(use_streaming=True)
                except Exception as e:
                    print(f"❌ Error processing interruption: {e}")
                    # Continue with standard listening with minimal response
                    self._speak_with_fallback("Sorry, could you try again?", allow_interruption=True)
                    print("🎤 Continuing with standard listening due to error...")
                    self.stt.reset_state()
                    self._process_user_input(use_streaming=True)
            else:
                print("⚠️ No interruption audio captured, continuing with standard listening")
                # Continue with standard listening
                self.stt.reset_state()
                self._process_user_input(use_streaming=True)
    
    def _welcome_greeting(self):
        """Give personalized welcome greeting"""
        try:
            # get current time for appropriate greeting
            from datetime import datetime
            import pytz
            from core.services.calendar_service import CalendarService
            
            tz = pytz.timezone(config.timezone)
            current_time = datetime.now(tz)
            hour = current_time.hour
            
            # Check if we're in the afternoon/evening (after 12 PM)
            is_afternoon_or_evening = hour >= 12
            
            # PREPARE EVERYTHING BEFORE SPEAKING
            print("🚀 Preparing your welcome experience...")
            
            # 1. Set private mode first (always, regardless of time)
            try:
                self.time_based_focus.focus_controller.set_do_not_disturb(True)
                print("🔒 Private mode activated")
            except Exception:
                print("⚠️ Could not set private mode")
            
            # 2. Prepare Spotify music (always, regardless of time)
            music_status = "ready"
            try:
                playlist_name = self.default_playlist
                print(f"🎵 Preparing {playlist_name} playlist...")
                
                # Use direct AppleScript approach for reliable playback
                spotify_success = self.spotify_direct.ensure_ready_and_play_nightmode()
                
                if spotify_success:
                    # Verify playback is actually working
                    player_state = self.spotify_direct.get_player_state()
                    if player_state == "playing":
                        track_info = self.spotify_direct.get_current_track_info()
                        if track_info:
                            print(f"🎵 Now playing: {track_info['track']} by {track_info['artist']}")
                        music_status = "playing"
                    else:
                        print(f"⚠️ Player state after play attempt: {player_state}")
                        music_status = "not_ready"
                else:
                    print("❌ Failed to play Nightmode playlist")
                    music_status = "error"
                    
            except Exception as e:
                print(f"Spotify integration error: {e}")
                music_status = "error"
            
            # 3. Get calendar information
            calendar_info = ""
            try:
                calendar_service = CalendarService()
                calendar_info = calendar_service.format_rest_of_day_schedule()
                print("📅 Calendar information retrieved")
            except Exception as e:
                print(f"Error getting calendar info: {e}")
            
            # NOW BUILD THE GREETING MESSAGE IN THE CORRECT ORDER
            if 5 <= hour < 12:
                greeting = "Good morning"
            elif 12 <= hour < 17:
                greeting = "Good afternoon"
            else:
                greeting = "Good evening"
            
            # 1. Welcome home (greet)
            welcome_message = f"{greeting}, {config.user_title}! Welcome home."
            
            # 2. Set home to private mode
            welcome_message += " I've set your home to private mode."
            
            # 3. Played music
            if music_status == "playing":
                welcome_message += f" I've started playing your {self.default_playlist} playlist on Spotify."
            elif music_status == "ready":
                welcome_message += " I'm ready to help you with music when you want."
            elif music_status == "error":
                welcome_message += " I'm ready to help you with music when you ask."
            elif music_status == "no_device":
                welcome_message += " I'm ready to help you with music when you ask."
            elif music_status == "no_playlist":
                welcome_message += " I couldn't find your default playlist, but I'm ready to play music when you ask."
            elif music_status == "not_ready":
                welcome_message += " I'm ready to help you with music when you want."
            
            # 4. Schedule for remainder of day
            welcome_message += f" {calendar_info}"
            
            # 5. Finally: hope you have a productive xxx
            welcome_message += f" Hope you have a productive {greeting.lower().replace('good ', '')}."
            
            print(f"🎭 {welcome_message}")
            self.tts.speak(welcome_message)
            
            # Update conversation state
            self.conversation_state["greeting_given"] = True
            self.conversation_state["active"] = True
            
        except Exception as e:
            print(f"Error in welcome greeting: {e}")
            # fallback greeting
            fallback = f"Hello, {config.user_title}! Welcome home. How may I serve you today?"
            print(f"🎭 {fallback}")
            self.tts.speak(fallback)
            
            # Update conversation state
            self.conversation_state["greeting_given"] = True
            self.conversation_state["active"] = True
    
    def _ensure_spotify_ready(self):
        """Ensure Spotify is running and ready to play music
        
        Returns:
            bool: True if Spotify is ready, False otherwise
        """
        try:
            import subprocess
            import time
            
            # Check if Spotify is already running and ready
            if self.spotify.is_available():
                try:
                    # Quick test to see if Spotify responds
                    devices = self.spotify.get_available_devices()
                    if devices:
                        print("🎵 Spotify is already running and ready")
                        return True
                except Exception:
                    pass
            
            # Spotify is not ready, try to launch it
            print("🎵 Launching Spotify...")
            try:
                # Launch Spotify using macOS open command
                subprocess.run(['open', '-a', 'Spotify'], check=True, capture_output=True)
                print("🎵 Spotify launch command sent")
                
                # Wait for Spotify to be ready with timeout
                timeout_seconds = 15  # Reasonable timeout
                wait_interval = 1  # Check every second
                
                print(f"⏳ Waiting up to {timeout_seconds} seconds for Spotify to be ready...")
                
                for attempt in range(timeout_seconds):
                    time.sleep(wait_interval)
                    
                    try:
                        # Test if Spotify is responding
                        devices = self.spotify.get_available_devices()
                        if devices:
                            print(f"✅ Spotify is ready after {attempt + 1} seconds")
                            return True
                    except Exception as e:
                        print(f"⏳ Spotify not ready yet (attempt {attempt + 1}/{timeout_seconds}): {e}")
                        continue
                
                print(f"⏰ Spotify took too long to start (>{timeout_seconds}s), skipping music")
                return False
                
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to launch Spotify: {e}")
                return False
            except Exception as e:
                print(f"❌ Error launching Spotify: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Error in _ensure_spotify_ready: {e}")
            return False
    
    def _get_spotify_status(self):
        """Check Spotify's current status
        
        Returns:
            str: "ready", "open_not_ready", "not_open", or "error"
        """
        try:
            # First check if Spotify service is available
            if not self.spotify.is_available():
                return "not_open"
            
            # Try to get devices to see if Spotify is responding
            try:
                devices = self.spotify.get_available_devices()
                if devices and len(devices) > 0:
                    # Check if any device is active
                    active_devices = [d for d in devices if d.get('is_active', False)]
                    if active_devices:
                        return "ready"
                    else:
                        return "open_not_ready"
                else:
                    return "open_not_ready"
            except Exception:
                return "open_not_ready"
                
        except Exception as e:
            print(f"❌ Error checking Spotify status: {e}")
            return "error"
    
    def _start_playlist_smart(self, playlist_name):
        """Smart playlist starting with proper error handling
        
        Args:
            playlist_name (str): Name of playlist to start
            
        Returns:
            bool: True if playlist started successfully, False otherwise
        """
        try:
            print(f"🔍 Looking for playlist: '{playlist_name}'")
            playlist = self.spotify.find_playlist_by_name(playlist_name)
            
            if not playlist:
                print(f"❌ Playlist '{playlist_name}' not found")
                return False
            
            print(f"✅ Found playlist: {playlist.get('name', 'Unknown')} (ID: {playlist.get('id', 'Unknown')})")
            
            # Try to start the playlist
            print(f"🎵 Starting playlist: {playlist_name}")
            self.spotify.start_playlist(playlist_name)
            print(f"🎵 Successfully started {playlist_name} playlist")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start playlist: {e}")
            return False
            
    def _play_spotify_with_state_machine(self, playlist_name, max_timeout=40):
        """
        Robust state machine for playing Spotify with proper state transitions.
        
        States:
        1. AUTH_READY - Check if Spotify auth is valid
        2. APP_READY - Check if Spotify app is running and responsive
        3. DEVICE_READY - Ensure we have an active device
        4. PLAYBACK_READY - Prepare playback settings
        5. PLAYING - Successfully playing music
        
        Args:
            playlist_name (str): Name of the playlist to play
            max_timeout (int): Maximum total seconds to spend on the entire process
            
        Returns:
            str: Status message ("playing", "error", etc.)
        """
        import time
        import subprocess
        
        start_time = time.time()
        
        # STATE 1: AUTH_READY - Verify Spotify auth
        print("🔑 Checking Spotify authentication...")
        if not self.spotify.is_available():
            print("❌ Spotify authentication not available")
            return "auth_error"
            
        # STATE 2: APP_READY - Check if app is running
        print("🔍 Checking if Spotify app is running...")
        
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
                        devices = self.spotify.get_available_devices()
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
                            devices = self.spotify.get_available_devices()
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
        print("🎮 Checking for available Spotify devices...")
        try:
            devices = self.spotify.get_available_devices()
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
                        self.spotify._make_request('PUT', 'https://api.spotify.com/v1/me/player', 
                                                  data={'device_ids': [device_id], 'play': False})
                        print(f"✅ Device activated on attempt {attempt + 1}")
                        activated = True
                        break
                    except Exception as e:
                        print(f"⚠️ Activation attempt {attempt + 1} failed: {e}")
                        time.sleep(backoff)
                
                if not activated:
                    print("⚠️ Failed to activate device via API, trying AppleScript fallback...")
                    try:
                        # Fallback: Try to activate Spotify via AppleScript
                        import subprocess
                        subprocess.run(["osascript", "-e", 'tell application "Spotify" to activate'], check=True)
                        print("✅ Spotify activated via AppleScript")
                        
                        # Wait a moment for Spotify to become active
                        time.sleep(2)
                        
                        # Try a direct AppleScript command to play
                        try:
                            subprocess.run(["osascript", "-e", 'tell application "Spotify" to play'], check=True)
                            print("✅ Spotify play command sent via AppleScript")
                            activated = True
                        except Exception as e:
                            print(f"⚠️ AppleScript play failed: {e}")
                    except Exception as e:
                        print(f"❌ AppleScript activation failed: {e}")
                        # Continue anyway
            
            # Prime the device with a play/pause action to ensure it's fully ready
            print("🔌 Priming device for playback...")
            primed = self._prime_spotify_device()
            if primed:
                print("✅ Device successfully primed")
            else:
                print("⚠️ Device priming failed, but continuing anyway")
            
            # STATE 4: PLAYBACK_READY - Prepare playback settings
            print(f"🎵 Preparing to play playlist: {playlist_name}")
            
            # Find the playlist
            playlist = self.spotify.find_playlist_by_name(playlist_name)
            if not playlist:
                print(f"❌ Playlist '{playlist_name}' not found")
                return "playlist_not_found"
            
            print(f"✅ Found playlist: {playlist.get('name')} (ID: {playlist.get('id')})")
            
            # Configure player settings (optional)
            try:
                # Set shuffle off
                self.spotify._make_request('PUT', 'https://api.spotify.com/v1/me/player/shuffle?state=false')
                print("✅ Shuffle turned off")
            except Exception as e:
                print(f"⚠️ Could not set shuffle: {e}")
            
            # STATE 5: PLAYING - Start playback
            print("▶️ Starting playlist...")
            
            # Try up to 2 times to start playback
            for attempt in range(2):
                if time.time() - start_time > max_timeout:
                    print(f"⏰ Overall timeout reached ({max_timeout}s)")
                    return "timeout"
                    
                try:
                    # Start the playlist via API
                    try:
                        self.spotify.start_playlist(playlist_name)
                        print("✅ Start playlist API call successful")
                    except Exception as e:
                        print(f"⚠️ API playlist start failed: {e}")
                        
                        # Try AppleScript fallback if API fails
                        if attempt == 1:  # Only try AppleScript on second attempt
                            print("🔄 Trying AppleScript fallback to start playlist...")
                            try:
                                # First activate Spotify
                                import subprocess
                                subprocess.run(["osascript", "-e", 'tell application "Spotify" to activate'], check=True)
                                
                                # Get the playlist URI if available
                                playlist_uri = None
                                if playlist and playlist.get('uri'):
                                    playlist_uri = playlist.get('uri')
                                    print(f"✅ Found playlist URI: {playlist_uri}")
                                
                                # Try to play the playlist directly if we have the URI
                                if playlist_uri:
                                    try:
                                        play_uri_cmd = f'tell application "Spotify" to play track "{playlist_uri}"'
                                        subprocess.run(["osascript", "-e", play_uri_cmd], check=True)
                                        print("✅ AppleScript play URI command sent")
                                    except Exception as e:
                                        print(f"⚠️ AppleScript URI play failed: {e}")
                                        # Try generic play as fallback
                                        play_cmd = 'tell application "Spotify" to play'
                                        subprocess.run(["osascript", "-e", play_cmd], check=True)
                                        print("✅ AppleScript generic play command sent")
                                else:
                                    # Just try to play whatever is loaded
                                    play_cmd = 'tell application "Spotify" to play'
                                    subprocess.run(["osascript", "-e", play_cmd], check=True)
                                    print("✅ AppleScript generic play command sent")
                            except Exception as e:
                                print(f"❌ AppleScript fallback failed: {e}")
                                # Continue to verification anyway
                    
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
                            # Check current playback via API
                            try:
                                player_state = self.spotify._make_request('GET', 'https://api.spotify.com/v1/me/player')
                                
                                # Check if playing
                                if player_state and player_state.get('is_playing'):
                                    print(f"✅ Playback verified after {verify_attempt + 1}s")
                                    playback_verified = True
                                    break
                            except Exception:
                                # Try AppleScript verification as fallback
                                try:
                                    import subprocess
                                    result = subprocess.run(
                                        ["osascript", "-e", 'tell application "Spotify" to player state as string'],
                                        capture_output=True, text=True, check=True
                                    )
                                    if "playing" in result.stdout.lower():
                                        print(f"✅ Playback verified via AppleScript after {verify_attempt + 1}s")
                                        playback_verified = True
                                        break
                                except Exception:
                                    pass
                        except Exception as e:
                            print(f"⏳ Waiting for playback confirmation... ({verify_attempt + 1}s)")
                    
                    if playback_verified:
                        print(f"🎵 Successfully playing {playlist_name} playlist")
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
    
    def _prime_spotify_device(self):
        """Prime the Spotify device by playing and pausing a track
        
        This helps ensure the device is fully activated and ready for playback.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Try API approach first
            try:
                print("🎯 Priming device via API...")
                
                # 1. Play something (doesn't matter what)
                self.spotify._make_request('PUT', 'https://api.spotify.com/v1/me/player/play')
                print("✅ Play command sent")
                time.sleep(1)
                
                # 2. Then pause it
                self.spotify._make_request('PUT', 'https://api.spotify.com/v1/me/player/pause')
                print("✅ Pause command sent")
                
                return True
            except Exception as e:
                print(f"⚠️ API priming failed: {e}")
                
                # Try AppleScript fallback
                print("🎯 Trying AppleScript fallback...")
                try:
                    import subprocess
                    
                    # 1. Activate Spotify
                    subprocess.run(["osascript", "-e", 'tell application "Spotify" to activate'], check=True)
                    
                    # 2. Play
                    subprocess.run(["osascript", "-e", 'tell application "Spotify" to play'], check=True)
                    print("✅ Play command sent via AppleScript")
                    time.sleep(1)
                    
                    # 3. Pause
                    subprocess.run(["osascript", "-e", 'tell application "Spotify" to pause'], check=True)
                    print("✅ Pause command sent via AppleScript")
                    
                    return True
                except Exception as e:
                    print(f"❌ AppleScript priming failed: {e}")
                    return False
        except Exception as e:
            print(f"❌ Device priming error: {e}")
            return False
    
    def _wait_for_spotify_ready(self, timeout_seconds=10):
        """Wait for Spotify to become ready
        
        Args:
            timeout_seconds (int): Maximum time to wait
            
        Returns:
            bool: True if Spotify becomes ready, False if timeout
        """
        print(f"⏳ Waiting up to {timeout_seconds} seconds for Spotify to be ready...")
        
        for attempt in range(timeout_seconds):
            time.sleep(1)
            
            try:
                devices = self.spotify.get_available_devices()
                if devices and any(d.get('is_active', False) for d in devices):
                    print(f"✅ Spotify is ready after {attempt + 1} seconds")
                    return True
            except Exception as e:
                print(f"⏳ Spotify not ready yet (attempt {attempt + 1}/{timeout_seconds}): {e}")
                continue
        
        print(f"⏰ Spotify took too long to be ready (>{timeout_seconds}s)")
        return False
    
    def _launch_and_wait_for_spotify(self, timeout_seconds=15):
        """Launch Spotify and wait for it to be ready
        
        Args:
            timeout_seconds (int): Maximum time to wait after launch
            
        Returns:
            bool: True if Spotify launches and becomes ready, False otherwise
        """
        try:
            import subprocess
            
            print("🎵 Launching Spotify...")
            subprocess.run(['open', '-a', 'Spotify'], check=True, capture_output=True)
            print("🎵 Spotify launch command sent")
            
            # Wait for Spotify to be ready
            return self._wait_for_spotify_ready(timeout_seconds)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to launch Spotify: {e}")
            return False
        except Exception as e:
            print(f"❌ Error launching Spotify: {e}")
            return False
    
    def _show_voice_health_hud(self):
        """Display Voice Health HUD with current metrics"""
        try:
            # get current audio stats if available
            audio_stats = {}
            if hasattr(self.stt, 'ring_buffer'):
                audio_stats = self.stt.ring_buffer.get_stats()
            
            # get VAD stats if available
            vad_stats = {}
            if hasattr(self.stt, 'vad') and self.stt.vad:
                vad_stats = {
                    "vad_enabled": True,
                    "frame_duration_ms": config.vad_frame_duration,
                    "on_threshold": config.vad_on_threshold,
                    "off_threshold": config.vad_off_threshold
                }
            
            # display HUD
            print("\n" + "="*60)
            print("🎤 VOICE HEALTH HUD")
            print("="*60)
            
            if audio_stats:
                print(f"📊 Audio Buffer: {audio_stats.get('current_frames', 0)}/{audio_stats.get('max_frames', 0)} frames")
                print(f"   Utilization: {audio_stats.get('utilization', 0):.1%}")
                print(f"   Overflows: {audio_stats.get('overflow_count', 0)} | Underflows: {audio_stats.get('underflow_count', 0)}")
            
            if vad_stats:
                print(f"🎯 VAD Settings: Frame={vad_stats['frame_duration_ms']}ms, On={vad_stats['on_threshold']}, Off={vad_stats['off_threshold']}")
            
            print(f"🔊 TTS Status: {'Speaking' if self.tts.is_currently_speaking() else 'Idle'}")
            print(f"🎧 Wake Word: {'Listening' if self.current_mode == 'wake_word' else 'Push-to-Talk'}")
            print("="*60)
            
        except Exception as e:
            logger.log("hud_error", {"error": str(e)}, "ERROR")
    
    def _process_user_input(self, use_streaming: bool = True, first_interaction: bool = False):
        """Process user input through the full pipeline
        
        Args:
            use_streaming: Whether to use streaming responses
            first_interaction: Whether this is the first interaction after startup
        """
        try:
            # get speech input from user with fallback mechanisms
            if first_interaction:
                print("🎤 I'm listening... (speak now)")
            else:
                print("🎤 Listening for your request...")
            
            # Try VAD-based recording first
            user_input = None
            try:
                user_input = self.stt.record_audio_with_vad()
            except Exception as stt_error:
                logger.log("stt_error", {"error": str(stt_error), "method": "vad"}, "ERROR")
                print(f"⚠️  VAD recording failed: {stt_error}")
                print("🔄 Falling back to fixed duration recording...")
                
                # Fallback to fixed duration recording
                try:
                    user_input = self.stt.record_audio_fixed()
                except Exception as fixed_error:
                    logger.log("stt_error", {"error": str(fixed_error), "method": "fixed"}, "ERROR")
                    print(f"⚠️  Fixed recording failed: {fixed_error}")
            
            if not user_input:
                print("⚠️  No speech detected")
                self.tts.speak("I didn't catch that. Could you please repeat?")
                return
            
            print(f"👤 You said: '{user_input}'")
            
            # process request with brain
            print("🧠 Processing your request...")
            
            # Try streaming response with fallback to non-streaming
            try:
                if use_streaming:
                    # Get streaming response
                    print("🤖 Nova: ", end="", flush=True)
                    
                    # Collect the full response for TTS
                    full_response = ""
                    
                    # Process streaming response
                    for chunk in self.brain.process_input(user_input, stream=True):
                        print(chunk, end="", flush=True)
                        full_response += chunk
                    
                    # Add newline after streaming completes
                    print()
                    
                    # Speak the full response with interruption capability
                    if not self._speak_with_fallback(full_response, allow_interruption=True):
                        print("⚠️  TTS failed")
                else:
                    # Get full response at once
                    response = self.brain.process_input(user_input)
                    
                    if response:
                        print(f"🤖 Nova: {response}")
                        
                        # Speak response to user with interruption capability
                        # Always allow interruption for all responses including calendar
                        if not self._speak_with_fallback(response, allow_interruption=True):
                            print("⚠️  TTS failed")
                    else:
                        print("⚠️  No response generated")
                        self._speak_with_fallback("I'm sorry, I couldn't process that request.")
                        return
            except Exception as brain_error:
                logger.log("brain_error", {"error": str(brain_error)}, "ERROR")
                print(f"⚠️  Brain processing failed: {brain_error}")
                self._speak_with_fallback("I'm having trouble processing that. Let me try again.")
                
                # Fallback to simple response
                try:
                    # Try a simple non-streaming response as fallback
                    response = "I'm sorry, I'm having trouble with my advanced processing. I'll try to help with basic responses."
                    print(f"🤖 Nova (fallback): {response}")
                    self._speak_with_fallback(response)
                except:
                    pass
            
            # reset STT state before entering conversation mode
            try:
                self.stt.reset_state()
            except Exception as reset_error:
                logger.log("reset_error", {"error": str(reset_error)}, "ERROR")
                print(f"⚠️  STT reset failed: {reset_error}")
            
            # enter conversation mode for follow-up responses
            self._enter_conversation_mode(use_streaming)
                
        except Exception as e:
            logger.log("process_error", {"error": str(e)}, "ERROR")
            print(f"Error processing user input: {e}")
            self._speak_with_fallback("I encountered an error. Please try again.")
            
    def _speak_with_fallback(self, text: str, allow_interruption: bool = False) -> bool:
        """Speak text with fallback mechanisms and optional interruption
        
        Args:
            text: Text to speak
            allow_interruption: Whether to allow user interruptions
            
        Returns:
            bool: True if speech was successful, False otherwise
        """
        if not text:
            return False
        
        # Use interruption-capable speaking if requested
        if allow_interruption:
            try:
                return self.tts.speak_with_interruption(text, self.stt)
            except Exception as interrupt_error:
                logger.log("tts_error", {"error": str(interrupt_error), "method": "interruption"}, "ERROR")
                print(f"⚠️  Interruption-capable TTS failed: {interrupt_error}")
                # Fall back to regular speaking
        
        # Try Azure TTS first
        try:
            return self.tts.speak(text)
        except Exception as azure_error:
            logger.log("tts_error", {"error": str(azure_error), "method": "azure"}, "ERROR")
            print(f"⚠️  Azure TTS failed: {azure_error}")
            
            # Try macOS TTS as fallback
            try:
                print("🔄 Falling back to macOS TTS...")
                result = subprocess.run(
                    ["say", text],
                    check=False,
                    timeout=10
                )
                return result.returncode == 0
            except Exception as macos_error:
                logger.log("tts_error", {"error": str(macos_error), "method": "macos"}, "ERROR")
                print(f"⚠️  macOS TTS failed: {macos_error}")
                
                # Final fallback - just print the text
                print(f"🔤 Text fallback: {text}")
                return False
    
    def _enter_conversation_mode(self, use_streaming: bool = True):
        """Enter conversation mode for continuous dialogue with VAD
        
        Args:
            use_streaming: Whether to use streaming responses
        """
        import threading
        import time
        from core.config import config
        
        print("\n💬 Conversation mode: I'm listening for your response...")
        print(f"   (Speak naturally - I'll respond when you pause, say 'goodbye' to exit, or wait {config.conversation_timeout}s for wake word mode)")
        
        # Set up inactivity timer
        last_activity_time = time.time()
        conversation_active = True
        
        # Function to monitor inactivity
        def check_inactivity():
            nonlocal conversation_active, last_activity_time
            while conversation_active:
                current_time = time.time()
                elapsed = current_time - last_activity_time
                
                # Check if currently speaking
                if self.tts.is_currently_speaking():
                    # Reset timer while speaking
                    last_activity_time = current_time
                    continue
                    
                # Only timeout when not speaking and after timeout period
                if elapsed > config.conversation_timeout:
                    conversation_active = False
                    print(f"\n⏰ Conversation timeout after {config.conversation_timeout} seconds of inactivity")
                    self._return_to_wake_word_mode()
                    return
                
                # Check every second
                time.sleep(1)
        
        # Start inactivity monitor in background thread
        inactivity_thread = threading.Thread(target=check_inactivity, daemon=True)
        inactivity_thread.start()
        
        # continue listening for user responses
        while conversation_active:
            try:
                # listen for follow-up response with fallbacks
                print("🎤 Listening... (speak naturally)")
                
                # Try VAD-based recording first
                user_input = None
                try:
                    # Reset inactivity timer when starting to listen
                    last_activity_time = time.time()
                    
                    user_input = self.stt.record_audio_with_vad()
                    
                    # Reset inactivity timer when speech is detected
                    last_activity_time = time.time()
                except Exception as stt_error:
                    logger.log("stt_error", {"error": str(stt_error), "method": "vad", "mode": "conversation"}, "ERROR")
                    print(f"⚠️  VAD recording failed: {stt_error}")
                    print("🔄 Falling back to fixed duration recording...")
                    
                    # Fallback to fixed duration recording
                    try:
                        user_input = self.stt.record_audio_fixed()
                        
                        # Reset inactivity timer when speech is detected
                        if user_input:
                            last_activity_time = time.time()
                    except Exception as fixed_error:
                        logger.log("stt_error", {"error": str(fixed_error), "method": "fixed", "mode": "conversation"}, "ERROR")
                        print(f"⚠️  Fixed recording failed: {fixed_error}")
                
                # Check if conversation is still active (might have timed out during recording)
                if not conversation_active:
                    return
                
                if not user_input:
                    print("⚠️  No speech detected, continuing to listen...")
                    continue
                
                # check for exit commands and shutdown commands
                exit_commands = ['goodbye', 'exit', 'stop', 'end', 'good night', 'goodnight', 'bye', 'see you']
                shutdown_commands = ['shut down', 'shutdown', 'power off', 'turn off', 'terminate']
                
                if any(word in user_input.lower() for word in exit_commands):
                    print("👋 Ending conversation, returning to wake word mode...")
                    conversation_active = False
                    self._return_to_wake_word_mode("Goodbye! I'll be here when you need me.")
                    return  # exit conversation mode completely
                
                # Check for shutdown commands
                elif any(cmd in user_input.lower() for cmd in shutdown_commands):
                    print("🛑 Shutdown command detected...")
                    self._speak_with_fallback("Shutting down now. Goodbye!")
                    self.is_running = False
                    conversation_active = False
                    return  # exit conversation mode completely
                
                print(f"👤 You said: '{user_input}'")
                
                # process response with brain and fallbacks
                print("🧠 Processing your response...")
                
                try:
                    if use_streaming:
                        # Get streaming response
                        print("🤖 Nova: ", end="", flush=True)
                        
                        # Collect the full response for TTS
                        full_response = ""
                        
                        # Process streaming response
                        for chunk in self.brain.process_input(user_input, stream=True):
                            print(chunk, end="", flush=True)
                            full_response += chunk
                        
                        # Add newline after streaming completes
                        print()
                        
                        # The interruption capability is now handled in the speaker class
                        
                        # Speak the full response with fallback and interruption capability
                        # Always enable interruption for all responses
                        if not self._speak_with_fallback(full_response, allow_interruption=True):
                            if self.tts.was_interrupted:
                                print("👂 Speech was interrupted, listening for new command...")
                                # Reset activity timer after interruption
                                last_activity_time = time.time()
                                # Skip the rest of this loop iteration to immediately listen
                                continue
                            else:
                                print("⚠️  TTS failed")
                        else:
                            # Reset activity timer after speaking
                            last_activity_time = time.time()
                    else:
                        # Get full response at once
                        response = self.brain.process_input(user_input)
                        
                        if response:
                            print(f"🤖 Nova: {response}")
                            
                            # The interruption capability is now handled in the speaker class
                            
                            if not self._speak_with_fallback(response, allow_interruption=True):
                                if self.tts.was_interrupted:
                                    print("👂 Speech was interrupted, listening for new command...")
                                    # Reset activity timer after interruption
                                    last_activity_time = time.time()
                                    # Skip the rest of this loop iteration to immediately listen
                                    continue
                                else:
                                    print("⚠️  TTS failed")
                            else:
                                # Reset activity timer after speaking
                                last_activity_time = time.time()
                        else:
                            print("⚠️  No response generated")
                            self._speak_with_fallback("I'm sorry, I couldn't process that.")
                            # Reset activity timer after speaking
                            last_activity_time = time.time()
                            continue
                except Exception as brain_error:
                    logger.log("brain_error", {"error": str(brain_error), "mode": "conversation"}, "ERROR")
                    print(f"⚠️  Brain processing failed: {brain_error}")
                    self._speak_with_fallback("I'm having trouble processing that. Let's continue our conversation.")
                    # Reset activity timer after speaking
                    last_activity_time = time.time()
                    
                    # Fallback to simple response
                    try:
                        # Try a simple non-streaming response as fallback
                        response = "I'm sorry, I'm having trouble with my advanced processing. Could you try asking me something else?"
                        print(f"🤖 Nova (fallback): {response}")
                        self._speak_with_fallback(response)
                        # Reset activity timer after speaking
                        last_activity_time = time.time()
                    except:
                        pass
                
                # reset state for next response with fallback
                try:
                    self.stt.reset_state()
                except Exception as reset_error:
                    logger.log("reset_error", {"error": str(reset_error), "mode": "conversation"}, "ERROR")
                    print(f"⚠️  STT reset failed: {reset_error}")
                    
            except KeyboardInterrupt:
                print("\n🛑 Keyboard interrupt detected...")
                conversation_active = False
                return  # Exit conversation mode
            except Exception as e:
                logger.log("conversation_error", {"error": str(e)}, "ERROR")
                print(f"Error in conversation mode: {e}")
                self._speak_with_fallback("I encountered an error. Let's continue our conversation.")
                # Reset activity timer after speaking
                last_activity_time = time.time()
    
    def _process_interruption(self, interruption_text: str):
        """Process an interruption from the user
        
        Args:
            interruption_text: The transcribed text from the interruption
        """
        # Update interruption tracking
        self.conversation_state["interruption_count"] += 1
        self.conversation_state["last_interruption"] = interruption_text
        
        # Normalize the text for better command detection
        normalized_text = interruption_text.lower().strip()
        
        # Check for exit commands and shutdown commands
        exit_commands = ['goodbye', 'exit', 'stop', 'end', 'good night', 'goodnight', 'bye', 'see you']
        shutdown_commands = ['shut down', 'shutdown', 'power off', 'turn off', 'terminate']
        
        # Handle exit commands
        if any(word in normalized_text for word in exit_commands):
            print("👋 Ending conversation via interruption, returning to wake word mode...")
            self._return_to_wake_word_mode("Goodbye! I'll be here when you need me.")
            return
        
        # Handle shutdown commands
        elif any(cmd in normalized_text for cmd in shutdown_commands):
            print("🛑 Shutdown command detected via interruption...")
            self._speak_with_fallback("Shutting down now. Goodbye!")
            self.is_running = False
            return
        
        # Check for very short or likely misheard interruptions
        if len(normalized_text.split()) <= 2:
            # Check if it's a common short command
            common_short_commands = ['yes', 'no', 'stop', 'wait', 'hey', 'hi', 'ok']
            question_starters = ['what', 'who', 'when', 'where', 'why', 'how', 'can', 'could', 'will', 'would', 'should', 'is', 'are']
            
            if any(cmd == normalized_text for cmd in common_short_commands):
                # Process common short commands directly
                print(f"✅ Recognized short command: '{normalized_text}'")
                # Continue processing
            elif any(normalized_text.startswith(cmd) for cmd in question_starters):
                # Continue processing if it starts with a question word
                print(f"✅ Recognized question starter: '{normalized_text}'")
                # Continue processing
            else:
                # For very short interruptions that aren't commands or questions, ask for clarification
                print("⚠️ Very short interruption detected, asking for clarification...")
                self._speak_with_fallback("I heard you interrupt. What would you like to know?", allow_interruption=True)
                # Continue with standard listening
                self.stt.reset_state()
                self._process_user_input(use_streaming=True)
                return
        
        # Process the interruption as a normal request
        try:
            # Get streaming response
            print("🤖 Nova: ", end="", flush=True)
            
            # Collect the full response for TTS
            full_response = ""
            
            # Process streaming response
            for chunk in self.brain.process_input(interruption_text, stream=True):
                print(chunk, end="", flush=True)
                full_response += chunk
            
            # Add newline after streaming completes
            print()
            
            # Speak the full response with interruption capability
            if not self._speak_with_fallback(full_response, allow_interruption=True):
                if self.tts.was_interrupted:
                    # If this response was interrupted too, let the interrupt handler take over
                    print("👂 Response was interrupted again, handling new interruption...")
                    return
                else:
                    print("⚠️ TTS failed for interruption response")
            
            # After speaking, continue conversation mode
            self._enter_conversation_mode(use_streaming=True)
            
        except Exception as e:
            print(f"❌ Error processing interruption: {e}")
            self._speak_with_fallback("I'm sorry, I couldn't process that properly. What else can I help with?", allow_interruption=True)
            # Continue conversation mode
            self._enter_conversation_mode(use_streaming=True)
    
    def _return_to_wake_word_mode(self, message: str = "I'll be listening for 'Hey Nova' when you need me again."):
        """Return to wake word detection mode with a message
        
        Args:
            message: The message to speak before returning to wake word mode
        """
        # Speak the transition message
        self._speak_with_fallback(message)
        
        # Set mode to wake word
        self.current_mode = "wake_word"
        
        # Reset conversation state
        self.conversation_state.update({
            "active": False,
            "last_input": None,
            "last_response": None,
            "interruption_count": 0,
            "last_interruption": None
        })
        
        # Make sure wake word detection is active
        try:
            if hasattr(self.wake_detector, 'is_listening') and not self.wake_detector.is_listening:
                self.wake_detector.start_listening()
            print("🔔 Wake word detection active - say 'Hey Nova' when you need me")
        except Exception as e:
            print(f"⚠️  Error activating wake word detection: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.is_running = False
        
        try:
            # Perform cleanup
            self.cleanup()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            print("🔄 Signal handler cleanup complete")
    
    def cleanup(self):
        """Clean up resources"""
        print("🧹 Cleaning up...")
        
        # Force stop any active processes
        self.is_running = False
        
        # Stop time-based focus controller first (it has a thread)
        try:
            self.time_based_focus.stop()
            print("🌙 Time-based focus controller stopped")
        except Exception as e:
            print(f"⚠️  Error stopping time-based focus controller: {e}")
        
        # Stop any active speech
        try:
            self.tts.stop_speaking()
            print("🔇 Speech stopped")
        except Exception as e:
            print(f"⚠️  Error stopping speech: {e}")
            
        # Say goodbye before shutting down (only if not already speaking)
        try:
            if not self.tts.is_currently_speaking():
                self.tts.speak("Goodbye! It was a pleasure serving you.")
                # Give it a moment to finish speaking
                time.sleep(1)
        except Exception as e:
            print(f"⚠️  Error saying goodbye: {e}")
        
        # Clean up wake word detector
        try:
            self.wake_detector.cleanup()
            print("🔇 Wake word detection stopped")
        except Exception as e:
            print(f"⚠️  Error stopping wake word detection: {e}")
            
        # Clean up push-to-talk if active
        try:
            self.push_to_talk.stop_listening()
            print("🔇 Push-to-talk stopped")
        except Exception as e:
            print(f"⚠️  Error stopping push-to-talk: {e}")
        
        # Clean up STT
        try:
            self.stt.cleanup()
            print("🔇 Speech recognition stopped")
        except Exception as e:
            print(f"⚠️  Error stopping speech recognition: {e}")
        
        # Final stop of TTS
        try:
            self.tts.stop_speaking()
        except Exception as e:
            print(f"⚠️  Final TTS stop error: {e}")
        
        print("✅ Cleanup complete. Goodbye!")
        
        # Final cleanup of any remaining resources
        try:
            # Force garbage collection to clean up any remaining objects
            import gc
            gc.collect()
            
            # Clear any remaining references
            self.brain = None
            self.tts = None
            self.stt = None
            self.wake_detector = None
            self.push_to_talk = None
            self.time_based_focus = None
            
            print("🧹 Final resource cleanup complete")
        except Exception as e:
            print(f"⚠️ Error during final cleanup: {e}")

def main():
    """Main entry point"""
    nova = None
    try:
        nova = HeyNova()
        nova.start()
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt detected, shutting down...")
        if nova:
            try:
                nova.cleanup()
            except Exception as e:
                print(f"Error during cleanup: {e}")
        print("🔄 Exiting gracefully...")
    except Exception as e:
        print(f"Fatal error: {e}")
        if nova:
            try:
                nova.cleanup()
            except Exception as cleanup_error:
                print(f"Error during cleanup: {cleanup_error}")
        print("🔄 Exiting due to fatal error...")
    finally:
        # Ensure cleanup happens even if there are errors
        if nova:
            try:
                nova.cleanup()
            except Exception as e:
                print(f"Final cleanup error: {e}")
        print("✅ Exit complete")

if __name__ == "__main__":
    main()
