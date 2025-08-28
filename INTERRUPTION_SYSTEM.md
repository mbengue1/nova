# Nova Interruption System

This document explains Nova's interruption system, which allows users to interrupt Nova while it's speaking and have Nova immediately process the interruption.

## Overview

The interruption system consists of several components:

1. **InterruptionMonitor**: A dedicated class that monitors audio input for speech during TTS output
2. **SpeechSynthesizer**: Enhanced to support interruption detection and immediate stopping
3. **SpeechTranscriber**: Enhanced to transcribe interruption audio
4. **HeyNova**: Updated to process interruptions as new requests

## How It Works

1. When Nova is speaking, the interruption monitor continuously listens for user speech
2. When speech is detected:
   - The current TTS output is immediately stopped
   - Audio is captured from the interruption
   - The audio is transcribed to text
   - The transcribed text is processed as a new request
   - Nova responds to the interruption

## Components

### InterruptionMonitor

Located in `core/audio/interruption_monitor.py`, this class provides:

- Adaptive baseline energy detection
- Consecutive frame tracking
- Audio capture on interruption
- Integration with Nova's transcription system

### SpeechSynthesizer Enhancements

The `SpeechSynthesizer` class in `core/tts/speaker.py` has been enhanced with:

- Support for interruption detection during speech
- Immediate stopping of speech when interrupted
- Integration with the InterruptionMonitor

### Azure TTS Enhancements

The `AzureSpeechSynthesizer` class in `core/tts/azure_speaker.py` has been enhanced with:

- Support for cancellation of speech synthesis
- Immediate stopping of speech when interrupted

### HeyNova Enhancements

The `HeyNova` class in `core/main.py` has been enhanced with:

- Processing of interruption audio
- Conversation state tracking
- Handling of interruptions as new requests

## Usage

The interruption system is automatically active when Nova is speaking. Users can simply start speaking to interrupt Nova, and Nova will:

1. Stop speaking immediately
2. Process what the user said
3. Respond to the user's interruption

## Testing

The interruption system can be tested using the `test_nova_interruption.py` script:

```bash
# Test all components
python scripts/test_nova_interruption.py

# Test specific components
python scripts/test_nova_interruption.py --test monitor  # Test just the interruption monitor
python scripts/test_nova_interruption.py --test tts      # Test TTS interruption
python scripts/test_nova_interruption.py --test nova     # Test full Nova integration
```

## Future Improvements

1. **Streaming Transcription**: Implement streaming transcription for even faster response
2. **Context Preservation**: Maintain context from the interrupted response
3. **Partial Response Handling**: Handle partial responses more intelligently
4. **Multi-turn Interruptions**: Support interruptions in multi-turn conversations
5. **User Preference Settings**: Allow users to configure interruption sensitivity
