# Interruption Capability: Next Steps

## What We've Learned

Based on our research and testing, we've identified that proper barge-in capability requires:

1. **Acoustic Echo Cancellation (AEC)** - The system needs to be able to hear the user while it's speaking, which requires echo cancellation to filter out its own output from the input.

2. **Full-Duplex Audio** - A single audio stream that handles both input and output simultaneously, with aligned sample rates and buffer sizes.

3. **Chunked TTS Streaming** - Breaking TTS output into small chunks (20-40ms) with interruption checks between chunks.

4. **10ms Frame Processing** - Using standard 10ms frames for audio processing, which is the standard for WebRTC and voice applications.

## What We've Created

1. **Documentation**:
   - `AEC_IMPLEMENTATION_PLAN.md` - Detailed plan for implementing AEC
   - `NOVA_AEC_INTEGRATION.md` - Specific integration points for Nova
   - `INTERRUPTION_STATUS.md` - Current status and known issues

2. **Test Scripts**:
   - `scripts/test_interruption.py` - For testing interruption detection
   - `scripts/test_macos_voice_processing.py` - For testing macOS Voice Processing I/O

3. **Implementation Approach**:
   - macOS-specific approach using AVAudioEngine with Voice Processing I/O
   - Cross-platform fallback using WebRTC Audio Processing Module

## Next Steps

### 1. Proof of Concept Testing

Before integrating into Nova, test the macOS Voice Processing I/O approach:

```bash
# Activate the virtual environment first
source .venv/bin/activate

# Install PyObjC if not already installed
pip install pyobjc

# Run the test script with an audio file
python scripts/test_macos_voice_processing.py --input /path/to/audio.wav --output recording.wav
```

### 2. Core Audio Manager Implementation

1. Create the `NovaAudioManager` class as outlined in `NOVA_AEC_INTEGRATION.md`
2. Implement the macOS-specific `MacOSAudioEngine` class
3. Test basic audio I/O functionality

### 3. TTS Integration

1. Update `SpeechSynthesizer` to use the new audio manager
2. Implement chunked streaming with interruption checks
3. Test TTS with interruption capability

### 4. Main Integration

1. Update `Nova` class to use the new audio manager
2. Replace direct audio input/output with audio manager
3. Test the complete system

### 5. Refinement

1. Tune parameters for optimal performance
2. Add fallbacks for edge cases
3. Document the implementation

## Resources

- [Apple Voice Processing I/O Documentation](https://developer.apple.com/documentation/audiotoolbox/kaudiounitsubtype_voiceprocessingio)
- [WebRTC Audio Processing Module](https://chromium.googlesource.com/external/webrtc/+/lkgr/modules/audio_processing/include/audio_processing.h)
- [PortAudio Buffering and Latency Guidelines](https://github.com/PortAudio/portaudio/wiki/BufferingLatencyAndTimingImplementationGuidelines)
- [AVAudioSession PlayAndRecord Category](https://developer.apple.com/documentation/avfaudio/avaudiosession/category-swift.struct/playandrecord)

## Important Reminder

Always remember to activate the virtual environment before running any scripts or commands:

```bash
cd /Users/mouhamed23/nova
source .venv/bin/activate
```

This ensures that all the required dependencies are available and prevents conflicts with system-wide Python packages.
