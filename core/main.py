"""
Hey Nova - Main Entry Point
Orchestrates wake word detection, STT, brain processing, and TTS
"""
import signal
import sys
import time
from typing import Optional

from config import config
from wakeword import WakeWordDetector, PushToTalkDetector
from stt import SpeechTranscriber
from tts import SpeechSynthesizer
from brain import NovaBrain

class HeyNova:
    """Main Nova assistant class"""
    
    def __init__(self):
        print("🚀 Initializing Hey Nova...")
        
        # initialize core components
        self.brain = NovaBrain()
        self.tts = SpeechSynthesizer()
        self.stt = SpeechTranscriber()
        
        # initialize wake word detection systems
        self.wake_detector = WakeWordDetector(self._on_wake_word)
        self.push_to_talk = PushToTalkDetector(self._on_push_to_talk)
        
        # system state variables
        self.is_running = False
        self.current_mode = "wake_word"  # or "push_to_talk"
        
        # setup system signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def start(self):
        """Start Nova assistant"""
        print("\n" + "="*50)
        print("🌟 Hey Nova is now active!")
        print("="*50)
        
        # validate system configuration
        config.validate_config()
        
        # start wake word detection
        try:
            self.wake_detector.start_listening()
            self.current_mode = "wake_word"
            print("🎧 Listening for 'Hey Nova'...")
            print("   (Press Ctrl+C to exit)")
        except Exception as e:
            print(f"⚠️  Wake word detection failed: {e}")
            print("🔄 Falling back to push-to-talk mode...")
            self.push_to_talk.start_listening()
            self.current_mode = "push_to_talk"
        
        self.is_running = True
        
        # main system loop
        try:
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        finally:
            self.cleanup()
    
    def _on_wake_word(self):
        """Called when wake word is detected"""
        print("\n🔔 Wake word detected!")
        self._process_user_input()
    
    def _on_push_to_talk(self):
        """Called when push-to-talk is activated"""
        print("\n🎤 Push-to-talk activated!")
        self._process_user_input()
    
    def _process_user_input(self):
        """Process user input through the full pipeline"""
        try:
            # get speech input from user
            print("🎤 Listening for your request...")
            user_input = self.stt.record_audio()
            
            if not user_input:
                print("⚠️  No speech detected")
                self.tts.speak("I didn't catch that. Could you please repeat?")
                return
            
            print(f"👤 You said: '{user_input}'")
            
            # process request with brain
            print("🧠 Processing your request...")
            response = self.brain.process_input(user_input)
            
            if response:
                print(f"🤖 Nova: {response}")
                
                # speak response to user
                self.tts.speak(response)
                
                # enter conversation mode for follow-up responses
                self._enter_conversation_mode()
            else:
                print("⚠️  No response generated")
                self.tts.speak("I'm sorry, I couldn't process that request.")
                
        except Exception as e:
            print(f"Error processing user input: {e}")
            self.tts.speak("I encountered an error. Please try again.")
    
    def _enter_conversation_mode(self):
        """Enter conversation mode for continuous dialogue"""
        print("\n💬 Conversation mode: I'm listening for your response...")
        print("   (Say 'goodbye' or 'exit' to end conversation, or just speak naturally)")
        
        # continue listening for user responses
        while True:
            try:
                # listen for follow-up response
                print("🎤 Listening for your response...")
                user_input = self.stt.record_audio()
                
                if not user_input:
                    print("⚠️  No speech detected")
                    continue
                
                # check for exit commands
                if any(word in user_input.lower() for word in ['goodbye', 'exit', 'stop', 'end', 'good night', 'bye', 'see you']):
                    print("👋 Ending conversation, returning to wake word mode...")
                    self.tts.speak("Goodbye! I'll be here when you need me.")
                    return  # exit conversation mode completely
                
                print(f"👤 You said: '{user_input}'")
                
                # process response with brain
                print("🧠 Processing your response...")
                response = self.brain.process_input(user_input)
                
                if response:
                    print(f"🤖 Nova: {response}")
                    self.tts.speak(response)
                else:
                    print("⚠️  No response generated")
                    self.tts.speak("I'm sorry, I couldn't process that.")
                    
            except KeyboardInterrupt:
                print("\n🔄 Returning to wake word mode...")
                break
            except Exception as e:
                print(f"Error in conversation mode: {e}")
                self.tts.speak("I encountered an error. Let's continue our conversation.")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.is_running = False
    
    def cleanup(self):
        """Clean up resources"""
        print("🧹 Cleaning up...")
        
        # say goodbye before shutting down
        try:
            self.tts.speak("Goodbye! It was a pleasure serving you.")
        except:
            pass
        
        if self.current_mode == "wake_word":
            self.wake_detector.cleanup()
        else:
            self.push_to_talk.stop_listening()
        
        self.stt.cleanup()
        self.tts.stop_speaking()
        
        print("✅ Cleanup complete. Goodbye!")

def main():
    """Main entry point"""
    try:
        nova = HeyNova()
        nova.start()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
