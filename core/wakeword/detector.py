"""
Wake word detector using Porcupine
Detects "Hey Nova" wake phrase efficiently
"""
import pvporcupine
import pyaudio
import numpy as np
import struct
import threading
import time
from typing import Callable, Optional
from config import config

class WakeWordDetector:
    """Detects wake word using Porcupine"""
    
    def __init__(self, wake_word_callback: Callable[[], None]):
        self.wake_word_callback = wake_word_callback
        self.is_listening = False
        self.audio = None
        self.porcupine = None
        self.audio_stream = None
        
        # initialize porcupine wake word detection
        try:
            # attempt to load custom nova wake word model
            try:
                self.porcupine = pvporcupine.create(
                    access_key=config.picovoice_access_key,
                    keyword_paths=['Hey-Nova_en_mac_v3_0_0/Hey-Nova_en_mac_v3_0_0.ppn']
                )
                print("✅ Custom Nova wake word model loaded!")
            except Exception as e:
                print(f"⚠️  Could not load custom Nova model: {e}")
                print("🔄 Falling back to default 'computer' keyword...")
                self.porcupine = pvporcupine.create(
                    access_key=config.picovoice_access_key,
                    keywords=['computer'],
                    sensitivities=[0.5]
                )
            print("✅ Wake word detector initialized")
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize Porcupine: {e}")
            print("   Falling back to push-to-talk mode")
            self.porcupine = None
    
    def start_listening(self):
        """Start listening for wake word"""
        if not self.porcupine:
            print("Push-to-talk mode: Press Enter to speak")
            return
            
        self.is_listening = True
        
        # initialize pyaudio for audio input
        self.audio = pyaudio.PyAudio()
        
        # get sample rate and frame length from porcupine
        self.sample_rate = self.porcupine.sample_rate
        self.frame_length = self.porcupine.frame_length
        
        # open audio input stream
        self.audio_stream = self.audio.open(
            rate=self.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.frame_length
        )
        
        print(f"🎧 Audio config: Sample rate={self.sample_rate}, Frame length={self.frame_length}")
        print("🎧 Listening for 'Hey Nova'...")
        
        # start listening in separate thread
        self.listen_thread = threading.Thread(target=self._listen_loop)
        self.listen_thread.daemon = True
        self.listen_thread.start()
    
    def _listen_loop(self):
        """main listening loop for wake word detection"""
        # buffer to collect audio data
        audio_buffer = b''
        bytes_per_frame = self.frame_length * 2  # 2 bytes per sample (16-bit)
        
        print("🎧 Audio streaming started...")
        
        while self.is_listening:
            try:
                # read audio data in smaller chunks to avoid frame size issues
                chunk_size = min(256, self.frame_length)  # read in smaller chunks
                audio_chunk = self.audio_stream.read(
                    chunk_size, 
                    exception_on_overflow=False
                )
                
                # add audio chunk to buffer
                audio_buffer += audio_chunk
                
                # process when buffer has enough data for a complete frame
                while len(audio_buffer) >= bytes_per_frame:
                    # extract exactly one frame from buffer
                    frame_data = audio_buffer[:bytes_per_frame]
                    audio_buffer = audio_buffer[bytes_per_frame:]
                    
                    # convert bytes to numpy array for porcupine processing
                    try:
                        # convert bytes to 16-bit integers, then to numpy array
                        frame_array = np.frombuffer(frame_data, dtype=np.int16)
                        
                        # process frame with porcupine wake word detection
                        keyword_index = self.porcupine.process(frame_array)
                        
                        if keyword_index >= 0:
                            print("🔔 Wake word detected!")
                            self.wake_word_callback()
                    except Exception as e:
                        print(f"❌ Error processing audio frame: {e}")
                        # continue processing other frames
                        continue
                    
            except Exception as e:
                print(f"❌ Error in wake word detection: {e}")
                break
    
    def stop_listening(self):
        """Stop listening for wake word"""
        self.is_listening = False
        
        if self.audio_stream:
            self.audio_stream.close()
        if self.audio:
            self.audio.terminate()
        
        print("🔇 Wake word detection stopped")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            # Stop listening if active
            self.stop_listening()
            
            # Clean up Porcupine instance
            if self.porcupine:
                try:
                    self.porcupine.delete()
                    self.porcupine = None
                except Exception as e:
                    print(f"⚠️ Error deleting Porcupine instance: {e}")
            
            # Clean up audio resources
            if hasattr(self, 'audio'):
                try:
                    if self.audio:
                        self.audio.terminate()
                        self.audio = None
                except Exception as e:
                    print(f"⚠️ Error terminating audio: {e}")
            
            # Clear callback reference
            if hasattr(self, 'wake_word_callback'):
                self.wake_word_callback = None
            
            print("🔇 Wake word detector cleanup complete")
        except Exception as e:
            print(f"⚠️ Error during wake word detector cleanup: {e}")

class PushToTalkDetector:
    """Simple push-to-talk fallback when wake word isn't available"""
    
    def __init__(self, speak_callback: Callable[[], None]):
        self.speak_callback = speak_callback
        self.is_listening = False
        self.input_thread = None
    
    def start_listening(self):
        """Start listening for Enter key press"""
        self.is_listening = True
        print("⌨️  Push-to-talk mode: Press Enter to speak")
        
        self.input_thread = threading.Thread(target=self._input_loop)
        self.input_thread.daemon = True
        self.input_thread.start()
    
    def _input_loop(self):
        """Listen for Enter key press"""
        while self.is_listening:
            try:
                input()  # Wait for Enter
                if self.is_listening:
                    print("🎤 Speak now...")
                    self.speak_callback()
            except (EOFError, KeyboardInterrupt):
                break
    
    def stop_listening(self):
        """Stop listening for input"""
        self.is_listening = False
        print("🔇 Push-to-talk stopped")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            # Stop listening if active
            self.stop_listening()
            
            # Ensure input thread is stopped
            if self.input_thread and self.input_thread.is_alive():
                self.input_thread.join(timeout=2.0)
                if self.input_thread.is_alive():
                    print("⚠️ Push-to-talk input thread did not stop gracefully")
            
            # Clear references
            self.input_thread = None
            self.speak_callback = None
            
            print("🔇 Push-to-talk cleanup complete")
        except Exception as e:
            print(f"⚠️ Error during push-to-talk cleanup: {e}")
