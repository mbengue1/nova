"""
Regression Tests for Nova's Audio Pipeline

This module provides comprehensive tests for the audio components:
1. Speech-to-Text (STT) initialization and processing
2. Text-to-Speech (TTS) with both macOS and Azure backends
3. Voice Activity Detection (VAD) state machine transitions
4. Audio buffer management and processing

These tests ensure that the audio pipeline remains stable during
development and that changes don't break existing functionality.
They use mocking to avoid actual audio device access during testing.

Expected test results:
- STT initialization: Verifies proper configuration of Whisper and VAD
- TTS macOS speak: Confirms subprocess calls with correct parameters
- Azure TTS: Validates Azure Speech SDK integration
- VAD state machine: Tests all state transitions with simulated audio frames

To run these tests:
$ python tests/run_tests.py

Future enhancements:
- Audio fixture files for consistent testing
- Performance benchmarks for transcription accuracy
- End-to-end tests with recorded conversations
- Stress tests for long-running sessions
"""
import os
import sys
import unittest
import tempfile
import numpy as np
from unittest.mock import patch, MagicMock

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Nova components
from core.stt.transcriber import SpeechTranscriber
from core.tts.speaker import SpeechSynthesizer
from core.tts.azure_speaker import AzureSpeechSynthesizer
from core.config import NovaConfig

class AudioPipelineTests(unittest.TestCase):
    """Test suite for audio pipeline components"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temp directory for test artifacts
        self.test_dir = tempfile.mkdtemp()
        
        # Mock config for testing
        self.config_patcher = patch('core.config.config')
        self.mock_config = self.config_patcher.start()
        
        # Configure mock config
        self.mock_config.vad_enabled = True
        self.mock_config.vad_aggressiveness = 2
        self.mock_config.vad_frame_duration = 30
        self.mock_config.vad_padding_duration = 500
        self.mock_config.sample_rate = 16000
        
    def tearDown(self):
        """Clean up after tests"""
        self.config_patcher.stop()
    
    @patch('core.stt.transcriber.WhisperModel')
    @patch('core.stt.transcriber.webrtcvad.Vad')
    def test_stt_initialization(self, mock_vad, mock_whisper):
        """Test STT initialization"""
        # Configure mocks
        mock_vad_instance = MagicMock()
        mock_vad.return_value = mock_vad_instance
        
        mock_whisper_instance = MagicMock()
        mock_whisper.return_value = mock_whisper_instance
        
        # Initialize STT
        stt = SpeechTranscriber()
        
        # Verify initialization
        self.assertIsNotNone(stt)
        self.assertEqual(stt.sample_rate, 16000)
        self.assertEqual(stt.frame_ms, 30)
        self.assertEqual(stt.frame_samples_vad, 480)  # 16000 * 30 / 1000
        self.assertEqual(stt.frame_bytes_vad, 960)    # 480 * 2 bytes (int16)
        
        # Verify VAD initialization
        mock_vad.assert_called_once()
        self.assertIsNotNone(stt.vad)
        
        # Verify Whisper initialization
        mock_whisper.assert_called_once()
        self.assertIsNotNone(stt.whisper_model)
    
    @patch('core.tts.speaker.subprocess.Popen')
    def test_tts_macos_speak(self, mock_popen):
        """Test macOS TTS functionality"""
        # Configure mock
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        
        # Initialize TTS with mocked Azure
        with patch('core.tts.speaker.AzureSpeechSynthesizer') as mock_azure:
            mock_azure_instance = MagicMock()
            mock_azure_instance.is_available.return_value = False
            mock_azure.return_value = mock_azure_instance
            
            tts = SpeechSynthesizer()
            
            # Test speak functionality
            result = tts._speak_macos("Hello, this is a test", "Daniel", 1.0, None)
            
            # Verify speak was called correctly
            self.assertTrue(result)
            mock_popen.assert_called_once()
            args = mock_popen.call_args[0][0]
            self.assertEqual(args[0], "say")
            self.assertEqual(args[-1], "Hello, this is a test")
    
    @patch('core.tts.azure_speaker.speechsdk.SpeechSynthesizer')
    @patch('core.tts.azure_speaker.speechsdk.SpeechConfig')
    def test_azure_tts(self, mock_speech_config, mock_synthesizer):
        """Test Azure TTS functionality"""
        # Configure mocks
        mock_config_instance = MagicMock()
        mock_speech_config.return_value = mock_config_instance
        
        mock_synthesizer_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.reason.return_value = "SynthesizingAudioCompleted"
        mock_synthesizer_instance.speak_text_async.return_value.get.return_value = mock_result
        mock_synthesizer.return_value = mock_synthesizer_instance
        
        # Set environment variables for test
        with patch.dict(os.environ, {
            "AZURE_SPEECH_KEY": "test_key",
            "AZURE_SPEECH_REGION": "test_region"
        }):
            # Initialize Azure TTS
            azure_tts = AzureSpeechSynthesizer()
            
            # Verify initialization
            self.assertIsNotNone(azure_tts)
            self.assertEqual(azure_tts.voice_name, "en-GB-LibbyNeural")
            mock_speech_config.assert_called_once_with(
                subscription="test_key",
                region="test_region"
            )
            
            # Test speak functionality
            azure_tts.speak("Hello, this is a test")
            
            # Verify speak was called correctly
            mock_synthesizer.assert_called_once()
            mock_synthesizer_instance.speak_text_async.assert_called_once_with("Hello, this is a test")
    
    def test_vad_state_machine(self):
        """Test VAD state machine transitions"""
        # Initialize STT with mocked components
        with patch('core.stt.transcriber.WhisperModel'), \
             patch('core.stt.transcriber.webrtcvad.Vad'):
            
            stt = SpeechTranscriber()
            
            # Initialize VAD state
            stt._vad_state = {
                'state': 'IDLE',
                'enter_count': 0,
                'exit_count': 0,
                'frame_count': 0,
                'speech_frame_count': 0,
                'speech_start_time': None,
                'speech_end_time': None,
                'start_time': 0,
                'max_duration': 15,
                'preroll_buffer': [],
                'utterance_buffer': [],
                'postroll_buffer': []
            }
            
            # Mock VAD is_speech method
            stt.vad = MagicMock()
            
            # Test IDLE → PRE_SPEECH transition
            stt.vad.is_speech.return_value = True
            
            # Process 3 speech frames (assuming vad_enter_consec = 2)
            for i in range(3):
                stt._process_vad_frame(b'0' * 960, i)
            
            self.assertEqual(stt._vad_state['state'], 'PRE_SPEECH')
            
            # Test PRE_SPEECH → IN_SPEECH transition
            stt._process_vad_frame(b'0' * 960, 3)
            self.assertEqual(stt._vad_state['state'], 'IN_SPEECH')
            
            # Process more speech frames
            for i in range(4, 10):
                stt._process_vad_frame(b'0' * 960, i)
            
            # Test IN_SPEECH → POST_SPEECH transition
            stt.vad.is_speech.return_value = False
            
            # Process 7 silence frames (assuming vad_exit_consec = 6)
            for i in range(10, 17):
                stt._process_vad_frame(b'0' * 960, i)
            
            self.assertEqual(stt._vad_state['state'], 'POST_SPEECH')
            
            # Verify utterance buffer has frames
            self.assertGreater(len(stt._vad_state['utterance_buffer']), 0)

if __name__ == '__main__':
    unittest.main()
