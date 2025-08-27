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
        
        # Try to import personal configuration
        try:
            from core.personal_config import (
                USER_NAME, USER_TITLE, GRADUATION_YEAR, LOCATION, TIMEZONE, MAJOR,
                COURSES, ACTIVITIES, CAREER_GOAL, PROJECTS, ACADEMIC_GOALS, INTERESTS
            )
            
            # Personal information from personal_config.py
            self.user_name = USER_NAME
            self.user_title = USER_TITLE
            self.graduation_year = GRADUATION_YEAR
            self.location = LOCATION
            self.timezone = TIMEZONE
            self.major = MAJOR
            
            # Academic schedule from personal_config.py
            self.courses = COURSES
            
            # Activities and interests from personal_config.py
            self.activities = ACTIVITIES
            
            # Goals and projects from personal_config.py
            self.career_goal = CAREER_GOAL
            self.projects = PROJECTS
            self.academic_goals = ACADEMIC_GOALS
            self.interests = INTERESTS
            
            print("✅ Personal configuration loaded")
        except ImportError:
            # Default values if personal_config.py doesn't exist
            print("⚠️  No personal configuration found, using defaults")
            
            # Default personal information
            self.user_name = "User"
            self.user_title = "Sir"
            self.graduation_year = "2026"
            self.location = "University of Rochester, Rochester, New York"
            self.timezone = "America/New_York"
            self.major = "Computer Science"
            
            # Default academic schedule (empty)
            self.courses = []
            
            # Default activities (empty)
            self.activities = []
            
            # Default goals and projects
            self.career_goal = "Success"
            self.projects = ["Nova AI Assistant"]
            self.academic_goals = ["Excel in courses"]
            self.interests = ["Technology"]
        
        # persona prompt
        self.persona = f"""You are Nova, a sophisticated AI assistant serving {self.user_name} at the University of Rochester.

        PERSONALITY:
        - Address {self.user_name} as "{self.user_title}" (e.g., "Good morning, {self.user_title}")
        - Speak with a refined British accent and manner
        - Be proactive, helpful, and slightly formal but warm
        - Show pride in {self.user_name}'s academic achievements (Class of {self.graduation_year})
        - Occasionally use appropriate humor to lighten the mood
        - Act as a professional assistant focused on productivity
        
        ACADEMIC CONTEXT:
        - {self.user_name} is studying {self.major} at {self.location}
        - Aware of {self.user_name}'s course schedule and professors
        - Understand the locations and timing of classes across campus
        - Recognize academic priorities and deadlines
        
        PERSONAL CONTEXT:
        - {self.user_name} plays basketball daily and values physical activity
        - Working on several projects including Nova, a sports betting application, and resume preparation
        - Career goal is in Software Engineering
        - Values productivity and professional growth
        
        CONTEXT AWARENESS:
        - You're located at {self.location}
        - Use Eastern Time (ET) for all time references
        - Know local weather patterns, campus life, and Rochester area
        - Understand university terminology and academic calendar
        
        RESPONSE STYLE:
        - Keep responses concise but informative
        - Always acknowledge {self.user_name} respectfully
        - Provide context-aware information when relevant
        - Maintain your sophisticated British personality
        - Prioritize information relevant to {self.user_name}'s schedule and goals"""
    
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
        from datetime import datetime
        import pytz
        
        try:
            # Get current time and day
            tz = pytz.timezone(self.timezone)
            current_time = datetime.now(tz)
            current_day = current_time.strftime("%A")
            
            # Find today's classes
            todays_classes = []
            for course in self.courses:
                if current_day in course["days"]:
                    todays_classes.append({
                        "name": course["name"],
                        "code": course["code"],
                        "time": course["time"],
                        "location": course["location"],
                        "professor": course["professor"]
                    })
            
            # Get today's activities
            todays_activities = []
            for activity in self.activities:
                if activity["frequency"] == "daily" or current_day in activity.get("days", []):
                    todays_activities.append(activity)
            
            return {
                "user_name": self.user_name,
                "user_title": self.user_title,
                "graduation_year": self.graduation_year,
                "location": self.location,
                "timezone": self.timezone,
                "major": self.major,
                "current_day": current_day,
                "current_time": current_time.strftime("%I:%M %p"),
                "todays_classes": todays_classes,
                "todays_activities": todays_activities,
                "projects": self.projects,
                "academic_goals": self.academic_goals,
                "interests": self.interests,
                "career_goal": self.career_goal
            }
        except Exception as e:
            print(f"Error getting personal context: {e}")
            # Return basic context if there's an error
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
            current_day = current_time.strftime("%A")
            time_greeting = self._get_time_greeting(current_time.hour)
            
            # Find today's classes
            todays_classes = []
            for course in self.courses:
                if current_day in course["days"]:
                    todays_classes.append(f"{course['name']} ({course['code']}) at {course['time']} in {course['location']}")
            
            # Check if basketball practice is today (it's daily)
            activities_today = []
            for activity in self.activities:
                if activity["frequency"] == "daily" or current_day in activity.get("days", []):
                    activities_today.append(f"{activity['name']} at {activity['time']} in {activity['location']}")
            
            # Build schedule context
            schedule_context = "No classes or activities scheduled for today."
            if todays_classes or activities_today:
                schedule_items = []
                if todays_classes:
                    schedule_items.append(f"Classes today: {', '.join(todays_classes)}")
                if activities_today:
                    schedule_items.append(f"Activities today: {', '.join(activities_today)}")
                schedule_context = " ".join(schedule_items)
            
            return f"""{self.persona}
            
            CURRENT CONTEXT:
            - Current time: {current_time.strftime('%I:%M %p ET')}
            - Today is: {current_day}
            - Greeting: {time_greeting}
            - Location: {self.location}
            - Academic year: {self.graduation_year}
            - Major: {self.major}
            - {schedule_context}
            - Current projects: {', '.join(self.projects)}
            - Career focus: {self.career_goal}
            
            CONVERSATION GUIDANCE:
            - If {self.user_name} has classes today, be ready to provide schedule information
            - Acknowledge {self.user_name}'s basketball practice if it's happening today
            - Be aware of {self.user_name}'s projects and offer relevant support
            - Remember to always address {self.user_name} as "{self.user_title}" and provide context-aware information
            - Occasionally use appropriate humor while maintaining professionalism"""
        except Exception as e:
            print(f"Error generating enhanced persona: {e}")
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
