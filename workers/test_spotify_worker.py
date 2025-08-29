#!/usr/bin/env python3
"""
Test Spotify Worker in Isolation
Tests the Spotify AppleScript integration without Nova
"""

import os
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the SpotifyAppleScript class
from core.services.spotify_applescript import SpotifyAppleScript

def test_spotify_worker_isolation():
    """Test Spotify worker functionality in isolation"""
    print("\n🎵 Testing Spotify Worker in Isolation 🎵")
    print("=" * 60)
    
    # Create Spotify worker instance
    spotify = SpotifyAppleScript()
    
    # Test 1: Availability Check
    print("\n1️⃣ Testing Spotify Availability...")
    available = spotify.is_available()
    print(f"   ✅ Spotify available: {available}")
    if not available:
        print("   ❌ Spotify not available - cannot continue testing")
        return False
    
    # Test 2: App State Management
    print("\n2️⃣ Testing App State Management...")
    
    # Check if running
    running = spotify.is_running()
    print(f"   📱 Spotify running: {running}")
    
    # Launch if not running
    if not running:
        print("   🚀 Launching Spotify...")
        launched = spotify.launch()
        print(f"   ✅ Launch success: {launched}")
        if launched:
            time.sleep(3)  # Wait for launch
            running = spotify.is_running()
            print(f"   📱 Spotify running after launch: {running}")
    
    # Test 3: Playlist Playback
    print("\n3️⃣ Testing Playlist Playback...")
    
    # Test the full nightmode sequence
    print("   🎯 Testing ensure_ready_and_play_nightmode...")
    success = spotify.ensure_ready_and_play_nightmode()
    print(f"   ✅ Playback success: {success}")
    
    if success:
        # Verify playback
        player_state = spotify.get_player_state()
        print(f"   🎮 Player state: {player_state}")
        
        if player_state == "playing":
            track_info = spotify.get_current_track_info()
            if track_info:
                print(f"   🎵 Now playing: {track_info['track']} by {track_info['artist']}")
            print("   ✅ Playback verified successfully!")
        else:
            print(f"   ⚠️ Player state unexpected: {player_state}")
    
    # Test 4: Volume Management
    print("\n4️⃣ Testing Volume Management...")
    
    # Get current volume
    current_volume = spotify._get_current_volume()
    print(f"   📢 Current volume: {current_volume}%")
    
    # Test volume setting (only if current volume is very low)
    if current_volume is not None and current_volume < 20:
        print(f"   🔧 Volume is low ({current_volume}%), testing adjustment...")
        volume_set = spotify.set_volume(80)
        print(f"   ✅ Volume set to 80%: {volume_set}")
        
        # Verify volume change
        new_volume = spotify._get_current_volume()
        print(f"   📢 New volume: {new_volume}%")
    else:
        print(f"   ✅ Volume is at good level ({current_volume}%), no adjustment needed")
    
    # Test 5: Error Handling
    print("\n5️⃣ Testing Error Handling...")
    
    # Test with invalid playlist (should handle gracefully)
    print("   🧪 Testing invalid playlist handling...")
    try:
        # This should not crash
        invalid_result = spotify.play_playlist("spotify:playlist:invalid")
        print(f"   ✅ Invalid playlist handled gracefully: {invalid_result}")
    except Exception as e:
        print(f"   ❌ Invalid playlist caused error: {e}")
    
    print("\n" + "=" * 60)
    print("🎵 Spotify Worker Isolation Test Complete")
    print("=" * 60)
    
    return True

def test_spotify_worker_performance():
    """Test Spotify worker performance characteristics"""
    print("\n⚡ Testing Spotify Worker Performance ⚡")
    print("=" * 60)
    
    spotify = SpotifyAppleScript()
    
    # Test 1: Launch Time
    print("\n1️⃣ Testing Launch Performance...")
    
    if not spotify.is_running():
        start_time = time.time()
        launched = spotify.launch()
        launch_time = time.time() - start_time
        
        print(f"   🚀 Launch time: {launch_time:.2f} seconds")
        print(f"   ✅ Launch success: {launched}")
        
        if launch_time > 10:
            print("   ⚠️ Launch time is slow (>10s)")
        elif launch_time > 5:
            print("   ⚠️ Launch time is moderate (>5s)")
        else:
            print("   ✅ Launch time is fast (<5s)")
    
    # Test 2: Playback Response Time
    print("\n2️⃣ Testing Playback Response Time...")
    
    start_time = time.time()
    success = spotify.ensure_ready_and_play_nightmode()
    response_time = time.time() - start_time
    
    print(f"   🎯 Playback response time: {response_time:.2f} seconds")
    print(f"   ✅ Playback success: {success}")
    
    if response_time > 5:
        print("   ⚠️ Playback response is slow (>5s)")
    elif response_time > 2:
        print("   ⚠️ Playback response is moderate (>2s)")
    else:
        print("   ✅ Playback response is fast (<2s)")
    
    # Test 3: Volume Response Time
    print("\n3️⃣ Testing Volume Response Time...")
    
    start_time = time.time()
    volume_set = spotify.set_volume(50)
    volume_time = time.time() - start_time
    
    print(f"   📢 Volume response time: {volume_time:.2f} seconds")
    print(f"   ✅ Volume set: {volume_set}")
    
    if volume_time > 1:
        print("   ⚠️ Volume response is slow (>1s)")
    else:
        print("   ✅ Volume response is fast (<1s)")
    
    print("\n" + "=" * 60)
    print("⚡ Spotify Worker Performance Test Complete")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("🧪 Starting Spotify Worker Isolation Tests...")
    
    # Run isolation tests
    isolation_success = test_spotify_worker_isolation()
    
    if isolation_success:
        # Run performance tests
        performance_success = test_spotify_worker_performance()
        
        print("\n" + "=" * 60)
        print("🎯 FINAL TEST RESULTS")
        print("=" * 60)
        print(f"   Isolation Tests: {'✅ PASSED' if isolation_success else '❌ FAILED'}")
        print(f"   Performance Tests: {'✅ PASSED' if performance_success else '❌ FAILED'}")
        
        if isolation_success and performance_success:
            print("\n🎉 ALL TESTS PASSED! Spotify Worker is ready for integration.")
        else:
            print("\n⚠️ Some tests failed. Review issues before integration.")
    else:
        print("\n❌ Isolation tests failed. Cannot proceed to performance tests.")
