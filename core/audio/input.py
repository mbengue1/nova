"""
Audio input system with ring buffer for stable VAD processing
Prevents frame starvation and provides consistent audio flow
"""
import numpy as np
import sounddevice as sd
import threading
import time
from typing import Optional, Callable, List
from collections import deque
import sys
import os
# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import config
from core.nova_logger import logger

class AudioRingBuffer:
    """Ring buffer for audio frames with thread-safe operations"""
    
    def __init__(self, buffer_seconds: float = 2.5, sample_rate: int = 16000, frame_ms: int = 30):
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.frame_samples = int(sample_rate * frame_ms / 1000)
        
        # calculate buffer size in frames
        self.buffer_frames = int(buffer_seconds * 1000 / frame_ms)
        self.buffer = deque(maxlen=self.buffer_frames)
        
        # thread safety
        self.lock = threading.Lock()
        self.overflow_count = 0
        self.underflow_count = 0
        
        logger.log("ring_buffer_initialized", {
            "buffer_seconds": buffer_seconds,
            "sample_rate": sample_rate,
            "frame_ms": frame_ms,
            "frame_samples": self.frame_samples,
            "buffer_frames": self.buffer_frames
        })
    
    def push_frame(self, frame_data: np.ndarray) -> bool:
        """Add a frame to the buffer"""
        with self.lock:
            if len(self.buffer) >= self.buffer_frames:
                self.overflow_count += 1
                logger.log("ring_buffer_overflow", {
                    "overflow_count": self.overflow_count,
                    "current_frames": len(self.buffer)
                })
                return False
            
            self.buffer.append(frame_data.copy())
            return True
    
    def pop_frame(self) -> Optional[np.ndarray]:
        """Remove and return a frame from the buffer"""
        with self.lock:
            if not self.buffer:
                self.underflow_count += 1
                logger.log("ring_buffer_underflow", {
                    "underflow_count": self.underflow_count
                })
                return None
            
            return self.buffer.popleft()
    
    def peek_frame(self) -> Optional[np.ndarray]:
        """Look at the next frame without removing it"""
        with self.lock:
            if not self.buffer:
                return None
            return self.buffer[0]
    
    def get_frame_count(self) -> int:
        """Get current number of frames in buffer"""
        with self.lock:
            return len(self.buffer)
    
    def clear(self):
        """Clear all frames from buffer"""
        with self.lock:
            self.buffer.clear()
            logger.log("ring_buffer_cleared", {})
    
    def get_stats(self) -> dict:
        """Get buffer statistics"""
        with self.lock:
            return {
                "current_frames": len(self.buffer),
                "max_frames": self.buffer_frames,
                "overflow_count": self.overflow_count,
                "underflow_count": self.underflow_count,
                "utilization": len(self.buffer) / self.buffer_frames
            }

class AudioInputManager:
    """Manages audio input with ring buffer and VAD integration"""
    
    def __init__(self):
        self.ring_buffer = AudioRingBuffer(
            buffer_seconds=2.5,
            sample_rate=config.sample_rate,
            frame_ms=config.vad_frame_duration
        )
        
        self.is_recording = False
        self.audio_stream = None
        self.frame_callback = None
        
        logger.log("audio_input_initialized", {
            "sample_rate": config.sample_rate,
            "frame_duration_ms": config.vad_frame_duration
        })
    
    def set_frame_callback(self, callback: Callable[[np.ndarray], None]):
        """Set callback for processing audio frames"""
        self.frame_callback = callback
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback from sounddevice audio stream"""
        if status:
            logger.log("audio_callback_status", {"status": status})
        
        if not self.is_recording:
            return
        
        try:
            # ensure correct frame size
            if frames != self.ring_buffer.frame_samples:
                logger.log("frame_size_mismatch", {
                    "expected": self.ring_buffer.frame_samples,
                    "received": frames
                })
                return
            
            # convert to mono if needed
            if indata.ndim > 1:
                frame_data = indata[:, 0]  # take first channel
            else:
                frame_data = indata.flatten()
            
            # ensure int16 format
            if frame_data.dtype != np.int16:
                frame_data = (frame_data * 32767).astype(np.int16)
            
            # add to ring buffer
            success = self.ring_buffer.push_frame(frame_data)
            
            if success and self.frame_callback:
                # process frame in separate thread to avoid blocking
                threading.Thread(
                    target=self.frame_callback,
                    args=(frame_data,),
                    daemon=True
                ).start()
            
        except Exception as e:
            logger.log("audio_callback_error", {"error": str(e)}, "ERROR")
    
    def start_recording(self):
        """Start audio recording"""
        if self.is_recording:
            return
        
        try:
            self.is_recording = True
            self.ring_buffer.clear()
            
            # start audio stream
            self.audio_stream = sd.InputStream(
                callback=self._audio_callback,
                channels=1,
                samplerate=config.sample_rate,
                dtype=np.int16,
                blocksize=self.ring_buffer.frame_samples
            )
            
            self.audio_stream.start()
            
            logger.log("audio_recording_started", {
                "sample_rate": config.sample_rate,
                "frame_samples": self.ring_buffer.frame_samples
            })
            
        except Exception as e:
            logger.log("audio_recording_start_error", {"error": str(e)}, "ERROR")
            self.is_recording = False
    
    def stop_recording(self):
        """Stop audio recording"""
        if not self.is_recording:
            return
        
        try:
            self.is_recording = False
            
            if self.audio_stream:
                self.audio_stream.stop()
                self.audio_stream.close()
                self.audio_stream = None
            
            # log final stats
            stats = self.ring_buffer.get_stats()
            logger.log("audio_recording_stopped", stats)
            
        except Exception as e:
            logger.log("audio_recording_stop_error", {"error": str(e)}, "ERROR")
    
    def get_audio_chunk(self, duration_ms: int) -> Optional[np.ndarray]:
        """Get audio chunk of specified duration from buffer"""
        if not self.is_recording:
            return None
        
        # calculate frames needed
        frames_needed = int(duration_ms * config.sample_rate / 1000 / self.ring_buffer.frame_samples)
        
        if frames_needed <= 0:
            return None
        
        # collect frames
        frames = []
        for _ in range(frames_needed):
            frame = self.ring_buffer.pop_frame()
            if frame is not None:
                frames.append(frame)
            else:
                break
        
        if not frames:
            return None
        
        # concatenate frames
        return np.concatenate(frames)
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_recording()
        self.ring_buffer.clear()
        logger.log("audio_input_cleanup", {})
