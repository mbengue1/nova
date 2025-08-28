"""
Text-to-Speech using macOS built-in voices
Provides natural speech output for Nova's responses
"""
import subprocess
import platform
from typing import Optional
from config import config

class SpeechSynthesizer:
    """Handles text-to-speech using macOS voices or Azure (if available)"""
    
    def __init__(self):
        self.system = platform.system()
        self.available_voices = self._get_available_voices()
        self.is_speaking = False
        self.current_speech_process = None
        
        # attempt to initialize azure tts for high quality speech
        self.azure_tts = None
        try:
            from .azure_speaker import AzureSpeechSynthesizer
            self.azure_tts = AzureSpeechSynthesizer()
            if self.azure_tts.is_available():
                print(f"✅ Azure TTS initialized with voice: {self.azure_tts.voice_name}")
            else:
                print("⚠️  Azure TTS not available, using macOS voices")
        except ImportError:
            print("⚠️  Azure TTS not available, using macOS voices")
        
        if self.available_voices:
            print(f"✅ macOS TTS initialized with {len(self.available_voices)} voices")
        else:
            print("⚠️  Warning: No TTS voices available")
    
    def _get_available_voices(self) -> list:
        """Get list of available system voices"""
        if self.system != "Darwin":  # macOS
            return []
        
        try:
            # get available voices using macos 'say' command
            result = subprocess.run(
                ["say", "-v", "?"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                voices = []
                for line in result.stdout.split('\n'):
                    if line.strip():
                        # parse voice info (format: name language gender)
                        parts = line.split()
                        if len(parts) >= 2:
                            voice_name = parts[0]
                            # filter for english voices only
                            if any(lang in line.lower() for lang in ['en_', 'en-']):
                                voices.append(voice_name)
                return voices
        except Exception as e:
            print(f"Error getting voices: {e}")
        
        return []
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text to make it more natural for speech output
        
        Removes markdown formatting, asterisks, and other text that shouldn't be spoken
        """
        import re
        
        # Replace markdown bold/italic with nothing
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        # Replace bullet points with natural pauses
        text = re.sub(r'^\s*-\s*', 'Next, ', text, flags=re.MULTILINE)
        
        # Clean up any double spaces
        text = re.sub(r'\s{2,}', ' ', text)
        
        return text
        
    def speak(self, text: str, voice: str = None, rate: float = None, pitch: float = None) -> bool:
        """Convert text to speech and play it"""
        if not text.strip():
            return False
            
        # Stop any current speech before starting a new one
        if self.is_currently_speaking():
            self.stop_speaking()
        
        # Clean text for more natural speech
        cleaned_text = self._clean_text_for_speech(text)
            
        # try azure tts first for high quality speech
        if self.azure_tts and self.azure_tts.is_available():
            print("🎭 Using Azure TTS (high quality)")
            return self.azure_tts.speak(cleaned_text, voice, rate, pitch)
        
        # fallback to macos built-in tts
        print("🍎 Using macOS TTS (fallback)")
        voice = voice or config.voice_name
        rate = rate or config.voice_rate
        pitch = pitch or config.voice_pitch
        
        if self.system == "Darwin":  # macos
            return self._speak_macos(cleaned_text, voice, rate, pitch)
        else:
            # fallback for other operating systems
            print(f"TTS not supported on {self.system}")
            return False
    
    def stop_speaking(self):
        """Stop current speech immediately"""
        self.is_speaking = False
        
        # stop azure tts if speaking
        if self.azure_tts and self.azure_tts.get_speaking_status():
            self.azure_tts.stop_speaking()
        
        # stop macos speech if speaking
        if self.current_speech_process:
            try:
                self.current_speech_process.terminate()
                self.current_speech_process = None
            except:
                pass
        
        print("🔇 Speech stopped")
    
    def is_currently_speaking(self) -> bool:
        """Check if currently speaking"""
        return self.is_speaking
    
    def _speak_macos(self, text: str, voice: str, rate: float, pitch: float) -> bool:
        """Speak text using macOS 'say' command"""
        try:
            # build say command with parameters
            cmd = ["say"]
            
            # add voice parameter if specified
            if voice and voice in self.available_voices:
                cmd.extend(["-v", voice])
            
            # add speech rate parameter
            if rate:
                # convert rate to words per minute (0.5 = slow, 2.0 = fast)
                wpm = int(200 * rate)  # base 200 wpm
                cmd.extend(["-r", str(wpm)])
            
            # add text to speak
            cmd.append(text)
            
            # execute the say command asynchronously
            print(f"🗣️  Speaking: '{text}'")
            self.is_speaking = True
            self.current_speech_process = subprocess.Popen(cmd)
            
            # wait for completion
            self.current_speech_process.wait()
            self.is_speaking = False
            self.current_speech_process = None
            
            return True
            
        except Exception as e:
            print(f"Error speaking text: {e}")
            self.is_speaking = False
            self.current_speech_process = None
            return False
    

    
    def get_voice_info(self) -> dict:
        """Get information about current voice configuration"""
        return {
            "current_voice": config.voice_name,
            "current_rate": config.voice_rate,
            "current_pitch": config.voice_pitch,
            "available_voices": self.available_voices,
            "system": self.system
        }
    
    def list_voices(self):
        """List all available voices"""
        if not self.available_voices:
            print("No TTS voices available")
            return
        
        print("Available voices:")
        for i, voice in enumerate(self.available_voices, 1):
            print(f"  {i}. {voice}")
        
        print(f"\nCurrent voice: {config.voice_name}")
        print(f"Current rate: {config.voice_rate}")
        print(f"Current pitch: {config.voice_pitch}")

class TextOutputFallback:
    """Fallback text output when TTS isn't available"""
    
    @staticmethod
    def output(text: str):
        """Output text to console"""
        print(f"Nova: {text}")
