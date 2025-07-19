"""
Session repository for database operations
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date

from app import db
from app.models.session import Session

def get_all() -> List[Dict[str, Any]]:
    """
    Get all sessions
    
    Returns:
        List of session dictionaries
    """
    sessions = Session.query.all()
    return [session.to_dict() for session in sessions]

def get_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a session by ID
    
    Args:
        session_id: The session ID
        
    Returns:
        Session dictionary or None if not found
    """
    session = Session.query.get(session_id)
    return session.to_dict() if session else None

def get_by_student_id(student_id: str) -> List[Dict[str, Any]]:
    """
    Get all sessions for a student
    
    Args:
        student_id: The student ID
        
    Returns:
        List of session dictionaries
    """
    sessions = Session.query.filter_by(student_id=student_id).order_by(Session.start_datetime.desc()).all()
    return [session.to_dict() for session in sessions]

def get_by_date_range(start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """
    Get all sessions within a date range
    
    Args:
        start_date: The start date
        end_date: The end date
        
    Returns:
        List of session dictionaries
    """
    sessions = Session.query.filter(
        Session.start_datetime >= start_date,
        Session.start_datetime <= end_date
    ).order_by(Session.start_datetime.desc()).all()
    
    return [session.to_dict() for session in sessions]

def create(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new session
    
    Args:
        session_data: The session data
        
    Returns:
        The created session
    """
    session = Session(**session_data)
    db.session.add(session)
    db.session.commit()
    
    return session.to_dict()

def update(session_id: str, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update a session
    
    Args:
        session_id: The session ID
        session_data: The session data
        
    Returns:
        The updated session or None if not found
    """
    session = Session.query.get(session_id)
    if not session:
        return None
    
    for key, value in session_data.items():
        if hasattr(session, key):
            setattr(session, key, value)
    
    db.session.commit()
    
    return session.to_dict()

def delete(session_id: str) -> bool:
    """
    Delete a session
    
    Args:
        session_id: The session ID
        
    Returns:
        True if deleted, False if not found
    """
    session = Session.query.get(session_id)
    if not session:
        return False
    
    db.session.delete(session)
    db.session.commit()
    
    return True

def get_sessions_count() -> int:
    """
    Get the total number of sessions
    
    Returns:
        The total number of sessions
    """
    return Session.query.count()

def get_sessions_today_count() -> int:
    """
    Get the number of sessions today
    
    Returns:
        The number of sessions today
    """
    today = date.today()
    return Session.query.filter(
        Session.start_datetime >= today,
        Session.start_datetime < today.replace(day=today.day + 1)
    ).count()

def get_sessions_by_day() -> Dict[str, int]:
    """
    Get the number of sessions by day for the last 30 days
    
    Returns:
        Dictionary of day -> count
    """
    from sqlalchemy import func
    
    thirty_days_ago = date.today().replace(day=date.today().day - 30)
    
    # Query to get count by day
    results = db.session.query(
        func.date(Session.start_datetime).label('day'),
        func.count().label('count')
    ).filter(
        Session.start_datetime >= thirty_days_ago
    ).group_by(
        func.date(Session.start_datetime)
    ).all()
    
    # Convert to dictionary
    return {str(day): count for day, count in results}