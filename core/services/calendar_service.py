"""
Calendar Service for Nova

This service combines class schedule from personal_config with 
calendar events from Google Calendar (preferred) or Notion to provide 
a unified view of the user's schedule.
"""
import datetime
import os
import sys
from typing import List, Dict, Any, Optional, Union

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import config
from core.integrations.notion_client import NotionClient

# Import Google Calendar service with better error handling
GoogleCalendarService = None
try:
    # Try absolute import
    from core.services.google_calendar_service import GoogleCalendarService
    print("✅ GoogleCalendarService imported via absolute import")
except ImportError as e:
    print(f"⚠️  GoogleCalendarService import failed: {e}")
    GoogleCalendarService = None

# Import the shared calendar models
from core.services.calendar_models import CalendarEvent, CalendarDay



class CalendarService:
    """Service for managing and querying calendar events"""
    
    def __init__(self):
        """Initialize the calendar service"""
        # Try to initialize Google Calendar service first (preferred)
        self.google_calendar = None
        if GoogleCalendarService is not None:
            try:
                print("🔄 Initializing Google Calendar service...")
                self.google_calendar = GoogleCalendarService()
                print(f"GoogleCalendarService instance created: {self.google_calendar}")
                
                # Check if the service is available
                if self.google_calendar and self.google_calendar.is_available():
                    print("✅ Using Google Calendar as primary calendar source")
                else:
                    print("⚠️  Google Calendar service initialized but not available")
                    print(f"   self.google_calendar: {self.google_calendar}")
                    if self.google_calendar:
                        print(f"   is_available(): {self.google_calendar.is_available()}")
                    # Don't set to None yet, let's see what happens when we try to use it
            except Exception as e:
                print(f"⚠️  Could not initialize Google Calendar service: {e}")
                import traceback
                traceback.print_exc()
                self.google_calendar = None
        else:
            print("❌ GoogleCalendarService is None (import failed)")
        
        # Initialize Notion client but don't use it for calendar data
        # We keep this initialization for backward compatibility
        self.notion_client = NotionClient()
        
        # Log calendar source status
        if not self.google_calendar or not self.google_calendar.is_available():
            print("⚠️  Google Calendar not available - using only personal config")
            print("ℹ️  Notion calendar integration is disabled")
    
    def get_day_schedule(self, date: Optional[datetime.date] = None) -> CalendarDay:
        """Get the schedule for a specific day"""
        if not date:
            date = datetime.date.today()
            
        day = CalendarDay(date)
        
        # Add class schedule from personal config
        weekday = date.strftime("%A")
        for course in config.courses:
            if weekday in course.get("days", []):
                class_event = CalendarEvent.from_class_info(course, date)
                day.add_event(class_event)
        
        # Add activities from personal config
        for activity in config.activities:
            frequency = activity.get("frequency", "")
            activity_days = activity.get("days", [])
            
            if frequency == "daily" or weekday in activity_days:
                # Create an event for this activity
                start_time = None
                end_time = None
                
                # Parse time if available
                time_str = activity.get("time", "")
                if " - " in time_str:
                    time_parts = time_str.split(" - ")
                    if len(time_parts) == 2:
                        # Convert to ISO format
                        try:
                            # Parse start time
                            start_str = time_parts[0].strip()
                            if "pm" in start_str.lower() and not start_str.startswith("12"):
                                hour = int(start_str.split(":")[0]) + 12
                                start_str = f"{hour}:{start_str.split(':')[1].split(' ')[0]}"
                            else:
                                start_str = start_str.split(' ')[0]
                            
                            # Parse end time
                            end_str = time_parts[1].strip()
                            if "pm" in end_str.lower() and not end_str.startswith("12"):
                                hour = int(end_str.split(":")[0]) + 12
                                end_str = f"{hour}:{end_str.split(':')[1].split(' ')[0]}"
                            else:
                                end_str = end_str.split(' ')[0]
                            
                            # Create ISO format datetime strings
                            start_time = f"{date.isoformat()}T{start_str}:00"
                            end_time = f"{date.isoformat()}T{end_str}:00"
                        except Exception as e:
                            print(f"Error parsing activity time: {e}")
                
                activity_event = CalendarEvent(
                    title=activity.get("name", "Activity"),
                    start_time=start_time,
                    end_time=end_time,
                    location=activity.get("location"),
                    event_type="activity"
                )
                day.add_event(activity_event)
        
        # Add Google Calendar events if available
        if self.google_calendar:
            try:
                if self.google_calendar.is_available():
                    print(f"Google Calendar is available, getting events for {date}")
                    # Use the Google Calendar service to get events
                    google_events = self.google_calendar.get_calendar_events(date)
                    print(f"Found {len(google_events)} Google Calendar events")
                    for event in google_events:
                        print(f"Processing Google event: {event}")
                        google_event = CalendarEvent(
                            title=event.get('title', 'Untitled Event'),
                            start_time=event.get('start_time'),
                            end_time=event.get('end_time'),
                            location=event.get('location'),
                            description=event.get('description'),
                            event_type='event',
                            all_day=event.get('all_day', False),
                            tags=[],
                            url=event.get('url')
                        )
                        day.add_event(google_event)
                        print(f"Added Google Calendar event: {event.get('title', 'Untitled Event')}")
                else:
                    print(f"Google Calendar service exists but is_available() returned False")
            except Exception as e:
                print(f"Error accessing Google Calendar: {e}")
        else:
            print(f"Google Calendar service not initialized")
        
        # We no longer use Notion for calendar data
        # This section is commented out to preserve the code for reference
        # 
        # elif self.notion_client.is_available():
        #     notion_events = self.notion_client.get_calendar_events(date)
        #     for event in notion_events:
        #         notion_event = CalendarEvent.from_notion_event(event)
        #         day.add_event(notion_event)
        
        return day
    
    def get_today_schedule(self) -> CalendarDay:
        """Get today's schedule"""
        return self.get_day_schedule(datetime.date.today())
    
    def get_tomorrow_schedule(self) -> CalendarDay:
        """Get tomorrow's schedule"""
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        return self.get_day_schedule(tomorrow)
    
    def get_week_schedule(self) -> List[CalendarDay]:
        """Get the schedule for the next 7 days"""
        today = datetime.date.today()
        return [self.get_day_schedule(today + datetime.timedelta(days=i)) for i in range(7)]
        
    def get_rest_of_day_schedule(self) -> List[CalendarEvent]:
        """Get events for the rest of the current day"""
        today = datetime.date.today()
        now = datetime.datetime.now()
        
        # Get today's schedule
        day = self.get_day_schedule(today)
        events = day.get_sorted_events()
        
        # Filter for events that haven't started yet or are currently ongoing
        upcoming_events = []
        for event in events:
            try:
                if event.start_time:
                    # Parse the event start time
                    event_start = datetime.datetime.fromisoformat(event.start_time)
                    
                    # Convert both times to timezone-naive for comparison
                    if event_start.tzinfo is not None:
                        # Remove timezone info for comparison
                        event_start = event_start.replace(tzinfo=None)
                    
                    # Include events that start in the future or are currently ongoing
                    if event_start >= now:
                        upcoming_events.append(event)
                else:
                    # Events without start time are excluded (they're usually all-day events that don't need time filtering)
                    pass
            except (ValueError, TypeError):
                # If we can't parse the time, exclude the event to be safe
                pass
        
        return upcoming_events
    
    def format_day_schedule(self, day: CalendarDay) -> str:
        """Format a day's schedule for conversational response"""
        events = day.get_sorted_events()
        
        # Get day name (today, tomorrow, or day of week)
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        if day.date == today:
            day_name = "today"
        elif day.date == tomorrow:
            day_name = "tomorrow"
        else:
            day_name = f"on {day.date.strftime('%A')}"
        
        if not events:
            return f"You don't have anything scheduled {day_name}."
        
        # Create a conversational response
        if len(events) == 1:
            event = events[0]
            time_str = event.format_time()
            location_str = f" at {event.location}" if event.location else ""
            
            if event.event_type == "class":
                return f"{day_name.capitalize()}, you have {event.title} at {time_str}{location_str}."
            else:
                return f"{day_name.capitalize()}, you have {event.title} scheduled at {time_str}{location_str}."
        else:
            # For multiple events, create a more flowing response
            response = f"For {day_name}, you have {len(events)} events: "
            
            for i, event in enumerate(events):
                time_str = event.format_time()
                location_str = f" at {event.location}" if event.location else ""
                
                # Extract just the course name from the title (remove code in parentheses)
                title = event.title
                if "(" in title and ")" in title:
                    title = title.split("(")[0].strip()
                
                # Add appropriate transition words
                if i == 0:
                    response += f"{title} at {time_str}{location_str}"
                elif i == len(events) - 1:
                    response += f", and finally {title} at {time_str}{location_str}."
                else:
                    response += f", then {title} at {time_str}{location_str}"
            
            return response
    
    def format_rest_of_day_schedule(self) -> str:
        """Format the rest of day's schedule for conversational response"""
        events = self.get_rest_of_day_schedule()
        
        # Get current time period (morning, afternoon, evening, night)
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            time_period = "day"
        elif 12 <= hour < 17:
            time_period = "day"
        elif 17 <= hour < 20:
            time_period = "evening"
        else:
            time_period = "night"
        
        if not events:
            return f"You have nothing scheduled for the rest of the {time_period}."
        
        # Create a conversational response
        if len(events) == 1:
            event = events[0]
            time_str = event.format_time()
            location_str = f" at {event.location}" if event.location else ""
            
            if event.event_type == "class":
                return f"You have {event.title} at {time_str}{location_str} today."
            else:
                return f"You have {event.title} scheduled at {time_str}{location_str} today."
        else:
            # For multiple events, create a more flowing response
            response = f"For the rest of the {time_period}, you have {len(events)} events: "
            
            for i, event in enumerate(events):
                time_str = event.format_time()
                location_str = f" at {event.location}" if event.location else ""
                
                # Extract just the course name from the title (remove code in parentheses)
                title = event.title
                if "(" in title and ")" in title:
                    title = title.split("(")[0].strip()
                
                # Add appropriate transition words
                if i == 0:
                    response += f"{title} at {time_str}{location_str}"
                elif i == len(events) - 1:
                    response += f", and finally {title} at {time_str}{location_str}."
                else:
                    response += f", then {title} at {time_str}{location_str}"
            
            return response
    
    def format_week_schedule(self, days: List[CalendarDay]) -> str:
        """Format a week's schedule for conversational response"""
        if not days:
            return "You don't have anything scheduled for the upcoming week."
        
        # Count total events
        total_events = sum(len(day.get_sorted_events()) for day in days)
        
        if total_events == 0:
            return "Your calendar is clear for the entire week."
        
        # Create a conversational summary
        busy_days = [day for day in days if day.get_sorted_events()]
        
        if len(busy_days) == 1:
            # Only one day has events
            day = busy_days[0]
            day_name = day.date.strftime('%A')
            return f"This week, you only have events on {day_name}. {self.format_day_schedule(day)}"
        
        # Multiple days have events
        response = f"For this week, you have {total_events} events across {len(busy_days)} days. "
        
        # Highlight the busiest day
        busiest_day = max(days, key=lambda d: len(d.get_sorted_events()))
        busiest_day_events = len(busiest_day.get_sorted_events())
        
        if busiest_day_events > 0:
            busiest_day_name = busiest_day.date.strftime('%A')
            response += f"Your busiest day is {busiest_day_name} with {busiest_day_events} events. "
        
        # Mention next upcoming event
        today = datetime.date.today()
        future_days = [day for day in days if day.date >= today and day.get_sorted_events()]
        
        if future_days:
            next_day = min(future_days, key=lambda d: d.date)
            next_event = next_day.get_sorted_events()[0]
            next_day_name = next_day.date.strftime('%A')
            
            time_str = next_event.format_time()
            title = next_event.title
            if "(" in title and ")" in title:
                title = title.split("(")[0].strip()
                
            response += f"Your next event is {title} on {next_day_name} at {time_str}."
        
        return response
