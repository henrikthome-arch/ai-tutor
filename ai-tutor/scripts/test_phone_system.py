#!/usr/bin/env python3
"""
Test script for phone-based student identification system
"""

import json
import requests
import time

def test_phone_system():
    """Test the phone-based identification system"""
    
    base_url = "http://localhost:3000"
    
    print("🧪 TESTING PHONE-BASED STUDENT IDENTIFICATION SYSTEM")
    print("=" * 60)
    
    # Test 1: Add phone mapping for Emma
    print("\n📞 TEST 1: Adding phone mapping for Emma Smith")
    
    # We'll add this directly to the phone mapping file
    phone_mapping = {
        "phone_to_student": {
            "+12345678901": "emma_smith",
            "+19876543210": "jane_doe"
        },
        "last_updated": "2025-01-17T08:00:00Z"
    }
    
    with open('data/phone_mapping.json', 'w') as f:
        json.dump(phone_mapping, f, indent=2)
    
    print("✓ Phone mappings added:")
    print("  +12345678901 → emma_smith")
    print("  +19876543210 → jane_doe")
    
    # Test 2: Check server health
    print("\n🏥 TEST 2: Checking server health")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Server is healthy")
        else:
            print("✗ Server health check failed")
            return
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        print("   Make sure session-enhanced-server.py is running")
        return
    
    # Test 3: Test phone number lookup - existing student
    print("\n📱 TEST 3: Testing phone lookup for existing student")
    try:
        payload = {
            "phone_number": "+12345678901"
        }
        response = requests.post(f"{base_url}/mcp/get-student-context", 
                               json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                student_name = data['data']['profile']['name']
                print(f"✓ Successfully resolved phone +12345678901 → {student_name}")
            else:
                print(f"✗ Request failed: {data}")
        else:
            print(f"✗ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"✗ Phone lookup test failed: {e}")
    
    # Test 4: Test phone number lookup - unknown phone
    print("\n❓ TEST 4: Testing phone lookup for unknown number")
    try:
        payload = {
            "phone_number": "+15551234567"
        }
        response = requests.post(f"{base_url}/mcp/get-student-context", 
                               json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('success') and data.get('error') == 'unknown_phone_number':
                print("✓ Unknown phone number correctly detected")
                print(f"   Action required: {data.get('action_required')}")
            else:
                print(f"✗ Unexpected response for unknown phone: {data}")
        else:
            print(f"✗ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"✗ Unknown phone test failed: {e}")
    
    # Test 5: Test traditional student_id lookup still works
    print("\n🆔 TEST 5: Testing traditional student_id lookup")
    try:
        payload = {
            "student_id": "emma_smith"
        }
        response = requests.post(f"{base_url}/mcp/get-student-context", 
                               json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                student_name = data['data']['profile']['name']
                print(f"✓ Student ID lookup still works: emma_smith → {student_name}")
            else:
                print(f"✗ Student ID lookup failed: {data}")
        else:
            print(f"✗ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"✗ Student ID test failed: {e}")
    
    # Test 6: Check tools manifest includes phone_number parameter
    print("\n🛠️  TEST 6: Checking tools manifest")
    try:
        response = requests.get(f"{base_url}/mcp/tools", timeout=5)
        if response.status_code == 200:
            tools = response.json()
            context_tool = tools['tools'][0]
            properties = context_tool['inputSchema']['properties']
            
            if 'phone_number' in properties:
                print("✓ Tools manifest includes phone_number parameter")
                print(f"   Description: {properties['phone_number']['description']}")
            else:
                print("✗ Tools manifest missing phone_number parameter")
        else:
            print(f"✗ Tools manifest request failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Tools manifest test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 PHONE SYSTEM TESTING COMPLETE")
    print("\nNext steps:")
    print("1. Deploy updated server to Render.com")
    print("2. Configure VAPI to send phone numbers in webhooks")
    print("3. Set up welcome call workflow for new students")
    print("=" * 60)

if __name__ == '__main__':
    test_phone_system()