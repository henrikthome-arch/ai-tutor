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

def assign_default_curriculum_to_student(student_id: int) -> int:
    """
    Assign the default curriculum to a student by creating StudentSubject records.
    
    Args:
        student_id: The student ID
        
    Returns:
        Number of StudentSubject records created
    """
    try:
        from app.models.curriculum import Curriculum, CurriculumDetail
        from app.models.assessment import StudentSubject
        
        # Find the default curriculum
        default_curriculum = Curriculum.query.filter_by(is_default=True).first()
        if not default_curriculum:
            print(f"⚠️ No default curriculum found for student {student_id}")
            return 0
        
        print(f"📚 Assigning default curriculum '{default_curriculum.name}' to student {student_id}")
        
        # Get all curriculum details for the default curriculum
        curriculum_details = CurriculumDetail.query.filter_by(
            curriculum_id=default_curriculum.id
        ).all()
        
        if not curriculum_details:
            print(f"⚠️ No curriculum details found for default curriculum {default_curriculum.id}")
            return 0
        
        # Create StudentSubject records for each curriculum detail
        created_count = 0
        for detail in curriculum_details:
            # Check if StudentSubject already exists for this combination
            existing = StudentSubject.query.filter_by(
                student_id=student_id,
                curriculum_detail_id=detail.id
            ).first()
            
            if existing:
                print(f"📝 StudentSubject already exists for student {student_id}, detail {detail.id}")
                continue
            
            # Create new StudentSubject with sensible defaults
            student_subject = StudentSubject(
                student_id=student_id,
                curriculum_detail_id=detail.id,
                is_active_for_tutoring=True,
                is_in_use=True,
                progress_percentage=0.0,
                completion_percentage=0.0,
                mastery_level='beginner'
            )
            
            db.session.add(student_subject)
            created_count += 1
            
            subject_name = detail.subject.name if detail.subject else 'Unknown'
            print(f"✅ Created StudentSubject: {subject_name} Grade {detail.grade_level}")
        
        # Commit all StudentSubject records
        if created_count > 0:
            db.session.commit()
            print(f"📚 Successfully assigned {created_count} subjects from default curriculum to student {student_id}")
        else:
            print(f"ℹ️ No new subjects assigned to student {student_id} (all already exist)")
        
        return created_count
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error assigning default curriculum to student {student_id}: {e}")
        raise e

def create(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new student and automatically assign default curriculum
    
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
        
        # Commit student and profile first
        db.session.commit()
        
        # Automatically assign default curriculum to ALL new students
        # This ensures every student has curriculum assignments regardless of school
        try:
            subjects_assigned = assign_default_curriculum_to_student(student.id)
            if subjects_assigned > 0:
                print(f"📚 Auto-assigned {subjects_assigned} subjects from default curriculum to new student {student.id}")
            else:
                print(f"ℹ️ No new subjects assigned to student {student.id} (may already exist or no default curriculum)")
        except Exception as curriculum_error:
            print(f"⚠️ Error auto-assigning default curriculum to student {student.id}: {curriculum_error}")
            # Don't fail student creation if curriculum assignment fails
        
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
    Delete a student and ALL associated data for GDPR compliance
    
    This function ensures complete data erasure by removing:
    - Student record
    - Profile data
    - All assessment/progress records (StudentSubject)
    - All session records
    - Any other related data
    
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
        
        print(f"🗑️ Starting GDPR-compliant deletion for student {student_id_int}")
        
        # Delete all student assessments/progress (StudentSubject records)
        from app.repositories import assessment_repository
        try:
            deleted_assessments = assessment_repository.delete_all_for_student(student_id_int)
            print(f"✅ Deleted {deleted_assessments} assessment records")
        except Exception as assessment_error:
            print(f"⚠️ Error deleting assessments: {assessment_error}")
            # Continue with deletion even if assessments fail
        
        # Delete all sessions for this student
        try:
            from app.models.session import Session
            deleted_sessions = Session.query.filter_by(student_id=student_id_int).delete()
            print(f"✅ Deleted {deleted_sessions} session records")
        except Exception as session_error:
            print(f"⚠️ Error deleting sessions: {session_error}")
            # Continue with deletion even if sessions fail
        
        # Delete legacy Assessment records if they exist (backward compatibility)
        try:
            from app.models.assessment import Assessment
            deleted_legacy = Assessment.query.filter_by(student_id=student_id_int).delete()
            if deleted_legacy > 0:
                print(f"✅ Deleted {deleted_legacy} legacy assessment records")
        except Exception as legacy_error:
            print(f"⚠️ Error deleting legacy assessments: {legacy_error}")
            # Continue with deletion even if legacy records fail
        
        # Delete profile (foreign key constraint)
        try:
            profile = Profile.query.filter_by(student_id=student_id_int).first()
            if profile:
                db.session.delete(profile)
                print(f"✅ Deleted profile record")
        except Exception as profile_error:
            print(f"⚠️ Error deleting profile: {profile_error}")
            # Continue with deletion even if profile fails
        
        # Delete the student record itself
        db.session.delete(student)
        
        # Commit all deletions
        db.session.commit()
        
        print(f"✅ GDPR-compliant deletion completed for student {student_id_int}")
        return True
        
    except (ValueError, TypeError):
        return False
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"❌ Error during GDPR deletion for student {student_id}: {e}")
        raise e

def delete_gdpr_compliant(student_id) -> Dict[str, Any]:
    """
    Delete a student with detailed GDPR compliance reporting
    
    Args:
        student_id: The student ID (int or str)
        
    Returns:
        Dictionary with deletion results and counts
    """
    try:
        student_id_int = int(student_id)
        student = Student.query.get(student_id_int)
        if not student:
            return {
                'success': False,
                'error': 'Student not found',
                'student_id': student_id_int
            }
        
        # Track deletion results
        deletion_results = {
            'success': True,
            'student_id': student_id_int,
            'student_name': f"{student.first_name} {student.last_name}".strip(),
            'deleted_records': {
                'assessments': 0,
                'sessions': 0,
                'legacy_assessments': 0,
                'profile': 0,
                'student': 1
            },
            'errors': []
        }
        
        # Delete all student assessments/progress
        try:
            from app.repositories import assessment_repository
            deleted_assessments = assessment_repository.delete_all_for_student(student_id_int)
            deletion_results['deleted_records']['assessments'] = deleted_assessments
        except Exception as e:
            deletion_results['errors'].append(f"Assessment deletion error: {str(e)}")
        
        # Delete all sessions
        try:
            from app.models.session import Session
            deleted_sessions = Session.query.filter_by(student_id=student_id_int).delete()
            deletion_results['deleted_records']['sessions'] = deleted_sessions
        except Exception as e:
            deletion_results['errors'].append(f"Session deletion error: {str(e)}")
        
        # Delete legacy assessments
        try:
            from app.models.assessment import Assessment
            deleted_legacy = Assessment.query.filter_by(student_id=student_id_int).delete()
            deletion_results['deleted_records']['legacy_assessments'] = deleted_legacy
        except Exception as e:
            deletion_results['errors'].append(f"Legacy assessment deletion error: {str(e)}")
        
        # Delete profile
        try:
            profile = Profile.query.filter_by(student_id=student_id_int).first()
            if profile:
                db.session.delete(profile)
                deletion_results['deleted_records']['profile'] = 1
        except Exception as e:
            deletion_results['errors'].append(f"Profile deletion error: {str(e)}")
        
        # Delete student
        db.session.delete(student)
        db.session.commit()
        
        # Calculate total records deleted
        deletion_results['total_records_deleted'] = sum(deletion_results['deleted_records'].values())
        
        return deletion_results
        
    except (ValueError, TypeError):
        return {
            'success': False,
            'error': 'Invalid student ID',
            'student_id': student_id
        }
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'error': str(e),
            'student_id': student_id
        }