"""
Speech-to-Text using Whisper with Voice Activity Detection (VAD)

This module provides advanced speech recognition capabilities:
1. Natural conversation detection using WebRTC VAD
2. Dynamic speech detection with state machine (IDLE → PRE_SPEECH → IN_SPEECH → POST_SPEECH)
3. Hysteresis for stable speech detection with configurable thresholds
4. Pre/post-roll audio capture for complete utterance context
5. Short utterance handling for common phrases
6. Audio normalization and volume boosting for better transcription
7. Streaming audio processing with frame buffering

The VAD state machine ensures reliable speech detection with minimal false triggers
while the Whisper model provides accurate transcription even for complex queries.

Future enhancements:
- Streaming transcription for real-time feedback
- Speaker identification
- Noise cancellation and acoustic adaptation
- Wake word-free continuous listening with local privacy filtering
"""
import sounddevice as sd
import numpy as np
import threading
import time
import webrtcvad
import uuid
from typing import Optional, Callable
from faster_whisper import WhisperModel
from config import config
import sys
import os
# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nova_logger import logger
from audio.input import AudioInputManager

class SpeechTranscriber:
    """Handles speech-to-text conversion using Whisper with VAD"""
    
    def __init__(self):
        self.audio = None
        self.whisper_model = None
        self.is_recording = False
        self.audio_frames = []
        self.vad = None
        self.interrupt_callback = None
        
        # audio configuration constants (fix scope issues)
        self.sample_rate = 16000
        self.frame_ms = 30
        self.frame_samples_vad = int(self.sample_rate * self.frame_ms / 1000)  # 480 samples
        self.frame_bytes_vad = self.frame_samples_vad * 2  # int16 mono = 960 bytes
        self.channels = 1
        self.dtype = 'int16'
        self._inbuf = bytearray()  # buffer for partial chunks from device
        
        # initialize VAD state (will be updated per recording session)
        self._vad_state = {
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
        
        # initialize whisper speech recognition model
        try:
            self.whisper_model = WhisperModel(
                "small",  # small model for better accuracy
                device="cpu",  # cpu processing for mvp
                compute_type="int8"
            )
            print("✅ Whisper model loaded")
        except Exception as e:
            print(f"⚠️  Warning: Could not load Whisper model: {e}")
            print("   Text input mode will be used instead")
        
        # initialize voice activity detection
        if config.vad_enabled:
            try:
                self.vad = webrtcvad.Vad(config.vad_aggressiveness)
                print("✅ Voice Activity Detection enabled")
            except Exception as e:
                print(f"⚠️  Warning: Could not initialize VAD: {e}")
                print("   Falling back to fixed duration recording")
                self.vad = None
        else:
            print("ℹ️  VAD disabled, using fixed duration recording")
    
    def set_interrupt_callback(self, callback: Callable):
        """Set callback function for handling interrupts"""
        self.interrupt_callback = callback
        
    def detect_interruption(self, duration_ms: int = 30) -> bool:
        """Listen for interruptions for a specified duration
        
        Args:
            duration_ms: How long to listen for interruptions (milliseconds)
            
        Returns:
            bool: True if interruption was detected, False otherwise
        """
        import sounddevice as sd
        import numpy as np
        import webrtcvad
        import time
        
        # Initialize VAD for interruption detection - most aggressive setting
        vad = webrtcvad.Vad(3)  # Most aggressive VAD for interruptions
        
        # Calculate frames needed based on duration
        # Use very short frames for faster detection
        frame_duration_ms = 10  # 10ms frames
        frame_size = int(self.sample_rate * frame_duration_ms / 1000)
        num_frames = max(1, int(duration_ms / frame_duration_ms))
        
        # Use extremely sensitive detection parameters for half-duplex fallback
        # We'll accept more false positives to ensure we catch real interruptions
        energy_threshold = 0.05  # Very low threshold to detect even quiet interruptions
        
        # Static variables to maintain state between calls
        if not hasattr(self, '_interruption_state'):
            self._interruption_state = {
                'speech_frames': 0,
                'energy_frames': 0,
                'last_frame_energy': 0,
                'energy_rise': 0,
                'last_detection_time': 0
            }
        
        # Hysteresis: don't trigger again too soon after a detection
        current_time = time.time()
        if (current_time - self._interruption_state['last_detection_time']) < 1.0:
            # Don't check again for 1 second after a detection
            return False
        
        try:
            # Open stream for short duration
            with sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                blocksize=frame_size,
                dtype='int16'
            ) as stream:
                for _ in range(num_frames):
                    # Read audio frame
                    audio_data, overflowed = stream.read(frame_size)
                    
                    # Convert to bytes for VAD
                    audio_bytes = audio_data.tobytes()
                    
                    # Check energy level (for non-speech sounds)
                    audio_float = audio_data.flatten().astype(np.float32) / 32768.0
                    frame_energy = np.sqrt(np.mean(audio_float**2))
                    
                    # Calculate energy rise (spectral flux simplified)
                    energy_rise = max(0, frame_energy - self._interruption_state['last_frame_energy'])
                    self._interruption_state['last_frame_energy'] = frame_energy
                    self._interruption_state['energy_rise'] += energy_rise
                    
                    # Very aggressive energy detection
                    if frame_energy > energy_threshold:
                        self._interruption_state['energy_frames'] += 1
                        if self._interruption_state['energy_frames'] >= 1:  # Just 1 frame above threshold
                            self._interruption_state['last_detection_time'] = current_time
                            self._interruption_state['energy_frames'] = 0
                            print("🛑 Interruption detected (energy)!")
                            return True
                    else:
                        self._interruption_state['energy_frames'] = 0
                    
                    # Energy rise detection (onset detection)
                    if self._interruption_state['energy_rise'] > 0.1:  # Significant rise in energy
                        self._interruption_state['last_detection_time'] = current_time
                        self._interruption_state['energy_rise'] = 0
                        print("🛑 Interruption detected (onset)!")
                        return True
                    
                    # Check if frame contains speech
                    try:
                        # Pad the frame if needed (WebRTC VAD requires specific frame sizes)
                        if len(audio_bytes) < 2 * frame_size:
                            padding = b'\x00' * (2 * frame_size - len(audio_bytes))
                            audio_bytes += padding
                            
                        is_speech = vad.is_speech(audio_bytes, self.sample_rate)
                        
                        if is_speech:
                            self._interruption_state['speech_frames'] += 1
                            if self._interruption_state['speech_frames'] >= 1:  # Just 1 frame of speech
                                self._interruption_state['last_detection_time'] = current_time
                                self._interruption_state['speech_frames'] = 0
                                print("🛑 Interruption detected (speech)!")
                                return True
                        else:
                            self._interruption_state['speech_frames'] = 0
                    except Exception:
                        pass
            
            return False
        except Exception as e:
            print(f"Error detecting interruption: {e}")
            return False
    
    def record_audio_with_vad(self, max_duration: int = None) -> Optional[str]:
        """Record audio using Voice Activity Detection with state machine"""
        if not self.whisper_model:
            return input("Type your message: ")
        
        if not self.vad:
            logger.log("vad_fallback", {"reason": "vad_not_available"})
            return self.record_audio_fixed(max_duration)
        
        # use config timeout if none specified
        if max_duration is None:
            max_duration = config.vad_timeout
        
        # generate utterance ID for tracking
        utterance_id = str(uuid.uuid4())[:8]
        logger.start_utterance(utterance_id)
        
        print(f"🎤 Listening... (utterance {utterance_id})")
        
        # initialize VAD state machine
        state = "IDLE"
        enter_count = 0
        exit_count = 0
        
        # audio buffers
        preroll_buffer = []
        utterance_buffer = []
        postroll_buffer = []
        
        # timing
        start_time = time.time()
        speech_start_time = None
        speech_end_time = None
        
        # frame processing
        frame_count = 0
        speech_frame_count = 0
        
        logger.log("vad_state_initialized", {
            "state": state,
            "enter_count": enter_count,
            "exit_count": exit_count,
            "start_time": start_time
        })
        
        # reset VAD state for this recording session
        self._vad_state.update({
            'state': state,
            'enter_count': enter_count,
            'exit_count': exit_count,
            'frame_count': frame_count,
            'speech_frame_count': speech_frame_count,
            'speech_start_time': speech_start_time,
            'speech_end_time': speech_end_time,
            'start_time': start_time,
            'max_duration': max_duration,
            'preroll_buffer': preroll_buffer,
            'utterance_buffer': utterance_buffer,
            'postroll_buffer': postroll_buffer
        })
        
        # test audio device before starting stream
        logger.log("vad_audio_device_test", {
            "device_info": sd.query_devices(),
            "default_input": sd.default.device[0],
            "sample_rate": self.sample_rate,
            "frame_samples_vad": self.frame_samples_vad,
            "frame_bytes_vad": self.frame_bytes_vad,
            "channels": self.channels,
            "dtype": self.dtype
        })
        
        # log clear frame size separation
        logger.log("audio_config_separation", {
            "wakeword_samples": 512,  # porcupine frame size
            "vad_samples": self.frame_samples_vad,  # 480 samples (30ms)
            "vad_bytes": self.frame_bytes_vad,  # 960 bytes
            "sample_rate": self.sample_rate
        })
        
        try:
            # first, test if we can actually capture audio with a simple test
            logger.log("vad_simple_audio_test", {"message": "Testing basic audio capture..."})
            
            # test with a simple blocking read first
            try:
                with sd.InputStream(
                    channels=self.channels,
                    samplerate=self.sample_rate,
                    dtype=self.dtype,
                    blocksize=self.frame_samples_vad
                ) as test_stream:
                    # try to read one frame
                    test_data, overflowed = test_stream.read(self.frame_samples_vad)
                    logger.log("vad_simple_audio_test_result", {
                        "success": True,
                        "data_shape": test_data.shape if test_data is not None else None,
                        "overflowed": overflowed
                    })
            except Exception as test_e:
                logger.log("vad_simple_audio_test_result", {
                    "success": False,
                    "error": str(test_e)
                }, "ERROR")
            

            
            # verify state before starting callback stream
            logger.log("pre_callback_stream_state", {
                "is_recording": self.is_recording,
                "has_vad_state": hasattr(self, '_vad_state'),
                "vad_state_keys": list(self._vad_state.keys()) if hasattr(self, '_vad_state') else [],
                "callback_method_exists": hasattr(self, '_on_audio')
            })
            
            # CRITICAL: Set recording state BEFORE starting stream
            self.is_recording = True
            logger.log("recording_state_set", {"is_recording": self.is_recording})
            
            # now try the callback-based stream
            with sd.InputStream(
                callback=self._on_audio,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=self.dtype,
                blocksize=self.frame_samples_vad
            ) as stream:
                logger.log("vad_stream_started", {"stream_active": stream.active})
                
                # wait for recording to complete
                start_wait = time.time()
                while self.is_recording and self._vad_state['state'] != "COMPLETE":
                    time.sleep(0.01)  # 10ms polling for responsiveness
                    
                    # log progress every 100ms
                    elapsed = time.time() - start_wait
                    if int(elapsed * 1000) % 100 == 0:
                        logger.log("vad_recording_progress", {
                            "state": self._vad_state['state'],
                            "frame_count": self._vad_state['frame_count'],
                            "is_recording": self.is_recording,
                            "elapsed_ms": elapsed * 1000
                        })
                    
                    # safety timeout - if no frames received after 1 second, something's wrong
                    if elapsed > 1.0 and self._vad_state['frame_count'] == 0:
                        logger.log("vad_no_frames_timeout", {"elapsed_ms": elapsed * 1000})
                        break
                
                self.is_recording = False
                logger.log("vad_stream_completed", {
                    "final_state": self._vad_state['state'], 
                    "total_frames": self._vad_state['frame_count']
                })
                
        except Exception as e:
            logger.log("vad_stream_error", {"error": str(e)}, "ERROR")
            raise
        
        print("🔇 Recording stopped")
        
        # finalize utterance metrics
        if (self._vad_state['speech_start_time'] and 
            self._vad_state['speech_end_time']):
            endpoint_ms = ((self._vad_state['speech_end_time'] - 
                           self._vad_state['speech_start_time']) * 1000)
            logger.update_utterance_metrics(
                frames_speech=self._vad_state['speech_frame_count'],
                endpoint_ms=endpoint_ms
            )
        
        # check if we have enough audio
        logger.log("utterance_buffer_check", {
            "buffer_length": len(self._vad_state['utterance_buffer']),
            "buffer_empty": not self._vad_state['utterance_buffer'],
            "preroll_length": len(self._vad_state['preroll_buffer']),
            "postroll_length": len(self._vad_state['postroll_buffer'])
        })
        
        if not self._vad_state['utterance_buffer']:
            logger.log("vad_no_utterance", {"state": self._vad_state['state']})
            print("⚠️  No utterance captured")
            logger.complete_utterance()
            return None
        
        # save audio traces for debugging
        if self._vad_state['preroll_buffer']:
            preroll_audio = np.frombuffer(b''.join(self._vad_state['preroll_buffer']), dtype=np.int16)
            logger.save_audio_trace(preroll_audio, "preroll", utterance_id)
        
        utterance_audio = np.frombuffer(b''.join(self._vad_state['utterance_buffer']), dtype=np.int16)
        logger.save_audio_trace(utterance_audio, "utterance", utterance_id)
        
        if self._vad_state['postroll_buffer']:
            postroll_audio = np.frombuffer(b''.join(self._vad_state['postroll_buffer']), dtype=np.int16)
            logger.save_audio_trace(postroll_audio, "postroll", utterance_id)
        
        # transcribe audio to text
        result = self._transcribe_audio_from_buffer(self._vad_state['utterance_buffer'], utterance_id)
        logger.complete_utterance(result)
        
        # always ensure clean state
        self.is_recording = False
        return result
    
    def record_audio_fixed(self, duration: int = None) -> Optional[str]:
        """Fallback: Record audio with fixed duration"""
        duration = duration or config.record_seconds
        
        print(f"🎤 Recording for {duration} seconds...")
        print("   Speak now!")
        
        try:
            audio_data = sd.rec(
                int(config.sample_rate * duration),
                samplerate=config.sample_rate,
                channels=1,
                dtype=np.int16
            )
            
            sd.wait()
            print("🔇 Recording stopped")
            
            self.audio_frames = [audio_data.tobytes()]
            return self._transcribe_audio()
            
        except Exception as e:
            print(f"Error recording audio: {e}")
            return None
    
    def record_audio(self, duration: int = None) -> Optional[str]:
        """Main recording method - uses VAD if available, falls back to fixed duration"""
        if config.vad_enabled and self.vad:
            return self.record_audio_with_vad(duration)
        else:
            return self.record_audio_fixed(duration)
    
    def _transcribe_audio_from_buffer(self, audio_buffer: list, utterance_id: str) -> Optional[str]:
        """Transcribe audio from buffer with timing and logging"""
        if not audio_buffer:
            return None
        
        try:
            start_time = time.time()
            
            # convert audio frames to numpy array
            audio_data = b''.join(audio_buffer)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # normalize audio data and boost volume for better detection
            audio_array = audio_array.astype(np.float32) / 32768.0
            
            # Dynamic normalization to handle different volume levels
            # First calculate RMS volume
            rms = np.sqrt(np.mean(audio_array**2))
            
            # Apply adaptive gain based on volume
            if rms < 0.05:  # Very quiet audio
                gain = 3.0  # Higher boost for quiet audio
            elif rms < 0.1:  # Moderately quiet audio
                gain = 2.5
            elif rms < 0.2:  # Normal audio
                gain = 2.0
            else:  # Already loud audio
                gain = 1.5
                
            # Apply the calculated gain with clipping to prevent distortion
            audio_array = np.clip(audio_array * gain, -1.0, 1.0)
            
            # Apply noise gate to reduce background noise
            noise_gate = 0.01  # Threshold below which audio is considered noise
            audio_array[np.abs(audio_array) < noise_gate] = 0.0
            
            # log transcription start
            logger.log_stt_event("transcription_started",
                utterance_id=utterance_id,
                audio_samples=len(audio_array),
                audio_duration_ms=len(audio_array) / config.sample_rate * 1000
            )
            
            # transcribe audio with whisper model - enhanced parameters for better accuracy
            segments, _ = self.whisper_model.transcribe(
                audio_array,
                language="en",
                beam_size=5,
                word_timestamps=True,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=100,  # even shorter silence detection
                    threshold=0.15  # more sensitive for better speech detection
                ),
                condition_on_previous_text=False,  # don't bias based on previous text
                temperature=0.0,  # use greedy decoding for more accurate results
                no_speech_threshold=0.4,  # more sensitive to detect speech
                compression_ratio_threshold=2.4,  # better handling of background noise
                log_prob_threshold=-1.0  # more lenient probability threshold
            )
            
            # extract transcription text from segments (convert generator to list)
            segments_list = list(segments)
            transcription = " ".join([segment.text for segment in segments_list])
            
            # log segment details for debugging
            for i, segment in enumerate(segments_list):
                logger.log("whisper_segment", {
                    "segment": i,
                    "text": segment.text,
                    "start": segment.start,
                    "end": segment.end,
                    "words": len(getattr(segment, 'words', [])),
                    "confidence": getattr(segment, 'confidence', 0)
                })
            
            # calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            if transcription.strip():
                logger.log_stt_event("transcription_complete",
                    utterance_id=utterance_id,
                    text=transcription.strip(),
                    latency_ms=latency_ms,
                    segments=len(segments_list)
                )
                
                print(f"📝 Transcribed: '{transcription}'")
                return transcription.strip()
            else:
                # Try to handle very short utterances (like "Yes", "No", "Hi")
                # Look for any speech frames and make a best effort
                if self._vad_state['speech_frame_count'] > 2:
                    # Attempt to recognize common short phrases
                    short_phrases = ["yes", "no", "hi", "hey", "okay", "thanks", "stop", "help", 
                                    "what", "time", "weather", "how", "why", "when", "where"]
                    
                    # Check if audio duration is very short (less than 1500ms of speech)
                    speech_duration_ms = self._vad_state['speech_frame_count'] * self.frame_ms
                    logger.log("short_utterance_attempt", {
                        "speech_frames": self._vad_state['speech_frame_count'],
                        "speech_duration_ms": speech_duration_ms
                    })
                    
                    if speech_duration_ms < 1500:
                        # Try to make better guesses based on speech duration and energy pattern
                        # Get audio data for energy analysis
                        audio_data = b''.join(self._vad_state['utterance_buffer'])
                        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                        
                        # Calculate energy features
                        energy = np.abs(audio_array)
                        mean_energy = np.mean(energy)
                        energy_variance = np.var(energy)
                        
                        # Calculate zero crossing rate (voice characteristic)
                        zero_crossings = np.sum(np.abs(np.diff(np.signbit(audio_array))))
                        zero_crossing_rate = zero_crossings / len(audio_array) if len(audio_array) > 0 else 0
                        
                        # More sophisticated pattern matching based on speech characteristics
                        if speech_duration_ms < 300:
                            # Very short utterances: yes, no, hi
                            if zero_crossing_rate > 0.2:  # Higher frequency content ("yes")
                                guess = "yes"
                            elif mean_energy > 0.2:  # Louder, shorter sound ("no")
                                guess = "no"
                            else:
                                guess = "hi"
                        elif speech_duration_ms < 600:
                            # Short utterances: okay, stop, thanks
                            if zero_crossing_rate < 0.15 and energy_variance < 0.01:  # Smoother sound ("okay")
                                guess = "okay"
                            elif mean_energy > 0.25:  # Louder, sharper sound ("stop")
                                guess = "stop"
                            else:
                                guess = "thanks"
                        elif speech_duration_ms < 900:
                            # Medium short utterances: cancel, continue, goodbye
                            if energy_variance > 0.015:  # More varied energy ("cancel")
                                guess = "cancel"
                            elif zero_crossing_rate > 0.18:  # More varied frequency ("continue")
                                guess = "continue"
                            else:
                                guess = "goodbye"
                        else:
                            # Slightly longer utterances (900-1500ms)
                            if mean_energy > 0.2:  # Stronger utterance
                                guess = "good night"
                            elif zero_crossing_rate > 0.2:  # More varied frequency
                                guess = "what time is it"
                            else:
                                guess = "what's the weather"
                        logger.log_stt_event("transcription_short_guess",
                            utterance_id=utterance_id,
                            latency_ms=latency_ms,
                            guess=guess,
                            speech_frames=self._vad_state['speech_frame_count']
                        )
                        print(f"📝 Short utterance guess: '{guess}'")
                        return guess
                
                # If not a short utterance or couldn't guess, log as empty
                logger.log_stt_event("transcription_empty",
                    utterance_id=utterance_id,
                    latency_ms=latency_ms
                )
                print("⚠️  No speech detected in transcription")
                return None
                
        except Exception as e:
            logger.log_stt_event("transcription_error",
                utterance_id=utterance_id,
                error=str(e)
            )
            print(f"Error transcribing audio: {e}")
            return None
    
    def _transcribe_audio(self) -> Optional[str]:
        """Legacy method - transcribe from audio_frames"""
        if not self.audio_frames:
            return None
        
        # convert to new format and call new method
        utterance_id = str(uuid.uuid4())[:8]
        return self._transcribe_audio_from_buffer(self.audio_frames, utterance_id)
    
    def stop_recording(self):
        """Stop recording immediately"""
        self.is_recording = False
    
    def is_currently_recording(self) -> bool:
        """Check if currently recording"""
        return self.is_recording
    
    def transcribe_file(self, file_path: str) -> Optional[str]:
        """Transcribe an audio file
        
        Args:
            file_path: Path to the audio file to transcribe
            
        Returns:
            str: Transcribed text, or None if transcription failed
        """
        if not self.whisper_model:
            print("⚠️ Whisper model not available for file transcription")
            return None
        
        if not os.path.exists(file_path):
            print(f"⚠️ Audio file not found: {file_path}")
            return None
        
        try:
            print(f"🎤 Transcribing audio file: {file_path}")
            
            # Process with Whisper
            segments, info = self.whisper_model.transcribe(
                file_path,
                beam_size=5,
                language="en",
                vad_filter=True
            )
            
            # Collect all segments
            transcript = " ".join([segment.text for segment in segments])
            
            # Clean up the transcript
            transcript = transcript.strip()
            
            print(f"✅ Transcription complete: '{transcript}'")
            return transcript
            
        except Exception as e:
            print(f"❌ Error transcribing file: {e}")
            return None
    
    def reset_state(self):
        """Reset VAD and recording state for clean conversation flow"""
        self.is_recording = False
        self.audio_frames = []
        print("🔄 VAD state reset for new conversation")
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_recording()
        # sounddevice doesn't need explicit cleanup
        pass
    
    def _on_audio(self, indata, frames, time, status):
        """Audio callback with buffer-slice pattern"""
        # always log callback entry for debugging
        logger.log("audio_callback_entry", {
            "is_recording": getattr(self, 'is_recording', 'missing'),
            "has_vad_state": hasattr(self, '_vad_state'),
            "frames": frames,
            "status": str(status) if status else "ok"
        })
        
        if status:
            logger.log("audio_callback_status", {"status": status}, "WARNING")
        
        if not self.is_recording or not hasattr(self, '_vad_state'):
            logger.log("audio_callback_guard_failed", {
                "is_recording": self.is_recording,
                "has_vad_state": hasattr(self, '_vad_state')
            })
            return
        
        # log every 5th callback to confirm it's working
        if self._vad_state['frame_count'] % 5 == 0:
            logger.log("audio_callback_active", {
                "frame": self._vad_state['frame_count'],
                "frames_received": frames,
                "recording": self.is_recording
            })
        
        # indata is numpy array, convert to bytes for buffering
        self._inbuf.extend(indata.tobytes())
        
        # slice exact 30ms VAD frames; keep remainder in buffer
        while len(self._inbuf) >= self.frame_bytes_vad:
            frame_bytes = bytes(self._inbuf[:self.frame_bytes_vad])
            del self._inbuf[:self.frame_bytes_vad]
            self._process_vad_frame(frame_bytes, self._vad_state['frame_count'])
            self._vad_state['frame_count'] += 1
    
    def _process_vad_frame(self, frame_bytes, frame_num):
        """Process individual VAD frames"""
        if not hasattr(self, '_vad_state'):
            return
            
        state = self._vad_state
        logger.update_utterance_metrics(frames_total=frame_num)
        
        # check if frame contains speech using webrtcvad
        is_speech = self.vad.is_speech(frame_bytes, self.sample_rate)
        
        # debug logging for VAD decisions
        if frame_num % 10 == 0:  # log every 10th frame to avoid spam
            logger.log("vad_frame_processed", {
                "frame": frame_num,
                "is_speech": is_speech,
                "state": state['state'],
                "enter_count": state['enter_count'],
                "exit_count": state['exit_count'],
                "frame_bytes": len(frame_bytes)
            })
        
        if is_speech:
            state['speech_frame_count'] += 1
            logger.log_vad_event("speech_detected", frame_count=frame_num)
        else:
            logger.log_vad_event("silence_detected", frame_count=frame_num)
        
        # VAD State Machine
        if state['state'] == "IDLE":
            # collect preroll audio
            state['preroll_buffer'].append(frame_bytes)
            
            if is_speech:
                state['enter_count'] += 1
                if state['enter_count'] >= config.vad_enter_consec:
                    # transition to PRE_SPEECH
                    state['state'] = "PRE_SPEECH"
                    state['enter_count'] = 0
                    logger.log("vad_state_transition", {
                        "from": "IDLE",
                        "to": "PRE_SPEECH",
                        "enter_count": config.vad_enter_consec
                    })
            else:
                state['enter_count'] = 0
        
        elif state['state'] == "PRE_SPEECH":
            # continue collecting preroll
            state['preroll_buffer'].append(frame_bytes)
            
            if is_speech:
                # transition to IN_SPEECH
                state['state'] = "IN_SPEECH"
                state['speech_start_time'] = time.time()
                
                # start utterance buffer with preroll
                state['utterance_buffer'].extend(state['preroll_buffer'])
                state['utterance_buffer'].append(frame_bytes)
                
                logger.log("vad_state_transition", {
                    "from": "PRE_SPEECH",
                    "to": "IN_SPEECH",
                    "preroll_frames": len(state['preroll_buffer'])
                })
            else:
                # return to IDLE if speech stops
                state['state'] = "IDLE"
                state['preroll_buffer'].clear()
                state['enter_count'] = 0
        
        elif state['state'] == "IN_SPEECH":
            # collect utterance audio
            state['utterance_buffer'].append(frame_bytes)
            
            if not is_speech:
                state['exit_count'] += 1
                if state['exit_count'] >= config.vad_exit_consec:
                    # transition to POST_SPEECH
                    state['state'] = "POST_SPEECH"
                    state['speech_end_time'] = time.time()
                    state['exit_count'] = 0
                    
                    logger.log("vad_state_transition", {
                        "from": "IN_SPEECH",
                        "to": "POST_SPEECH",
                        "exit_count": config.vad_exit_consec,
                        "utterance_frames": len(state['utterance_buffer'])
                    })
            else:
                state['exit_count'] = 0
        
        elif state['state'] == "POST_SPEECH":
            # collect postroll audio
            state['postroll_buffer'].append(frame_bytes)
            state['utterance_buffer'].append(frame_bytes)
            
            # check if postroll is complete or max duration reached
            postroll_duration = (len(state['postroll_buffer']) * self.frame_ms)
            utterance_duration = (len(state['utterance_buffer']) * self.frame_ms)
            
            if (postroll_duration >= config.vad_postroll_ms or 
                utterance_duration >= config.vad_max_utterance_ms):
                # finalize utterance
                state['state'] = "COMPLETE"
                self.is_recording = False
                
                logger.log("vad_state_transition", {
                    "from": "POST_SPEECH",
                    "to": "COMPLETE",
                    "postroll_ms": postroll_duration,
                    "utterance_ms": utterance_duration
                })
        
        # check for timeout
        if time.time() - state['start_time'] > state['max_duration']:
            logger.log("vad_timeout", {"max_duration": state['max_duration']})
            state['state'] = "COMPLETE"
            self.is_recording = False
