# Barge-In (Speech Interruption) Implementation Notes

This document outlines the approach for implementing robust speech interruption ("barge-in") capability in Nova.

## Current Implementation (Half-Duplex Fallback)

The current implementation uses a simple half-duplex approach:
- Separate thread monitors microphone during TTS output
- Basic VAD and energy threshold detection
- Interrupts TTS when speech is detected

This approach has limitations but serves as a proof-of-concept for the interruption flow.

## Target Implementation (Full-Duplex with AEC)

For a robust, production-quality barge-in capability, we need to implement:

### 1) Acoustic Echo Cancellation (AEC)

- **macOS**: Use CoreAudio/AVAudioEngine with `kAudioUnitSubType_VoiceProcessingIO`
  - Provides AEC + NS + AGC + VAD in hardware-optimized form
  - Enable voice processing, 10 ms buffers, mono 16k/48k

- **Key requirements**:
  - Feed the exact PCM sent to speakers into the AEC reverse path
  - Use a single, full-duplex stream (same device, same rate) to avoid drift

### 2) Chunked TTS Playback

- Play TTS via non-blocking pull (stream chunks of 20-40 ms)
- After each chunk, check for user speech
- If detected, immediately stop output and switch to listen mode
- Keep output buffer ≤ 100 ms to minimize latency

### 3) Unified Audio Pipeline

- Use a full-duplex PortAudio/CoreAudio stream that:
  1. Pulls mic frames → AEC → VAD/Whisper feeder
  2. Pushes speaker frames from the TTS buffer
- Avoids thread scheduling issues
- Use real-time priority for audio thread

### 4) Improved Speech Detection

- Use short-term spectral flux or onset detection alongside VAD
- Implement hysteresis:
  - Trigger if speech probability > 0.7 for ≥ 50 ms
  - Require it to fall < 0.3 for ≥ 200 ms to reset
- Use 10 ms frames for responsive detection

### 5) Audio Ducking

- When possible speech is detected, duck TTS by ~12 dB
- Improves SNR for the mic to help VAD cross threshold
- Ramp back up if false alarm

### 6) Optimized Audio Parameters

- Standardize on 16k or 48k mono throughout the pipeline
- Use 128-512 frame buffers (2.7-10.7 ms at 48k)
- Match sample rates and buffer sizes end-to-end

### 7) Performance Optimization

- Pin audio I/O thread to real-time / high priority
- Keep Whisper off the hot path
- Use only VAD/onset detection on the realtime thread

## Implementation Roadmap

1. **Phase 1**: Half-duplex fallback (current)
2. **Phase 2**: Integrate macOS VoiceProcessingIO for AEC
3. **Phase 3**: Restructure audio pipeline for full-duplex operation
4. **Phase 4**: Implement chunked TTS playback
5. **Phase 5**: Add improved speech detection logic

## Expected Performance

With proper implementation, we should see ≤ 60 ms from user onset to TTS stop on a decent Mac.
