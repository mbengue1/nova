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
from typing import Optional

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from wakeword import WakeWordDetector, PushToTalkDetector
from stt import SpeechTranscriber
from tts import SpeechSynthesizer
from brain import NovaBrain
from nova_logger import logger

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
        
        # system state variables
        self.is_running = False
        self.current_mode = "wake_word"  # or "push_to_talk"
        
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
        
        # Set initial mode to conversation
        self.current_mode = "conversation"
        self.is_running = True
        
        # give welcome greeting
        self._welcome_greeting()
        
        # Start in conversation mode immediately
        print("\n🔊 Nova is ready and listening...")
        print("   (Press Ctrl+C to exit)")
        
        # Process first input directly without wake word
        self._process_user_input(use_streaming=True, first_interaction=True)
        
        # main system loop - after first interaction, system will be in wake word mode
        try:
            print("\n🔊 Nova is now in wake word mode - say 'Hey Nova' to activate")
            print("   (Press Ctrl+C to exit)")
            while self.is_running:
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
    
    def _welcome_greeting(self):
        """Give personalized welcome greeting"""
        try:
            # get current time for appropriate greeting
            from datetime import datetime
            import pytz
            
            tz = pytz.timezone(config.timezone)
            current_time = datetime.now(tz)
            hour = current_time.hour
            
            if 5 <= hour < 12:
                greeting = "Good morning"
            elif 12 <= hour < 17:
                greeting = "Good afternoon"
            else:
                greeting = "Good evening"
            
            welcome_message = f"{greeting}, {config.user_title}! Welcome home. How may I serve you today?"
            
            print(f"🎭 {welcome_message}")
            self.tts.speak(welcome_message)
            
        except Exception as e:
            print(f"Error in welcome greeting: {e}")
            # fallback greeting
            fallback = f"Hello, {config.user_title}! Welcome home. How may I serve you today?"
            print(f"🎭 {fallback}")
            self.tts.speak(fallback)
    
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
                    
                    # Speak the full response
                    if not self._speak_with_fallback(full_response):
                        print("⚠️  TTS failed")
                else:
                    # Get full response at once
                    response = self.brain.process_input(user_input)
                    
                    if response:
                        print(f"🤖 Nova: {response}")
                        
                        # speak response to user with fallback
                        if not self._speak_with_fallback(response):
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
            
    def _speak_with_fallback(self, text: str) -> bool:
        """Speak text with fallback mechanisms
        
        Returns:
            bool: True if speech was successful, False otherwise
        """
        if not text:
            return False
            
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
                        
                        # Speak the full response with fallback
                        if not self._speak_with_fallback(full_response):
                            print("⚠️  TTS failed")
                        else:
                            # Reset activity timer after speaking
                            last_activity_time = time.time()
                    else:
                        # Get full response at once
                        response = self.brain.process_input(user_input)
                        
                        if response:
                            print(f"🤖 Nova: {response}")
                            if not self._speak_with_fallback(response):
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
    
    def _return_to_wake_word_mode(self, message: str = "I'll be listening for 'Hey Nova' when you need me again."):
        """Return to wake word detection mode with a message
        
        Args:
            message: The message to speak before returning to wake word mode
        """
        # Speak the transition message
        self._speak_with_fallback(message)
        
        # Set mode to wake word
        self.current_mode = "wake_word"
        
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
            # Force immediate cleanup and exit
            self.cleanup()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            # Force exit regardless of cleanup success
            import os
            os._exit(0)
    
    def cleanup(self):
        """Clean up resources"""
        print("🧹 Cleaning up...")
        
        # Force stop any active processes
        self.is_running = False
        
        # Stop any active speech first
        try:
            self.tts.stop_speaking()
            print("🔇 Speech stopped")
        except Exception:
            pass
            
        # Say goodbye before shutting down (only if not already speaking)
        try:
            if not self.tts.is_currently_speaking():
                self.tts.speak("Goodbye! It was a pleasure serving you.")
        except Exception:
            pass
        
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
        except Exception:
            pass
        
        # Clean up STT
        try:
            self.stt.cleanup()
            print("🔇 Speech recognition stopped")
        except Exception:
            pass
        
        # Final stop of TTS
        try:
            self.tts.stop_speaking()
        except Exception:
            pass
        
        print("✅ Cleanup complete. Goodbye!")

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
        # Force exit to avoid segmentation faults
        import os
        os._exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        if nova:
            try:
                nova.cleanup()
            except:
                pass
        # Force exit to avoid segmentation faults
        import os
        os._exit(1)

if __name__ == "__main__":
    main()
