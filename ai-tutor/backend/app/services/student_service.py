"""
Student service for business logic
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from types import SimpleNamespace

from app.repositories import student_repository
from app.models.student import Student
from app.models.profile import Profile
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
                    Session.start_time >= today_start,
                    Session.start_time <= today_end
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
                    
                    # Count students using default curriculum (approximation)
                    students_with_default_curriculum = Student.query.join(Profile).filter(
                        Profile.curriculum == default_curriculum_obj.name
                    ).count() if hasattr(Student, 'profile') else 0
                    
            except Exception as curriculum_e:
                print(f"Error getting curriculum stats: {curriculum_e}")
            
            # Server status (always 'Running' for now since we're responding)
            server_status = "Running"
            
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
                'students_with_default_curriculum': students_with_default_curriculum
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
                'students_with_default_curriculum': 0
            }
    
    def get_all_students(self) -> List[Any]:
        """Get all students with profile information"""
        try:
            students = Student.query.all()
            result = []
            
            for student in students:
                student_dict = student.to_dict()
                
                # Add profile information if exists
                if student.profile:
                    student_dict.update({
                        'interests': student.profile.interests or [],
                        'learning_preferences': student.profile.learning_preferences or [],
                        'grade': student.profile.grade or 'Unknown',
                        'curriculum': student.profile.curriculum or 'Unknown'
                    })
                else:
                    student_dict.update({
                        'interests': [],
                        'learning_preferences': [],
                        'grade': 'Unknown',
                        'curriculum': 'Unknown'
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
                        last_session = Session.query.filter_by(student_id=student.id).order_by(Session.start_time.desc()).first()
                        if last_session and last_session.start_time:
                            student_dict['last_session'] = last_session.start_time.strftime('%Y-%m-%d')
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
            
            # Profile data
            profile_data = {}
            if student.profile:
                profile_data = {
                    'name': student.full_name,
                    'age': student.age,
                    'grade': student.profile.grade,
                    'curriculum': student.profile.curriculum,
                    'interests': student.profile.interests or [],
                    'learning_preferences': student.profile.learning_preferences or [],
                    'learning_style': student.profile.learning_style,
                    'motivational_triggers': student.profile.motivational_triggers
                }
            else:
                profile_data = {
                    'name': student.full_name,
                    'age': student.age,
                    'grade': 'Unknown',
                    'curriculum': 'Unknown',
                    'interests': [],
                    'learning_preferences': [],
                    'learning_style': 'Unknown',
                    'motivational_triggers': 'Unknown'
                }
            
            # Sessions data
            sessions_data = []
            for session in student.sessions:
                session_dict = session.to_dict() if hasattr(session, 'to_dict') else {
                    'id': session.id,
                    'start_time': session.start_time.isoformat() if session.start_time else None,
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
            # Create student with basic info
            student_data = {
                'first_name': 'Unknown',
                'last_name': f'Caller {student_id}',
                'phone_number': phone,
                'student_type': 'International'
            }
            
            student = Student(**student_data)
            db.session.add(student)
            db.session.flush()  # Get the ID
            
            # Create basic profile
            profile = Profile(
                student_id=student.id,
                grade='Unknown',
                curriculum='Unknown',
                interests=[],
                learning_preferences=[]
            )
            db.session.add(profile)
            db.session.commit()
            
            return str(student.id)
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating student from call: {e}")
            # Return the original student_id as fallback
            return student_id
    
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
                'student_type': 'International'
            }
            
            # Calculate date of birth from age
            if age and age > 0:
                birth_year = datetime.now().year - age
                student_data['date_of_birth'] = date(birth_year, 1, 1)
            
            student = Student(**student_data)
            db.session.add(student)
            db.session.flush()
            
            # Create profile
            profile = Profile(
                student_id=student.id,
                grade=str(grade),
                curriculum='Unknown',
                interests=interests,
                learning_preferences=[]
            )
            db.session.add(profile)
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
            
            # Update profile
            if student.profile:
                student.profile.grade = str(grade)
                student.profile.interests = interests
            else:
                profile = Profile(
                    student_id=student.id,
                    grade=str(grade),
                    curriculum='Unknown',
                    interests=interests,
                    learning_preferences=[]
                )
                db.session.add(profile)
            
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