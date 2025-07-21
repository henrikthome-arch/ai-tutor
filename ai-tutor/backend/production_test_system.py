#!/usr/bin/env python3
"""
Production Self-Testing System for AI Tutor
Tests end-to-end workflow on render.com with real database
"""

import json
import requests
from datetime import datetime
from typing import Dict, Any, List, Tuple
from app import db, app
from app.repositories import student_repository, session_repository
from system_logger import log_system, log_webhook, log_error

class ProductionTestSuite:
    """Production testing suite for AI Tutor core functionality"""
    
    def __init__(self):
        self.test_results = []
        self.test_student_id = None
        self.test_session_id = None
        
    def log_test_result(self, test_name: str, success: bool, message: str, details: Dict = None):
        """Log a test result"""
        self.test_results.append({
            'test_name': test_name,
            'success': success,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })
        
        # Also log to system logger
        level = 'INFO' if success else 'ERROR'
        log_system(f"Production Test: {test_name} - {message}", 
                  test_result=success, details=details, level=level)
    
    def test_database_connection(self) -> bool:
        """Test database connectivity and table existence"""
        try:
            # Test basic connection
            from sqlalchemy import text
            result = db.session.execute(text('SELECT 1')).fetchall()
            
            # Test table existence
            from app.models.student import Student
            from app.models.session import Session
            from app.models.system_log import SystemLog
            
            student_count = Student.query.count()
            session_count = Session.query.count()
            log_count = SystemLog.query.count()
            
            details = {
                'students': student_count,
                'sessions': session_count, 
                'logs': log_count
            }
            
            self.log_test_result(
                'Database Connection',
                True,
                f'Database operational - Students: {student_count}, Sessions: {session_count}, Logs: {log_count}',
                details
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                'Database Connection',
                False,
                f'Database connection failed: {str(e)}',
                {'error': str(e)}
            )
            return False
    
    def test_student_creation(self) -> bool:
        """Test student creation via repository"""
        try:
            # Create test student
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            student_data = {
                'first_name': 'Production',
                'last_name': f'Test_{timestamp}',
                'phone_number': f'+1555TEST{timestamp[-4:]}',
                'student_type': 'International',
                'school_id': None,
                'interests': ['testing', 'validation'],
                'learning_preferences': ['systematic']
            }
            
            # Create student
            new_student = student_repository.create(student_data)
            
            if new_student and 'id' in new_student:
                self.test_student_id = new_student['id']
                
                # Verify retrieval
                retrieved = student_repository.get_by_id(self.test_student_id)
                
                if retrieved:
                    self.log_test_result(
                        'Student Creation',
                        True,
                        f'Student created and retrieved successfully (ID: {self.test_student_id})',
                        {'student_id': self.test_student_id, 'name': f"{student_data['first_name']} {student_data['last_name']}"}
                    )
                    return True
                else:
                    self.log_test_result(
                        'Student Creation',
                        False,
                        'Student created but retrieval failed',
                        {'student_id': self.test_student_id}
                    )
                    return False
            else:
                self.log_test_result(
                    'Student Creation',
                    False,
                    'Student creation returned invalid result',
                    {'result': new_student}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                'Student Creation',
                False,
                f'Student creation failed: {str(e)}',
                {'error': str(e)}
            )
            return False
    
    def test_session_creation(self) -> bool:
        """Test session creation via repository"""
        if not self.test_student_id:
            self.log_test_result(
                'Session Creation',
                False,
                'Cannot test session creation - no test student available',
                {}
            )
            return False
            
        try:
            # Create test session
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            session_data = {
                'student_id': self.test_student_id,
                'call_id': f'production_test_{timestamp}',
                'session_type': 'phone',
                'start_datetime': datetime.now(),
                'duration': 180,  # 3 minutes
                'transcript': f'Production test conversation - {timestamp}',
                'summary': 'Test session for production validation',
                'topics_covered': ['testing'],
                'engagement_score': 95
            }
            
            # Create session
            new_session = session_repository.create(session_data)
            
            if new_session and 'id' in new_session:
                self.test_session_id = new_session['id']
                
                # Verify retrieval
                retrieved = session_repository.get_by_id(self.test_session_id)
                
                if retrieved:
                    self.log_test_result(
                        'Session Creation',
                        True,
                        f'Session created and retrieved successfully (ID: {self.test_session_id})',
                        {'session_id': self.test_session_id, 'student_id': self.test_student_id}
                    )
                    return True
                else:
                    self.log_test_result(
                        'Session Creation',
                        False,
                        'Session created but retrieval failed',
                        {'session_id': self.test_session_id}
                    )
                    return False
            else:
                self.log_test_result(
                    'Session Creation',
                    False,
                    'Session creation returned invalid result',
                    {'result': new_session}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                'Session Creation',
                False,
                f'Session creation failed: {str(e)}',
                {'error': str(e)}
            )
            return False
    
    def test_system_logging(self) -> bool:
        """Test system logging functionality"""
        try:
            # Test different log types
            test_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            log_system(f"Production test system message - {test_id}", test_marker=True)
            log_webhook("production-test", f"Production test webhook - {test_id}", test_marker=True)
            
            # Test error logging
            try:
                raise ValueError(f"Production test error - {test_id}")
            except Exception as e:
                log_error("PRODUCTION_TEST", f"Production test error logging - {test_id}", e, test_marker=True)
            
            self.log_test_result(
                'System Logging',
                True,
                'System logging completed successfully',
                {'test_id': test_id}
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                'System Logging',
                False,
                f'System logging failed: {str(e)}',
                {'error': str(e)}
            )
            return False
    
    def test_webhook_simulation(self) -> bool:
        """Test webhook processing simulation"""
        try:
            # Test phone normalization function
            from admin_server import normalize_phone_number
            
            test_phone = "5551234567"
            normalized = normalize_phone_number(test_phone)
            
            expected = "+15551234567"
            if normalized == expected:
                self.log_test_result(
                    'Webhook Processing',
                    True,
                    f'Phone normalization working correctly: {test_phone} → {normalized}',
                    {'input': test_phone, 'output': normalized}
                )
                return True
            else:
                self.log_test_result(
                    'Webhook Processing',
                    False,
                    f'Phone normalization incorrect: {test_phone} → {normalized} (expected {expected})',
                    {'input': test_phone, 'output': normalized, 'expected': expected}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                'Webhook Processing',
                False,
                f'Webhook processing test failed: {str(e)}',
                {'error': str(e)}
            )
            return False
    
    def test_mcp_integration(self) -> bool:
        """Test MCP server integration (if available)"""
        try:
            # Test if MCP server is accessible locally
            # This would test the system on render.com
            import os
            base_url = os.getenv('BASE_URL', 'http://localhost:5000')
            mcp_url = f"{base_url.replace(':5000', ':3000')}/health"
            
            response = requests.get(mcp_url, timeout=5)
            if response.status_code == 200:
                self.log_test_result(
                    'MCP Integration',
                    True,
                    'MCP server accessible and responding',
                    {'mcp_url': mcp_url, 'status': response.status_code}
                )
                return True
            else:
                self.log_test_result(
                    'MCP Integration',
                    False,
                    f'MCP server responded with status {response.status_code}',
                    {'mcp_url': mcp_url, 'status': response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                'MCP Integration',
                False,
                f'MCP server not accessible: {str(e)}',
                {'error': str(e)}
            )
            return False
    
    def cleanup_test_data(self) -> None:
        """Clean up test data created during testing"""
        try:
            # Clean up test session
            if self.test_session_id:
                session_repository.delete(self.test_session_id)
                
            # Clean up test student
            if self.test_student_id:
                student_repository.delete(self.test_student_id)
                
            self.log_test_result(
                'Cleanup',
                True,
                'Test data cleaned up successfully',
                {'session_id': self.test_session_id, 'student_id': self.test_student_id}
            )
            
        except Exception as e:
            self.log_test_result(
                'Cleanup',
                False,
                f'Test data cleanup failed: {str(e)}',
                {'error': str(e)}
            )
    
    def run_full_test_suite(self) -> Dict[str, Any]:
        """Run the complete test suite"""
        print("🧪 Starting Production Test Suite...")
        
        # Run all tests
        test_functions = [
            self.test_database_connection,
            self.test_student_creation,
            self.test_session_creation,
            self.test_system_logging,
            self.test_webhook_simulation,
            self.test_mcp_integration
        ]
        
        passed = 0
        for test_func in test_functions:
            if test_func():
                passed += 1
        
        # Cleanup
        self.cleanup_test_data()
        
        # Calculate summary
        total = len(test_functions)
        success_rate = (passed / total) * 100
        
        summary = {
            'test_results': self.test_results,
            'summary': {
                'total_tests': total,
                'passed': passed,
                'failed': total - passed,
                'success_rate': success_rate,
                'overall_status': 'PASS' if passed == total else 'PARTIAL' if passed > 0 else 'FAIL',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Log overall result
        log_system(
            f"Production Test Suite Complete: {passed}/{total} tests passed ({success_rate:.1f}%)",
            test_suite_summary=summary['summary'],
            level='INFO' if passed == total else 'WARNING'
        )
        
        return summary

# Function to be called from admin routes
def run_production_tests() -> Dict[str, Any]:
    """Run production tests and return results"""
    with app.app_context():
        test_suite = ProductionTestSuite()
        return test_suite.run_full_test_suite()