#!/usr/bin/env python3
"""
Test script for Spotify integration with Nova

This script tests:
1. Spotify authentication
2. Basic API functionality
3. Playlist management
4. Playback control
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path so we can import the core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_spotify_integration():
    """Test Spotify integration functionality"""
    print("===== Testing Spotify Integration =====\n")
    
    try:
        # Test importing Spotify services
        print("🔍 Testing Spotify service imports...")
        from core.services.spotify_service import SpotifyService
        from core.services.spotify_auth import SpotifyAuth
        print("✅ Spotify services imported successfully")
        
        # Test Spotify authentication
        print("\n🔍 Testing Spotify authentication...")
        spotify = SpotifyService()
        
        if spotify.is_available():
            print("✅ Spotify already authenticated")
        else:
            print("🔐 Spotify authentication required...")
            if spotify.authenticate():
                print("✅ Spotify authentication successful")
            else:
                print("❌ Spotify authentication failed")
                return False
        
        # Test basic API functionality
        print("\n🔍 Testing basic Spotify API functionality...")
        
        # Get user profile
        profile = spotify.get_user_profile()
        if profile:
            print(f"✅ User profile: {profile.get('display_name', 'Unknown')}")
            print(f"   Email: {profile.get('email', 'Not provided')}")
            print(f"   Country: {profile.get('country', 'Not provided')}")
        else:
            print("❌ Failed to get user profile")
        
        # Get available devices
        devices = spotify.get_available_devices()
        if devices:
            print(f"✅ Available devices: {len(devices)}")
            for device in devices:
                print(f"   • {device['name']} ({device['type']}) - {'Active' if device['is_active'] else 'Inactive'}")
        else:
            print("⚠️ No Spotify devices available")
        
        # Get user playlists
        playlists = spotify.get_user_playlists()
        if playlists:
            print(f"✅ User playlists: {len(playlists)}")
            print("   First 5 playlists:")
            for i, playlist in enumerate(playlists[:5]):
                print(f"   • {playlist['name']} ({playlist['tracks']['total']} tracks)")
        else:
            print("❌ Failed to get user playlists")
        
        # Test playlist search
        print("\n🔍 Testing playlist search...")
        default_playlist = os.getenv('SPOTIFY_DEFAULT_PLAYLIST', 'Nightmode')
        playlist = spotify.find_playlist_by_name(default_playlist)
        
        if playlist:
            print(f"✅ Found default playlist: {playlist['name']}")
            print(f"   Tracks: {playlist['tracks']['total']}")
            print(f"   Public: {'Yes' if playlist['public'] else 'No'}")
            
            # Get playlist details
            playlist_info = spotify.get_playlist_info(default_playlist)
            if playlist_info:
                print(f"   Description: {playlist_info.get('description', 'No description')}")
                
                # Get first few tracks
                tracks = spotify.get_playlist_tracks(default_playlist)
                if tracks:
                    print(f"   Sample tracks:")
                    for i, track in enumerate(tracks[:3]):
                        print(f"     • {track['name']} by {track['artist']}")
        else:
            print(f"⚠️ Default playlist '{default_playlist}' not found")
            print("   Available playlists:")
            for playlist in playlists[:5]:
                print(f"   • {playlist['name']}")
        
        # Test current playback status
        print("\n🔍 Testing playback status...")
        playback = spotify.get_current_playback()
        if playback:
            if playback.get('is_playing'):
                track = playback.get('item')
                if track:
                    artist = track['artists'][0]['name'] if track['artists'] else 'Unknown'
                    print(f"✅ Currently playing: {track['name']} by {artist}")
                else:
                    print("✅ Music is playing (no track info)")
            else:
                print("⏸️ Playback is paused")
        else:
            print("ℹ️ No active playback")
        
        print("\n===== Spotify Integration Test Complete =====")
        print("🎵 Ready to integrate with Nova's greeting system!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_spotify_integration()
    sys.exit(0 if success else 1)
