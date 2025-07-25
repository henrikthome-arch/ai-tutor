#!/usr/bin/env python3
"""
Debug script to identify the "Total Students = 0" dashboard bug
"""

import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.student import Student
from app.services.student_service import StudentService

def debug_student_stats():
    """Debug the student statistics issue"""
    
    # Create application context
    app = create_app('development')
    
    with app.app_context():
        print("🔍 Debugging Student Statistics")
        print("=" * 50)
        
        # Test database connection
        try:
            db.create_all()
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return
        
        # Test raw Student model query
        try:
            raw_count = Student.query.count()
            print(f"📊 Raw Student.query.count(): {raw_count}")
        except Exception as e:
            print(f"❌ Raw query error: {e}")
            print(f"   Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
        
        # Test all students query
        try:
            all_students = Student.query.all()
            print(f"📊 Student.query.all() length: {len(all_students)}")
            for i, student in enumerate(all_students[:3]):  # Show first 3
                print(f"   Student {i+1}: ID={student.id}, Name={student.full_name}")
        except Exception as e:
            print(f"❌ All students query error: {e}")
            import traceback
            traceback.print_exc()
        
        # Test student service
        print("\n🔧 Testing StudentService")
        try:
            service = StudentService()
            stats = service.get_system_stats()
            print(f"📊 StudentService.get_system_stats(): {stats}")
        except Exception as e:
            print(f"❌ StudentService error: {e}")
            import traceback
            traceback.print_exc()
        
        # Check database tables exist
        print("\n🗄️ Database Tables Check")
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Available tables: {tables}")
            
            if 'student' in tables:
                columns = inspector.get_columns('student')
                print(f"📋 Student table columns: {[col['name'] for col in columns]}")
            else:
                print("❌ 'student' table not found!")
                
        except Exception as e:
            print(f"❌ Table inspection error: {e}")
        
        # Try to create a test student if none exist
        if raw_count == 0:
            print("\n➕ Attempting to create test student...")
            try:
                from app.models.profile import Profile
                
                test_student = Student(
                    first_name="Test",
                    last_name="Student",
                    student_type="International",
                    phone_number="+1234567890"
                )
                db.session.add(test_student)
                db.session.flush()
                
                test_profile = Profile(
                    student_id=test_student.id,
                    grade="5",
                    curriculum="Test Curriculum"
                )
                db.session.add(test_profile)
                db.session.commit()
                
                print(f"✅ Created test student with ID: {test_student.id}")
                
                # Re-test stats
                new_stats = service.get_system_stats()
                print(f"📊 New stats after test student: {new_stats}")
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error creating test student: {e}")
                import traceback
                traceback.print_exc()

if __name__ == '__main__':
    debug_student_stats()