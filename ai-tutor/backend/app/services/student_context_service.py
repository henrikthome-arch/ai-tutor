"""
Student Context Service for v4 context contract
Provides comprehensive student context for AI tutoring sessions
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from app import db
from app.models.student import Student
from app.models.curriculum import Curriculum
from app.repositories import student_repository, student_profile_repository, student_memory_repository
from app.repositories.curriculum_repository import get_grade_atlas


class StudentContextService:
    """Service class for building v4 student context for AI tutoring"""
    
    def __init__(self):
        pass
    
    def build(self, student_id: int) -> Dict[str, Any]:
        """
        Build comprehensive v4 student context for AI tutoring
        
        Args:
            student_id: The student ID
            
        Returns:
            Dictionary containing v4 context structure with:
            - demographics
            - profile 
            - memories
            - progress
            - _curriculum (curriculum atlas)
            - context_version: 4
        """
        try:
            # Get basic student data
            student = Student.query.get(student_id)
            if not student:
                return {
                    'error': 'Student not found',
                    'student_id': student_id,
                    'context_version': 4
                }
            
            # Build demographics block
            demographics = self._build_demographics(student)
            
            # Build profile block
            profile = self._build_profile(student)
            
            # Build memories block
            memories = self._build_memories(student_id)
            
            # Build progress block
            progress = self._build_progress(student_id)
            
            # Build curriculum atlas block
            curriculum_atlas = self._build_curriculum_atlas(student)
            
            # Assemble v4 context
            context = {
                'student_id': student_id,
                'context_version': 4,
                'demographics': demographics,
                'profile': profile,
                'memories': memories,
                'progress': progress,
                '_curriculum': curriculum_atlas,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            print(f"✅ Built v4 context for student {student_id}")
            return context
            
        except Exception as e:
            print(f"❌ Error building v4 context for student {student_id}: {e}")
            return {
                'error': str(e),
                'student_id': student_id,
                'context_version': 4,
                'generated_at': datetime.utcnow().isoformat()
            }
    
    def _build_demographics(self, student: Student) -> Dict[str, Any]:
        """Build demographics block"""
        return {
            'student_id': student.id,
            'name': student.full_name,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'age': student.age,
            'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
            'grade_level': student.get_grade(),
            'student_type': student.student_type,
            'phone_number': student.phone_number,
            'created_at': student.created_at.isoformat() if student.created_at else None
        }
    
    def _build_profile(self, student: Student) -> Dict[str, Any]:
        """Build profile block with current AI-generated profile and legacy arrays"""
        try:
            # Get current AI-generated profile
            current_profile = student_profile_repository.get_current(student.id)
            
            # Build profile structure
            profile = {
                'current_narrative': current_profile.get('narrative', '') if current_profile else '',
                'current_traits': current_profile.get('traits', {}) if current_profile else {},
                'profile_last_updated': current_profile.get('updated_at') if current_profile else None,
                'legacy_arrays': {
                    'interests': student.interests or [],
                    'learning_preferences': student.learning_preferences or [],
                    'motivational_triggers': student.motivational_triggers or []
                }
            }
            
            return profile
            
        except Exception as e:
            print(f"Error building profile for student {student.id}: {e}")
            return {
                'current_narrative': '',
                'current_traits': {},
                'profile_last_updated': None,
                'legacy_arrays': {
                    'interests': student.interests or [],
                    'learning_preferences': student.learning_preferences or [],
                    'motivational_triggers': student.motivational_triggers or []
                },
                'error': str(e)
            }
    
    def _build_memories(self, student_id: int) -> Dict[str, Any]:
        """Build memories block organized by scope"""
        try:
            # Get memories grouped by scope
            memories_by_scope = student_memory_repository.get_by_scope_grouped(student_id)
            
            # Build memories structure
            memories = {
                'personal_facts': memories_by_scope.get('personal_fact', []),
                'game_states': memories_by_scope.get('game_state', []),
                'strategy_logs': memories_by_scope.get('strategy_log', []),
                'total_memories': sum(len(scope_memories) for scope_memories in memories_by_scope.values())
            }
            
            return memories
            
        except Exception as e:
            print(f"Error building memories for student {student_id}: {e}")
            return {
                'personal_facts': [],
                'game_states': [],
                'strategy_logs': [],
                'total_memories': 0,
                'error': str(e)
            }
    
    def _build_progress(self, student_id: int) -> Dict[str, Any]:
        """Build progress block with mastery tracking data"""
        try:
            from app.repositories.student_goal_progress_repository import StudentGoalProgressRepository
            from app.repositories.student_kc_progress_repository import StudentKCProgressRepository
            
            # Initialize repositories
            goal_progress_repo = StudentGoalProgressRepository(db.session)
            kc_progress_repo = StudentKCProgressRepository(db.session)
            
            # Get progress data
            goal_mastery_map = goal_progress_repo.get_mastery_map(student_id)
            kc_mastery_map = kc_progress_repo.get_kc_mastery_map(student_id)
            
            # Get incomplete items for AI awareness (limited for context size)
            incomplete_goals = goal_progress_repo.get_incomplete_goals(student_id, threshold=100.0)[:10]
            incomplete_kcs = kc_progress_repo.get_incomplete_kcs(student_id, threshold=100.0)[:15]
            
            # Build progress structure
            progress = {
                'overall_mastery': {
                    'goal_mastery_percentage': goal_mastery_map.get('overall_mastery_percentage', 0.0),
                    'kc_mastery_percentage': kc_mastery_map.get('overall_kc_mastery_percentage', 0.0),
                    'total_goals_tracked': goal_mastery_map.get('total_goals_tracked', 0),
                    'total_kcs_tracked': kc_mastery_map.get('total_kcs_tracked', 0)
                },
                'mastery_by_subject': goal_mastery_map.get('mastery_by_subject', {}),
                'incomplete_goals': incomplete_goals,
                'incomplete_knowledge_components': incomplete_kcs,
                'progress_summary': f"Tracking {goal_mastery_map.get('total_goals_tracked', 0)} goals and {kc_mastery_map.get('total_kcs_tracked', 0)} knowledge components"
            }
            
            return progress
            
        except Exception as e:
            print(f"Error building progress for student {student_id}: {e}")
            return {
                'overall_mastery': {
                    'goal_mastery_percentage': 0.0,
                    'kc_mastery_percentage': 0.0,
                    'total_goals_tracked': 0,
                    'total_kcs_tracked': 0
                },
                'mastery_by_subject': {},
                'incomplete_goals': [],
                'incomplete_knowledge_components': [],
                'progress_summary': 'Error loading progress data',
                'error': str(e)
            }
    
    def _build_curriculum_atlas(self, student: Student) -> Dict[str, Any]:
        """Build curriculum atlas block using the new repository method"""
        try:
            # Get default curriculum (or student's assigned curriculum if available)
            default_curriculum = Curriculum.query.filter_by(is_default=True).first()
            if not default_curriculum:
                return {
                    'error': 'No default curriculum found',
                    'subjects': {}
                }
            
            # Get student's grade level
            grade_level = student.get_grade()
            if not grade_level or grade_level == 'Unknown':
                grade_level = 1  # Default to grade 1 if unknown
            
            # Get curriculum atlas using the new repository method (with Redis caching)
            curriculum_atlas = get_grade_atlas(default_curriculum.id, grade_level)
            
            # Add metadata
            curriculum_atlas['curriculum_name'] = default_curriculum.name
            curriculum_atlas['curriculum_type'] = default_curriculum.curriculum_type
            curriculum_atlas['atlas_generated_at'] = datetime.utcnow().isoformat()
            
            return curriculum_atlas
            
        except Exception as e:
            print(f"Error building curriculum atlas for student {student.id}: {e}")
            return {
                'error': str(e),
                'subjects': {},
                'atlas_generated_at': datetime.utcnow().isoformat()
            }
    
    def get_context_summary(self, student_id: int) -> Dict[str, Any]:
        """
        Get a lightweight summary of the student context (for performance)
        
        Args:
            student_id: The student ID
            
        Returns:
            Dictionary with context summary
        """
        try:
            student = Student.query.get(student_id)
            if not student:
                return {'error': 'Student not found'}
            
            # Get memory counts by scope
            memories_by_scope = student_memory_repository.get_by_scope_grouped(student_id)
            memory_counts = {scope: len(memories) for scope, memories in memories_by_scope.items()}
            
            # Get basic progress summary
            try:
                from app.repositories.student_goal_progress_repository import StudentGoalProgressRepository
                goal_progress_repo = StudentGoalProgressRepository(db.session)
                goal_mastery_map = goal_progress_repo.get_mastery_map(student_id)
                mastery_percentage = goal_mastery_map.get('overall_mastery_percentage', 0.0)
            except:
                mastery_percentage = 0.0
            
            return {
                'student_id': student_id,
                'name': student.full_name,
                'age': student.age,
                'grade': student.get_grade(),
                'memory_counts': memory_counts,
                'overall_mastery_percentage': mastery_percentage,
                'context_version': 4,
                'summary_generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting context summary for student {student_id}: {e}")
            return {
                'error': str(e),
                'student_id': student_id,
                'context_version': 4
            }