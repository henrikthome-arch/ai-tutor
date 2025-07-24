#!/usr/bin/env python3
"""
Test script for name extraction logic
Tests the patterns used to detect default names like "Student 6010"
"""

import re
import json

def test_default_name_patterns():
    """Test the regex patterns used for default name detection"""
    
    print("🔍 Testing Default Name Pattern Detection")
    print("=" * 50)
    
    # Test cases that should be detected as default names
    default_name_cases = [
        "Student 6010",
        "Student 1234", 
        "Student123",
        "Student 999",
        "Student",
        "Unknown_abc123",
        "Student   789",  # Multiple spaces
        "Student2025",
        "Student 0001"
    ]
    
    # Test cases that should NOT be detected as default names  
    real_name_cases = [
        "Emma Smith",
        "John Doe", 
        "Carl",
        "Sarah Johnson",
        "Michael Student",  # Last name is Student
        "Ana Maria",
        "David Thompson",
        "Lisa",
        "Christopher Williams"
    ]
    
    print("Testing cases that SHOULD be detected as default names:")
    print("-" * 50)
    
    for test_case in default_name_cases:
        # Split into parts like the actual code does
        name_parts = test_case.split()
        first_name = name_parts[0] if name_parts else ""
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ""
        full_name = f"{first_name} {last_name}".strip()
        
        # Apply the same checks as in the code (FIXED VERSION)
        is_default_name_checks = {
            'first_equals_Student': first_name == 'Student',
            'full_starts_with_Student_space': full_name.startswith('Student '),
            'contains_Unknown_': 'Unknown_' in full_name,
            'matches_Student_digits': bool(re.match(r'^Student\s*\d+$', full_name)),
            'first_is_just_Student': bool(re.match(r'^Student$', first_name)),
            'matches_generated_pattern': bool(re.match(r'^(Student|Unknown).*\d+$', full_name))
        }
        
        is_default_name = any(is_default_name_checks.values())
        
        status = "✅ DETECTED" if is_default_name else "❌ MISSED"
        print(f"{status}: '{test_case}' -> first='{first_name}', last='{last_name}', full='{full_name}'")
        print(f"    Checks: {json.dumps(is_default_name_checks, indent=8)}")
        print()
    
    print("\nTesting cases that should NOT be detected as default names:")
    print("-" * 50)
    
    for test_case in real_name_cases:
        # Split into parts like the actual code does
        name_parts = test_case.split()
        first_name = name_parts[0] if name_parts else ""
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ""
        full_name = f"{first_name} {last_name}".strip()
        
        # Apply the same checks as in the code (FIXED VERSION)
        is_default_name_checks = {
            'first_equals_Student': first_name == 'Student',
            'full_starts_with_Student_space': full_name.startswith('Student '),
            'contains_Unknown_': 'Unknown_' in full_name,
            'matches_Student_digits': bool(re.match(r'^Student\s*\d+$', full_name)),
            'first_is_just_Student': bool(re.match(r'^Student$', first_name)),
            'matches_generated_pattern': bool(re.match(r'^(Student|Unknown).*\d+$', full_name))
        }
        
        is_default_name = any(is_default_name_checks.values())
        
        status = "✅ CORRECT" if not is_default_name else "❌ FALSE POSITIVE"
        print(f"{status}: '{test_case}' -> first='{first_name}', last='{last_name}', full='{full_name}'")
        if is_default_name:
            print(f"    Checks: {json.dumps(is_default_name_checks, indent=8)}")
        print()

def test_ai_extraction_scenarios():
    """Test scenarios where AI extracts names correctly"""
    
    print("\n🤖 Testing AI Extraction Scenarios")
    print("=" * 50)
    
    # Scenarios based on the bug description
    test_scenarios = [
        {
            "description": "AI extracts 'Carl' in preferred_name field",
            "current_student": {"first_name": "Student", "last_name": "6010"},
            "extracted_info": {"preferred_name": "Carl"},
            "expected_result": {"first_name": "Carl", "last_name": ""}
        },
        {
            "description": "AI extracts 'Emma' in name field", 
            "current_student": {"first_name": "Student", "last_name": "1234"},
            "extracted_info": {"name": "Emma"},
            "expected_result": {"first_name": "Emma", "last_name": ""}
        },
        {
            "description": "AI extracts 'Sarah Johnson' in name field",
            "current_student": {"first_name": "Student", "last_name": "999"},
            "extracted_info": {"name": "Sarah Johnson"},
            "expected_result": {"first_name": "Sarah", "last_name": "Johnson"}
        },
        {
            "description": "Student profile wrapper with preferred_name",
            "current_student": {"first_name": "Student", "last_name": "5678"},
            "extracted_info": {"student_profile": {"preferred_name": "Michael"}},
            "expected_result": {"first_name": "Michael", "last_name": ""}
        },
        {
            "description": "Should NOT update real name",
            "current_student": {"first_name": "Emma", "last_name": "Smith"},
            "extracted_info": {"name": "John"},
            "expected_result": {"first_name": "Emma", "last_name": "Smith"}  # No change
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"Scenario {i}: {scenario['description']}")
        print("-" * 30)
        
        # Simulate the name extraction logic
        current_first = scenario["current_student"].get("first_name", "")
        current_last = scenario["current_student"].get("last_name", "")
        current_full = f"{current_first} {current_last}".strip()
        
        print(f"Current: first='{current_first}', last='{current_last}', full='{current_full}'")
        
        # Check for extracted names
        extracted_info = scenario["extracted_info"]
        extracted_name = None
        
        if 'name' in extracted_info and extracted_info['name'] and extracted_info['name'] != 'Unknown':
            extracted_name = extracted_info['name']
            print(f"Found name in 'name' field: '{extracted_name}'")
        elif 'preferred_name' in extracted_info and extracted_info['preferred_name']:
            extracted_name = extracted_info['preferred_name']
            print(f"Found name in 'preferred_name' field: '{extracted_name}'")
        elif 'student_profile' in extracted_info:
            profile_data = extracted_info['student_profile']
            if 'name' in profile_data and profile_data['name'] and profile_data['name'] != 'Unknown':
                extracted_name = profile_data['name']
                print(f"Found name in student_profile 'name' field: '{extracted_name}'")
            elif 'preferred_name' in profile_data and profile_data['preferred_name']:
                extracted_name = profile_data['preferred_name']
                print(f"Found name in student_profile 'preferred_name' field: '{extracted_name}'")
        
        if extracted_name:
            full_name = str(extracted_name).strip()
            
            if full_name and full_name.lower() not in ['unknown', 'student', 'not specified']:
                name_parts = full_name.split()
                if len(name_parts) >= 1:
                    new_first_name = name_parts[0]
                    new_last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                    
                    # Check if current name is default
                    is_default_name_checks = {
                        'first_equals_Student': current_first == 'Student',
                        'full_starts_with_Student_space': current_full.startswith('Student '),
                        'contains_Unknown_': 'Unknown_' in current_full,
                        'very_short': len(current_full) <= 10,
                        'matches_Student_digits': bool(re.match(r'^Student\s*\d+$', current_full)),
                        'first_is_just_Student': bool(re.match(r'^Student$', current_first))
                    }
                    
                    is_default_name = any(is_default_name_checks.values())
                    
                    print(f"Extracted: '{full_name}' -> first='{new_first_name}', last='{new_last_name}'")
                    print(f"Is default name: {is_default_name}")
                    
                    if is_default_name:
                        result_first = new_first_name
                        result_last = new_last_name
                        print(f"WOULD UPDATE to: first='{result_first}', last='{result_last}'")
                    else:
                        result_first = current_first
                        result_last = current_last
                        print(f"WOULD NOT UPDATE, keeping: first='{result_first}', last='{result_last}'")
                    
                    # Check against expected result
                    expected = scenario["expected_result"]
                    if result_first == expected["first_name"] and result_last == expected["last_name"]:
                        print("✅ CORRECT BEHAVIOR")
                    else:
                        print(f"❌ INCORRECT - Expected: first='{expected['first_name']}', last='{expected['last_name']}'")
        else:
            print("No extracted name found")
            
        print()

if __name__ == "__main__":
    test_default_name_patterns()
    test_ai_extraction_scenarios()