"""
Configuration Manager for Hey Nova

This module manages all configuration settings for the Nova assistant:
1. API keys and credentials (OpenAI, Azure, Picovoice)
2. Voice and audio settings (TTS voice, rate, pitch)
3. VAD parameters for natural conversation detection
4. LLM settings for response generation
5. Personalization settings (user name, title, location)

The configuration is loaded from environment variables (.env file)
and provides a centralized way to access and validate all settings.
It also generates enhanced persona prompts for the LLM with current
context (time of day, location, etc.) for more natural interactions.

Future enhancements:
- User-editable configuration via web interface
- Profile switching for different users or contexts
- Dynamic configuration updates without restart
- Secure credential storage using system keychain
- Configuration backup and sync across devices
"""
import os
from pathlib import Path
from typing import Optional

class NovaConfig:
    """Configuration manager for Hey Nova"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".nova"
        self.config_file = self.config_dir / "config.json"
        self.env_file = Path(".env")
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Load environment variables
        self._load_env()
        
        # default settings
        self.wake_word = "hey nova"
        self.voice_name = "Victoria"  # macos british voice for natural speech
        self.voice_rate = 0.6  # speech rate adjustment (0.1 to 2.0)
        self.voice_pitch = 1.1  # pitch adjustment (0.5 to 2.0)
        
        # Audio settings
        self.sample_rate = 16000
        self.chunk_size = 512  # smaller chunks for faster processing
        
        # Voice Activity Detection settings (Phase 2 - Hysteresis + Preroll/Postroll)
        self.vad_enabled = True
        self.vad_frame_duration = 30  # milliseconds per frame (480 samples @ 16kHz)
        self.vad_on_threshold = 0.30  # speech probability threshold to enter speech (LOWERED)
        self.vad_off_threshold = 0.20  # speech probability threshold to exit speech (LOWERED)
        self.vad_enter_consec = 2  # consecutive frames needed to enter speech (REDUCED)
        self.vad_exit_consec = 6  # consecutive frames needed to exit speech (REDUCED)
        self.vad_preroll_ms = 200  # milliseconds to capture before speech (REDUCED)
        self.vad_postroll_ms = 300  # milliseconds to capture after speech (REDUCED)
        self.vad_max_utterance_ms = 12000  # maximum utterance length
        self.vad_aggressiveness = 1  # webrtcvad aggressiveness (0-3) - MORE SENSITIVE
        self.vad_timeout = 15  # maximum seconds to listen before timeout
        
        # Legacy recording (fallback)
        self.record_seconds = 5
        
        # Porcupine settings
        self.picovoice_access_key = os.getenv("PICOVOICE_ACCESS_KEY", "")
        
        # llm settings
        self.llm_model = "gpt-4o-mini"  # openai model for natural language processing
        self.max_tokens = 100  # shorter responses for faster processing
        self.temperature = 0.5  # more focused responses
        
        # personal information
        self.user_name = "Mouhamed"
        self.user_title = "Sir"
        self.graduation_year = "2026"
        self.location = "University of Rochester, Rochester, New York"
        self.timezone = "America/New_York"
        
        # persona prompt
        self.persona = f"""You are Nova, a sophisticated AI assistant serving {self.user_name} at the University of Rochester.

        PERSONALITY:
        - Address {self.user_name} as "{self.user_title}" (e.g., "Good morning, {self.user_title}")
        - Speak with a refined British accent and manner
        - Be proactive, helpful, and slightly formal but warm
        - Show pride in {self.user_name}'s academic achievements (Class of {self.graduation_year})
        
        CONTEXT AWARENESS:
        - You're located at {self.location}
        - Use Eastern Time (ET) for all time references
        - Know local weather patterns, campus life, and Rochester area
        - Understand university terminology and academic calendar
        
        RESPONSE STYLE:
        - Keep responses concise but informative
        - Always acknowledge {self.user_name} respectfully
        - Provide context-aware information when relevant
        - Maintain your sophisticated British personality"""
    
    def _load_env(self):
        """Load environment variables from .env file"""
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from environment"""
        return os.getenv("OPENAI_API_KEY")
    
    @property
    def notion_api_key(self) -> Optional[str]:
        """Get Notion API key from environment"""
        return os.getenv("NOTION_API_KEY")
    
    @property
    def notion_database_id(self) -> Optional[str]:
        """Get Notion database ID from environment"""
        return os.getenv("NOTION_DATABASE_ID")
    
    def validate_config(self) -> bool:
        """Validate that required configuration is present"""
        if not self.openai_api_key:
            print("⚠️  Warning: OPENAI_API_KEY not found in environment")
            print("   Nova will work but LLM responses will be limited")
            return False
        return True
    
    def get_voice_settings(self) -> dict:
        """Get voice configuration for TTS"""
        return {
            "voice": self.voice_name,
            "rate": self.voice_rate,
            "pitch": self.voice_pitch
        }
    
    def get_personal_context(self) -> dict:
        """Get personal context for enhanced responses"""
        return {
            "user_name": self.user_name,
            "user_title": self.user_title,
            "graduation_year": self.graduation_year,
            "location": self.location,
            "timezone": self.timezone
        }
    
    def get_enhanced_persona(self) -> str:
        """Get enhanced persona with current context"""
        from datetime import datetime
        import pytz
        
        try:
            # get current time in user's timezone
            tz = pytz.timezone(self.timezone)
            current_time = datetime.now(tz)
            time_greeting = self._get_time_greeting(current_time.hour)
            
            return f"""{self.persona}
            
            CURRENT CONTEXT:
            - Current time: {current_time.strftime('%I:%M %p ET')}
            - Greeting: {time_greeting}
            - Location: {self.location}
            - Academic year: {self.graduation_year}
            
            Remember to always address {self.user_name} as "{self.user_title}" and provide context-aware information."""
        except:
            return self.persona
    
    def _get_time_greeting(self, hour: int) -> str:
        """Get appropriate greeting based on time of day"""
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        elif 17 <= hour < 21:
            return "Good evening"
        else:
            return "Good night"

# Global config instance
config = NovaConfig()
