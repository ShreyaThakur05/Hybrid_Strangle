"""
Configuration manager for persistent config updates
"""

import json
import os
from datetime import datetime
from config import CONFIG

class ConfigManager:
    """Manages configuration persistence and updates"""
    
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self):
        """Load config from file or create default"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Create default config
            default_config = {
                'closed_date': '2025-12-11',
                'max_adjustment': 0,
                'spot_reference': 0.0
            }
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config=None):
        """Save config to file"""
        if config is None:
            config = self.config
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get_current_date(self):
        """Get current system date as string"""
        return datetime.now().strftime('%Y-%m-%d')
    
    def is_closed_today(self):
        """Check if already closed for today"""
        return self.config['closed_date'] == self.get_current_date()
    
    def is_closed_date_past(self):
        """Check if closed_date is less than system date"""
        return self.config['closed_date'] < self.get_current_date()
    
    def should_initiate(self):
        """Check if strategy should be initiated"""
        return (self.config['max_adjustment'] == 0 and 
                self.config['spot_reference'] == 0.0 and 
                self.is_closed_date_past())
    
    def should_adjust(self):
        """Check if adjustments should be made"""
        return (self.is_closed_date_past() and 
                self.config['max_adjustment'] != 0)
    
    def should_monitor(self):
        """Check if should enter monitoring mode"""
        return (self.config['max_adjustment'] == 0 and 
                self.is_closed_date_past() and 
                self.config['spot_reference'] != 0.0)
    
    def initiate_strategy(self, spot_value):
        """Update config after strategy initiation"""
        self.config['max_adjustment'] = 2
        self.config['spot_reference'] = float(spot_value)
        self._save_config()
    
    def decrement_adjustment(self):
        """Decrement max_adjustment after adjustment"""
        if self.config['max_adjustment'] > 0:
            self.config['max_adjustment'] -= 1
            self._save_config()
    
    def reset_for_next_day(self):
        """Reset config for next trading day"""
        self.config['spot_reference'] = 0.0
        self.config['max_adjustment'] = 0
        self.config['closed_date'] = self.get_current_date()
        self._save_config()
    
    def get_spot_reference(self):
        """Get current spot reference"""
        return self.config['spot_reference']
    
    def get_max_adjustment(self):
        """Get current max adjustment count"""
        return self.config['max_adjustment']
    
    def update_spot_reference(self, spot_value):
        """Update spot reference value"""
        self.config['spot_reference'] = float(spot_value)
        self._save_config()
    
    def reset_adjustments(self):
        """Reset adjustment count to maximum"""
        self.config['max_adjustment'] = 2
        self._save_config()