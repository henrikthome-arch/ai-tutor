#!/usr/bin/env python3
"""
System Logger for AI Tutor Admin Dashboard
Handles centralized logging for all backend processes with automatic cleanup
"""

import os
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class SystemLogger:
    """Centralized system logger with automatic cleanup and web interface support"""
    
    def __init__(self, log_dir: str = '../data/logs', max_age_days: int = 30):
        """
        Initialize the system logger
        
        Args:
            log_dir: Directory to store log files
            max_age_days: Maximum age of logs before automatic deletion
        """
        self.log_dir = log_dir
        self.max_age_days = max_age_days
        self.lock = threading.Lock()
        
        # Create logs directory
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Initialize with startup log
        self.log('SYSTEM', 'SystemLogger initialized', {'log_dir': log_dir, 'max_age_days': max_age_days})
    
    def log(self, category: str, message: str, data: Optional[Dict[str, Any]] = None, level: str = 'INFO'):
        """
        Log a system event
        
        Args:
            category: Category of the log (WEBHOOK, AI_ANALYSIS, ADMIN, SYSTEM, etc.)
            message: Human-readable message
            data: Additional structured data
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        timestamp = datetime.now()
        
        log_entry = {
            'timestamp': timestamp.isoformat(),
            'category': category.upper(),
            'level': level.upper(),
            'message': message,
            'data': data or {},
            'date': timestamp.strftime('%Y-%m-%d'),
            'time': timestamp.strftime('%H:%M:%S')
        }
        
        # Determine log file path (one file per day)
        log_file = os.path.join(self.log_dir, f"{timestamp.strftime('%Y-%m-%d')}.jsonl")
        
        # Thread-safe writing
        with self.lock:
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            except Exception as e:
                # Fallback to console if file writing fails
                print(f"[LOGGER ERROR] Failed to write log: {e}")
                print(f"[{timestamp.isoformat()}] {category.upper()}/{level.upper()}: {message}")
    
    def log_webhook(self, event_type: str, message: str, **kwargs):
        """Log VAPI webhook events"""
        self.log('WEBHOOK', message, {
            'event_type': event_type,
            **kwargs
        })
    
    def log_ai_analysis(self, message: str, **kwargs):
        """Log AI analysis events"""
        self.log('AI_ANALYSIS', message, kwargs)
    
    def log_admin_action(self, action: str, user: str, **kwargs):
        """Log admin interface actions"""
        self.log('ADMIN', f"{user} performed: {action}", {
            'action': action,
            'user': user,
            **kwargs
        })
    
    def log_error(self, category: str, message: str, error: Exception, **kwargs):
        """Log errors with exception details"""
        self.log(category, message, {
            'error_type': type(error).__name__,
            'error_message': str(error),
            **kwargs
        }, level='ERROR')
    
    def cleanup_old_logs(self) -> Dict[str, int]:
        """
        Remove log files older than max_age_days
        
        Returns:
            Dict with cleanup statistics
        """
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        deleted_count = 0
        deleted_size = 0
        
        with self.lock:
            try:
                for filename in os.listdir(self.log_dir):
                    if filename.endswith('.jsonl'):
                        try:
                            # Parse date from filename (YYYY-MM-DD.jsonl)
                            date_str = filename.replace('.jsonl', '')
                            file_date = datetime.strptime(date_str, '%Y-%m-%d')
                            
                            if file_date < cutoff_date:
                                file_path = os.path.join(self.log_dir, filename)
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                deleted_count += 1
                                deleted_size += file_size
                                
                        except (ValueError, OSError) as e:
                            print(f"Error processing log file {filename}: {e}")
                            
            except OSError as e:
                print(f"Error accessing log directory: {e}")
        
        # Log the cleanup operation
        if deleted_count > 0:
            self.log('SYSTEM', f"Cleaned up {deleted_count} old log files", {
                'deleted_files': deleted_count,
                'deleted_bytes': deleted_size,
                'cutoff_date': cutoff_date.isoformat()
            })
        
        return {
            'deleted_files': deleted_count,
            'deleted_bytes': deleted_size,
            'cutoff_date': cutoff_date.isoformat()
        }
    
    def get_logs(self, days: int = 7, category: Optional[str] = None, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve logs for display in admin interface
        
        Args:
            days: Number of recent days to retrieve
            category: Filter by category (optional)
            level: Filter by log level (optional)
            
        Returns:
            List of log entries
        """
        logs = []
        start_date = datetime.now() - timedelta(days=days)
        
        with self.lock:
            try:
                for filename in sorted(os.listdir(self.log_dir), reverse=True):
                    if filename.endswith('.jsonl'):
                        try:
                            date_str = filename.replace('.jsonl', '')
                            file_date = datetime.strptime(date_str, '%Y-%m-%d')
                            
                            if file_date >= start_date:
                                file_path = os.path.join(self.log_dir, filename)
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    for line in f:
                                        try:
                                            log_entry = json.loads(line.strip())
                                            
                                            # Apply filters
                                            if category and log_entry.get('category') != category.upper():
                                                continue
                                            if level and log_entry.get('level') != level.upper():
                                                continue
                                            
                                            logs.append(log_entry)
                                            
                                        except json.JSONDecodeError:
                                            continue
                                            
                        except (ValueError, OSError):
                            continue
                            
            except OSError:
                pass
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return logs
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get statistics about the logging system"""
        stats = {
            'total_log_files': 0,
            'total_log_entries': 0,
            'total_size_bytes': 0,
            'oldest_log_date': None,
            'newest_log_date': None,
            'categories': {},
            'levels': {}
        }
        
        with self.lock:
            try:
                log_files = [f for f in os.listdir(self.log_dir) if f.endswith('.jsonl')]
                stats['total_log_files'] = len(log_files)
                
                if log_files:
                    # Get date range
                    dates = []
                    for filename in log_files:
                        try:
                            date_str = filename.replace('.jsonl', '')
                            dates.append(datetime.strptime(date_str, '%Y-%m-%d'))
                        except ValueError:
                            continue
                    
                    if dates:
                        stats['oldest_log_date'] = min(dates).strftime('%Y-%m-%d')
                        stats['newest_log_date'] = max(dates).strftime('%Y-%m-%d')
                    
                    # Count entries and analyze categories/levels
                    for filename in log_files:
                        file_path = os.path.join(self.log_dir, filename)
                        try:
                            file_size = os.path.getsize(file_path)
                            stats['total_size_bytes'] += file_size
                            
                            with open(file_path, 'r', encoding='utf-8') as f:
                                for line in f:
                                    try:
                                        log_entry = json.loads(line.strip())
                                        stats['total_log_entries'] += 1
                                        
                                        category = log_entry.get('category', 'UNKNOWN')
                                        level = log_entry.get('level', 'UNKNOWN')
                                        
                                        stats['categories'][category] = stats['categories'].get(category, 0) + 1
                                        stats['levels'][level] = stats['levels'].get(level, 0) + 1
                                        
                                    except json.JSONDecodeError:
                                        continue
                                        
                        except OSError:
                            continue
                            
            except OSError:
                pass
        
        return stats

# Global logger instance
system_logger = SystemLogger()

# Convenience functions
def log_system(message: str, **kwargs):
    """Log a system event"""
    system_logger.log('SYSTEM', message, kwargs)

def log_webhook(event_type: str, message: str, **kwargs):
    """Log a webhook event"""
    system_logger.log_webhook(event_type, message, **kwargs)

def log_ai_analysis(message: str, **kwargs):
    """Log an AI analysis event"""
    system_logger.log_ai_analysis(message, **kwargs)

def log_admin_action(action: str, user: str, **kwargs):
    """Log an admin action"""
    system_logger.log_admin_action(action, user, **kwargs)

def log_error(category: str, message: str, error: Exception, **kwargs):
    """Log an error"""
    system_logger.log_error(category, message, error, **kwargs)