import json
import requests
import traceback
from datetime import datetime
from sqlalchemy import text
from flask import current_app

# Import the database instance directly
from app import db

def check_system_logs_table():
    """Check if the system_logs table exists and return its status."""
    try:
        # Use direct database access
        result = db.session.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'system_logs')")).scalar()
        return {
            "exists": bool(result),
            "message": "System logs table exists" if result else "System logs table does not exist"
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        return {
            "exists": False,
            "message": f"Error checking system logs table: {str(e)}",
            "error": str(e),
            "trace": error_trace
        }

def generate_test_webhook_payload():
    """Generate a test webhook payload for VAPI."""
    current_time = datetime.now().isoformat()
    return {
        "call_id": f"test_call_{current_time}",
        "phone_number": "+1234567890",
        "student_name": "Test Student",
        "transcript": "This is a test transcript for VAPI webhook testing.",
        "summary": "Test summary",
        "duration": 60,
        "timestamp": current_time,
        "test": True
    }

def send_test_webhook(base_url=None):
    """Send a test webhook to the VAPI webhook endpoint."""
    try:
        # Get the base URL from the app config if not provided
        if not base_url:
            base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
        
        # Remove trailing slash if present
        if base_url.endswith('/'):
            base_url = base_url[:-1]
            
        webhook_url = f"{base_url}/api/vapi/webhook"
        payload = generate_test_webhook_payload()
        
        # Log the test webhook
        current_app.logger.info(f"Sending test webhook to {webhook_url} with payload: {json.dumps(payload)}")
        
        # Send the webhook
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response": response.text,
            "webhook_url": webhook_url,
            "payload": payload
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        return {
            "success": False,
            "message": f"Error sending test webhook: {str(e)}",
            "error": str(e),
            "trace": error_trace
        }

def check_webhook_logs():
    """Check if webhook logs were created for the test webhook."""
    try:
        # Use direct database access
        result = db.session.execute(
            text("SELECT COUNT(*) FROM system_logs WHERE message LIKE '%test_call%'")
        ).scalar()
        
        return {
            "success": result > 0,
            "count": result,
            "message": f"Found {result} webhook logs" if result > 0 else "No webhook logs found"
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        return {
            "success": False,
            "message": f"Error checking webhook logs: {str(e)}",
            "error": str(e),
            "trace": error_trace
        }

def check_test_student_created():
    """Check if a test student was created from the test webhook."""
    try:
        # Use direct database access
        result = db.session.execute(
            text("SELECT COUNT(*) FROM students WHERE phone_number = '+1234567890'")
        ).scalar()
        
        return {
            "success": result > 0,
            "count": result,
            "message": f"Found {result} test students" if result > 0 else "No test students found"
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        return {
            "success": False,
            "message": f"Error checking test student: {str(e)}",
            "error": str(e),
            "trace": error_trace
        }

def check_test_session_created():
    """Check if a test session was created from the test webhook."""
    try:
        # Use direct database access
        result = db.session.execute(
            text("SELECT COUNT(*) FROM sessions WHERE call_id LIKE '%test_call%'")
        ).scalar()
        
        return {
            "success": result > 0,
            "count": result,
            "message": f"Found {result} test sessions" if result > 0 else "No test sessions found"
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        return {
            "success": False,
            "message": f"Error checking test session: {str(e)}",
            "error": str(e),
            "trace": error_trace
        }

def run_vapi_integration_test(base_url=None):
    """Run a complete VAPI integration test and return the results."""
    results = {
        "system_logs_table": check_system_logs_table(),
        "test_webhook": send_test_webhook(base_url),
        "webhook_logs": None,
        "test_student": None,
        "test_session": None,
        "overall_success": False
    }
    
    # Only check for logs, student, and session if the webhook was sent successfully
    if results["test_webhook"]["success"]:
        results["webhook_logs"] = check_webhook_logs()
        results["test_student"] = check_test_student_created()
        results["test_session"] = check_test_session_created()
        
        # Overall success is true if all checks passed
        results["overall_success"] = (
            results["system_logs_table"]["exists"] and
            results["webhook_logs"]["success"] and
            results["test_student"]["success"] and
            results["test_session"]["success"]
        )
    
    return results