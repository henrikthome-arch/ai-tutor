"""
School repository for database operations
"""

from typing import Dict, List, Optional, Any

from app import db
from app.models.school import School
from app.models.curriculum import SchoolDefaultSubject

def get_all() -> List[Dict[str, Any]]:
    """
    Get all schools
    
    Returns:
        List of school dictionaries
    """
    schools = School.query.all()
    return [school.to_dict() for school in schools]

def get_by_id(school_id) -> Optional[Dict[str, Any]]:
    """
    Get a school by ID
    
    Args:
        school_id: The school ID (int or str)
        
    Returns:
        School dictionary or None if not found
    """
    # Handle both int and str school_id types
    try:
        school_id_int = int(school_id)
        school = School.query.get(school_id_int)
        return school.to_dict() if school else None
    except (ValueError, TypeError):
        return None

def get_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a school by name
    
    Args:
        name: The school name
        
    Returns:
        School dictionary or None if not found
    """
    school = School.query.filter_by(name=name).first()
    return school.to_dict() if school else None

def get_by_country(country: str) -> List[Dict[str, Any]]:
    """
    Get schools by country
    
    Args:
        country: The country name
        
    Returns:
        List of school dictionaries
    """
    schools = School.query.filter_by(country=country).all()
    return [school.to_dict() for school in schools]

def get_with_default_subjects(school_id) -> Dict[str, Any]:
    """
    Get a school with its default subjects
    
    Args:
        school_id: The school ID (int or str)
        
    Returns:
        School dictionary with default subjects or None if not found
    """
    try:
        school_id_int = int(school_id)
        school = School.query.get(school_id_int)
        if not school:
            return None
        
        # Get school data
        school_data = school.to_dict()
        
        # Get default subjects
        default_subjects = SchoolDefaultSubject.query.filter_by(school_id=school_id_int).all()
        school_data['default_subjects'] = [ds.to_dict() for ds in default_subjects]
        
        return school_data
    except (ValueError, TypeError):
        return None

def create(school_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new school
    
    Args:
        school_data: The school data
        
    Returns:
        The created school
    """
    try:
        # Extract any nested data that should be handled separately
        default_subjects = school_data.pop('default_subjects', [])
        
        # Create school
        school = School(**school_data)
        db.session.add(school)
        db.session.flush()  # Get the ID without committing
        
        # Create default subject assignments if provided
        for subject_data in default_subjects:
            subject_data['school_id'] = school.id
            default_subject = SchoolDefaultSubject(**subject_data)
            db.session.add(default_subject)
        
        # Commit all changes
        db.session.commit()
        
        # Return school data
        result = school.to_dict()
        if default_subjects:
            # Reload default subjects with IDs
            created_subjects = SchoolDefaultSubject.query.filter_by(school_id=school.id).all()
            result['default_subjects'] = [ds.to_dict() for ds in created_subjects]
        
        return result
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error creating school: {e}")
        raise e

def update(school_id, school_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update a school
    
    Args:
        school_id: The school ID (int or str)
        school_data: The school data
        
    Returns:
        The updated school or None if not found
    """
    # Handle both int and str school_id types
    try:
        school_id_int = int(school_id)
        school = School.query.get(school_id_int)
        if not school:
            return None
        
        # Extract any nested data that should be handled separately
        default_subjects = school_data.pop('default_subjects', None)
        
        # Update school fields
        for key, value in school_data.items():
            if hasattr(school, key):
                setattr(school, key, value)
        
        # Update default subjects if provided
        if default_subjects is not None:
            # Remove existing default subjects
            SchoolDefaultSubject.query.filter_by(school_id=school_id_int).delete()
            
            # Add new default subjects
            for subject_data in default_subjects:
                subject_data['school_id'] = school_id_int
                default_subject = SchoolDefaultSubject(**subject_data)
                db.session.add(default_subject)
        
        db.session.commit()
        
        # Return updated school data
        result = school.to_dict()
        if default_subjects is not None:
            # Reload default subjects
            updated_subjects = SchoolDefaultSubject.query.filter_by(school_id=school_id_int).all()
            result['default_subjects'] = [ds.to_dict() for ds in updated_subjects]
        
        return result
    except (ValueError, TypeError):
        return None
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error updating school: {e}")
        raise e

def delete(school_id) -> bool:
    """
    Delete a school and all related data
    
    Args:
        school_id: The school ID (int or str)
        
    Returns:
        True if deleted, False if not found
    """
    # Handle both int and str school_id types
    try:
        school_id_int = int(school_id)
        school = School.query.get(school_id_int)
        if not school:
            return False
        
        # Delete related default subjects first (foreign key constraint)
        SchoolDefaultSubject.query.filter_by(school_id=school_id_int).delete()
        
        # Note: Students associated with this school will have their school_id set to NULL
        # This is handled by the database foreign key constraint (nullable=True)
        
        # Delete school
        db.session.delete(school)
        db.session.commit()
        
        return True
    except (ValueError, TypeError):
        return False
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error deleting school: {e}")
        raise e

def add_default_subject(school_id, subject_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Add a default subject to a school
    
    Args:
        school_id: The school ID (int or str)
        subject_data: The subject assignment data
        
    Returns:
        The created default subject assignment or None if school not found
    """
    try:
        school_id_int = int(school_id)
        school = School.query.get(school_id_int)
        if not school:
            return None
        
        # Add school_id to subject data
        subject_data['school_id'] = school_id_int
        
        # Create default subject assignment
        default_subject = SchoolDefaultSubject(**subject_data)
        db.session.add(default_subject)
        db.session.commit()
        
        return default_subject.to_dict()
    except (ValueError, TypeError):
        return None
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error adding default subject: {e}")
        raise e

def remove_default_subject(school_id, subject_id) -> bool:
    """
    Remove a default subject from a school
    
    Args:
        school_id: The school ID (int or str)
        subject_id: The subject ID (int or str)
        
    Returns:
        True if removed, False if not found
    """
    try:
        school_id_int = int(school_id)
        subject_id_int = int(subject_id)
        
        default_subject = SchoolDefaultSubject.query.filter_by(
            school_id=school_id_int,
            subject_id=subject_id_int
        ).first()
        
        if not default_subject:
            return False
        
        db.session.delete(default_subject)
        db.session.commit()
        
        return True
    except (ValueError, TypeError):
        return False
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error removing default subject: {e}")
        raise e

def get_students_count(school_id) -> int:
    """
    Get the number of students in a school
    
    Args:
        school_id: The school ID (int or str)
        
    Returns:
        Number of students in the school
    """
    try:
        school_id_int = int(school_id)
        # Import here to avoid circular imports
        from app.models.student import Student
        count = Student.query.filter_by(school_id=school_id_int).count()
        return count
    except (ValueError, TypeError):
        return 0
    except Exception as e:
        print(f"Error getting student count: {e}")
        return 0