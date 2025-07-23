"""
Curriculum repository for database operations
"""

from typing import Dict, List, Optional, Any
from sqlalchemy import and_

from app import db
from app.models.curriculum import Curriculum, Subject, CurriculumDetail, SchoolDefaultSubject

def get_all() -> List[Dict[str, Any]]:
    """
    Get all curricula
    
    Returns:
        List of curriculum dictionaries
    """
    curricula = Curriculum.query.all()
    return [curriculum.to_dict() for curriculum in curricula]

def get_by_id(curriculum_id) -> Optional[Dict[str, Any]]:
    """
    Get a curriculum by ID
    
    Args:
        curriculum_id: The curriculum ID (int or str)
        
    Returns:
        Curriculum dictionary or None if not found
    """
    try:
        curriculum_id_int = int(curriculum_id)
        curriculum = Curriculum.query.get(curriculum_id_int)
        return curriculum.to_dict() if curriculum else None
    except (ValueError, TypeError):
        return None

def get_by_type(curriculum_type: str) -> List[Dict[str, Any]]:
    """
    Get curricula by type
    
    Args:
        curriculum_type: The curriculum type (e.g., 'IB', 'American', 'British')
        
    Returns:
        List of curriculum dictionaries
    """
    curricula = Curriculum.query.filter_by(curriculum_type=curriculum_type).all()
    return [curriculum.to_dict() for curriculum in curricula]

def get_templates() -> List[Dict[str, Any]]:
    """
    Get all template curricula
    
    Returns:
        List of template curriculum dictionaries
    """
    curricula = Curriculum.query.filter_by(is_template=True).all()
    return [curriculum.to_dict() for curriculum in curricula]

def get_by_school_id(school_id) -> List[Dict[str, Any]]:
    """
    Get curricula associated with a school
    
    Args:
        school_id: The school ID (int or str)
        
    Returns:
        List of curriculum dictionaries
    """
    try:
        school_id_int = int(school_id)
        curricula = Curriculum.query.filter_by(school_id=school_id_int).all()
        return [curriculum.to_dict() for curriculum in curricula]
    except (ValueError, TypeError):
        return []

def get_with_details(curriculum_id) -> Optional[Dict[str, Any]]:
    """
    Get a curriculum with all its details and subjects
    
    Args:
        curriculum_id: The curriculum ID (int or str)
        
    Returns:
        Curriculum dictionary with details or None if not found
    """
    try:
        curriculum_id_int = int(curriculum_id)
        curriculum = Curriculum.query.get(curriculum_id_int)
        if not curriculum:
            return None
        
        # Get curriculum data
        curriculum_data = curriculum.to_dict()
        
        # Get all curriculum details
        details = CurriculumDetail.query.filter_by(curriculum_id=curriculum_id_int).all()
        curriculum_data['details'] = [detail.to_dict() for detail in details]
        
        # Group details by grade and subject for easier access
        curriculum_data['details_by_grade'] = {}
        curriculum_data['subjects'] = []
        subject_ids = set()
        
        for detail in details:
            grade = detail.grade_level
            if grade not in curriculum_data['details_by_grade']:
                curriculum_data['details_by_grade'][grade] = []
            
            detail_dict = detail.to_dict()
            curriculum_data['details_by_grade'][grade].append(detail_dict)
            
            # Collect unique subjects
            if detail.subject_id not in subject_ids:
                subject_ids.add(detail.subject_id)
                subject = Subject.query.get(detail.subject_id)
                if subject:
                    curriculum_data['subjects'].append(subject.to_dict())
        
        return curriculum_data
    except (ValueError, TypeError):
        return None

def get_by_grade(grade_level: int) -> List[Dict[str, Any]]:
    """
    Get curricula that include a specific grade level
    
    Args:
        grade_level: The grade level
        
    Returns:
        List of curriculum dictionaries
    """
    curricula = Curriculum.query.filter(
        Curriculum.grade_levels.contains([grade_level])
    ).all()
    return [curriculum.to_dict() for curriculum in curricula]

def create(curriculum_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new curriculum
    
    Args:
        curriculum_data: The curriculum data
        
    Returns:
        The created curriculum
    """
    try:
        # Extract nested data
        details_data = curriculum_data.pop('details', [])
        
        # Create curriculum
        curriculum = Curriculum(**curriculum_data)
        db.session.add(curriculum)
        db.session.flush()  # Get the ID without committing
        
        # Create curriculum details if provided
        for detail_data in details_data:
            detail_data['curriculum_id'] = curriculum.id
            detail = CurriculumDetail(**detail_data)
            db.session.add(detail)
        
        # Commit all changes
        db.session.commit()
        
        # Return curriculum data
        result = curriculum.to_dict()
        if details_data:
            # Reload details with IDs
            created_details = CurriculumDetail.query.filter_by(curriculum_id=curriculum.id).all()
            result['details'] = [detail.to_dict() for detail in created_details]
        
        return result
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error creating curriculum: {e}")
        raise e

def update(curriculum_id, curriculum_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update a curriculum
    
    Args:
        curriculum_id: The curriculum ID (int or str)
        curriculum_data: The curriculum data
        
    Returns:
        The updated curriculum or None if not found
    """
    try:
        curriculum_id_int = int(curriculum_id)
        curriculum = Curriculum.query.get(curriculum_id_int)
        if not curriculum:
            return None
        
        # Extract nested data
        details_data = curriculum_data.pop('details', None)
        
        # Update curriculum fields
        for key, value in curriculum_data.items():
            if hasattr(curriculum, key):
                setattr(curriculum, key, value)
        
        # Update details if provided
        if details_data is not None:
            # Remove existing details
            CurriculumDetail.query.filter_by(curriculum_id=curriculum_id_int).delete()
            
            # Add new details
            for detail_data in details_data:
                detail_data['curriculum_id'] = curriculum_id_int
                detail = CurriculumDetail(**detail_data)
                db.session.add(detail)
        
        db.session.commit()
        
        # Return updated curriculum data
        result = curriculum.to_dict()
        if details_data is not None:
            # Reload details
            updated_details = CurriculumDetail.query.filter_by(curriculum_id=curriculum_id_int).all()
            result['details'] = [detail.to_dict() for detail in updated_details]
        
        return result
    except (ValueError, TypeError):
        return None
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error updating curriculum: {e}")
        raise e

def delete(curriculum_id) -> bool:
    """
    Delete a curriculum and all related data
    
    Args:
        curriculum_id: The curriculum ID (int or str)
        
    Returns:
        True if deleted, False if not found
    """
    try:
        curriculum_id_int = int(curriculum_id)
        curriculum = Curriculum.query.get(curriculum_id_int)
        if not curriculum:
            return False
        
        # Delete related curriculum details first (foreign key constraint)
        CurriculumDetail.query.filter_by(curriculum_id=curriculum_id_int).delete()
        
        # Delete curriculum
        db.session.delete(curriculum)
        db.session.commit()
        
        return True
    except (ValueError, TypeError):
        return False
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error deleting curriculum: {e}")
        raise e

def clone_curriculum(curriculum_id, new_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Clone a curriculum with new metadata
    
    Args:
        curriculum_id: The source curriculum ID (int or str)
        new_data: New data for the cloned curriculum (name, school_id, etc.)
        
    Returns:
        The cloned curriculum or None if source not found
    """
    try:
        curriculum_id_int = int(curriculum_id)
        source_curriculum = Curriculum.query.get(curriculum_id_int)
        if not source_curriculum:
            return None
        
        # Create new curriculum with source data and new overrides
        curriculum_data = source_curriculum.to_dict()
        curriculum_data.pop('id', None)  # Remove ID for new creation
        curriculum_data.pop('created_at', None)  # Will be set automatically
        curriculum_data.pop('updated_at', None)  # Will be set automatically
        curriculum_data.update(new_data)  # Apply new data
        curriculum_data['is_template'] = False  # Cloned curricula are not templates
        
        # Create new curriculum
        new_curriculum = Curriculum(**curriculum_data)
        db.session.add(new_curriculum)
        db.session.flush()  # Get the new ID
        
        # Clone all curriculum details
        source_details = CurriculumDetail.query.filter_by(curriculum_id=curriculum_id_int).all()
        for source_detail in source_details:
            detail_data = source_detail.to_dict()
            detail_data.pop('id', None)  # Remove ID for new creation
            detail_data['curriculum_id'] = new_curriculum.id  # Use new curriculum ID
            
            new_detail = CurriculumDetail(**detail_data)
            db.session.add(new_detail)
        
        db.session.commit()
        
        # Return cloned curriculum with details
        return get_with_details(new_curriculum.id)
    except (ValueError, TypeError):
        return None
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error cloning curriculum: {e}")
        raise e

def add_subject_to_curriculum(curriculum_id, subject_id, grade_levels: List[int], 
                            detail_data: Dict[str, Any] = None) -> bool:
    """
    Add a subject to a curriculum for specific grade levels
    
    Args:
        curriculum_id: The curriculum ID (int or str)
        subject_id: The subject ID (int or str)
        grade_levels: List of grade levels to add the subject to
        detail_data: Optional curriculum detail data (objectives, hours, etc.)
        
    Returns:
        True if added successfully, False if curriculum/subject not found
    """
    try:
        curriculum_id_int = int(curriculum_id)
        subject_id_int = int(subject_id)
        
        # Verify curriculum and subject exist
        curriculum = Curriculum.query.get(curriculum_id_int)
        subject = Subject.query.get(subject_id_int)
        if not curriculum or not subject:
            return False
        
        # Default detail data
        default_detail_data = {
            'learning_objectives': [f"Grade level {subject.name} objectives"],
            'assessment_criteria': ['Understanding', 'Application'],
            'recommended_hours_per_week': 3,
            'prerequisites': [],
            'resources': ['Textbook', 'Online Materials']
        }
        
        if detail_data:
            default_detail_data.update(detail_data)
        
        # Add curriculum details for each grade level
        for grade in grade_levels:
            # Check if detail already exists
            existing_detail = CurriculumDetail.query.filter_by(
                curriculum_id=curriculum_id_int,
                subject_id=subject_id_int,
                grade_level=grade
            ).first()
            
            if not existing_detail:
                detail = CurriculumDetail(
                    curriculum_id=curriculum_id_int,
                    subject_id=subject_id_int,
                    grade_level=grade,
                    **default_detail_data
                )
                db.session.add(detail)
        
        db.session.commit()
        return True
    except (ValueError, TypeError):
        return False
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error adding subject to curriculum: {e}")
        raise e

def remove_subject_from_curriculum(curriculum_id, subject_id, grade_levels: List[int] = None) -> bool:
    """
    Remove a subject from a curriculum
    
    Args:
        curriculum_id: The curriculum ID (int or str)
        subject_id: The subject ID (int or str)
        grade_levels: Optional list of specific grade levels to remove (if None, removes all)
        
    Returns:
        True if removed successfully, False if not found
    """
    try:
        curriculum_id_int = int(curriculum_id)
        subject_id_int = int(subject_id)
        
        # Build query
        query = CurriculumDetail.query.filter_by(
            curriculum_id=curriculum_id_int,
            subject_id=subject_id_int
        )
        
        # Filter by specific grades if provided
        if grade_levels:
            query = query.filter(CurriculumDetail.grade_level.in_(grade_levels))
        
        # Delete matching details
        deleted_count = query.delete()
        db.session.commit()
        
        return deleted_count > 0
    except (ValueError, TypeError):
        return False
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error removing subject from curriculum: {e}")
        raise e

def get_subjects_for_grade(curriculum_id, grade_level: int) -> List[Dict[str, Any]]:
    """
    Get all subjects for a specific grade in a curriculum
    
    Args:
        curriculum_id: The curriculum ID (int or str)
        grade_level: The grade level
        
    Returns:
        List of subjects with curriculum details
    """
    try:
        curriculum_id_int = int(curriculum_id)
        
        # Get curriculum details for the grade
        details = CurriculumDetail.query.filter_by(
            curriculum_id=curriculum_id_int,
            grade_level=grade_level
        ).all()
        
        subjects = []
        for detail in details:
            subject = Subject.query.get(detail.subject_id)
            if subject:
                subject_data = subject.to_dict()
                subject_data['curriculum_detail'] = detail.to_dict()
                subjects.append(subject_data)
        
        return subjects
    except (ValueError, TypeError):
        return []

def get_all_subjects() -> List[Dict[str, Any]]:
    """
    Get all available subjects
    
    Returns:
        List of subject dictionaries
    """
    subjects = Subject.query.all()
    return [subject.to_dict() for subject in subjects]

def create_subject(subject_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new subject
    
    Args:
        subject_data: The subject data
        
    Returns:
        The created subject
    """
    try:
        subject = Subject(**subject_data)
        db.session.add(subject)
        db.session.commit()
        
        return subject.to_dict()
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Error creating subject: {e}")
        raise e