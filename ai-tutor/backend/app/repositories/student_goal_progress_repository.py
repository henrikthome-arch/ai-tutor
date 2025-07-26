"""
Student Goal Progress repository for database operations
Manages student mastery progress on curriculum goals with UPSERT operations
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.mastery_tracking import StudentGoalProgress, CurriculumGoal


class StudentGoalProgressRepository:
    """Repository for student goal progress operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get(self, student_id: int, goal_id: int) -> Optional[StudentGoalProgress]:
        """
        Get progress for a specific student and goal
        
        Args:
            student_id: The student ID
            goal_id: The goal ID
            
        Returns:
            StudentGoalProgress object or None if not found
        """
        try:
            return self.session.query(StudentGoalProgress)\
                              .filter_by(student_id=student_id, goal_id=goal_id)\
                              .first()
        except Exception as e:
            print(f"Error getting goal progress for student {student_id}, goal {goal_id}: {e}")
            return None
    
    def get_all_for_student(self, student_id: int) -> List[StudentGoalProgress]:
        """
        Get all goal progress records for a student
        
        Args:
            student_id: The student ID
            
        Returns:
            List of StudentGoalProgress objects
        """
        try:
            return self.session.query(StudentGoalProgress)\
                              .filter_by(student_id=student_id)\
                              .order_by(StudentGoalProgress.last_updated.desc())\
                              .all()
        except Exception as e:
            print(f"Error getting all goal progress for student {student_id}: {e}")
            return []
    
    def get_for_goal(self, goal_id: int) -> List[StudentGoalProgress]:
        """
        Get all progress records for a specific goal
        
        Args:
            goal_id: The goal ID
            
        Returns:
            List of StudentGoalProgress objects
        """
        try:
            return self.session.query(StudentGoalProgress)\
                              .filter_by(goal_id=goal_id)\
                              .order_by(StudentGoalProgress.mastery_percentage.desc())\
                              .all()
        except Exception as e:
            print(f"Error getting progress for goal {goal_id}: {e}")
            return []
    
    def get_incomplete_goals(self, student_id: int, threshold: float = 100.0) -> List[Dict[str, Any]]:
        """
        Get goals with mastery below threshold (for AI context)
        
        Args:
            student_id: The student ID
            threshold: Mastery threshold (default 100%)
            
        Returns:
            List of goal progress dictionaries with goal details
        """
        try:
            results = self.session.query(StudentGoalProgress, CurriculumGoal)\
                                 .join(CurriculumGoal, StudentGoalProgress.goal_id == CurriculumGoal.id)\
                                 .filter(StudentGoalProgress.student_id == student_id)\
                                 .filter(StudentGoalProgress.mastery_percentage < threshold)\
                                 .order_by(StudentGoalProgress.mastery_percentage.asc())\
                                 .all()
            
            incomplete_goals = []
            for progress, goal in results:
                goal_data = {
                    'goal_id': goal.id,
                    'goal_code': goal.goal_code,
                    'title': goal.title,
                    'description': goal.description,
                    'subject': goal.subject,
                    'grade_level': goal.grade_level,
                    'mastery_percentage': progress.mastery_percentage,
                    'last_updated': progress.last_updated.isoformat() if progress.last_updated else None
                }
                incomplete_goals.append(goal_data)
            
            return incomplete_goals
            
        except Exception as e:
            print(f"Error getting incomplete goals for student {student_id}: {e}")
            return []
    
    def upsert(self, student_id: int, goal_id: int, mastery_percentage: float) -> StudentGoalProgress:
        """
        Insert or update goal progress for a student (UPSERT operation)
        
        Args:
            student_id: The student ID
            goal_id: The goal ID
            mastery_percentage: The mastery percentage (0.0 to 100.0)
            
        Returns:
            The created/updated StudentGoalProgress object
        """
        try:
            # Validate mastery percentage
            if not (0.0 <= mastery_percentage <= 100.0):
                raise ValueError(f"Mastery percentage must be between 0.0 and 100.0, got {mastery_percentage}")
            
            # Check for existing progress
            existing = self.get(student_id, goal_id)
            
            if existing:
                # Update existing progress
                existing.mastery_percentage = mastery_percentage
                existing.last_updated = datetime.utcnow()
                
                self.session.commit()
                
                print(f"✅ Updated goal progress for student {student_id}, goal {goal_id}: {mastery_percentage}%")
                return existing
            else:
                # Create new progress record
                new_progress = StudentGoalProgress(
                    student_id=student_id,
                    goal_id=goal_id,
                    mastery_percentage=mastery_percentage
                )
                
                self.session.add(new_progress)
                self.session.commit()
                
                print(f"✅ Created goal progress for student {student_id}, goal {goal_id}: {mastery_percentage}%")
                return new_progress
                
        except Exception as e:
            self.session.rollback()
            print(f"Error upserting goal progress for student {student_id}, goal {goal_id}: {e}")
            raise e
    
    def upsert_multiple(self, student_id: int, goal_progress_updates: Dict[int, float]) -> List[StudentGoalProgress]:
        """
        Batch upsert multiple goal progress records
        
        Args:
            student_id: The student ID
            goal_progress_updates: Dictionary with goal_id as key and mastery_percentage as value
            
        Returns:
            List of created/updated StudentGoalProgress objects
        """
        try:
            results = []
            
            for goal_id, mastery_percentage in goal_progress_updates.items():
                result = self.upsert(student_id, goal_id, mastery_percentage)
                results.append(result)
            
            print(f"✅ Batch updated {len(goal_progress_updates)} goal progress records for student {student_id}")
            return results
            
        except Exception as e:
            print(f"Error batch upserting goal progress for student {student_id}: {e}")
            raise e
    
    def update_from_ai_delta(self, student_id: int, goal_patches: List[Dict[str, Any]]) -> List[StudentGoalProgress]:
        """
        Update goal progress based on AI-generated delta changes
        
        Args:
            student_id: The student ID
            goal_patches: List of goal progress updates from AI
                         Example: [{"goal_code": "4.NBT.A.1", "mastery_percentage": 75.0}]
            
        Returns:
            List of updated StudentGoalProgress objects
        """
        try:
            results = []
            
            for patch in goal_patches:
                goal_code = patch.get('goal_code')
                mastery_percentage = patch.get('mastery_percentage')
                
                if not goal_code or mastery_percentage is None:
                    print(f"⚠️ Invalid goal patch: {patch}")
                    continue
                
                # Find goal by code
                goal = self.session.query(CurriculumGoal).filter_by(goal_code=goal_code).first()
                if not goal:
                    print(f"⚠️ Goal not found: {goal_code}")
                    continue
                
                # Upsert progress
                result = self.upsert(student_id, goal.id, mastery_percentage)
                results.append(result)
            
            print(f"✅ Updated {len(results)} goal progress records from AI delta for student {student_id}")
            return results
            
        except Exception as e:
            print(f"Error updating goal progress from AI delta for student {student_id}: {e}")
            raise e
    
    def get_mastery_map(self, student_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive mastery map for a student
        
        Args:
            student_id: The student ID
            
        Returns:
            Dictionary with mastery map data
        """
        try:
            # Get all progress with goal details
            results = self.session.query(StudentGoalProgress, CurriculumGoal)\
                                 .join(CurriculumGoal, StudentGoalProgress.goal_id == CurriculumGoal.id)\
                                 .filter(StudentGoalProgress.student_id == student_id)\
                                 .order_by(CurriculumGoal.subject, CurriculumGoal.grade_level, CurriculumGoal.goal_code)\
                                 .all()
            
            # Group by subject and grade
            mastery_by_subject = {}
            total_goals = 0
            total_mastery = 0.0
            
            for progress, goal in results:
                subject = goal.subject
                grade = goal.grade_level
                
                if subject not in mastery_by_subject:
                    mastery_by_subject[subject] = {}
                if grade not in mastery_by_subject[subject]:
                    mastery_by_subject[subject][grade] = []
                
                goal_data = {
                    'goal_id': goal.id,
                    'goal_code': goal.goal_code,
                    'title': goal.title,
                    'description': goal.description,
                    'mastery_percentage': progress.mastery_percentage,
                    'last_updated': progress.last_updated.isoformat() if progress.last_updated else None
                }
                
                mastery_by_subject[subject][grade].append(goal_data)
                total_goals += 1
                total_mastery += progress.mastery_percentage
            
            # Calculate overall statistics
            overall_mastery = total_mastery / total_goals if total_goals > 0 else 0.0
            
            return {
                'student_id': student_id,
                'overall_mastery_percentage': round(overall_mastery, 2),
                'total_goals_tracked': total_goals,
                'mastery_by_subject': mastery_by_subject,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting mastery map for student {student_id}: {e}")
            return {
                'student_id': student_id,
                'overall_mastery_percentage': 0.0,
                'total_goals_tracked': 0,
                'mastery_by_subject': {},
                'generated_at': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def delete_all_for_student(self, student_id: int) -> int:
        """
        Delete all goal progress for a student (GDPR compliance)
        
        Args:
            student_id: The student ID
            
        Returns:
            Number of progress records deleted
        """
        try:
            deleted_count = self.session.query(StudentGoalProgress)\
                                       .filter_by(student_id=student_id)\
                                       .delete()
            self.session.commit()
            
            print(f"✅ Deleted {deleted_count} goal progress records for student {student_id}")
            return deleted_count
            
        except Exception as e:
            self.session.rollback()
            print(f"Error deleting goal progress for student {student_id}: {e}")
            raise e
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get system-wide goal progress statistics
        
        Returns:
            Dictionary with progress statistics
        """
        try:
            from sqlalchemy import distinct
            
            # Total progress records
            total_records = self.session.query(func.count(StudentGoalProgress.student_id)).scalar()
            
            # Unique students with progress
            students_with_progress = self.session.query(func.count(distinct(StudentGoalProgress.student_id))).scalar()
            
            # Average mastery percentage
            avg_mastery = self.session.query(func.avg(StudentGoalProgress.mastery_percentage)).scalar()
            
            # Mastery distribution
            high_mastery = self.session.query(func.count(StudentGoalProgress.student_id))\
                                      .filter(StudentGoalProgress.mastery_percentage >= 80.0).scalar()
            
            medium_mastery = self.session.query(func.count(StudentGoalProgress.student_id))\
                                        .filter(StudentGoalProgress.mastery_percentage >= 50.0,
                                               StudentGoalProgress.mastery_percentage < 80.0).scalar()
            
            low_mastery = self.session.query(func.count(StudentGoalProgress.student_id))\
                                     .filter(StudentGoalProgress.mastery_percentage < 50.0).scalar()
            
            return {
                'total_progress_records': total_records,
                'students_with_progress': students_with_progress,
                'average_mastery_percentage': round(avg_mastery, 2) if avg_mastery else 0.0,
                'mastery_distribution': {
                    'high_mastery_80_plus': high_mastery,
                    'medium_mastery_50_79': medium_mastery,
                    'low_mastery_below_50': low_mastery
                }
            }
            
        except Exception as e:
            print(f"Error getting goal progress statistics: {e}")
            return {
                'total_progress_records': 0,
                'students_with_progress': 0,
                'average_mastery_percentage': 0.0,
                'mastery_distribution': {
                    'high_mastery_80_plus': 0,
                    'medium_mastery_50_79': 0,
                    'low_mastery_below_50': 0
                }
            }