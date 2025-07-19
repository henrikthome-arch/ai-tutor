#!/usr/bin/env python3
"""
System Logger for AI Tutor Admin Dashboard
Handles centralized logging for all backend processes with SQL-based storage
"""

import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session
from app import db
from app.repositories.system_log_repository import SystemLogRepository
from app.config import Config

class SystemLogger:
    """Centralized system logger with SQL-based storage and web interface support"""
    
    def __init__(self, max_age_days: int = 30):
        """
        Initialize the system logger
        
        Args:
            max_age_days: Maximum age of logs before automatic deletion
        """
        self.max_age_days = max_age_days
        self.lock = threading.Lock()
        
        # Create a database session
        self.db_session = db.session
        
        # Initialize the repository
        self.repository = SystemLogRepository(self.db_session)
        
        # Initialize with startup log
        self.log('SYSTEM', 'SystemLogger initialized', {'max_age_days': max_age_days})
    
    def log(self, category: str, message: str, data: Optional[Dict[str, Any]] = None, level: str = 'INFO'):
        """
        Log a system event
        
        Args:
            category: Category of the log (WEBHOOK, AI_ANALYSIS, ADMIN, SYSTEM, etc.)
            message: Human-readable message
            data: Additional structured data
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        # Thread-safe logging
        with self.lock:
            try:
                self.repository.create(category, message, data, level)
            except Exception as e:
                # Fallback to console if database writing fails
                timestamp = datetime.now()
                print(f"[LOGGER ERROR] Failed to write log to database: {e}")
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
        Remove log entries older than max_age_days
        
        Returns:
            Dict with cleanup statistics
        """
        with self.lock:
            try:
                deleted_count = self.repository.cleanup_old_logs(self.max_age_days)
                
                # Log the cleanup operation
                if deleted_count > 0:
                    cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
                    self.log('SYSTEM', f"Cleaned up {deleted_count} old log entries", {
                        'deleted_entries': deleted_count,
                        'cutoff_date': cutoff_date.isoformat()
                    })
                
                return {
                    'deleted_entries': deleted_count,
                    'cutoff_date': (datetime.now() - timedelta(days=self.max_age_days)).isoformat()
                }
                
            except Exception as e:
                print(f"Error cleaning up old logs: {e}")
                return {
                    'deleted_entries': 0,
                    'error': str(e)
                }
    
    def get_logs(self, days: int = 7, category: Optional[str] = None, level: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve logs for display in admin interface
        
        Args:
            days: Number of recent days to retrieve
            category: Filter by category (optional)
            level: Filter by log level (optional)
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of log entries as dictionaries
        """
        with self.lock:
            try:
                logs = self.repository.get_logs(days, category, level, limit)
                return [log.to_dict() for log in logs]
            except Exception as e:
                print(f"Error retrieving logs: {e}")
                return []
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get statistics about the logging system"""
        with self.lock:
            try:
                return self.repository.get_log_statistics()
            except Exception as e:
                print(f"Error retrieving log statistics: {e}")
                return {
                    'error': str(e),
                    'total_log_entries': 0,
                    'categories': {},
                    'levels': {}
                }

# Global logger instance
system_logger = SystemLogger(max_age_days=Config.LOG_RETENTION_DAYS)

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