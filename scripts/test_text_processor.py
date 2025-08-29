#!/usr/bin/env python3
"""
Test script for Nova's Text Processor
"""

import sys
import os
sys.path.append('.')

def test_text_processor():
    """Test the text processor with various examples"""
    print("🧪 Testing Nova's Text Processor")
    print("=" * 50)
    
    try:
        from core.utils.text_processor import (
            TextProcessor, 
            make_speakable, 
            make_calendar_speakable,
            make_technical_speakable
        )
        print("✅ TextProcessor imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import TextProcessor: {e}")
        return
    
    # Test cases
    test_cases = [
            # Time formatting
            ("6:11 PM", "6 11 PM"),
            ("14:30", "2 30 PM"),
            ("9:00 AM", "9 AM"),
            ("2:30-4:00 PM", "2 30 to 4 PM"),
            
            # Calendar text
            ("Today you have CSC240 at 3:25 PM", "Today you have C S C 2 4 0 at 3 25 PM"),
            ("FMST210 at 6:15 PM", "F M S T 2 1 0 at 6 15 PM"),
            ("Class on Mon, Aug 28", "Class on Monday, August 28th, 2025"),
            
            # Technical text
            ("CPU usage is 50%", "C P U usage is 50 percent"),
            ("WiFi connection failed", "Wi Fi connection failed"),
            ("API endpoint /users", "A P I endpoint /users"),
            
            # Markdown and formatting
            ("**Bold text** and *italic*", "Bold text and italic"),
            ("- First item\n- Second item", "Next, First item, then Second item"),
            ("# Header text", "Header text"),
            
            # Punctuation and symbols
            ("Text with: colons; semicolons", "Text with, colons, semicolons"),
            ("Price: $25.99", "Price, 25 dollars and 99 cents"),
            ("Phone: 555-123-4567", "Phone, 5 5 5 1 2 3 4 5 6 7"),
            
            # Abbreviations
            ("Dr. Smith vs. Mr. Jones", "Doctor Smith versus Mister Jones"),
            ("UR campus in NY", "U of R campus in New York"),
            ("PhD student at UofR", "P H D student at U of R"),
            
            # Context awareness tests
            ("I am functioning optimally", "I am functioning optimally"),
            ("I am going to the store", "I am going to the store"),
            ("The meeting is at 3 PM", "The meeting is at 3 P M"),
            ("I am not sure about that", "I am not sure about that"),
            ("Class starts at 9 AM", "Class starts at 9 A M"),
            ("I am working on Nova", "I am working on Nova"),
        ]
    
    print("\n📝 Testing Text Processing:")
    print("-" * 30)
    
    for original, expected in test_cases:
        try:
            # Process the text
            processed = make_speakable(original)
            
            # Display results
            print(f"Original: {original}")
            print(f"Processed: {processed}")
            print(f"Expected: {expected}")
            print("-" * 30)
            
        except Exception as e:
            print(f"❌ Error processing '{original}': {e}")
            print("-" * 30)
    
    # Test calendar-specific processing
    print("\n📅 Testing Calendar Text Processing:")
    print("-" * 30)
    
    calendar_texts = [
        "CSC240 at 3:25 PM in Hylan 101",
        "FMST210 on Thu, Aug 28 at 6:15 PM",
        "Meeting from 2:30-4:00 PM",
        "Class schedule: Mon-Fri, 9:00 AM-5:00 PM"
    ]
    
    for text in calendar_texts:
        try:
            processed = make_calendar_speakable(text)
            print(f"Original: {text}")
            print(f"Processed: {processed}")
            print("-" * 30)
        except Exception as e:
            print(f"❌ Error processing calendar text '{text}': {e}")
            print("-" * 30)
    
    # Test technical text processing
    print("\n💻 Testing Technical Text Processing:")
    print("-" * 30)
    
    tech_texts = [
        "CPU usage: 75%, RAM: 8GB, SSD: 256GB",
        "WiFi connection to VPN server",
        "API response: HTTP 200 OK, JSON format",
        "Python script with C++ library"
    ]
    
    for text in tech_texts:
        try:
            processed = make_technical_speakable(text)
            print(f"Original: {text}")
            print(f"Processed: {processed}")
            print("-" * 30)
        except Exception as e:
            print(f"❌ Error processing technical text '{text}': {e}")
            print("-" * 30)
    
    print("\n🎉 Text Processor Test Complete!")

if __name__ == "__main__":
    test_text_processor()
