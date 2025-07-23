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
        StudentSubject.last_assessment_date >= cutoff_date
    ).order_by(desc(StudentSubject.last_assessment_date)).all()
    
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
        if any(key in assessment_data for key in ['current_mastery_level', 'performance_score', 'completed_topics', 'learning_goals']):
            student_subject.last_assessment_date = datetime.utcnow()
        
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
            student_subject.current_mastery_level = progress_data['mastery_level']
        
        if 'performance_score' in progress_data:
            student_subject.performance_score = progress_data['performance_score']
        
        if 'completed_topics' in progress_data:
            student_subject.completed_topics = progress_data['completed_topics']
        
        if 'learning_goals' in progress_data:
            student_subject.learning_goals = progress_data['learning_goals']
        
        if 'strengths' in progress_data:
            student_subject.strengths = progress_data['strengths']
        
        if 'areas_for_improvement' in progress_data:
            student_subject.areas_for_improvement = progress_data['areas_for_improvement']
        
        if 'session_count' in progress_data:
            student_subject.session_count = progress_data['session_count']
        
        if 'total_time_minutes' in progress_data:
            student_subject.total_time_minutes = progress_data['total_time_minutes']
        
        # Always update last assessment date when progress is updated
        student_subject.last_assessment_date = datetime.utcnow()
        
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
            'current_mastery_level': 'beginner',
            'performance_score': 0.0,
            'completed_topics': [],
            'learning_goals': [],
            'strengths': [],
            'areas_for_improvement': [],
            'session_count': 0,
            'total_time_minutes': 0
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
        total_sessions = sum(ss.session_count for ss in active_subjects)
        total_time_minutes = sum(ss.total_time_minutes for ss in active_subjects)
        total_time_hours = total_time_minutes / 60.0
        
        # Calculate average performance (excluding 0 scores)
        performance_scores = [ss.performance_score for ss in active_subjects if ss.performance_score > 0]
        average_performance = sum(performance_scores) / len(performance_scores) if performance_scores else 0.0
        
        # Count mastery levels
        mastery_counts = {}
        for ss in active_subjects:
            level = ss.current_mastery_level
            mastery_counts[level] = mastery_counts.get(level, 0) + 1
        
        return {
            'student_id': student_id_int,
            'total_subjects': total_subjects,
            'average_performance': round(average_performance, 2),
            'total_sessions': total_sessions,
            'total_time_hours': round(total_time_hours, 2),
            'mastery_distribution': mastery_counts,
            'subjects': [ss.to_dict() for ss in active_subjects],
            'last_updated': max(ss.last_assessment_date for ss in active_subjects if ss.last_assessment_date) if active_subjects else None
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
        performance_scores = [e.performance_score for e in enrollments if e.performance_score > 0]
        average_performance = sum(performance_scores) / len(performance_scores) if performance_scores else 0.0
        
        # Mastery level distribution
        mastery_counts = {}
        for enrollment in enrollments:
            level = enrollment.current_mastery_level
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
            'total_sessions': sum(e.session_count for e in enrollments),
            'total_time_hours': round(sum(e.total_time_minutes for e in enrollments) / 60.0, 2)
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
        performance_scores = [e.performance_score for e in enrollments if e.performance_score > 0]
        average_performance = sum(performance_scores) / len(performance_scores) if performance_scores else 0.0
        
        return {
            'total_enrollments': len(enrollments),
            'unique_students': unique_students,
            'average_performance': round(average_performance, 2),
            'total_sessions': sum(e.session_count for e in enrollments),
            'total_time_hours': round(sum(e.total_time_minutes for e in enrollments) / 60.0, 2),
            'filters': {
                'grade_level': grade_level,
                'subject_id': subject_id
            }
        }
    except (ValueError, TypeError):
        return {'error': 'Invalid parameters'}