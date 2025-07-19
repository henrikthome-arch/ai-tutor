"""
Service for analytics functionality.
"""

from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional

from app.repositories.analytics_repository import AnalyticsRepository
from app.tasks.analytics_tasks import aggregate_daily_stats

class AnalyticsService:
    """Service for analytics functionality."""
    
    def __init__(self, db_session):
        """Initialize with database session."""
        self.repository = AnalyticsRepository(db_session)
    
    def get_dashboard_data(self, time_range: str = 'week') -> Dict[str, Any]:
        """
        Get data for the analytics dashboard.
        
        Args:
            time_range: 'week', 'month', 'quarter', or 'year'
            
        Returns:
            Dictionary with dashboard data
        """
        today = datetime.utcnow().date()
        
        # Determine date range based on time_range
        if time_range == 'week':
            start_date = today - timedelta(days=7)
        elif time_range == 'month':
            start_date = today - timedelta(days=30)
        elif time_range == 'quarter':
            start_date = today - timedelta(days=90)
        elif time_range == 'year':
            start_date = today - timedelta(days=365)
        else:
            # Default to week
            start_date = today - timedelta(days=7)
            time_range = 'week'
        
        # Get daily stats for the date range
        daily_stats = self.repository.get_daily_stats_range(
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(today, datetime.max.time())
        )
        
        # Get popular topics for the same period
        days = (today - start_date).days
        popular_topics = self.repository.get_popular_topics(days=days)
        
        # Get system performance metrics
        performance_metrics = self.repository.get_system_performance_metrics(days=days)
        
        # Format data for the dashboard
        formatted_stats = []
        for stat in daily_stats:
            formatted_stats.append({
                'date': stat.date.strftime('%Y-%m-%d'),
                'total_sessions': stat.total_sessions,
                'avg_duration': stat.avg_duration,
                'total_users': stat.total_users,
                'avg_satisfaction': stat.avg_satisfaction,
                'avg_engagement': stat.avg_engagement
            })
        
        return {
            'daily_stats': formatted_stats,
            'popular_topics': popular_topics,
            'performance_metrics': performance_metrics,
            'time_range': time_range
        }
    
    def get_student_analytics(self, student_id: str) -> Dict[str, Any]:
        """
        Get analytics data for a specific student.
        
        Args:
            student_id: ID of the student
            
        Returns:
            Dictionary with student analytics data
        """
        # Get student progress records
        progress_records = self.repository.get_student_progress(student_id)
        
        # Get engagement metrics
        engagement_metrics = self.repository.get_student_engagement_over_time(student_id)
        
        # Format progress data by subject
        progress_by_subject = {}
        for record in progress_records:
            subject = record.subject
            if subject not in progress_by_subject:
                progress_by_subject[subject] = []
            
            progress_by_subject[subject].append({
                'date': record.date.strftime('%Y-%m-%d'),
                'proficiency_level': record.proficiency_level,
                'sessions_count': record.sessions_count,
                'total_time_spent': record.total_time_spent
            })
        
        # Format engagement data
        engagement_data = []
        for metric in engagement_metrics:
            engagement_data.append({
                'date': metric.created_at.strftime('%Y-%m-%d'),
                'duration': metric.duration_seconds,
                'engagement': metric.student_engagement,
                'satisfaction': metric.student_satisfaction,
                'topics': metric.topics_covered
            })
        
        return {
            'progress_by_subject': progress_by_subject,
            'engagement_data': engagement_data
        }
    
    def record_session_metrics(self, session_id: str, metrics_data: Dict[str, Any]) -> bool:
        """
        Record metrics for a tutoring session.
        
        Args:
            session_id: ID of the session
            metrics_data: Dictionary with metrics data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if metrics already exist for this session
            existing_metrics = self.repository.get_session_metrics(session_id)
            
            if existing_metrics:
                # Update existing metrics
                self.repository.update_session_metrics(session_id, metrics_data)
            else:
                # Create new metrics
                metrics_data['session_id'] = session_id
                self.repository.create_session_metrics(metrics_data)
            
            return True
        except Exception as e:
            print(f"Error recording session metrics: {e}")
            return False
    
    def update_student_progress(self, student_id: str, subject: str, 
                               proficiency_delta: float, session_time: int) -> bool:
        """
        Update a student's progress in a subject.
        
        Args:
            student_id: ID of the student
            subject: Subject name
            proficiency_delta: Change in proficiency level
            session_time: Time spent in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the latest progress record for this student and subject
            latest_progress = self.repository.get_latest_student_progress(student_id, subject)
            
            # Calculate new proficiency level
            if latest_progress:
                new_level = min(100, max(0, latest_progress.proficiency_level + proficiency_delta))
                sessions_count = latest_progress.sessions_count + 1
                total_time = latest_progress.total_time_spent + session_time
            else:
                new_level = min(100, max(0, proficiency_delta))
                sessions_count = 1
                total_time = session_time
            
            # Create a new progress record
            progress_data = {
                'student_id': student_id,
                'date': datetime.utcnow(),
                'subject': subject,
                'proficiency_level': new_level,
                'sessions_count': sessions_count,
                'total_time_spent': total_time
            }
            
            self.repository.create_student_progress(progress_data)
            return True
        except Exception as e:
            print(f"Error updating student progress: {e}")
            return False
    
    def schedule_metrics_aggregation(self) -> str:
        """
        Schedule the daily metrics aggregation task.
        
        Returns:
            Task ID
        """
        # Use Celery to schedule the task
        task = aggregate_daily_stats.delay()
        return task.id
    
    def get_aggregation_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a metrics aggregation task.
        
        Args:
            task_id: ID of the Celery task
            
        Returns:
            Dictionary with task status
        """
        from celery.result import AsyncResult
        
        task_result = AsyncResult(task_id)
        
        if task_result.ready():
            if task_result.successful():
                return {
                    'status': 'completed',
                    'result': task_result.result
                }
            else:
                return {
                    'status': 'failed',
                    'error': str(task_result.result)
                }
        else:
            return {
                'status': 'processing'
            }