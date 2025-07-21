"""
Session service for managing session data
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from app import db
from app.models.session import Session
from app.models.student import Student


class SessionService:
    """Service class for session operations"""
    
    def __init__(self):
        pass
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all sessions
        
        Returns:
            List of session dictionaries
        """
        try:
            sessions = Session.query.all()
            return [session.to_dict() for session in sessions] if hasattr(Session, 'to_dict') else []
        except Exception as e:
            print(f"Error getting all sessions: {e}")
            return []
    
    def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session by ID
        
        Args:
            session_id: The session ID
            
        Returns:
            Session dictionary or None if not found
        """
        try:
            session = Session.query.get(int(session_id))
            return session.to_dict() if session and hasattr(session, 'to_dict') else None
        except Exception as e:
            print(f"Error getting session {session_id}: {e}")
            return None
    
    def get_sessions_by_student_id(self, student_id: str) -> List[Dict[str, Any]]:
        """
        Get all sessions for a student
        
        Args:
            student_id: The student ID
            
        Returns:
            List of session dictionaries
        """
        try:
            sessions = Session.query.filter_by(student_id=int(student_id)).all()
            return [session.to_dict() for session in sessions] if hasattr(Session, 'to_dict') else []
        except Exception as e:
            print(f"Error getting sessions for student {student_id}: {e}")
            return []
    
    def get_student_sessions(self, student_id: str) -> List[Dict[str, Any]]:
        """
        Get sessions for a specific student (alias for get_sessions_by_student_id)
        
        Args:
            student_id: The student ID
            
        Returns:
            List of session dictionaries
        """
        return self.get_sessions_by_student_id(student_id)
    
    def get_recent_sessions(self, student_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent sessions
        
        Args:
            student_id: Optional student ID to filter by
            limit: Maximum number of sessions to return
            
        Returns:
            List of recent session dictionaries
        """
        try:
            query = Session.query
            
            if student_id:
                query = query.filter_by(student_id=int(student_id))
            
            sessions = query.order_by(Session.start_time.desc()).limit(limit).all()
            return [session.to_dict() for session in sessions] if hasattr(Session, 'to_dict') else []
        except Exception as e:
            print(f"Error getting recent sessions: {e}")
            return []
    
    def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new session
        
        Args:
            session_data: The session data
            
        Returns:
            The created session
        """
        try:
            session = Session(**session_data)
            db.session.add(session)
            db.session.commit()
            return session.to_dict() if hasattr(session, 'to_dict') else {}
        except Exception as e:
            db.session.rollback()
            print(f"Error creating session: {e}")
            return {}
    
    def update_session(self, session_id: str, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a session
        
        Args:
            session_id: The session ID
            session_data: The session data
            
        Returns:
            The updated session or None if not found
        """
        try:
            session = Session.query.get(int(session_id))
            if not session:
                return None
            
            for key, value in session_data.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            
            db.session.commit()
            return session.to_dict() if hasattr(session, 'to_dict') else {}
        except Exception as e:
            db.session.rollback()
            print(f"Error updating session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: The session ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            session = Session.query.get(int(session_id))
            if not session:
                return False
            
            db.session.delete(session)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics
        
        Returns:
            Dictionary of session statistics
        """
        try:
            total_sessions = Session.query.count()
            
            # Get sessions from today
            from datetime import date
            today = date.today()
            sessions_today = Session.query.filter(
                db.func.date(Session.start_time) == today
            ).count()
            
            # Calculate average duration
            avg_duration = db.session.query(db.func.avg(Session.duration_seconds)).scalar() or 0
            
            return {
                "total_sessions": total_sessions,
                "sessions_today": sessions_today,
                "average_duration": float(avg_duration),
                "sessions_by_day": {}  # Could be implemented with more complex query
            }
        except Exception as e:
            print(f"Error getting session statistics: {e}")
            return {
                "total_sessions": 0,
                "sessions_today": 0,
                "average_duration": 0,
                "sessions_by_day": {}
            }
    
    def get_session_details(self, student_id: str, session_file: str) -> tuple:
        """
        Get session details including transcript and analysis
        
        Args:
            student_id: The student ID
            session_file: The session filename
            
        Returns:
            Tuple of (session_data, transcript, analysis)
        """
        try:
            # For now, fallback to file-based approach
            session_path = f"data/students/{student_id}/sessions/{session_file}"
            
            session_data = None
            transcript = None
            analysis = None
            
            # Try to read session file
            if os.path.exists(session_path):
                with open(session_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
            
            # Try to read transcript
            transcript_file = session_data.get('transcript_file') if session_data else None
            if transcript_file:
                transcript_path = f"data/students/{student_id}/sessions/{transcript_file}"
                if os.path.exists(transcript_path):
                    with open(transcript_path, 'r', encoding='utf-8') as f:
                        transcript = f.read()
            
            # Try to read analysis
            analysis_file = session_file.replace('.json', '_analysis.json')
            analysis_path = f"data/students/{student_id}/sessions/{analysis_file}"
            if os.path.exists(analysis_path):
                with open(analysis_path, 'r', encoding='utf-8') as f:
                    analysis = json.load(f)
            
            return session_data, transcript, analysis
            
        except Exception as e:
            print(f"Error getting session details for {student_id}/{session_file}: {e}")
            return None, None, None
    
    def process_vapi_end_of_call(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process VAPI end-of-call webhook
        
        Args:
            webhook_data: The webhook data
            
        Returns:
            Processing result
        """
        # Extract data from webhook
        call_id = webhook_data.get('call', {}).get('id')
        phone_number = webhook_data.get('phoneNumber')
        
        if not call_id or not phone_number:
            return {"error": "Missing call_id or phone_number"}
        
        # This will be implemented with the VAPI client and repositories
        # For now, just return a placeholder
        return {
            "status": "processed",
            "call_id": call_id,
            "phone": phone_number,
            "timestamp": datetime.now().isoformat()
        }
    
    def enqueue_ai_analysis(self, session_id: str) -> bool:
        """
        Enqueue a session for AI analysis
        
        Args:
            session_id: The session ID
            
        Returns:
            True if enqueued, False if failed
        """
        try:
            # This will be implemented with Celery
            # For now, just return a placeholder
            print(f"AI analysis queued for session {session_id}")
            return True
        except Exception as e:
            print(f"Error enqueuing AI analysis for session {session_id}: {e}")
            return False