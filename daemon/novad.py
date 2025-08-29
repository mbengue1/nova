#!/usr/bin/env python3
"""
Nova Daemon - Production Home Starter Mode System

This daemon provides the complete Nova experience with:
- Wake word detection ("Hey Nova")
- Speech-to-text with VAD and Whisper
- Natural language processing via NovaBrain
- Text-to-speech with Azure TTS
- Interruption handling (barge-in capability)
- Spotify integration and focus control
- Calendar management and smart scheduling
- IPC server for external communication
- State machine for proper flow control

The system runs in background mode, listening for wake words,
and provides seamless conversation with full interruption support.
"""

import os
import sys
import time
import json
import socket
import threading
import logging
import signal
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import configuration
from core.config import config

# Import core services
from core.services.spotify_applescript import SpotifyAppleScript
from core.services.calendar_service import CalendarService
from core.services.app_control_service import FocusController

# Import complete Nova audio pipeline
from wakeword import WakeWordDetector, PushToTalkDetector
from stt import SpeechTranscriber
from tts import SpeechSynthesizer
from brain import NovaBrain

# Import state machine and scheduling
from tests.test_state_machine import NovaStateMachine
from core.scheduling.class_scheduler import ClassScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/nova_daemon.log'),
        logging.StreamHandler()
    ]
)

class NovaDaemon:
    """Production Nova Daemon with complete audio pipeline and all capabilities"""
    
    def __init__(self):
        """Initialize the Nova daemon with all components"""
        self.running = False
        self.is_running = False
        
        # Initialize core services
        self.state_machine = NovaStateMachine()
        self.spotify = SpotifyAppleScript()
        self.calendar = CalendarService()
        self.focus_controller = FocusController()
        
        # Initialize complete Nova audio pipeline
        print("🚀 Initializing complete Nova audio pipeline...")
        self.brain = NovaBrain()
        self.tts = SpeechSynthesizer()
        self.stt = SpeechTranscriber()
        
        # Setup interrupt handling between STT and TTS
        self.stt.set_interrupt_callback(self._interrupt_speech)
        
        # Initialize wake word detection systems
        self.wake_detector = WakeWordDetector(self._on_wake_word)
        self.push_to_talk = PushToTalkDetector(self._on_push_to_talk)
        
        # Smart scheduling and login detection
        self.scheduler = ClassScheduler('config/class_schedule.yaml')
        self.login_detection_file = "/tmp/nova_login_detection"
        self._setup_login_detection()
        
        # IPC server setup
        self.socket_path = "/tmp/nova.sock"
        self.server_socket = None
        self.clients = []
        
        # System state variables
        self.current_mode = "wake_word"  # or "push_to_talk"
        self.conversation_state = {
            "active": False,
            "last_input": None,
            "last_response": None,
            "interruption_count": 0,
            "last_interruption": None,
            "greeting_given": False
        }
        
        # Signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logging.info("🚀 Nova Daemon initialized with complete audio pipeline")
    
    def _setup_login_detection(self):
        """Setup login detection to trigger fresh greetings on each daemon start"""
        try:
            # Create timestamp file for login detection
            current_time = time.time()
            with open(self.login_detection_file, 'w') as f:
                f.write(str(current_time))
            
            # Remove old greeting lockfile to force fresh greeting
            if os.path.exists("/tmp/nova_greeting.lock"):
                os.remove("/tmp/nova_greeting.lock")
                logging.info("🔄 Login detected - removing old greeting lock for fresh welcome")
            else:
                logging.info("🆕 Fresh login session - Nova will greet you")
                
        except Exception as e:
            logging.warning(f"⚠️ Login detection setup failed: {e}")
    
    def _on_wake_word(self):
        """Callback when wake word is detected"""
        logging.info("🔔 Wake word detected!")
        print("🔔 Wake word detected!")
        
        # Check smart scheduling first
        should_run, reason = self.scheduler.should_nova_run_now()
        if not should_run:
            logging.info(f"🤫 Wake word ignored due to scheduling: {reason}")
            return
        
        logging.info(f"✅ Wake word accepted: {reason}")
        print("💬 Processing single request...")
        
        self.current_mode = "active"
        self._process_single_request()
    
    def _on_push_to_talk(self):
        """Callback when push-to-talk is activated"""
        logging.info("🎤 Push-to-talk activated!")
        print("🎤 Push-to-talk activated!")
        print("💬 Processing single request...")
        
        self.current_mode = "active"
        self._process_single_request()
    
    def _interrupt_speech(self):
        """Handle speech interruption (barge-in capability)"""
        if self.tts.is_currently_speaking():
            logging.info("🛑 User interrupted speech - stopping TTS")
            print("🛑 User interrupted speech - stopping TTS")
            self.tts.stop_speaking()
            
            # Check if we have captured audio from the interruption
            interruption_audio = None
            if hasattr(self.tts, 'interruption_monitor') and self.tts.interruption_monitor:
                interruption_audio = self.tts.interruption_monitor.get_interruption_audio_file()
            
            if interruption_audio and os.path.exists(interruption_audio):
                logging.info(f"🎤 Processing interruption audio: {interruption_audio}")
                print(f"🎤 Processing interruption audio: {interruption_audio}")
                
                # Process the interruption audio with our transcriber
                try:
                    # Try up to 2 times to get a valid transcription
                    interruption_text = None
                    
                    # First attempt - use faster transcription for responsiveness
                    logging.info("🎧 Fast-transcribing interruption audio...")
                    print("🎧 Fast-transcribing interruption audio...")
                    interruption_text = self.stt.transcribe_file(interruption_audio)
                    
                    # If first attempt failed, try again with more careful transcription
                    if not interruption_text or len(interruption_text.strip()) == 0:
                        logging.info("⚠️ Empty transcription on first attempt, retrying...")
                        print(f"⚠️ Empty transcription on first attempt, retrying with more careful processing...")
                        time.sleep(0.1)  # Very short delay
                        interruption_text = self.stt.transcribe_file(interruption_audio)
                    
                    if interruption_text and len(interruption_text.strip()) > 0:
                        logging.info(f"👤 Interruption: '{interruption_text}'")
                        print(f"👤 Interruption: '{interruption_text}'")
                        
                        # Process the interruption text immediately
                        logging.info("🧠 Processing interruption...")
                        print("🧠 Processing interruption...")
                        self._process_interruption(interruption_text)
                    else:
                        logging.warning("⚠️ Empty transcription from interruption audio after multiple attempts")
                        print("⚠️ Empty transcription from interruption audio after multiple attempts")
                        # Give shorter response for better flow
                        self._speak_with_fallback("I heard you, but couldn't understand. Could you repeat that?", allow_interruption=True)
                        # Continue with standard listening
                        logging.info("🎤 Continuing with standard listening...")
                        print("🎤 Continuing with standard listening...")
                        self.stt.reset_state()
                        self._process_user_input(use_streaming=True)
                except Exception as e:
                    logging.error(f"❌ Error processing interruption: {e}")
                    print(f"❌ Error processing interruption: {e}")
                    # Continue with standard listening with minimal response
                    self._speak_with_fallback("Sorry, could you try again?", allow_interruption=True)
                    logging.info("🎤 Continuing with standard listening due to error...")
                    print("🎤 Continuing with standard listening due to error...")
                    self.stt.reset_state()
                    self._process_single_request()
            else:
                logging.warning("⚠️ No interruption audio captured, continuing with standard listening")
                print("⚠️ No interruption audio captured, continuing with standard listening")
                # Continue with standard listening
                self.stt.reset_state()
                self._process_single_request()
    
    def _process_single_request(self):
        """Process a single user request and return to background mode"""
        try:
            logging.info("🎯 Processing single user request...")
            print("🎯 Processing single user request...")
            
            # Process user input
            self._process_user_input(use_streaming=True, first_interaction=False)
            
            # Return to background mode
            self._return_to_background_mode()
            
        except Exception as e:
            logging.error(f"❌ Error processing single request: {e}")
            print(f"❌ Error processing single request: {e}")
            self._return_to_background_mode()
    
    def _process_user_input(self, use_streaming: bool = True, first_interaction: bool = False):
        """Process user input through the complete Nova pipeline"""
        try:
            # Get speech input from user with fallback mechanisms
            if first_interaction:
                logging.info("🎤 I'm listening... (speak now)")
                print("🎤 I'm listening... (speak now)")
            else:
                logging.info("🎤 Listening for your request...")
                print("🎤 Listening for your request...")
            
            # Try VAD-based recording first
            user_input = None
            try:
                user_input = self.stt.record_audio_with_vad()
            except Exception as stt_error:
                logging.error(f"STT recording failed: {stt_error}")
                print(f"⚠️  VAD recording failed: {stt_error}")
                print("🔄 Falling back to fixed duration recording...")
                
                # Fallback to fixed duration recording
                try:
                    user_input = self.stt.record_audio_fixed()
                except Exception as fixed_error:
                    logging.error(f"Fixed recording failed: {fixed_error}")
                    print(f"⚠️  Fixed recording failed: {fixed_error}")
            
            if not user_input:
                logging.warning("⚠️ No speech detected")
                print("⚠️  No speech detected")
                self.tts.speak("I didn't catch that. Could you please repeat?")
                return
            
            logging.info(f"👤 You said: '{user_input}'")
            print(f"👤 You said: '{user_input}'")
            
            # Process request with brain
            logging.info("🧠 Processing your request...")
            print("🧠 Processing your request...")
            
            # Get response from brain
            response = self.brain.process_input(user_input)
            
            if response:
                logging.info(f"🧠 Brain response: {response}")
                print(f"🧠 Brain response: {response}")
                
                # Speak the response
                self.tts.speak(response)
            else:
                logging.warning("⚠️ No response from brain")
                print("⚠️ No response from brain")
                self.tts.speak("I'm sorry, I couldn't process that request.")
                
        except Exception as e:
            logging.error(f"❌ Error processing user input: {e}")
            print(f"❌ Error processing user input: {e}")
            self.tts.speak("I encountered an error processing your request. Please try again.")
    
    def _process_interruption(self, interruption_text: str):
        """Process interruption text immediately"""
        try:
            logging.info(f"🧠 Processing interruption: {interruption_text}")
            print(f"🧠 Processing interruption: {interruption_text}")
            
            # Process the interruption with brain
            response = self.brain.process_input(interruption_text)
            
            if response:
                logging.info(f"🧠 Interruption response: {response}")
                print(f"🧠 Interruption response: {response}")
                
                # Speak the response
                self.tts.speak(response)
            else:
                logging.warning("⚠️ No response for interruption")
                print("⚠️ No response for interruption")
                self.tts.speak("I heard your interruption but couldn't process it.")
                
        except Exception as e:
            logging.error(f"❌ Error processing interruption: {e}")
            print(f"❌ Error processing interruption: {e}")
            self.tts.speak("Sorry, I couldn't process your interruption.")
    
    def _speak_with_fallback(self, text: str, allow_interruption: bool = False):
        """Speak text with fallback and interruption support"""
        try:
            if allow_interruption:
                # Use TTS with interruption support
                self.tts.speak(text)
            else:
                # Use standard TTS
                self.tts.speak(text)
        except Exception as e:
            logging.error(f"❌ TTS failed: {e}")
            print(f"❌ TTS failed: {e}")
            # Fallback to system say command
            try:
                subprocess.run(["say", text], check=True, timeout=5)
                logging.info(f"🗣️ Fallback TTS: {text}")
                print(f"🗣️ Fallback TTS: {text}")
            except Exception as fallback_error:
                logging.error(f"❌ Fallback TTS also failed: {fallback_error}")
                print(f"❌ Fallback TTS also failed: {fallback_error}")
    
    def _return_to_background_mode(self):
        """Return to background mode after processing request"""
        try:
            logging.info("🌙 Returning to background mode...")
            print("🌙 Returning to background mode...")
            
            # Reset conversation state
            self.conversation_state["active"] = False
            self.current_mode = "wake_word"
            
            # Reset STT state
            self.stt.reset_state()
            
            logging.info("✅ Back to background mode - listening for wake word")
            print("✅ Back to background mode - listening for wake word")
            
        except Exception as e:
            logging.error(f"❌ Error returning to background mode: {e}")
            print(f"❌ Error returning to background mode: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logging.info(f"📡 Received signal {signum}, shutting down gracefully...")
        self.shutdown()
    
    def start(self):
        """Start the Nova daemon with complete audio pipeline"""
        logging.info("🚀 Starting Nova Daemon...")
        
        try:
            # Start IPC server
            if not self._start_ipc_server():
                logging.error("❌ Failed to start IPC server")
                return False
            
            # Run startup sequence
            if not self._run_startup_sequence():
                logging.error("❌ Startup sequence failed")
                return False
            
            # Start health monitoring
            self._start_health_monitor()
            
            # Main daemon loop
            self.running = True
            self.is_running = True
            logging.info("✅ Nova Daemon started successfully")
            
            # Start wake word detection in background
            try:
                self.wake_detector.start_listening()
                logging.info("✅ Wake word detection started")
                print("✅ Wake word detection started")
            except Exception as e:
                logging.error(f"⚠️ Wake word detection failed: {e}")
                print(f"⚠️ Wake word detection failed: {e}")
            
            # Start push-to-talk as backup
            try:
                self.push_to_talk.start_listening()
                logging.info("✅ Push-to-talk started")
                print("✅ Push-to-talk started")
            except Exception as e:
                logging.error(f"⚠️ Push-to-talk failed: {e}")
                print(f"⚠️ Push-to-talk failed: {e}")
            
            print("\n🌙 Nova is in background mode - say 'Hey Nova' to activate")
            print("   (Press Ctrl+C to exit)")
            
            while self.running:
                time.sleep(0.1)
                
        except Exception as e:
            logging.error(f"❌ Daemon error: {e}")
            return False
        
        return True
    
    def _run_startup_sequence(self) -> bool:
        """Run the startup sequence with proper state machine integration"""
        logging.info("🚀 Running startup sequence...")
        
        # Check smart scheduling first
        should_run, reason = self.scheduler.should_nova_run_now()
        if not should_run:
            logging.info(f"🤫 Nova scheduled to be silent: {reason}")
            logging.info("   Nova will wait in background mode until allowed time")
            
            # Transition to background mode without greeting
            if not self.state_machine.transition_to("BACKGROUND_IDLE", f"Scheduled silence: {reason}"):
                logging.error("❌ Failed to transition to background mode")
                return False
            
            logging.info("✅ Startup sequence completed (silent mode)")
            return True
        
        logging.info(f"✅ Nova scheduled to run: {reason}")
        
        # Use state machine to determine startup flow
        if not self.state_machine.run_startup_sequence():
            logging.error("❌ Startup sequence failed")
            return False
        
        # If greeting is needed, run it
        if self.state_machine.current_state == "GREETING_ONCE":
            if not self._run_greeting_sequence():
                logging.error("❌ Greeting sequence failed")
                return False
        
        logging.info("✅ Startup sequence completed")
        return True
    
    def _run_greeting_sequence(self) -> bool:
        """Run the one-time greeting sequence - seamless like original Nova"""
        logging.info("🎉 Running greeting sequence...")
        
        try:
            # PREPARE EVERYTHING IN BACKGROUND FIRST (like original Nova)
            logging.info("   🔧 Preparing applications in background...")
            
            # Step 1: Set private mode (fast)
            logging.info("   1. Setting private mode (Do Not Disturb)")
            dnd_success = self.focus_controller.set_do_not_disturb(True)
            
            # Step 2: Start Spotify in background (fast)
            logging.info("   2. Starting Spotify Nightmode playlist")
            spotify_success = self.spotify.ensure_ready_and_play_nightmode()
            
            # Step 3: Get calendar ready (fast)
            logging.info("   3. Preparing calendar schedule")
            schedule_text = self.calendar.format_rest_of_day_schedule()
            
            # NOW GREET WHILE EVERYTHING IS READY (seamless experience)
            logging.info("   🎉 Starting seamless greeting...")
            
            # Welcome message
            welcome_message = self._get_time_based_greeting()
            self._speak_message(welcome_message)
            
            # Private mode confirmation
            if dnd_success:
                self._speak_message("I've set your home to private mode")
            else:
                self._speak_message("I'm setting your home to private mode")
            
            # Music confirmation
            if spotify_success:
                self._speak_message("I've started playing your Nightmode playlist")
            else:
                self._speak_message("I'm starting your music")
            
            # Calendar schedule
            self._speak_message(schedule_text)
            
            # Productive message
            productive_message = self._get_productive_message()
            self._speak_message(productive_message)
            
            # Mark greeting as completed
            self.state_machine.create_greeting_lockfile()
            
            # Transition to background mode
            if not self.state_machine.transition_to("BACKGROUND_IDLE", "Greeting sequence completed"):
                logging.error("❌ Failed to transition to background mode")
                return False
            
            logging.info("✅ Greeting sequence completed successfully")
            return True
            
        except Exception as e:
            logging.error(f"❌ Greeting sequence failed: {e}")
            return False
    
    def _get_time_based_greeting(self) -> str:
        """Get time-appropriate greeting"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            return "Good morning, Sir. Welcome home."
        elif 12 <= current_hour < 17:
            return "Good afternoon, Sir. Welcome home."
        else:
            return "Good evening, Sir. Welcome home."
    
    def _get_productive_message(self) -> str:
        """Get time-appropriate productive message"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            return "Hope you have a productive morning."
        elif 12 <= current_hour < 17:
            return "Hope you have a productive afternoon."
        else:
            return "Hope you have a productive evening."
    
    def _speak_message(self, message: str):
        """Speak a message using TTS"""
        try:
            # Speak the message
            logging.info(f"🗣️ Speaking: {message}")
            self.tts.speak(message)
            
        except Exception as e:
            logging.error(f"❌ TTS failed: {e}")
            # Fallback to system say command
            try:
                subprocess.run(["say", message], check=True, timeout=5)
                logging.info(f"🗣️ Fallback TTS: {message}")
            except Exception as fallback_error:
                logging.error(f"❌ Fallback TTS also failed: {fallback_error}")
    
    def _start_ipc_server(self) -> bool:
        """Start the IPC server for external communication"""
        try:
            # Clean up existing socket
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
            
            # Create Unix domain socket
            self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.server_socket.bind(self.socket_path)
            self.server_socket.listen(5)
            
            # Set socket permissions
            os.chmod(self.socket_path, 0o600)
            
            # Start IPC server thread
            ipc_thread = threading.Thread(target=self._ipc_server_loop, daemon=True)
            ipc_thread.start()
            
            logging.info(f"✅ IPC Server started on {self.socket_path}")
            return True
            
        except Exception as e:
            logging.error(f"❌ IPC server start failed: {e}")
            return False
    
    def _ipc_server_loop(self):
        """IPC server main loop for handling external connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                logging.info("🔌 New client connected")
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_ipc_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    logging.warning(f"⚠️ Client connection error: {e}")
    
    def _handle_ipc_client(self, client_socket):
        """Handle individual IPC client connection"""
        self.clients.append(client_socket)
        
        try:
            while self.running:
                # Receive message
                data = client_socket.recv(4096)
                if not data:
                    break
                
                # Parse and handle message
                try:
                    message = json.loads(data.decode('utf-8'))
                    response = self._process_ipc_message(message)
                    
                    if response:
                        client_socket.send(json.dumps(response).encode('utf-8'))
                        
                except json.JSONDecodeError as e:
                    logging.error(f"❌ Invalid JSON: {e}")
                    error_response = {
                        "type": "Error",
                        "error": "Invalid JSON format",
                        "details": str(e)
                    }
                    client_socket.send(json.dumps(error_response).encode('utf-8'))
                    
        except Exception as e:
            logging.warning(f"⚠️ Client handling error: {e}")
        finally:
            # Clean up
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()
            logging.info("🔌 Client disconnected")
    
    def _process_ipc_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming IPC message"""
        message_type = message.get('type')
        
        handlers = {
            "WakeDetected": self._handle_wake_detected,
            "BeginSTT": self._handle_begin_stt,
            "NLPRoute": self._handle_nlp_route,
            "ExecuteSkill": self._handle_execute_skill,
            "Speak": self._handle_speak,
            "Transition": self._handle_transition,
            "Health": self._handle_health,
            "Status": self._handle_status
        }
        
        if message_type in handlers:
            return handlers[message_type](message)
        else:
            return {
                "type": "Error",
                "error": "Unknown message type",
                "details": f"Unsupported type: {message_type}"
            }
    
    def _handle_wake_detected(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle wake word detection via IPC"""
        logging.info("👂 Wake word detected via IPC")
        
        # Check smart scheduling first
        should_run, reason = self.scheduler.should_nova_run_now()
        if not should_run:
            logging.info(f"🤫 Wake word ignored due to scheduling: {reason}")
            return {
                "type": "WakeDetected",
                "status": "silent",
                "reason": f"Respecting class schedule: {reason}",
                "state": self.state_machine.current_state,
                "timestamp": time.time()
            }
        
        logging.info(f"✅ Wake word accepted: {reason}")
        
        # Use state machine to handle wake word
        if self.state_machine.handle_wake_word():
            return {
                "type": "WakeDetected",
                "status": "success",
                "state": self.state_machine.current_state,
                "timestamp": time.time()
            }
        else:
            return {
                "type": "WakeDetected",
                "status": "error",
                "error": "Invalid state for wake word",
                "timestamp": time.time()
            }
    
    def _handle_begin_stt(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle speech-to-text request via IPC"""
        req_id = message.get('req_id', 'unknown')
        max_seconds = message.get('max_seconds', 10)
        
        logging.info(f"🎤 STT request {req_id} for {max_seconds}s")
        
        # TODO: Integrate with actual STT service
        # For now, simulate STT processing
        time.sleep(1)
        
        return {
            "type": "STTResult",
            "req_id": req_id,
            "text": "Hello Nova, what's my schedule for today?",
            "confidence": 0.95,
            "status": "success"
        }
    
    def _handle_nlp_route(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle NLP routing request via IPC"""
        req_id = message.get('req_id', 'unknown')
        text = message.get('text', '')
        
        logging.info(f"🧠 NLP routing request {req_id}: '{text}'")
        
        # Simple intent detection (can be enhanced with GPT later)
        if "schedule" in text.lower():
            intent = "GetSchedule"
            slots = {"timeframe": "today"}
        elif "music" in text.lower() or "spotify" in text.lower():
            intent = "ControlMusic"
            slots = {"action": "play"}
        elif "focus" in text.lower() or "dnd" in text.lower():
            intent = "ControlFocus"
            slots = {"mode": "Do Not Disturb"}
        else:
            intent = "Unknown"
            slots = {}
        
        return {
            "type": "Intent",
            "req_id": req_id,
            "intent": intent,
            "slots": slots,
            "reply_template": f"I'll help you with {intent}",
            "status": "success"
        }
    
    def _handle_execute_skill(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle skill execution request via IPC"""
        req_id = message.get('req_id', 'unknown')
        intent = message.get('intent', {})
        
        logging.info(f"⚡ Skill execution request {req_id}: {intent}")
        
        try:
            skill_name = intent.get('name', 'Unknown')
            
            if skill_name == "GetSchedule":
                result = self._execute_get_schedule()
            elif skill_name == "ControlMusic":
                result = self._execute_control_music()
            elif skill_name == "ControlFocus":
                result = self._execute_control_focus()
            else:
                result = {"success": False, "error": f"Unknown skill: {skill_name}"}
            
            return {
                "type": "SkillResult",
                "req_id": req_id,
                "ok": result.get("success", False),
                "data": result,
                "status": "success"
            }
            
        except Exception as e:
            logging.error(f"❌ Skill execution failed: {e}")
            return {
                "type": "SkillResult",
                "req_id": req_id,
                "ok": False,
                "data": {"error": str(e)},
                "status": "error"
            }
    
    def _execute_get_schedule(self) -> Dict[str, Any]:
        """Execute get schedule skill"""
        try:
            schedule_text = self.calendar.format_rest_of_day_schedule()
            return {
                "success": True,
                "schedule": schedule_text,
                "timestamp": time.time()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_control_music(self) -> Dict[str, Any]:
        """Execute music control skill"""
        try:
            success = self.spotify.ensure_ready_and_play_nightmode()
            return {
                "success": success,
                "action": "play_nightmode",
                "timestamp": time.time()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_control_focus(self) -> Dict[str, Any]:
        """Execute focus control skill"""
        try:
            success = self.focus_controller.set_do_not_disturb(True)
            return {
                "success": success,
                "action": "set_dnd",
                "timestamp": time.time()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_speak(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text-to-speech request via IPC"""
        req_id = message.get('req_id', 'unknown')
        text = message.get('text', '')
        
        logging.info(f"🗣️ TTS request {req_id}: '{text[:50]}...'")
        
        # TODO: Integrate with actual TTS service
        # For now, simulate TTS processing
        time.sleep(1)
        
        return {
            "type": "TTSResult",
            "req_id": req_id,
            "ok": True,
            "status": "success"
        }
    
    def _handle_transition(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle state transition via IPC"""
        from_state = message.get('from', 'unknown')
        to_state = message.get('to', 'unknown')
        reason = message.get('reason', 'no reason')
        
        logging.info(f"🔄 State transition: {from_state} → {to_state} ({reason})")
        
        # Use state machine for transitions
        if self.state_machine.transition_to(to_state, reason):
            return {
                "type": "Transition",
                "status": "success",
                "from": from_state,
                "to": to_state,
                "reason": reason,
                "timestamp": time.time()
            }
        else:
            return {
                "type": "Transition",
                "status": "error",
                "error": "Invalid transition",
                "timestamp": time.time()
            }
    
    def _handle_health(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health check request via IPC"""
        return {
            "type": "Health",
            "status": "healthy",
            "state": self.state_machine.current_state,
            "clients": len(self.clients),
            "workers": 0,  # No workers in this implementation
            "uptime": time.time(),
            "timestamp": time.time()
        }
    
    def _handle_status(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status request via IPC"""
        # Get smart scheduling status
        should_run, reason = self.scheduler.should_nova_run_now()
        current_class_info = self.scheduler.get_current_class_info()
        next_class_info = self.scheduler.get_next_class_info()
        
        return {
            "type": "Status",
            "status": "running",
            "state": self.state_machine.current_state,
            "clients": len(self.clients),
            "workers": 0,  # No workers in this implementation
            "socket_path": self.socket_path,
            "smart_scheduling": {
                "scheduled_to_run": should_run,
                "reason": reason,
                "current_class": current_class_info,
                "next_class": next_class_info,
                "buffer_minutes": self.scheduler.buffer_minutes,
                "class_hours_protection": "enabled"
            },
            "timestamp": time.time()
        }
    
    def _start_health_monitor(self):
        """Start health monitoring thread"""
        def health_monitor():
            while self.running:
                try:
                    # Check daemon health
                    current_time = time.time()
                    logging.debug(f"🏥 Health check at {datetime.fromtimestamp(current_time)}")
                    
                    # Check state machine health
                    if self.state_machine.current_state == "RECOVER":
                        logging.warning("⚠️ State machine in recovery mode")
                    
                    time.sleep(30)  # Health check every 30 seconds
                    
                except Exception as e:
                    logging.error(f"❌ Health monitor error: {e}")
                    time.sleep(5)
        
        health_thread = threading.Thread(target=health_monitor, daemon=True)
        health_thread.start()
        logging.info("🏥 Health monitor started")
    
    def shutdown(self):
        """Shutdown the daemon gracefully"""
        logging.info("🛑 Shutting down Nova Daemon...")
        
        self.running = False
        self.is_running = False
        
        # Stop wake word detection
        try:
            if hasattr(self, 'wake_detector'):
                self.wake_detector.stop_listening()
                logging.info("🎧 Wake word detection stopped")
        except Exception as e:
            logging.warning(f"⚠️ Error stopping wake word detection: {e}")
        
        # Stop push-to-talk
        try:
            if hasattr(self, 'push_to_talk'):
                self.push_to_talk.stop_listening()
                logging.info("⌨️ Push-to-talk stopped")
        except Exception as e:
            logging.warning(f"⚠️ Error stopping push-to-talk: {e}")
        
        # Clean up audio pipeline
        try:
            if hasattr(self, 'tts'):
                self.tts.stop_speaking()
                logging.info("🗣️ TTS stopped")
        except Exception as e:
            logging.warning(f"⚠️ Error stopping TTS: {e}")
        
        # Clean up old audio files
        try:
            if hasattr(self.tts, 'interruption_monitor') and self.tts.interruption_monitor:
                logging.info("🧹 Cleaning up old audio files...")
                deleted_count = self.tts.interruption_monitor.auto_cleanup()
                if deleted_count > 0:
                    logging.info(f"✅ Cleaned up {deleted_count} old audio files")
                else:
                    logging.info("✅ No old audio files to clean up")
        except Exception as e:
            logging.warning(f"⚠️ Audio cleanup failed: {e}")
        
        # Close client connections
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        
        # Close server socket
        if self.server_socket:
            self.server_socket.close()
        
        # Clean up socket file
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        logging.info("✅ Nova Daemon shutdown complete")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            logging.info("🧹 Cleaning up Nova Daemon resources...")
            
            # Clean up wake word detector
            if hasattr(self, 'wake_detector'):
                self.wake_detector.cleanup()
            
            # Clean up push-to-talk
            if hasattr(self, 'push_to_talk'):
                self.push_to_talk.cleanup()
            
            # Clean up TTS
            if hasattr(self, 'tts'):
                self.tts.stop_speaking()
            
            # Clean up STT
            if hasattr(self, 'stt'):
                self.stt.reset_state()
            
            logging.info("✅ Cleanup completed")
            
        except Exception as e:
            logging.error(f"❌ Error during cleanup: {e}")

def main():
    """Main function to run the Nova daemon"""
    print("🚀 Starting Nova Daemon...")
    
    daemon = NovaDaemon()
    
    try:
        if daemon.start():
            print("✅ Nova Daemon started successfully")
        else:
            print("❌ Nova Daemon failed to start")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
    finally:
        daemon.shutdown()
        print("✅ Nova Daemon stopped")

if __name__ == "__main__":
    main()
