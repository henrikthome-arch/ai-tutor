"""
Student service for business logic
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from types import SimpleNamespace

from app.repositories import student_repository, student_profile_repository, student_memory_repository
from app.models.student import Student
from app.models.school import School
from app import db


class StudentService:
    """Service class for student operations"""
    
    def __init__(self):
        pass
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics for dashboard"""
        try:
            # Student statistics
            total_students = Student.query.count()
            
            # Get recent activity count (last 7 days)
            from datetime import timedelta
            week_ago = datetime.now() - timedelta(days=7)
            recent_students = Student.query.filter(Student.created_at >= week_ago).count()
            
            # Get students with phone numbers
            students_with_phone = Student.query.filter(Student.phone_number.isnot(None)).count()
            
            # Session statistics
            total_sessions = 0
            sessions_today = 0
            try:
                from app.models.session import Session
                total_sessions = Session.query.count()
                
                # Sessions today
                today = datetime.now().date()
                today_start = datetime.combine(today, datetime.min.time())
                today_end = datetime.combine(today, datetime.max.time())
                sessions_today = Session.query.filter(
                    Session.start_datetime >= today_start,
                    Session.start_datetime <= today_end
                ).count()
            except Exception as session_e:
                print(f"Error getting session stats: {session_e}")
            
            # Curriculum statistics
            total_curriculums = 0
            curriculum_details_count = 0
            default_curriculum = None
            default_curriculum_subjects = 0
            students_with_default_curriculum = 0
            
            try:
                from app.models.curriculum import Curriculum, CurriculumDetail
                total_curriculums = Curriculum.query.count()
                curriculum_details_count = CurriculumDetail.query.count()
                
                # Get default curriculum
                default_curriculum_obj = Curriculum.query.filter_by(is_default=True).first()
                if default_curriculum_obj:
                    default_curriculum = {
                        'id': default_curriculum_obj.id,
                        'name': default_curriculum_obj.name,
                        'curriculum_type': default_curriculum_obj.curriculum_type,
                        'grade_levels': default_curriculum_obj.grade_levels
                    }
                    
                    # Count subjects for default curriculum
                    default_curriculum_subjects = CurriculumDetail.query.filter_by(
                        curriculum_id=default_curriculum_obj.id
                    ).count()
                    
                    # Count students using default curriculum (approximation - legacy Profile removed)
                    students_with_default_curriculum = 0  # Legacy Profile table no longer used
                    
            except Exception as curriculum_e:
                print(f"Error getting curriculum stats: {curriculum_e}")
            
            # System information
            server_status = "Running"
            
            # Environment detection
            environment = os.environ.get('ENVIRONMENT', 'production')
            if os.environ.get('RENDER'):
                environment = 'production (Render)'
            elif os.environ.get('DEVELOPMENT'):
                environment = 'development'
            
            # Database information
            database_info = {
                'connection_status': 'connected',
                'type': 'PostgreSQL',
                'error': None
            }
            try:
                # Test database connection
                db.session.execute(db.text('SELECT 1'))
                database_info['connection_status'] = 'connected'
            except Exception as db_e:
                database_info['connection_status'] = 'error'
                database_info['error'] = str(db_e)
            
            # Data directory size calculation
            data_size = "N/A"
            try:
                if os.path.exists('data'):
                    total_size = 0
                    for dirpath, dirnames, filenames in os.walk('data'):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            if os.path.exists(filepath):
                                total_size += os.path.getsize(filepath)
                    
                    # Convert to human readable format
                    if total_size < 1024:
                        data_size = f"{total_size} B"
                    elif total_size < 1024 * 1024:
                        data_size = f"{total_size / 1024:.1f} KB"
                    elif total_size < 1024 * 1024 * 1024:
                        data_size = f"{total_size / (1024 * 1024):.1f} MB"
                    else:
                        data_size = f"{total_size / (1024 * 1024 * 1024):.1f} GB"
            except Exception as size_e:
                print(f"Error calculating data directory size: {size_e}")
                data_size = "Error calculating"
            
            # Current timestamp
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            
            # Last backup (placeholder - would be implemented with actual backup system)
            last_backup = "Not implemented"
            
            return {
                # Student stats
                'total_students': total_students,
                'recent_students': recent_students,
                'students_with_phone': students_with_phone,
                'phone_mappings': students_with_phone,
                
                # Session stats
                'total_sessions': total_sessions,
                'sessions_today': sessions_today,
                
                # Server status
                'server_status': server_status,
                
                # Curriculum stats
                'total_curriculums': total_curriculums,
                'curriculum_details_count': curriculum_details_count,
                'default_curriculum': default_curriculum,
                'default_curriculum_subjects': default_curriculum_subjects,
                'students_with_default_curriculum': students_with_default_curriculum,
                
                # System information for /admin/system page
                'environment': environment,
                'database': database_info,
                'data_size': data_size,
                'timestamp': current_timestamp,
                'last_backup': last_backup
            }
            
        except Exception as e:
            print(f"Error getting system stats: {e}")
            # Return safe fallback values
            return {
                'total_students': 0,
                'recent_students': 0,
                'students_with_phone': 0,
                'phone_mappings': 0,
                'total_sessions': 0,
                'sessions_today': 0,
                'server_status': 'Unknown',
                'total_curriculums': 0,
                'curriculum_details_count': 0,
                'default_curriculum': None,
                'default_curriculum_subjects': 0,
                'students_with_default_curriculum': 0,
                'environment': 'Unknown',
                'database': {
                    'connection_status': 'error',
                    'type': 'Unknown',
                    'error': 'System error'
                },
                'data_size': 'Unknown',
                'timestamp': 'Unknown',
                'last_backup': 'Unknown'
            }
    
    def get_all_students(self) -> List[Any]:
        """Get all students with profile information"""
        try:
            students = Student.query.all()
            result = []
            
            for student in students:
                student_dict = student.to_dict()
                
                # Use Student table fields directly
                student_dict.update({
                    'interests': student.interests or [],
                    'learning_preferences': student.learning_preferences or [],
                    'grade': student.get_grade() or 'Unknown',
                    'curriculum': 'Unknown'  # Not stored in Student table
                })
                
                # Format for template compatibility - ensure all required fields
                student_dict.update({
                    'name': student.full_name,
                    'phone': student.phone_number,
                    'progress': 75,  # Default progress percentage
                    'last_session': None,  # Will be calculated from sessions
                    'session_count': 0  # Will be calculated from sessions
                })
                
                # Calculate session stats safely
                try:
                    session_count = student.sessions.count() if hasattr(student.sessions, 'count') else 0
                    student_dict['session_count'] = session_count
                    
                    # Get last session date safely
                    student_dict['last_session'] = None
                    if session_count > 0:
                        # Import Session model locally to avoid circular imports
                        from app.models.session import Session
                        last_session = Session.query.filter_by(student_id=student.id).order_by(Session.start_datetime.desc()).first()
                        if last_session and last_session.start_datetime:
                            student_dict['last_session'] = last_session.start_datetime.strftime('%Y-%m-%d')
                except Exception as e:
                    print(f"Error calculating session stats for student {student.id}: {e}")
                    student_dict['session_count'] = 0
                    student_dict['last_session'] = None
                
                # Convert dictionary to object with attribute access for template compatibility
                student_obj = SimpleNamespace(**student_dict)
                result.append(student_obj)
            
            return result
        except Exception as e:
            print(f"Error getting all students: {e}")
            return []
    
    def get_phone_mappings(self) -> Dict[str, str]:
        """Get phone number to student ID mappings"""
        try:
            students = Student.query.filter(Student.phone_number.isnot(None)).all()
            return {student.phone_number: str(student.id) for student in students}
        except Exception as e:
            print(f"Error getting phone mappings: {e}")
            return {}
    
    def get_student_data(self, student_id) -> Optional[Dict[str, Any]]:
        """Get comprehensive student data including profile, progress, sessions"""
        try:
            student = Student.query.get(int(student_id))
            if not student:
                return None
            
            # Base student data
            student_data = student.to_dict()
            
            # Profile data from Student table
            profile_data = {
                'name': student.full_name,
                'age': student.age,
                'grade': student.get_grade() or 'Unknown',
                'curriculum': 'Unknown',  # Not stored in Student table
                'interests': student.interests or [],
                'learning_preferences': student.learning_preferences or [],
                'learning_style': 'Unknown',  # Not stored in Student table
                'motivational_triggers': student.motivational_triggers or []
            }
            
            # Sessions data
            sessions_data = []
            for session in student.sessions:
                session_dict = session.to_dict() if hasattr(session, 'to_dict') else {
                    'id': session.id,
                    'start_datetime': session.start_datetime.isoformat() if session.start_datetime else None,
                    'duration_seconds': session.duration_seconds,
                    'session_type': session.session_type,
                    'transcript_file': session.transcript_file
                }
                sessions_data.append(session_dict)
            
            return {
                'profile': profile_data,
                'progress': {},  # Placeholder for progress data
                'assessment': {},  # Placeholder for assessment data
                'sessions': sessions_data
            }
            
        except Exception as e:
            print(f"Error getting student data for {student_id}: {e}")
            return None
    
    def get_student_phone(self, student_id) -> Optional[str]:
        """Get student's phone number"""
        try:
            student = Student.query.get(int(student_id))
            return student.phone_number if student else None
        except Exception as e:
            print(f"Error getting student phone for {student_id}: {e}")
            return None
    
    def get_student_by_phone(self, phone: str) -> Optional[str]:
        """Get student ID by phone number"""
        try:
            student = Student.query.filter_by(phone_number=phone).first()
            return str(student.id) if student else None
        except Exception as e:
            print(f"Error getting student by phone {phone}: {e}")
            return None
    
    def create_student_from_call(self, student_id: str, phone: str, call_id: str) -> str:
        """Create a new student from call data"""
        try:
            # Create student with placeholder name that AI analysis can replace
            # Use "Student" prefix so TranscriptAnalyzer.update_student_profile() can update it
            student_data = {
                'first_name': f'Student {phone[-4:]}',  # AI will replace this with real name
                'last_name': '',  # Keep empty - AI will populate if available
                'phone_number': phone,
                'student_type': 'International'
            }
            
            student = Student(**student_data)
            db.session.add(student)
            db.session.flush()  # Get the database-generated integer ID
            
            # Assign default curriculum subjects (use grade 1 as default for unknown students)
            self._assign_default_curriculum_subjects(student.id, grade_level=1)
            
            # Commit the student creation (no separate Profile needed - data is in Student table)
            db.session.commit()
            
            # Return the actual database-generated integer ID as string
            return str(student.id)
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating student from call: {e}")
            # Don't return a string ID as fallback since it causes database errors
            raise e
    
    def remove_phone_mapping(self, phone_number: str) -> bool:
        """Remove phone mapping (set phone to None)"""
        try:
            student = Student.query.filter_by(phone_number=phone_number).first()
            if student:
                student.phone_number = None
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error removing phone mapping for {phone_number}: {e}")
            return False
    
    def add_phone_mapping(self, phone_number: str, student_id: str) -> bool:
        """Add phone mapping to student"""
        try:
            student = Student.query.get(int(student_id))
            if student:
                student.phone_number = phone_number
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error adding phone mapping {phone_number} -> {student_id}: {e}")
            return False
    
    def student_exists(self, student_id) -> bool:
        """Check if student exists"""
        try:
            student = Student.query.get(int(student_id))
            return student is not None
        except Exception as e:
            print(f"Error checking if student {student_id} exists: {e}")
            return False
    
    def create_student(self, name: str, age: int, grade: int, interests: List[str], phone: str = None) -> str:
        """Create a new student"""
        try:
            # Split name into first/last
            name_parts = name.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Create student
            student_data = {
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': phone,
                'student_type': 'International',
                'interests': interests
            }
            
            # Calculate date of birth from age
            if age and age > 0:
                birth_year = datetime.now().year - age
                student_data['date_of_birth'] = date(birth_year, 1, 1)
            
            student = Student(**student_data)
            db.session.add(student)
            db.session.flush()
            
            # Set grade level directly on student
            student.grade_level = grade
            
            # Assign default curriculum subjects
            self._assign_default_curriculum_subjects(student.id, grade)
            
            db.session.commit()
            
            return str(student.id)
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating student: {e}")
            raise e
    
    def update_student(self, student_id: str, name: str, age: int, grade: int, interests: List[str], phone: str = None) -> bool:
        """Update an existing student"""
        try:
            student = Student.query.get(int(student_id))
            if not student:
                return False
            
            # Split name into first/last
            name_parts = name.strip().split(' ', 1)
            student.first_name = name_parts[0]
            student.last_name = name_parts[1] if len(name_parts) > 1 else ''
            student.phone_number = phone
            
            # Update date of birth from age
            if age and age > 0:
                birth_year = datetime.now().year - age
                student.date_of_birth = date(birth_year, 1, 1)
            
            # Update grade level directly on student (Profile is legacy)
            student.grade_level = grade
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error updating student {student_id}: {e}")
            return False
    
    def delete_student(self, student_id: str) -> bool:
        """Delete a student"""
        try:
            student = Student.query.get(int(student_id))
            if not student:
                return False
            
            # Cascade delete will handle profile, sessions, etc.
            db.session.delete(student)
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting student {student_id}: {e}")
            return False
    
    def _assign_default_curriculum_subjects(self, student_id: int, grade_level: int) -> bool:
        """Assign default curriculum subjects to a newly created student"""
        try:
            from app.models.curriculum import Curriculum, CurriculumDetail
            from app.models.assessment import StudentSubject
            
            # Find the default curriculum
            default_curriculum = Curriculum.query.filter_by(is_default=True).first()
            if not default_curriculum:
                print("⚠️ No default curriculum found - students will not have subjects assigned")
                return False
            
            print(f"📚 Assigning default curriculum '{default_curriculum.name}' to student {student_id} (grade {grade_level})")
            
            # Get all curriculum details for the student's grade level and above
            # This follows the architecture requirement: "for their grade and above"
            curriculum_details = CurriculumDetail.query.filter(
                CurriculumDetail.curriculum_id == default_curriculum.id,
                CurriculumDetail.grade_level >= grade_level
            ).all()
            
            print(f"📖 Found {len(curriculum_details)} curriculum details to assign")
            
            student_subjects_created = 0
            for detail in curriculum_details:
                try:
                    # Check if StudentSubject already exists
                    existing = StudentSubject.query.filter_by(
                        student_id=student_id,
                        curriculum_detail_id=detail.id
                    ).first()
                    
                    if existing:
                        print(f"⚠️ StudentSubject already exists for student {student_id}, detail {detail.id}")
                        continue
                    
                    # Create StudentSubject record
                    student_subject = StudentSubject(
                        student_id=student_id,
                        curriculum_detail_id=detail.id,
                        is_in_use=True,  # Mark as in use (part of current curriculum)
                        is_active_for_tutoring=False,  # Initially inactive for tutoring
                        progress_percentage=0.0,  # Start at 0% progress
                        completion_percentage=0.0,  # Start at 0% completion
                        mastery_level='Not Started'  # Initial mastery level
                    )
                    
                    db.session.add(student_subject)
                    student_subjects_created += 1
                    
                    subject_name = detail.subject.name if detail.subject else 'Unknown'
                    print(f"✅ Created StudentSubject: {subject_name} (Grade {detail.grade_level})")
                    
                except Exception as detail_error:
                    print(f"❌ Error creating StudentSubject for detail {detail.id}: {detail_error}")
                    continue
            
            print(f"✅ Successfully created {student_subjects_created} StudentSubject records for student {student_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error assigning default curriculum subjects to student {student_id}: {e}")
            return False
    
    def get_student_name(self, student_id: str) -> str:
        """Get student's full name"""
        try:
            student = Student.query.get(int(student_id))
            return student.full_name if student else 'Unknown'
        except Exception as e:
            print(f"Error getting student name for {student_id}: {e}")
            return 'Unknown'
    
    def get_all_schools(self) -> List[Dict[str, Any]]:
        """Get all schools (fallback to file-based for now)"""
        try:
            schools = School.query.all()
            return [school.to_dict() for school in schools] if hasattr(School, 'to_dict') else []
        except Exception as e:
            print(f"Error getting schools from database: {e}")
            # Fallback to file-based
            try:
                schools_file = 'data/schools.json'
                if os.path.exists(schools_file):
                    with open(schools_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                return []
            except Exception as file_e:
                print(f"Error reading schools file: {file_e}")
                return []
    
    def save_all_schools(self, schools: List[Dict[str, Any]]) -> bool:
        """Save all schools (fallback to file-based for now)"""
        try:
            # For now, save to file until school management is fully migrated
            schools_file = 'data/schools.json'
            os.makedirs(os.path.dirname(schools_file), exist_ok=True)
            with open(schools_file, 'w', encoding='utf-8') as f:
                json.dump(schools, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving schools: {e}")
            return False
    
    def get_full_context(self, student_id: int) -> Dict[str, Any]:
        """
        Get complete student context including profile, memories, mastery map, and basic data
        Used by AI tutor for personalized interactions
        
        Args:
            student_id: The student ID
            
        Returns:
            Dictionary with complete student context
        """
        try:
            # Get basic student data
            student = Student.query.get(student_id)
            if not student:
                return {
                    'error': 'Student not found',
                    'student_id': student_id
                }
            
            # Get current profile
            current_profile = student_profile_repository.get_current(student_id)
            
            # Get memories grouped by scope
            memories_by_scope = student_memory_repository.get_by_scope_grouped(student_id)
            
            # Get mastery map data (incomplete goals and KCs for AI awareness)
            mastery_context = self._get_mastery_context(student_id)
            
            # Get session summaries (will be implemented in SessionService)
            session_summaries = []
            try:
                from app.models.session import Session
                recent_sessions = Session.query.filter_by(student_id=student_id)\
                                             .order_by(Session.start_datetime.desc())\
                                             .limit(5).all()
                session_summaries = [
                    {
                        'id': session.id,
                        'date': session.start_datetime.isoformat() if session.start_datetime else None,
                        'summary': session.summary,
                        'duration_minutes': session.duration_seconds // 60 if session.duration_seconds else 0
                    }
                    for session in recent_sessions if session.summary
                ]
            except Exception as session_error:
                print(f"Error getting session summaries for student {student_id}: {session_error}")
            
            # Build comprehensive context
            context = {
                'student_id': student_id,
                'basic_info': {
                    'name': student.full_name,
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'age': student.age,
                    'grade': student.get_grade(),
                    'phone': student.phone_number,
                    'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
                    'student_type': student.student_type,
                    'created_at': student.created_at.isoformat() if student.created_at else None
                },
                'legacy_arrays': {
                    'interests': student.interests or [],
                    'learning_preferences': student.learning_preferences or [],
                    'motivational_triggers': student.motivational_triggers or []
                },
                'current_profile': current_profile,
                'memories': memories_by_scope,
                'mastery_context': mastery_context,
                'recent_sessions': session_summaries,
                'context_timestamp': datetime.utcnow().isoformat()
            }
            
            print(f"✅ Retrieved full context for student {student_id} (including mastery data)")
            return context
            
        except Exception as e:
            print(f"Error getting full context for student {student_id}: {e}")
            return {
                'error': str(e),
                'student_id': student_id,
                'context_timestamp': datetime.utcnow().isoformat()
            }
    
    def update_profile_from_ai_delta(self, student_id: int, profile_delta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update student profile based on AI-generated delta changes
        
        Args:
            student_id: The student ID
            profile_delta: Dictionary containing profile updates from AI analysis
            
        Returns:
            Updated profile dictionary or None if no changes
        """
        try:
            return student_profile_repository.update_from_ai_delta(student_id, profile_delta)
        except Exception as e:
            print(f"Error updating profile from AI delta for student {student_id}: {e}")
            raise e
    
    def update_memories_from_ai_delta(self, student_id: int, memory_delta: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update student memories based on AI-generated delta changes
        
        Args:
            student_id: The student ID
            memory_delta: Dictionary with scope as key and memory updates as value
            
        Returns:
            List of updated memory dictionaries
        """
        try:
            return student_memory_repository.update_from_ai_delta(student_id, memory_delta)
        except Exception as e:
            print(f"Error updating memories from AI delta for student {student_id}: {e}")
            raise e
    
    def get_memory_by_scope(self, student_id: int, scope: str) -> List[Dict[str, Any]]:
        """
        Get student memories filtered by scope
        
        Args:
            student_id: The student ID
            scope: The memory scope to filter by
            
        Returns:
            List of memory dictionaries for the specified scope
        """
        try:
            from app.models.student_memory import MemoryScope
            memory_scope = MemoryScope(scope)
            return student_memory_repository.get_many(student_id, scope=memory_scope)
        except ValueError:
            print(f"Invalid memory scope: {scope}")
            return []
        except Exception as e:
            print(f"Error getting memories by scope for student {student_id}: {e}")
            return []
    
    def set_memory(self, student_id: int, memory_key: str, memory_value: str, scope: str, expires_at: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Set a single memory for a student
        
        Args:
            student_id: The student ID
            memory_key: The memory key
            memory_value: The memory value
            scope: The memory scope
            expires_at: Optional expiration datetime
            
        Returns:
            The created/updated memory dictionary
        """
        try:
            from app.models.student_memory import MemoryScope
            memory_scope = MemoryScope(scope)
            return student_memory_repository.set(student_id, memory_key, memory_value, memory_scope, expires_at)
        except ValueError:
            print(f"Invalid memory scope: {scope}")
            raise ValueError(f"Invalid memory scope: {scope}")
        except Exception as e:
            print(f"Error setting memory for student {student_id}: {e}")
            raise e
    
    def delete_memory(self, student_id: int, memory_key: str) -> bool:
        """
        Delete a specific memory for a student
        
        Args:
            student_id: The student ID
            memory_key: The memory key to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            return student_memory_repository.delete_key(student_id, memory_key)
        except Exception as e:
            print(f"Error deleting memory for student {student_id}: {e}")
            raise e
    
    def get_profile_history(self, student_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get profile version history for a student
        
        Args:
            student_id: The student ID
            limit: Optional limit on number of versions
            
        Returns:
            List of profile versions ordered by creation date (newest first)
        """
        try:
            return student_profile_repository.get_all_versions(student_id, limit)
        except Exception as e:
            print(f"Error getting profile history for student {student_id}: {e}")
            return []
    
    def _get_mastery_context(self, student_id: int) -> Dict[str, Any]:
        """
        Get mastery context for AI awareness (incomplete goals and KCs)
        
        Args:
            student_id: The student ID
            
        Returns:
            Dictionary with mastery context data
        """
        try:
            from app.repositories.student_goal_progress_repository import StudentGoalProgressRepository
            from app.repositories.student_kc_progress_repository import StudentKCProgressRepository
            
            # Initialize repositories
            goal_progress_repo = StudentGoalProgressRepository(db.session)
            kc_progress_repo = StudentKCProgressRepository(db.session)
            
            # Get incomplete goals (below 100% mastery)
            incomplete_goals = goal_progress_repo.get_incomplete_goals(student_id, threshold=100.0)
            
            # Get incomplete knowledge components (below 100% mastery)
            incomplete_kcs = kc_progress_repo.get_incomplete_kcs(student_id, threshold=100.0)
            
            # Limit the data for AI context (avoid overwhelming the prompt)
            max_goals = 10
            max_kcs = 15
            
            return {
                'incomplete_goals': incomplete_goals[:max_goals],
                'incomplete_knowledge_components': incomplete_kcs[:max_kcs],
                'total_incomplete_goals': len(incomplete_goals),
                'total_incomplete_kcs': len(incomplete_kcs),
                'mastery_context_note': 'This shows goals and knowledge components where the student has not yet achieved 100% mastery'
            }
            
        except Exception as e:
            print(f"Error getting mastery context for student {student_id}: {e}")
            return {
                'incomplete_goals': [],
                'incomplete_knowledge_components': [],
                'total_incomplete_goals': 0,
                'total_incomplete_kcs': 0,
                'mastery_context_note': f'Error loading mastery data: {str(e)}'
            }
    
    def update_mastery_from_ai_delta(self, student_id: int, mastery_delta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update student mastery progress based on AI-generated delta changes
        
        Args:
            student_id: The student ID
            mastery_delta: Dictionary containing mastery updates from AI analysis
                          Example: {
                              "goal_patches": [
                                  {"goal_code": "4.NBT.A.1", "mastery_percentage": 75.0}
                              ],
                              "kc_patches": [
                                  {"goal_code": "4.NBT.A.1", "kc_code": "place-value", "mastery_percentage": 85.0}
                              ]
                          }
            
        Returns:
            Dictionary with update results
        """
        try:
            from app.repositories.student_goal_progress_repository import StudentGoalProgressRepository
            from app.repositories.student_kc_progress_repository import StudentKCProgressRepository
            
            # Initialize repositories
            goal_progress_repo = StudentGoalProgressRepository(db.session)
            kc_progress_repo = StudentKCProgressRepository(db.session)
            
            results = {
                'updated_goals': [],
                'updated_kcs': [],
                'errors': []
            }
            
            # Process goal patches
            goal_patches = mastery_delta.get('goal_patches', [])
            if goal_patches:
                try:
                    updated_goals = goal_progress_repo.update_from_ai_delta(student_id, goal_patches)
                    results['updated_goals'] = [goal.to_dict() for goal in updated_goals]
                    print(f"✅ Updated {len(updated_goals)} goal progress records from AI delta")
                except Exception as goal_error:
                    error_msg = f"Error updating goal progress: {str(goal_error)}"
                    results['errors'].append(error_msg)
                    print(f"❌ {error_msg}")
            
            # Process KC patches
            kc_patches = mastery_delta.get('kc_patches', [])
            if kc_patches:
                try:
                    updated_kcs = kc_progress_repo.update_from_ai_delta(student_id, kc_patches)
                    results['updated_kcs'] = [kc.to_dict() for kc in updated_kcs]
                    print(f"✅ Updated {len(updated_kcs)} KC progress records from AI delta")
                except Exception as kc_error:
                    error_msg = f"Error updating KC progress: {str(kc_error)}"
                    results['errors'].append(error_msg)
                    print(f"❌ {error_msg}")
            
            # Log summary
            total_updates = len(results['updated_goals']) + len(results['updated_kcs'])
            if total_updates > 0:
                print(f"✅ Successfully updated {total_updates} mastery records for student {student_id}")
            else:
                print(f"ℹ️ No mastery updates for student {student_id}")
            
            return results
            
        except Exception as e:
            error_msg = f"Error updating mastery from AI delta for student {student_id}: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'updated_goals': [],
                'updated_kcs': [],
                'errors': [error_msg]
            }
    
    def get_mastery_map(self, student_id: int) -> Dict[str, Any]:
        """
        Get comprehensive mastery map for a student (for admin UI and API)
        
        Args:
            student_id: The student ID
            
        Returns:
            Dictionary with complete mastery map
        """
        try:
            from app.repositories.student_goal_progress_repository import StudentGoalProgressRepository
            from app.repositories.student_kc_progress_repository import StudentKCProgressRepository
            
            # Initialize repositories
            goal_progress_repo = StudentGoalProgressRepository(db.session)
            kc_progress_repo = StudentKCProgressRepository(db.session)
            
            # Get goal mastery map
            goal_mastery_map = goal_progress_repo.get_mastery_map(student_id)
            
            # Get KC mastery map
            kc_mastery_map = kc_progress_repo.get_kc_mastery_map(student_id)
            
            # Combine both maps
            return {
                'student_id': student_id,
                'goal_mastery': goal_mastery_map,
                'kc_mastery': kc_mastery_map,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting mastery map for student {student_id}: {e}")
            return {
                'student_id': student_id,
                'goal_mastery': {
                    'overall_mastery_percentage': 0.0,
                    'total_goals_tracked': 0,
                    'mastery_by_subject': {},
                    'error': str(e)
                },
                'kc_mastery': {
                    'overall_kc_mastery_percentage': 0.0,
                    'total_kcs_tracked': 0,
                    'kc_mastery_by_subject': {},
                    'error': str(e)
                },
                'generated_at': datetime.utcnow().isoformat()
            }