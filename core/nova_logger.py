"""
Structured logging system for Nova with audio tracing and metrics
Provides visibility into VAD, STT, and conversation flow
"""
import json
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import wave
import numpy as np

class NovaLogger:
    """Structured logger with audio tracing capabilities"""
    
    def __init__(self):
        self.start_time = time.monotonic()
        self.trace_dir = Path("/tmp/nova_traces")
        self.trace_dir.mkdir(exist_ok=True)
        
        # audio trace settings
        self.enable_audio_traces = True
        self.sample_rate = 16000
        
        # metrics tracking
        self.current_utterance = None
        self.utterance_metrics = {}
    
    def _get_timestamp(self) -> float:
        """Get monotonic timestamp since start"""
        return time.monotonic() - self.start_time
    
    def log(self, event: str, data: Dict[str, Any], level: str = "INFO"):
        """Log structured event with timestamp"""
        log_entry = {
            "timestamp": self._get_timestamp(),
            "level": level,
            "event": event,
            "data": data
        }
        
        # Filter out verbose logs
        verbose_events = [
            "vad_frame_processed", "vad_silence_detected", "vad_speech_detected",
            "audio_callback_entry", "audio_callback_active", "vad_recording_progress",
            "pre_callback_stream_state", "vad_audio_device_test", "vad_simple_audio_test",
            "vad_simple_audio_test_result", "audio_config_separation", "utterance_buffer_check"
        ]
        
        # Only print important logs
        if event not in verbose_events:
            ts_str = f"[{log_entry['timestamp']:.3f}s]"
            print(f"{ts_str} {level}: {event} - {json.dumps(data, default=str)}")
        
        # TODO: Add file logging if needed
        return log_entry
    
    def start_utterance(self, utterance_id: str):
        """Start tracking a new utterance"""
        self.current_utterance = utterance_id
        self.utterance_metrics = {
            "utterance_id": utterance_id,
            "start_time": self._get_timestamp(),
            "frames_total": 0,
            "frames_speech": 0,
            "vad_trigger_count": 0,
            "dropped_frames": 0,
            "latency_stt_ms": 0,
            "endpoint_ms": 0,
            "silence_ms_after_peak": 0
        }
        
        self.log("utterance_started", {
            "utterance_id": utterance_id,
            "start_time": self.utterance_metrics["start_time"]
        })
    
    def update_utterance_metrics(self, **kwargs):
        """Update current utterance metrics"""
        if self.current_utterance:
            self.utterance_metrics.update(kwargs)
    
    def complete_utterance(self, final_text: str = None):
        """Complete current utterance and log metrics"""
        if not self.current_utterance:
            return
        
        # calculate final metrics
        end_time = self._get_timestamp()
        duration = end_time - self.utterance_metrics["start_time"]
        
        # calculate speech ratio
        speech_ratio = 0
        if self.utterance_metrics["frames_total"] > 0:
            speech_ratio = self.utterance_metrics["frames_speech"] / self.utterance_metrics["frames_total"]
        
        final_metrics = {
            **self.utterance_metrics,
            "end_time": end_time,
            "duration_ms": duration * 1000,
            "speech_ratio": speech_ratio,
            "final_text": final_text
        }
        
        self.log("utterance_completed", final_metrics, "INFO")
        
        # reset for next utterance
        self.current_utterance = None
        self.utterance_metrics = {}
    
    def save_audio_trace(self, audio_data: np.ndarray, trace_type: str, utterance_id: str = None):
        """Save audio snippet for debugging"""
        if not self.enable_audio_traces:
            return
        
        try:
            # generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{timestamp}-{trace_type}"
            if utterance_id:
                filename += f"-{utterance_id[:8]}"
            filename += ".wav"
            
            filepath = self.trace_dir / filename
            
            # save as WAV
            with wave.open(str(filepath), 'wb') as wav_file:
                wav_file.setnchannels(1)  # mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            self.log("audio_trace_saved", {
                "filepath": str(filepath),
                "trace_type": trace_type,
                "utterance_id": utterance_id,
                "duration_ms": len(audio_data) / self.sample_rate * 1000,
                "samples": len(audio_data)
            })
            
        except Exception as e:
            self.log("audio_trace_error", {
                "error": str(e),
                "trace_type": trace_type
            }, "ERROR")
    
    def log_vad_event(self, event_type: str, **kwargs):
        """Log VAD-specific events"""
        self.log(f"vad_{event_type}", kwargs)
        
        if self.current_utterance:
            if event_type == "speech_detected":
                self.utterance_metrics["frames_speech"] += 1
                self.utterance_metrics["vad_trigger_count"] += 1
            elif event_type == "frame_processed":
                self.utterance_metrics["frames_total"] += 1
            elif event_type == "frame_dropped":
                self.utterance_metrics["dropped_frames"] += 1
    
    def log_stt_event(self, event_type: str, **kwargs):
        """Log STT-specific events"""
        self.log(f"stt_{event_type}", kwargs)
        
        if event_type == "transcription_complete" and self.current_utterance:
            latency = kwargs.get("latency_ms", 0)
            self.utterance_metrics["latency_stt_ms"] = latency
    
    def log_conversation_event(self, event_type: str, **kwargs):
        """Log conversation flow events"""
        self.log(f"conversation_{event_type}", kwargs)

# Global logger instance
logger = NovaLogger()
