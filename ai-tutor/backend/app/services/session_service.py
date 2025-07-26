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
        Get all sessions with formatted data for admin template
        
        Returns:
            List of session dictionaries formatted for template
        """
        try:
            # Query sessions with student information
            sessions_query = db.session.query(Session, Student).join(
                Student, Session.student_id == Student.id
            ).order_by(Session.start_datetime.desc()).all()
            
            formatted_sessions = []
            for session, student in sessions_query:
                # Convert duration from seconds to minutes
                duration_minutes = None
                if session.duration:
                    duration_minutes = round(session.duration / 60, 1)
                
                # Check if transcript and summary exist
                has_transcript = bool(session.transcript and session.transcript.strip())
                has_summary = bool(session.summary and session.summary.strip())
                
                formatted_session = {
                    'id': session.id,
                    'student_id': session.student_id,
                    'student_name': f"{student.first_name} {student.last_name}".strip(),
                    'start_datetime': session.start_datetime.isoformat() if session.start_datetime else None,
                    'duration': session.duration,  # Keep original for calculations
                    'duration_minutes': duration_minutes,  # For display
                    'session_type': session.session_type or 'phone',
                    'transcript': session.transcript,
                    'summary': session.summary,
                    'has_transcript': has_transcript,
                    'has_summary': has_summary,
                    'call_id': f"session_{session.id}"  # Fallback call ID
                }
                formatted_sessions.append(formatted_session)
            
            print(f"📋 Loaded {len(formatted_sessions)} sessions for admin display")
            return formatted_sessions
            
        except Exception as e:
            print(f"❌ Error getting all sessions: {e}")
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
            
            sessions = query.order_by(Session.start_datetime.desc()).limit(limit).all()
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
                db.func.date(Session.start_datetime) == today
            ).count()
            
            # Calculate average duration (field is 'duration', not 'duration_seconds')
            avg_duration = db.session.query(db.func.avg(Session.duration)).scalar() or 0
            
            # Get count of unique students with sessions
            total_students = db.session.query(Session.student_id).distinct().count()
            
            # Count VAPI sessions (phone sessions)
            vapi_sessions = Session.query.filter_by(session_type='phone').count()
            
            # Count sessions with analysis (sessions that have summary)
            with_analysis = Session.query.filter(Session.summary.isnot(None)).filter(Session.summary != '').count()
            
            return {
                "total_sessions": total_sessions,
                "sessions_today": sessions_today,
                "average_duration": float(avg_duration),
                "sessions_by_day": {},  # Could be implemented with more complex query
                "total_students": total_students,
                "vapi_sessions": vapi_sessions,
                "with_analysis": with_analysis
            }
        except Exception as e:
            print(f"Error getting session statistics: {e}")
            return {
                "total_sessions": 0,
                "sessions_today": 0,
                "average_duration": 0,
                "sessions_by_day": {},
                "total_students": 0,
                "vapi_sessions": 0,
                "with_analysis": 0
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
    
    def get_last_n_summaries(self, student_id: int, n: int = 5) -> List[Dict[str, Any]]:
        """
        Get the last N session summaries for a student for AI context
        
        Args:
            student_id: The student ID
            n: Number of summaries to retrieve (default: 5)
            
        Returns:
            List of session summaries ordered by date (newest first)
        """
        try:
            # Get recent sessions with summaries
            sessions = Session.query.filter_by(student_id=student_id)\
                                  .filter(Session.summary.isnot(None))\
                                  .filter(Session.summary != '')\
                                  .order_by(Session.start_datetime.desc())\
                                  .limit(n).all()
            
            summaries = []
            for session in sessions:
                summary_data = {
                    'id': session.id,
                    'date': session.start_datetime.isoformat() if session.start_datetime else None,
                    'summary': session.summary,
                    'duration_minutes': session.duration_seconds // 60 if session.duration_seconds else 0,
                    'session_type': session.session_type or 'phone',
                    'created_at': session.created_at.isoformat() if session.created_at else None
                }
                summaries.append(summary_data)
            
            print(f"✅ Retrieved {len(summaries)} session summaries for student {student_id}")
            return summaries
            
        except Exception as e:
            print(f"Error getting last {n} summaries for student {student_id}: {e}")
            return []
    
    def update_session_summary(self, session_id: int, summary: str) -> bool:
        """
        Update the summary for a session
        
        Args:
            session_id: The session ID
            summary: The session summary text
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            session = Session.query.get(session_id)
            if not session:
                print(f"Session {session_id} not found")
                return False
            
            session.summary = summary
            db.session.commit()
            
            print(f"✅ Updated summary for session {session_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error updating summary for session {session_id}: {e}")
            return False
    
    def ensure_session_summary(self, session_id: int) -> bool:
        """
        Ensure a session has a summary, creating one if missing
        Used by post-session processing to guarantee summary availability
        
        Args:
            session_id: The session ID
            
        Returns:
            True if summary exists or was created, False if failed
        """
        try:
            session = Session.query.get(session_id)
            if not session:
                print(f"Session {session_id} not found")
                return False
            
            # Check if summary already exists
            if session.summary and session.summary.strip():
                print(f"ℹ️ Session {session_id} already has summary")
                return True
            
            # Generate summary from transcript if available
            if session.transcript and session.transcript.strip():
                # Create a basic summary from transcript
                transcript_lines = session.transcript.split('\n')
                # Take first few lines as a basic summary
                summary_lines = transcript_lines[:3]
                basic_summary = ' '.join(summary_lines).strip()
                
                if basic_summary:
                    session.summary = f"Session summary (auto-generated): {basic_summary}"
                    db.session.commit()
                    print(f"✅ Created basic summary for session {session_id}")
                    return True
            
            # Fallback: create minimal summary
            session.summary = f"Session conducted on {session.start_datetime.strftime('%Y-%m-%d %H:%M') if session.start_datetime else 'unknown date'}"
            db.session.commit()
            print(f"✅ Created minimal summary for session {session_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error ensuring summary for session {session_id}: {e}")
            return False
    
    def get_sessions_needing_ai_update(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get sessions that need AI-driven profile/memory updates
        Used for batch processing of sessions
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session dictionaries that need AI processing
        """
        try:
            # Get recent sessions with transcripts but potentially needing AI updates
            sessions = Session.query.filter(Session.transcript.isnot(None))\
                                  .filter(Session.transcript != '')\
                                  .order_by(Session.start_datetime.desc())\
                                  .limit(limit).all()
            
            session_data = []
            for session in sessions:
                if hasattr(session, 'to_dict'):
                    session_data.append(session.to_dict())
                else:
                    session_data.append({
                        'id': session.id,
                        'student_id': session.student_id,
                        'start_datetime': session.start_datetime.isoformat() if session.start_datetime else None,
                        'transcript': session.transcript,
                        'summary': session.summary,
                        'session_type': session.session_type
                    })
            
            print(f"✅ Found {len(session_data)} sessions needing AI updates")
            return session_data
            
        except Exception as e:
            print(f"Error getting sessions needing AI update: {e}")
            return []