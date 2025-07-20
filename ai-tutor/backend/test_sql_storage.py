import os
import sys
import json
from datetime import datetime
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import models and repositories
from app.models.base import Base
from app.models.student import Student
from app.models.school import School
from app.models.curriculum import Curriculum
from app.models.session import Session
from app.models.assessment import Assessment
from app.repositories.student_repository import StudentRepository
from app.repositories.school_repository import SchoolRepository
from app.repositories.curriculum_repository import CurriculumRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.assessment_repository import AssessmentRepository

# Import transcript analyzer
from transcript_analyzer import TranscriptAnalyzer

class TestSQLStorage(unittest.TestCase):
    def setUp(self):
        """Set up the test database and repositories"""
        # Create an in-memory SQLite database for testing
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        
        # Create a session factory
        Session = sessionmaker(bind=self.engine)
        self.db_session = Session()
        
        # Create repositories
        self.student_repo = StudentRepository(self.db_session)
        self.school_repo = SchoolRepository(self.db_session)
        self.curriculum_repo = CurriculumRepository(self.db_session)
        self.session_repo = SessionRepository(self.db_session)
        self.assessment_repo = AssessmentRepository(self.db_session)
        
        # Create the transcript analyzer
        self.transcript_analyzer = TranscriptAnalyzer(self.student_repo)
        
    def tearDown(self):
        """Clean up after each test"""
        self.db_session.close()
        
    def test_school_crud(self):
        """Test CRUD operations for schools"""
        # Create a school
        school = School(name="Test School", location="Test Location")
        self.school_repo.create(school)
        
        # Read the school
        retrieved_school = self.school_repo.get_by_id(school.id)
        self.assertEqual(retrieved_school.name, "Test School")
        self.assertEqual(retrieved_school.location, "Test Location")
        
        # Update the school
        school.name = "Updated School"
        self.school_repo.update(school)
        updated_school = self.school_repo.get_by_id(school.id)
        self.assertEqual(updated_school.name, "Updated School")
        
        # Delete the school
        self.school_repo.delete(school.id)
        deleted_school = self.school_repo.get_by_id(school.id)
        self.assertIsNone(deleted_school)
        
    def test_curriculum_crud(self):
        """Test CRUD operations for curriculums"""
        # Create a curriculum
        curriculum_data = {
            "name": "Test Curriculum",
            "grade": 4,
            "subject": "Math",
            "units": [
                {
                    "name": "Unit 1",
                    "topics": ["Topic 1", "Topic 2"]
                }
            ]
        }
        curriculum = Curriculum(
            name="Test Curriculum",
            grade=4,
            subject="Math",
            content=json.dumps(curriculum_data)
        )
        self.curriculum_repo.create(curriculum)
        
        # Read the curriculum
        retrieved_curriculum = self.curriculum_repo.get_by_id(curriculum.id)
        self.assertEqual(retrieved_curriculum.name, "Test Curriculum")
        self.assertEqual(retrieved_curriculum.grade, 4)
        self.assertEqual(retrieved_curriculum.subject, "Math")
        
        # Update the curriculum
        curriculum.name = "Updated Curriculum"
        self.curriculum_repo.update(curriculum)
        updated_curriculum = self.curriculum_repo.get_by_id(curriculum.id)
        self.assertEqual(updated_curriculum.name, "Updated Curriculum")
        
        # Delete the curriculum
        self.curriculum_repo.delete(curriculum.id)
        deleted_curriculum = self.curriculum_repo.get_by_id(curriculum.id)
        self.assertIsNone(deleted_curriculum)
        
    def test_student_crud(self):
        """Test CRUD operations for students"""
        # Create a school first
        school = School(name="Test School", location="Test Location")
        self.school_repo.create(school)
        
        # Create a student
        student = Student(
            name="Test Student",
            grade=4,
            school_id=school.id,
            profile=json.dumps({
                "learning_style": "visual",
                "interests": ["math", "science"],
                "strengths": ["problem solving"],
                "areas_for_improvement": ["reading comprehension"]
            })
        )
        self.student_repo.create(student)
        
        # Read the student
        retrieved_student = self.student_repo.get_by_id(student.id)
        self.assertEqual(retrieved_student.name, "Test Student")
        self.assertEqual(retrieved_student.grade, 4)
        self.assertEqual(retrieved_student.school_id, school.id)
        
        # Update the student
        student.name = "Updated Student"
        self.student_repo.update(student)
        updated_student = self.student_repo.get_by_id(student.id)
        self.assertEqual(updated_student.name, "Updated Student")
        
        # Delete the student
        self.student_repo.delete(student.id)
        deleted_student = self.student_repo.get_by_id(student.id)
        self.assertIsNone(deleted_student)
        
    def test_session_crud(self):
        """Test CRUD operations for sessions"""
        # Create a school
        school = School(name="Test School", location="Test Location")
        self.school_repo.create(school)
        
        # Create a student
        student = Student(
            name="Test Student",
            grade=4,
            school_id=school.id,
            profile=json.dumps({
                "learning_style": "visual",
                "interests": ["math", "science"],
                "strengths": ["problem solving"],
                "areas_for_improvement": ["reading comprehension"]
            })
        )
        self.student_repo.create(student)
        
        # Create a session
        session = Session(
            student_id=student.id,
            date=datetime.now(),
            duration=30,
            transcript="This is a test transcript",
            summary=json.dumps({
                "topics_covered": ["addition", "subtraction"],
                "student_understanding": "good",
                "areas_for_improvement": ["multiplication"]
            })
        )
        self.session_repo.create(session)
        
        # Read the session
        retrieved_session = self.session_repo.get_by_id(session.id)
        self.assertEqual(retrieved_session.student_id, student.id)
        self.assertEqual(retrieved_session.transcript, "This is a test transcript")
        
        # Update the session
        session.transcript = "Updated transcript"
        self.session_repo.update(session)
        updated_session = self.session_repo.get_by_id(session.id)
        self.assertEqual(updated_session.transcript, "Updated transcript")
        
        # Delete the session
        self.session_repo.delete(session.id)
        deleted_session = self.session_repo.get_by_id(session.id)
        self.assertIsNone(deleted_session)
        
    def test_assessment_crud(self):
        """Test CRUD operations for assessments"""
        # Create a school
        school = School(name="Test School", location="Test Location")
        self.school_repo.create(school)
        
        # Create a student
        student = Student(
            name="Test Student",
            grade=4,
            school_id=school.id,
            profile=json.dumps({
                "learning_style": "visual",
                "interests": ["math", "science"],
                "strengths": ["problem solving"],
                "areas_for_improvement": ["reading comprehension"]
            })
        )
        self.student_repo.create(student)
        
        # Create an assessment
        assessment = Assessment(
            student_id=student.id,
            date=datetime.now(),
            subject="Math",
            score=85,
            details=json.dumps({
                "questions": 20,
                "correct": 17,
                "topics": ["addition", "subtraction", "multiplication"]
            })
        )
        self.assessment_repo.create(assessment)
        
        # Read the assessment
        retrieved_assessment = self.assessment_repo.get_by_id(assessment.id)
        self.assertEqual(retrieved_assessment.student_id, student.id)
        self.assertEqual(retrieved_assessment.subject, "Math")
        self.assertEqual(retrieved_assessment.score, 85)
        
        # Update the assessment
        assessment.score = 90
        self.assessment_repo.update(assessment)
        updated_assessment = self.assessment_repo.get_by_id(assessment.id)
        self.assertEqual(updated_assessment.score, 90)
        
        # Delete the assessment
        self.assessment_repo.delete(assessment.id)
        deleted_assessment = self.assessment_repo.get_by_id(assessment.id)
        self.assertIsNone(deleted_assessment)
        
    def test_relationships(self):
        """Test relationships between entities"""
        # Create a school
        school = School(name="Test School", location="Test Location")
        self.school_repo.create(school)
        
        # Create a curriculum
        curriculum_data = {
            "name": "Test Curriculum",
            "grade": 4,
            "subject": "Math",
            "units": [
                {
                    "name": "Unit 1",
                    "topics": ["Topic 1", "Topic 2"]
                }
            ]
        }
        curriculum = Curriculum(
            name="Test Curriculum",
            grade=4,
            subject="Math",
            content=json.dumps(curriculum_data)
        )
        self.curriculum_repo.create(curriculum)
        
        # Associate the curriculum with the school
        school.curriculum_ids = json.dumps([curriculum.id])
        self.school_repo.update(school)
        
        # Create a student
        student = Student(
            name="Test Student",
            grade=4,
            school_id=school.id,
            profile=json.dumps({
                "learning_style": "visual",
                "interests": ["math", "science"],
                "strengths": ["problem solving"],
                "areas_for_improvement": ["reading comprehension"]
            })
        )
        self.student_repo.create(student)
        
        # Create a session
        session = Session(
            student_id=student.id,
            date=datetime.now(),
            duration=30,
            transcript="This is a test transcript",
            summary=json.dumps({
                "topics_covered": ["addition", "subtraction"],
                "student_understanding": "good",
                "areas_for_improvement": ["multiplication"]
            })
        )
        self.session_repo.create(session)
        
        # Create an assessment
        assessment = Assessment(
            student_id=student.id,
            date=datetime.now(),
            subject="Math",
            score=85,
            details=json.dumps({
                "questions": 20,
                "correct": 17,
                "topics": ["addition", "subtraction", "multiplication"]
            })
        )
        self.assessment_repo.create(assessment)
        
        # Test school-student relationship
        retrieved_student = self.student_repo.get_by_id(student.id)
        self.assertEqual(retrieved_student.school_id, school.id)
        
        # Test student-session relationship
        retrieved_session = self.session_repo.get_by_id(session.id)
        self.assertEqual(retrieved_session.student_id, student.id)
        
        # Test student-assessment relationship
        retrieved_assessment = self.assessment_repo.get_by_id(assessment.id)
        self.assertEqual(retrieved_assessment.student_id, student.id)
        
        # Test school-curriculum relationship
        retrieved_school = self.school_repo.get_by_id(school.id)
        curriculum_ids = json.loads(retrieved_school.curriculum_ids)
        self.assertIn(curriculum.id, curriculum_ids)
        
    def test_transcript_analyzer(self):
        """Test the transcript analyzer with SQL storage"""
        # Create a student
        student = Student(
            name="Test Student",
            grade=4,
            profile=json.dumps({
                "learning_style": "visual",
                "interests": ["math", "science"],
                "strengths": ["problem solving"],
                "areas_for_improvement": ["reading comprehension"]
            })
        )
        self.student_repo.create(student)
        
        # Create a test transcript
        transcript = """
        Tutor: Hello! How are you today?
        Student: I'm good. I'm having trouble with fractions.
        Tutor: Let's work on fractions then. What specifically is giving you trouble?
        Student: I don't understand how to add fractions with different denominators.
        Tutor: That's a common challenge. Let me explain how to find a common denominator.
        Student: That makes sense. I think I get it now.
        Tutor: Great! Let's try a practice problem. What is 1/2 + 1/3?
        Student: I think it's 5/6.
        Tutor: Excellent! That's correct. You're making good progress.
        """
        
        # Analyze the transcript
        self.transcript_analyzer.analyze_transcript(transcript, student.id)
        
        # Verify that the student profile was updated
        updated_student = self.student_repo.get_by_id(student.id)
        profile = json.loads(updated_student.profile)
        
        # Check that the profile contains information extracted from the transcript
        self.assertIn("fractions", str(profile))
        
if __name__ == "__main__":
    unittest.main()