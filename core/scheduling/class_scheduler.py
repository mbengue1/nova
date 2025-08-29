"""
Smart Class Scheduling for Nova
Keeps Nova silent during your academic schedule
"""

import os
import yaml
import logging
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class ClassScheduler:
    """Smart scheduling based on your class schedule"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.schedule_data = None
        self.buffer_minutes = 15
        self.university_hours = {}
        self.nova_behavior = {}
        
        # Load configuration
        self._load_schedule()
        
        logging.info("🎓 Class Scheduler initialized")
    
    def _get_default_config_path(self) -> str:
        """Get default path for class schedule configuration"""
        # Look for config in current directory first, then user home
        current_dir = Path.cwd()
        config_paths = [
            current_dir / "config" / "class_schedule.yaml",
            Path.home() / ".nova" / "class_schedule.yaml",
            Path.home() / "nova" / "config" / "class_schedule.yaml"
        ]
        
        for path in config_paths:
            if path.exists():
                return str(path)
        
        # Return default path
        return str(current_dir / "config" / "class_schedule.yaml")
    
    def _load_schedule(self):
        """Load class schedule from configuration file"""
        try:
            if not os.path.exists(self.config_path):
                logging.warning(f"⚠️ Class schedule config not found at {self.config_path}")
                self._create_default_schedule()
                return
            
            with open(self.config_path, 'r') as f:
                self.schedule_data = yaml.safe_load(f)
            
            # Extract settings
            self.buffer_minutes = self.schedule_data.get('buffer_minutes', 15)
            self.university_hours = self.schedule_data.get('university_hours', {})
            self.nova_behavior = self.schedule_data.get('nova_behavior', {})
            
            logging.info(f"✅ Class schedule loaded from {self.config_path}")
            logging.info(f"   Buffer time: {self.buffer_minutes} minutes")
            logging.info(f"   University hours: {self.university_hours.get('enabled', False)}")
            
        except Exception as e:
            logging.error(f"❌ Failed to load class schedule: {e}")
            self._create_default_schedule()
    
    def _create_default_schedule(self):
        """Create a default schedule if none exists"""
        logging.info("📝 Creating default class schedule")
        
        self.schedule_data = {
            'buffer_minutes': 15,
            'class_schedule': {},
            'university_hours': {
                'enabled': True,
                'weekdays': [0, 1, 2, 3, 4],
                'start_time': '08:00',
                'end_time': '22:00'
            },
            'nova_behavior': {
                'respect_class_schedule': True,
                'respect_university_hours': True,
                'allow_manual_override': False,
                'log_silent_periods': True
            }
        }
        
        # Try to save default config
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(self.schedule_data, f, default_flow_style=False, indent=2)
            logging.info(f"✅ Default schedule saved to {self.config_path}")
        except Exception as e:
            logging.error(f"❌ Failed to save default schedule: {e}")
    
    def should_nova_run_now(self) -> Tuple[bool, str]:
        """
        Check if Nova should run now based on class schedule
        
        Returns:
            Tuple[bool, str]: (should_run, reason)
        """
        now = datetime.now()
        current_time = now.time()
        current_weekday = now.weekday()
        
        # Check if Nova behavior is enabled
        if not self.nova_behavior.get('respect_class_schedule', True):
            return True, "Class schedule protection disabled"
        
        # Check university hours first
        if self.university_hours.get('enabled', False):
            if not self._is_within_university_hours(current_time, current_weekday):
                return False, f"Outside university hours ({current_time.strftime('%H:%M')})"
        
        # Check class schedule
        if current_weekday in self.schedule_data.get('class_schedule', {}):
            classes = self.schedule_data['class_schedule'][current_weekday]
            
            for class_info in classes:
                if self._is_time_in_class_period(current_time, class_info):
                    return False, f"During class: {class_info.get('name', 'Unknown')}"
        
        return True, "Available time - no classes scheduled"
    
    def _is_within_university_hours(self, current_time: time, weekday: int) -> bool:
        """Check if current time is within general university hours"""
        if weekday not in self.university_hours.get('weekdays', []):
            return True  # Weekend
        
        start_time = self._parse_time(self.university_hours.get('start_time', '08:00'))
        end_time = self._parse_time(self.university_hours.get('end_time', '22:00'))
        
        return start_time <= current_time <= end_time
    
    def _is_time_in_class_period(self, current_time: time, class_info: Dict) -> bool:
        """Check if current time falls within a class period"""
        start_time = self._parse_time(class_info.get('start', '00:00'))
        end_time = self._parse_time(class_info.get('end', '23:59'))
        
        return start_time <= current_time <= end_time
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string (HH:MM) to time object"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        except (ValueError, AttributeError):
            logging.error(f"❌ Invalid time format: {time_str}")
            return time(0, 0)
    
    def get_current_class_info(self) -> Optional[Dict]:
        """Get information about current class if any"""
        now = datetime.now()
        current_time = now.time()
        current_weekday = now.weekday()
        
        if current_weekday not in self.schedule_data.get('class_schedule', {}):
            return None
        
        classes = self.schedule_data['class_schedule'][current_weekday]
        
        for class_info in classes:
            if self._is_time_in_class_period(current_time, class_info):
                return class_info
        
        return None
    
    def get_next_class_info(self) -> Optional[Dict]:
        """Get information about next upcoming class"""
        now = datetime.now()
        current_time = now.time()
        current_weekday = now.weekday()
        
        # Check today's remaining classes
        if current_weekday in self.schedule_data.get('class_schedule', {}):
            classes = self.schedule_data['class_schedule'][current_weekday]
            
            for class_info in classes:
                start_time = self._parse_time(class_info.get('start', '00:00'))
                if start_time > current_time:
                    return class_info
        
        # Check tomorrow's classes
        tomorrow = (current_weekday + 1) % 7
        if tomorrow in self.schedule_data.get('class_schedule', {}):
            classes = self.schedule_data['class_schedule'][tomorrow]
            if classes:
                return classes[0]
        
        return None
    
    def get_schedule_summary(self) -> str:
        """Get a human-readable summary of today's schedule"""
        now = datetime.now()
        current_weekday = now.weekday()
        
        if current_weekday not in self.schedule_data.get('class_schedule', {}):
            return "No classes scheduled today"
        
        classes = self.schedule_data['class_schedule'][current_weekday]
        if not classes:
            return "No classes scheduled today"
        
        summary = f"Today's classes ({now.strftime('%A')}):\n"
        for i, class_info in enumerate(classes, 1):
            name = class_info.get('name', 'Unknown')
            start = class_info.get('start', '00:00')
            end = class_info.get('end', '23:59')
            location = class_info.get('location', 'Unknown')
            
            summary += f"  {i}. {name}\n"
            summary += f"     Time: {start} - {end}\n"
            summary += f"     Location: {location}\n"
        
        return summary
    
    def reload_schedule(self):
        """Reload schedule from configuration file"""
        logging.info("🔄 Reloading class schedule")
        self._load_schedule()
    
    def is_configured(self) -> bool:
        """Check if class scheduler is properly configured"""
        return (
            self.schedule_data is not None and
            'class_schedule' in self.schedule_data and
            len(self.schedule_data['class_schedule']) > 0
        )
