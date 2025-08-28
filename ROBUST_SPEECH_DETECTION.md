# Robust Speech Detection for Interruption

This document outlines the improvements made to the speech detection system for more reliable interruption detection.

## Problem

The initial implementation of the interruption detection was too sensitive and would trigger on background noise or system sounds rather than actual speech. This resulted in false interruptions when no one was actually speaking.

## Solution

We've implemented a more robust speech detection system with the following features:

### 1. Adaptive Baseline Energy Detection

- **Baseline Calculation**: The system establishes a baseline energy level by averaging the energy of the first 10 frames.
- **Relative Threshold**: The interruption threshold is set relative to the baseline (5x the baseline or minimum 0.05).
- **Dynamic Adjustment**: The baseline can be periodically updated to account for changing background noise conditions.

### 2. Consecutive Frame Requirement

- **Multiple Frame Trigger**: Requires 3 consecutive frames above the threshold to trigger an interruption.
- **Noise Filtering**: This helps filter out short noise spikes that aren't actual speech.
- **Reset on Silence**: The consecutive frame counter resets when energy drops below threshold.

### 3. Energy Calculation

- **RMS Energy**: Uses Root Mean Square (RMS) energy calculation for more accurate speech detection.
- **Normalization**: Audio samples are normalized to float range [-1.0, 1.0] before energy calculation.
- **History Tracking**: Maintains a history of recent energy levels for trend analysis.

### 4. Dual Monitoring

- **Buffer Processing**: Monitors audio through the AVAudioEngine buffer tap.
- **Direct Sampling**: Also performs direct sampling with sounddevice during playback.
- **Redundancy**: The dual approach provides more reliable detection.

## Implementation

The implementation uses two key methods for interruption detection:

### 1. Audio Buffer Processing

```python
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
        # Set threshold relative to baseline (much higher than baseline)
        self.energy_threshold = max(0.05, self.baseline_energy * 5.0)
        print(f"📊 Energy threshold set to: {self.energy_threshold:.6f}")
    
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
    if self.consecutive_frames_above_threshold >= 3:  # Require 3 consecutive frames
        print(f"🛑 SPEECH INTERRUPTION DETECTED! Energy: {energy:.6f}")
        self.was_interrupted = True
        self.interruption_event.set()
```

### 2. Direct Monitoring During Playback

```python
# For direct monitoring during playback
import numpy as np
import sounddevice as sd

# Track energy for interruption detection
energy_history = []
consecutive_frames = 0
baseline = None

while process.poll() is None:
    # First check if interruption was already detected by audio buffer processing
    if self.interruption_event.is_set():
        print("🛑 Stopping playback due to interruption (from buffer processing)")
        process.terminate()
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
        
        # Add to history
        energy_history.append(energy)
        if len(energy_history) > 20:
            energy_history.pop(0)
        
        # Establish baseline if not yet set
        if baseline is None and len(energy_history) >= 10:
            baseline = sum(energy_history) / len(energy_history)
            print(f"📊 Direct monitoring baseline: {baseline:.6f}")
            # Set threshold relative to baseline
            threshold = max(0.05, baseline * 5.0)
            print(f"📊 Direct monitoring threshold: {threshold:.6f}")
        
        # Check for interruption
        if baseline is not None:
            if energy > threshold:
                consecutive_frames += 1
                print(f"⚡ Direct energy spike: {energy:.6f} (threshold: {threshold:.6f}, consecutive: {consecutive_frames})")
            else:
                consecutive_frames = 0
            
            # Only trigger after multiple consecutive frames
            if consecutive_frames >= 3:
                print(f"🛑 DIRECT SPEECH INTERRUPTION! Energy: {energy:.6f}")
                self.was_interrupted = True
                self.interruption_event.set()
                process.terminate()
                break
    except Exception as e:
        print(f"Error in direct monitoring: {e}")
```

## Integration with Nova

This robust speech detection system will be integrated into Nova's audio pipeline to provide reliable interruption detection. The key components to integrate are:

1. **Audio Manager**: The `NovaAudioManager` class will use this approach for interruption detection.
2. **TTS System**: The `SpeechSynthesizer` class will use the audio manager for interruption detection.
3. **Main Class**: The `Nova` class will use the audio manager for all audio I/O.

## Conclusion

By implementing this robust speech detection system, Nova will be able to reliably detect actual speech for interruptions while ignoring background noise and system sounds. This will provide a much better user experience with fewer false interruptions.
