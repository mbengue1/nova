"""
Nova's Brain - Command Router and Intelligence Core

This module serves as the central intelligence hub for Nova:
1. Routes commands to appropriate skills based on pattern matching
2. Provides LLM-powered conversational responses with personalization
3. Maintains conversation history for context-aware interactions
4. Implements streaming responses for natural conversation flow
5. Handles skill execution for app control, system info, and more

The router uses a hybrid approach - first attempting to match commands
to specific skills, then falling back to the LLM for general queries.
Math queries are routed directly to the LLM for better accuracy.

Skills currently implemented:
- App control (open/launch applications)
- System information (time, date, battery, volume)
- Notion integration (stubbed for MVP)

Future enhancements:
- Dynamic skill discovery and loading
- Multi-step skill workflows
- Memory integration for long-term context
- Proactive suggestions based on user patterns
- Fine-tuned local models for privacy-sensitive tasks
"""
import re
import openai
import sys
import os
from typing import Optional, Dict, Any, List

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import config

class NovaBrain:
    """Main brain that routes commands and generates responses"""
    
    def __init__(self):
        self.conversation_history = []
        self.skills = {}
        self.openai_client = None
        
        # Initialize OpenAI client if API key is available
        if config.openai_api_key:
            try:
                openai.api_key = config.openai_api_key
                self.openai_client = openai
                print("✅ OpenAI client initialized")
            except Exception as e:
                print(f"⚠️  Warning: Could not initialize OpenAI: {e}")
        else:
            print("⚠️  Warning: No OpenAI API key found")
            print("   Nova will use skills only (no conversational responses)")
        
        # Define skill patterns
        self._setup_skill_patterns()
        
        # Initialize skills
        self._initialize_skills()
    
    def _initialize_skills(self):
        """Initialize skill instances"""
        # Import skills only when needed to avoid circular imports
        from core.skills.notes_skill import NotesSkill
        from core.skills.focus_skill import FocusSkill
        from core.skills.spotify_skill import SpotifySkill
        from core.services.app_control_service import AppControlService
        from core.services.spotify_service import SpotifyService
        
        # Create shared services
        app_control_service = AppControlService()
        
        # Store skill instances
        self.skill_instances = {
            'notes': NotesSkill(),
            'focus': FocusSkill(app_control_service),
            'spotify': SpotifySkill(SpotifyService())
        }
    
    def _setup_skill_patterns(self):
        """Setup patterns for skill detection"""
        self.skill_patterns = {
            'app_control': [
                # Basic app opening commands
                r'\b(open|launch|start|run)\s+(vscode|code|visual\s+studio|chrome|safari|firefox|terminal|finder|mail|messages|slack|discord|spotify|music|calculator|notes|reminders|calendar|photos|preview|textedit|pages|numbers|keynote)\b',
                r'\b(open|launch|start|run)\s+(visual\s+studio\s+code|vs\s+code)\b',
                
                # Polite requests
                r'\b(can\s+you\s+open|could\s+you\s+open|please\s+open|would\s+you\s+open)\s+(vscode|code|visual\s+studio|chrome|safari|firefox|terminal|finder|mail|messages|slack|discord|spotify|music|calculator|notes|reminders|calendar|photos|preview|textedit|pages|numbers|keynote)\b',
                r'\b(can\s+you\s+launch|could\s+you\s+launch|please\s+launch|would\s+you\s+launch)\s+(vscode|code|visual\s+studio|chrome|safari|firefox|terminal|finder|mail|messages|slack|discord|spotify|music|calculator|notes|reminders|calendar|photos|preview|textedit|pages|numbers|keynote)\b',
                r'\b(can\s+you\s+start|could\s+you\s+start|please\s+start|would\s+you\s+start)\s+(vscode|code|visual\s+studio|chrome|safari|firefox|terminal|finder|mail|messages|slack|discord|spotify|music|calculator|notes|reminders|calendar|photos|preview|textedit|pages|numbers|keynote)\b',
                
                # Web browser specific commands
                r'\b(open|launch|start)\s+(a\s+new\s+tab|a\s+new\s+page|a\s+browser\s+tab|the\s+internet|the\s+web|internet|web|a\s+website|google)\b',
                r'\b(open|launch|start|go\s+to)\s+(google|gmail|youtube|facebook|twitter|instagram|amazon|netflix|hulu|spotify)\b',
                r'\b(browse|browse\s+to|navigate\s+to|surf\s+to|visit)\s+(google|gmail|youtube|facebook|twitter|instagram|amazon|netflix|hulu|spotify)\b',
                r'\b(can\s+you\s+browse|could\s+you\s+browse|please\s+browse|would\s+you\s+browse)\s+to\b',
                r'\b(can\s+you\s+open|could\s+you\s+open|please\s+open|would\s+you\s+open)\s+(a\s+new\s+tab|a\s+new\s+page|a\s+browser|the\s+internet|the\s+web|a\s+website)\b',
                
                # Common voice transcription variations
                r'\b(opened|opened up|lunch|launched|opening|running)\s+(vscode|code|visual\s+studio|chrome|safari|firefox|terminal|finder|mail|messages|slack|discord|spotify|music|calculator|notes|reminders|calendar|photos|preview|textedit|pages|numbers|keynote)\b',
                
                # More flexible patterns for voice commands
                r'\b(open|launch|start|run)\s+.{0,10}\s+(chrome|safari|firefox|browser)\b',
                r'\b(open|launch|start|run)\s+.{0,10}\s+(calculator|calendar|terminal|finder)\b',
                
                # Common misheard app names
                r'\b(open|launch|start|run)\s+(from|brom|crome|crime|chrom)\b',  # Chrome variations
                r'\b(open|launch|start|run)\s+(safar|safari|supply)\b',  # Safari variations
                r'\b(open|launch|start|run)\s+(firefox|fox|fire|fox fire)\b',  # Firefox variations
                r'\b(open|launch|start|run)\s+(terminal|term|termina)\b',  # Terminal variations
                r'\b(open|launch|start|run)\s+(find|finder|find her|find or)\b',  # Finder variations
                r'\b(open|launch|start|run)\s+(calc|calculator|calculation|calculate)\b',  # Calculator variations
                
                # System apps
                r'\b(open|launch|start|run)\s+(settings|preferences|system\s+settings|system\s+preferences)\b',
                
                # Very short commands
                r'^(chrome|safari|firefox|browser|terminal|finder|calculator)$',  # Just the app name
                r'^(open|launch|start|run)$'  # Just the action (will be handled by the fallback detection)
            ],
            'system_info': [
                r'\b(time|date|current\s+time|what\s+time|what\s+date|battery|volume|brightness|wifi|network|status)\b',
                r'\b(how\s+much\s+battery|what\s+is\s+the\s+time|system\s+info)\b'
            ],
            'calendar': [
                r'\b(what|show|tell|check).*(schedule|agenda|plan|calendar|event|class|have).*(today|tomorrow|week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
                r'\b(today\'s|todays|tomorrow\'s|tomorrows).*(schedule|agenda|plan|calendar|event|class)\b',
                r'\b(this|the|upcoming|next).*(week\'s|weeks).*(schedule|agenda|plan|calendar|event|class)\b',
                r'\bwhat.*(do|have).*i.*(today|tomorrow)\b',
                r'\b(what|anything|something).*(scheduled|planned|on|in).*(today|tomorrow|calendar)\b',
                r'\b(do\s+i\s+have|is\s+there).*(anything|something|events|meetings|classes).*(today|tomorrow|this\s+week)\b',
                r'\b(what\'s|what\s+is).*(on|in).*(my\s+calendar|my\s+schedule|my\s+agenda)\b'
            ],
            # Redirect Notion queries to calendar skill
            'calendar_redirect': [
                r'\b(tasks|todo|notion|what\'s\s+on\s+my\s+plate)\b',
                r'\b(show\s+me\s+my|read\s+my|check\s+my)\s+(tasks)\b'
            ],
            'notes': [
                # Create note patterns
                r'\b(create|make|start|new)\s+(a\s+)?(new\s+)?(note|notes)\b',
                r'\b(create|make|start|new)\s+(a\s+)?(new\s+)?(note|notes)\s+(called|named|titled|with\s+title)\b',
                r'\b(create|make|start|new)\s+(a\s+)?(new\s+)?(note|notes)\s+for\b',
                r'\b(create|make|start|new)\s+(a\s+)?(new\s+)?(shopping\s+list|grocery\s+list|to-do\s+list|todo\s+list)\b',
                
                # Add to note patterns
                r'\badd\s+(to|in|into)\s+(my\s+)?(note|notes|shopping\s+list|grocery\s+list)\b',
                r'\badd\s+(.*)\s+to\s+(my\s+)?(note|notes|shopping\s+list|grocery\s+list)\b',
                r'\b(put|place|write|jot\s+down)\s+(.*)\s+(in|into|to)\s+(my\s+)?(note|notes|shopping\s+list|grocery\s+list)\b',
                r'\bupdate\s+(my\s+)?(note|notes|shopping\s+list|grocery\s+list)\b',
                
                # Find note patterns
                r'\b(find|search\s+for|look\s+for)\s+(my\s+)?(note|notes)\b',
                r'\b(find|search\s+for|look\s+for)\s+(.*)\s+(in|from)\s+(my\s+)?(note|notes)\b',
                r'\b(show|list|display)\s+(my\s+)?(note|notes|all\s+notes)\b'
            ],
            'focus': [
                # Enable DND patterns
                r'\b(enable|turn\s+on|activate|set)\s+(do\s+not\s+disturb|dnd)\b',
                
                # Disable DND patterns
                r'\b(disable|turn\s+off|deactivate)\s+(do\s+not\s+disturb|dnd)\b',
                
                # Toggle DND patterns
                r'\b(toggle|switch)\s+(do\s+not\s+disturb|dnd)\b',
                
                # Get focus patterns
            ],
            'spotify': [
                # Play music commands
                r'\b(play|start)\s+(?:some\s+)?(?:music|tunes?)\b',
                r'\b(play|start)\s+(?:my\s+)?(?:playlist\s+)?([a-zA-Z0-9\s\-_]+?)(?:\s+playlist)?(?:\s+on\s+spotify)?\b',
                r'\b(play|start)\s+(?:the\s+)?([a-zA-Z0-9\s\-_]+?)(?:\s+playlist)?(?:\s+on\s+spotify)?\b',
                
                # Playback control
                r'\b(pause|stop|resume|next|previous|skip)\s+(?:the\s+)?(?:music|track|song)\b',
                r'\b(volume|louder|quieter|softer)\b',
                r'\bset\s+volume\s+to\s+\d+%?\b',
                
                # Information requests
                r'\bwhat(?:\'s|\s+is)\s+(?:currently\s+)?playing\b',
                r'\bwhat\s+playlists?\s+do\s+i\s+have\b',
                r'\bshow\s+me\s+my\s+playlists?\b',
                
                # Context music
                r'\bplay\s+something\s+(?:relaxing|energetic|calm|chill)\b',
                r'\bplay\s+music\s+for\s+(?:studying|working\s+out|background)\b',
                r'\bi\s+need\s+(?:some\s+)?background\s+music\b',
                
                # Help and general
                r'\b(?:can\s+you|do\s+you\s+know\s+how\s+to)\s+(?:play\s+music|control\s+spotify)\b',
                r'\bhelp\s+me\s+with\s+music\b',
                r'\bmusic\s+help\b'
            ],
            'focus': [
                # Enable DND patterns
                r'\b(enable|turn\s+on|activate|set)\s+(do\s+not\s+disturb|dnd)\b',
                
                # Disable DND patterns
                r'\b(disable|turn\s+off|deactivate)\s+(do\s+not\s+disturb|dnd)\b',
                
                # Toggle DND patterns
                r'\b(toggle|switch)\s+(do\s+not\s+disturb|dnd)\b',
                
                # Get focus patterns
                r'\b(what(?:\'s)?|which|get|check|is)\s+(my|the|if)?\s+(focus\s+mode|current\s+focus|do\s+not\s+disturb|dnd)\b',
                
                # Set focus patterns
                r'\b(set|change|switch)\s+(my|the)\s+focus\s+(to|mode)\b',
                
                # Private mode patterns
                r'\b(set|enable|turn\s+on)\s+(private\s+mode|privacy\s+mode|home\s+to\s+private)\b',
                
                # Set home/mode to DND patterns
                r'\b(set)\s+(home|mode|mac|macbook)\s+(to)\s+(do\s+not\s+disturb|dnd)\b',
                
                # Disable all focus patterns
                r'\b(disable|turn\s+off|deactivate)\s+(all|every)\s+(focus|mode)\b'
            ],
            'math': [
                r'\b(calculate|compute|what\s+is|math|add|subtract|multiply|divide|plus|minus|times|divided\s+by)\b',
                r'\b(\d+\s*[\+\-\*\/]\s*\d+|\d+\s+plus\s+\d+|\d+\s+minus\s+\d+)\b'
            ]
        }
    
    def process_input(self, user_input: str, stream: bool = False):
        """Process user input and return appropriate response
        
        Args:
            user_input: The user's input text
            stream: If True, returns a generator that yields response chunks
        
        Returns:
            If stream=False: A string containing the full response
            If stream=True: A generator that yields response chunks as they arrive
        """
        if not user_input.strip():
            return "I didn't catch that. Could you please repeat?"
        
        # 1. Check for conversation closure signals (only standalone phrases)
        closure_phrases = [
            "that's all", "that'll be all", 
            "that will be all", "that's it", "that is all", 
            "that's all i need", "that's all for now"
        ]
        
        # Simple thank you phrases (when used alone)
        simple_thanks = ["thank you", "thanks"]
        
        is_closure = False
        user_input_lower = user_input.lower()
        
        # Check if this is just a simple thank you without a question
        contains_question = any(q in user_input_lower for q in ["?", "what", "when", "where", "how", "who", "which", "can", "could", "would", "will", "do i", "am i", "is there"])
        
        # Detect if this is a conversation closure phrase
        for phrase in closure_phrases:
            if phrase in user_input_lower:
                is_closure = True
                break
                
        # Only treat thank you as closure if it's not part of a question
        if not is_closure and not contains_question:
            for phrase in simple_thanks:
                # Check if the input is primarily just a thank you
                # (allowing for minor additions like "thank you nova" or "thanks so much")
                if phrase in user_input_lower and len(user_input_lower.split()) < 5:
                    is_closure = True
                    break
        
        # Add user input to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # 2. Handle conversation closure with a polite acknowledgment
        if is_closure:
            acknowledgment = "Very good, Sir. I'll be here if you need anything else."
            self.conversation_history.append({"role": "assistant", "content": acknowledgment})
            return acknowledgment
        
        # 3. Prioritize app control commands (e.g., "open Chrome")
        # This ensures Nova can actually control apps even in conversational context
        app_control_match = False
        
        # Enhanced logging for app control detection
        print(f"🔍 Checking if input is app control command: '{user_input}'")
        
        # Check if this is an app control command using regex patterns
        for pattern in self.skill_patterns['app_control']:
            if re.search(pattern, user_input_lower):
                app_control_match = True
                matched_pattern = pattern
                print(f"✅ App control pattern matched: '{matched_pattern}'")
                break
        
        # Special handling for common voice transcription errors with app names
        app_keywords = ['open', 'launch', 'start', 'run']
        if any(keyword in user_input_lower for keyword in app_keywords):
            print(f"🔍 App action keyword detected, checking for app names...")
            # This might be an app control command that wasn't matched by the patterns
            words = user_input_lower.split()
            for i, word in enumerate(words):
                if word in app_keywords and i < len(words) - 1:
                    potential_app = words[i+1]
                    print(f"🔍 Potential app name detected: '{potential_app}'")
                    # Force app control match for common apps that might be misheard
                    if potential_app in ['chrome', 'safari', 'firefox', 'browser', 'finder', 'terminal', 'calculator', 'calendar']:
                        app_control_match = True
                        print(f"✅ Forced app control match for: '{potential_app}'")
                        break
        
        # Execute app control commands directly
        if app_control_match:
            print(f"🚀 Executing app control for: '{user_input}'")
            skill_response = self._handle_app_control(user_input)
            self.conversation_history.append({"role": "assistant", "content": skill_response})
            return skill_response
        
        # For other skills, use the normal detection
        skill_response = self._try_skills(user_input)
        if skill_response:
            # Add skill response to history
            self.conversation_history.append({"role": "assistant", "content": skill_response})
            return skill_response
        
        # Fallback to LLM if available
        if self.openai_client:
            # If streaming is requested, return a generator
            if stream:
                return self._get_llm_response(user_input, stream=True)
            
            # Otherwise, get the full response
            llm_response = self._get_llm_response(user_input)
            if llm_response:
                # Note: When not streaming, we add response to history in _get_llm_response
                return llm_response
        
        # Final fallback
        fallback = "I'm not sure how to help with that yet. Could you try asking me to open an app, check the time, or ask about your agenda?"
        self.conversation_history.append({"role": "assistant", "content": fallback})
        return fallback
    
    def _try_skills(self, user_input: str) -> Optional[str]:
        """Try to match user input with available skills
        
        This method checks if the user's input matches any of the defined skill patterns
        and executes the corresponding skill if a match is found.
        
        Note: App control skills are handled separately for better prioritization.
        
        Args:
            user_input: The user's input text
            
        Returns:
            Optional[str]: The skill response if a match is found, None otherwise
        """
        user_input_lower = user_input.lower()
        
        for skill_name, patterns in self.skill_patterns.items():
            # Skip app_control as it's handled separately in process_input
            if skill_name == 'app_control':
                continue
                
            for pattern in patterns:
                if re.search(pattern, user_input_lower):
                    return self._execute_skill(skill_name, user_input)
        
        return None
    
    def _execute_skill(self, skill_name: str, user_input: str) -> str:
        """Execute the matched skill"""
        try:
            if skill_name == 'app_control':
                return self._handle_app_control(user_input)
            elif skill_name == 'system_info':
                return self._handle_system_info(user_input)
            elif skill_name == 'calendar':
                return self._handle_calendar(user_input)
            elif skill_name == 'calendar_redirect':
                # Redirect Notion queries to calendar skill
                print("🔄 Redirecting Notion/task query to calendar skill")
                return self._handle_calendar(user_input)
            elif skill_name == 'notes':
                # Handle notes requests
                print("📝 Handling notes request")
                return self._handle_notes(user_input)
            elif skill_name == 'focus':
                # Handle focus mode requests
                print("🌙 Handling focus mode request")
                return self._handle_focus(user_input)
            elif skill_name == 'spotify':
                # Handle Spotify requests
                print("🎵 Handling Spotify request")
                return self._handle_spotify(user_input)
            elif skill_name == 'math':
                # COMMENTED OUT: Local math skills replaced with OpenAI LLM
                # return self._handle_math(user_input)
                
                # NEW: Route math requests directly to OpenAI LLM for better performance
                print("🧮 Math request detected - routing to OpenAI LLM for intelligent calculation...")
                return self._get_llm_response(user_input)
            else:
                return f"I have a skill for {skill_name}, but it's not implemented yet."
        except Exception as e:
            return f"Sorry, I encountered an error while trying to {skill_name}: {str(e)}"
    
    def _handle_app_control(self, user_input: str) -> str:
        """Handle app launching commands
        
        This method processes commands to open applications on macOS.
        It maps common app names to their actual application names and
        uses the 'open' command to launch them.
        
        Args:
            user_input: The user's request to open an application
            
        Returns:
            str: A confirmation message or error message
        """
        import subprocess
        import os
        import platform
        
        # Log the app control request
        print(f"🖥️ App control request detected: '{user_input}'")
        
        # Check if we're on macOS
        if platform.system() != "Darwin":
            return "I'm sorry, app control is currently only supported on macOS."
        
        # Extract app name from input
        app_mapping = {
            'vscode': 'Visual Studio Code',
            'code': 'Visual Studio Code',
            'visual studio code': 'Visual Studio Code',
            'vs code': 'Visual Studio Code',
            'chrome': 'Google Chrome',
            'browser': 'Google Chrome',  # Common fallback
            'safari': 'Safari',
            'firefox': 'Firefox',
            'terminal': 'Terminal',
            'finder': 'Finder',
            'mail': 'Mail',
            'email': 'Mail',  # Common fallback
            'messages': 'Messages',
            'imessage': 'Messages',  # Common name
            'slack': 'Slack',
            'discord': 'Discord',
            'spotify': 'Spotify',
            'music': 'Music',
            'calculator': 'Calculator',
            'calc': 'Calculator',  # Common shorthand
            'notes': 'Notes',
            'reminders': 'Reminders',
            'calendar': 'Calendar',
            'photos': 'Photos',
            'preview': 'Preview',
            'textedit': 'TextEdit',
            'pages': 'Pages',
            'numbers': 'Numbers',
            'keynote': 'Keynote',
            'system preferences': 'System Preferences',
            'settings': 'System Preferences',  # Common name
            'system settings': 'System Settings'  # For newer macOS
        }
        
        user_input_lower = user_input.lower()
        
        # Check for web browsing requests
        web_phrases = ['web', 'internet', 'new tab', 'new page', 'browser tab', 'website', 'google', 'gmail', 'youtube', 'facebook']
        is_web_request = any(phrase in user_input_lower for phrase in web_phrases)
        
        # Try to find a matching app
        matched_app = None
        for key, app_name in app_mapping.items():
            if key in user_input_lower:
                matched_app = app_name
                break
        
        # Handle web browsing requests
        if is_web_request and not matched_app:
            print("🌐 Web browsing request detected")
            # Default to Chrome for web browsing requests
            matched_app = "Google Chrome"
        
        if not matched_app:
            # Check for single word commands
            words = user_input_lower.split()
            if len(words) == 1:
                word = words[0]
                if word in ["chrome", "browser"]:
                    matched_app = "Google Chrome"
                elif word in ["safari"]:
                    matched_app = "Safari"
                elif word in ["firefox"]:
                    matched_app = "Firefox"
                elif word in ["terminal"]:
                    matched_app = "Terminal"
                elif word in ["finder"]:
                    matched_app = "Finder"
                elif word in ["calculator", "calc"]:
                    matched_app = "Calculator"
                elif word in ["calendar"]:
                    matched_app = "Calendar"
            
        if not matched_app:
            return "I'm not sure which app you'd like me to open. Could you be more specific?"
        
        print(f"🖥️ Attempting to open: {matched_app}")
        
        # First try the standard 'open -a' approach
        try:
            result = subprocess.run(['open', '-a', matched_app], 
                                  capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                return f"Opening {matched_app} for you."
            else:
                print(f"⚠️ Error opening app: {result.stderr}")
        except Exception as e:
            print(f"⚠️ Exception when opening app: {e}")
        
        # If that fails, try an alternative approach for system apps
        try:
            # For system apps, try a different approach
            if matched_app in ["System Preferences", "System Settings"]:
                alt_cmd = "open /System/Applications/System\\ Settings.app" if os.path.exists("/System/Applications/System Settings.app") else "open /System/Applications/System\\ Preferences.app"
                os.system(alt_cmd)
                return f"Opening {matched_app} for you."
            
            # Try looking in common locations
            common_paths = [
                f"/Applications/{matched_app}.app",
                f"/System/Applications/{matched_app}.app",
                f"/Users/{os.getenv('USER')}/Applications/{matched_app}.app"
            ]
            
            for path in common_paths:
                if os.path.exists(path.replace(" ", "\\ ")):
                    os.system(f"open '{path}'")
                    return f"Opening {matched_app} for you."
            
            return f"I couldn't find {matched_app} on your system. Please check if it's installed."
        except Exception as e:
            print(f"⚠️ Alternative app opening failed: {e}")
            return f"I had trouble opening {matched_app}. It might not be installed or accessible."
    
    def _handle_system_info(self, user_input: str) -> str:
        """Handle system information requests"""
        import datetime
        import subprocess
        
        if any(word in user_input.lower() for word in ['time', 'date']):
            now = datetime.datetime.now()
            time_str = now.strftime("%I:%M %p")
            date_str = now.strftime("%A, %B %d, %Y")
            return f"The current time is {time_str} on {date_str}."
        
        elif 'battery' in user_input.lower():
            try:
                result = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True)
                if result.returncode == 0:
                    # Parse battery info
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'InternalBattery' in line:
                            # Extract percentage
                            if '%' in line:
                                percentage = line.split('%')[0].split()[-1]
                                return f"Your battery is at {percentage}%."
                    return "I can see your battery status, but the percentage isn't clear."
            except Exception:
                pass
            return "I'm having trouble checking your battery status."
        
        elif 'volume' in user_input.lower():
            try:
                result = subprocess.run(['osascript', '-e', 'output volume of (get volume settings)'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    volume = result.stdout.strip()
                    return f"Your current volume is at {volume}%."
            except Exception:
                pass
            return "I can't check your volume right now."
        
        return "I can tell you the time, date, battery status, or volume. What would you like to know?"
    
    def _handle_calendar(self, user_input: str) -> str:
        """Handle calendar-related requests using the CalendarSkill"""
        from core.skills.calendar_skill import CalendarSkill
        
        calendar_skill = CalendarSkill()
        return calendar_skill.handle_query(user_input)
        
    def _handle_notes(self, user_input: str) -> str:
        """Handle notes-related requests using the NotesSkill"""
        if 'notes' in self.skill_instances:
            return self.skill_instances['notes'].handle_query(user_input)
        else:
            # Fallback if skill instance not available
            from core.skills.notes_skill import NotesSkill
            notes_skill = NotesSkill()
            return notes_skill.handle_query(user_input)
            
    def _handle_focus(self, user_input: str) -> str:
        """Handle focus mode-related requests using the FocusSkill"""
        if 'focus' in self.skill_instances:
            return self.skill_instances['focus'].process(user_input)
        else:
            # Fallback if skill instance not available
            from core.skills.focus_skill import FocusSkill
            from core.services.app_control_service import AppControlService
            focus_skill = FocusSkill(AppControlService())
            return focus_skill.process(user_input)
    
    def _handle_spotify(self, user_input: str) -> str:
        """Handle Spotify-related requests using the SpotifySkill"""
        if 'spotify' in self.skill_instances:
            return self.skill_instances['spotify'].process(user_input)
        else:
            # Fallback if skill instance not available
            from core.skills.spotify_skill import SpotifySkill
            from core.services.spotify_service import SpotifyService
            spotify_skill = SpotifySkill(SpotifyService())
            return spotify_skill.process(user_input)
    
    # def _handle_notion(self, user_input: str) -> str:
    #     """Handle Notion-related requests (deprecated)"""
    #     # This method is no longer used as we've migrated to Google Calendar
    #     # Notion queries are now redirected to the calendar skill
    #     return self._handle_calendar(user_input)
    
    def _handle_math(self, user_input: str) -> str:
        """Handle mathematical calculations - COMMENTED OUT FOR LLM-FIRST ARCHITECTURE"""
        # COMMENTED OUT: Local math skills replaced with OpenAI LLM for better performance
        # This code is kept for reference and can be re-enabled if needed
        
        """
        import re
        
        # Try to extract and evaluate mathematical expressions
        try:
            # Look for patterns like "what is 5 + 3" or "calculate 10 * 5"
            math_patterns = [
                r'what\s+is\s+(\d+[\+\-\*\/\s\d\(\)\.]+)',  # "what is 5 + 3"
                r'calculate\s+(\d+[\+\-\*\/\s\d\(\)\.]+)',   # "calculate 10 * 5"
                r'(\d+[\+\-\*\/\s\d\(\)\.]+)',               # "5 + 3"
            ]
            
            math_expression = None
            for pattern in math_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    math_expression = match.group(1).strip()
                    break
            
            if math_expression:
                # Clean up the expression for evaluation
                # Replace words with symbols
                cleaned_expr = math_expression.replace('plus', '+').replace('minus', '-').replace('times', '*').replace('divided by', '/')
                
                # Remove extra spaces and evaluate
                cleaned_expr = re.sub(r'\s+', '', cleaned_expr)
                
                # Safety check - only allow basic math operations
                if re.match(r'^[\d\+\-\*\/\(\)\.\s]+$', cleaned_expr):
                    # Use eval with a safe environment
                    safe_dict = {"__builtins__": {}}
                    result = eval(cleaned_expr, safe_dict)
                    
                    # Format the result nicely
                    if isinstance(result, (int, float)):
                        if result == int(result):
                            result = int(result)
                        return f"The answer is {result}."
                    else:
                        return f"I calculated: {result}"
                else:
                    return "I can only handle basic mathematical operations (+, -, *, /, parentheses)."
            
            # If no math expression found, provide helpful examples
            return "I can help with math! Try saying something like 'what is 5 plus 3', 'calculate 10 times 5', or 'what is 15 divided by 3'."
            
        except ZeroDivisionError:
            return "I can't divide by zero."
        except Exception as e:
            print(f"Math calculation error: {e}")
            return "I'm having trouble with that calculation. Could you rephrase it?"
        """
        
        # NEW: Route math requests to OpenAI LLM for better performance
        return self._get_llm_response(user_input)
    
    def _get_llm_response(self, user_input: str, stream: bool = False) -> Optional[str]:
        """Get response from OpenAI LLM with enhanced personalization
        
        Args:
            user_input: The user's input text
            stream: If True, returns a generator that yields response chunks
        """
        try:
            # Build conversation context with enhanced persona
            enhanced_persona = config.get_enhanced_persona()
            
            # Add special instructions for app control
            enhanced_persona += "\n\nIMPORTANT: Nova can open applications on the user's computer. " + \
                              "When the user says 'yes', 'ok', or gives a simple affirmation after Nova has opened an app, " + \
                              "respond with a friendly acknowledgment, not with a message suggesting you can't open apps."
            
            messages = [{"role": "system", "content": enhanced_persona}]
            
            # Add recent conversation history (last 20 exchanges)
            recent_history = self.conversation_history[-20:]  # Last 20 messages
            messages.extend(recent_history)
            
            # Check if this is a simple affirmation after opening an app
            user_input_lower = user_input.lower()
            simple_affirmations = ["yes", "ok", "okay", "sure", "thanks", "thank you", "good", "great", "perfect", "nice"]
            
            # Check if the last assistant message was about opening an app
            last_assistant_msg = ""
            for msg in reversed(self.conversation_history):
                if msg["role"] == "assistant":
                    last_assistant_msg = msg["content"].lower()
                    break
            
            # If this is a simple affirmation after opening an app, add a hint to the LLM
            if user_input_lower.strip() in simple_affirmations and "opening" in last_assistant_msg:
                messages.append({
                    "role": "system",
                    "content": "The user is acknowledging that you successfully opened the application. Respond positively without suggesting you can't open applications."
                })
            
            # Get response from OpenAI (new API)
            from openai import OpenAI
            client = OpenAI(api_key=config.openai_api_key)
            
            # If streaming is requested, return a generator
            if stream:
                return self._stream_llm_response(client, messages)
            
            # Otherwise, get the full response at once
            response = client.chat.completions.create(
                model=config.llm_model,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error getting LLM response: {e}")
            return None
            
    def _stream_llm_response(self, client, messages):
        """Stream response chunks from the LLM in real-time
        
        This method enables streaming responses from the OpenAI API,
        which provides a more natural conversational experience by
        displaying responses as they are generated rather than waiting
        for the complete response.
        
        Args:
            client: The OpenAI client instance
            messages: The conversation history and system messages
            
        Returns:
            Generator: A generator that yields response chunks as they arrive
            
        Note:
            The full response is collected and added to conversation history
            after streaming is complete.
        """
        try:
            # Create a streaming response
            stream = client.chat.completions.create(
                model=config.llm_model,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                stream=True  # Enable streaming
            )
            
            # Collect the full response for history
            full_response = ""
            
            # Yield each chunk as it arrives
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # Add the full response to conversation history
            self.conversation_history.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            print(f"Error streaming LLM response: {e}")
            yield f"I'm sorry, I encountered an error: {str(e)}"
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation"""
        if not self.conversation_history:
            return "No conversation history yet."
        
        # Count user and assistant messages
        user_messages = sum(1 for msg in self.conversation_history if msg["role"] == "user")
        assistant_messages = sum(1 for msg in self.conversation_history if msg["role"] == "assistant")
        
        return f"We've had {user_messages} exchanges. I've responded {assistant_messages} times."
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        print("Conversation history cleared.")
