"""
Data models for session analytics.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime

class SessionMetrics(Base):
    """
    Metrics for individual tutoring sessions.
    """
    __tablename__ = 'session_metrics'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(50), ForeignKey('sessions.id'), nullable=False)
    duration_seconds = Column(Integer, nullable=False, default=0)
    message_count = Column(Integer, nullable=False, default=0)
    student_satisfaction = Column(Float, nullable=True)
    topic_coverage = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="metrics")
    
    # Additional metrics
    topics_covered = Column(JSON, nullable=True)
    student_engagement = Column(Float, nullable=True)
    learning_progress = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<SessionMetrics(id={self.id}, session_id={self.session_id})>"


class DailyStats(Base):
    """
    Aggregated daily statistics for the AI Tutor system.
    """
    __tablename__ = 'daily_stats'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, unique=True)
    total_sessions = Column(Integer, nullable=False, default=0)
    avg_duration = Column(Float, nullable=False, default=0)
    total_users = Column(Integer, nullable=False, default=0)
    popular_topics = Column(JSON, nullable=True)  # JSON string of topic:count pairs
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metrics
    total_session_time = Column(Integer, nullable=False, default=0)  # Total seconds
    avg_satisfaction = Column(Float, nullable=True)
    avg_engagement = Column(Float, nullable=True)
    avg_progress = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<DailyStats(date={self.date}, total_sessions={self.total_sessions})>"


class StudentProgress(Base):
    """
    Tracking student progress over time.
    """
    __tablename__ = 'student_progress'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(String(50), ForeignKey('students.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    subject = Column(String(100), nullable=False)
    proficiency_level = Column(Float, nullable=False, default=0)  # 0-100 scale
    sessions_count = Column(Integer, nullable=False, default=0)
    total_time_spent = Column(Integer, nullable=False, default=0)  # seconds
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # student = relationship("Student", back_populates="progress_records")
    
    def __repr__(self):
        return f"<StudentProgress(student_id={self.student_id}, subject={self.subject}, level={self.proficiency_level})>"