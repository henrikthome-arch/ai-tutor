#!/usr/bin/env python3
"""
Simple AI Tutor Data Server
Alternative to the Node.js MCP server for quick testing
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TutorDataHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/health':
            self.send_json_response({'status': 'healthy', 'server': 'Python AI Tutor Server'})
        elif parsed_path.path == '/mcp/tools':
            self.send_tools_manifest()
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            request_data = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return
        
        parsed_path = urlparse(self.path)
        
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
    
    def handle_get_student_context(self, request_data):
        student_id = request_data.get('student_id')
        if not student_id:
            self.send_error(400, "student_id is required")
            return
        
        try:
            # Read all student data
            profile = self.read_json_file(f'data/students/{student_id}/profile.json')
            progress = self.read_json_file(f'data/students/{student_id}/progress.json')
            curriculum = self.read_json_file('data/curriculum/international_school_greece.json')
            
            # Get recent sessions
            sessions_dir = f'data/students/{student_id}/sessions'
            recent_sessions = []
            if os.path.exists(sessions_dir):
                session_files = [f for f in os.listdir(sessions_dir) if f.endswith('_summary.json')]
                session_files.sort(reverse=True)
                
                for session_file in session_files[:3]:
                    session_date = session_file.replace('_summary.json', '')
                    summary = self.read_json_file(f'{sessions_dir}/{session_file}')
                    recent_sessions.append({
                        'date': session_date,
                        'summary': summary
                    })
            
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
            self.send_error(500, str(e))
    
    def read_json_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response = json.dumps(data, indent=2, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))
    
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
                },
                {
                    "name": "get-student-progress",
                    "description": "Get current progress assessment for a student",
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
                    "name": "get-curriculum",
                    "description": "Get curriculum requirements and learning goals",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "curriculum_name": {
                                "type": "string",
                                "description": "Name of the curriculum file"
                            }
                        },
                        "required": ["curriculum_name"]
                    }
                }
            ]
        }
        self.send_json_response(tools)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server(port=3000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, TutorDataHandler)
    
    print(f"AI Tutor Data Server starting on port {port}")
    print(f"Health check: http://localhost:{port}/health")
    print(f"Tools manifest: http://localhost:{port}/mcp/tools")
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == '__main__':
    run_server()