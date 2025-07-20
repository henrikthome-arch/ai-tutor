import os
import sys
import unittest
from test_sql_storage import TestSQLStorage

def run_tests():
    """Run the SQL storage tests"""
    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSQLStorage)
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Print the results
    print("\n=== Test Results ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    
    # Return True if all tests passed, False otherwise
    return len(result.errors) == 0 and len(result.failures) == 0

if __name__ == "__main__":
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed! The SQL-based storage implementation is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the output above for details.")
        sys.exit(1)