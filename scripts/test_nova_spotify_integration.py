#!/usr/bin/env python3
"""
Test Nova's Spotify Integration

This script tests:
1. Spotify skill integration in NovaBrain
2. Welcome greeting with Spotify
3. Command processing through the integrated system
"""

import sys
import os
from dotenv import load_dotenv

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_spotify_skill_integration():
    """Test if Spotify skill is properly integrated into NovaBrain"""
    print("🔍 Testing Spotify Skill Integration in NovaBrain...")
    
    try:
        from core.brain.router import NovaBrain
        
        # Initialize NovaBrain
        brain = NovaBrain()
        print("✅ NovaBrain initialized successfully")
        
        # Test Spotify command recognition
        test_commands = [
            "Play some music",
            "Start my nightmode playlist",
            "Pause the music",
            "What's currently playing?",
            "Show me my playlists"
        ]
        
        print("\n🎵 Testing Spotify Command Recognition:")
        for cmd in test_commands:
            response = brain.process_input(cmd)
            print(f"  📝 '{cmd}' → {response[:100]}{'...' if len(response) > 100 else ''}")
        
        print("\n✅ Spotify skill integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Spotify skill integration test failed: {e}")
        return False

def test_welcome_greeting_spotify():
    """Test welcome greeting with Spotify integration"""
    print("\n🔍 Testing Welcome Greeting with Spotify...")
    
    try:
        from core.main import HeyNova
        
        # Initialize Nova (this will test the welcome greeting)
        print("  🚀 Initializing Nova...")
        nova = HeyNova()
        
        # Test the welcome greeting method directly
        print("  🎭 Testing welcome greeting method...")
        nova._welcome_greeting()
        
        print("✅ Welcome greeting with Spotify test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Welcome greeting with Spotify test failed: {e}")
        return False

def test_spotify_service_availability():
    """Test if Spotify service is available and working"""
    print("\n🔍 Testing Spotify Service Availability...")
    
    try:
        from core.services.spotify_service import SpotifyService
        
        spotify = SpotifyService()
        
        # Check if service is available
        if spotify.is_available():
            print("✅ Spotify service is available")
            
            # Test playlist finding
            playlist = spotify.find_playlist_by_name("Nightmode")
            if playlist:
                print(f"✅ Found playlist: {playlist['name']} ({playlist['tracks']['total']} tracks)")
            else:
                print("⚠️  Nightmode playlist not found")
                
            # Test user profile
            profile = spotify.get_user_profile()
            if profile:
                print(f"✅ User profile: {profile['display_name']}")
            else:
                print("⚠️  Could not get user profile")
                
        else:
            print("❌ Spotify service is not available")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Spotify service test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("🎵 NOVA SPOTIFY INTEGRATION TEST SUITE")
    print("="*60)
    
    # Load environment variables
    load_dotenv()
    
    # Run tests
    tests = [
        ("Spotify Service", test_spotify_service_availability),
        ("Spotify Skill Integration", test_spotify_skill_integration),
        ("Welcome Greeting with Spotify", test_welcome_greeting_spotify)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Nova's Spotify integration is working perfectly!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
