"""
Notion API Client for Nova

This module provides a client for interacting with the Notion API,
specifically focused on retrieving calendar and task information.
"""
import os
import json
import datetime
import sys
from typing import List, Dict, Any, Optional
import requests

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import config

class NotionClient:
    """Client for interacting with Notion API"""
    
    def __init__(self):
        """Initialize the Notion client with API key from config"""
        self.api_key = config.notion_api_key
        self.database_id = config.notion_database_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"  # Use the latest API version
        }
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 300  # Cache results for 5 minutes
    
    def is_available(self) -> bool:
        """Check if the Notion API is available and configured"""
        return bool(self.api_key and self.database_id)
    
    def query_database(self, database_id: Optional[str] = None, 
                      filter_params: Optional[Dict[str, Any]] = None,
                      sorts: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Query a Notion database with optional filters and sorting"""
        if not self.is_available():
            print("⚠️  Notion API not configured")
            return []
        
        db_id = database_id or self.database_id
        if not db_id:
            print("⚠️  No database ID provided")
            return []
        
        # Create cache key based on parameters
        cache_key = f"db_{db_id}_{json.dumps(filter_params)}_{json.dumps(sorts)}"
        
        # Check cache first
        if cache_key in self.cache and self.cache_expiry.get(cache_key, 0) > datetime.datetime.now().timestamp():
            return self.cache[cache_key]
        
        # Prepare request payload
        payload = {}
        if filter_params:
            payload["filter"] = filter_params
        if sorts:
            payload["sorts"] = sorts
        
        try:
            response = requests.post(
                f"{self.base_url}/databases/{db_id}/query",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            
            # Cache results
            self.cache[cache_key] = results
            self.cache_expiry[cache_key] = datetime.datetime.now().timestamp() + self.cache_duration
            
            return results
        except Exception as e:
            print(f"⚠️  Error querying Notion database: {e}")
            return []
    
    def get_calendar_events(self, start_date: datetime.date, 
                           end_date: Optional[datetime.date] = None) -> List[Dict[str, Any]]:
        """Get calendar events for a specific date range"""
        if not end_date:
            end_date = start_date
        
        # Format dates for Notion API
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        
        # Create filter for date range
        date_filter = {
            "and": [
                {
                    "property": "Date",  # Adjust based on your actual property name
                    "date": {
                        "on_or_after": start_str
                    }
                },
                {
                    "property": "Date",  # Adjust based on your actual property name
                    "date": {
                        "on_or_before": end_str
                    }
                }
            ]
        }
        
        # Sort by date
        sorts = [
            {
                "property": "Date",  # Adjust based on your actual property name
                "direction": "ascending"
            }
        ]
        
        # Query database with filters
        events = self.query_database(filter_params=date_filter, sorts=sorts)
        
        return self._parse_events(events)
    
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
        """Parse raw Notion API response into a more usable format"""
        parsed_events = []
        
        for event in events:
            properties = event.get("properties", {})
            
            # Try to find the title property (usually "Name", "Title", or the first title-type property)
            title = None
            date_info = None
            
            # First, look for common title property names
            for name in ["Name", "Title", "Event", "Summary"]:
                if name in properties:
                    title_prop = properties.get(name, {})
                    if title_prop.get("type") == "title":
                        title = self._extract_property_value(title_prop)
                        break
            
            # If not found, find the first title-type property
            if title is None:
                for prop_name, prop_value in properties.items():
                    if prop_value.get("type") == "title":
                        title = self._extract_property_value(prop_value)
                        break
            
            # Find date property (usually "Date", "When", "Time", or the first date-type property)
            for name in ["Date", "When", "Time", "DateTime", "Schedule"]:
                if name in properties:
                    date_prop = properties.get(name, {})
                    if date_prop.get("type") == "date":
                        date_info = self._extract_property_value(date_prop)
                        break
            
            # If not found, find the first date-type property
            if date_info is None:
                for prop_name, prop_value in properties.items():
                    if prop_value.get("type") == "date":
                        date_info = self._extract_property_value(prop_value)
                        break
            
            # Try to find location and description properties
            location = None
            description = None
            tags = None
            
            # Look for location
            for name in ["Location", "Place", "Where"]:
                if name in properties:
                    location = self._extract_property_value(properties.get(name, {}))
                    if location:
                        break
            
            # Look for description
            for name in ["Description", "Notes", "Details", "Info"]:
                if name in properties:
                    description = self._extract_property_value(properties.get(name, {}))
                    if description:
                        break
            
            # Look for tags
            for name in ["Tags", "Category", "Type", "Label"]:
                if name in properties:
                    tags = self._extract_property_value(properties.get(name, {}))
                    if tags:
                        break
            
            # Format date information
            start_time = None
            end_time = None
            all_day = False
            
            if isinstance(date_info, dict):
                start = date_info.get("start")
                end = date_info.get("end")
                
                if start:
                    start_time = start
                if end:
                    end_time = end
                    
                # Check if it's an all-day event (no time component)
                if start and len(start) == 10:  # YYYY-MM-DD format
                    all_day = True
            
            # Only add events with at least a title and date
            if title and date_info:
                parsed_events.append({
                    "id": event.get("id"),
                    "title": title or "Untitled Event",
                    "start_time": start_time,
                    "end_time": end_time,
                    "all_day": all_day,
                    "location": location,
                    "description": description,
                    "tags": tags,
                    "url": f"https://notion.so/{event.get('id').replace('-', '')}"
                })
            else:
                print(f"⚠️  Skipping event with missing title or date: {title}")
        
        return parsed_events
    
    def _extract_property_value(self, property_data: Dict[str, Any]) -> Any:
        """Extract the actual value from a Notion property object"""
        if not property_data:
            return None
            
        property_type = property_data.get("type")
        
        if property_type == "title":
            title_items = property_data.get("title", [])
            if title_items:
                return "".join([item.get("plain_text", "") for item in title_items])
            return ""
            
        elif property_type == "rich_text":
            text_items = property_data.get("rich_text", [])
            if text_items:
                return "".join([item.get("plain_text", "") for item in text_items])
            return ""
            
        elif property_type == "date":
            return property_data.get("date")
            
        elif property_type == "select":
            select_data = property_data.get("select")
            if select_data:
                return select_data.get("name")
            return None
            
        elif property_type == "multi_select":
            multi_select = property_data.get("multi_select", [])
            return [item.get("name") for item in multi_select]
            
        elif property_type == "checkbox":
            return property_data.get("checkbox")
            
        elif property_type == "url":
            return property_data.get("url")
            
        # Add more property types as needed
        
        return None
