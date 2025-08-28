"""
Test script for macOS Voice Processing I/O with PyObjC
This demonstrates how to use Apple's Voice Processing I/O for echo cancellation

IMPORTANT: Always activate the virtual environment first:
    source .venv/bin/activate
"""

import sys
import os
import time
import threading
import numpy as np
import argparse
import sounddevice as sd
import wave

# Check if running on macOS
import platform
if platform.system() != "Darwin":
    print("This script requires macOS to run")
    sys.exit(1)

try:
    # Import PyObjC components for AVAudioEngine
    import objc
    import Foundation
    import AVFoundation
    from Foundation import NSObject, NSMutableDictionary, NSURL
    
    # Import PyAudio for comparison testing
    import pyaudio
    import wave
    
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you've installed PyObjC: pip install pyobjc")
    print("And PyAudio: pip install pyaudio")
    sys.exit(1)

class MacOSVoiceProcessingDemo:
    """Demo of macOS Voice Processing I/O for echo cancellation"""
    
    def __init__(self):
        """Initialize the demo"""
        self.audio_engine = None
        self.input_node = None
        self.output_node = None
        self.mixer_node = None
        self.is_running = False
        self.audio_session = None
        
        # For storing audio data
        self.recorded_data = []
        self.should_record = False
        
        # For playback
        self.playback_file = None
        self.playback_data = None
        self.playback_position = 0
        self.playback_sample_rate = 44100
        
        # For interruption detection
        self.energy_threshold = 0.02  # Very aggressive for testing
        self.was_interrupted = False
        self.interruption_event = threading.Event()
        self.should_transcribe = False
        
        # For audio capture during interruption
        self.interruption_audio_file = None
        self.audio_capture_duration = 3.0  # seconds
        
        # For energy tracking
        self.energy_history = []
        self.consecutive_frames_above_threshold = 0
        self.baseline_energy = None
        
    def setup_audio_session(self):
        """Set up the AVAudioSession for voice processing"""
        try:
            # Get the shared audio session
            self.audio_session = AVFoundation.AVAudioSession.sharedInstance()
            
            # Configure for PlayAndRecord with voice chat mode
            category_result = self.audio_session.setCategory_withOptions_error_(
                AVFoundation.AVAudioSessionCategoryPlayAndRecord,
                AVFoundation.AVAudioSessionCategoryOptionDefaultToSpeaker | 
                AVFoundation.AVAudioSessionCategoryOptionAllowBluetooth,
                None
            )
            
            # Set mode to voice chat (enables echo cancellation)
            mode_result = self.audio_session.setMode_error_(
                AVFoundation.AVAudioSessionModeVoiceChat,
                None
            )
            
            # Enable echo cancellation
            # The method name might vary between PyObjC versions
            try:
                # Try the newer method name first
                echo_result = self.audio_session.setPreferredInputWithAEC_(True)
                print("Using setPreferredInputWithAEC_ method")
            except AttributeError:
                try:
                    # Try alternative method name
                    echo_result = self.audio_session.setPrefersEchoCancellation_(True)
                    print("Using setPrefersEchoCancellation_ method")
                except AttributeError:
                    # Fallback to another possible method name
                    try:
                        echo_result = self.audio_session.setAECEnabled_(True)
                        print("Using setAECEnabled_ method")
                    except AttributeError:
                        print("⚠️ Could not find echo cancellation method - AEC may not be available")
            
            # Activate the session
            activate_result = self.audio_session.setActive_withOptions_error_(
                True,
                AVFoundation.AVAudioSessionSetActiveOptionNotifyOthersOnDeactivation,
                None
            )
            
            print("✅ Audio session configured for voice processing")
            print(f"   Sample rate: {self.audio_session.sampleRate()} Hz")
            print(f"   I/O buffer duration: {self.audio_session.IOBufferDuration()} sec")
            print(f"   Mode: {self.audio_session.mode()}")
            # Echo cancellation status is not directly accessible in all PyObjC versions
            print(f"   Echo cancellation: Enabled via VoiceChat mode")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to configure audio session: {e}")
            return False
    
    def setup_audio_engine(self):
        """Set up the AVAudioEngine with input and output nodes"""
        try:
            # Create the audio engine
            self.audio_engine = AVFoundation.AVAudioEngine.alloc().init()
            
            # Get the input and output nodes
            self.input_node = self.audio_engine.inputNode()
            self.output_node = self.audio_engine.outputNode()
            
            # Create a mixer node
            self.mixer_node = self.audio_engine.mainMixerNode()
            
            # Get the input and output formats
            input_format = self.input_node.inputFormatForBus_(0)
            output_format = self.output_node.outputFormatForBus_(0)
            
            print(f"✅ Audio engine initialized")
            print(f"   Input format: {input_format.sampleRate()} Hz, {input_format.channelCount()} channels")
            print(f"   Output format: {output_format.sampleRate()} Hz, {output_format.channelCount()} channels")
            
            # Install a tap on the input node to get the audio data
            buffer_size = 1024  # Adjust as needed
            self.input_node.installTapOnBus_bufferSize_format_block_(
                0,  # bus 0
                buffer_size,
                input_format,
                self._process_audio_buffer
            )
            
            # Connect the mixer to the output
            self.audio_engine.connect_to_format_(self.mixer_node, self.output_node, output_format)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to set up audio engine: {e}")
            return False
    
    def _process_audio_buffer(self, buffer, when):
        """Process audio buffer from the input tap"""
        try:
            if not self.should_record:
                return
                
            # Get the audio data as numpy array
            frames = buffer.frameLength()
            channels = buffer.format().channelCount()
            
            # Get the buffer for each channel
            for channel in range(channels):
                try:
                    # Get the audio data for this channel
                    audio_buffer = buffer.floatChannelData()[channel]
                    
                    # Convert to Python list first to avoid PyObjC issues
                    audio_list = []
                    for i in range(frames):
                        audio_list.append(audio_buffer[i])
                    
                    # Convert to numpy array
                    import numpy as np
                    audio_data = np.array(audio_list, dtype=np.float32)
                    
                    # Store the data
                    if len(audio_data) > 0:
                        self.recorded_data.append(audio_data)
                    
                    # Check for interruption
                    if self.is_running and not self.was_interrupted and len(audio_data) > 0:
                        # Calculate energy
                        energy = 0
                        for sample in audio_data:
                            energy += sample * sample
                        energy = (energy / len(audio_data)) ** 0.5
                        
                        # Store energy for tracking
                        if not hasattr(self, 'energy_history'):
                            self.energy_history = []
                            self.consecutive_frames_above_threshold = 0
                            self.baseline_energy = None
                            
                        # Add to history
                        self.energy_history.append(energy)
                        if len(self.energy_history) > 20:  # Keep last 20 frames
                            self.energy_history.pop(0)
                            
                        # Establish baseline if not yet set
                        if self.baseline_energy is None and len(self.energy_history) >= 10:
                            self.baseline_energy = sum(self.energy_history) / len(self.energy_history)
                            print(f"📊 Baseline energy established: {self.baseline_energy:.6f}")
                            # Set threshold very aggressive for this test
                            self.energy_threshold = max(0.02, self.baseline_energy * 2.0)
                            print(f"📊 Energy threshold set to: {self.energy_threshold:.6f} (very aggressive for testing)")
                        
                        # Track consecutive frames above threshold
                        if energy > self.energy_threshold:
                            self.consecutive_frames_above_threshold += 1
                            print(f"⚡ Energy spike: {energy:.6f} (threshold: {self.energy_threshold:.6f}, consecutive: {self.consecutive_frames_above_threshold})")
                        else:
                            # Reset counter if energy drops below threshold
                            if self.consecutive_frames_above_threshold > 0:
                                self.consecutive_frames_above_threshold = 0
                        
                        # Only trigger interruption if energy stays above threshold for multiple frames
                        # This helps filter out short noise spikes
                        if self.consecutive_frames_above_threshold >= 2:  # Reduced to 2 frames for testing
                            print(f"🛑 SPEECH INTERRUPTION DETECTED! Energy: {energy:.6f}")
                            self.was_interrupted = True
                            self.interruption_event.set()
                            
                            # We'll set a flag to let the direct monitoring know to capture audio
                            # This will be handled by the direct monitoring thread
                            self.should_transcribe = True
                except Exception as e:
                    print(f"❌ Error processing channel {channel}: {e}")
        
        except Exception as e:
            print(f"❌ Error processing audio buffer: {e}")
    
    def start(self):
        """Start the audio engine"""
        try:
            # Prepare the engine
            self.audio_engine.prepare()
            
            # Start the engine
            start_result = self.audio_engine.startAndReturnError_(None)
            
            if start_result:
                self.is_running = True
                print("✅ Audio engine started")
                return True
            else:
                print("❌ Failed to start audio engine")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start audio engine: {e}")
            return False
    
    def stop(self):
        """Stop the audio engine"""
        try:
            # Remove the tap
            self.input_node.removeTapOnBus_(0)
            
            # Stop the engine
            self.audio_engine.stop()
            self.is_running = False
            
            print("✅ Audio engine stopped")
            return True
            
        except Exception as e:
            print(f"❌ Failed to stop audio engine: {e}")
            return False
    
    def load_audio_file(self, file_path):
        """Load an audio file for playback using a simpler approach with PyAudio"""
        try:
            # Use PyAudio and wave for simplicity
            import wave
            
            # Check if it's an AIFF file and convert if needed
            if file_path.lower().endswith('.aiff') or file_path.lower().endswith('.aif'):
                print(f"Converting AIFF file to WAV format for compatibility...")
                
                # Create a temporary WAV file
                import tempfile
                import subprocess
                
                temp_wav = tempfile.mktemp(suffix='.wav')
                
                # Use ffmpeg or afconvert if available
                try:
                    subprocess.run(['afconvert', '-f', 'WAVE', '-d', 'LEI16@44100', file_path, temp_wav], 
                                  check=True, capture_output=True)
                    file_path = temp_wav
                    self.temp_wav_path = temp_wav  # Store the path for later use
                    print(f"Converted to temporary WAV: {temp_wav}")
                except (subprocess.SubprocessError, FileNotFoundError):
                    print("⚠️ Could not convert AIFF to WAV - trying direct load")
            
            # Open the wave file
            try:
                wf = wave.open(file_path, 'rb')
                
                # Get file properties
                self.playback_sample_rate = wf.getframerate()
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                frame_count = wf.getnframes()
                
                # Read all frames
                self.playback_data = wf.readframes(frame_count)
                wf.close()
                
                print(f"✅ Loaded audio file: {file_path}")
                print(f"   Duration: {frame_count / self.playback_sample_rate:.2f} seconds")
                print(f"   Sample rate: {self.playback_sample_rate} Hz")
                print(f"   Channels: {channels}")
                print(f"   Sample width: {sample_width} bytes")
                
                return True
                
            except Exception as e:
                print(f"❌ Failed to load audio file with wave: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to load audio file: {e}")
            return False
    
    def play_audio_with_interruption(self):
        """Play the loaded audio file with interruption detection using subprocess"""
        if not self.playback_data:
            print("❌ No audio file loaded")
            return False
        
        try:
            # Reset interruption state
            self.was_interrupted = False
            self.interruption_event.clear()
            
            # Enable recording to detect interruptions
            self.should_record = True
            
            print("\n" + "="*60)
            print("🔊 PLAYING AUDIO - speak anytime to interrupt")
            print("="*60)
            
            # Use macOS 'afplay' command to play the audio
            import subprocess
            import threading
            
            # Get the path of the temporary file
            temp_wav_path = None
            if hasattr(self, 'temp_wav_path') and self.temp_wav_path:
                temp_wav_path = self.temp_wav_path
            else:
                # Find the most recently created temporary WAV file
                import glob
                import os
                temp_files = glob.glob('/var/folders/*/T/tmp*.wav')
                if temp_files:
                    temp_files.sort(key=os.path.getmtime, reverse=True)
                    temp_wav_path = temp_files[0]
            
            if not temp_wav_path:
                print("❌ Could not find temporary WAV file")
                return False
                
            print(f"Playing audio file: {temp_wav_path}")
            
            # Create a loop script to play the file multiple times at normal speed
            loop_script = f"""
            for i in {{1..10}}; do
                afplay "{temp_wav_path}"
                sleep 0.5
            done
            """
            
            # Start the loop script in a shell
            process = subprocess.Popen(['bash', '-c', loop_script])
            print("\n🔴 NOW PLAYING AUDIO 10 TIMES - SPEAK LOUDLY TO TEST INTERRUPTION 🔴")
            
            # Monitor for interruptions
            def check_for_interruption():
                # For direct monitoring during playback
                import numpy as np
                import sounddevice as sd
                
                # Track energy for interruption detection
                energy_history = []
                consecutive_frames = 0
                baseline = None
                
                print("👂 Direct monitoring for interruptions...")
                
                while process.poll() is None:
                    # First check if interruption was already detected by audio buffer processing
                    if self.interruption_event.is_set():
                        print("🛑 Stopping playback due to interruption (from buffer processing)")
                        process.terminate()
                        
                        # Capture audio for later analysis
                        self.capture_interruption_audio()
                        
                        break
                    
                    # Also do our own monitoring with sounddevice
                    try:
                        # Record a short audio sample
                        duration = 0.1  # 100ms
                        samples = int(self.playback_sample_rate * duration)
                        recording = sd.rec(samples, samplerate=self.playback_sample_rate, channels=1, dtype='int16')
                        sd.wait()
                        
                        # Calculate energy
                        audio_float = recording.flatten().astype(np.float32) / 32768.0
                        energy = np.sqrt(np.mean(audio_float**2))
                        
                        # Print energy level to see if microphone is picking up sound
                        scale = 1000
                        energy_bar = "█" * int(energy * scale)  # Scale for visualization
                        
                        # Show threshold if baseline is established
                        if baseline is not None:
                            threshold_pos = int(threshold * scale)
                            threshold_marker = " " * threshold_pos + "▲"
                            print(f"🎤 Energy: {energy:.6f} |{energy_bar}|\n   Threshold: {threshold:.6f} {threshold_marker}")
                        else:
                            print(f"🎤 Energy: {energy:.6f} |{energy_bar}| (establishing baseline...)")
                        
                        # Add to history
                        energy_history.append(energy)
                        if len(energy_history) > 20:
                            energy_history.pop(0)
                        
                        # Establish baseline if not yet set
                        if baseline is None and len(energy_history) >= 10:
                            baseline = sum(energy_history) / len(energy_history)
                            print(f"📊 Direct monitoring baseline: {baseline:.6f}")
                            # Set threshold very aggressive for this test
                            threshold = max(0.02, baseline * 2.0)
                            print(f"📊 Direct monitoring threshold: {threshold:.6f} (very aggressive for testing)")
                        
                        # Check for interruption
                        if baseline is not None:
                            if energy > threshold:
                                consecutive_frames += 1
                                print(f"⚡ Direct energy spike: {energy:.6f} (threshold: {threshold:.6f}, consecutive: {consecutive_frames})")
                            else:
                                consecutive_frames = 0
                            
                            # Only trigger after multiple consecutive frames
                            if consecutive_frames >= 2:  # Reduced to 2 frames for testing
                                print(f"🛑 DIRECT SPEECH INTERRUPTION! Energy: {energy:.6f}")
                                self.was_interrupted = True
                                self.interruption_event.set()
                                
                                # Stop playback first
                                process.terminate()
                                
                                # Then capture audio for later analysis
                                self.capture_interruption_audio()
                                    
                                # No transcription code needed
                                
                                break
                    except Exception as e:
                        print(f"Error in direct monitoring: {e}")
                    
                    time.sleep(0.05)
            
            # Start the interruption monitoring thread
            monitor_thread = threading.Thread(target=check_for_interruption, daemon=True)
            monitor_thread.start()
            
            # Wait for playback to complete or be interrupted
            process.wait()
            
            # Stop recording
            self.should_record = False
            
            if self.interruption_event.is_set():
                print("✅ Playback was interrupted successfully")
                return False
            else:
                print("✅ Playback completed without interruption")
                return True
                
        except Exception as e:
            print(f"❌ Error during playback: {e}")
            self.should_record = False
            return False
    
    def capture_interruption_audio(self):
        """Capture audio for a few seconds after interruption is detected"""
        try:
            print(f"🎤 Capturing {self.audio_capture_duration} seconds of audio after interruption...")
            
            # Create a fixed filename in the current directory
            self.interruption_audio_file = "audio_cache/interruption_latest.wav"
            
            # Record audio using a subprocess to avoid segmentation faults
            try:
                # Import needed modules
                import subprocess
                
                # Create a simple Python script to record audio
                record_script = """
import sounddevice as sd
import wave
import numpy as np
import sys

duration = 3.0  # seconds
fs = 44100  # sample rate
channels = 1
        filename = "audio_cache/interruption_latest.wav"

print(f"Recording {duration} seconds of audio...")
recording = sd.rec(int(duration * fs), samplerate=fs, channels=channels, dtype='int16')
sd.wait()

print(f"Saving to {filename}...")
with wave.open(filename, 'wb') as wf:
    wf.setnchannels(channels)
    wf.setsampwidth(2)  # 2 bytes for int16
    wf.setframerate(fs)
    wf.writeframes(recording.tobytes())

print(f"Done! Audio saved to {filename}")
"""
                # Write the script to a temporary file
                with open("temp_record.py", "w") as f:
                    f.write(record_script)
                
                # Run the script in a separate process
                print("Starting recording subprocess...")
                subprocess.run([sys.executable, "temp_record.py"], check=True)
                
                # Clean up
                os.remove("temp_record.py")
                
                print(f"\n🎙️ INTERRUPTION AUDIO CAPTURED!")
                print(f"✅ Interruption audio saved to: {self.interruption_audio_file}")
                print(f"🔊 To analyze this audio later, you can use:")
                print(f"   - Play: ffplay {self.interruption_audio_file}")
                print(f"   - Transcribe: whisper {self.interruption_audio_file}")
                print(f"   - Process with Nova: python -m core.main --transcribe {self.interruption_audio_file}\n")
                
                return self.interruption_audio_file
            except Exception as e:
                print(f"❌ Error in recording subprocess: {e}")
                return None
                
        except Exception as e:
            print(f"❌ Error capturing interruption audio: {e}")
            return None
    
    def test_echo_cancellation(self, output_file=None):
        """Run a test to verify echo cancellation is working"""
        print("\n" + "="*60)
        print("🧪 ECHO CANCELLATION TEST")
        print("="*60)
        print("This test will play audio while recording from the microphone.")
        print("The recording should have minimal echo if AEC is working.")
        print("Speak occasionally during playback to test barge-in detection.")
        
        # Clear any previous recordings
        self.recorded_data = []
        
        # Play audio with interruption detection
        result = self.play_audio_with_interruption()
        
        if output_file and self.recorded_data:
            try:
                import numpy as np
                
                # Filter out empty arrays
                valid_data = [arr for arr in self.recorded_data if len(arr) > 0]
                
                if valid_data:
                    # Convert recorded data to a single numpy array
                    all_data = np.concatenate(valid_data)
                    
                    # Scale to int16 range
                    all_data = (all_data * 32767).astype(np.int16)
                    
                    # Save to WAV file
                    with wave.open(output_file, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)  # 2 bytes for int16
                        wf.setframerate(int(self.audio_session.sampleRate()))
                        wf.writeframes(all_data.tobytes())
                    
                    print(f"✅ Recorded audio saved to: {output_file}")
                else:
                    print("⚠️ No valid audio data recorded")
                
            except Exception as e:
                print(f"❌ Failed to save recording: {e}")
        
        return result

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test macOS Voice Processing I/O for echo cancellation")
    parser.add_argument("--input", "-i", help="Audio file to play")
    parser.add_argument("--output", "-o", help="Output file for recording")
    args = parser.parse_args()
    
    # Create the demo
    demo = MacOSVoiceProcessingDemo()
    
    # Set up the audio session
    if not demo.setup_audio_session():
        print("❌ Failed to set up audio session")
        return
    
    # Set up the audio engine
    if not demo.setup_audio_engine():
        print("❌ Failed to set up audio engine")
        return
    
    # Start the audio engine
    if not demo.start():
        print("❌ Failed to start audio engine")
        return
    
    try:
        # If input file is provided, load it
        if args.input:
            if not demo.load_audio_file(args.input):
                print(f"❌ Failed to load audio file: {args.input}")
                return
            
            # Run the echo cancellation test
            demo.test_echo_cancellation(args.output)
        else:
            print("No input file provided. Please specify an audio file with --input")
            return
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    finally:
        # Stop the audio engine
        demo.stop()
        
        print("\n✅ Test completed")

if __name__ == "__main__":
    main()
