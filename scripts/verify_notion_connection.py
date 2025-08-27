#!/usr/bin/env python3
"""
Script to verify Notion API connection
"""
import os
import sys
import json
import requests
from dotenv import load_dotenv

# Add the core directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_notion_connection():
    """Verify the Notion API connection"""
    # Load environment variables
    load_dotenv()
    
    # Get API key and database ID
    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    print("\n" + "="*60)
    print("🔍 Notion API Connection Verification")
    print("="*60)
    
    # Check if API key is set
    if not api_key:
        print("❌ NOTION_API_KEY not found in .env file")
        return False
    
    # Check if database ID is set
    if not database_id:
        print("❌ NOTION_DATABASE_ID not found in .env file")
        return False
    
    print(f"✅ NOTION_API_KEY found: {api_key[:4]}...{api_key[-4:]}")
    print(f"✅ NOTION_DATABASE_ID found: {database_id}")
    
    # Test Notion API connection
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Test the API by listing users
    print("\nTesting Notion API connection by listing users...")
    try:
        response = requests.get(
            "https://api.notion.com/v1/users",
            headers=headers
        )
        
        if response.status_code == 200:
            users = response.json().get("results", [])
            print(f"✅ Successfully connected to Notion API!")
            print(f"✅ Found {len(users)} users:")
            
            for user in users:
                user_type = user.get("type")
                if user_type == "person":
                    name = user.get("name", "Unknown")
                    print(f"  - {name} (Person)")
                elif user_type == "bot":
                    name = user.get("name", "Unknown")
                    print(f"  - {name} (Bot)")
        else:
            print(f"❌ Failed to connect to Notion API: {response.status_code} {response.reason}")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to Notion API: {e}")
        return False
    
    # Test database access
    print("\nTesting database access...")
    try:
        response = requests.get(
            f"https://api.notion.com/v1/databases/{database_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            db_info = response.json()
            db_title = "Unknown"
            
            # Extract database title
            title_property = db_info.get("title", [])
            if title_property:
                db_title = "".join([t.get("plain_text", "") for t in title_property])
            
            print(f"✅ Successfully accessed database: {db_title}")
            
            # Show database properties
            properties = db_info.get("properties", {})
            print(f"✅ Database has {len(properties)} properties:")
            
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get("type", "unknown")
                print(f"  - {prop_name} ({prop_type})")
            
            return True
        else:
            print(f"❌ Failed to access database: {response.status_code} {response.reason}")
            print(f"Error: {response.text}")
            
            if response.status_code == 404:
                print("\n⚠️  Database not found. Please check the database ID.")
                print("   Make sure you're using the correct ID from the database URL.")
            elif response.status_code == 401:
                print("\n⚠️  Unauthorized. Your integration token may be invalid or expired.")
                print("   Please check your NOTION_API_KEY in the .env file.")
            elif response.status_code == 403:
                print("\n⚠️  Permission denied. Your integration doesn't have access to this database.")
                print("   Please make sure you've shared the database with your integration:")
                print("   1. Go to your database in Notion")
                print("   2. Click the '...' menu in the top-right corner")
                print("   3. Select 'Add connections'")
                print("   4. Add your 'nova-integration'")
            
            return False
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return False

if __name__ == "__main__":
    verify_notion_connection()
