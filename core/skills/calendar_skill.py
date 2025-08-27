"""
Calendar Skill for Nova

This skill provides calendar-related functionality, combining
class schedule from personal_config with Notion calendar events.
"""
import datetime
import os
import sys
import re
from typing import Optional, Dict, Any, List

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.services.calendar_service import CalendarService

class CalendarSkill:
    """Skill for handling calendar-related queries"""
    
    def __init__(self):
        """Initialize the calendar skill"""
        self.calendar_service = CalendarService()
    
    def handle_query(self, query: str) -> str:
        """Handle a calendar-related query"""
        query = query.lower()
        
        # Check for today's schedule
        if re.search(r'(what|show|tell|check).*(schedule|agenda|plan|calendar|event|class|have).*today', query) or \
           re.search(r'(today\'s|todays).*(schedule|agenda|plan|calendar|event|class)', query) or \
           re.search(r'what.*(do|have).*i.*today', query):
            return self.get_today_schedule()
        
        # Check for tomorrow's schedule
        elif re.search(r'(what|show|tell|check).*(schedule|agenda|plan|calendar|event|class|have).*tomorrow', query) or \
             re.search(r'(tomorrow\'s|tomorrows).*(schedule|agenda|plan|calendar|event|class)', query) or \
             re.search(r'what.*(do|have).*i.*tomorrow', query):
            return self.get_tomorrow_schedule()
        
        # Check for this week's schedule
        elif re.search(r'(what|show|tell|check).*(schedule|agenda|plan|calendar|event|class|have).*week', query) or \
             re.search(r'(this|the|upcoming|next).*(week\'s|weeks).*(schedule|agenda|plan|calendar|event|class)', query):
            return self.get_week_schedule()
        
        # Check for specific day
        elif re.search(r'(what|show|tell|check).*(schedule|agenda|plan|calendar|event|class|have).*(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', query):
            day_match = re.search(r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', query)
            if day_match:
                return self.get_day_schedule(day_match.group(1))
        
        # Default response
        return "I can tell you about your schedule for today, tomorrow, or the upcoming week. What would you like to know?"
    
    def get_today_schedule(self) -> str:
        """Get today's schedule"""
        today = self.calendar_service.get_today_schedule()
        return self.calendar_service.format_day_schedule(today)
    
    def get_tomorrow_schedule(self) -> str:
        """Get tomorrow's schedule"""
        tomorrow = self.calendar_service.get_tomorrow_schedule()
        return self.calendar_service.format_day_schedule(tomorrow)
    
    def get_week_schedule(self) -> str:
        """Get the schedule for the next 7 days"""
        week = self.calendar_service.get_week_schedule()
        return self.calendar_service.format_week_schedule(week)
    
    def get_day_schedule(self, day_name: str) -> str:
        """Get the schedule for a specific day of the week"""
        # Map day name to datetime.date
        today = datetime.date.today()
        current_weekday = today.weekday()  # 0=Monday, 6=Sunday
        
        # Convert day name to weekday number
        day_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        target_weekday = day_map.get(day_name.lower())
        
        if target_weekday is None:
            return f"I'm not sure which day '{day_name}' refers to."
        
        # Calculate days to add
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0:
            # If it's the same day, check if we're referring to today or next week
            if 'next' in day_name.lower():
                days_ahead = 7
        
        target_date = today + datetime.timedelta(days=days_ahead)
        day = self.calendar_service.get_day_schedule(target_date)
        return self.calendar_service.format_day_schedule(day)
