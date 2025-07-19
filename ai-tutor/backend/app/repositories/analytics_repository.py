"""
Repository for analytics data access.
"""

from sqlalchemy import func, desc, and_
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from app.models.analytics import SessionMetrics, DailyStats, StudentProgress
from app.repositories.base_repository import BaseRepository

class AnalyticsRepository(BaseRepository):
    """Repository for analytics data access."""
    
    def __init__(self, session: Session):
        """Initialize with database session."""
        super().__init__(session)
    
    # Session Metrics Methods
    
    def get_session_metrics(self, session_id: str) -> SessionMetrics:
        """Get metrics for a specific session."""
        return self.session.query(SessionMetrics).filter_by(session_id=session_id).first()
    
    def create_session_metrics(self, metrics_data: dict) -> SessionMetrics:
        """Create new session metrics."""
        metrics = SessionMetrics(**metrics_data)
        self.session.add(metrics)
        self.session.commit()
        return metrics
    
    def update_session_metrics(self, session_id: str, metrics_data: dict) -> SessionMetrics:
        """Update existing session metrics."""
        metrics = self.get_session_metrics(session_id)
        if not metrics:
            return None
        
        for key, value in metrics_data.items():
            if hasattr(metrics, key):
                setattr(metrics, key, value)
        
        self.session.commit()
        return metrics
    
    # Daily Stats Methods
    
    def get_daily_stats(self, date: datetime) -> DailyStats:
        """Get stats for a specific date."""
        return self.session.query(DailyStats).filter(
            func.date(DailyStats.date) == func.date(date)
        ).first()
    
    def get_daily_stats_range(self, start_date: datetime, end_date: datetime) -> list:
        """Get stats for a date range."""
        return self.session.query(DailyStats).filter(
            DailyStats.date.between(start_date, end_date)
        ).order_by(DailyStats.date).all()
    
    def create_or_update_daily_stats(self, date: datetime, stats_data: dict) -> DailyStats:
        """Create or update daily stats."""
        stats = self.get_daily_stats(date)
        if stats:
            # Update existing stats
            for key, value in stats_data.items():
                if hasattr(stats, key):
                    setattr(stats, key, value)
        else:
            # Create new stats
            stats = DailyStats(date=date, **stats_data)
            self.session.add(stats)
        
        self.session.commit()
        return stats
    
    # Student Progress Methods
    
    def get_student_progress(self, student_id: str, subject: str = None) -> list:
        """Get progress records for a student, optionally filtered by subject."""
        query = self.session.query(StudentProgress).filter_by(student_id=student_id)
        
        if subject:
            query = query.filter_by(subject=subject)
        
        return query.order_by(StudentProgress.date).all()
    
    def get_latest_student_progress(self, student_id: str, subject: str) -> StudentProgress:
        """Get the most recent progress record for a student in a subject."""
        return self.session.query(StudentProgress).filter_by(
            student_id=student_id, subject=subject
        ).order_by(desc(StudentProgress.date)).first()
    
    def create_student_progress(self, progress_data: dict) -> StudentProgress:
        """Create a new student progress record."""
        progress = StudentProgress(**progress_data)
        self.session.add(progress)
        self.session.commit()
        return progress
    
    # Analytics Query Methods
    
    def get_popular_topics(self, days: int = 30) -> dict:
        """Get popular topics from the last N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get daily stats with popular topics
        stats = self.session.query(DailyStats).filter(
            DailyStats.date >= cutoff_date
        ).all()
        
        # Aggregate topics from all days
        topics_aggregate = {}
        for stat in stats:
            if stat.popular_topics:
                topics = stat.popular_topics
                for topic, count in topics.items():
                    topics_aggregate[topic] = topics_aggregate.get(topic, 0) + count
        
        # Sort by count (descending)
        return dict(sorted(
            topics_aggregate.items(), 
            key=lambda item: item[1], 
            reverse=True
        )[:10])  # Top 10 topics
    
    def get_student_engagement_over_time(self, student_id: str, days: int = 90) -> list:
        """Get a student's engagement metrics over time."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all session metrics for this student in the time period
        metrics = self.session.query(SessionMetrics).join(
            SessionMetrics.session
        ).filter(
            SessionMetrics.session.has(student_id=student_id),
            SessionMetrics.created_at >= cutoff_date
        ).order_by(SessionMetrics.created_at).all()
        
        return metrics
    
    def get_system_performance_metrics(self, days: int = 30) -> dict:
        """Get system performance metrics for the dashboard."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get daily stats for the period
        stats = self.get_daily_stats_range(cutoff_date, datetime.utcnow())
        
        # Calculate aggregate metrics
        total_sessions = sum(stat.total_sessions for stat in stats)
        total_users = sum(stat.total_users for stat in stats)
        avg_duration = sum(stat.avg_duration * stat.total_sessions for stat in stats) / total_sessions if total_sessions > 0 else 0
        
        # Get daily session counts for the chart
        daily_sessions = [(stat.date.strftime('%Y-%m-%d'), stat.total_sessions) for stat in stats]
        
        return {
            'total_sessions': total_sessions,
            'total_users': total_users,
            'avg_duration': avg_duration,
            'daily_sessions': daily_sessions,
            'popular_topics': self.get_popular_topics(days)
        }