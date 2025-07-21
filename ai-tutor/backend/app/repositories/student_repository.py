"""
Student repository for database operations
"""

from typing import Dict, List, Optional, Any

from app import db
from app.models.student import Student
from app.models.profile import Profile

def get_all() -> List[Dict[str, Any]]:
    """
    Get all students
    
    Returns:
        List of student dictionaries
    """
    students = Student.query.all()
    return [student.to_dict() for student in students]

def get_by_id(student_id) -> Optional[Dict[str, Any]]:
    """
    Get a student by ID
    
    Args:
        student_id: The student ID (int or str)
        
    Returns:
        Student dictionary or None if not found
    """
    # Handle both int and str student_id types
    try:
        student_id_int = int(student_id)
        student = Student.query.get(student_id_int)
        return student.to_dict() if student else None
    except (ValueError, TypeError):
        return None

def get_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """
    Get a student by phone number
    
    Args:
        phone: The phone number
        
    Returns:
        Student dictionary or None if not found
    """
    student = Student.query.filter_by(phone_number=phone).first()
    return student.to_dict() if student else None

def create(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new student
    
    Args:
        student_data: The student data
        
    Returns:
        The created student
    """
    try:
        # Extract profile data
        profile_data = {
            'interests': student_data.pop('interests', []),
            'learning_preferences': student_data.pop('learning_preferences', [])
        }
        
        # Create student
        student = Student(**student_data)
        db.session.add(student)
        db.session.flush()  # Get the ID without committing
        
        # Create profile
        profile = Profile(student_id=student.id, **profile_data)
        db.session.add(profile)
        
        # Commit both
        db.session.commit()
        
        # Return combined data
        result = student.to_dict()
        result.update({
            'interests': profile.interests,
            'learning_preferences': profile.learning_preferences
        })
        
        return result
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error creating student: {e}")
        raise e

def update(student_id, student_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update a student
    
    Args:
        student_id: The student ID (int or str)
        student_data: The student data
        
    Returns:
        The updated student or None if not found
    """
    # Handle both int and str student_id types
    try:
        student_id_int = int(student_id)
        student = Student.query.get(student_id_int)
        if not student:
            return None
        
        # Extract profile data
        profile_data = {}
        if 'interests' in student_data:
            profile_data['interests'] = student_data.pop('interests')
        if 'learning_preferences' in student_data:
            profile_data['learning_preferences'] = student_data.pop('learning_preferences')
        
        # Update student
        for key, value in student_data.items():
            if hasattr(student, key):
                setattr(student, key, value)
        
        # Update profile if needed
        if profile_data:
            profile = Profile.query.filter_by(student_id=student_id_int).first()
            if profile:
                for key, value in profile_data.items():
                    setattr(profile, key, value)
            else:
                profile = Profile(student_id=student_id_int, **profile_data)
                db.session.add(profile)
        
        db.session.commit()
        
        # Return combined data
        result = student.to_dict()
        profile = Profile.query.filter_by(student_id=student_id_int).first()
        if profile:
            result.update({
                'interests': profile.interests,
                'learning_preferences': profile.learning_preferences
            })
        
        return result
    except (ValueError, TypeError):
        return None
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error updating student: {e}")
        raise e

def delete(student_id) -> bool:
    """
    Delete a student
    
    Args:
        student_id: The student ID (int or str)
        
    Returns:
        True if deleted, False if not found
    """
    # Handle both int and str student_id types
    try:
        student_id_int = int(student_id)
        student = Student.query.get(student_id_int)
        if not student:
            return False
        
        # Delete profile first (foreign key constraint)
        profile = Profile.query.filter_by(student_id=student_id_int).first()
        if profile:
            db.session.delete(profile)
        
        # Delete student
        db.session.delete(student)
        db.session.commit()
        
        return True
    except (ValueError, TypeError):
        return False
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error deleting student: {e}")
        raise e