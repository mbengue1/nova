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
try:
    from core.services.google_calendar_service import GoogleCalendarService
except ImportError:
    # If Google Calendar service is not available, we'll fall back to Notion
    GoogleCalendarService = None

class CalendarEvent:
    """Represents a calendar event (either class or Notion event)"""
    
    def __init__(self, 
                title: str,
                start_time: str,
                end_time: Optional[str] = None,
                location: Optional[str] = None,
                description: Optional[str] = None,
                event_type: str = "event",  # "class" or "event"
                all_day: bool = False,
                tags: Optional[List[str]] = None,
                url: Optional[str] = None):
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.description = description
        self.event_type = event_type
        self.all_day = all_day
        self.tags = tags or []
        self.url = url
    
    @classmethod
    def from_class_info(cls, class_info: Dict[str, Any], date: datetime.date) -> 'CalendarEvent':
        """Create a CalendarEvent from class information"""
        # Parse time strings (e.g., "14:00 - 15:15 pm")
        time_parts = class_info.get("time", "").split(" - ")
        start_time = None
        end_time = None
        
        if len(time_parts) == 2:
            # Convert to ISO format for consistency
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
                print(f"Error parsing class time: {e}")
        
        return cls(
            title=f"{class_info.get('name')} ({class_info.get('code')})",
            start_time=start_time,
            end_time=end_time,
            location=class_info.get("location"),
            description=f"Professor: {class_info.get('professor')}",
            event_type="class"
        )
    
    @classmethod
    def from_notion_event(cls, notion_event: Dict[str, Any]) -> 'CalendarEvent':
        """Create a CalendarEvent from a Notion event"""
        return cls(
            title=notion_event.get("title", "Untitled Event"),
            start_time=notion_event.get("start_time"),
            end_time=notion_event.get("end_time"),
            location=notion_event.get("location"),
            description=notion_event.get("description"),
            event_type="event",
            all_day=notion_event.get("all_day", False),
            tags=notion_event.get("tags", []),
            url=notion_event.get("url")
        )
    
    def format_time(self) -> str:
        """Format the event time for conversational display"""
        if not self.start_time:
            return "time not specified"
            
        if self.all_day:
            return "all day"
            
        try:
            # Parse ISO datetime
            start_dt = datetime.datetime.fromisoformat(self.start_time)
            
            # Format hour without leading zero and handle special cases
            hour = start_dt.hour
            if hour == 0:
                hour_str = "midnight"
            elif hour == 12:
                hour_str = "noon"
            elif hour > 12:
                hour_str = f"{hour - 12}"
            else:
                hour_str = f"{hour}"
                
            # Only add minutes if not on the hour
            if start_dt.minute == 0:
                if hour not in [0, 12]:  # Not midnight or noon
                    am_pm = "am" if hour < 12 else "pm"
                    start_str = f"{hour_str} {am_pm}"
                else:
                    start_str = hour_str  # Just "midnight" or "noon"
            else:
                am_pm = "am" if hour < 12 else "pm"
                start_str = f"{hour_str}:{start_dt.minute:02d} {am_pm}"
            
            if self.end_time:
                try:
                    end_dt = datetime.datetime.fromisoformat(self.end_time)
                    
                    # Only include end time if it's not the same day or if it matters
                    if start_dt.date() != end_dt.date():
                        return f"{start_str} today until {end_dt.strftime('%A')}"
                    else:
                        # Format hour without leading zero
                        hour = end_dt.hour
                        if hour == 0:
                            hour_str = "midnight"
                        elif hour == 12:
                            hour_str = "noon"
                        elif hour > 12:
                            hour_str = f"{hour - 12}"
                        else:
                            hour_str = f"{hour}"
                            
                        # Only add minutes if not on the hour
                        if end_dt.minute == 0:
                            if hour not in [0, 12]:  # Not midnight or noon
                                am_pm = "am" if hour < 12 else "pm"
                                end_str = f"{hour_str} {am_pm}"
                            else:
                                end_str = hour_str  # Just "midnight" or "noon"
                        else:
                            am_pm = "am" if hour < 12 else "pm"
                            end_str = f"{hour_str}:{end_dt.minute:02d} {am_pm}"
                        
                        return f"{start_str} to {end_str}"
                except:
                    return start_str
            else:
                return start_str
        except Exception:
            # Fall back to raw strings if parsing fails
            if self.end_time:
                return f"{self.start_time} to {self.end_time}"
            return str(self.start_time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "title": self.title,
            "time": self.format_time(),
            "location": self.location,
            "description": self.description,
            "type": self.event_type,
            "all_day": self.all_day,
            "tags": self.tags,
            "url": self.url
        }

class CalendarDay:
    """Represents a full day of events"""
    
    def __init__(self, date: datetime.date):
        self.date = date
        self.events = []
    
    def add_event(self, event: CalendarEvent):
        """Add an event to this day"""
        self.events.append(event)
    
    def get_sorted_events(self) -> List[CalendarEvent]:
        """Get events sorted by start time"""
        def get_sort_key(event):
            if not event.start_time:
                return "Z"  # Sort events without times last
            return event.start_time
            
        return sorted(self.events, key=get_sort_key)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "date": self.date.isoformat(),
            "weekday": self.date.strftime("%A"),
            "events": [event.to_dict() for event in self.get_sorted_events()]
        }

class CalendarService:
    """Service for managing and querying calendar events"""
    
    def __init__(self):
        """Initialize the calendar service"""
        # Try to initialize Google Calendar service first (preferred)
        self.google_calendar = None
        if GoogleCalendarService is not None:
            try:
                # Try multiple times to initialize Google Calendar service
                for attempt in range(3):
                    self.google_calendar = GoogleCalendarService()
                    if self.google_calendar.is_available():
                        print("✅ Using Google Calendar as primary calendar source")
                        break
                    else:
                        print(f"⚠️  Attempt {attempt+1}/3: Google Calendar service not available, retrying...")
            except Exception as e:
                print(f"⚠️  Could not initialize Google Calendar service: {e}")
                self.google_calendar = None
        
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
        if self.google_calendar and self.google_calendar.is_available():
            # Use the Google Calendar service to get events
            google_events = self.google_calendar.get_calendar_events(date)
            for event in google_events:
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
