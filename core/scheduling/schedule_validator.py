"""
Schedule Validation for Nova Class Scheduler
Validates and validates class schedule configuration
"""

import yaml
import logging
from typing import Dict, List, Tuple, Optional
from datetime import time

class ScheduleValidator:
    """Validates class schedule configuration"""
    
    @staticmethod
    def validate_schedule(schedule_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate class schedule configuration
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required top-level keys
        required_keys = ['buffer_minutes', 'class_schedule', 'university_hours', 'nova_behavior']
        for key in required_keys:
            if key not in schedule_data:
                errors.append(f"Missing required key: {key}")
        
        if errors:
            return False, errors
        
        # Validate buffer minutes
        if not ScheduleValidator._validate_buffer_minutes(schedule_data['buffer_minutes']):
            errors.append("Invalid buffer_minutes: must be 0-60")
        
        # Validate class schedule
        schedule_errors = ScheduleValidator._validate_class_schedule(schedule_data['class_schedule'])
        errors.extend(schedule_errors)
        
        # Validate university hours
        hours_errors = ScheduleValidator._validate_university_hours(schedule_data['university_hours'])
        errors.extend(hours_errors)
        
        # Validate Nova behavior
        behavior_errors = ScheduleValidator._validate_nova_behavior(schedule_data['nova_behavior'])
        errors.extend(behavior_errors)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_buffer_minutes(buffer_minutes) -> bool:
        """Validate buffer minutes value"""
        try:
            buffer = int(buffer_minutes)
            return 0 <= buffer <= 60
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def _validate_class_schedule(class_schedule: Dict) -> List[str]:
        """Validate class schedule structure"""
        errors = []
        
        if not isinstance(class_schedule, dict):
            errors.append("class_schedule must be a dictionary")
            return errors
        
        # Check each day (0-6 for Monday-Sunday)
        for day_num in range(7):
            day_key = str(day_num)
            if day_key in class_schedule:
                day_classes = class_schedule[day_key]
                
                if not isinstance(day_classes, list):
                    errors.append(f"Day {day_num} classes must be a list")
                    continue
                
                # Validate each class
                for i, class_info in enumerate(day_classes):
                    class_errors = ScheduleValidator._validate_class_info(class_info, day_num, i)
                    errors.extend(class_errors)
        
        return errors
    
    @staticmethod
    def _validate_class_info(class_info: Dict, day_num: int, class_index: int) -> List[str]:
        """Validate individual class information"""
        errors = []
        
        if not isinstance(class_info, dict):
            errors.append(f"Day {day_num}, class {class_index}: must be a dictionary")
            return errors
        
        # Required fields
        required_fields = ['name', 'start', 'end']
        for field in required_fields:
            if field not in class_info:
                errors.append(f"Day {day_num}, class {class_index}: missing required field '{field}'")
        
        if errors:
            return errors
        
        # Validate time format
        start_time = class_info.get('start')
        end_time = class_info.get('end')
        
        if not ScheduleValidator._is_valid_time_format(start_time):
            errors.append(f"Day {day_num}, class {class_index}: invalid start time format '{start_time}' (use HH:MM)")
        
        if not ScheduleValidator._is_valid_time_format(end_time):
            errors.append(f"Day {day_num}, class {class_index}: invalid end time format '{end_time}' (use HH:MM)")
        
        # Validate time logic
        if start_time and end_time:
            if not ScheduleValidator._is_valid_time_range(start_time, end_time):
                errors.append(f"Day {day_num}, class {class_index}: end time must be after start time")
        
        return errors
    
    @staticmethod
    def _validate_university_hours(university_hours: Dict) -> List[str]:
        """Validate university hours configuration"""
        errors = []
        
        if not isinstance(university_hours, dict):
            errors.append("university_hours must be a dictionary")
            return errors
        
        # Check required fields
        if 'enabled' not in university_hours:
            errors.append("university_hours missing 'enabled' field")
        elif not isinstance(university_hours['enabled'], bool):
            errors.append("university_hours 'enabled' must be boolean")
        
        if 'weekdays' not in university_hours:
            errors.append("university_hours missing 'weekdays' field")
        elif not isinstance(university_hours['weekdays'], list):
            errors.append("university_hours 'weekdays' must be a list")
        else:
            # Validate weekday numbers
            for weekday in university_hours['weekdays']:
                if not isinstance(weekday, int) or weekday < 0 or weekday > 6:
                    errors.append("university_hours 'weekdays' must contain numbers 0-6")
        
        # Validate time format
        for time_field in ['start_time', 'end_time']:
            if time_field in university_hours:
                time_value = university_hours[time_field]
                if not ScheduleValidator._is_valid_time_format(time_value):
                    errors.append(f"university_hours '{time_field}' invalid format '{time_value}' (use HH:MM)")
        
        return errors
    
    @staticmethod
    def _validate_nova_behavior(nova_behavior: Dict) -> List[str]:
        """Validate Nova behavior configuration"""
        errors = []
        
        if not isinstance(nova_behavior, dict):
            errors.append("nova_behavior must be a dictionary")
            return errors
        
        # Check boolean fields
        boolean_fields = ['respect_class_schedule', 'respect_university_hours', 
                         'allow_manual_override', 'log_silent_periods']
        
        for field in boolean_fields:
            if field in nova_behavior:
                if not isinstance(nova_behavior[field], bool):
                    errors.append(f"nova_behavior '{field}' must be boolean")
        
        return errors
    
    @staticmethod
    def _is_valid_time_format(time_str: str) -> bool:
        """Check if time string is in valid HH:MM format"""
        if not isinstance(time_str, str):
            return False
        
        try:
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
            
            hour = int(parts[0])
            minute = int(parts[1])
            
            return 0 <= hour <= 23 and 0 <= minute <= 59
            
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def _is_valid_time_range(start_time: str, end_time: str) -> bool:
        """Check if end time is after start time"""
        try:
            start_parts = start_time.split(':')
            end_parts = end_time.split(':')
            
            start_hour = int(start_parts[0])
            start_minute = int(start_parts[1])
            end_hour = int(end_parts[0])
            end_minute = int(end_parts[1])
            
            start_total = start_hour * 60 + start_minute
            end_total = end_hour * 60 + end_minute
            
            return end_total > start_total
            
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def validate_yaml_file(file_path: str) -> Tuple[bool, List[str]]:
        """Validate a YAML configuration file"""
        try:
            with open(file_path, 'r') as f:
                schedule_data = yaml.safe_load(f)
            
            return ScheduleValidator.validate_schedule(schedule_data)
            
        except FileNotFoundError:
            return False, [f"Configuration file not found: {file_path}"]
        except yaml.YAMLError as e:
            return False, [f"Invalid YAML format: {e}"]
        except Exception as e:
            return False, [f"Error reading file: {e}"]
