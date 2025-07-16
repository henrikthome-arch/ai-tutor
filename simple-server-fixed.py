#!/usr/bin/env python3
"""
Simple AI Tutor Data Server - Fixed Version
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TutorDataHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        logger.info(f"GET request for: {parsed_path.path}")
        
        try:
            if parsed_path.path == '/health':
                self.send_json_response({'status': 'healthy', 'server': 'Python AI Tutor Server'})
            elif parsed_path.path == '/mcp/tools':
                self.send_tools_manifest()
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
            
            logger.info(f"Request data: {request_data}")
            
            if parsed_path.path == '/mcp/get-student-context':
                self.handle_get_student_context(request_data)
            elif parsed_path.path == '/mcp/get-student-profile':
                self.handle_get_student_profile(request_data)
            elif parsed_path.path == '/mcp/get-student-progress':
                self.handle_get_student_progress(request_data)
            elif parsed_path.path == '/mcp/get-curriculum':
                self.handle_get_curriculum(request_data)
            else:
                self.send_error(404, "Endpoint not found")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            self.send_error(400, "Invalid JSON")
        except Exception as e:
            logger.error(f"Error in POST handler: {e}")
            self.send_error(500, f"Server error: {str(e)}")
    
    def handle_get_student_context(self, request_data):
        student_id = request_data.get('student_id')
        if not student_id:
            self.send_error(400, "student_id is required")
            return
        
        logger.info(f"Getting context for student: {student_id}")
        
        try:
            # Check if files exist first
            profile_path = f'data/students/{student_id}/profile.json'
            progress_path = f'data/students/{student_id}/progress.json'
            curriculum_path = 'data/curriculum/international_school_greece.json'
            
            if not os.path.exists(profile_path):
                self.send_error(404, f"Student profile not found: {student_id}")
                return
            
            # Read student data
            profile = self.read_json_file(profile_path)
            progress = self.read_json_file(progress_path)
            curriculum = self.read_json_file(curriculum_path)
            
            # Get recent sessions
            sessions_dir = f'data/students/{student_id}/sessions'
            recent_sessions = []
            if os.path.exists(sessions_dir):
                session_files = [f for f in os.listdir(sessions_dir) if f.endswith('_summary.json')]
                session_files.sort(reverse=True)
                
                for session_file in session_files[:3]:
                    session_date = session_file.replace('_summary.json', '')
                    try:
                        summary = self.read_json_file(f'{sessions_dir}/{session_file}')
                        recent_sessions.append({
                            'date': session_date,
                            'summary': summary
                        })
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
            
            logger.info(f"Successfully retrieved context for {student_id}")
            self.send_json_response({'success': True, 'data': response_data})
            
        except Exception as e:
            logger.error(f"Error getting student context: {e}")
            self.send_error(500, str(e))
    
    def handle_get_student_profile(self, request_data):
        student_id = request_data.get('student_id')
        if not student_id:
            self.send_error(400, "student_id is required")
            return
        
        try:
            profile = self.read_json_file(f'data/students/{student_id}/profile.json')
            self.send_json_response({'success': True, 'data': profile})
        except Exception as e:
            logger.error(f"Error getting student profile: {e}")
            self.send_error(500, str(e))
    
    def handle_get_student_progress(self, request_data):
        student_id = request_data.get('student_id')
        if not student_id:
            self.send_error(400, "student_id is required")
            return
        
        try:
            progress = self.read_json_file(f'data/students/{student_id}/progress.json')
            self.send_json_response({'success': True, 'data': progress})
        except Exception as e:
            logger.error(f"Error getting student progress: {e}")
            self.send_error(500, str(e))
    
    def handle_get_curriculum(self, request_data):
        curriculum_name = request_data.get('curriculum_name')
        if not curriculum_name:
            self.send_error(400, "curriculum_name is required")
            return
        
        try:
            curriculum = self.read_json_file(f'data/curriculum/{curriculum_name}.json')
            self.send_json_response({'success': True, 'data': curriculum})
        except Exception as e:
            logger.error(f"Error getting curriculum: {e}")
            self.send_error(500, str(e))
    
    def read_json_file(self, file_path):
        logger.info(f"Reading file: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def send_json_response(self, data, status_code=200):
        try:
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            response = json.dumps(data, indent=2, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
            logger.info(f"Sent response: {status_code}")
            
        except Exception as e:
            logger.error(f"Error sending response: {e}")
    
    def send_tools_manifest(self):
        tools = {
            "tools": [
                {
                    "name": "get-student-context",
                    "description": "Get comprehensive context for a student including profile, progress, recent sessions, and curriculum data",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "student_id": {
                                "type": "string",
                                "description": "The unique identifier for the student"
                            }
                        },
                        "required": ["student_id"]
                    }
                },
                {
                    "name": "get-student-profile",
                    "description": "Get detailed profile information for a student",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "student_id": {
                                "type": "string",
                                "description": "The unique identifier for the student"
                            }
                        },
                        "required": ["student_id"]
                    }
                }
            ]
        }
        self.send_json_response(tools)
    
    def do_OPTIONS(self):
        try:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
        except Exception as e:
            logger.error(f"Error in OPTIONS handler: {e}")

def run_server(port=3000):
    server_address = ('', port)
    
    try:
        httpd = HTTPServer(server_address, TutorDataHandler)
        
        print("=" * 50)
        print("AI Tutor Data Server - STARTING")
        print("=" * 50)
        print(f"Server starting on port {port}")
        print(f"Health check: http://localhost:{port}/health")
        print(f"Tools manifest: http://localhost:{port}/mcp/tools")
        print(f"Working directory: {os.getcwd()}")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Check if data directory exists
        if os.path.exists('data'):
            print("✓ Data directory found")
            if os.path.exists('data/students/emma_smith'):
                print("✓ Sample student data found")
            else:
                print("⚠ Sample student data not found")
        else:
            print("✗ Data directory not found")
        
        print("=" * 50)
        
        httpd.serve_forever()
        
    except OSError as e:
        if e.errno == 10048:  # Port already in use
            print(f"ERROR: Port {port} is already in use")
            print("Try stopping other servers or use a different port")
        else:
            print(f"ERROR: Could not start server: {e}")
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        logger.error(f"Server error: {e}")

if __name__ == '__main__':
    run_server()