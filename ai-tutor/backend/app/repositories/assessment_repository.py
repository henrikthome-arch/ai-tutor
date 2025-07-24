"""
Assessment repository for database operations
Manages StudentSubject assessments and progress tracking
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, desc

from app import db
from app.models.assessment import StudentSubject, Assessment  # Keep Assessment for backward compatibility

def get_all() -> List[Dict[str, Any]]:
    """
    Get all student subject assessments
    
    Returns:
        List of student subject dictionaries
    """
    student_subjects = StudentSubject.query.all()
    return [ss.to_dict() for ss in student_subjects]

def get_by_student_id(student_id) -> List[Dict[str, Any]]:
    """
    Get all subject assessments for a student
    
    Args:
        student_id: The student ID (int or str)
        
    Returns:
        List of student subject dictionaries
    """
    try:
        student_id_int = int(student_id)
        student_subjects = StudentSubject.query.filter_by(student_id=student_id_int).all()
        return [ss.to_dict() for ss in student_subjects]
    except (ValueError, TypeError):
        return []

def get_by_subject_id(subject_id) -> List[Dict[str, Any]]:
    """
    Get all student assessments for a specific subject
    
    Args:
        subject_id: The subject ID (int or str)
        
    Returns:
        List of student subject dictionaries
    """
    try:
        subject_id_int = int(subject_id)
        student_subjects = StudentSubject.query.filter_by(subject_id=subject_id_int).all()
        return [ss.to_dict() for ss in student_subjects]
    except (ValueError, TypeError):
        return []

def get_by_student_and_subject(student_id, subject_id) -> Optional[Dict[str, Any]]:
    """
    Get a specific student's assessment for a subject
    
    Args:
        student_id: The student ID (int or str)
        subject_id: The subject ID (int or str)
        
    Returns:
        Student subject dictionary or None if not found
    """
    try:
        student_id_int = int(student_id)
        subject_id_int = int(subject_id)
        
        student_subject = StudentSubject.query.filter_by(
            student_id=student_id_int,
            subject_id=subject_id_int
        ).first()
        
        return student_subject.to_dict() if student_subject else None
    except (ValueError, TypeError):
        return None

def get_active_subjects(student_id) -> List[Dict[str, Any]]:
    """
    Get all active subjects for a student (is_in_use = True)
    
    Args:
        student_id: The student ID (int or str)
        
    Returns:
        List of active student subject dictionaries
    """
    try:
        student_id_int = int(student_id)
        student_subjects = StudentSubject.query.filter_by(
            student_id=student_id_int,
            is_in_use=True
        ).all()
        return [ss.to_dict() for ss in student_subjects]
    except (ValueError, TypeError):
        return []

def get_by_grade_level(grade_level: int) -> List[Dict[str, Any]]:
    """
    Get all student subjects for a specific grade level
    
    Args:
        grade_level: The grade level
        
    Returns:
        List of student subject dictionaries
    """
    student_subjects = StudentSubject.query.filter_by(grade_level=grade_level).all()
    return [ss.to_dict() for ss in student_subjects]

def get_recent_assessments(days: int = 7) -> List[Dict[str, Any]]:
    """
    Get assessments updated in the last N days
    
    Args:
        days: Number of days to look back
        
    Returns:
        List of recently updated student subject dictionaries
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    student_subjects = StudentSubject.query.filter(
        StudentSubject.updated_at >= cutoff_date
    ).order_by(desc(StudentSubject.updated_at)).all()
    
    return [ss.to_dict() for ss in student_subjects]

def create(assessment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new student subject assessment
    
    Args:
        assessment_data: The assessment data
        
    Returns:
        The created student subject assessment
    """
    try:
        # Set enrollment date if not provided
        if 'enrollment_date' not in assessment_data:
            assessment_data['enrollment_date'] = datetime.utcnow()
        
        # Set is_in_use to True by default
        if 'is_in_use' not in assessment_data:
            assessment_data['is_in_use'] = True
        
        # Create student subject
        student_subject = StudentSubject(**assessment_data)
        db.session.add(student_subject)
        db.session.commit()
        
        return student_subject.to_dict()
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error creating student subject assessment: {e}")
        raise e

def update(student_id, subject_id, assessment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update a student subject assessment
    
    Args:
        student_id: The student ID (int or str)
        subject_id: The subject ID (int or str)
        assessment_data: The assessment data to update
        
    Returns:
        The updated student subject assessment or None if not found
    """
    try:
        student_id_int = int(student_id)
        subject_id_int = int(subject_id)
        
        student_subject = StudentSubject.query.filter_by(
            student_id=student_id_int,
            subject_id=subject_id_int
        ).first()
        
        if not student_subject:
            return None
        
        # Update fields
        for key, value in assessment_data.items():
            if hasattr(student_subject, key):
                setattr(student_subject, key, value)
        
        # Update last assessment date if assessment data is being updated
        if any(key in assessment_data for key in ['mastery_level', 'progress_percentage', 'ai_assessment']):
            # last_assessment_date doesn't exist, updated_at is handled automatically
            pass
        
        db.session.commit()
        
        return student_subject.to_dict()
    except (ValueError, TypeError):
        return None
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error updating student subject assessment: {e}")
        raise e

def update_progress(student_id, subject_id, progress_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update specific progress fields for a student's subject
    
    Args:
        student_id: The student ID (int or str)
        subject_id: The subject ID (int or str)
        progress_data: Progress-specific data (mastery_level, score, topics, etc.)
        
    Returns:
        The updated student subject assessment or None if not found
    """
    try:
        student_id_int = int(student_id)
        subject_id_int = int(subject_id)
        
        student_subject = StudentSubject.query.filter_by(
            student_id=student_id_int,
            subject_id=subject_id_int
        ).first()
        
        if not student_subject:
            return None
        
        # Update progress-specific fields
        if 'mastery_level' in progress_data:
            student_subject.mastery_level = progress_data['mastery_level']
        
        if 'performance_score' in progress_data:
            # Map performance_score to progress_percentage (0-100 scale)
            student_subject.progress_percentage = progress_data['performance_score'] / 100.0 if progress_data['performance_score'] <= 100 else progress_data['performance_score']
        
        if 'completed_topics' in progress_data:
            # completed_topics doesn't exist in model, store in ai_assessment field as JSON
            student_subject.ai_assessment = f"Completed topics: {progress_data['completed_topics']}"
        
        if 'learning_goals' in progress_data:
            # learning_goals doesn't exist in model, append to teacher_notes
            if student_subject.teacher_notes:
                student_subject.teacher_notes += f"\nLearning goals: {progress_data['learning_goals']}"
            else:
                student_subject.teacher_notes = f"Learning goals: {progress_data['learning_goals']}"
        
        if 'strengths' in progress_data:
            # strengths doesn't exist in model, store in comments_tutor
            if student_subject.comments_tutor:
                student_subject.comments_tutor += f"\nStrengths: {progress_data['strengths']}"
            else:
                student_subject.comments_tutor = f"Strengths: {progress_data['strengths']}"
        
        if 'areas_for_improvement' in progress_data:
            # Map areas_for_improvement to weaknesses field
            student_subject.weaknesses = progress_data['areas_for_improvement']
        
        # Note: session_count and total_time_minutes fields don't exist in StudentSubject model
        # These would need to be added to the model if session tracking is required
        # if 'session_count' in progress_data:
        #     student_subject.session_count = progress_data['session_count']
        # if 'total_time_minutes' in progress_data:
        #     student_subject.total_time_minutes = progress_data['total_time_minutes']
        
        # updated_at is handled automatically by the model
        # student_subject.last_assessment_date doesn't exist
        
        db.session.commit()
        
        return student_subject.to_dict()
    except (ValueError, TypeError):
        return None
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error updating progress: {e}")
        raise e

def delete(student_id, subject_id) -> bool:
    """
    Delete a student subject assessment
    
    Args:
        student_id: The student ID (int or str)
        subject_id: The subject ID (int or str)
        
    Returns:
        True if deleted, False if not found
    """
    try:
        student_id_int = int(student_id)
        subject_id_int = int(subject_id)
        
        student_subject = StudentSubject.query.filter_by(
            student_id=student_id_int,
            subject_id=subject_id_int
        ).first()
        
        if not student_subject:
            return False
        
        db.session.delete(student_subject)
        db.session.commit()
        
        return True
    except (ValueError, TypeError):
        return False
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error deleting student subject assessment: {e}")
        raise e

def delete_all_for_student(student_id) -> int:
    """
    Delete all subject assessments for a student (for GDPR compliance)
    
    Args:
        student_id: The student ID (int or str)
        
    Returns:
        Number of assessments deleted
    """
    try:
        student_id_int = int(student_id)
        
        # Count before deletion
        count = StudentSubject.query.filter_by(student_id=student_id_int).count()
        
        # Delete all student subjects
        StudentSubject.query.filter_by(student_id=student_id_int).delete()
        
        db.session.commit()
        
        return count
    except (ValueError, TypeError):
        return 0
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error deleting all assessments for student: {e}")
        raise e

def enroll_student_in_subject(student_id, subject_id, grade_level: int, 
                             initial_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Enroll a student in a subject
    
    Args:
        student_id: The student ID (int or str)
        subject_id: The subject ID (int or str)
        grade_level: The grade level for this subject
        initial_data: Optional initial assessment data
        
    Returns:
        The created student subject assessment
    """
    try:
        student_id_int = int(student_id)
        subject_id_int = int(subject_id)
        
        # Check if already enrolled
        existing = StudentSubject.query.filter_by(
            student_id=student_id_int,
            subject_id=subject_id_int
        ).first()
        
        if existing:
            # Reactivate if inactive
            if not existing.is_in_use:
                existing.is_in_use = True
                existing.enrollment_date = datetime.utcnow()
                db.session.commit()
            return existing.to_dict()
        
        # Create enrollment data
        enrollment_data = {
            'student_id': student_id_int,
            'subject_id': subject_id_int,
            'grade_level': grade_level,
            'enrollment_date': datetime.utcnow(),
            'is_in_use': True,
            'mastery_level': 'beginner',
            'progress_percentage': 0.0
            # Note: completed_topics, learning_goals, strengths, areas_for_improvement don't exist in current model
            # Note: session_count and total_time_minutes not available in current model
        }
        
        # Apply any initial data
        if initial_data:
            enrollment_data.update(initial_data)
        
        return create(enrollment_data)
    except (ValueError, TypeError):
        raise ValueError("Invalid student_id or subject_id")

def unenroll_student_from_subject(student_id, subject_id) -> bool:
    """
    Unenroll a student from a subject (set is_in_use to False)
    
    Args:
        student_id: The student ID (int or str)
        subject_id: The subject ID (int or str)
        
    Returns:
        True if unenrolled, False if not found
    """
    try:
        student_id_int = int(student_id)
        subject_id_int = int(subject_id)
        
        student_subject = StudentSubject.query.filter_by(
            student_id=student_id_int,
            subject_id=subject_id_int
        ).first()
        
        if not student_subject:
            return False
        
        student_subject.is_in_use = False
        db.session.commit()
        
        return True
    except (ValueError, TypeError):
        return False
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error unenrolling student from subject: {e}")
        raise e

def get_student_progress_summary(student_id) -> Dict[str, Any]:
    """
    Get a comprehensive progress summary for a student
    
    Args:
        student_id: The student ID (int or str)
        
    Returns:
        Progress summary with statistics
    """
    try:
        student_id_int = int(student_id)
        
        # Get all active subjects
        active_subjects = StudentSubject.query.filter_by(
            student_id=student_id_int,
            is_in_use=True
        ).all()
        
        if not active_subjects:
            return {
                'student_id': student_id_int,
                'total_subjects': 0,
                'average_performance': 0.0,
                'total_sessions': 0,
                'total_time_hours': 0.0,
                'subjects': []
            }
        
        # Calculate summary statistics
        total_subjects = len(active_subjects)
        # Note: session_count and total_time_minutes not available in current model
        total_sessions = 0  # Default to 0 since session tracking not implemented
        total_time_minutes = 0  # Default to 0 since time tracking not implemented
        total_time_hours = total_time_minutes / 60.0
        
        # Calculate average performance using progress_percentage (excluding 0 scores)
        performance_scores = [ss.progress_percentage * 100 for ss in active_subjects if ss.progress_percentage and ss.progress_percentage > 0]
        average_performance = sum(performance_scores) / len(performance_scores) if performance_scores else 0.0
        
        # Count mastery levels
        mastery_counts = {}
        for ss in active_subjects:
            level = ss.mastery_level if ss.mastery_level else 'unknown'
            mastery_counts[level] = mastery_counts.get(level, 0) + 1
        
        return {
            'student_id': student_id_int,
            'total_subjects': total_subjects,
            'average_performance': round(average_performance, 2),
            'total_sessions': total_sessions,
            'total_time_hours': round(total_time_hours, 2),
            'mastery_distribution': mastery_counts,
            'subjects': [ss.to_dict() for ss in active_subjects],
            'last_updated': max(ss.updated_at for ss in active_subjects if ss.updated_at).isoformat() if active_subjects and any(ss.updated_at for ss in active_subjects) else None
        }
    except (ValueError, TypeError):
        return {'error': 'Invalid student_id'}

def get_subject_performance_stats(subject_id) -> Dict[str, Any]:
    """
    Get performance statistics for a subject across all students
    
    Args:
        subject_id: The subject ID (int or str)
        
    Returns:
        Subject performance statistics
    """
    try:
        subject_id_int = int(subject_id)
        
        # Get all active enrollments for this subject
        enrollments = StudentSubject.query.filter_by(
            subject_id=subject_id_int,
            is_in_use=True
        ).all()
        
        if not enrollments:
            return {
                'subject_id': subject_id_int,
                'total_students': 0,
                'average_performance': 0.0,
                'mastery_distribution': {},
                'grade_distribution': {}
            }
        
        # Calculate statistics
        total_students = len(enrollments)
        performance_scores = [e.progress_percentage * 100 for e in enrollments if e.progress_percentage and e.progress_percentage > 0]
        average_performance = sum(performance_scores) / len(performance_scores) if performance_scores else 0.0
        
        # Mastery level distribution
        mastery_counts = {}
        for enrollment in enrollments:
            level = enrollment.mastery_level if enrollment.mastery_level else 'unknown'
            mastery_counts[level] = mastery_counts.get(level, 0) + 1
        
        # Grade level distribution
        grade_counts = {}
        for enrollment in enrollments:
            grade = enrollment.grade_level
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        return {
            'subject_id': subject_id_int,
            'total_students': total_students,
            'average_performance': round(average_performance, 2),
            'mastery_distribution': mastery_counts,
            'grade_distribution': grade_counts,
            'total_sessions': 0,  # Session tracking not implemented in current model
            'total_time_hours': 0.0  # Time tracking not implemented in current model
        }
    except (ValueError, TypeError):
        return {'error': 'Invalid subject_id'}

def get_class_analytics(grade_level: int = None, subject_id = None) -> Dict[str, Any]:
    """
    Get analytics for a class (by grade level and/or subject)
    
    Args:
        grade_level: Optional grade level filter
        subject_id: Optional subject ID filter
        
    Returns:
        Class analytics data
    """
    try:
        # Build query
        query = StudentSubject.query.filter_by(is_in_use=True)
        
        if grade_level is not None:
            query = query.filter_by(grade_level=grade_level)
        
        if subject_id is not None:
            subject_id_int = int(subject_id)
            query = query.filter_by(subject_id=subject_id_int)
        
        enrollments = query.all()
        
        if not enrollments:
            return {
                'total_enrollments': 0,
                'unique_students': 0,
                'average_performance': 0.0,
                'filters': {
                    'grade_level': grade_level,
                    'subject_id': subject_id
                }
            }
        
        # Calculate analytics
        unique_students = len(set(e.student_id for e in enrollments))
        performance_scores = [e.progress_percentage * 100 for e in enrollments if e.progress_percentage and e.progress_percentage > 0]
        average_performance = sum(performance_scores) / len(performance_scores) if performance_scores else 0.0
        
        return {
            'total_enrollments': len(enrollments),
            'unique_students': unique_students,
            'average_performance': round(average_performance, 2),
            'total_sessions': 0,  # Session tracking not implemented in current model
            'total_time_hours': 0.0,  # Time tracking not implemented in current model
            'filters': {
                'grade_level': grade_level,
                'subject_id': subject_id
            }
        }
    except (ValueError, TypeError):
        return {'error': 'Invalid parameters'}