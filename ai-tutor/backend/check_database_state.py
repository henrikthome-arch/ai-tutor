#!/usr/bin/env python3
"""
Check current database state for debugging
"""

from app import create_app, db
from app.models.student import Student
from app.models.session import Session
from app.models.profile import Profile
from app.models.curriculum import Curriculum, Subject, CurriculumDetail
from app.models.assessment import StudentSubject
from sqlalchemy import func, select

def main():
    app = create_app()
    with app.app_context():
        print("=== DATABASE STATE CHECK ===")
        
        # Check student count
        stmt = select(func.count(Student.id))
        student_count = db.session.execute(stmt).scalar()
        print(f'Total students in database: {student_count}')
        
        # Check session count
        stmt = select(func.count(Session.id))
        session_count = db.session.execute(stmt).scalar()
        print(f'Total sessions in database: {session_count}')
        
        # Check curriculum data
        stmt = select(func.count(Curriculum.id))
        curriculum_count = db.session.execute(stmt).scalar()
        print(f'Total curriculums in database: {curriculum_count}')
        
        stmt = select(func.count(CurriculumDetail.id))
        curriculum_detail_count = db.session.execute(stmt).scalar()
        print(f'Total curriculum details in database: {curriculum_detail_count}')
        
        stmt = select(func.count(StudentSubject.id))
        student_subject_count = db.session.execute(stmt).scalar()
        print(f'Total student subjects in database: {student_subject_count}')
        
        # Get some student examples if any exist
        if student_count > 0:
            stmt = select(Student).limit(5)
            students = db.session.execute(stmt).scalars().all()
            print(f'\nFirst 5 students:')
            for s in students:
                profile_count = 1 if s.profile else 0
                print(f'  ID: {s.id}, Name: "{s.first_name}" "{s.last_name}", Phone: {s.phone_number}, Profile: {profile_count}')
        else:
            print('\n❌ No students found in database - this explains "Total students = 0"')
            
        # Check if default curriculum exists
        stmt = select(Curriculum).where(Curriculum.is_default == True)
        default_curriculum = db.session.execute(stmt).scalar_one_or_none()
        if default_curriculum:
            print(f'\n✅ Default curriculum found: {default_curriculum.name} (ID: {default_curriculum.id})')
        else:
            print(f'\n❌ No default curriculum found')

if __name__ == "__main__":
    main()