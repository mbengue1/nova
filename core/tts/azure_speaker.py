"""
Azure Text-to-Speech using Azure Cognitive Services
Provides high-quality neural voices including Libby (British female)
"""
import os
import azure.cognitiveservices.speech as speechsdk
from typing import Optional
from config import config

class AzureSpeechSynthesizer:
    """High-quality TTS using Azure Speech Service"""
    
    def __init__(self):
        self.speech_config = None
        self.voice_name = "en-GB-LibbyNeural"  # British female voice
        
        # initialize azure speech configuration
        try:
            azure_key = os.getenv("AZURE_SPEECH_KEY")
            azure_region = os.getenv("AZURE_SPEECH_REGION")
            
            if azure_key and azure_region:
                self.speech_config = speechsdk.SpeechConfig(
                    subscription=azure_key, 
                    region=azure_region
                )
                
                # configure voice and speech properties
                self.speech_config.speech_synthesis_voice_name = self.voice_name
                self.speech_config.speech_synthesis_speaking_rate = 1.0  # normal speed
                
                print(f"✅ Azure TTS initialized with voice: {self.voice_name}")
            else:
                print("⚠️  Azure credentials not found in environment")
                self.speech_config = None
                
        except Exception as e:
            print(f"⚠️  Could not initialize Azure TTS: {e}")
            self.speech_config = None
    
    def speak(self, text: str, voice: str = None, rate: float = None, pitch: float = None) -> bool:
        """Convert text to speech using Azure"""
        if not self.speech_config:
            print("❌ Azure TTS not initialized")
            return False
        
        if not text.strip():
            return False
        
        try:
            # update voice if specified
            if voice:
                self.speech_config.speech_synthesis_voice_name = voice
            
            # update speaking rate if specified
            if rate:
                # azure rate: 0.5 = slow, 2.0 = fast
                self.speech_config.speech_synthesis_speaking_rate = rate
            
            # create speech synthesizer instance
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config
            )
            
            print(f"🗣️  Azure TTS Speaking: '{text}'")
            print(f"   Voice: {self.speech_config.speech_synthesis_voice_name}")
            print(f"   Rate: {self.speech_config.speech_synthesis_speaking_rate}")
            
            # synthesize speech from text
            result = speech_synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print("✅ Azure TTS completed successfully")
                return True
            else:
                print(f"❌ Azure TTS failed: {result.reason}")
                return False
                
        except Exception as e:
            print(f"Error in Azure TTS: {e}")
            return False
    
    def speak_async(self, text: str, voice: str = None, rate: float = None, pitch: float = None):
        """Speak text asynchronously"""
        import threading
        
        def _speak_thread():
            self.speak(text, voice, rate, pitch)
        
        thread = threading.Thread(target=_speak_thread)
        thread.daemon = True
        thread.start()
    
    def get_available_voices(self) -> list:
        """Get list of available Azure voices"""
        if not self.speech_config:
            return []
        
        try:
            # This would require additional API calls to get voice list
            # For now, return common British voices
            return [
                "en-GB-LibbyNeural",      # British female (default)
                "en-GB-SoniaNeural",      # British female
                "en-GB-RyanNeural",       # British male
                "en-GB-AbbiNeural",       # British female
                "en-GB-BellaNeural"       # British female
            ]
        except Exception as e:
            print(f"Error getting voices: {e}")
            return []
    
    def get_voice_info(self) -> dict:
        """Get information about current voice configuration"""
        return {
            "current_voice": self.voice_name,
            "current_rate": getattr(self.speech_config, 'speech_synthesis_speaking_rate', 1.0) if self.speech_config else 1.0,
            "current_pitch": 1.0,  # Azure handles pitch automatically
            "available_voices": self.get_available_voices(),
            "system": "Azure Cognitive Services"
        }
    
    def is_available(self) -> bool:
        """Check if Azure TTS is available"""
        return self.speech_config is not None
