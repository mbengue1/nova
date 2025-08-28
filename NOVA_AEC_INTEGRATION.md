# Nova AEC Integration Plan

This document outlines the specific changes needed to integrate Acoustic Echo Cancellation (AEC) into Nova's existing architecture.

## Current Architecture

Nova's current audio pipeline:

1. **Audio Input**: Uses PyAudio to capture microphone input
2. **Wake Word Detection**: Processes audio frames for wake word detection
3. **Voice Activity Detection (VAD)**: Detects speech activity
4. **Speech Recognition**: Transcribes speech using Whisper
5. **Text-to-Speech (TTS)**: Generates speech using Azure TTS or macOS TTS
6. **Audio Output**: Plays TTS output using PyAudio or subprocess

## Integration Points

### 1. Core Audio Manager (`core/audio/audio_manager.py`)

Create a new audio manager class that will handle both input and output in a full-duplex mode:

```python
class NovaAudioManager:
    """Manages audio I/O with echo cancellation support"""
    
    def __init__(self, sample_rate=16000, channels=1, chunk_size=480):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size  # 30ms at 16kHz
        
        # For macOS, use AVAudioEngine with voice processing
        if platform.system() == "Darwin":
            self.audio_engine = MacOSAudioEngine(
                sample_rate=sample_rate,
                channels=channels,
                chunk_size=chunk_size
            )
        else:
            # For other platforms, use WebRTC APM with PyAudio
            self.audio_engine = WebRTCAudioEngine(
                sample_rate=sample_rate,
                channels=channels,
                chunk_size=chunk_size
            )
        
        # Audio queues for input/output
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        # Callbacks
        self.on_audio_input = None
        self.on_interruption = None
    
    def start(self):
        """Start the audio engine"""
        return self.audio_engine.start()
    
    def stop(self):
        """Stop the audio engine"""
        return self.audio_engine.stop()
    
    def add_to_output_queue(self, audio_data):
        """Add audio data to the output queue for playback"""
        self.output_queue.put(audio_data)
    
    def clear_output_queue(self):
        """Clear the output queue (for interruptions)"""
        with self.output_queue.mutex:
            self.output_queue.queue.clear()
    
    def set_on_audio_input(self, callback):
        """Set callback for audio input"""
        self.on_audio_input = callback
    
    def set_on_interruption(self, callback):
        """Set callback for interruption detection"""
        self.on_interruption = callback
```

### 2. macOS Audio Engine (`core/audio/macos_audio_engine.py`)

Implement the macOS-specific audio engine using AVAudioEngine:

```python
class MacOSAudioEngine:
    """macOS audio engine using AVAudioEngine with voice processing"""
    
    def __init__(self, sample_rate=16000, channels=1, chunk_size=480):
        # Import PyObjC components
        import objc
        import Foundation
        import AVFoundation
        from Foundation import NSObject, NSURL
        
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        
        # AVAudioEngine components
        self.audio_engine = None
        self.input_node = None
        self.output_node = None
        self.mixer_node = None
        
        # Audio session
        self.audio_session = None
        
        # Callbacks
        self.on_audio_input = None
        self.on_interruption = None
        
        # State
        self.is_running = False
        self.is_speaking = False
        self.energy_threshold = 0.02
        self.was_interrupted = False
        
        # For recording
        self.recorded_data = []
        self.should_record = False
    
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
            
            # Try to enable echo cancellation explicitly if available
            try:
                # Try different method names that might be available
                methods = [
                    'setPreferredInputWithAEC_',
                    'setPrefersEchoCancellation_',
                    'setAECEnabled_'
                ]
                
                for method in methods:
                    if hasattr(self.audio_session, method):
                        getattr(self.audio_session, method)(True)
                        print(f"Echo cancellation enabled with {method}")
                        break
            except Exception as e:
                print(f"Note: Could not explicitly enable echo cancellation: {e}")
                print("Echo cancellation is still enabled via VoiceChat mode")
            
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
                    
                    # Call the audio input callback if provided
                    if self.on_audio_input:
                        self.on_audio_input(audio_data)
                    
                    # Check for interruption
                    if self.is_running and not self.was_interrupted and len(audio_data) > 0:
                        # Calculate energy
                        energy = 0
                        for sample in audio_data:
                            energy += sample * sample
                        energy = (energy / len(audio_data)) ** 0.5
                        
                        if energy > self.energy_threshold:
                            print(f"🛑 Interruption detected! Energy: {energy:.6f}")
                            self.was_interrupted = True
                            if self.on_interruption:
                                self.on_interruption()
                except Exception as e:
                    print(f"❌ Error processing channel {channel}: {e}")
        
        except Exception as e:
            print(f"❌ Error processing audio buffer: {e}")
    
    def start(self):
        """Start the audio engine"""
        try:
            # Set up the audio session
            if not self.setup_audio_session():
                return False
                
            # Set up the audio engine
            if not self.setup_audio_engine():
                return False
                
            # Prepare the engine
            self.audio_engine.prepare()
            
            # Start the engine
            start_result = self.audio_engine.startAndReturnError_(None)
            
            if start_result:
                self.is_running = True
                self.should_record = True
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
            # Stop recording
            self.should_record = False
            
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
    
    def play_audio(self, audio_data):
        """Play audio data with interruption detection"""
        if not audio_data or len(audio_data) == 0:
            return False
            
        try:
            # Reset interruption state
            self.was_interrupted = False
            
            # Create a player node
            format = AVFoundation.AVAudioFormat.alloc().initWithCommonFormat_sampleRate_channels_interleaved_(
                AVFoundation.AVAudioCommonFormatPCMFloat32,
                self.sample_rate,
                self.channels,
                False
            )
            
            # Create a buffer with the audio data
            buffer = AVFoundation.AVAudioPCMBuffer.alloc().initWithPCMFormat_frameCapacity_(
                format,
                len(audio_data)
            )
            
            # Fill the buffer with the audio data
            for i in range(len(audio_data)):
                buffer.floatChannelData()[0][i] = audio_data[i]
            
            buffer.setFrameLength_(len(audio_data))
            
            # Create a player node
            player_node = self.audio_engine.attachPlayerNodeWithFormat_(format)
            
            # Connect the player to the mixer
            self.audio_engine.connect_to_format_(player_node, self.mixer_node, format)
            
            # Schedule the buffer for playback
            player_node.scheduleBuffer_completionHandler_(buffer, None)
            
            # Start playback
            player_node.play()
            
            # Wait for playback to complete or interruption
            import time
            while player_node.isPlaying() and not self.was_interrupted:
                time.sleep(0.01)
            
            # Disconnect the player
            self.audio_engine.disconnectNodeOutput_(player_node)
            self.audio_engine.detachNode_(player_node)
            
            return not self.was_interrupted
            
        except Exception as e:
            print(f"❌ Error during playback: {e}")
            return False
```

### 3. WebRTC Audio Engine (`core/audio/webrtc_audio_engine.py`)

Implement the cross-platform audio engine using WebRTC APM:

```python
class WebRTCAudioEngine:
    """Cross-platform audio engine using WebRTC APM"""
    
    def __init__(self, sample_rate=16000, channels=1, chunk_size=480):
        # Similar structure to MacOSAudioEngine but using WebRTC APM
        # This is a fallback for non-macOS platforms
```

### 4. TTS Integration (`core/tts/speaker.py`)

Update the TTS system to use the new audio manager:

```python
def speak_with_interruption(self, text, audio_manager, voice=None, rate=None, pitch=None):
    """Speak text with interruption capability using the audio manager"""
    
    if not text.strip():
        return False
    
    # Clean text for more natural speech
    cleaned_text = self._clean_text_for_speech(text)
    
    # Reset interruption flag
    self.was_interrupted = False
    
    # Generate speech audio data
    if self.azure_tts and self.azure_tts.is_available():
        audio_data = self.azure_tts.synthesize(cleaned_text, voice, rate, pitch)
    else:
        audio_data = self._synthesize_macos(cleaned_text, voice, rate, pitch)
    
    if not audio_data:
        return False
    
    # Stream the audio in chunks
    chunk_size = 480  # 30ms at 16kHz
    
    self.is_speaking = True
    
    # Set up interruption handler
    def on_interruption():
        self.was_interrupted = True
        self.is_speaking = False
        print("🛑 Speech interrupted")
    
    audio_manager.set_on_interruption(on_interruption)
    
    # Stream audio in chunks
    for i in range(0, len(audio_data), chunk_size):
        if not self.is_speaking or self.was_interrupted:
            break
        
        chunk = audio_data[i:i+chunk_size]
        audio_manager.add_to_output_queue(chunk)
        
        # Small sleep to allow for interruption
        time.sleep(0.001)
    
    self.is_speaking = False
    return not self.was_interrupted
```

### 5. Main Integration (`core/main.py`)

Update the main class to use the new audio manager:

```python
def __init__(self):
    # Other initialization...
    
    # Initialize the audio manager
    self.audio_manager = NovaAudioManager(
        sample_rate=16000,
        channels=1,
        chunk_size=480  # 30ms at 16kHz
    )
    
    # Set up audio input callback
    self.audio_manager.set_on_audio_input(self._on_audio_input)
    
    # Start the audio manager
    self.audio_manager.start()

def _on_audio_input(self, audio_data):
    """Handle audio input from the audio manager"""
    # Process for wake word detection, VAD, etc.
    
def _speak_with_fallback(self, text, allow_interruption=False):
    """Speak text with fallback and interruption support"""
    if allow_interruption:
        return self.tts.speak_with_interruption(text, self.audio_manager)
    else:
        return self.tts.speak(text)
```

## Implementation Sequence

1. **Create Audio Manager Classes**
   - Implement `NovaAudioManager`
   - Implement `MacOSAudioEngine`
   - (Optional) Implement `WebRTCAudioEngine`

2. **Update TTS Integration**
   - Modify `SpeechSynthesizer` to use the audio manager
   - Implement chunked streaming

3. **Update Main Class**
   - Replace direct audio input/output with audio manager
   - Update callbacks and processing

4. **Testing**
   - Test with the proof-of-concept script first
   - Integrate and test incrementally
   - Validate interruption detection works reliably

## Dependencies

- **PyObjC**: For interfacing with AVAudioEngine on macOS
- **WebRTC APM**: (Optional) For cross-platform echo cancellation

## Conclusion

This integration plan provides a roadmap for implementing proper echo cancellation in Nova. By focusing on macOS-specific capabilities first, we can leverage Apple's built-in voice processing for optimal results. The modular design allows for future expansion to other platforms using WebRTC APM.
