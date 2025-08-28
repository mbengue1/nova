# Acoustic Echo Cancellation (AEC) Implementation Plan for Nova

This document outlines the plan to implement proper barge-in capability for Nova using Acoustic Echo Cancellation (AEC) and related techniques.

## Core Problem

The current interruption detection doesn't work because Nova can't reliably hear the user while it's speaking. This is a fundamental issue in voice assistants that requires proper echo cancellation.

## Implementation Plan

### 1. Implement Acoustic Echo Cancellation (AEC)

#### For macOS (Primary Target)

1. **Use Apple's Voice Processing I/O**
   - Replace current audio input setup with AVAudioEngine's voice-processing mode
   - Configure AVAudioSession with `PlayAndRecord` category and voice-chat mode
   - Enable echo cancellation with `setPrefersEchoCancelledInput(true)`

2. **Implementation Steps**
   - Create a new `MacOSAudioManager` class that uses AVAudioEngine
   - Set up a single full-duplex audio stream for both input and output
   - Configure the session for voice processing:

```swift
// Swift code for reference (will need to be called from Python)
let audioSession = AVAudioSession.sharedInstance()
try audioSession.setCategory(.playAndRecord, 
                           options: [.defaultToSpeaker, .allowBluetooth])
try audioSession.setMode(.voiceChat)  // Enables echo cancellation
try audioSession.setPrefersEchoCancelledInput(true)
```

3. **Integration with Python**
   - Use PyObjC to interface with AVAudioEngine from Python
   - Alternatively, create a small Swift/Objective-C helper app that handles the audio I/O

#### Cross-Platform Alternative (Backup Plan)

1. **Use WebRTC Audio Processing Library**
   - Integrate WebRTC's Audio Processing Module (APM)
   - Feed TTS output to `ProcessReverseStream()`
   - Process microphone input with `ProcessStream()`

2. **Implementation Steps**
   - Add WebRTC APM as a dependency
   - Create wrapper functions for the APM interface
   - Set up the processing pipeline to handle both input and output streams

### 2. Redesign Audio I/O Architecture

1. **Create Full-Duplex Audio Stream**
   - Use a single audio device for both input and output
   - Ensure same sample rate and buffer configuration
   - Use small buffer sizes (e.g., 480 samples for 10ms @ 48kHz)

2. **Implementation Steps**
   - Refactor audio handling to use a single PyAudio stream in full-duplex mode:

```python
stream = p.open(
    format=pyaudio.paFloat32,
    channels=1,
    rate=sample_rate,
    input=True,
    output=True,
    frames_per_buffer=buffer_size,
    stream_callback=audio_callback
)
```

3. **Align Buffer Sizes and Timing**
   - Use consistent 10ms frames throughout the audio pipeline
   - Ensure buffer sizes are aligned between input and output
   - Minimize prebuffering to reduce latency

### 3. Implement Chunked TTS Streaming

1. **Stream TTS in Small Chunks**
   - Break TTS output into 20-40ms chunks
   - Add polling between chunks to check for interruptions
   - Implement immediate stop capability

2. **Implementation Steps**
   - Modify Azure TTS to request audio in smaller chunks
   - For macOS TTS, capture output and stream it in chunks
   - Add interruption check between each chunk:

```python
def stream_tts_with_interruption(audio_data, chunk_size_ms=30):
    chunk_samples = int(sample_rate * chunk_size_ms / 1000)
    
    for i in range(0, len(audio_data), chunk_samples):
        if interruption_detected():
            return False
            
        chunk = audio_data[i:i+chunk_samples]
        output_stream.write(chunk.tobytes())
        
        # Short sleep to allow for interruption checking
        time.sleep(0.001)
    
    return True
```

### 4. Optimize Detection Parameters

1. **Use 10ms Frames for Processing**
   - Configure VAD to use 10ms frames (standard for WebRTC)
   - Trigger on ~50ms of detected speech (5 consecutive frames)
   - Require ~200ms of silence to reset detection state

2. **Implementation Steps**
   - Update VAD configuration in `core/config.py`
   - Adjust frame sizes in audio processing pipeline
   - Tune detection thresholds for optimal performance

### 5. Implement Soft Barge-In as Fallback

1. **Add Temporary Soft Barge-In**
   - Initially duck (lower volume) TTS when potential speech is detected
   - Fully stop only when speech is confirmed
   - This helps bridge the gap until full AEC is working

2. **Implementation Steps**
   - Add volume control to TTS output
   - Implement ducking when energy rises above threshold
   - Stop completely if speech continues

## Implementation Sequence

1. **Phase 1: Audio Architecture Redesign**
   - Implement full-duplex audio stream
   - Align buffer sizes and timing
   - Test basic audio I/O functionality

2. **Phase 2: Echo Cancellation Integration**
   - Implement macOS Voice Processing I/O
   - Set up render reference path for AEC
   - Test echo cancellation effectiveness

3. **Phase 3: Chunked TTS and Interruption**
   - Implement chunked TTS streaming
   - Add interruption polling
   - Optimize detection parameters

4. **Phase 4: Testing and Refinement**
   - Test with various scenarios
   - Tune parameters for optimal performance
   - Implement fallbacks for edge cases

## Resources

- [Apple Voice Processing I/O Documentation](https://developer.apple.com/documentation/audiotoolbox/kaudiounitsubtype_voiceprocessingio)
- [WebRTC Audio Processing Module](https://chromium.googlesource.com/external/webrtc/+/lkgr/modules/audio_processing/include/audio_processing.h)
- [PortAudio Buffering and Latency Guidelines](https://github.com/PortAudio/portaudio/wiki/BufferingLatencyAndTimingImplementationGuidelines)
- [AVAudioSession PlayAndRecord Category](https://developer.apple.com/documentation/avfaudio/avaudiosession/category-swift.struct/playandrecord)

## Next Steps

1. Create a proof-of-concept implementation of macOS Voice Processing I/O
2. Test the effectiveness of echo cancellation with simple audio playback
3. Integrate the solution into Nova's audio pipeline
4. Refine and optimize based on testing results
