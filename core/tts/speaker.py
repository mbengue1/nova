"""
Text-to-Speech using macOS built-in voices
Provides natural speech output for Nova's responses
"""
import subprocess
import platform
import threading
import queue
import os
import re
import time
from typing import Optional
from config import config

# Import the new interruption monitor
try:
    from core.audio.interruption_monitor import InterruptionMonitor
except ImportError:
    print("⚠️ InterruptionMonitor not available - falling back to basic interruption detection")
    InterruptionMonitor = None

class SpeechSynthesizer:
    """Handles text-to-speech using macOS voices or Azure (if available)"""
    
    def __init__(self):
        self.system = platform.system()
        self.available_voices = self._get_available_voices()
        self.is_speaking = False
        self.current_speech_process = None
        self.interrupt_listener = None
        self.was_interrupted = False
        self.sample_rate = 16000  # Standard sample rate for audio processing
        
        # Queue-based approach for interruption
        self.audio_output_queue = queue.Queue()
        self.should_stop_speaking = threading.Event()
        
        # Initialize the dedicated interruption monitor if available
        self.interruption_monitor = None
        if InterruptionMonitor is not None:
            try:
                self.interruption_monitor = InterruptionMonitor(
                    sample_rate=self.sample_rate,
                    energy_threshold=0.012,  # Balanced sensitivity
                    min_duration_ms=40,      # Slightly longer to avoid false positives
                    consecutive_frames=2,    # Require 2 frames for better reliability
                    speech_validation_window=8  # Shorter window for faster validation
                )
            except Exception as e:
                print(f"⚠️ Failed to initialize interruption monitor: {e}")
                self.interruption_monitor = None
        
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
        
        # stop interruption monitor if active
        if self.interruption_monitor and hasattr(self.interruption_monitor, 'is_monitoring'):
            try:
                if self.interruption_monitor.is_monitoring:
                    self.interruption_monitor.stop_monitoring()
            except Exception as e:
                print(f"⚠️ Error stopping interruption monitor: {e}")
        
        print("🔇 Speech stopped")
    
    def cleanup(self):
        """Clean up all resources"""
        self.stop_speaking()
        
        # Clean up interruption monitor
        if self.interruption_monitor:
            try:
                if hasattr(self.interruption_monitor, 'stop_monitoring'):
                    self.interruption_monitor.stop_monitoring()
                if hasattr(self.interruption_monitor, 'cleanup'):
                    self.interruption_monitor.cleanup()
            except Exception as e:
                print(f"⚠️ Error cleaning up interruption monitor: {e}")
        
        # Clean up Azure TTS
        if self.azure_tts and hasattr(self.azure_tts, 'cleanup'):
            try:
                self.azure_tts.cleanup()
            except Exception as e:
                print(f"⚠️ Error cleaning up Azure TTS: {e}")
        
        print("🔇 TTS cleanup complete")
    
    def is_currently_speaking(self) -> bool:
        """Check if currently speaking"""
        return self.is_speaking
        
    def speak_with_interruption(self, text: str, stt, voice: str = None, rate: float = None, pitch: float = None) -> bool:
        """Speak text with interruption capability using dedicated interruption monitor
        
        Args:
            text: Text to speak
            stt: SpeechTranscriber instance for interruption detection (kept for backward compatibility)
            voice, rate, pitch: TTS parameters
            
        Returns:
            bool: True if speech completed, False if interrupted or failed
        """
        if not text.strip():
            return False
            
        # Stop any current speech before starting a new one
        if self.is_currently_speaking():
            self.stop_speaking()
        
        # Clean text for more natural speech
        cleaned_text = self._clean_text_for_speech(text)
        
        # Reset interruption flag
        self.was_interrupted = False
        
        # Define the interruption handler
        def on_interruption():
            print("🛑 INTERRUPTION DETECTED! Stopping speech immediately...")
            self.was_interrupted = True
            
            # Force immediate stop
            if self.azure_tts and self.azure_tts.is_available():
                self.azure_tts.stop_speaking()
            
            # Also call the general stop_speaking method
            self.stop_speaking()
            
        # Start the interruption monitor if available
        using_dedicated_monitor = False
        if self.interruption_monitor is not None:
            try:
                # Make sure to stop any existing monitor first for clean restart
                if self.interruption_monitor.is_monitoring:
                    self.interruption_monitor.stop_monitoring()
                    time.sleep(0.1)  # Small delay to ensure clean restart
                
                print("🎤 Starting dedicated interruption monitor...")
                if self.interruption_monitor.start_monitoring(on_interruption=on_interruption):
                    using_dedicated_monitor = True
                    print("✅ Dedicated interruption monitor active")
                else:
                    print("⚠️ Failed to start dedicated interruption monitor - falling back to legacy method")
            except Exception as e:
                print(f"⚠️ Error starting interruption monitor: {e} - falling back to legacy method")
                
        # If dedicated monitor failed, fall back to legacy method
        if not using_dedicated_monitor:
            # Start legacy interruption detection in a separate thread
            def legacy_interruption_listener():
                try:
                    print("👂 Using legacy interruption detection...")
                    
                    import numpy as np
                    import sounddevice as sd
                    
                    # Use a sliding window for energy detection
                    window_size = 10  # Number of frames to keep in history
                    energy_history = []
                    baseline_energy = None
                    
                    while self.is_speaking:
                        # Record a very short audio sample
                        duration = 0.05  # 50ms - extremely short for responsiveness
                        samples = int(self.sample_rate * duration)
                        recording = sd.rec(samples, samplerate=self.sample_rate, channels=1, dtype='int16')
                        sd.wait()
                        
                        # Convert to float and calculate energy
                        audio_float = recording.flatten().astype(np.float32) / 32768.0
                        energy = np.sqrt(np.mean(audio_float**2))
                        
                        # Add to history
                        energy_history.append(energy)
                        if len(energy_history) > window_size:
                            energy_history.pop(0)
                        
                        # Establish baseline if not yet set
                        if baseline_energy is None and len(energy_history) >= 5:
                            baseline_energy = sum(energy_history) / len(energy_history)
                            print(f"📊 Baseline energy: {baseline_energy:.6f}")
                        
                        # Check for significant energy increase over baseline
                        if baseline_energy is not None:
                            # Calculate current average
                            current_avg = sum(energy_history[-3:]) / 3 if len(energy_history) >= 3 else energy
                            
                            # If energy is significantly higher than baseline, consider it an interruption
                            if current_avg > baseline_energy * 2.5 or current_avg > 0.015:
                                print(f"🛑 INTERRUPTION DETECTED! Energy: {current_avg:.6f} (baseline: {baseline_energy:.6f})")
                                on_interruption()
                                break
                        
                        # Very short sleep for responsiveness
                        time.sleep(0.01)
                        
                except Exception as e:
                    print(f"Legacy interruption listener error: {e}")
            
            # Start the legacy interruption detection thread
            self.interrupt_listener = threading.Thread(target=legacy_interruption_listener, daemon=True)
            self.interrupt_listener.start()
        
        print("\n" + "="*60)
        print("🔊 INTERRUPTION DETECTION ACTIVE - speak anytime to interrupt Nova")
        print("🎤 Using " + ("dedicated" if using_dedicated_monitor else "legacy") + " interruption monitor")
        print("="*60 + "\n")
        
        # Speak the text
        self.is_speaking = True
        
        if self.azure_tts and self.azure_tts.is_available():
            result = self.azure_tts.speak(cleaned_text, voice, rate, pitch)
        else:
            result = self.speak(cleaned_text, voice, rate, pitch)
        
        # Stop the interruption monitor
        if using_dedicated_monitor:
            self.interruption_monitor.stop_monitoring()
        elif self.interrupt_listener:
            self.interrupt_listener.join(timeout=1.0)
            self.interrupt_listener = None
        
        self.is_speaking = False
        return result and not self.was_interrupted
    
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
