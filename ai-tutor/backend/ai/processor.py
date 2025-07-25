"""
AI processor for analyzing session transcripts
"""

import logging
from typing import Dict, Any, Optional, Tuple

from app import db
from app.models.session import Session
from app.models.student import Student
from app.models.profile import Profile
from ai.providers import provider_manager

logger = logging.getLogger(__name__)

class AIProcessor:
    """AI processor for analyzing session transcripts"""
    
    def __init__(self):
        self.provider_manager = provider_manager
    
    async def process_session(self, session_id: int) -> Dict[str, Any]:
        """
        Process a session
        
        Args:
            session_id: The session ID
            
        Returns:
            Processing result
        """
        # Get session
        session = Session.query.get(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return {"error": "Session not found"}
        
        # Get student
        student = Student.query.get(session.student_id)
        if not student:
            logger.error(f"Student {session.student_id} not found")
            return {"error": "Student not found"}
        
        # Get student profile
        profile = Profile.query.filter_by(student_id=student.id).first()
        
        # Prepare context
        context = {
            "student_name": student.full_name,
            "student_age": student.age,
            "student_grade": student.grade,
            "interests": profile.interests if profile else [],
            "learning_preferences": profile.learning_preferences if profile else [],
            "task": "session_analysis"
        }
        
        # Process transcript
        try:
            analysis = await self.provider_manager.analyze_session(session.transcript, context)
            
            # Update session summary
            session.summary = analysis.raw_response
            db.session.commit()
            
            # Update student profile using transcript analyzer
            from transcript_analyzer import TranscriptAnalyzer
            analyzer = TranscriptAnalyzer()
            
            # Extract profile information from analysis
            if hasattr(analysis, 'raw_response'):
                try:
                    import json
                    profile_info = json.loads(analysis.raw_response)
                    analyzer.update_student_profile(student.id, profile_info)
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(f"Could not parse analysis for profile update: {e}")
            
            # Update assessment
            self._update_assessment(student.id, student.grade, "General", analysis)
            
            return {
                "success": True,
                "session_id": session_id,
                "student_id": student.id,
                "analysis": analysis.to_dict()
            }
        except Exception as e:
            logger.error(f"Error processing session {session_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "student_id": student.id
            }
    
    def _update_student_profile(self, student_id: int, analysis: Any) -> None:
        """
        Update student profile based on analysis
        
        Args:
            student_id: The student ID
            analysis: The analysis result
        """
        # This is a placeholder - in a real implementation, we would extract
        # interests, learning preferences, etc. from the analysis
        pass
    
    def _update_assessment(self, student_id: int, grade: int, subject: str, analysis: Any) -> None:
        """
        Update assessment using StudentSubject model (replaces legacy Assessment)
        
        Args:
            student_id: The student ID
            grade: The grade level
            subject: The subject
            analysis: The analysis result
        """
        # Use StudentSubject model instead of legacy Assessment
        from app.models.assessment import StudentSubject
        
        # Get or create student subject
        student_subject = StudentSubject.query.filter_by(
            student_id=student_id,
            subject_name=subject
        ).first()
        
        if not student_subject:
            student_subject = StudentSubject(
                student_id=student_id,
                subject_name=subject,
                grade_level=grade
            )
            db.session.add(student_subject)
        
        # Update assessment fields based on analysis
        # This is a placeholder - in a real implementation, we would extract
        # strengths, weaknesses, mastery level, etc. from the analysis
        
        db.session.commit()

# Global processor instance
ai_processor = AIProcessor()