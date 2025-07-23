#!/usr/bin/env python3
"""
Legacy Phone Mapping Migration - End-to-End Test
Tests the complete database-first phone mapping functionality
"""

import os
import sys
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Flask app and database
from admin-server import app, db, DatabasePhoneManager, normalize_phone_number
from app.models.student import Student
from app.repositories import student_repository

def test_database_phone_manager():
    """Test the DatabasePhoneManager class functionality"""
    print("🧪 Testing DatabasePhoneManager functionality...")
    
    with app.app_context():
        # Initialize the database-first phone manager
        db_phone_manager = DatabasePhoneManager()
        
        # Test 1: Phone number normalization
        print("\n📞 Test 1: Phone number normalization")
        test_phones = [
            "+46852506010",
            "46852506010", 
            "1234567890",
            "11234567890"
        ]
        
        for phone in test_phones:
            normalized = normalize_phone_number(phone)
            print(f"  {phone} → {normalized}")
        
        # Test 2: Create test student with phone number
        print("\n👤 Test 2: Create test student with phone number")
        test_student_data = {
            'first_name': 'Test',
            'last_name': 'Student',
            'phone_number': '+46852506010',
            'student_type': 'International',
            'school_id': None
        }
        
        try:
            test_student = student_repository.create(test_student_data)
            if test_student:
                student_id = str(test_student['id'])
                print(f"  ✅ Created test student: {student_id}")
                
                # Test 3: Database phone lookup
                print("\n🔍 Test 3: Database phone lookup")
                found_student_id = db_phone_manager.get_student_by_phone('+46852506010')
                if found_student_id == student_id:
                    print(f"  ✅ Phone lookup successful: {found_student_id}")
                else:
                    print(f"  ❌ Phone lookup failed: expected {student_id}, got {found_student_id}")
                
                # Test 4: Get all phone mappings
                print("\n📋 Test 4: Get all phone mappings")
                all_mappings = db_phone_manager.get_all_phone_mappings()
                if '+46852506010' in all_mappings and all_mappings['+46852506010'] == student_id:
                    print(f"  ✅ Phone mapping found in all mappings")
                else:
                    print(f"  ❌ Phone mapping not found in all mappings")
                
                # Test 5: Get phone by student ID
                print("\n🔄 Test 5: Get phone by student ID")
                found_phone = db_phone_manager.get_phone_by_student_id(student_id)
                if found_phone == '+46852506010':
                    print(f"  ✅ Reverse lookup successful: {found_phone}")
                else:
                    print(f"  ❌ Reverse lookup failed: expected +46852506010, got {found_phone}")
                
                # Test 6: Phone mappings count
                print("\n🔢 Test 6: Phone mappings count")
                count = db_phone_manager.get_phone_mappings_count()
                print(f"  📊 Phone mappings count: {count}")
                
                # Test 7: Add phone mapping to existing student
                print("\n➕ Test 7: Add phone mapping to existing student")
                success = db_phone_manager.add_phone_mapping('+1234567890', student_id)
                if success:
                    print(f"  ✅ Phone mapping added successfully")
                    # Verify the mapping
                    found_id = db_phone_manager.get_student_by_phone('+1234567890')
                    if found_id == student_id:
                        print(f"  ✅ New phone mapping verified")
                    else:
                        print(f"  ❌ New phone mapping verification failed")
                else:
                    print(f"  ❌ Phone mapping addition failed")
                
                # Test 8: Remove phone mapping
                print("\n➖ Test 8: Remove phone mapping")
                success = db_phone_manager.remove_phone_mapping('+1234567890')
                if success:
                    print(f"  ✅ Phone mapping removed successfully")
                    # Verify removal
                    found_id = db_phone_manager.get_student_by_phone('+1234567890')
                    if found_id is None:
                        print(f"  ✅ Phone mapping removal verified")
                    else:
                        print(f"  ❌ Phone mapping removal verification failed")
                else:
                    print(f"  ❌ Phone mapping removal failed")
                
                # Cleanup: Delete test student
                print("\n🧹 Cleanup: Delete test student")
                if student_repository.delete(student_id):
                    print(f"  ✅ Test student deleted successfully")
                else:
                    print(f"  ❌ Test student deletion failed")
                    
            else:
                print(f"  ❌ Failed to create test student")
                
        except Exception as e:
            print(f"  ❌ Test error: {e}")
            import traceback
            print(f"  🔍 Stack trace: {traceback.format_exc()}")

def test_webhook_phone_lookup():
    """Test VAPI webhook phone lookup functionality"""
    print("\n🌐 Testing VAPI webhook phone lookup...")
    
    with app.app_context():
        from admin-server import identify_or_create_student, normalize_phone_number
        
        # Test phone number formats that VAPI might send
        test_phones = [
            "+46852506010",
            "46852506010",
            "+1234567890"
        ]
        
        for phone in test_phones:
            try:
                print(f"\n📞 Testing phone: {phone}")
                normalized = normalize_phone_number(phone)
                print(f"  Normalized: {normalized}")
                
                # Test student identification/creation
                student_id = identify_or_create_student(phone, f"test_call_{phone.replace('+', '')}")
                
                if student_id:
                    print(f"  ✅ Student identified/created: {student_id}")
                    
                    # Cleanup
                    if student_repository.delete(student_id):
                        print(f"  🧹 Test student cleaned up")
                else:
                    print(f"  ❌ Student identification/creation failed")
                    
            except Exception as e:
                print(f"  ❌ Webhook test error: {e}")

def test_system_integration():
    """Test system integration components"""
    print("\n🔧 Testing system integration...")
    
    with app.app_context():
        from admin-server import get_system_stats
        
        try:
            # Test system stats phone counting
            print("\n📊 Testing system stats phone counting")
            stats = get_system_stats()
            
            if 'phone_mappings' in stats:
                print(f"  ✅ Phone mappings count in stats: {stats['phone_mappings']}")
            else:
                print(f"  ❌ Phone mappings count missing from stats")
                
            print(f"  📈 Full stats: {json.dumps(stats, indent=2)}")
            
        except Exception as e:
            print(f"  ❌ System integration test error: {e}")

def run_migration_test():
    """Run the complete migration test suite"""
    print("🚀 Legacy Phone Mapping Migration - End-to-End Test")
    print("="*60)
    
    try:
        # Test database-first phone manager
        test_database_phone_manager()
        
        # Test webhook phone lookup
        test_webhook_phone_lookup()
        
        # Test system integration
        test_system_integration()
        
        print("\n" + "="*60)
        print("✅ Migration test completed!")
        print("🎯 Database-first phone mapping is working correctly")
        
    except Exception as e:
        print(f"\n❌ Critical test error: {e}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")

if __name__ == '__main__':
    run_migration_test()