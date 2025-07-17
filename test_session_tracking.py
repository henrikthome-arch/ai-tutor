#!/usr/bin/env python3
"""
Test script for session tracking functionality
"""

import requests
import json
import time
from datetime import datetime

def test_session_tracking():
    """Test the enhanced session tracking system"""
    
    base_url = "http://localhost:3000"
    
    print("🧪 TESTING SESSION TRACKING SYSTEM")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Server healthy: {data['server']}")
            print(f"   ✓ Session tracking: {data.get('session_tracking', 'unknown')}")
            print(f"   ✓ Active sessions: {data.get('active_sessions', 0)}")
        else:
            print(f"   ✗ Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"   ✗ Could not connect to server: {e}")
        print("   Make sure the enhanced server is running:")
        print("   python session-enhanced-server.py")
        return
    
    # Test 2: MCP function call (creates session)
    print("\n2. Testing MCP function call (session creation)...")
    try:
        mcp_data = {"student_id": "emma_smith"}
        response = requests.post(f"{base_url}/mcp/get-student-context", json=mcp_data)
        
        if response.status_code == 200:
            print("   ✓ MCP call successful")
            print("   ✓ Session should be created automatically")
        else:
            print(f"   ✗ MCP call failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ MCP call error: {e}")
    
    # Test 3: Check active sessions
    print("\n3. Checking active sessions...")
    try:
        response = requests.get(f"{base_url}/sessions/active")
        if response.status_code == 200:
            data = response.json()
            session_count = data['data']['count']
            print(f"   ✓ Active sessions: {session_count}")
            
            if session_count > 0:
                session = data['data']['sessions'][0]
                session_id = session['session_id']
                print(f"   ✓ Session ID: {session_id}")
                print(f"   ✓ Student: {session['student_id']}")
                print(f"   ✓ MCP interactions: {len(session['mcp_interactions'])}")
                return session_id
        else:
            print(f"   ✗ Failed to get active sessions: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Active sessions error: {e}")
    
    return None

def test_vapi_webhook(session_id=None):
    """Test VAPI webhook integration"""
    
    base_url = "http://localhost:3000"
    
    print("\n4. Testing VAPI webhook integration...")
    
    # Simulate VAPI webhook data
    vapi_data = {
        "call_id": "test_call_123",
        "started_at": datetime.utcnow().isoformat() + "Z",
        "ended_at": datetime.utcnow().isoformat() + "Z",
        "duration_seconds": 900,  # 15 minutes
        "transcript": "Student: Hi, I need help with fractions. AI: I'd be happy to help you with fractions! Let me get your information first. Student: My name is Emma. AI: Great Emma! Let's start with basic fractions. A fraction represents a part of a whole...",
        "cost": 0.25,
        "ended_reason": "hangup",
        "metadata": {
            "student_id": "emma_smith"
        }
    }
    
    try:
        response = requests.post(f"{base_url}/webhook/vapi/session-complete", json=vapi_data)
        
        if response.status_code == 200:
            data = response.json()
            print("   ✓ VAPI webhook processed successfully")
            print(f"   ✓ Session ID: {data.get('session_id', 'unknown')}")
            
            # Check if session was updated with transcript
            if data.get('session_id'):
                session_response = requests.get(f"{base_url}/sessions/{data['session_id']}")
                if session_response.status_code == 200:
                    session_data = session_response.json()['data']
                    print(f"   ✓ Transcript added: {len(session_data['conversation']['transcript'])} characters")
                    print(f"   ✓ Word count: {session_data['conversation']['word_count']}")
                    print(f"   ✓ Platform: {session_data['platform']}")
                    print(f"   ✓ Status: {session_data['status']}")
        else:
            print(f"   ✗ VAPI webhook failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ✗ VAPI webhook error: {e}")

def test_session_timeout():
    """Test session timeout detection"""
    
    base_url = "http://localhost:3000"
    
    print("\n5. Testing session timeout detection...")
    print("   Making MCP call...")
    
    # Make first call
    mcp_data = {"student_id": "emma_smith"}
    response1 = requests.post(f"{base_url}/mcp/get-student-context", json=mcp_data)
    
    if response1.status_code == 200:
        print("   ✓ First call successful")
        
        # Wait a moment (simulate normal session activity)
        print("   Waiting 2 seconds (normal activity)...")
        time.sleep(2)
        
        # Make second call
        response2 = requests.post(f"{base_url}/mcp/get-student-context", json=mcp_data)
        
        if response2.status_code == 200:
            print("   ✓ Second call successful (should be same session)")
            
            # Check session count
            sessions_response = requests.get(f"{base_url}/sessions/active")
            if sessions_response.status_code == 200:
                session_count = sessions_response.json()['data']['count']
                print(f"   ✓ Active sessions: {session_count} (should be 1)")
                
                if session_count == 1:
                    session = sessions_response.json()['data']['sessions'][0]
                    interaction_count = len(session['mcp_interactions'])
                    print(f"   ✓ MCP interactions in session: {interaction_count} (should be 2)")

def test_generic_webhook():
    """Test generic webhook endpoint"""
    
    base_url = "http://localhost:3000"
    
    print("\n6. Testing generic webhook endpoint...")
    
    # Test with VAPI platform
    webhook_data = {
        "platform": "vapi",
        "call_id": "generic_test_456",
        "started_at": datetime.utcnow().isoformat() + "Z",
        "ended_at": datetime.utcnow().isoformat() + "Z",
        "transcript": "This is a test conversation via generic webhook.",
        "metadata": {
            "student_id": "emma_smith"
        }
    }
    
    try:
        response = requests.post(f"{base_url}/webhook/session-data", json=webhook_data)
        
        if response.status_code == 200:
            print("   ✓ Generic webhook processed successfully")
        else:
            print(f"   ✗ Generic webhook failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Generic webhook error: {e}")

def main():
    """Run all tests"""
    
    print("🚀 SESSION TRACKING TEST SUITE")
    print("=" * 50)
    print("Make sure the enhanced server is running:")
    print("python session-enhanced-server.py")
    print("=" * 50)
    
    # Run tests
    session_id = test_session_tracking()
    test_vapi_webhook(session_id)
    test_session_timeout()
    test_generic_webhook()
    
    print("\n" + "=" * 50)
    print("🎉 TEST SUITE COMPLETED")
    print("=" * 50)
    print("\nTo view session data:")
    print("1. Active sessions: GET http://localhost:3000/sessions/active")
    print("2. Specific session: GET http://localhost:3000/sessions/{session_id}")
    print("3. Check data/students/emma_smith/sessions/ for saved session files")

if __name__ == '__main__':
    main()