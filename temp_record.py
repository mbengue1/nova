
import sounddevice as sd
import wave
import numpy as np
import sys

duration = 3.0  # seconds
fs = 44100  # sample rate
channels = 1
filename = "interruption_latest.wav"

print(f"Recording {duration} seconds of audio...")
recording = sd.rec(int(duration * fs), samplerate=fs, channels=channels, dtype='int16')
sd.wait()

print(f"Saving to {filename}...")
with wave.open(filename, 'wb') as wf:
    wf.setnchannels(channels)
    wf.setsampwidth(2)  # 2 bytes for int16
    wf.setframerate(fs)
    wf.writeframes(recording.tobytes())

print(f"Done! Audio saved to {filename}")
