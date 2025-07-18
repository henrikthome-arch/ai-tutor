#!/usr/bin/env python3
"""
Session-Enhanced AI Tutor Server
Platform-agnostic session tracking with VAPI webhook integration
"""

import json
import os
import time
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import logging
import uuid
import yaml
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SessionTracker:
    """Handles session tracking and detection"""
    
    def __init__(self, timeout_minutes=10):
        self.timeout_minutes = timeout_minutes
        self.active_sessions = {}  # {student_id: session_data}
        self.session_history = {}  # {session_id: session_data}
        
    def log_interaction(self, student_id: str, function_name: str, request_data: dict, response_size: int):
        """Log an MCP function call interaction"""
        timestamp = datetime.utcnow()
        
        # Check if this is a new session or continuation
        session = self.get_or_create_session(student_id, timestamp)
        
        interaction = {
            'timestamp': timestamp.isoformat(),
            'function': function_name,
            'request_data': request_data,
            'response_size_bytes': response_size,
            'subjects_accessed': self.extract_subjects(request_data, function_name)
        }
        
        session['mcp_interactions'].append(interaction)
        session['last_activity'] = timestamp.isoformat()
        session['status'] = 'active'
        
        logger.info(f"Logged interaction for session {session['session_id']}: {function_name}")
        return session['session_id']
    
    def get_or_create_session(self, student_id: str, timestamp: datetime):
        """Get existing session or create new one based on time gap"""
        
        # Check if student has active session
        if student_id in self.active_sessions:
            last_session = self.active_sessions[student_id]
            last_activity = datetime.fromisoformat(last_session['last_activity'])
            
            # If gap is less than timeout, continue existing session
            if timestamp - last_activity < timedelta(minutes=self.timeout_minutes):
                return last_session
            else:
                # Close previous session and create new one
                self.close_session(last_session['session_id'])
        
        # Create new session
        session_id = self.generate_session_id(student_id, timestamp)
        session = {
            'session_id': session_id,
            'student_id': student_id,
            'start_time': timestamp.isoformat(),
            'last_activity': timestamp.isoformat(),
            'end_time': None,
            'platform': 'unknown',
            'status': 'active',
            'mcp_interactions': [],
            'conversation': {
                'transcript': None,
                'source': 'pending',
                'word_count': 0
            },
            'metadata': {},
            'analysis': None
        }
        
        self.active_sessions[student_id] = session
        self.session_history[session_id] = session
        
        logger.info(f"Created new session: {session_id}")
        return session
    
    def generate_session_id(self, student_id: str, timestamp: datetime) -> str:
        """Generate consistent session ID for matching with external platforms"""
        return f"{student_id}_{timestamp.strftime('%Y%m%d_%H%M')}"
    
    def close_session(self, session_id: str):
        """Mark session as completed"""
        if session_id in self.session_history:
            session = self.session_history[session_id]
            session['status'] = 'completed'
            session['end_time'] = datetime.utcnow().isoformat()
            
            # Remove from active sessions
            student_id = session['student_id']
            if student_id in self.active_sessions and self.active_sessions[student_id]['session_id'] == session_id:
                del self.active_sessions[student_id]
            
            # Save session to file
            self.save_session(session)
            logger.info(f"Closed session: {session_id}")
    
    def save_session(self, session: dict):
        """Save session data to file system"""
        student_id = session['student_id']
        session_id = session['session_id']
        
        # Create sessions directory if it doesn't exist
        sessions_dir = f'../data/students/{student_id}/sessions'
        os.makedirs(sessions_dir, exist_ok=True)
        
        # Save session file
        session_file = f'{sessions_dir}/{session_id}_session.json'
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved session to: {session_file}")
    
    def extract_subjects(self, request_data: dict, function_name: str) -> List[str]:
        """Extract subject areas from request data"""
        subjects = []
        # Add logic to extract subjects based on function and data
        if function_name == 'get-student-context':
            # Could extract from curriculum data accessed
            subjects = ['general']
        return subjects
    
    def find_session_by_timeframe(self, student_id: str, start_time: str, end_time: str = None) -> Optional[dict]:
        """Find session by time range for webhook matching"""
        # Ensure timezone-aware datetime parsing
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00')) if end_time else start_dt + timedelta(hours=2)
        
        for session in self.session_history.values():
            if session['student_id'] != student_id:
                continue
                
            # Parse session start time and make it timezone-aware if needed
            session_start_str = session['start_time']
            if session_start_str.endswith('Z'):
                session_start = datetime.fromisoformat(session_start_str.replace('Z', '+00:00'))
            elif '+' in session_start_str or session_start_str.endswith('00:00'):
                session_start = datetime.fromisoformat(session_start_str)
            else:
                # Make timezone-aware by adding UTC offset
                session_start = datetime.fromisoformat(session_start_str).replace(tzinfo=start_dt.tzinfo)
            
            # Check if session times overlap (within 5 minutes)
            if abs((session_start - start_dt).total_seconds()) < 300:
                return session
        
        return None

class ConfigManager:
    """Manages configuration for session tracking and analysis"""
    
    def __init__(self, config_path='../scripts/session_config.yaml'):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> dict:
        """Load configuration from YAML file"""
        default_config = {
            'session_tracking': {
                'timeout_minutes': 10,
                'auto_save': True
            },
            'webhooks': {
                'vapi': {
                    'enabled': True,
                    'endpoint': '/webhook/vapi/session-complete',
                    'auth_token': None
                }
            },
            'analysis': {
                'enabled': False,
                'openai_api_key': None,
                'triggers': ['on_session_complete'],
                'prompts': {
                    'session_summary': 'Analyze this tutoring session...',
                    'progress_update': 'Update student progress based on...'
                }
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    # Merge with defaults
                    default_config.update(loaded_config)
            except Exception as e:
                logger.warning(f"Could not load config file: {e}")
        
        return default_config
    
    def get(self, key_path: str, default=None):
        """Get configuration value by dot notation path"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value

class SessionAnalyzer:
    """Handles session analysis with configurable prompts"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.enabled = config.get('analysis.enabled', False)
    
    def analyze_session(self, session: dict) -> Optional[dict]:
        """Analyze session data if enabled and configured"""
        if not self.enabled:
            return None
        
        # Placeholder for analysis logic
        # In production, this would use OpenAI API with configurable prompts
        analysis = {
            'session_summary': 'Session analysis would go here',
            'learning_outcomes': [],
            'engagement_score': 0.8,
            'next_steps': [],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Generated analysis for session {session['session_id']}")
        return analysis

class PhoneMappingManager:
    """Manages phone number to student ID mapping"""
    
    def __init__(self, mapping_file='../data/phone_mapping.json'):
        # Production-ready pathing: make path absolute relative to this script file
        # This will resolve any issues with the current working directory in deployment
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.mapping_file = os.path.join(script_dir, mapping_file)
        
        self.phone_mapping = self.load_phone_mapping()
    
    def load_phone_mapping(self):
        """Load phone to student mapping"""
        if os.path.exists(self.mapping_file):
            try:
                with open(self.mapping_file, 'r') as f:
                    data = json.load(f)
                    # The mapping is the entire file content, not nested.
                    # This was a bug. Correcting to load the entire dictionary.
                    return data
            except Exception as e:
                logger.error(f"Error loading phone mapping: {e}")
                return {}
        return {}
    
    def save_phone_mapping(self):
        """Save phone to student mapping"""
        try:
            os.makedirs(os.path.dirname(self.mapping_file), exist_ok=True)
            # This was also a bug. Saving the mapping directly.
            with open(self.mapping_file, 'w') as f:
                json.dump(self.phone_mapping, f, indent=2)
            logger.info(f"📞 Saved phone mapping to {self.mapping_file}")
        except Exception as e:
            logger.error(f"Error saving phone mapping: {e}")
    
    def get_student_by_phone(self, phone_number):
        """Get student ID by phone number, ensuring fresh data."""
        # Critical fix: Reload the mapping from disk on every lookup to prevent stale state
        current_mapping = self.load_phone_mapping()
        
        normalized_phone = self.normalize_phone_number(phone_number)
        
        # Look up in the freshly loaded mapping
        student_id = current_mapping.get(normalized_phone)
        
        logger.info(f"📞 Phone lookup: {normalized_phone} → {student_id} (from fresh data)")
        return student_id
    
    def add_phone_mapping(self, phone_number, student_id):
        """Add new phone to student mapping, ensuring data integrity."""
        # CRITICAL FIX: Load the latest mapping from disk to avoid overwriting with a stale in-memory version.
        current_mapping = self.load_phone_mapping()
        
        normalized_phone = self.normalize_phone_number(phone_number)
        
        # Add the new mapping to the freshly loaded data
        current_mapping[normalized_phone] = student_id
        
        # Update the in-memory mapping and save the complete, updated version to disk
        self.phone_mapping = current_mapping
        self.save_phone_mapping()
        
        logger.info(f"📞 Mapped {normalized_phone} → {student_id} (and saved full mapping)")
    
    def normalize_phone_number(self, phone_number):
        """Normalize phone number format"""
        if not phone_number:
            return None
            
        # Remove all non-digits
        digits_only = ''.join(filter(str.isdigit, phone_number))
        
        # Handle different formats
        if len(digits_only) == 10:
            return f"+1{digits_only}"  # US number
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"   # US number with country code
        else:
            return f"+{digits_only}"   # International format

class EnhancedTutorDataHandler(BaseHTTPRequestHandler):
    
    def __init__(self, *args, session_tracker=None, config_manager=None, analyzer=None, phone_manager=None, **kwargs):
        self.session_tracker = session_tracker
        self.config = config_manager
        self.analyzer = analyzer
        self.phone_manager = phone_manager
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        logger.info(f"GET request for: {parsed_path.path}")
        
        try:
            if parsed_path.path == '/health':
                self.send_json_response({
                    'status': 'healthy', 
                    'server': 'Session-Enhanced AI Tutor Server',
                    'session_tracking': 'enabled',
                    'active_sessions': len(self.session_tracker.active_sessions)
                })
            elif parsed_path.path == '/mcp/tools':
                self.send_tools_manifest()
            elif parsed_path.path == '/mcp/get-student-context':
                # Handle GET with query parameters
                from urllib.parse import parse_qs
                query_params = parse_qs(parsed_path.query)
                student_id = query_params.get('student_id', [None])[0]
                if student_id:
                    self.handle_get_student_context({'student_id': student_id})
                else:
                    self.send_error(400, "student_id parameter is required")
            elif parsed_path.path == '/sessions/active':
                self.handle_get_active_sessions()
            elif parsed_path.path.startswith('/sessions/'):
                session_id = parsed_path.path.split('/')[-1]
                self.handle_get_session(session_id)
            else:
                self.send_error(404, "Endpoint not found")
        except Exception as e:
            logger.error(f"Error in GET handler: {e}")
            self.send_error(500, f"Server error: {str(e)}")
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        logger.info(f"POST request for: {parsed_path.path}")
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
            else:
                request_data = {}
            
            logger.info(f"Request data keys: {list(request_data.keys())}")
            
            if parsed_path.path == '/mcp/get-student-context':
                self.handle_get_student_context(request_data)
            elif parsed_path.path == '/webhook/vapi/session-complete':
                self.handle_vapi_webhook(request_data)
            elif parsed_path.path == '/webhook/session-data':
                self.handle_generic_webhook(request_data)
            elif parsed_path.path == '/sessions/close':
                self.handle_close_session(request_data)
            else:
                self.send_error(404, "Endpoint not found")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            self.send_error(400, "Invalid JSON")
        except Exception as e:
            logger.error(f"Error in POST handler: {e}")
            self.send_error(500, f"Server error: {str(e)}")
    
    def handle_get_student_context(self, request_data):
        """Enhanced student context handler with session tracking and phone lookup"""
        # Support both student_id and phone_number parameters
        student_id = request_data.get('student_id')
        phone_number = request_data.get('phone_number')
        
        # If phone number provided, lookup student_id
        if phone_number and not student_id:
            student_id = self.phone_manager.get_student_by_phone(phone_number)
            if not student_id:
                # This is a new caller - could trigger welcome flow in future
                logger.info(f"📞 Unknown phone number: {phone_number}")
                self.send_json_response({
                    'success': False,
                    'error': 'unknown_phone_number',
                    'message': 'Phone number not registered',
                    'phone_number': phone_number,
                    'action_required': 'welcome_onboarding'
                })
                return
            else:
                logger.info(f"📞 Resolved phone {phone_number} → {student_id}")
        
        if not student_id:
            self.send_error(400, "Either student_id or phone_number is required")
            return
        
        logger.info(f"Getting context for student: {student_id}")
        
        try:
            # Read student data (same as before)
            profile_path = f'../data/students/{student_id}/profile.json'
            progress_path = f'../data/students/{student_id}/progress.json'
            curriculum_path = '../data/curriculum/international_school_greece.json'
            
            if not os.path.exists(profile_path):
                self.send_error(404, f"Student profile not found: {student_id}")
                return
            
            profile = self.read_json_file(profile_path)
            progress = self.read_json_file(progress_path)
            curriculum = self.read_json_file(curriculum_path)
            
            # Get recent sessions (enhanced)
            sessions_dir = f'../data/students/{student_id}/sessions'
            recent_sessions = []
            if os.path.exists(sessions_dir):
                session_files = [f for f in os.listdir(sessions_dir) if f.endswith('_session.json')]
                session_files.sort(reverse=True)
                
                for session_file in session_files[:3]:
                    try:
                        session_data = self.read_json_file(f'{sessions_dir}/{session_file}')
                        recent_sessions.append(session_data)
                    except Exception as e:
                        logger.warning(f"Could not read session file {session_file}: {e}")
            
            grade_data = curriculum.get('grades', {}).get(str(profile.get('grade', 4)), {})
            
            response_data = {
                'profile': profile,
                'progress': progress,
                'recent_sessions': recent_sessions,
                'curriculum_context': {
                    'grade_subjects': grade_data,
                    'school_type': curriculum.get('school_type'),
                    'curriculum_system': curriculum.get('curriculum_system')
                }
            }
            
            # Log this interaction in session tracker
            response_json = json.dumps(response_data, ensure_ascii=False)
            session_id = self.session_tracker.log_interaction(
                student_id=student_id,
                function_name='get-student-context', 
                request_data=request_data,
                response_size=len(response_json.encode('utf-8'))
            )
            
            logger.info(f"Successfully retrieved context for {student_id} (session: {session_id})")
            self.send_json_response({'success': True, 'data': response_data})
            
        except Exception as e:
            logger.error(f"Error getting student context: {e}")
            self.send_error(500, str(e))
    
    def handle_vapi_webhook(self, request_data):
        """Handle VAPI session completion webhook"""
        logger.info("Received VAPI webhook")
        
        try:
            # Extract VAPI data
            call_id = request_data.get('call_id')
            transcript = request_data.get('transcript', '')
            started_at = request_data.get('started_at')
            ended_at = request_data.get('ended_at')
            duration = request_data.get('duration_seconds', 0)
            
            # Extract student ID (implementation depends on VAPI setup)
            student_id = self.extract_student_from_vapi_data(request_data)
            
            if not student_id:
                logger.warning("Could not extract student_id from VAPI webhook")
                self.send_json_response({'success': False, 'error': 'student_id not found'})
                return
            
            # Find matching session
            session = self.session_tracker.find_session_by_timeframe(student_id, started_at, ended_at)
            
            if not session:
                logger.warning(f"No matching session found for VAPI call {call_id}")
                # Create new session for this conversation
                session = self.session_tracker.get_or_create_session(
                    student_id, 
                    datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                )
            
            # Update session with VAPI data
            session.update({
                'end_time': ended_at,
                'platform': 'vapi',
                'status': 'completed',
                'conversation': {
                    'transcript': transcript,
                    'source': 'vapi',
                    'word_count': len(transcript.split()),
                    'duration_seconds': duration
                },
                'vapi_metadata': {
                    'call_id': call_id,
                    'cost': request_data.get('cost'),
                    'ended_reason': request_data.get('ended_reason')
                }
            })
            
            # Close session and save
            self.session_tracker.close_session(session['session_id'])
            
            # Trigger analysis if enabled
            if self.analyzer and self.analyzer.enabled:
                analysis = self.analyzer.analyze_session(session)
                if analysis:
                    session['analysis'] = analysis
                    self.session_tracker.save_session(session)
            
            logger.info(f"Successfully processed VAPI webhook for session {session['session_id']}")
            self.send_json_response({'success': True, 'session_id': session['session_id']})
            
        except Exception as e:
            logger.error(f"Error processing VAPI webhook: {e}")
            self.send_error(500, str(e))
    
    def extract_student_from_vapi_data(self, vapi_data) -> Optional[str]:
        """Extract student ID from VAPI webhook data"""
        # Strategy 1: Check custom metadata
        if 'metadata' in vapi_data and 'student_id' in vapi_data['metadata']:
            return vapi_data['metadata']['student_id']
        
        # Strategy 2: Extract from transcript (first few words)
        transcript = vapi_data.get('transcript', '')
        if transcript:
            # Look for patterns like "My name is Emma" or student identification
            # This is a simplified implementation
            words = transcript.lower().split()
            if 'emma' in words:
                return 'emma_smith'
            elif 'jane' in words:
                return 'jane_doe'
        
        # Strategy 3: Use phone number mapping (if available)
        phone = vapi_data.get('customer', {}).get('number')
        if phone:
            # Use phone manager for lookup
            return self.phone_manager.get_student_by_phone(phone)
        
        return None
    
    def handle_generic_webhook(self, request_data):
        """Handle generic platform webhook"""
        platform = request_data.get('platform', 'unknown')
        logger.info(f"Received webhook from platform: {platform}")
        
        if platform == 'vapi':
            self.handle_vapi_webhook(request_data)
        else:
            logger.warning(f"Unsupported platform: {platform}")
            self.send_json_response({'success': False, 'error': f'Unsupported platform: {platform}'})
    
    def handle_get_active_sessions(self):
        """Get all active sessions"""
        active = {
            'count': len(self.session_tracker.active_sessions),
            'sessions': list(self.session_tracker.active_sessions.values())
        }
        self.send_json_response({'success': True, 'data': active})
    
    def handle_get_session(self, session_id):
        """Get specific session data"""
        if session_id in self.session_tracker.session_history:
            session = self.session_tracker.session_history[session_id]
            self.send_json_response({'success': True, 'data': session})
        else:
            self.send_error(404, f"Session not found: {session_id}")
    
    def handle_close_session(self, request_data):
        """Manually close a session"""
        session_id = request_data.get('session_id')
        if not session_id:
            self.send_error(400, "session_id is required")
            return
        
        self.session_tracker.close_session(session_id)
        self.send_json_response({'success': True, 'message': f'Session {session_id} closed'})
    
    def read_json_file(self, file_path):
        """Read JSON file with error handling"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response with CORS headers"""
        try:
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            response = json.dumps(data, indent=2, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error sending response: {e}")
    
    def send_tools_manifest(self):
        """Send MCP tools manifest"""
        tools = {
            "tools": [
                {
                    "name": "get-student-context",
                    "description": "Get comprehensive context for a student including profile, progress, recent sessions, and curriculum data. Supports both student_id and phone_number lookup.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "student_id": {
                                "type": "string",
                                "description": "The unique identifier for the student"
                            },
                            "phone_number": {
                                "type": "string",
                                "description": "Phone number to lookup student (alternative to student_id)"
                            }
                        },
                        "anyOf": [
                            {"required": ["student_id"]},
                            {"required": ["phone_number"]}
                        ]
                    }
                }
            ]
        }
        self.send_json_response(tools)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        try:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
        except Exception as e:
            logger.error(f"Error in OPTIONS handler: {e}")

def create_handler_class(session_tracker, config_manager, analyzer, phone_manager):
    """Factory function to create handler class with dependencies"""
    class Handler(EnhancedTutorDataHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, session_tracker=session_tracker,
                           config_manager=config_manager, analyzer=analyzer,
                           phone_manager=phone_manager, **kwargs)
    return Handler

def run_enhanced_server(port=3000):
    """Run the enhanced server with session tracking"""
    
    # Initialize components
    config_manager = ConfigManager()
    session_tracker = SessionTracker(
        timeout_minutes=config_manager.get('session_tracking.timeout_minutes', 10)
    )
    analyzer = SessionAnalyzer(config_manager)
    phone_manager = PhoneMappingManager()
    
    # Create handler class with dependencies
    HandlerClass = create_handler_class(session_tracker, config_manager, analyzer, phone_manager)
    
    server_address = ('', port)
    
    try:
        httpd = HTTPServer(server_address, HandlerClass)
        
        print("=" * 60)
        print("SESSION-ENHANCED AI TUTOR SERVER - STARTING")
        print("=" * 60)
        print(f"Server starting on port {port}")
        print(f"Health check: http://localhost:{port}/health")
        print(f"MCP Tools: http://localhost:{port}/mcp/tools")
        print(f"Active sessions: http://localhost:{port}/sessions/active")
        print(f"Working directory: {os.getcwd()}")
        print()
        print("🔄 SESSION TRACKING ENABLED")
        print(f"   - Session timeout: {session_tracker.timeout_minutes} minutes")
        print(f"   - VAPI webhook: {config_manager.get('webhooks.vapi.endpoint')}")
        print(f"   - Analysis enabled: {analyzer.enabled}")
        print()
        print("📝 WEBHOOK ENDPOINTS:")
        print(f"   - VAPI: POST {config_manager.get('webhooks.vapi.endpoint')}")
        print(f"   - Generic: POST /webhook/session-data")
        print()
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Check data directory
        if os.path.exists('../data'):
            print("✓ Data directory found")
            if os.path.exists('../data/students/emma_smith'):
                print("✓ Sample student data found")
        else:
            print("✗ Data directory not found")
        
        print("=" * 60)
        
        httpd.serve_forever()
        
    except OSError as e:
        if e.errno == 10048:
            print(f"ERROR: Port {port} is already in use")
            print("Try stopping other servers or use a different port")
        else:
            print(f"ERROR: Could not start server: {e}")
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("SERVER STOPPED BY USER")
        print(f"Sessions tracked: {len(session_tracker.session_history)}")
        print("=" * 60)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        logger.error(f"Server error: {e}")

if __name__ == '__main__':
    run_enhanced_server()