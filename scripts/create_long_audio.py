"""
Create a longer audio file by concatenating multiple system sounds
"""

import os
import subprocess
import tempfile

def create_long_audio():
    """Create a longer audio file by concatenating multiple system sounds"""
    # List of system sounds to concatenate
    system_sounds = [
        "/System/Library/Sounds/Submarine.aiff",
        "/System/Library/Sounds/Hero.aiff",
        "/System/Library/Sounds/Ping.aiff",
        "/System/Library/Sounds/Submarine.aiff",
        "/System/Library/Sounds/Hero.aiff",
        "/System/Library/Sounds/Ping.aiff",
    ]
    
    # Create temporary WAV files
    temp_wavs = []
    for sound in system_sounds:
        temp_wav = tempfile.mktemp(suffix='.wav')
        try:
            subprocess.run(['afconvert', '-f', 'WAVE', '-d', 'LEI16@44100', sound, temp_wav], 
                          check=True, capture_output=True)
            temp_wavs.append(temp_wav)
            print(f"Converted {sound} to {temp_wav}")
        except Exception as e:
            print(f"Error converting {sound}: {e}")
    
    # Create output directory if it doesn't exist
    os.makedirs("test_audio", exist_ok=True)
    
    # Concatenate WAV files
    output_file = "test_audio/long_test.wav"
    concat_list = " ".join(temp_wavs)
    
    try:
        # Create a file list for ffmpeg
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
            for wav in temp_wavs:
                f.write(f"file '{wav}'\n")
            file_list = f.name
        
        # Use ffmpeg to concatenate the files
        subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', file_list, '-c', 'copy', output_file], 
                      check=True, capture_output=True)
        print(f"Created long audio file: {output_file}")
        
        # Get duration of the output file using ffprobe
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                                '-of', 'default=noprint_wrappers=1:nokey=1', output_file], 
                               capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        print(f"Duration: {duration:.2f} seconds")
        
        # Clean up the file list
        try:
            os.remove(file_list)
        except:
            pass
        
        return output_file
    except Exception as e:
        print(f"Error creating long audio file: {e}")
        return None
    finally:
        # Clean up temporary files
        for temp_wav in temp_wavs:
            try:
                os.remove(temp_wav)
            except:
                pass

if __name__ == "__main__":
    create_long_audio()
