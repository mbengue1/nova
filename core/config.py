"""
Configuration for Hey Nova MVP
Handles API keys, voice preferences, and core settings
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
        self.chunk_size = 1024
        self.record_seconds = 5
        
        # Porcupine settings
        self.picovoice_access_key = os.getenv("PICOVOICE_ACCESS_KEY", "")
        
        # llm settings
        self.llm_model = "gpt-4o-mini"  # openai model for natural language processing
        self.max_tokens = 150
        self.temperature = 0.7
        
        # persona prompt
        self.persona = """You are Nova, a helpful and friendly AI assistant. 
        You speak naturally and conversationally, like a British butler or personal assistant.
        Keep responses concise but warm. Always maintain your helpful personality."""
    
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

# Global config instance
config = NovaConfig()
