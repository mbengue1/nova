"""
Speech-to-Text using Whisper
Converts audio input to text for processing
"""
import sounddevice as sd
import numpy as np
import threading
import time
from typing import Optional, Callable
from faster_whisper import WhisperModel
from config import config

class SpeechTranscriber:
    """Handles speech-to-text conversion using Whisper"""
    
    def __init__(self):
        self.audio = None
        self.whisper_model = None
        self.is_recording = False
        self.audio_frames = []
        
        # initialize whisper speech recognition model
        try:
            # use faster-whisper for improved performance
            self.whisper_model = WhisperModel(
                "base",  # base model for mvp
                device="cpu",  # cpu processing for mvp
                compute_type="int8"
            )
            print("✅ Whisper model loaded")
        except Exception as e:
            print(f"⚠️  Warning: Could not load Whisper model: {e}")
            print("   Text input mode will be used instead")
    
    def record_audio(self, duration: int = None) -> Optional[str]:
        """Record audio and transcribe to text"""
        if not self.whisper_model:
            # fallback to text input mode
            return input("Type your message: ")
        
        duration = duration or config.record_seconds
        
        print(f"🎤 Recording for {duration} seconds...")
        print("   Speak now!")
        
        # record audio using sounddevice
        try:
            # record audio input
            audio_data = sd.rec(
                int(config.sample_rate * duration),
                samplerate=config.sample_rate,
                channels=1,
                dtype=np.int16
            )
            
            # wait for recording to complete
            sd.wait()
            
            print("🔇 Recording stopped")
            
            # store audio data for transcription
            self.audio_frames = [audio_data.tobytes()]
            
            # transcribe audio to text
            return self._transcribe_audio()
            
        except Exception as e:
            print(f"Error recording audio: {e}")
            return None
    
    def _transcribe_audio(self) -> Optional[str]:
        """Transcribe recorded audio to text"""
        if not self.audio_frames:
            return None
        
        try:
            # convert audio frames to numpy array
            audio_data = b''.join(self.audio_frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # normalize audio data
            audio_array = audio_array.astype(np.float32) / 32768.0
            
            # transcribe audio with whisper model
            segments, _ = self.whisper_model.transcribe(
                audio_array,
                language="en",
                beam_size=5
            )
            
            # extract transcription text from segments
            transcription = " ".join([segment.text for segment in segments])
            
            if transcription.strip():
                print(f"📝 Transcribed: '{transcription}'")
                return transcription.strip()
            else:
                print("⚠️  No speech detected")
                return None
                
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return None
    
    def stop_recording(self):
        """Stop audio recording"""
        self.is_recording = False
    
    def cleanup(self):
        """Clean up resources"""
        # sounddevice doesn't need explicit cleanup
        pass

class TextInputFallback:
    """Fallback text input when audio isn't available"""
    
    @staticmethod
    def get_input(prompt: str = "Type your message: ") -> str:
        """Get text input from user"""
        return input(prompt)
