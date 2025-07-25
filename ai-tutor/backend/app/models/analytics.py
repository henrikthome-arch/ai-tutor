"""
Data models for session analytics.
"""

from app import db
from sqlalchemy.sql import func
from datetime import datetime

class SessionMetrics(db.Model):
    """
    Metrics for individual tutoring sessions.
    """
    __tablename__ = 'session_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    duration_seconds = db.Column(db.Integer, nullable=False, default=0)
    message_count = db.Column(db.Integer, nullable=False, default=0)
    student_satisfaction = db.Column(db.Float, nullable=True)
    topic_coverage = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    session = db.relationship("Session", back_populates="metrics")
    
    # Additional metrics
    topics_covered = db.Column(db.JSON, nullable=True)
    student_engagement = db.Column(db.Float, nullable=True)
    learning_progress = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f"<SessionMetrics(id={self.id}, session_id={self.session_id})>"


class DailyStats(db.Model):
    """
    Aggregated daily statistics for the AI Tutor system.
    """
    __tablename__ = 'daily_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, unique=True)
    total_sessions = db.Column(db.Integer, nullable=False, default=0)
    avg_duration = db.Column(db.Float, nullable=False, default=0)
    total_users = db.Column(db.Integer, nullable=False, default=0)
    popular_topics = db.Column(db.JSON, nullable=True)  # JSON string of topic:count pairs
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Additional metrics
    total_session_time = db.Column(db.Integer, nullable=False, default=0)  # Total seconds
    avg_satisfaction = db.Column(db.Float, nullable=True)
    avg_engagement = db.Column(db.Float, nullable=True)
    avg_progress = db.Column(db.Float, nullable=True)
    
    def __repr__(self):
        return f"<DailyStats(date={self.date}, total_sessions={self.total_sessions})>"




# Backward compatibility alias
Analytics = SessionMetrics  # Use SessionMetrics as the default Analytics class