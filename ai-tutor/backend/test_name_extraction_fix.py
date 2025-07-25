#!/usr/bin/env python3
"""
Unit test for the student name extraction fix.
Tests the refactored update_student_profile method to ensure it properly
replaces placeholder names with AI-extracted names.
"""

import json
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the backend directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestNameExtractionFix(unittest.TestCase):
    """Test cases for the fixed student name extraction logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = None
        
    def create_mock_student(self, student_id, first_name, last_name=None):
        """Create a mock student object"""
        mock_student = MagicMock()
        mock_student.id = student_id
        mock_student.first_name = first_name
        mock_student.last_name = last_name or ''
        mock_student.date_of_birth = None
        mock_student.grade_level = None
        
        # Create mock profile
        mock_profile = MagicMock()
        mock_profile.interests = []
        mock_profile.learning_preferences = []
        mock_student.profile = mock_profile
        
        return mock_student, mock_profile
    
    @patch('transcript_analyzer.flask.has_app_context')
    @patch('transcript_analyzer.Student')
    @patch('transcript_analyzer.Profile')
    @patch('transcript_analyzer.db')
    def test_placeholder_name_replacement_nested_structure(self, mock_db, mock_profile_class, mock_student_class, mock_has_app_context):
        """Test that placeholder names are replaced when AI response has nested structure"""
        from transcript_analyzer import TranscriptAnalyzer
        
        # Setup mocks
        mock_has_app_context.return_value = True
        
        # Create mock student with placeholder name
        mock_student, mock_profile = self.create_mock_student(123, "Student", "6010")
        mock_student_class.query.get.return_value = mock_student
        
        # Create analyzer
        analyzer = TranscriptAnalyzer()
        
        # Create AI response with nested student_profile structure (conditional prompts)
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
        
        # Call the method
        result = analyzer.update_student_profile(123, extracted_info)
        
        # Verify the result
        self.assertTrue(result, "update_student_profile should return True on success")
        
        # Verify that the student name was updated
        self.assertEqual(mock_student.first_name, "Emma")
        self.assertEqual(mock_student.last_name, "Johnson")
        
        # Verify database commit was called
        mock_db.session.commit.assert_called_once()
    
    @patch('transcript_analyzer.flask.has_app_context')
    @patch('transcript_analyzer.Student')
    @patch('transcript_analyzer.Profile')
    @patch('transcript_analyzer.db')
    def test_placeholder_name_replacement_direct_structure(self, mock_db, mock_profile_class, mock_student_class, mock_has_app_context):
        """Test that placeholder names are replaced when AI response has direct structure"""
        from transcript_analyzer import TranscriptAnalyzer
        
        # Setup mocks
        mock_has_app_context.return_value = True
        
        # Create mock student with placeholder name
        mock_student, mock_profile = self.create_mock_student(456, "Student", "1234")
        mock_student_class.query.get.return_value = mock_student
        
        # Create analyzer
        analyzer = TranscriptAnalyzer()
        
        # Create AI response with direct structure (fallback prompts)
        extracted_info = {
            "first_name": "Oliver",
            "last_name": "Smith",
            "age": 10,
            "grade": 5,
            "interests": ["soccer", "video games"],
            "confidence_score": 0.9
        }
        
        # Call the method
        result = analyzer.update_student_profile(456, extracted_info)
        
        # Verify the result
        self.assertTrue(result, "update_student_profile should return True on success")
        
        # Verify that the student name was updated
        self.assertEqual(mock_student.first_name, "Oliver")
        self.assertEqual(mock_student.last_name, "Smith")
        
        # Verify database commit was called
        mock_db.session.commit.assert_called_once()
    
    @patch('transcript_analyzer.flask.has_app_context')
    @patch('transcript_analyzer.Student')
    @patch('transcript_analyzer.Profile')
    @patch('transcript_analyzer.db')
    def test_non_placeholder_name_preserved(self, mock_db, mock_profile_class, mock_student_class, mock_has_app_context):
        """Test that existing non-placeholder names are NOT replaced"""
        from transcript_analyzer import TranscriptAnalyzer
        
        # Setup mocks
        mock_has_app_context.return_value = True
        
        # Create mock student with a real name (not a placeholder)
        mock_student, mock_profile = self.create_mock_student(789, "Sarah", "Wilson")
        mock_student_class.query.get.return_value = mock_student
        
        # Create analyzer
        analyzer = TranscriptAnalyzer()
        
        # Create AI response trying to change the name
        extracted_info = {
            "first_name": "Emma",
            "last_name": "Johnson",
            "age": 8,
            "grade": 3
        }
        
        # Call the method
        result = analyzer.update_student_profile(789, extracted_info)
        
        # Verify the result
        self.assertTrue(result, "update_student_profile should return True on success")
        
        # Verify that the existing name was preserved
        self.assertEqual(mock_student.first_name, "Sarah")
        self.assertEqual(mock_student.last_name, "Wilson")
        
        # Age should still be updated
        from datetime import date
        current_year = date.today().year
        expected_dob = date(current_year - 8, 1, 1)
        self.assertEqual(mock_student.date_of_birth, expected_dob)
    
    @patch('transcript_analyzer.flask.has_app_context')
    @patch('transcript_analyzer.Student')
    @patch('transcript_analyzer.Profile')
    @patch('transcript_analyzer.db')
    def test_placeholder_with_first_name_only(self, mock_db, mock_profile_class, mock_student_class, mock_has_app_context):
        """Test replacement when AI provides only first name"""
        from transcript_analyzer import TranscriptAnalyzer
        
        # Setup mocks
        mock_has_app_context.return_value = True
        
        # Create mock student with placeholder name
        mock_student, mock_profile = self.create_mock_student(101, "Student", "5678")
        mock_student_class.query.get.return_value = mock_student
        
        # Create analyzer
        analyzer = TranscriptAnalyzer()
        
        # Create AI response with only first name
        extracted_info = {
            "first_name": "Alex",
            "age": 12
        }
        
        # Call the method
        result = analyzer.update_student_profile(101, extracted_info)
        
        # Verify the result
        self.assertTrue(result, "update_student_profile should return True on success")
        
        # Verify that the first name was updated, last name kept as is
        self.assertEqual(mock_student.first_name, "Alex")
        self.assertEqual(mock_student.last_name, "5678")  # Should keep existing last name
    
    @patch('transcript_analyzer.flask.has_app_context')
    @patch('transcript_analyzer.Student')
    @patch('transcript_analyzer.Profile')
    @patch('transcript_analyzer.db')
    def test_no_valid_name_extracted(self, mock_db, mock_profile_class, mock_student_class, mock_has_app_context):
        """Test behavior when no valid name is extracted"""
        from transcript_analyzer import TranscriptAnalyzer
        
        # Setup mocks
        mock_has_app_context.return_value = True
        
        # Create mock student with placeholder name
        mock_student, mock_profile = self.create_mock_student(202, "Student", "9999")
        mock_student_class.query.get.return_value = mock_student
        
        # Create analyzer
        analyzer = TranscriptAnalyzer()
        
        # Create AI response with no valid name
        extracted_info = {
            "age": 7,
            "grade": 2,
            "interests": ["drawing", "reading"]
        }
        
        # Call the method
        result = analyzer.update_student_profile(202, extracted_info)
        
        # Verify the result
        self.assertTrue(result, "update_student_profile should return True on success")
        
        # Verify that the placeholder name was NOT changed
        self.assertEqual(mock_student.first_name, "Student")
        self.assertEqual(mock_student.last_name, "9999")
        
        # But other fields should still be updated
        from datetime import date
        current_year = date.today().year
        expected_dob = date(current_year - 7, 1, 1)
        self.assertEqual(mock_student.date_of_birth, expected_dob)
        self.assertEqual(mock_student.grade_level, 2)
    
    @patch('transcript_analyzer.flask.has_app_context')
    @patch('transcript_analyzer.Student')
    @patch('transcript_analyzer.Profile')
    @patch('transcript_analyzer.db')
    def test_edge_case_invalid_names(self, mock_db, mock_profile_class, mock_student_class, mock_has_app_context):
        """Test handling of invalid or filtered names"""
        from transcript_analyzer import TranscriptAnalyzer
        
        # Setup mocks
        mock_has_app_context.return_value = True
        
        # Create mock student with placeholder name
        mock_student, mock_profile = self.create_mock_student(303, "Student", "0001")
        mock_student_class.query.get.return_value = mock_student
        
        # Create analyzer
        analyzer = TranscriptAnalyzer()
        
        # Create AI response with invalid names that should be filtered out
        extracted_info = {
            "first_name": "Unknown",  # Should be filtered out
            "last_name": "null",      # Should be filtered out
            "age": 9
        }
        
        # Call the method
        result = analyzer.update_student_profile(303, extracted_info)
        
        # Verify the result
        self.assertTrue(result, "update_student_profile should return True on success")
        
        # Verify that the placeholder name was NOT changed (invalid names filtered)
        self.assertEqual(mock_student.first_name, "Student")
        self.assertEqual(mock_student.last_name, "0001")


def run_test_suite():
    """Run the complete test suite"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestNameExtractionFix)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print(f"\n✅ All {result.testsRun} tests passed successfully!")
        print("The student name extraction fix is working correctly.")
        return True
    else:
        print(f"\n❌ {len(result.failures + result.errors)} out of {result.testsRun} tests failed.")
        return False


if __name__ == '__main__':
    print("Testing Student Name Extraction Fix")
    print("=" * 50)
    print("This test validates that the refactored update_student_profile method")
    print("correctly replaces placeholder names with AI-extracted names.")
    print("=" * 50)
    
    success = run_test_suite()
    
    if success:
        print("\n🎉 The fix is ready for deployment!")
    else:
        print("\n⚠️  The fix needs additional work before deployment.")
    
    exit(0 if success else 1)