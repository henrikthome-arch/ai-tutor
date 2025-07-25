"""
Repository for analytics data access.
"""

from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from app import db
from app.models.analytics import SessionMetrics, DailyStats

# Session Metrics Methods

def get_session_metrics(session_id: str) -> Optional[SessionMetrics]:
    """Get metrics for a specific session."""
    return SessionMetrics.query.filter_by(session_id=session_id).first()

def create_session_metrics(metrics_data: dict) -> SessionMetrics:
    """Create new session metrics."""
    try:
        metrics = SessionMetrics(**metrics_data)
        db.session.add(metrics)
        db.session.commit()
        return metrics
    except Exception as e:
        db.session.rollback()
        print(f"Error creating session metrics: {e}")
        raise e

def update_session_metrics(session_id: str, metrics_data: dict) -> Optional[SessionMetrics]:
    """Update existing session metrics."""
    try:
        metrics = get_session_metrics(session_id)
        if not metrics:
            return None
        
        for key, value in metrics_data.items():
            if hasattr(metrics, key):
                setattr(metrics, key, value)
        
        db.session.commit()
        return metrics
    except Exception as e:
        db.session.rollback()
        print(f"Error updating session metrics: {e}")
        raise e

# Daily Stats Methods

def get_daily_stats(date: datetime) -> Optional[DailyStats]:
    """Get stats for a specific date."""
    return DailyStats.query.filter(
        func.date(DailyStats.date) == func.date(date)
    ).first()

def get_daily_stats_range(start_date: datetime, end_date: datetime) -> List[DailyStats]:
    """Get stats for a date range."""
    return DailyStats.query.filter(
        DailyStats.date.between(start_date, end_date)
    ).order_by(DailyStats.date).all()

def create_or_update_daily_stats(date: datetime, stats_data: dict) -> DailyStats:
    """Create or update daily stats."""
    try:
        stats = get_daily_stats(date)
        if stats:
            # Update existing stats
            for key, value in stats_data.items():
                if hasattr(stats, key):
                    setattr(stats, key, value)
        else:
            # Create new stats
            stats = DailyStats(date=date, **stats_data)
            db.session.add(stats)
        
        db.session.commit()
        return stats
    except Exception as e:
        db.session.rollback()
        print(f"Error creating/updating daily stats: {e}")
        raise e

# Analytics Query Methods

def get_popular_topics(days: int = 30) -> dict:
    """Get popular topics from the last N days."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get daily stats with popular topics
    stats = DailyStats.query.filter(
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

def get_student_engagement_over_time(student_id: str, days: int = 90) -> List[SessionMetrics]:
    """Get a student's engagement metrics over time."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all session metrics for this student in the time period
    metrics = SessionMetrics.query.join(
        SessionMetrics.session
    ).filter(
        SessionMetrics.session.has(student_id=student_id),
        SessionMetrics.created_at >= cutoff_date
    ).order_by(SessionMetrics.created_at).all()
    
    return metrics

def get_system_performance_metrics(days: int = 30) -> dict:
    """Get system performance metrics for the dashboard."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get daily stats for the period
    stats = get_daily_stats_range(cutoff_date, datetime.utcnow())
    
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
        'popular_topics': get_popular_topics(days)
    }