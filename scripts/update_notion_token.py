#!/usr/bin/env python3
"""
Script to update the Notion API token in the .env file
"""
import os
import sys

def update_notion_token():
    """Update the Notion API token in the .env file"""
    # Get the path to the .env file
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    
    # Check if .env file exists
    if not os.path.exists(env_path):
        print("❌ .env file not found.")
        return False
    
    # Get the new token from the user
    print("\n" + "="*60)
    print("🔑 Update Notion API Token")
    print("="*60)
    print("\nPlease paste your Notion Internal Integration Secret:")
    new_token = input("> ").strip()
    
    if not new_token:
        print("❌ No token provided.")
        return False
    
    # Read existing .env file
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Check if NOTION_API_KEY already exists
    token_exists = False
    for i, line in enumerate(lines):
        if line.startswith('NOTION_API_KEY='):
            lines[i] = f'NOTION_API_KEY={new_token}\n'
            token_exists = True
            break
    
    # If not, add it
    if not token_exists:
        lines.append('\n# Notion integration\n')
        lines.append(f'NOTION_API_KEY={new_token}\n')
    
    # Write back to .env file
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print("\n✅ Updated .env file with new Notion API token")
    print(f"   NOTION_API_KEY={new_token[:4]}...{new_token[-4:]}")
    
    # Verify the token
    print("\nVerifying the new token...")
    os.system(f"{sys.executable} {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify_notion_connection.py')}")
    
    return True

if __name__ == "__main__":
    update_notion_token()
