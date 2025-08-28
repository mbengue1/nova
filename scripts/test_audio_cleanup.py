#!/usr/bin/env python3
"""
Test script for Nova's audio cleanup functionality
"""

import os
import time
import tempfile
import shutil
from pathlib import Path

def create_test_audio_files(directory: str, count: int = 15):
    """Create test audio files with different timestamps"""
    print(f"🎵 Creating {count} test audio files in {directory}...")
    
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    # Create files with different timestamps
    for i in range(count):
        # Create files with different ages (some old, some new)
        if i < 5:
            # Old files (more than 24 hours)
            timestamp = time.time() - (25 * 3600) + i * 100
        elif i < 10:
            # Medium files (12-24 hours)
            timestamp = time.time() - (18 * 3600) + i * 100
        else:
            # Recent files (less than 12 hours)
            timestamp = time.time() - (6 * 3600) + i * 100
        
        filename = f"interruption_test_{i:02d}.wav"
        filepath = os.path.join(directory, filename)
        
        # Create a dummy WAV file
        with open(filepath, 'wb') as f:
            # Minimal WAV header + some dummy data
            f.write(b'RIFF')
            f.write((36 + i * 1000).to_bytes(4, 'little'))  # File size
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))  # Chunk size
            f.write((1).to_bytes(2, 'little'))   # Audio format (PCM)
            f.write((1).to_bytes(2, 'little'))   # Channels
            f.write((44100).to_bytes(4, 'little'))  # Sample rate
            f.write((44100 * 2).to_bytes(4, 'little'))  # Byte rate
            f.write((2).to_bytes(2, 'little'))   # Block align
            f.write((16).to_bytes(2, 'little'))  # Bits per sample
            f.write(b'data')
            f.write((i * 1000).to_bytes(4, 'little'))  # Data size
            f.write(b'\x00' * (i * 1000))  # Dummy audio data
        
        # Set the file modification time
        os.utime(filepath, (timestamp, timestamp))
        
        # Get file size for display
        size = os.path.getsize(filepath)
        print(f"   Created {filename} ({size} bytes)")
    
    print(f"✅ Created {count} test audio files")

def test_cleanup_functionality():
    """Test the cleanup functionality"""
    print("🧪 Testing Nova's audio cleanup functionality...")
    
    # Create a temporary test directory
    test_dir = "test_audio_cache"
    
    try:
        # Create test files
        create_test_audio_files(test_dir, count=15)
        
        # Show initial state
        print(f"\n📊 Initial state:")
        files = list(Path(test_dir).glob("*.wav"))
        print(f"   Total files: {len(files)}")
        
        # Import and test the cleanup functionality
        try:
            from core.audio.interruption_monitor import InterruptionMonitor
            
            # Create a monitor instance
            monitor = InterruptionMonitor()
            
            # Test cleanup with different parameters
            print(f"\n🧹 Testing cleanup with max_files=5, max_age_hours=12:")
            
            # Temporarily change the working directory to test the cleanup
            original_cwd = os.getcwd()
            os.chdir(test_dir)
            
            try:
                deleted_count = monitor.cleanup_old_audio_files(
                    max_files=5, 
                    max_age_hours=12
                )
            finally:
                os.chdir(original_cwd)
            print(f"   Files deleted: {deleted_count}")
            
            # Show final state
            remaining_files = list(Path(test_dir).glob("*.wav"))
            print(f"\n📊 Final state:")
            print(f"   Remaining files: {len(remaining_files)}")
            
            if remaining_files:
                print("   Remaining files:")
                for file in sorted(remaining_files):
                    mtime = time.ctime(os.path.getmtime(file))
                    size = os.path.getsize(file)
                    print(f"     {file.name} - {mtime} - {size} bytes")
            
        except ImportError as e:
            print(f"❌ Could not import InterruptionMonitor: {e}")
            print("   This test requires Nova's core modules to be available")
        
    finally:
        # Clean up test directory
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"\n🧹 Cleaned up test directory: {test_dir}")

def test_manual_cleanup():
    """Test manual cleanup of the real audio_cache directory"""
    print("\n🧪 Testing manual cleanup of real audio_cache directory...")
    
    if not os.path.exists("audio_cache"):
        print("❌ audio_cache directory not found")
        return
    
    # Count current files
    files = list(Path("audio_cache").glob("interruption_*.wav"))
    print(f"📊 Current audio_cache state:")
    print(f"   Total interruption files: {len(files)}")
    
    if files:
        total_size = sum(os.path.getsize(f) for f in files)
        size_mb = total_size / (1024 * 1024)
        print(f"   Total size: {size_mb:.2f} MB")
        
        # Show oldest and newest files
        files_with_time = [(f, os.path.getmtime(f)) for f in files]
        files_with_time.sort(key=lambda x: x[1])
        
        if len(files_with_time) >= 2:
            oldest = files_with_time[0]
            newest = files_with_time[-1]
            print(f"   Oldest: {oldest[0].name} - {time.ctime(oldest[1])}")
            print(f"   Newest: {newest[0].name} - {time.ctime(newest[1])}")
    
    # Test cleanup
    try:
        from core.audio.interruption_monitor import InterruptionMonitor
        
        monitor = InterruptionMonitor()
        
        print(f"\n🧹 Running cleanup (max_files=10, max_age_hours=24):")
        deleted_count = monitor.cleanup_old_audio_files(max_files=10, max_age_hours=24)
        
        if deleted_count > 0:
            print(f"✅ Cleanup complete: {deleted_count} files deleted")
            
            # Show new state
            remaining_files = list(Path("audio_cache").glob("interruption_*.wav"))
            remaining_size = sum(os.path.getsize(f) for f in remaining_files)
            remaining_size_mb = remaining_size / (1024 * 1024)
            print(f"📊 New state: {len(remaining_files)} files, {remaining_size_mb:.2f} MB")
        else:
            print("✅ No files needed cleanup")
            
    except ImportError as e:
        print(f"❌ Could not import InterruptionMonitor: {e}")

if __name__ == "__main__":
    print("🎵 Nova Audio Cleanup Test")
    print("=" * 40)
    
    # Test with dummy files
    test_cleanup_functionality()
    
    # Test with real audio_cache directory
    test_manual_cleanup()
    
    print("\n🎉 Test complete!")
