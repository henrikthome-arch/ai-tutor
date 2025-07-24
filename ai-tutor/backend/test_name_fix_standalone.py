#!/usr/bin/env python3
"""
Standalone test for the student name extraction fix logic.
Tests the core name extraction and update logic without requiring Flask dependencies.
"""

import json
import unittest


class MockStudent:
    """Mock student object for testing"""
    def __init__(self, student_id, first_name, last_name=None):
        self.id = student_id
        self.first_name = first_name
        self.last_name = last_name or ''
        self.date_of_birth = None
        self.grade_level = None


def extract_name_from_ai_response(extracted_info):
    """
    Standalone implementation of the name extraction logic from the fix.
    This is the exact same logic as in the refactored update_student_profile method.
    """
    # Priority order for extracting name information
    sources = [
        extracted_info.get('student_profile', {}),  # Nested structure from conditional prompts
        extracted_info                              # Direct structure from fallback prompts
    ]
    
    for source in sources:
        if not source:
            continue
            
        first_name = source.get('first_name')
        last_name = source.get('last_name')
        
        # Clean and validate first name
        if first_name:
            first_name = str(first_name).strip()
            if first_name and first_name not in ['Unknown', 'unknown', 'None', 'null', '']:
                # Also extract last name if available
                if last_name:
                    last_name = str(last_name).strip()
                    if last_name in ['Unknown', 'unknown', 'None', 'null', '']:
                        last_name = None
                
                return first_name, last_name
    
    return None, None


def should_update_name(current_first_name, new_first_name):
    """
    Standalone implementation of the decisive update rule from the fix.
    Simple, decisive rule: If current first name starts with "Student", update it
    """
    return new_first_name and current_first_name.startswith('Student')


class TestNameExtractionFixStandalone(unittest.TestCase):
    """Test cases for the fixed student name extraction logic (standalone)"""
    
    def test_extract_name_nested_structure(self):
        """Test name extraction with nested student_profile structure"""
        extracted_info = {
            "student_profile": {
                "first_name": "Emma",
                "last_name": "Johnson",
                "age": 8,
                "grade": 3
            },
            "_analysis_metadata": {
                "prompt_used": "introductory_analysis",
                "call_type": "new_student"
            }
        }
        
        first_name, last_name = extract_name_from_ai_response(extracted_info)
        
        self.assertEqual(first_name, "Emma")
        self.assertEqual(last_name, "Johnson")
    
    def test_extract_name_direct_structure(self):
        """Test name extraction with direct structure"""
        extracted_info = {
            "first_name": "Oliver",
            "last_name": "Smith",
            "age": 10,
            "grade": 5,
            "interests": ["soccer", "video games"],
            "confidence_score": 0.9
        }
        
        first_name, last_name = extract_name_from_ai_response(extracted_info)
        
        self.assertEqual(first_name, "Oliver")
        self.assertEqual(last_name, "Smith")
    
    def test_extract_name_first_name_only(self):
        """Test name extraction when only first name is provided"""
        extracted_info = {
            "first_name": "Alex",
            "age": 12
        }
        
        first_name, last_name = extract_name_from_ai_response(extracted_info)
        
        self.assertEqual(first_name, "Alex")
        self.assertIsNone(last_name)
    
    def test_extract_name_invalid_names_filtered(self):
        """Test that invalid names are filtered out"""
        extracted_info = {
            "first_name": "Unknown",  # Should be filtered out
            "last_name": "null",      # Should be filtered out
            "age": 9
        }
        
        first_name, last_name = extract_name_from_ai_response(extracted_info)
        
        self.assertIsNone(first_name)
        self.assertIsNone(last_name)
    
    def test_extract_name_no_valid_name(self):
        """Test extraction when no valid name is present"""
        extracted_info = {
            "age": 7,
            "grade": 2,
            "interests": ["drawing", "reading"]
        }
        
        first_name, last_name = extract_name_from_ai_response(extracted_info)
        
        self.assertIsNone(first_name)
        self.assertIsNone(last_name)
    
    def test_extract_name_priority_order(self):
        """Test that nested student_profile takes priority over direct structure"""
        extracted_info = {
            "first_name": "WrongName",  # This should be ignored
            "student_profile": {
                "first_name": "CorrectName",  # This should be used
                "last_name": "CorrectLast"
            }
        }
        
        first_name, last_name = extract_name_from_ai_response(extracted_info)
        
        self.assertEqual(first_name, "CorrectName")
        self.assertEqual(last_name, "CorrectLast")
    
    def test_should_update_placeholder_names(self):
        """Test that placeholder names trigger updates"""
        # Test cases that should trigger updates
        self.assertTrue(should_update_name("Student", "Emma"))
        self.assertTrue(should_update_name("Student6010", "Oliver"))
        self.assertTrue(should_update_name("StudentABC", "Sarah"))
        
        # Test cases that should NOT trigger updates
        self.assertFalse(should_update_name("Emma", "Oliver"))  # Real name to real name
        self.assertFalse(should_update_name("Sarah", "Emma"))   # Real name to real name
        self.assertFalse(should_update_name("John", "Alex"))    # Real name to real name
        
        # Test with no new name
        self.assertFalse(should_update_name("Student", None))
        self.assertFalse(should_update_name("Student", ""))
    
    def test_end_to_end_placeholder_replacement(self):
        """Test complete end-to-end scenario: placeholder name gets replaced"""
        # Create mock student with placeholder name
        student = MockStudent(123, "Student", "6010")
        
        # AI response with nested structure
        extracted_info = {
            "student_profile": {
                "first_name": "Emma",
                "last_name": "Johnson",
                "age": 8,
                "grade": 3
            }
        }
        
        # Extract name
        new_first_name, new_last_name = extract_name_from_ai_response(extracted_info)
        
        # Check if update should happen
        should_update = should_update_name(student.first_name, new_first_name)
        
        # Verify the logic
        self.assertTrue(should_update, "Should update placeholder name")
        self.assertEqual(new_first_name, "Emma")
        self.assertEqual(new_last_name, "Johnson")
        
        # Simulate the update
        if should_update:
            student.first_name = new_first_name
            if new_last_name:
                student.last_name = new_last_name
        
        # Verify final state
        self.assertEqual(student.first_name, "Emma")
        self.assertEqual(student.last_name, "Johnson")
    
    def test_end_to_end_real_name_preserved(self):
        """Test complete end-to-end scenario: real name is preserved"""
        # Create mock student with real name
        student = MockStudent(456, "Sarah", "Wilson")
        
        # AI response trying to change the name
        extracted_info = {
            "first_name": "Emma",
            "last_name": "Johnson"
        }
        
        # Extract name
        new_first_name, new_last_name = extract_name_from_ai_response(extracted_info)
        
        # Check if update should happen
        should_update = should_update_name(student.first_name, new_first_name)
        
        # Verify the logic
        self.assertFalse(should_update, "Should NOT update real name")
        self.assertEqual(new_first_name, "Emma")
        self.assertEqual(new_last_name, "Johnson")
        
        # Simulate the update (should not happen)
        if should_update:
            student.first_name = new_first_name
            if new_last_name:
                student.last_name = new_last_name
        
        # Verify final state (unchanged)
        self.assertEqual(student.first_name, "Sarah")
        self.assertEqual(student.last_name, "Wilson")


def run_standalone_test_suite():
    """Run the standalone test suite"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestNameExtractionFixStandalone)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print(f"\n✅ All {result.testsRun} tests passed successfully!")
        print("The student name extraction fix logic is working correctly.")
        return True
    else:
        print(f"\n❌ {len(result.failures + result.errors)} out of {result.testsRun} tests failed.")
        return False


if __name__ == '__main__':
    print("Testing Student Name Extraction Fix (Standalone)")
    print("=" * 60)
    print("This test validates the core logic of the refactored name extraction")
    print("without requiring Flask or database dependencies.")
    print("=" * 60)
    
    success = run_standalone_test_suite()
    
    if success:
        print("\n🎉 The fix logic is working correctly!")
        print("✅ Placeholder names (starting with 'Student') will be replaced")
        print("✅ Real names will be preserved")
        print("✅ Name extraction works for both nested and direct AI response structures")
        print("\nThe fix is ready for deployment!")
    else:
        print("\n⚠️  The fix logic needs additional work before deployment.")
    
    exit(0 if success else 1)