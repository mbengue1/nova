#!/usr/bin/env python3
"""
Text Processor for Nova - Converts raw data into natural, speakable text
"""

import re
from typing import List, Dict, Any
from datetime import datetime, time


class TextProcessor:
    """Processes text to make it natural and speakable"""
    
    @staticmethod
    def process_for_speech(text: str) -> str:
        """Main method to process text for natural speech output"""
        if not text:
            return text
            
        # Process in order of priority
        text = TextProcessor._clean_markdown(text)
        text = TextProcessor._process_time_formatting(text)
        text = TextProcessor._process_numbers_and_symbols(text)
        text = TextProcessor._process_abbreviations(text)
        text = TextProcessor._process_punctuation(text)
        text = TextProcessor._clean_whitespace(text)
        
        return text
    
    @staticmethod
    def _clean_markdown(text: str) -> str:
        """Remove markdown formatting"""
        # Remove bold/italic markers
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        # Remove code blocks
        text = re.sub(r'`(.*?)`', r'\1', text)
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # Remove bullet points and replace with natural language
        text = re.sub(r'^\s*[-•*]\s*', 'Next, ', text, flags=re.MULTILINE)
        text = re.sub(r'\n\s*[-•*]\s*', ', then ', text)
        
        # Remove headers
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        
        return text
    
    @staticmethod
    def _process_time_formatting(text: str) -> str:
        """Convert time formats to speakable text"""
        
        # Handle 24-hour time with colon (e.g., "14:30" -> "2 30 PM")
        def convert_24hr_time(match):
            time_str = match.group(1)
            try:
                # Parse the time
                hour, minute = map(int, time_str.split(':'))
                
                # Convert to 12-hour format
                if hour == 0:
                    return "12 AM"
                elif hour == 12:
                    return f"12 {minute:02d} PM" if minute > 0 else "12 PM"
                elif hour > 12:
                    return f"{hour - 12} {minute:02d} PM" if minute > 0 else f"{hour - 12} PM"
                else:
                    return f"{hour} {minute:02d} AM" if minute > 0 else f"{hour} AM"
            except:
                return match.group(0)
        
        # Handle 12-hour time with colon (e.g., "6:11 PM" -> "6 11 PM")
        def convert_12hr_time(match):
            time_str = match.group(1)
            ampm = match.group(2)
            try:
                hour, minute = map(int, time_str.split(':'))
                if minute == 0:
                    return f"{hour} {ampm}"
                else:
                    return f"{hour} {minute:02d} {ampm}"
            except:
                return match.group(0)
        
        # Process time in order of specificity to avoid conflicts
        
        # 1. Handle time ranges with AM/PM first (most specific)
        text = re.sub(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*(AM|PM)', 
                     lambda m: f"{TextProcessor._convert_time_to_speech(m.group(1))} to {TextProcessor._convert_time_to_speech(m.group(2))} {m.group(3)}", 
                     text, flags=re.IGNORECASE)
        
        # 2. Handle time ranges with mixed AM/PM
        text = re.sub(r'(\d{1,2}:\d{2})\s*(AM|PM)\s*-\s*(\d{1,2}:\d{2})\s*(AM|PM)', 
                     lambda m: f"{TextProcessor._convert_time_to_speech(m.group(1))} {m.group(2)} to {TextProcessor._convert_time_to_speech(m.group(3))} {m.group(4)}", 
                     text, flags=re.IGNORECASE)
        
        # 3. Handle time ranges without AM/PM
        text = re.sub(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})(?!\s*(AM|PM))', 
                     lambda m: f"{TextProcessor._convert_time_to_speech(m.group(1))} to {TextProcessor._convert_time_to_speech(m.group(2))}", 
                     text)
        
        # 4. Handle 12-hour time with AM/PM
        text = re.sub(r'(\d{1,2}:\d{2})\s*(AM|PM)', convert_12hr_time, text, flags=re.IGNORECASE)
        
        # 5. Handle 24-hour time without AM/PM (least specific)
        text = re.sub(r'(\d{1,2}:\d{2})(?!\s*(AM|PM))', convert_24hr_time, text)
        
        return text
    
    @staticmethod
    def _convert_time_to_speech(time_str: str) -> str:
        """Convert a single time string to speech format"""
        try:
            hour, minute = map(int, time_str.split(':'))
            if minute == 0:
                return str(hour)
            else:
                return f"{hour} {minute:02d}"
        except:
            return time_str
    
    @staticmethod
    def _process_numbers_and_symbols(text: str) -> str:
        """Process numbers and symbols for natural speech"""
        
        # Handle percentages
        text = re.sub(r'(\d+)%', r'\1 percent', text)
        
        # Handle fractions
        text = re.sub(r'(\d+)/(\d+)', r'\1 over \2', text)
        
        # Handle mathematical symbols (but not in time ranges or phone numbers)
        # Only replace standalone mathematical symbols, not those in context
        text = re.sub(r'\b\+\b', ' plus ', text)
        text = re.sub(r'\b-\b(?!\d)', ' minus ', text)  # Don't replace in time ranges
        text = re.sub(r'\b\*\b', ' times ', text)
        text = re.sub(r'\b/\b(?!\d)', ' divided by ', text)  # Don't replace in fractions
        text = re.sub(r'\b=\b', ' equals ', text)
        text = re.sub(r'\b<\b', ' less than ', text)
        text = re.sub(r'\b>\b', ' greater than ', text)
        
        # Handle currency
        text = re.sub(r'\$(\d+)', r'\1 dollars', text)
        text = re.sub(r'\$(\d+)\.(\d{2})', r'\1 dollars and \2 cents', text)
        
        # Handle phone numbers (e.g., "555-123-4567" -> "5 5 5 1 2 3 4 5 6 7")
        text = re.sub(r'(\d{3})-(\d{3})-(\d{4})', r'\1 \2 \3', text)
        
        # Handle dates (e.g., "2025-08-28" -> "August 28th, 2025")
        text = re.sub(r'(\d{4})-(\d{1,2})-(\d{1,2})', 
                     lambda m: TextProcessor._format_date_for_speech(m.group(1), m.group(2), m.group(3)), text)
        
        return text
    
    @staticmethod
    def _format_date_for_speech(year: str, month: str, day: str) -> str:
        """Format date components for speech"""
        try:
            month_names = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            
            month_idx = int(month) - 1
            if 0 <= month_idx < 12:
                month_name = month_names[month_idx]
            else:
                month_name = month
                
            # Add ordinal suffix to day
            day_num = int(day)
            if 10 <= day_num % 100 <= 20:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day_num % 10, 'th')
            
            return f"{month_name} {day}{suffix}, {year}"
        except:
            return f"{year}-{month}-{day}"
    
    @staticmethod
    def _process_abbreviations(text: str) -> str:
        """Expand common abbreviations for speech with context awareness"""
        
        # Academic abbreviations
        abbreviations = {
            # Time abbreviations - only expand when clearly time-related
            'AM': 'A M',
            'PM': 'P M',
            
            # Course codes - only expand when they look like course codes
            'CSC': 'C S C',
            'FMST': 'F M S T',
            
            # Location abbreviations
            'UR': 'U of R',
            'UofR': 'U of R',
            'NY': 'New York',
            'CA': 'California',
            'USA': 'U S A',
            
            # Academic degrees - only expand when clearly academic
            'PhD': 'P H D',
            'MBA': 'M B A',
            'BS': 'B S',
            'MS': 'M S',
            
            # Common abbreviations
            'vs.': 'versus',
            'etc.': 'and so on',
            'i.e.': 'that is',
            'e.g.': 'for example',
            
            # Titles - only expand when clearly titles
            'Dr.': 'Doctor',
            'Mr.': 'Mister',
            'Mrs.': 'Missus',
            'Ms.': 'Miss',
            'Prof.': 'Professor',
            
            # Address abbreviations - only expand when clearly addresses
            'St.': 'Street',
            'Ave.': 'Avenue',
            'Blvd.': 'Boulevard',
            'Rd.': 'Road',
            'Ln.': 'Lane',
            'Ct.': 'Court',
            'Pl.': 'Place',
            'Dr.': 'Drive'
        }
        
        # Apply abbreviations with context awareness
        for abbrev, expansion in abbreviations.items():
            if abbrev.lower() in ['am', 'pm']:
                # Only expand AM/PM when they're clearly time indicators
                # Pattern: number followed by AM/PM, not part of words like "I am"
                time_pattern = r'(?<!\w)(\d{1,2}(?::\d{2})?)\s*' + re.escape(abbrev) + r'(?!\w)'
                text = re.sub(time_pattern, r'\1 ' + expansion, text, flags=re.IGNORECASE)
                
            elif abbrev.lower() in ['csc', 'fmst']:
                # Only expand course codes when they look like course codes
                # Pattern: standalone course code, not part of other words
                course_pattern = r'\b' + re.escape(abbrev) + r'\b'
                text = re.sub(course_pattern, expansion, text, flags=re.IGNORECASE)
                
            elif abbrev.lower() in ['dr', 'mr', 'mrs', 'ms', 'prof']:
                # Only expand titles when they're clearly titles
                # Pattern: title followed by a name (capital letter)
                title_pattern = r'\b' + re.escape(abbrev) + r'\.\s+[A-Z]'
                text = re.sub(title_pattern, expansion + r'. ', text, flags=re.IGNORECASE)
                
            elif abbrev.lower() in ['st', 'ave', 'blvd', 'rd', 'ln', 'ct', 'pl']:
                # Only expand address abbreviations when they're clearly addresses
                # Pattern: number followed by address abbreviation
                address_pattern = r'(\d+)\s+' + re.escape(abbrev) + r'\.'
                text = re.sub(address_pattern, r'\1 ' + expansion, text, flags=re.IGNORECASE)
                
            else:
                # For other abbreviations, use normal word boundary replacement
                pattern = r'\b' + re.escape(abbrev) + r'\b'
                text = re.sub(pattern, expansion, text, flags=re.IGNORECASE)
        
        return text
    
    @staticmethod
    def _process_punctuation(text: str) -> str:
        """Process punctuation for natural speech"""
        
        # Replace multiple punctuation with natural pauses
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        text = re.sub(r'[.]{2,}', '.', text)
        
        # Handle special punctuation that might not be speakable
        text = re.sub(r'[;]', ',', text)  # Semicolon becomes comma
        text = re.sub(r'[:]', ',', text)  # Colon becomes comma (except in time)
        
        # Handle quotes more naturally
        text = re.sub(r'"([^"]*)"', r'\1', text)  # Remove quotes, keep content
        text = re.sub(r"'([^']*)'", r'\1', text)  # Remove single quotes
        
        # Handle parentheses more naturally
        text = re.sub(r'\(([^)]*)\)', r', \1,', text)
        
        # Handle brackets
        text = re.sub(r'\[([^\]]*)\]', r', \1,', text)
        text = re.sub(r'\{([^}]*)\}', r', \1,', text)
        
        return text
    
    @staticmethod
    def _clean_whitespace(text: str) -> str:
        """Clean up whitespace and formatting"""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Clean up multiple commas
        text = re.sub(r',\s*,', ',', text)
        text = re.sub(r',\s*$', '', text)  # Remove trailing comma
        
        # Clean up multiple periods
        text = re.sub(r'\.\s*\.', '.', text)
        
        # Ensure proper spacing around punctuation
        text = re.sub(r'\s*([,.!?])\s*', r'\1 ', text)
        
        # Remove double spaces
        text = re.sub(r' {2,}', ' ', text)
        
        return text
    
    @staticmethod
    def process_calendar_text(text: str) -> str:
        """Specialized processing for calendar-related text"""
        if not text:
            return text
            
        # Process time-specific formatting first
        text = TextProcessor._process_time_formatting(text)
        
        # Handle calendar-specific abbreviations
        calendar_abbrevs = {
            'Mon': 'Monday',
            'Tue': 'Tuesday',
            'Wed': 'Wednesday',
            'Thu': 'Thursday',
            'Fri': 'Friday',
            'Sat': 'Saturday',
            'Sun': 'Sunday',
            'Jan': 'January',
            'Feb': 'February',
            'Mar': 'March',
            'Apr': 'April',
            'Jun': 'June',
            'Jul': 'July',
            'Aug': 'August',
            'Sep': 'September',
            'Oct': 'October',
            'Nov': 'November',
            'Dec': 'December'
        }
        
        for abbrev, full in calendar_abbrevs.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            text = re.sub(pattern, full, text, flags=re.IGNORECASE)
        
        # Apply general processing
        return TextProcessor.process_for_speech(text)
    
    @staticmethod
    def process_technical_text(text: str) -> str:
        """Specialized processing for technical/system text"""
        if not text:
            return text
            
        # Handle technical abbreviations
        tech_abbrevs = {
            'CPU': 'C P U',
            'GPU': 'G P U',
            'RAM': 'R A M',
            'SSD': 'S S D',
            'HDD': 'H D D',
            'USB': 'U S B',
            'WiFi': 'Wi Fi',
            'VPN': 'V P N',
            'API': 'A P I',
            'URL': 'U R L',
            'HTTP': 'H T T P',
            'HTTPS': 'H T T P S',
            'JSON': 'Jason',
            'XML': 'X M L',
            'HTML': 'H T M L',
            'CSS': 'C S S',
            'JS': 'JavaScript',
            'Python': 'Python',
            'Java': 'Java',
            'C++': 'C plus plus',
            'C#': 'C sharp'
        }
        
        for abbrev, expansion in tech_abbrevs.items():
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            text = re.sub(pattern, expansion, text, flags=re.IGNORECASE)
        
        # Apply general processing
        return TextProcessor.process_for_speech(text)


# Convenience functions for common use cases
def make_speakable(text: str) -> str:
    """Convert any text to speakable format"""
    return TextProcessor.process_for_speech(text)


def make_calendar_speakable(text: str) -> str:
    """Convert calendar text to speakable format"""
    return TextProcessor.process_calendar_text(text)


def make_technical_speakable(text: str) -> str:
    """Convert technical text to speakable format"""
    return TextProcessor.process_technical_text(text)
