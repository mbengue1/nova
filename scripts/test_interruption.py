"""
Test script for interruption detection
Isolates the interruption functionality for easier debugging

IMPORTANT: Always activate the virtual environment first:
    source .venv/bin/activate
"""

import sys
import os
import time
import threading

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from core.audio.interruption_monitor import InterruptionMonitor
    import pyaudio
    import numpy as np
    import sounddevice as sd
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you've activated the virtual environment: source .venv/bin/activate")
    sys.exit(1)

def play_audio_file(file_path):
    """Play an audio file while monitoring for interruptions"""
    try:
        import soundfile as sf
        
        # Load the audio file
        data, sample_rate = sf.read(file_path)
        
        print(f"Playing audio file: {file_path}")
        print(f"Sample rate: {sample_rate}, Duration: {len(data)/sample_rate:.2f}s")
        
        # Start interruption monitor
        monitor = InterruptionMonitor(
            sample_rate=sample_rate,
            energy_threshold=0.01,  # Very sensitive
            min_duration_ms=50      # Detect very short sounds
        )
        
        interrupted = threading.Event()
        
        def on_interruption():
            print("\n🛑 INTERRUPTION DETECTED!")
            print("Stopping audio playback...")
            interrupted.set()
        
        # Start monitoring
        monitor.start_monitoring(on_interruption=on_interruption)
        
        # Play the audio file in chunks to allow for interruption
        chunk_size = 1024
        
        # Create a stream for audio output
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paFloat32,
            channels=data.shape[1] if len(data.shape) > 1 else 1,
            rate=sample_rate,
            output=True
        )
        
        print("\n" + "="*60)
        print("🔊 INTERRUPTION TEST ACTIVE - speak anytime to interrupt")
        print("="*60 + "\n")
        
        # Play audio in chunks
        for i in range(0, len(data), chunk_size):
            if interrupted.is_set():
                break
                
            # Get the next chunk
            chunk = data[i:i+chunk_size]
            
            # Convert to float32 if needed
            if chunk.dtype != np.float32:
                chunk = chunk.astype(np.float32)
                
            # Play the chunk
            stream.write(chunk.tobytes())
            
            # Print progress occasionally
            if i % (chunk_size * 50) == 0:
                print(f"▶️ Playing... {i/len(data)*100:.1f}% ({i/sample_rate:.1f}s)")
        
        # Clean up
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Stop monitoring
        monitor.stop_monitoring()
        
        if interrupted.is_set():
            print("✅ Audio was successfully interrupted!")
        else:
            print("✅ Audio playback completed without interruption")
            
    except Exception as e:
        print(f"Error playing audio file: {e}")

def test_microphone_monitoring():
    """Test microphone monitoring for energy levels"""
    try:
        print("\n" + "="*60)
        print("🎤 MICROPHONE ENERGY LEVEL TEST")
        print("This will monitor your microphone and display energy levels")
        print("Speak at different volumes to see the detection thresholds")
        print("Press Ctrl+C to exit")
        print("="*60 + "\n")
        
        # Parameters
        duration = 0.1  # 100ms chunks
        sample_rate = 16000
        
        # Energy history
        energy_history = []
        baseline_energy = None
        
        # Start time
        start_time = time.time()
        
        try:
            while True:
                # Record audio
                recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
                sd.wait()
                
                # Calculate energy
                audio_float = recording.flatten().astype(np.float32) / 32768.0
                energy = np.sqrt(np.mean(audio_float**2))
                
                # Add to history
                energy_history.append(energy)
                if len(energy_history) > 20:
                    energy_history.pop(0)
                
                # Establish baseline if not yet set
                if baseline_energy is None and len(energy_history) >= 10:
                    baseline_energy = sum(energy_history) / len(energy_history)
                    print(f"📊 Baseline energy established: {baseline_energy:.6f}")
                
                # Calculate current average (last 3 frames)
                current_avg = sum(energy_history[-3:]) / min(3, len(energy_history))
                
                # Detect significant energy increase
                would_trigger = False
                if baseline_energy is not None:
                    would_trigger = (
                        current_avg > baseline_energy * 3.0 or  # 3x baseline
                        current_avg > 0.015                      # Absolute threshold
                    )
                
                # Print energy level with visual indicator
                bar_length = min(50, int(energy * 1000))
                bar = "█" * bar_length
                
                # Only print occasionally to avoid flooding the console
                elapsed = time.time() - start_time
                if elapsed % 0.5 < duration:
                    status = "🔴 WOULD TRIGGER" if would_trigger else "🟢 Normal"
                    print(f"Energy: {energy:.6f} | Avg: {current_avg:.6f} | {status}")
                    print(f"[{bar}]")
                    
                    if would_trigger:
                        print(f"🔊 Significant sound detected! {current_avg/baseline_energy:.1f}x baseline")
                
                # Short sleep
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n✅ Microphone monitoring test completed")
            
    except Exception as e:
        print(f"Error in microphone monitoring: {e}")

def main():
    """Main function"""
    print("="*60)
    print("NOVA INTERRUPTION TEST SCRIPT")
    print("="*60)
    print("\nThis script helps isolate and test the interruption detection capability.")
    print("Choose one of the following options:")
    print("1. Test microphone energy levels")
    print("2. Play audio file with interruption monitoring")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-3): ")
            
            if choice == "1":
                test_microphone_monitoring()
            elif choice == "2":
                file_path = input("Enter the path to an audio file to play: ")
                if os.path.exists(file_path):
                    play_audio_file(file_path)
                else:
                    print(f"Error: File not found: {file_path}")
            elif choice == "3":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
