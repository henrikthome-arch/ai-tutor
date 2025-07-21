"""
API Blueprint
RESTful API endpoints for the AI Tutor system
"""

import os
import json
import hmac
import hashlib
import asyncio
from datetime import datetime
from typing import Dict, Any
from flask import Blueprint, request, jsonify, current_app
from flask import session

# Import system components
from backend.system_logger import system_logger, log_admin_action, log_webhook, log_ai_analysis, log_error, log_system
from backend.vapi.client import vapi_client

# Import auth components
from app.auth.decorators import token_or_session_auth, require_token_scope

# Import AI components
try:
    from backend.ai.session_processor import session_processor
    from backend.ai.providers import provider_manager
    AI_POC_AVAILABLE = True
except ImportError as e:
    AI_POC_AVAILABLE = False
    print(f"⚠️  AI POC not available in API: {e}")

# Import services and repositories
from backend.app.services.student_service import StudentService
from backend.app.services.session_service import SessionService
from backend.app.services.ai_service import AIService

# Import the blueprint from parent module
from app.api import bp as api

# Initialize services
student_service = StudentService()
session_service = SessionService()
ai_service = AIService()

# Authentication helper (kept for backward compatibility)
def check_auth():
    """Check if user is authenticated"""
    return session.get('admin_logged_in', False)

# API routes for AJAX requests
@api.route('/admin/api/stats')
@token_or_session_auth(required_scope='admin:read')
def api_stats():
    return jsonify(student_service.get_system_stats())

@api.route('/admin/api/ai-stats')
@token_or_session_auth(required_scope='admin:read')
def api_ai_stats():
    """Get AI processing statistics"""
    if not AI_POC_AVAILABLE:
        return jsonify({'error': 'AI POC not available'}), 503
    
    return jsonify(session_processor.get_processing_stats())

@api.route('/admin/api/task/<task_id>')
@token_or_session_auth(required_scope='tasks:read')
def api_task_status(task_id):
    """Get the status of a Celery task"""
    task_status = ai_service.get_task_status(task_id)
    return jsonify(task_status)

# VAPI Webhook Routes
def verify_vapi_signature(payload_body, signature, headers_info):
    """Verify VAPI webhook signature using HMAC"""
    # Get VAPI secret from app config
    vapi_secret = current_app.config['VAPI_SECRET']
    
    # If VAPI secret is not configured, allow webhooks but log warning
    if vapi_secret == 'your_vapi_secret_here':
        log_webhook('SECURITY_WARNING', 'VAPI webhook processed without signature verification - secret not configured',
                   ip_address=request.remote_addr,
                   signature_provided=bool(signature),
                   payload_size=len(payload_body),
                   headers_info=headers_info)
        return True
    
    # If no signature provided, allow but log warning (VAPI may not be configured to send signatures)
    if not signature:
        log_webhook('SECURITY_WARNING', 'VAPI webhook processed without signature - VAPI may not be configured to send signatures',
                   ip_address=request.remote_addr,
                   signature_provided=False,
                   payload_size=len(payload_body),
                   headers_info=headers_info)
        return True
    
    try:
        expected_signature = hmac.new(
            vapi_secret.encode('utf-8'),
            payload_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        log_error('WEBHOOK', f"Error verifying VAPI signature: {str(e)}", e,
                 signature_length=len(signature) if signature else 0,
                 payload_size=len(payload_body))
        return False

@api.route('/vapi/webhook', methods=['POST'])
def vapi_webhook():
    """Handle VAPI webhook events - simplified API-first approach"""
    try:
        # Get raw payload for signature verification
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-Vapi-Signature', '')
        
        # Get headers info for debugging
        vapi_headers = {k: v for k, v in request.headers.items() if k.lower().startswith('x-vapi')}
        headers_info = {
            'vapi_headers': vapi_headers,
            'content_type': request.headers.get('Content-Type', ''),
            'user_agent': request.headers.get('User-Agent', ''),
            'all_header_names': list(request.headers.keys())
        }
        
        # Verify signature
        if not verify_vapi_signature(payload, signature, headers_info):
            log_webhook('SECURITY_FAILURE', 'VAPI webhook signature verification failed',
                       ip_address=request.remote_addr,
                       signature_provided=bool(signature),
                       payload_size=len(payload))
            print(f"🚨 VAPI webhook signature verification failed")
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse the webhook data
        data = request.get_json()
        if not data:
            log_webhook('INVALID_PAYLOAD', 'VAPI webhook received empty or invalid payload',
                       ip_address=request.remote_addr,
                       payload_size=len(payload))
            return jsonify({'error': 'Invalid payload'}), 400
        
        message = data.get('message', {})
        message_type = message.get('type')
        
        log_webhook(message_type or 'unknown-event', f"VAPI webhook received: {message_type}",
                   ip_address=request.remote_addr,
                   call_id=message.get('call', {}).get('id') if isinstance(message, dict) else None,
                   payload_size=len(payload))
        print(f"📞 VAPI webhook received: {message_type}")
        
        # Only handle end-of-call-report - ignore all other events
        if message_type == 'end-of-call-report':
            handle_end_of_call_api_driven(message)
        else:
            # Log but ignore other events
            log_webhook('ignored-event', f"Ignored VAPI event: {message_type}",
                       call_id=message.get('call', {}).get('id') if isinstance(message, dict) else None)
            print(f"📝 Ignored VAPI event: {message_type}")
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        log_error('WEBHOOK', f"VAPI webhook error: {str(e)}", e,
                 ip_address=request.remote_addr,
                 payload_size=len(payload) if 'payload' in locals() else 0)
        print(f"❌ VAPI webhook error: {e}")
        return jsonify({'error': str(e)}), 500

def handle_end_of_call_api_driven(message: Dict[Any, Any]) -> None:
    """Handle end-of-call using API-first approach"""
    try:
        # Extract basic info from webhook
        call_id = None  # Initialize call_id for robust error logging
        call_id = message.get('call', {}).get('id')
        phone_number = message.get('phoneNumber')  # Direct from webhook
        student_id = None  # Initialize student_id to prevent UnboundLocalError
        
        if not call_id:
            log_error('WEBHOOK', 'No call_id in end-of-call-report', ValueError())
            return
        
        log_webhook('end-of-call-report', f"Processing call {call_id} via API",
                   call_id=call_id, phone=phone_number)
        print(f"📞 Processing call {call_id} via API")
        
        # Check if VAPI client is configured
        if not vapi_client.is_configured():
            log_error('WEBHOOK', 'VAPI API client not configured - falling back to webhook data',
                     ValueError('VAPI_API_KEY missing'),
                     call_id=call_id)
            # Fallback to webhook data processing
            handle_end_of_call_webhook_fallback(message)
            return
        
        # Fetch complete call data from API
        call_data = vapi_client.get_call_details(call_id)
        
        if not call_data:
            log_error('WEBHOOK', f'Failed to fetch call data for {call_id} - falling back to webhook',
                     ValueError('API call failed'),
                     call_id=call_id)
            # Fallback to webhook data processing
            handle_end_of_call_webhook_fallback(message)
            return
        
        # Extract authoritative data from API response
        metadata = vapi_client.extract_call_metadata(call_data)
        transcript = vapi_client.get_call_transcript(call_id)
        
        customer_phone = metadata.get('customer_phone') or phone_number
        duration = metadata.get('duration_seconds', 0)
        
        log_webhook('api-success', f"Successfully processed call {call_id} via API",
                   call_id=call_id,
                   phone=customer_phone,
                   duration_seconds=duration,
                   transcript_length=len(transcript) if transcript else 0)
        
        print(f"📝 API data - Call {call_id}: {duration}s duration")
        print(f"📞 Phone: {customer_phone}")
        print(f"📄 Transcript: {len(transcript) if transcript else 0} chars")
        
        # Student identification and session saving
        student_id = identify_or_create_student(customer_phone, call_id)
        save_api_driven_session(call_id, student_id, customer_phone,
                               duration, transcript, call_data)
        
        # Trigger AI analysis
        # Always analyze transcript for profile extraction regardless of length
        # Only skip if transcript is extremely short or empty
        if student_id and transcript and len(transcript) > 100 and AI_POC_AVAILABLE:
            trigger_ai_analysis_async(student_id, transcript, call_id)
        elif transcript and len(transcript) <= 100:
            log_ai_analysis("Skipping AI analysis for extremely short transcript",
                           call_id=call_id, student_id=student_id,
                           duration_seconds=duration, transcript_length=len(transcript))
            
    except Exception as e:
        log_error('WEBHOOK', f"Error in API-driven end-of-call handler", e,
                 call_id=call_id if 'call_id' in locals() else None)
        print(f"❌ API-driven handler error: {e}")

def save_vapi_session(call_id, student_id, phone, duration, user_transcript, assistant_transcript, full_message):
    """Save VAPI session data to student directory"""
    try:
        # Create student directory if it doesn't exist
        student_dir = f'data/students/{student_id}'
        sessions_dir = f'{student_dir}/sessions'
        os.makedirs(sessions_dir, exist_ok=True)
        
        # Generate session filename with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        session_file = f'{sessions_dir}/{timestamp}_vapi_session.json'
        transcript_file = f'{sessions_dir}/{timestamp}_vapi_transcript.txt'
        
        # Create session data
        session_data = {
            'call_id': call_id,
            'student_id': student_id,
            'phone_number': phone,
            'start_time': datetime.now().isoformat(),
            'duration_seconds': duration,
            'session_type': 'vapi_call',
            'transcript_file': f'{timestamp}_vapi_transcript.txt',
            'user_transcript_length': len(user_transcript),
            'assistant_transcript_length': len(assistant_transcript),
            'vapi_data': full_message  # Store complete VAPI response
        }
        
        # Save session metadata
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        # Save combined transcript
        combined_transcript = f"=== VAPI Call Transcript ===\n"
        combined_transcript += f"Call ID: {call_id}\n"
        combined_transcript += f"Duration: {duration} seconds\n"
        combined_transcript += f"Phone: {phone}\n"
        combined_transcript += f"Timestamp: {datetime.now().isoformat()}\n\n"
        combined_transcript += f"=== User Transcript ===\n{user_transcript}\n\n"
        combined_transcript += f"=== Assistant Transcript ===\n{assistant_transcript}\n"
        
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(combined_transcript)
        
        # Analyze transcript and update student profile
        if user_transcript:
            try:
                from backend.transcript_analyzer import TranscriptAnalyzer
                analyzer = TranscriptAnalyzer()
                # Use only the user transcript for profile extraction
                extracted_info = analyzer.analyze_transcript(user_transcript)
                if extracted_info:
                    analyzer.update_student_profile(student_id, extracted_info)
                    log_webhook('profile-updated', f"Updated student profile from webhook session",
                               call_id=call_id, student_id=student_id,
                               extracted_info=extracted_info)
                    print(f"👤 Updated profile for student {student_id} with extracted information")
            except Exception as e:
                log_error('TRANSCRIPT_ANALYSIS', f"Error analyzing webhook session transcript", e,
                         call_id=call_id, student_id=student_id)
                print(f"⚠️ Error analyzing webhook session transcript: {e}")
        
        print(f"💾 Saved VAPI session: {session_file}")
        
    except Exception as e:
        print(f"❌ Error saving VAPI session: {e}")

def normalize_phone_number(phone_number: str) -> str:
    """Normalize phone number format to always include + and country code."""
    if not phone_number:
        return ""
        
    # Remove all non-digits
    digits_only = ''.join(filter(str.isdigit, phone_number))
    
    if not digits_only:
        return ""

    # Handle different formats to ensure a consistent `+<country_code><number>` format
    if len(digits_only) == 10:
        # Assumes a 10-digit number is a US number, adds +1
        return f"+1{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        # Assumes an 11-digit number starting with 1 is a US number
        return f"+{digits_only}"
    else:
        # For other numbers, just ensure it starts with a +
        return f"+{digits_only}"

def identify_or_create_student(phone_number: str, call_id: str) -> str:
    """Identify existing student or create new one with better logic"""
    if not phone_number:
        return f"unknown_caller_{call_id}"
    
    # Clean and normalize phone number
    clean_phone = normalize_phone_number(phone_number)
    
    # Log the exact lookup for debugging
    log_webhook('phone-lookup', f"Looking up student by phone: {clean_phone}",
               call_id=call_id, phone=clean_phone, original_phone=phone_number)
    
    # Get student by phone
    student_id = student_service.get_student_by_phone(clean_phone)
    if student_id:
        log_webhook('student-identified', f"Found student {student_id}",
                   call_id=call_id, student_id=student_id, phone=clean_phone)
        return student_id
    
    # Create new student if not found
    log_webhook('student-not-found', f"No student found for phone: {clean_phone}",
               call_id=call_id, phone=clean_phone)
    
    # Create new student
    new_student_id = create_student_from_call(clean_phone, call_id)
    log_webhook('student-created', f"Created new student {new_student_id}",
               call_id=call_id, student_id=new_student_id, phone=clean_phone)
    
    return new_student_id

def create_student_from_call(phone: str, call_id: str) -> str:
    """Create a new student from phone call data"""
    # Ensure phone is normalized for consistent lookup and storage
    normalized_phone = normalize_phone_number(phone)
    
    # Use last 4 digits of normalized phone for ID creation
    phone_suffix = normalized_phone[-4:] if normalized_phone else ""
    student_id = f"student_{phone_suffix}" if phone else f"unknown_{call_id[-6:]}"
    
    # Create student with basic info
    return student_service.create_student_from_call(
        student_id=student_id,
        phone=normalized_phone,
        call_id=call_id
    )

def save_api_driven_session(call_id: str, student_id: str, phone: str,
                           duration: int, transcript: str, call_data: Dict[Any, Any]):
    """Save VAPI session data using API-fetched data"""
    try:
        # Create student directory if it doesn't exist
        student_dir = f'data/students/{student_id}'
        sessions_dir = f'{student_dir}/sessions'
        os.makedirs(sessions_dir, exist_ok=True)
        
        # Generate session filename with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        session_file = f'{sessions_dir}/{timestamp}_vapi_session.json'
        transcript_file = f'{sessions_dir}/{timestamp}_vapi_transcript.txt'
        
        # Create session data using API metadata
        metadata = vapi_client.extract_call_metadata(call_data)
        
        # Calculate a more reliable duration based on transcript length if duration is 0
        effective_duration = duration
        if duration == 0 and transcript and len(transcript) > 100:
            # Estimate ~10 seconds per 100 characters as a fallback
            effective_duration = len(transcript) // 10
            log_webhook('duration-estimate', f"Estimated duration from transcript length",
                       call_id=call_id, original_duration=duration,
                       estimated_duration=effective_duration,
                       transcript_length=len(transcript))
            print(f"⏱️ Estimated duration from transcript: {effective_duration}s (original: {duration}s)")
        
        session_data = {
            'call_id': call_id,
            'student_id': student_id,
            'phone_number': phone,
            'start_time': metadata.get('created_at', datetime.now().isoformat()),
            'duration_seconds': effective_duration,  # Use the effective duration
            'original_duration': duration,  # Keep the original for reference
            'session_type': 'vapi_call_api',
            'transcript_file': f'{timestamp}_vapi_transcript.txt',
            'transcript_length': len(transcript) if transcript else 0,
            'data_source': 'vapi_api',
            'call_status': metadata.get('status'),
            'call_cost': metadata.get('cost', 0),
            'has_recording': metadata.get('has_recording', False),
            'recording_url': metadata.get('recording_url'),
            'vapi_metadata': metadata,
            'analysis_summary': metadata.get('analysis_summary', ''),
            'analysis_data': metadata.get('analysis_structured_data', {})
        }
        
        # Save session metadata
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        # Save transcript and analyze regardless of duration
        if transcript:
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            # Always analyze transcript for profile information if there's content
            if len(transcript) > 100:  # Only analyze if there's meaningful content
                try:
                    from backend.transcript_analyzer import TranscriptAnalyzer
                    analyzer = TranscriptAnalyzer()
                    log_webhook('transcript-analysis-start', f"Starting transcript analysis for profile extraction",
                               call_id=call_id, student_id=student_id,
                               transcript_length=len(transcript))
                    print(f"🔍 Analyzing transcript for student {student_id} profile information...")
                    
                    extracted_info = analyzer.analyze_transcript(transcript)
                    if extracted_info:
                        analyzer.update_student_profile(student_id, extracted_info)
                        log_webhook('profile-updated', f"Updated student profile from transcript",
                                   call_id=call_id, student_id=student_id,
                                   extracted_info=extracted_info)
                        print(f"👤 Updated profile for student {student_id} with extracted information: {extracted_info}")
                    else:
                        log_webhook('profile-no-info', f"No profile information extracted from transcript",
                                   call_id=call_id, student_id=student_id)
                        print(f"ℹ️ No profile information extracted from transcript for student {student_id}")
                except Exception as e:
                    log_error('TRANSCRIPT_ANALYSIS', f"Error analyzing transcript", e,
                             call_id=call_id, student_id=student_id)
                    print(f"⚠️ Error analyzing transcript: {e}")
        
        print(f"💾 Saved API-driven session: {session_file}")
        log_webhook('session-saved', f"Saved session for call {call_id}",
                   call_id=call_id,
                   student_id=student_id,
                   session_file=session_file,
                   transcript_length=len(transcript) if transcript else 0)
        
    except Exception as e:
        log_error('WEBHOOK', f"Error saving API-driven session for call {call_id}", e,
                 call_id=call_id, student_id=student_id)
        print(f"❌ Error saving API-driven session: {e}")

def handle_end_of_call_webhook_fallback(message: Dict[Any, Any]) -> None:
    """Fallback to webhook-based processing when API is unavailable"""
    call_id = 'unknown' # Initialize call_id for robust error logging
    try:
        log_webhook('webhook-fallback', "Using webhook fallback processing")
        print("📱 Using webhook fallback processing")

        # Robustness: Ensure message is a dictionary
        if not isinstance(message, dict):
            log_error('WEBHOOK', 'Fallback received non-dict message', TypeError(f"Expected dict, got {type(message).__name__}"),
                      message_type=type(message).__name__)
            return

        # Extract data from webhook message (old method)
        call_info = message.get('call', {})
        call_id = call_info.get('id')
        customer_phone = call_info.get('customer', {}).get('number') or message.get('phoneNumber')
        duration = message.get('durationSeconds', 0)
        
        # Get transcript from webhook
        transcript_data = message.get('transcript', {})
        user_transcript = ""
        assistant_transcript = ""

        # Handle both string and dict transcript formats
        if isinstance(transcript_data, dict):
            user_transcript = transcript_data.get('user', '')
            assistant_transcript = transcript_data.get('assistant', '')
        elif isinstance(transcript_data, str):
            user_transcript = transcript_data # Assume the whole string is the user's part

        # Identify student, ensuring a valid student_id is always returned or created
        student_id = identify_or_create_student(customer_phone, call_id)
        
        combined_transcript = user_transcript + "\n" + assistant_transcript
        
        # Calculate a more reliable duration based on transcript length if duration is 0
        effective_duration = duration
        if duration == 0 and combined_transcript and len(combined_transcript) > 100:
            # Estimate ~10 seconds per 100 characters as a fallback
            effective_duration = len(combined_transcript) // 10
            log_webhook('duration-estimate', f"Estimated duration from webhook transcript length",
                       call_id=call_id, original_duration=duration,
                       estimated_duration=effective_duration,
                       transcript_length=len(combined_transcript))
            print(f"⏱️ Estimated duration from webhook transcript: {effective_duration}s (original: {duration}s)")
        
        # Save using old method with the effective duration
        save_vapi_session(call_id, student_id, customer_phone, effective_duration,
                         user_transcript, assistant_transcript, message)
        
        # Always analyze transcript for profile information if there's content
        if student_id and combined_transcript.strip() and len(combined_transcript) > 100:
            try:
                from backend.transcript_analyzer import TranscriptAnalyzer
                analyzer = TranscriptAnalyzer()
                log_webhook('transcript-analysis-start', f"Starting webhook transcript analysis for profile extraction",
                           call_id=call_id, student_id=student_id,
                           transcript_length=len(combined_transcript))
                print(f"🔍 Analyzing webhook transcript for student {student_id} profile information...")
                
                extracted_info = analyzer.analyze_transcript(combined_transcript)
                if extracted_info:
                    analyzer.update_student_profile(student_id, extracted_info)
                    log_webhook('profile-updated', f"Updated student profile from webhook transcript",
                               call_id=call_id, student_id=student_id,
                               extracted_info=extracted_info)
                    print(f"👤 Updated profile for student {student_id} with extracted information: {extracted_info}")
                else:
                    log_webhook('profile-no-info', f"No profile information extracted from webhook transcript",
                               call_id=call_id, student_id=student_id)
                    print(f"ℹ️ No profile information extracted from webhook transcript for student {student_id}")
            except Exception as e:
                log_error('TRANSCRIPT_ANALYSIS', f"Error analyzing webhook transcript", e,
                         call_id=call_id, student_id=student_id)
                print(f"⚠️ Error analyzing webhook transcript: {e}")
        
        # Always analyze transcript for profile extraction regardless of length
        # Only skip if transcript is extremely short or empty
        if student_id and combined_transcript.strip() and len(combined_transcript) > 100 and AI_POC_AVAILABLE:
            trigger_ai_analysis_async(student_id, combined_transcript, call_id)
        elif combined_transcript.strip() and len(combined_transcript) <= 100:
            log_ai_analysis("Skipping AI analysis for extremely short webhook transcript",
                           call_id=call_id, student_id=student_id,
                           duration_seconds=duration, transcript_length=len(combined_transcript))
            
    except Exception as e:
        log_error('WEBHOOK', f"Error in webhook fallback processing", e,
                 call_id=call_id if 'call_id' in locals() else 'unknown')
        print(f"❌ Webhook fallback error: {e}")

def trigger_ai_analysis_async(student_id, transcript, call_id):
    """Trigger AI analysis for VAPI transcript using Celery tasks"""
    if not AI_POC_AVAILABLE:
        log_ai_analysis("AI POC not available for analysis",
                       call_id=call_id,
                       student_id=student_id,
                       level='WARNING')
        return
    
    try:
        log_ai_analysis("Starting AI analysis for VAPI transcript using Celery",
                       call_id=call_id,
                       student_id=student_id,
                       transcript_length=len(transcript))
        
        # Get student context
        student_data = student_service.get_student_data(student_id)
        student_context = {}
        
        if student_data and student_data.get('profile'):
            profile = student_data['profile']
            student_context = {
                'name': profile.get('name', 'Unknown'),
                'age': profile.get('age', 'Unknown'),
                'grade': profile.get('grade', 'Unknown'),
                'curriculum': profile.get('curriculum', 'Unknown'),
                'primary_interests': profile.get('interests', 'Unknown'),
                'learning_style': profile.get('learning_style', 'Unknown'),
                'motivational_triggers': profile.get('motivational_triggers', 'Unknown')
            }
        else:
            student_context = {
                'name': student_id,
                'age': 'Unknown',
                'grade': 'Unknown',
                'curriculum': 'Unknown',
                'primary_interests': 'Unknown',
                'learning_style': 'Unknown',
                'motivational_triggers': 'Unknown'
            }
        
        # Construct model parameters
        model_params = {
            'student_context': student_context,
            'call_id': call_id
        }
        
        # Use the AIService to process the transcript asynchronously
        result = ai_service.analyze_transcript(transcript, session_id=call_id, async_mode=True)
        
        log_ai_analysis("AI analysis task queued successfully",
                       call_id=call_id,
                       student_id=student_id,
                       task_id=result.get('task_id'))
        print(f"✅ AI analysis task queued for call {call_id}: {result.get('task_id')}")
        
    except Exception as e:
        log_error('AI_ANALYSIS', f"Error triggering AI analysis for call {call_id}", e,
                 call_id=call_id,
                 student_id=student_id)
        print(f"❌ Error triggering AI analysis: {e}")

# API routes for debugging and testing
@api.route('/admin/api/logs')
@token_or_session_auth(required_scope='logs:read')
def api_logs():
    """Get system logs for debugging and testing"""
    try:
        # Get query parameters
        date = request.args.get('date')
        level = request.args.get('level')
        limit = request.args.get('limit', 100, type=int)
        
        # Get logs from system_logger
        logs = system_logger.get_logs(date=date, level=level, limit=limit)
        
        return jsonify({
            'status': 'success',
            'count': len(logs),
            'logs': logs
        })
    except Exception as e:
        log_error('API', f"Error retrieving logs: {str(e)}", e)
        return jsonify({
            'status': 'error',
            'message': f"Error retrieving logs: {str(e)}"
        }), 500

@api.route('/admin/api/logs/sessions')
@token_or_session_auth(required_scope='logs:read')
def api_session_logs():
    """Get session logs for debugging and testing"""
    try:
        # Get query parameters
        student_id = request.args.get('student_id')
        limit = request.args.get('limit', 10, type=int)
        
        # Get session logs
        sessions = session_service.get_recent_sessions(student_id=student_id, limit=limit)
        
        return jsonify({
            'status': 'success',
            'count': len(sessions),
            'sessions': sessions
        })
    except Exception as e:
        log_error('API', f"Error retrieving session logs: {str(e)}", e)
        return jsonify({
            'status': 'error',
            'message': f"Error retrieving session logs: {str(e)}"
        }), 500

# Token verification API endpoint
@api.route('/admin/api/verify-token')
@token_or_session_auth(required_scope='api:read')
def verify_token():
    """Verify token validity and return token information"""
    try:
        # If we reach here, the token is valid (decorator validates it)
        return jsonify({
            'status': 'valid',
            'message': 'Token is valid and active',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        log_error('API', f"Error verifying token: {str(e)}", e)
        return jsonify({
            'status': 'error',
            'message': f"Error verifying token: {str(e)}"
        }), 500

# Test transcript analysis endpoint
@api.route('/admin/api/test-transcript-analysis', methods=['POST'])
@token_or_session_auth(required_scope='api:read')
def test_transcript_analysis():
    """Test transcript analysis with sample data"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        transcript = data.get('transcript')
        test_mode = data.get('test_mode', True)
        
        if not transcript:
            return jsonify({
                'status': 'error',
                'message': 'Transcript is required'
            }), 400
        
        # Check if AI POC is available
        if not AI_POC_AVAILABLE:
            return jsonify({
                'status': 'error',
                'message': 'AI analysis not available'
            }), 503
        
        # Analyze transcript using the AI service
        result = ai_service.analyze_transcript(
            transcript=transcript,
            session_id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            async_mode=False  # Synchronous for testing
        )
        
        return jsonify({
            'status': 'success',
            'analysis': result,
            'test_mode': test_mode,
            'transcript_length': len(transcript),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        log_error('API', f"Error in test transcript analysis: {str(e)}", e)
        return jsonify({
            'status': 'error',
            'message': f"Analysis failed: {str(e)}"
        }), 500