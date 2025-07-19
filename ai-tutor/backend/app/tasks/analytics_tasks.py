"""
Background tasks for analytics processing.
"""

from app import celery, db
from sqlalchemy import func
import json
from datetime import datetime, timedelta
import logging

from app.models.analytics import DailyStats, SessionMetrics
from app.models.session import Session
from app.models.student import Student

logger = logging.getLogger(__name__)

@celery.task
def aggregate_daily_stats(date=None):
    """
    Aggregate session data into daily statistics.
    
    Args:
        date: Date to aggregate stats for (defaults to yesterday)
        
    Returns:
        String with aggregation results
    """
    logger.info("Starting daily stats aggregation")
    
    # Determine the date to aggregate
    if date is None:
        # Default to yesterday
        target_date = datetime.utcnow().date() - timedelta(days=1)
    else:
        if isinstance(date, str):
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
        else:
            target_date = date.date() if hasattr(date, 'date') else date
    
    start = datetime.combine(target_date, datetime.min.time())
    end = datetime.combine(target_date, datetime.max.time())
    
    logger.info(f"Aggregating stats for {target_date}")
    
    try:
        # Get sessions for the target date
        sessions = db.session.query(Session).filter(
            Session.created_at.between(start, end)
        ).all()
        
        if not sessions:
            logger.info(f"No sessions found for {target_date}")
            return f"No sessions found for {target_date}"
        
        # Calculate metrics
        total_sessions = len(sessions)
        
        # Calculate total duration and average
        total_duration = sum(s.duration_seconds for s in sessions if s.duration_seconds)
        avg_duration = total_duration / total_sessions if total_sessions > 0 else 0
        
        # Count unique students
        unique_students = set(s.student_id for s in sessions)
        total_users = len(unique_students)
        
        # Get session metrics for satisfaction and engagement
        session_ids = [s.id for s in sessions]
        metrics = db.session.query(SessionMetrics).filter(
            SessionMetrics.session_id.in_(session_ids)
        ).all()
        
        # Calculate average satisfaction and engagement
        satisfaction_values = [m.student_satisfaction for m in metrics if m.student_satisfaction is not None]
        engagement_values = [m.student_engagement for m in metrics if m.student_engagement is not None]
        
        avg_satisfaction = sum(satisfaction_values) / len(satisfaction_values) if satisfaction_values else None
        avg_engagement = sum(engagement_values) / len(engagement_values) if engagement_values else None
        
        # Aggregate topics
        topics = {}
        for metric in metrics:
            if metric.topics_covered:
                for topic in metric.topics_covered:
                    topics[topic] = topics.get(topic, 0) + 1
        
        # Sort topics by count
        sorted_topics = {k: v for k, v in sorted(
            topics.items(), key=lambda item: item[1], reverse=True
        )[:10]}  # Top 10 topics
        
        # Create or update daily stats
        stats = db.session.query(DailyStats).filter(
            func.date(DailyStats.date) == target_date
        ).first()
        
        if stats:
            # Update existing stats
            stats.total_sessions = total_sessions
            stats.avg_duration = avg_duration
            stats.total_users = total_users
            stats.popular_topics = sorted_topics
            stats.total_session_time = total_duration
            stats.avg_satisfaction = avg_satisfaction
            stats.avg_engagement = avg_engagement
            stats.updated_at = datetime.utcnow()
        else:
            # Create new stats
            stats = DailyStats(
                date=start,
                total_sessions=total_sessions,
                avg_duration=avg_duration,
                total_users=total_users,
                popular_topics=sorted_topics,
                total_session_time=total_duration,
                avg_satisfaction=avg_satisfaction,
                avg_engagement=avg_engagement
            )
            db.session.add(stats)
        
        db.session.commit()
        
        logger.info(f"Successfully aggregated stats for {target_date}")
        return f"Aggregated stats for {target_date}: {total_sessions} sessions, {total_users} users"
    
    except Exception as e:
        logger.error(f"Error aggregating daily stats: {str(e)}")
        db.session.rollback()
        raise


@celery.task
def calculate_student_progress(student_id, days=30):
    """
    Calculate progress for a student over time.
    
    Args:
        student_id: ID of the student
        days: Number of days to analyze
        
    Returns:
        Dictionary with progress data
    """
    logger.info(f"Calculating progress for student {student_id}")
    
    try:
        # Get date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all sessions for this student in the time period
        sessions = db.session.query(Session).filter(
            Session.student_id == student_id,
            Session.created_at.between(start_date, end_date)
        ).order_by(Session.created_at).all()
        
        if not sessions:
            logger.info(f"No sessions found for student {student_id}")
            return {"student_id": student_id, "progress": {}, "message": "No sessions found"}
        
        # Get session metrics
        session_ids = [s.id for s in sessions]
        metrics = db.session.query(SessionMetrics).filter(
            SessionMetrics.session_id.in_(session_ids)
        ).all()
        
        # Create a lookup for metrics by session_id
        metrics_by_session = {m.session_id: m for m in metrics}
        
        # Aggregate topics and calculate progress by subject
        topics_count = {}
        subjects = {}
        total_duration = 0
        
        for session in sessions:
            # Add duration
            duration = session.duration_seconds or 0
            total_duration += duration
            
            # Get metrics for this session
            metrics = metrics_by_session.get(session.id)
            if metrics and metrics.topics_covered:
                for topic in metrics.topics_covered:
                    topics_count[topic] = topics_count.get(topic, 0) + 1
                    
                    # Extract subject from topic (assuming format like "Math: Fractions")
                    subject = topic.split(':')[0].strip() if ':' in topic else topic
                    
                    if subject not in subjects:
                        subjects[subject] = {
                            "sessions": 0,
                            "duration": 0,
                            "engagement": [],
                            "satisfaction": []
                        }
                    
                    subjects[subject]["sessions"] += 1
                    subjects[subject]["duration"] += duration
                    
                    if metrics.student_engagement is not None:
                        subjects[subject]["engagement"].append(metrics.student_engagement)
                    
                    if metrics.student_satisfaction is not None:
                        subjects[subject]["satisfaction"].append(metrics.student_satisfaction)
        
        # Calculate averages for each subject
        progress_by_subject = {}
        for subject, data in subjects.items():
            avg_engagement = sum(data["engagement"]) / len(data["engagement"]) if data["engagement"] else None
            avg_satisfaction = sum(data["satisfaction"]) / len(data["satisfaction"]) if data["satisfaction"] else None
            
            progress_by_subject[subject] = {
                "sessions": data["sessions"],
                "total_duration": data["duration"],
                "avg_engagement": avg_engagement,
                "avg_satisfaction": avg_satisfaction,
                "percentage_of_total": (data["duration"] / total_duration * 100) if total_duration > 0 else 0
            }
        
        # Get top topics
        top_topics = sorted(topics_count.items(), key=lambda x: x[1], reverse=True)[:5]
        
        result = {
            "student_id": student_id,
            "total_sessions": len(sessions),
            "total_duration": total_duration,
            "progress_by_subject": progress_by_subject,
            "top_topics": dict(top_topics)
        }
        
        logger.info(f"Successfully calculated progress for student {student_id}")
        return result
    
    except Exception as e:
        logger.error(f"Error calculating student progress: {str(e)}")
        raise


@celery.task
def generate_system_report(days=30):
    """
    Generate a comprehensive system report.
    
    Args:
        days: Number of days to include in the report
        
    Returns:
        Dictionary with report data
    """
    logger.info(f"Generating system report for the last {days} days")
    
    try:
        # Get date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily stats for the period
        daily_stats = db.session.query(DailyStats).filter(
            DailyStats.date.between(start_date, end_date)
        ).order_by(DailyStats.date).all()
        
        # Get total sessions and users
        total_sessions = sum(stat.total_sessions for stat in daily_stats)
        
        # Get unique users across all days
        # Note: This is an approximation since daily_stats.total_users might count some users multiple times
        unique_users_count = db.session.query(func.count(func.distinct(Session.student_id))).filter(
            Session.created_at.between(start_date, end_date)
        ).scalar()
        
        # Calculate average metrics
        if total_sessions > 0:
            avg_duration = sum(stat.avg_duration * stat.total_sessions for stat in daily_stats) / total_sessions
            
            satisfaction_values = [stat.avg_satisfaction for stat in daily_stats if stat.avg_satisfaction is not None]
            avg_satisfaction = sum(satisfaction_values) / len(satisfaction_values) if satisfaction_values else None
            
            engagement_values = [stat.avg_engagement for stat in daily_stats if stat.avg_engagement is not None]
            avg_engagement = sum(engagement_values) / len(engagement_values) if engagement_values else None
        else:
            avg_duration = 0
            avg_satisfaction = None
            avg_engagement = None
        
        # Aggregate topics across all days
        topics_aggregate = {}
        for stat in daily_stats:
            if stat.popular_topics:
                for topic, count in stat.popular_topics.items():
                    topics_aggregate[topic] = topics_aggregate.get(topic, 0) + count
        
        # Sort topics by count
        top_topics = dict(sorted(
            topics_aggregate.items(), 
            key=lambda item: item[1], 
            reverse=True
        )[:10])  # Top 10 topics
        
        # Format daily data for charts
        daily_data = []
        for stat in daily_stats:
            daily_data.append({
                "date": stat.date.strftime('%Y-%m-%d'),
                "sessions": stat.total_sessions,
                "users": stat.total_users,
                "avg_duration": stat.avg_duration,
                "avg_satisfaction": stat.avg_satisfaction,
                "avg_engagement": stat.avg_engagement
            })
        
        report = {
            "period": {
                "start": start_date.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d'),
                "days": days
            },
            "summary": {
                "total_sessions": total_sessions,
                "unique_users": unique_users_count,
                "avg_duration": avg_duration,
                "avg_satisfaction": avg_satisfaction,
                "avg_engagement": avg_engagement
            },
            "top_topics": top_topics,
            "daily_data": daily_data,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Successfully generated system report")
        return report
    
    except Exception as e:
        logger.error(f"Error generating system report: {str(e)}")
        raise