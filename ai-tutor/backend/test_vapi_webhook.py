#!/usr/bin/env python3
"""
Test script for VAPI webhook integration
Simulates a VAPI webhook call to test the integration
"""

import requests
import json
import sys
import os
import hmac
import hashlib
from datetime import datetime

# Default webhook URL (can be overridden with command line argument)
DEFAULT_WEBHOOK_URL = "http://localhost:5000/vapi/webhook"

# Sample end-of-call-report payload
SAMPLE_PAYLOAD = {
    "message": {
        "type": "end-of-call-report",
        "call": {
            "id": "test_call_" + datetime.now().strftime("%Y%m%d%H%M%S"),
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

def sign_payload(payload_str, secret):
    """Sign the payload with HMAC-SHA256 using the provided secret"""
    if not secret:
        return None
    
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

def send_webhook(url, payload, secret=None):
    """Send a webhook request to the specified URL with the given payload"""
    # Convert payload to JSON string
    payload_str = json.dumps(payload)
    
    # Set up headers
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'VAPI-Webhook-Test/1.0',
    }
    
    # Add signature if secret is provided
    if secret:
        signature = sign_payload(payload_str, secret)
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
        
        return response
    except Exception as e:
        print(f"❌ Error sending webhook: {e}")
        return None

def main():
    """Main function to send a test webhook"""
    # Get webhook URL from command line argument or use default
    webhook_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_WEBHOOK_URL
    
    # Get VAPI secret from environment variable
    vapi_secret = os.environ.get('VAPI_SECRET', '')
    
    # Send the webhook
    response = send_webhook(webhook_url, SAMPLE_PAYLOAD, vapi_secret)
    
    # Check if the webhook was successful
    if response and response.status_code == 200:
        print("✅ Webhook sent successfully!")
        sys.exit(0)
    else:
        print("❌ Webhook failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()