"""
Student Knowledge Component Progress repository for database operations
Manages student mastery progress on individual knowledge components with UPSERT operations
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.mastery_tracking import StudentKCProgress, CurriculumGoal, GoalKC


class StudentKCProgressRepository:
    """Repository for student knowledge component progress operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get(self, student_id: int, goal_id: int, kc_code: str) -> Optional[StudentKCProgress]:
        """
        Get KC progress for a specific student, goal, and knowledge component
        
        Args:
            student_id: The student ID
            goal_id: The goal ID
            kc_code: The knowledge component code
            
        Returns:
            StudentKCProgress object or None if not found
        """
        try:
            return self.session.query(StudentKCProgress)\
                              .filter_by(student_id=student_id, goal_id=goal_id, kc_code=kc_code)\
                              .first()
        except Exception as e:
            print(f"Error getting KC progress for student {student_id}, goal {goal_id}, KC {kc_code}: {e}")
            return None
    
    def get_all_for_student(self, student_id: int) -> List[StudentKCProgress]:
        """
        Get all KC progress records for a student
        
        Args:
            student_id: The student ID
            
        Returns:
            List of StudentKCProgress objects
        """
        try:
            return self.session.query(StudentKCProgress)\
                              .filter_by(student_id=student_id)\
                              .order_by(StudentKCProgress.last_updated.desc())\
                              .all()
        except Exception as e:
            print(f"Error getting all KC progress for student {student_id}: {e}")
            return []
    
    def get_for_goal(self, student_id: int, goal_id: int) -> List[StudentKCProgress]:
        """
        Get all KC progress records for a student and specific goal
        
        Args:
            student_id: The student ID
            goal_id: The goal ID
            
        Returns:
            List of StudentKCProgress objects
        """
        try:
            return self.session.query(StudentKCProgress)\
                              .filter_by(student_id=student_id, goal_id=goal_id)\
                              .order_by(StudentKCProgress.kc_code)\
                              .all()
        except Exception as e:
            print(f"Error getting KC progress for student {student_id}, goal {goal_id}: {e}")
            return []
    
    def get_incomplete_kcs(self, student_id: int, threshold: float = 100.0) -> List[Dict[str, Any]]:
        """
        Get knowledge components with mastery below threshold (for AI context)
        
        Args:
            student_id: The student ID
            threshold: Mastery threshold (default 100%)
            
        Returns:
            List of KC progress dictionaries with goal and KC details
        """
        try:
            results = self.session.query(StudentKCProgress, CurriculumGoal, GoalKC)\
                                 .join(CurriculumGoal, StudentKCProgress.goal_id == CurriculumGoal.id)\
                                 .join(GoalKC, (StudentKCProgress.goal_id == GoalKC.goal_id) & 
                                              (StudentKCProgress.kc_code == GoalKC.kc_code))\
                                 .filter(StudentKCProgress.student_id == student_id)\
                                 .filter(StudentKCProgress.mastery_percentage < threshold)\
                                 .order_by(StudentKCProgress.mastery_percentage.asc())\
                                 .all()
            
            incomplete_kcs = []
            for progress, goal, goal_kc in results:
                kc_data = {
                    'goal_id': goal.id,
                    'goal_code': goal.goal_code,
                    'goal_title': goal.title,
                    'subject': goal.subject,
                    'grade_level': goal.grade_level,
                    'kc_code': progress.kc_code,
                    'kc_name': goal_kc.kc_name,
                    'kc_description': goal_kc.description,
                    'mastery_percentage': progress.mastery_percentage,
                    'last_updated': progress.last_updated.isoformat() if progress.last_updated else None
                }
                incomplete_kcs.append(kc_data)
            
            return incomplete_kcs
            
        except Exception as e:
            print(f"Error getting incomplete KCs for student {student_id}: {e}")
            return []
    
    def upsert(self, student_id: int, goal_id: int, kc_code: str, mastery_percentage: float) -> StudentKCProgress:
        """
        Insert or update KC progress for a student (UPSERT operation)
        
        Args:
            student_id: The student ID
            goal_id: The goal ID
            kc_code: The knowledge component code
            mastery_percentage: The mastery percentage (0.0 to 100.0)
            
        Returns:
            The created/updated StudentKCProgress object
        """
        try:
            # Validate mastery percentage
            if not (0.0 <= mastery_percentage <= 100.0):
                raise ValueError(f"Mastery percentage must be between 0.0 and 100.0, got {mastery_percentage}")
            
            # Verify that the KC exists for this goal
            goal_kc = self.session.query(GoalKC)\
                                 .filter_by(goal_id=goal_id, kc_code=kc_code)\
                                 .first()
            if not goal_kc:
                raise ValueError(f"Knowledge component {kc_code} does not exist for goal {goal_id}")
            
            # Check for existing progress
            existing = self.get(student_id, goal_id, kc_code)
            
            if existing:
                # Update existing progress
                existing.mastery_percentage = mastery_percentage
                existing.last_updated = datetime.utcnow()
                
                self.session.commit()
                
                print(f"✅ Updated KC progress for student {student_id}, goal {goal_id}, KC {kc_code}: {mastery_percentage}%")
                return existing
            else:
                # Create new progress record
                new_progress = StudentKCProgress(
                    student_id=student_id,
                    goal_id=goal_id,
                    kc_code=kc_code,
                    mastery_percentage=mastery_percentage
                )
                
                self.session.add(new_progress)
                self.session.commit()
                
                print(f"✅ Created KC progress for student {student_id}, goal {goal_id}, KC {kc_code}: {mastery_percentage}%")
                return new_progress
                
        except Exception as e:
            self.session.rollback()
            print(f"Error upserting KC progress for student {student_id}, goal {goal_id}, KC {kc_code}: {e}")
            raise e
    
    def upsert_multiple_for_goal(self, student_id: int, goal_id: int, kc_progress_updates: Dict[str, float]) -> List[StudentKCProgress]:
        """
        Batch upsert multiple KC progress records for a specific goal
        
        Args:
            student_id: The student ID
            goal_id: The goal ID
            kc_progress_updates: Dictionary with kc_code as key and mastery_percentage as value
            
        Returns:
            List of created/updated StudentKCProgress objects
        """
        try:
            results = []
            
            for kc_code, mastery_percentage in kc_progress_updates.items():
                result = self.upsert(student_id, goal_id, kc_code, mastery_percentage)
                results.append(result)
            
            print(f"✅ Batch updated {len(kc_progress_updates)} KC progress records for student {student_id}, goal {goal_id}")
            return results
            
        except Exception as e:
            print(f"Error batch upserting KC progress for student {student_id}, goal {goal_id}: {e}")
            raise e
    
    def update_from_ai_delta(self, student_id: int, kc_patches: List[Dict[str, Any]]) -> List[StudentKCProgress]:
        """
        Update KC progress based on AI-generated delta changes
        
        Args:
            student_id: The student ID
            kc_patches: List of KC progress updates from AI
                       Example: [{"goal_code": "4.NBT.A.1", "kc_code": "place-value", "mastery_percentage": 85.0}]
            
        Returns:
            List of updated StudentKCProgress objects
        """
        try:
            results = []
            
            for patch in kc_patches:
                goal_code = patch.get('goal_code')
                kc_code = patch.get('kc_code')
                mastery_percentage = patch.get('mastery_percentage')
                
                if not goal_code or not kc_code or mastery_percentage is None:
                    print(f"⚠️ Invalid KC patch: {patch}")
                    continue
                
                # Find goal by code
                goal = self.session.query(CurriculumGoal).filter_by(goal_code=goal_code).first()
                if not goal:
                    print(f"⚠️ Goal not found: {goal_code}")
                    continue
                
                # Upsert KC progress
                result = self.upsert(student_id, goal.id, kc_code, mastery_percentage)
                results.append(result)
            
            print(f"✅ Updated {len(results)} KC progress records from AI delta for student {student_id}")
            return results
            
        except Exception as e:
            print(f"Error updating KC progress from AI delta for student {student_id}: {e}")
            raise e
    
    def get_kc_mastery_map(self, student_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive knowledge component mastery map for a student
        
        Args:
            student_id: The student ID
            
        Returns:
            Dictionary with KC mastery map data
        """
        try:
            # Get all KC progress with goal and KC details
            results = self.session.query(StudentKCProgress, CurriculumGoal, GoalKC)\
                                 .join(CurriculumGoal, StudentKCProgress.goal_id == CurriculumGoal.id)\
                                 .join(GoalKC, (StudentKCProgress.goal_id == GoalKC.goal_id) & 
                                              (StudentKCProgress.kc_code == GoalKC.kc_code))\
                                 .filter(StudentKCProgress.student_id == student_id)\
                                 .order_by(CurriculumGoal.subject, CurriculumGoal.grade_level, 
                                          CurriculumGoal.goal_code, StudentKCProgress.kc_code)\
                                 .all()
            
            # Group by subject, grade, and goal
            mastery_by_subject = {}
            total_kcs = 0
            total_mastery = 0.0
            
            for progress, goal, goal_kc in results:
                subject = goal.subject
                grade = goal.grade_level
                goal_code = goal.goal_code
                
                # Initialize nested structure
                if subject not in mastery_by_subject:
                    mastery_by_subject[subject] = {}
                if grade not in mastery_by_subject[subject]:
                    mastery_by_subject[subject][grade] = {}
                if goal_code not in mastery_by_subject[subject][grade]:
                    mastery_by_subject[subject][grade][goal_code] = {
                        'goal_id': goal.id,
                        'goal_title': goal.title,
                        'goal_description': goal.description,
                        'knowledge_components': []
                    }
                
                kc_data = {
                    'kc_code': progress.kc_code,
                    'kc_name': goal_kc.kc_name,
                    'kc_description': goal_kc.description,
                    'mastery_percentage': progress.mastery_percentage,
                    'last_updated': progress.last_updated.isoformat() if progress.last_updated else None
                }
                
                mastery_by_subject[subject][grade][goal_code]['knowledge_components'].append(kc_data)
                total_kcs += 1
                total_mastery += progress.mastery_percentage
            
            # Calculate overall statistics
            overall_mastery = total_mastery / total_kcs if total_kcs > 0 else 0.0
            
            return {
                'student_id': student_id,
                'overall_kc_mastery_percentage': round(overall_mastery, 2),
                'total_kcs_tracked': total_kcs,
                'kc_mastery_by_subject': mastery_by_subject,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting KC mastery map for student {student_id}: {e}")
            return {
                'student_id': student_id,
                'overall_kc_mastery_percentage': 0.0,
                'total_kcs_tracked': 0,
                'kc_mastery_by_subject': {},
                'generated_at': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def get_goal_kc_summary(self, student_id: int, goal_id: int) -> Dict[str, Any]:
        """
        Get KC mastery summary for a specific goal
        
        Args:
            student_id: The student ID
            goal_id: The goal ID
            
        Returns:
            Dictionary with goal KC summary
        """
        try:
            # Get goal details
            goal = self.session.query(CurriculumGoal).filter_by(id=goal_id).first()
            if not goal:
                return {'error': f'Goal {goal_id} not found'}
            
            # Get all KCs for this goal
            goal_kcs = self.session.query(GoalKC).filter_by(goal_id=goal_id).all()
            
            # Get student progress for these KCs
            kc_progress = self.get_for_goal(student_id, goal_id)
            progress_dict = {p.kc_code: p for p in kc_progress}
            
            # Build KC summary
            kcs_summary = []
            total_mastery = 0.0
            kcs_with_progress = 0
            
            for goal_kc in goal_kcs:
                kc_code = goal_kc.kc_code
                progress = progress_dict.get(kc_code)
                
                kc_data = {
                    'kc_code': kc_code,
                    'kc_name': goal_kc.kc_name,
                    'kc_description': goal_kc.description,
                    'mastery_percentage': progress.mastery_percentage if progress else 0.0,
                    'has_progress': progress is not None,
                    'last_updated': progress.last_updated.isoformat() if progress and progress.last_updated else None
                }
                
                kcs_summary.append(kc_data)
                
                if progress:
                    total_mastery += progress.mastery_percentage
                    kcs_with_progress += 1
            
            # Calculate averages
            avg_mastery = total_mastery / kcs_with_progress if kcs_with_progress > 0 else 0.0
            progress_coverage = (kcs_with_progress / len(goal_kcs)) * 100 if goal_kcs else 0.0
            
            return {
                'student_id': student_id,
                'goal_id': goal_id,
                'goal_code': goal.goal_code,
                'goal_title': goal.title,
                'total_kcs': len(goal_kcs),
                'kcs_with_progress': kcs_with_progress,
                'progress_coverage_percentage': round(progress_coverage, 2),
                'average_mastery_percentage': round(avg_mastery, 2),
                'knowledge_components': kcs_summary
            }
            
        except Exception as e:
            print(f"Error getting goal KC summary for student {student_id}, goal {goal_id}: {e}")
            return {'error': str(e)}
    
    def delete_all_for_student(self, student_id: int) -> int:
        """
        Delete all KC progress for a student (GDPR compliance)
        
        Args:
            student_id: The student ID
            
        Returns:
            Number of KC progress records deleted
        """
        try:
            deleted_count = self.session.query(StudentKCProgress)\
                                       .filter_by(student_id=student_id)\
                                       .delete()
            self.session.commit()
            
            print(f"✅ Deleted {deleted_count} KC progress records for student {student_id}")
            return deleted_count
            
        except Exception as e:
            self.session.rollback()
            print(f"Error deleting KC progress for student {student_id}: {e}")
            raise e
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get system-wide KC progress statistics
        
        Returns:
            Dictionary with KC progress statistics
        """
        try:
            from sqlalchemy import distinct
            
            # Total KC progress records
            total_records = self.session.query(func.count(StudentKCProgress.student_id)).scalar()
            
            # Unique students with KC progress
            students_with_progress = self.session.query(func.count(distinct(StudentKCProgress.student_id))).scalar()
            
            # Average KC mastery percentage
            avg_mastery = self.session.query(func.avg(StudentKCProgress.mastery_percentage)).scalar()
            
            # KC mastery distribution
            high_mastery = self.session.query(func.count(StudentKCProgress.student_id))\
                                      .filter(StudentKCProgress.mastery_percentage >= 80.0).scalar()
            
            medium_mastery = self.session.query(func.count(StudentKCProgress.student_id))\
                                        .filter(StudentKCProgress.mastery_percentage >= 50.0,
                                               StudentKCProgress.mastery_percentage < 80.0).scalar()
            
            low_mastery = self.session.query(func.count(StudentKCProgress.student_id))\
                                     .filter(StudentKCProgress.mastery_percentage < 50.0).scalar()
            
            # Unique KCs being tracked
            unique_kcs = self.session.query(func.count(distinct(StudentKCProgress.kc_code))).scalar()
            
            return {
                'total_kc_progress_records': total_records,
                'students_with_kc_progress': students_with_progress,
                'unique_kcs_tracked': unique_kcs,
                'average_kc_mastery_percentage': round(avg_mastery, 2) if avg_mastery else 0.0,
                'kc_mastery_distribution': {
                    'high_mastery_80_plus': high_mastery,
                    'medium_mastery_50_79': medium_mastery,
                    'low_mastery_below_50': low_mastery
                }
            }
            
        except Exception as e:
            print(f"Error getting KC progress statistics: {e}")
            return {
                'total_kc_progress_records': 0,
                'students_with_kc_progress': 0,
                'unique_kcs_tracked': 0,
                'average_kc_mastery_percentage': 0.0,
                'kc_mastery_distribution': {
                    'high_mastery_80_plus': 0,
                    'medium_mastery_50_79': 0,
                    'low_mastery_below_50': 0
                }
            }