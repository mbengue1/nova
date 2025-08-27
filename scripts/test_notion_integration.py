#!/usr/bin/env python3
"""
Test script for Nova's Notion integration
"""
import os
import sys
import json
from datetime import datetime, timedelta

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Nova components
from core.integrations.notion_client import NotionClient
from core.services.calendar_service import CalendarService
from core.skills.calendar_skill import CalendarSkill
from config import config

def test_notion_client():
    """Test the Notion client configuration"""
    print("\n" + "="*60)
    print("🔍 Testing Notion Client Configuration")
    print("="*60)
    
    client = NotionClient()
    
    print(f"API Key configured: {'✅ Yes' if client.api_key else '❌ No'}")
    print(f"Database ID configured: {'✅ Yes' if client.database_id else '❌ No'}")
    print(f"Client is available: {'✅ Yes' if client.is_available() else '❌ No'}")
    
    if not client.is_available():
        print("\n⚠️  Notion client is not fully configured.")
        print("Make sure you have set the following in your .env file:")
        print("  NOTION_API_KEY=your_integration_secret")
        print("  NOTION_DATABASE_ID=your_database_id")
        return False
    
    return True

def test_notion_database_query():
    """Test querying the Notion database"""
    print("\n" + "="*60)
    print("🔍 Testing Notion Database Query")
    print("="*60)
    
    client = NotionClient()
    
    if not client.is_available():
        print("⚠️  Notion client not available, skipping database query test.")
        return False
    
    print("Querying database for events...")
    
    # Try to query events for the next 7 days
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
    events = client.get_calendar_events(today, next_week)
    
    print(f"Found {len(events)} events in the next 7 days.")
    
    if events:
        print("\nSample event details:")
        print(json.dumps(events[0], indent=2, default=str))
    else:
        print("\nNo events found. This could be normal if you don't have any events in your database,")
        print("or it could indicate an issue with the database ID or permissions.")
    
    return True

def test_calendar_service():
    """Test the calendar service"""
    print("\n" + "="*60)
    print("🔍 Testing Calendar Service")
    print("="*60)
    
    service = CalendarService()
    
    print("Getting today's schedule...")
    today = service.get_today_schedule()
    
    print(f"Found {len(today.events)} events for today.")
    print("\nFormatted schedule:")
    print(service.format_day_schedule(today))
    
    print("\nGetting tomorrow's schedule...")
    tomorrow = service.get_tomorrow_schedule()
    print(f"Found {len(tomorrow.events)} events for tomorrow.")
    
    print("\nGetting week schedule...")
    week = service.get_week_schedule()
    print(f"Retrieved schedule for {len(week)} days.")
    
    return True

def test_calendar_skill():
    """Test the calendar skill"""
    print("\n" + "="*60)
    print("🔍 Testing Calendar Skill")
    print("="*60)
    
    skill = CalendarSkill()
    
    test_queries = [
        "What do I have scheduled today?",
        "What's on my calendar for tomorrow?",
        "Show me my schedule for this week",
        "What do I have on Wednesday?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        response = skill.handle_query(query)
        print(f"Response: {response}")
    
    return True

def main():
    """Main test function"""
    print("\n🌟 Nova Notion Integration Test")
    
    # Run tests in sequence
    client_ok = test_notion_client()
    
    if client_ok:
        db_ok = test_notion_database_query()
        if db_ok:
            service_ok = test_calendar_service()
            if service_ok:
                skill_ok = test_calendar_skill()
    
    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)

if __name__ == "__main__":
    main()
