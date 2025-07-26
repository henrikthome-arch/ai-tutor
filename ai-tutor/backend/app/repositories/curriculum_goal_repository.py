"""
Curriculum Goal repository for database operations
Manages curriculum goals and their knowledge components (read-only operations)
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.models.mastery_tracking import CurriculumGoal, GoalKC


class CurriculumGoalRepository:
    """Repository for curriculum goal read operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, goal_id: int) -> Optional[CurriculumGoal]:
        """
        Get a curriculum goal by ID
        
        Args:
            goal_id: The goal ID
            
        Returns:
            CurriculumGoal object or None if not found
        """
        try:
            return self.session.query(CurriculumGoal).filter_by(id=goal_id).first()
        except Exception as e:
            print(f"Error getting goal by ID {goal_id}: {e}")
            return None
    
    def get_by_code(self, goal_code: str) -> Optional[CurriculumGoal]:
        """
        Get a curriculum goal by code
        
        Args:
            goal_code: The goal code (e.g., "4.NBT.A.1")
            
        Returns:
            CurriculumGoal object or None if not found
        """
        try:
            return self.session.query(CurriculumGoal).filter_by(goal_code=goal_code).first()
        except Exception as e:
            print(f"Error getting goal by code {goal_code}: {e}")
            return None
    
    def get_all(self) -> List[CurriculumGoal]:
        """
        Get all curriculum goals
        
        Returns:
            List of CurriculumGoal objects
        """
        try:
            return self.session.query(CurriculumGoal).order_by(CurriculumGoal.goal_code).all()
        except Exception as e:
            print(f"Error getting all goals: {e}")
            return []
    
    def get_by_subject_and_grade(self, subject: str, grade_level: int) -> List[CurriculumGoal]:
        """
        Get curriculum goals by subject and grade level
        
        Args:
            subject: The subject name (e.g., "Mathematics")
            grade_level: The grade level
            
        Returns:
            List of CurriculumGoal objects
        """
        try:
            return self.session.query(CurriculumGoal)\
                              .filter_by(subject=subject, grade_level=grade_level)\
                              .order_by(CurriculumGoal.goal_code)\
                              .all()
        except Exception as e:
            print(f"Error getting goals for {subject} grade {grade_level}: {e}")
            return []
    
    def get_by_grade_level(self, grade_level: int) -> List[CurriculumGoal]:
        """
        Get all curriculum goals for a specific grade level
        
        Args:
            grade_level: The grade level
            
        Returns:
            List of CurriculumGoal objects
        """
        try:
            return self.session.query(CurriculumGoal)\
                              .filter_by(grade_level=grade_level)\
                              .order_by(CurriculumGoal.subject, CurriculumGoal.goal_code)\
                              .all()
        except Exception as e:
            print(f"Error getting goals for grade {grade_level}: {e}")
            return []
    
    def get_knowledge_components(self, goal_id: int) -> List[GoalKC]:
        """
        Get all knowledge components for a specific goal
        
        Args:
            goal_id: The goal ID
            
        Returns:
            List of GoalKC objects
        """
        try:
            return self.session.query(GoalKC)\
                              .filter_by(goal_id=goal_id)\
                              .order_by(GoalKC.kc_code)\
                              .all()
        except Exception as e:
            print(f"Error getting knowledge components for goal {goal_id}: {e}")
            return []
    
    def get_knowledge_component(self, goal_id: int, kc_code: str) -> Optional[GoalKC]:
        """
        Get a specific knowledge component by goal ID and KC code
        
        Args:
            goal_id: The goal ID
            kc_code: The knowledge component code
            
        Returns:
            GoalKC object or None if not found
        """
        try:
            return self.session.query(GoalKC)\
                              .filter_by(goal_id=goal_id, kc_code=kc_code)\
                              .first()
        except Exception as e:
            print(f"Error getting KC {kc_code} for goal {goal_id}: {e}")
            return None
    
    def get_goals_with_kcs(self, subject: Optional[str] = None, grade_level: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get goals with their knowledge components in a structured format
        
        Args:
            subject: Optional subject filter
            grade_level: Optional grade level filter
            
        Returns:
            List of dictionaries with goal data and KCs
        """
        try:
            # Build base query
            query = self.session.query(CurriculumGoal)
            
            if subject:
                query = query.filter_by(subject=subject)
            if grade_level:
                query = query.filter_by(grade_level=grade_level)
            
            goals = query.order_by(CurriculumGoal.goal_code).all()
            
            result = []
            for goal in goals:
                kcs = self.get_knowledge_components(goal.id)
                
                goal_data = goal.to_dict()
                goal_data['knowledge_components'] = [kc.to_dict() for kc in kcs]
                result.append(goal_data)
            
            return result
            
        except Exception as e:
            print(f"Error getting goals with KCs: {e}")
            return []
    
    def search_goals(self, search_term: str) -> List[CurriculumGoal]:
        """
        Search goals by title, description, or goal code
        
        Args:
            search_term: The search term
            
        Returns:
            List of matching CurriculumGoal objects
        """
        try:
            search_pattern = f"%{search_term}%"
            return self.session.query(CurriculumGoal)\
                              .filter(
                                  (CurriculumGoal.title.ilike(search_pattern)) |
                                  (CurriculumGoal.description.ilike(search_pattern)) |
                                  (CurriculumGoal.goal_code.ilike(search_pattern))
                              )\
                              .order_by(CurriculumGoal.goal_code)\
                              .all()
        except Exception as e:
            print(f"Error searching goals with term '{search_term}': {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get curriculum goal statistics
        
        Returns:
            Dictionary with goal statistics
        """
        try:
            from sqlalchemy import func, distinct
            
            # Total goals
            total_goals = self.session.query(func.count(CurriculumGoal.id)).scalar()
            
            # Unique subjects
            unique_subjects = self.session.query(func.count(distinct(CurriculumGoal.subject))).scalar()
            
            # Goals by subject
            subject_counts = {}
            subjects = self.session.query(distinct(CurriculumGoal.subject)).all()
            for (subject,) in subjects:
                count = self.session.query(func.count(CurriculumGoal.id))\
                                   .filter_by(subject=subject).scalar()
                subject_counts[subject] = count
            
            # Goals by grade level
            grade_counts = {}
            grades = self.session.query(distinct(CurriculumGoal.grade_level)).all()
            for (grade,) in grades:
                count = self.session.query(func.count(CurriculumGoal.id))\
                                   .filter_by(grade_level=grade).scalar()
                grade_counts[grade] = count
            
            # Total knowledge components
            total_kcs = self.session.query(func.count(GoalKC.goal_id)).scalar()
            
            # Average KCs per goal
            avg_kcs = total_kcs / total_goals if total_goals > 0 else 0
            
            return {
                'total_goals': total_goals,
                'unique_subjects': unique_subjects,
                'goals_by_subject': subject_counts,
                'goals_by_grade': grade_counts,
                'total_knowledge_components': total_kcs,
                'average_kcs_per_goal': round(avg_kcs, 2)
            }
            
        except Exception as e:
            print(f"Error getting goal statistics: {e}")
            return {
                'total_goals': 0,
                'unique_subjects': 0,
                'goals_by_subject': {},
                'goals_by_grade': {},
                'total_knowledge_components': 0,
                'average_kcs_per_goal': 0.0
            }