"""
SystemLogRepository for managing system logs in the database
"""

from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.models.system_log import SystemLog

class SystemLogRepository:
    """Repository for managing system logs in the database"""
    
    def __init__(self, db_session: Session):
        """Initialize with a database session"""
        self.db_session = db_session
    
    def create(self, category: str, message: str, data: Optional[Dict[str, Any]] = None, level: str = 'INFO') -> SystemLog:
        """
        Create a new system log entry
        
        Args:
            category: Category of the log (WEBHOOK, AI_ANALYSIS, ADMIN, SYSTEM, etc.)
            message: Human-readable message
            data: Additional structured data
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            
        Returns:
            The created SystemLog object
        """
        log = SystemLog(
            timestamp=datetime.now(),
            category=category.upper(),
            level=level.upper(),
            message=message,
            data=data or {}
        )
        
        self.db_session.add(log)
        self.db_session.commit()
        return log
    
    def get_by_id(self, log_id: int) -> Optional[SystemLog]:
        """Get a log entry by ID"""
        return self.db_session.query(SystemLog).filter(SystemLog.id == log_id).first()
    
    def get_logs(self, days: int = 7, category: Optional[str] = None, level: Optional[str] = None, limit: int = 100) -> List[SystemLog]:
        """
        Get logs filtered by various criteria
        
        Args:
            days: Number of recent days to retrieve
            category: Filter by category (optional)
            level: Filter by log level (optional)
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of SystemLog objects
        """
        start_date = datetime.now() - timedelta(days=days)
        
        query = self.db_session.query(SystemLog).filter(SystemLog.timestamp >= start_date)
        
        if category:
            query = query.filter(SystemLog.category == category.upper())
        
        if level:
            query = query.filter(SystemLog.level == level.upper())
        
        return query.order_by(SystemLog.timestamp.desc()).limit(limit).all()
    
    def get_logs_by_date(self, date: datetime.date, category: Optional[str] = None, level: Optional[str] = None) -> List[SystemLog]:
        """Get logs for a specific date"""
        query = self.db_session.query(SystemLog).filter(
            func.date(SystemLog.timestamp) == date
        )
        
        if category:
            query = query.filter(SystemLog.category == category.upper())
        
        if level:
            query = query.filter(SystemLog.level == level.upper())
        
        return query.order_by(SystemLog.timestamp.desc()).all()
    
    def get_logs_by_date_range(self, start_date: datetime.date, end_date: datetime.date, 
                              category: Optional[str] = None, level: Optional[str] = None) -> List[SystemLog]:
        """Get logs for a date range"""
        query = self.db_session.query(SystemLog).filter(
            func.date(SystemLog.timestamp) >= start_date,
            func.date(SystemLog.timestamp) <= end_date
        )
        
        if category:
            query = query.filter(SystemLog.category == category.upper())
        
        if level:
            query = query.filter(SystemLog.level == level.upper())
        
        return query.order_by(SystemLog.timestamp.desc()).all()
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """
        Remove log entries older than the specified number of days
        
        Args:
            days: Maximum age of logs in days
            
        Returns:
            Number of deleted log entries
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted = self.db_session.query(SystemLog).filter(SystemLog.timestamp < cutoff_date).delete()
        self.db_session.commit()
        return deleted
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the logging system
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_log_entries': 0,
            'oldest_log_date': None,
            'newest_log_date': None,
            'categories': {},
            'levels': {}
        }
        
        # Get total count
        stats['total_log_entries'] = self.db_session.query(SystemLog).count()
        
        # Get date range
        oldest = self.db_session.query(func.min(SystemLog.timestamp)).scalar()
        newest = self.db_session.query(func.max(SystemLog.timestamp)).scalar()
        
        if oldest:
            stats['oldest_log_date'] = oldest.strftime('%Y-%m-%d')
        
        if newest:
            stats['newest_log_date'] = newest.strftime('%Y-%m-%d')
        
        # Get category counts
        category_counts = self.db_session.query(
            SystemLog.category, func.count(SystemLog.id)
        ).group_by(SystemLog.category).all()
        
        for category, count in category_counts:
            stats['categories'][category] = count
        
        # Get level counts
        level_counts = self.db_session.query(
            SystemLog.level, func.count(SystemLog.id)
        ).group_by(SystemLog.level).all()
        
        for level, count in level_counts:
            stats['levels'][level] = count
        
        return stats