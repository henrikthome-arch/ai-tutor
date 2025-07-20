#!/usr/bin/env python3
"""
Test the entire VAPI webhook flow
1. Verify database connection and tables
2. Send a test webhook
3. Verify that the webhook created entries in the database
"""

import os
import sys
import time
import subprocess
import json
import requests
from datetime import datetime

def run_command(command):
    """Run a command and return the output"""
    print(f"🔄 Running command: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                               capture_output=True, text=True)
        print(f"✅ Command completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        print(f"Error output: {e.stderr}")
        return None

def send_webhook(url, payload, vapi_secret=None):
    """Send a webhook request to the specified URL with the given payload"""
    # Convert payload to JSON string
    payload_str = json.dumps(payload)
    
    # Set up headers
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'VAPI-Webhook-Test/1.0',
    }
    
    # Add signature if secret is provided
    if vapi_secret:
        import hmac
        import hashlib
        signature = hmac.new(
            vapi_secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        headers['X-Vapi-Signature'] = signature
        print(f"🔐 Added signature: {signature[:10]}...")
    
    # Send the request
    print(f"📤 Sending webhook to {url}")
    print(f"📦 Payload: {payload_str[:200]}...")
    
    try:
        response = requests.post(url, data=payload_str, headers=headers)
        
        # Print response details
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response body: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error sending webhook: {e}")
        return False

def main():
    """Main function"""
    print("🔍 Starting VAPI webhook flow test")
    
    # Get webhook URL from environment variable or use default
    webhook_url = os.environ.get('WEBHOOK_URL', 'http://localhost:5000/vapi/webhook')
    
    # Get VAPI secret from environment variable
    vapi_secret = os.environ.get('VAPI_SECRET', '')
    
    # Step 1: Verify database connection and tables
    print("\n📊 Step 1: Verifying database connection and tables")
    db_result = run_command("python verify_database.py")
    if not db_result:
        print("❌ Database verification failed. Aborting test.")
        sys.exit(1)
    
    # Step 2: Check system_logs table
    print("\n📝 Step 2: Checking system_logs table before webhook")
    logs_before = run_command("python check_system_logs.py")
    if not logs_before:
        print("❌ System logs check failed. Aborting test.")
        sys.exit(1)
    
    # Step 3: Send a test webhook
    print("\n📞 Step 3: Sending test webhook")
    # Generate a unique call ID for this test
    call_id = f"test_call_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create a custom payload with the unique call ID
    payload = {
        "message": {
            "type": "end-of-call-report",
            "call": {
                "id": call_id,
                "customer": {
                    "number": "+15555555555"
                }
            },
            "phoneNumber": "+15555555555",
            "durationSeconds": 120,
            "transcript": {
                "user": "Hello, I'm a student in grade 5 and I need help with math. My name is Test Student and I like science.",
                "assistant": "Hi Test Student! I'd be happy to help you with math. I see you're in grade 5 and you like science. That's great! What specific math topic are you working on?"
            }
        }
    }
    
    # Send the webhook
    webhook_success = send_webhook(webhook_url, payload, vapi_secret)
    if not webhook_success:
        print("❌ Webhook sending failed. Aborting test.")
        sys.exit(1)
    
    # Step 4: Wait for processing
    print("\n⏱️ Step 4: Waiting for webhook processing (5 seconds)")
    time.sleep(5)
    
    # Step 5: Check system_logs table after webhook
    print("\n📝 Step 5: Checking system_logs table after webhook")
    logs_after = run_command("python check_system_logs.py")
    if not logs_after:
        print("❌ System logs check failed after webhook.")
        sys.exit(1)
    
    # Step 6: Check for student and session creation
    print("\n👤 Step 6: Checking for student and session creation")
    # Run a SQL query to check if a student was created with the test phone number
    check_student_cmd = f"""python -c "
import os
from sqlalchemy import create_engine, text
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'): db_url = db_url.replace('postgres://', 'postgresql://', 1)
engine = create_engine(db_url)
with engine.connect() as conn:
    result = conn.execute(text(\\"SELECT * FROM students WHERE phone_number = '+15555555555'\\")).fetchall()
    print(f'Found {len(result)} students with test phone number')
    for row in result:
        print(f'  - Student ID: {row.id}, Name: {row.first_name} {row.last_name}')
"
"""
    student_result = run_command(check_student_cmd)
    
    # Run a SQL query to check if a session was created with the test call ID
    check_session_cmd = f"""python -c "
import os
from sqlalchemy import create_engine, text
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'): db_url = db_url.replace('postgres://', 'postgresql://', 1)
engine = create_engine(db_url)
with engine.connect() as conn:
    result = conn.execute(text(\\"SELECT * FROM sessions WHERE call_id = '{call_id}'\\")).fetchall()
    print(f'Found {len(result)} sessions with test call ID')
    for row in result:
        print(f'  - Session ID: {row.id}, Student ID: {row.student_id}, Duration: {row.duration}')
"
"""
    session_result = run_command(check_session_cmd)
    
    # Step 7: Check for webhook logs
    print("\n📝 Step 7: Checking for webhook logs")
    check_webhook_logs_cmd = f"""python -c "
import os
from sqlalchemy import create_engine, text
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'): db_url = db_url.replace('postgres://', 'postgresql://', 1)
engine = create_engine(db_url)
with engine.connect() as conn:
    result = conn.execute(text(\\"SELECT * FROM system_logs WHERE category = 'WEBHOOK' AND message LIKE '%{call_id}%' ORDER BY timestamp DESC LIMIT 5\\")).fetchall()
    print(f'Found {len(result)} webhook logs for test call ID')
    for row in result:
        print(f'  - [{row.level}] {row.timestamp} {row.category}: {row.message[:50]}...')
"
"""
    webhook_logs_result = run_command(check_webhook_logs_cmd)
    
    # Print summary
    print("\n📋 Test Summary:")
    print(f"✅ Database verification: {'Successful' if db_result else 'Failed'}")
    print(f"✅ System logs check before webhook: {'Successful' if logs_before else 'Failed'}")
    print(f"✅ Webhook sending: {'Successful' if webhook_success else 'Failed'}")
    print(f"✅ System logs check after webhook: {'Successful' if logs_after else 'Failed'}")
    print(f"✅ Student creation check: {'Successful' if student_result else 'Failed'}")
    print(f"✅ Session creation check: {'Successful' if session_result else 'Failed'}")
    print(f"✅ Webhook logs check: {'Successful' if webhook_logs_result else 'Failed'}")
    
    # Overall result
    if all([db_result, logs_before, webhook_success, logs_after, student_result, session_result, webhook_logs_result]):
        print("\n🎉 VAPI webhook flow test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ VAPI webhook flow test failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()