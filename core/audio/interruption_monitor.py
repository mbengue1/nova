"""
Interruption Monitor for Nova

This module provides robust speech detection for interruption handling:
1. Adaptive baseline energy detection
2. Consecutive frame tracking
3. Audio capture on interruption
4. Integration with Nova's transcription system

The interruption monitor runs in a separate thread and uses direct audio sampling
for reliable detection of user speech during TTS output.
"""
import threading
import time
import numpy as np
import sounddevice as sd
import wave
import os
from typing import Optional, Callable

class InterruptionMonitor:
    """Monitors audio input for interruptions with robust speech detection"""
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 energy_threshold: float = 0.02,
                 min_duration_ms: int = 60,
                 consecutive_frames: int = 2,
                 speech_validation_window: int = 10):
        """Initialize the interruption monitor
        
        Args:
            sample_rate: Audio sample rate (Hz)
            energy_threshold: Energy threshold for speech detection
            min_duration_ms: Minimum duration for detection (ms)
            consecutive_frames: Number of consecutive frames above threshold
            speech_validation_window: Number of frames to check for speech pattern
        """
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.min_duration_ms = min_duration_ms
        self.required_consecutive_frames = consecutive_frames
        self.speech_validation_window = speech_validation_window
        
        # For adaptive threshold
        self.min_energy_threshold = 0.008  # Lower minimum threshold for better sensitivity
        self.max_energy_threshold = 0.025  # Lower maximum to avoid requiring too loud speech
        self.adaptive_factor = 3.0         # Higher multiplier for better detection in quiet environments
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # Interruption state
        self.was_interrupted = False
        self.interruption_event = threading.Event()
        self.interruption_callback = None
        
        # For energy tracking
        self.energy_history = []
        self.consecutive_frames_above_threshold = 0
        self.baseline_energy = None
        
        # For audio capture
        self.audio_capture_duration = 4.0  # seconds - longer to capture more speech
        self.audio_pre_buffer_duration = 0.5  # seconds of audio to capture before interruption
        self.interruption_audio_file = None
        self.pre_buffer = []  # Store recent audio for pre-buffer
        self.continuous_capture = True  # Capture audio continuously during detection
        self.capture_buffer = []  # Buffer for continuous capture during detection
    
    def start_monitoring(self, on_interruption: Optional[Callable] = None) -> bool:
        """Start monitoring for interruptions
        
        Args:
            on_interruption: Callback function to call when interruption is detected
            
        Returns:
            bool: True if monitoring started successfully, False otherwise
        """
        if self.is_monitoring:
            print("⚠️ Interruption monitor already running")
            return False
        
        # Reset state
        self.was_interrupted = False
        self.interruption_event.clear()
        self.interruption_callback = on_interruption
        self.stop_event.clear()
        self.energy_history = []
        self.consecutive_frames_above_threshold = 0
        self.baseline_energy = None
        self.pre_buffer = []  # Clear pre-buffer
        self.in_detection_mode = False  # Reset detection mode
        self.capture_buffer = []  # Clear capture buffer
        
        # Start monitoring thread
        try:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_audio, daemon=True)
            self.monitor_thread.start()
            return True
        except Exception as e:
            print(f"❌ Failed to start interruption monitor: {e}")
            self.is_monitoring = False
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop monitoring for interruptions
        
        Returns:
            bool: True if monitoring stopped successfully, False otherwise
        """
        if not self.is_monitoring:
            return True
        
        try:
            # Signal the thread to stop
            self.stop_event.set()
            
            # Wait for the thread to finish with timeout
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=1.0)
                
            # Reset state even if thread doesn't respond to join
            self.is_monitoring = False
            self.was_interrupted = False
            self.interruption_event.clear()
            self.energy_history = []
            self.consecutive_frames_above_threshold = 0
            self.baseline_energy = None
            self.pre_buffer = []
            self.in_detection_mode = False
            self.capture_buffer = []
            
            # Create a new stop event (the old one might be in a bad state)
            self.stop_event = threading.Event()
            
            print("🔄 Interruption monitor reset and stopped")
            return True
        except Exception as e:
            print(f"❌ Error stopping interruption monitor: {e}")
            self.is_monitoring = False  # Force state to not monitoring even on error
            return False
    
    def _monitor_audio(self):
        """Monitor audio for interruptions in a separate thread"""
        try:
            # Initialize audio input stream
            with sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                blocksize=int(self.sample_rate * 0.05),  # 50ms blocks
                dtype='int16'
            ) as stream:
                print("👂 Direct monitoring for interruptions...")
                
                # Initialize energy tracking
                energy_history = []
                consecutive_frames = 0
                baseline = None
                
                while not self.stop_event.is_set():
                    try:
                        # Record a short audio sample
                        audio_data, overflowed = stream.read(stream.blocksize)
                        
                        # Convert to float and calculate energy
                        audio_float = audio_data.flatten().astype(np.float32) / 32768.0
                        energy = np.sqrt(np.mean(audio_float**2))
                        
                        # Store in pre-buffer for potential capture
                        self.pre_buffer.append(audio_float.copy())
                        
                        # Keep pre-buffer at appropriate size
                        pre_buffer_size = int(self.audio_pre_buffer_duration / 0.05)  # 50ms blocks
                        while len(self.pre_buffer) > pre_buffer_size:
                            self.pre_buffer.pop(0)
                            
                        # Also store in continuous capture buffer if we're in detection mode
                        if hasattr(self, 'in_detection_mode') and self.in_detection_mode:
                            self.capture_buffer.append(audio_float.copy())
                        
                        # Add to history
                        energy_history.append(energy)
                        if len(energy_history) > 20:
                            energy_history.pop(0)
                        
                        # Establish baseline if not yet set
                        if baseline is None and len(energy_history) >= 10:
                            baseline = sum(energy_history) / len(energy_history)
                            print(f"📊 Baseline energy established: {baseline:.6f}")
                            
                            # Set adaptive threshold relative to baseline with limits
                            threshold = max(
                                self.min_energy_threshold, 
                                min(self.max_energy_threshold, baseline * self.adaptive_factor)
                            )
                            print(f"📊 Energy threshold set to: {threshold:.6f} (adaptive)")
                        
                        # Check for interruption
                        if baseline is not None:
                            # Visualize energy level
                            bar_length = int(min(80, max(0, energy * 80 / 0.1)))
                            bar = '|' + '█' * bar_length + '|'
                            
                            # Keep track of recent energy values for pattern detection
                            if not hasattr(self, 'recent_energies'):
                                self.recent_energies = []
                            
                            self.recent_energies.append(energy)
                            if len(self.recent_energies) > self.speech_validation_window:
                                self.recent_energies.pop(0)
                            
                            if energy > threshold:
                                consecutive_frames += 1
                                print(f"⚡ Energy spike: {energy:.6f} (threshold: {threshold:.6f}, consecutive: {consecutive_frames})")
                                
                                # Start continuous capture mode on first energy spike
                                if consecutive_frames == 1:
                                    self.in_detection_mode = True
                                    self.capture_buffer = []  # Clear previous capture buffer
                                    print("🎤 Starting continuous audio capture...")
                            else:
                                consecutive_frames = 0
                                
                                # If we were in detection mode but energy dropped, keep capturing for a bit
                                if hasattr(self, 'in_detection_mode') and self.in_detection_mode:
                                    # Keep capturing for a short time after energy drops
                                    pass
                            
                            # Only trigger after multiple consecutive frames AND validate speech pattern
                            if consecutive_frames >= self.required_consecutive_frames:
                                # Check if energy pattern looks like speech (has variations)
                                if self._validate_speech_pattern():
                                    print(f"🛑 SPEECH INTERRUPTION DETECTED! Energy: {energy:.6f}")
                                    self.was_interrupted = True
                                    self.interruption_event.set()
                                    
                                    # Use the already captured audio from continuous capture
                                    if self.continuous_capture and hasattr(self, 'in_detection_mode') and self.in_detection_mode:
                                        print(f"📊 Using {len(self.capture_buffer)} frames of already captured audio")
                                        self._save_captured_audio()
                                    else:
                                        # Fall back to traditional capture if continuous capture is disabled
                                        self.capture_interruption_audio()
                                    
                                    # Call the interruption callback if provided
                                    if self.interruption_callback:
                                        self.interruption_callback()
                                    
                                    break
                                else:
                                    print(f"⚠️ Energy spike detected but doesn't match speech pattern")
                                    consecutive_frames = 0
                                    # Reset detection mode
                                    if hasattr(self, 'in_detection_mode'):
                                        self.in_detection_mode = False
                    except Exception as e:
                        print(f"Error in audio monitoring: {e}")
                    
                    time.sleep(0.01)  # Short sleep for CPU efficiency
        except Exception as e:
            print(f"❌ Error in interruption monitor: {e}")
    
    def capture_interruption_audio(self) -> Optional[str]:
        """Capture audio after interruption is detected
        
        Returns:
            str: Path to the captured audio file, or None if capture failed
        """
        try:
            print(f"🎤 Capturing {self.audio_capture_duration} seconds of audio after interruption...")
            
            # Create a timestamped filename in the current directory
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            self.interruption_audio_file = f"interruption_{timestamp}.wav"
            
            # Include pre-buffer audio if available
            pre_buffer_audio = np.concatenate(self.pre_buffer) if self.pre_buffer else np.array([])
            
            # Record additional audio
            samples = int(self.sample_rate * self.audio_capture_duration)
            recording = sd.rec(samples, samplerate=self.sample_rate, channels=1, dtype='int16')
            
            # Wait for recording to complete
            sd.wait()
            
            # Convert to float for processing
            new_audio_float = recording.flatten().astype(np.float32) / 32768.0
            
            # Combine pre-buffer and new recording
            audio_float = np.concatenate([pre_buffer_audio, new_audio_float]) if len(pre_buffer_audio) > 0 else new_audio_float
            
            # Print info about the captured audio
            total_duration = len(audio_float) / self.sample_rate
            print(f"📊 Captured {total_duration:.2f}s of audio ({len(pre_buffer_audio)/self.sample_rate:.2f}s pre-buffer)")
            
            # Save to WAV file
            with wave.open(self.interruption_audio_file, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 2 bytes for int16
                wf.setframerate(self.sample_rate)
                wf.writeframes((audio_float * 32767).astype(np.int16).tobytes())
            
            print(f"\n🎙️ INTERRUPTION AUDIO CAPTURED!")
            print(f"✅ Interruption audio saved to: {self.interruption_audio_file}")
            
            return self.interruption_audio_file
        except Exception as e:
            print(f"❌ Error capturing interruption audio: {e}")
            return None
    
    def _validate_speech_pattern(self) -> bool:
        """Validate that the energy pattern looks like speech
        
        Human speech typically has variations in energy levels due to syllables,
        while consistent noise (like wind or fan) has more uniform energy.
        
        Returns:
            bool: True if the pattern looks like speech, False otherwise
        """
        if not hasattr(self, 'recent_energies') or len(self.recent_energies) < 5:
            return True  # Not enough data to validate, assume it's valid
        
        # Calculate variance in energy levels
        mean_energy = sum(self.recent_energies) / len(self.recent_energies)
        variance = sum((e - mean_energy) ** 2 for e in self.recent_energies) / len(self.recent_energies)
        
        # Calculate rate of change between consecutive energy values
        changes = [abs(self.recent_energies[i] - self.recent_energies[i-1]) 
                  for i in range(1, len(self.recent_energies))]
        avg_change = sum(changes) / len(changes) if changes else 0
        
        # Speech typically has higher variance and changes between frames
        # These thresholds have been tuned based on testing
        min_variance = 0.00003  # Lower minimum variance for better sensitivity
        min_avg_change = 0.0015  # Lower minimum change for better detection
        
        is_speech = variance > min_variance or avg_change > min_avg_change
        
        if is_speech:
            print(f"✅ Energy pattern validated as speech (variance: {variance:.6f}, avg_change: {avg_change:.6f})")
        else:
            print(f"❌ Energy pattern rejected (variance: {variance:.6f}, avg_change: {avg_change:.6f})")
            
        return is_speech
    
    def _save_captured_audio(self) -> Optional[str]:
        """Save the continuously captured audio to a file
        
        Returns:
            str: Path to the saved audio file, or None if saving failed
        """
        try:
            print(f"🎤 Saving continuously captured audio ({len(self.capture_buffer)} frames)...")
            
            # Create a timestamped filename in the current directory
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            self.interruption_audio_file = f"interruption_{timestamp}.wav"
            
            # Combine pre-buffer and captured audio
            combined_audio = np.concatenate(self.pre_buffer + self.capture_buffer) if self.pre_buffer else np.concatenate(self.capture_buffer)
            
            # Continue capturing for a short additional time
            additional_duration = 2.0  # seconds
            additional_samples = int(self.sample_rate * additional_duration)
            print(f"🎤 Capturing additional {additional_duration:.1f} seconds of audio...")
            
            # Record additional audio
            recording = sd.rec(additional_samples, samplerate=self.sample_rate, channels=1, dtype='int16')
            sd.wait()
            
            # Convert to float and append
            additional_audio = recording.flatten().astype(np.float32) / 32768.0
            
            # Combine all audio
            audio_float = np.concatenate([combined_audio, additional_audio])
            
            # Print info about the captured audio
            total_duration = len(audio_float) / self.sample_rate
            pre_buffer_duration = len(self.pre_buffer) * 0.05  # 50ms blocks
            print(f"📊 Captured {total_duration:.2f}s of audio ({pre_buffer_duration:.2f}s pre-buffer)")
            
            # Save to WAV file
            with wave.open(self.interruption_audio_file, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 2 bytes for int16
                wf.setframerate(self.sample_rate)
                wf.writeframes((audio_float * 32767).astype(np.int16).tobytes())
            
            print(f"\n🎙️ INTERRUPTION AUDIO CAPTURED!")
            print(f"✅ Interruption audio saved to: {self.interruption_audio_file}")
            
            # Reset continuous capture mode
            self.in_detection_mode = False
            self.capture_buffer = []
            
            return self.interruption_audio_file
        except Exception as e:
            print(f"❌ Error saving captured audio: {e}")
            return None
    
    def get_interruption_audio_file(self) -> Optional[str]:
        """Get the path to the most recently captured interruption audio file
        
        Returns:
            str: Path to the audio file, or None if no file was captured
        """
        return self.interruption_audio_file if os.path.exists(self.interruption_audio_file or "") else None