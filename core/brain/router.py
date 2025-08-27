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
    
    def _setup_skill_patterns(self):
        """Setup patterns for skill detection"""
        self.skill_patterns = {
            'app_control': [
                r'\b(open|launch|start)\s+(vscode|code|visual\s+studio|chrome|safari|firefox|terminal|finder|mail|messages|slack|discord|spotify|music|calculator|notes|reminders|calendar|photos|preview|textedit|pages|numbers|keynote)\b',
                r'\b(open|launch|start)\s+(visual\s+studio\s+code|vs\s+code)\b',
                r'\b(can\s+you\s+open|could\s+you\s+open|please\s+open|would\s+you\s+open)\s+(vscode|code|visual\s+studio|chrome|safari|firefox|terminal|finder|mail|messages|slack|discord|spotify|music|calculator|notes|reminders|calendar|photos|preview|textedit|pages|numbers|keynote)\b',
                r'\b(can\s+you\s+launch|could\s+you\s+launch|please\s+launch|would\s+you\s+launch)\s+(vscode|code|visual\s+studio|chrome|safari|firefox|terminal|finder|mail|messages|slack|discord|spotify|music|calculator|notes|reminders|calendar|photos|preview|textedit|pages|numbers|keynote)\b',
                r'\b(can\s+you\s+start|could\s+you\s+start|please\s+start|would\s+you\s+start)\s+(vscode|code|visual\s+studio|chrome|safari|firefox|terminal|finder|mail|messages|slack|discord|spotify|music|calculator|notes|reminders|calendar|photos|preview|textedit|pages|numbers|keynote)\b'
            ],
            'system_info': [
                r'\b(time|date|current\s+time|what\s+time|what\s+date|battery|volume|brightness|wifi|network|status)\b',
                r'\b(how\s+much\s+battery|what\s+is\s+the\s+time|system\s+info)\b'
            ],
            'notion': [
                r'\b(agenda|schedule|tasks|todo|notion|what\s+do\s+i\s+have|what\'s\s+on\s+my\s+plate|my\s+day)\b',
                r'\b(show\s+me\s+my|read\s+my|check\s+my)\s+(agenda|schedule|tasks|notes)\b'
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
        
        # 1. Check for conversation closure signals (e.g., "thanks", "that's all")
        closure_phrases = [
            "that's all", "thank you", "thanks", "that'll be all", 
            "that will be all", "that's it", "that is all", 
            "that's all i need", "that's all for now"
        ]
        
        is_closure = False
        user_input_lower = user_input.lower()
        
        # Detect if this is a conversation closure phrase
        for phrase in closure_phrases:
            if phrase in user_input_lower:
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
        
        # Check if this is an app control command using regex patterns
        for pattern in self.skill_patterns['app_control']:
            if re.search(pattern, user_input_lower):
                app_control_match = True
                break
        
        # Execute app control commands directly
        if app_control_match:
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
            elif skill_name == 'notion':
                return self._handle_notion(user_input)
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
        
        # Extract app name from input
        app_mapping = {
            'vscode': 'Visual Studio Code',
            'code': 'Visual Studio Code',
            'visual studio code': 'Visual Studio Code',
            'vs code': 'Visual Studio Code',
            'chrome': 'Google Chrome',
            'safari': 'Safari',
            'firefox': 'Firefox',
            'terminal': 'Terminal',
            'finder': 'Finder',
            'mail': 'Mail',
            'messages': 'Messages',
            'slack': 'Slack',
            'discord': 'Discord',
            'spotify': 'Spotify',
            'music': 'Music',
            'calculator': 'Calculator',
            'notes': 'Notes',
            'reminders': 'Reminders',
            'calendar': 'Calendar',
            'photos': 'Photos',
            'preview': 'Preview',
            'textedit': 'TextEdit',
            'pages': 'Pages',
            'numbers': 'Numbers',
            'keynote': 'Keynote'
        }
        
        for key, app_name in app_mapping.items():
            if key in user_input.lower():
                try:
                    subprocess.run(['open', '-a', app_name], check=True)
                    return f"Opening {app_name} for you."
                except subprocess.CalledProcessError:
                    return f"I couldn't open {app_name}. It might not be installed."
        
        return "I'm not sure which app you'd like me to open. Could you be more specific?"
    
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
    
    def _handle_notion(self, user_input: str) -> str:
        """Handle Notion-related requests (stubbed for MVP)"""
        # For MVP, return a stubbed response
        # Later, this will integrate with Notion API
        return "I can see you have a few tasks today: review the quarterly report, call the client at 2 PM, and prepare for tomorrow's meeting. Would you like me to help you with any of these?"
    
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
            messages = [{"role": "system", "content": enhanced_persona}]
            
            # Add recent conversation history (last 20 exchanges)
            recent_history = self.conversation_history[-20:]  # Last 20 messages
            messages.extend(recent_history)
            
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
