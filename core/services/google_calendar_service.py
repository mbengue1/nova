"""
Google Calendar Service for Nova

This service provides access to Google Calendar events through the Google Calendar API.
It handles authentication, token management, and calendar event retrieval.
"""
import os
import datetime
import pickle
import json
from typing import List, Dict, Any, Optional, Union
import pytz

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Add the core directory to Python path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import config
from core.services.calendar_models import CalendarEvent, CalendarDay

# Define the scopes needed for Google Calendar API
# Read-only access to calendar events
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

class GoogleCalendarService:
    """Service for accessing Google Calendar events"""
    
    def __init__(self):
        """Initialize the Google Calendar service"""
        credentials_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'credentials')
        
        # Look for credentials file - try both the default name and client_secret* pattern
        self.credentials_file = os.path.join(credentials_dir, 'google_credentials.json')
        if not os.path.exists(self.credentials_file):
            # Try to find any client_secret file
            client_secret_files = [f for f in os.listdir(credentials_dir) if f.startswith('client_secret') and f.endswith('.json')]
            if client_secret_files:
                self.credentials_file = os.path.join(credentials_dir, client_secret_files[0])
                print(f"📄 Using credentials file: {self.credentials_file}")
        
        self.token_file = os.path.join(credentials_dir, 'google_token.pickle')
        self.service = None
        self.timezone = config.timezone or 'America/New_York'
        
        # Try to authenticate
        self._authenticate()
    
    def is_available(self) -> bool:
        """Check if the Google Calendar API is available and configured"""
        return self.service is not None
    
    def _authenticate(self) -> None:
        """Authenticate with Google Calendar API"""
        creds = None
        
        # Check if token file exists
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If credentials don't exist or are invalid, refresh or create new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"⚠️  Error refreshing Google credentials: {e}")
                    creds = None
            else:
                # Check if credentials file exists
                if not os.path.exists(self.credentials_file):
                    print("⚠️  Google credentials file not found")
                    return
                
                try:
                    # Create credentials directory if it doesn't exist
                    os.makedirs(os.path.dirname(self.credentials_file), exist_ok=True)
                    
                    # Create the flow from client secrets file
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"⚠️  Error creating Google credentials: {e}")
                    return
            
            # Save the credentials for future use
            try:
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                print(f"⚠️  Error saving Google token: {e}")
        
        # Build the service
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            print("✅ Google Calendar service initialized")
        except Exception as e:
            print(f"⚠️  Error building Google Calendar service: {e}")
            self.service = None
    
    def get_calendar_events(self, start_date: datetime.date, 
                           end_date: Optional[datetime.date] = None) -> List[Dict[str, Any]]:
        """Get calendar events for a specific date range"""
        if not self.is_available():
            print("⚠️  Google Calendar service not available")
            return []
        
        if not end_date:
            end_date = start_date
        
        # Convert dates to datetime with timezone
        tz = pytz.timezone(self.timezone)
        start_datetime = datetime.datetime.combine(start_date, datetime.time.min).replace(tzinfo=tz)
        end_datetime = datetime.datetime.combine(end_date, datetime.time.max).replace(tzinfo=tz)
        
        # Format for Google Calendar API
        start_str = start_datetime.isoformat()
        end_str = end_datetime.isoformat()
        
        try:
            # Call the Calendar API
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_str,
                timeMax=end_str,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            
            return self._parse_events(events)
        except Exception as e:
            print(f"⚠️  Error retrieving Google Calendar events: {e}")
            return []
    
    def get_today_events(self) -> List[Dict[str, Any]]:
        """Get calendar events for today"""
        today = datetime.date.today()
        return self.get_calendar_events(today)
    
    def get_tomorrow_events(self) -> List[Dict[str, Any]]:
        """Get calendar events for tomorrow"""
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        return self.get_calendar_events(tomorrow)
    
    def get_week_events(self) -> List[Dict[str, Any]]:
        """Get calendar events for the current week"""
        today = datetime.date.today()
        end_of_week = today + datetime.timedelta(days=6)
        return self.get_calendar_events(today, end_of_week)
    
    def _parse_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse Google Calendar API response into a standard format"""
        parsed_events = []
        
        for event in events:
            # Extract event details
            title = event.get('summary', 'Untitled Event')
            
            # Parse start and end times
            start = event.get('start', {})
            end = event.get('end', {})
            
            start_time = None
            end_time = None
            all_day = False
            
            # Check if it's an all-day event
            if 'date' in start:
                all_day = True
                start_time = start.get('date')
                end_time = end.get('date')
            else:
                start_time = start.get('dateTime')
                end_time = end.get('dateTime')
            
            # Extract location and description
            location = event.get('location')
            description = event.get('description')
            
            # Extract conferencing data (for virtual meetings)
            conference_data = event.get('conferenceData')
            conference_link = None
            if conference_data:
                for entry_point in conference_data.get('entryPoints', []):
                    if entry_point.get('entryPointType') == 'video':
                        conference_link = entry_point.get('uri')
                        break
            
            # Extract attendees
            attendees = []
            for attendee in event.get('attendees', []):
                attendees.append(attendee.get('email'))
            
            # Create standardized event object
            parsed_events.append({
                'id': event.get('id'),
                'title': title,
                'start_time': start_time,
                'end_time': end_time,
                'all_day': all_day,
                'location': location,
                'description': description,
                'conference_link': conference_link,
                'attendees': attendees,
                'url': event.get('htmlLink')
            })
        
        return parsed_events
    
    def create_calendar_day(self, date: datetime.date) -> CalendarDay:
        """Create a CalendarDay object with events from Google Calendar"""
        day = CalendarDay(date)
        
        # Get Google Calendar events
        events = self.get_calendar_events(date)
        
        # Add events to the day
        for event in events:
            calendar_event = CalendarEvent(
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
            day.add_event(calendar_event)
        
        return day
