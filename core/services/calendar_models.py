"""
Calendar Models for Nova

This module contains the shared calendar data models used by
both the calendar service and Google Calendar service to avoid
circular imports.
"""
import datetime
from typing import List, Dict, Any, Optional

class CalendarEvent:
    """Represents a calendar event (either class or external event)"""
    
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
