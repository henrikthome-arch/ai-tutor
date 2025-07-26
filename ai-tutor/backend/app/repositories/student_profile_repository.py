"""
Student Profile repository for database operations
Manages versioned student profiles with AI-generated narratives and structured traits
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from app import db
from app.models.student_profile import StudentProfile

def get_current(student_id: int) -> Optional[Dict[str, Any]]:
    """
    Get the current (latest) profile for a student using the optimized view
    
    Args:
        student_id: The student ID
        
    Returns:
        Student profile dictionary or None if not found
    """
    try:
        # Use the optimized student_profiles_current view for best performance
        from sqlalchemy import text
        result = db.session.execute(
            text("SELECT * FROM student_profiles_current WHERE student_id = :student_id"),
            {'student_id': student_id}
        ).fetchone()
        
        if result:
            return {
                'id': result[0],
                'student_id': result[1], 
                'narrative': result[2],
                'traits': result[3],
                'created_at': result[4]
            }
        return None
        
    except Exception as e:
        print(f"Error getting current profile for student {student_id}: {e}")
        # Fallback to direct query if view fails
        try:
            profile = StudentProfile.query.filter_by(student_id=student_id)\
                                        .order_by(StudentProfile.created_at.desc())\
                                        .first()
            return profile.to_dict() if profile else None
        except Exception as fallback_error:
            print(f"Fallback query also failed: {fallback_error}")
            return None

def get_all_versions(student_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get all profile versions for a student, ordered by creation date (newest first)
    
    Args:
        student_id: The student ID
        limit: Optional limit on number of versions to return
        
    Returns:
        List of student profile dictionaries
    """
    try:
        query = StudentProfile.query.filter_by(student_id=student_id)\
                                  .order_by(StudentProfile.created_at.desc())
        
        if limit:
            query = query.limit(limit)
            
        profiles = query.all()
        return [profile.to_dict() for profile in profiles]
        
    except Exception as e:
        print(f"Error getting profile versions for student {student_id}: {e}")
        return []

def add_version(student_id: int, narrative: str, traits: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new profile version for a student
    
    Args:
        student_id: The student ID
        narrative: AI-generated narrative description
        traits: Structured traits dictionary
        
    Returns:
        The created profile dictionary
    """
    try:
        # Create new profile version
        profile = StudentProfile(
            student_id=student_id,
            narrative=narrative,
            traits=traits
        )
        
        db.session.add(profile)
        db.session.commit()
        
        print(f"✅ Created new profile version for student {student_id}")
        return profile.to_dict()
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating profile version for student {student_id}: {e}")
        raise e

def upsert_trait(student_id: int, trait_key: str, trait_value: Any) -> Dict[str, Any]:
    """
    Update a specific trait in the latest profile, creating a new version if needed
    
    Args:
        student_id: The student ID
        trait_key: The trait key to update
        trait_value: The new trait value
        
    Returns:
        The updated/created profile dictionary
    """
    try:
        # Get the current profile
        current_profile = get_current(student_id)
        
        if current_profile:
            # Update existing traits
            current_traits = current_profile.get('traits', {})
            current_traits[trait_key] = trait_value
            
            # Create new version with updated traits
            new_profile = add_version(
                student_id=student_id,
                narrative=current_profile.get('narrative', ''),
                traits=current_traits
            )
            
            print(f"✅ Updated trait '{trait_key}' for student {student_id}")
            return new_profile
        else:
            # No existing profile, create first version
            new_profile = add_version(
                student_id=student_id,
                narrative='',
                traits={trait_key: trait_value}
            )
            
            print(f"✅ Created first profile with trait '{trait_key}' for student {student_id}")
            return new_profile
            
    except Exception as e:
        print(f"Error upserting trait for student {student_id}: {e}")
        raise e

def update_from_ai_delta(student_id: int, profile_delta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update student profile based on AI-generated delta changes
    
    Args:
        student_id: The student ID
        profile_delta: Dictionary containing profile updates from AI analysis
        
    Returns:
        Updated profile dictionary or None if no changes needed
    """
    try:
        # Extract delta components
        narrative_changes = profile_delta.get('narrative_changes')
        trait_updates = profile_delta.get('trait_updates', {})
        should_create_new_version = profile_delta.get('should_create_new_profile_version', False)
        
        # Skip if no changes
        if not narrative_changes and not trait_updates:
            print(f"ℹ️ No profile changes for student {student_id}")
            return None
            
        # Get current profile
        current_profile = get_current(student_id)
        
        # Prepare new profile data
        new_narrative = narrative_changes if narrative_changes else (current_profile.get('narrative', '') if current_profile else '')
        
        # Merge trait updates with existing traits
        new_traits = {}
        if current_profile:
            new_traits.update(current_profile.get('traits', {}))
        new_traits.update(trait_updates)
        
        # Create new version if significant changes or explicitly requested
        if should_create_new_version or not current_profile:
            new_profile = add_version(
                student_id=student_id,
                narrative=new_narrative,
                traits=new_traits
            )
            
            print(f"✅ Created new profile version from AI delta for student {student_id}")
            return new_profile
        else:
            # Minor updates - just update traits individually
            updated_profile = current_profile
            for trait_key, trait_value in trait_updates.items():
                updated_profile = upsert_trait(student_id, trait_key, trait_value)
            
            print(f"✅ Updated profile traits from AI delta for student {student_id}")
            return updated_profile
            
    except Exception as e:
        print(f"Error updating profile from AI delta for student {student_id}: {e}")
        raise e

def delete_all_for_student(student_id: int) -> int:
    """
    Delete all profile versions for a student (GDPR compliance)
    
    Args:
        student_id: The student ID
        
    Returns:
        Number of profile versions deleted
    """
    try:
        deleted_count = StudentProfile.query.filter_by(student_id=student_id).delete()
        db.session.commit()
        
        print(f"✅ Deleted {deleted_count} profile versions for student {student_id}")
        return deleted_count
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting profiles for student {student_id}: {e}")
        raise e

def get_profile_statistics() -> Dict[str, Any]:
    """
    Get system-wide profile statistics
    
    Returns:
        Dictionary with profile statistics
    """
    try:
        from sqlalchemy import func, distinct
        
        # Get profile statistics
        total_profiles = db.session.query(func.count(StudentProfile.id)).scalar()
        unique_students = db.session.query(func.count(distinct(StudentProfile.student_id))).scalar()
        
        # Students with profiles
        students_with_profiles = db.session.query(distinct(StudentProfile.student_id)).count()
        
        # Average versions per student
        avg_versions = total_profiles / students_with_profiles if students_with_profiles > 0 else 0
        
        return {
            'total_profiles': total_profiles,
            'unique_students': unique_students,
            'students_with_profiles': students_with_profiles,
            'average_versions_per_student': round(avg_versions, 2)
        }
        
    except Exception as e:
        print(f"Error getting profile statistics: {e}")
        return {
            'total_profiles': 0,
            'unique_students': 0,
            'students_with_profiles': 0,
            'average_versions_per_student': 0.0
        }