#!/usr/bin/env python3
"""
Test script to verify automatic curriculum assignment during student creation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app, db
from app.services.student_service import StudentService
from app.models.student import Student
from app.models.assessment import StudentSubject
from app.models.curriculum import Curriculum, CurriculumDetail

def test_curriculum_assignment():
    """Test that new students automatically get assigned default curriculum subjects"""
    
    app = create_app()
    with app.app_context():
        print("🧪 Testing Curriculum Assignment During Student Creation")
        print("=" * 60)
        
        # Check if default curriculum exists
        default_curriculum = Curriculum.query.filter_by(is_default=True).first()
        if not default_curriculum:
            print("❌ No default curriculum found. Please run database reset first.")
            return False
        
        print(f"✅ Found default curriculum: {default_curriculum.name}")
        
        # Count curriculum details for grade 3
        grade_3_details = CurriculumDetail.query.filter(
            CurriculumDetail.curriculum_id == default_curriculum.id,
            CurriculumDetail.grade_level >= 3
        ).count()
        
        print(f"📚 Found {grade_3_details} curriculum details for grade 3 and above")
        
        # Create a test student
        service = StudentService()
        print(f"\n👤 Creating test student...")
        
        try:
            student_id = service.create_student(
                name="Test Student Curriculum",
                age=8,
                grade=3,
                interests=["Math", "Science"],
                phone="+1234567890"
            )
            
            print(f"✅ Student created with ID: {student_id}")
            
            # Check if StudentSubject records were created
            student_subjects = StudentSubject.query.filter_by(student_id=int(student_id)).all()
            
            print(f"\n📖 Student Subjects Assigned:")
            print("-" * 30)
            
            for ss in student_subjects:
                subject_name = ss.subject_name or "Unknown Subject"
                grade_level = ss.grade_level or "Unknown Grade"
                curriculum_name = ss.curriculum_name or "Unknown Curriculum"
                
                print(f"  • {subject_name} (Grade {grade_level}) - {curriculum_name}")
                print(f"    - In Use: {ss.is_in_use}")
                print(f"    - Active for Tutoring: {ss.is_active_for_tutoring}")
                print(f"    - Mastery Level: {ss.mastery_level}")
                print()
            
            print(f"📊 Total subjects assigned: {len(student_subjects)}")
            
            if len(student_subjects) == grade_3_details:
                print("✅ SUCCESS: Correct number of subjects assigned!")
                success = True
            else:
                print(f"⚠️ WARNING: Expected {grade_3_details} subjects, got {len(student_subjects)}")
                success = False
            
            # Test VAPI student creation too
            print(f"\n📞 Testing VAPI student creation...")
            
            vapi_student_id = service.create_student_from_call(
                student_id="Caller Test",
                phone="+9876543210",
                call_id="test_call_123"
            )
            
            print(f"✅ VAPI student created with ID: {vapi_student_id}")
            
            # Check VAPI student subjects (grade 1 and above)
            vapi_student_subjects = StudentSubject.query.filter_by(student_id=int(vapi_student_id)).all()
            
            grade_1_details = CurriculumDetail.query.filter(
                CurriculumDetail.curriculum_id == default_curriculum.id,
                CurriculumDetail.grade_level >= 1
            ).count()
            
            print(f"📖 VAPI Student Subjects: {len(vapi_student_subjects)} (expected: {grade_1_details})")
            
            if len(vapi_student_subjects) == grade_1_details:
                print("✅ SUCCESS: VAPI student correctly assigned curriculum!")
                vapi_success = True
            else:
                print(f"⚠️ WARNING: VAPI student - Expected {grade_1_details} subjects, got {len(vapi_student_subjects)}")
                vapi_success = False
            
            return success and vapi_success
            
        except Exception as e:
            print(f"❌ Error during test: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_curriculum_assignment()
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)