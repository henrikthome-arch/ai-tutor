#!/usr/bin/env python3
"""
AI Tutor Admin Dashboard
Flask web interface for managing students, sessions, and system data
"""

import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from flask import Flask, render_template, session, redirect, request, flash, url_for, jsonify
import secrets

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Using default settings.")
    print("   Install with: pip install python-dotenv")

# Import our existing MCP functionality
import sys
sys.path.append('.')

# Import PhoneMappingManager from session-enhanced-server.py
import importlib.util
spec = importlib.util.spec_from_file_location("session_enhanced_server", "./session-enhanced-server.py")
session_enhanced_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(session_enhanced_server)

PhoneMappingManager = session_enhanced_server.PhoneMappingManager
SessionTracker = session_enhanced_server.SessionTracker

# Import System Logger
from system_logger import system_logger, log_admin_action, log_webhook, log_ai_analysis, log_error, log_system

# Import AI POC components
try:
    from ai_poc.session_processor import session_processor
    from ai_poc.providers import provider_manager
    from ai_poc.validator import validator
    import asyncio
    AI_POC_AVAILABLE = True
    print("🤖 AI Post-Processing POC loaded successfully")
except ImportError as e:
    AI_POC_AVAILABLE = False
    print(f"⚠️  AI POC not available: {e}")

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

# Security Configuration with Environment Variables
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')  # Default for development only
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
FLASK_ENV = os.getenv('FLASK_ENV', 'development')

# VAPI Configuration
VAPI_SECRET = os.getenv('VAPI_SECRET', 'your_vapi_secret_here')

# Set secure secret key
app.secret_key = FLASK_SECRET_KEY

# Hash the password (whether from env var or default)
ADMIN_PASSWORD_HASH = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()

# Security warnings
if ADMIN_PASSWORD == 'admin123':
    print("🚨 SECURITY WARNING: Using default password!")
    print("   Set ADMIN_PASSWORD environment variable for production.")

if FLASK_ENV == 'development':
    print("⚠️  Running in development mode.")
    print("   Set FLASK_ENV=production for production deployment.")

# Initialize managers
phone_manager = PhoneMappingManager()
session_tracker = SessionTracker()

# Log system startup
log_system("AI Tutor Admin Dashboard starting up",
          flask_env=FLASK_ENV,
          admin_username=ADMIN_USERNAME,
          has_vapi_secret=VAPI_SECRET != 'your_vapi_secret_here',
          ai_poc_available=AI_POC_AVAILABLE)

def check_auth():
    """Check if user is authenticated"""
    return session.get('admin_logged_in', False)

def get_all_students():
    """Get list of all students from data directory"""
    students = []
    students_dir = '../data/students'
    
    if not os.path.exists(students_dir):
        return students
    
    for student_id in os.listdir(students_dir):
        student_path = os.path.join(students_dir, student_id)
        if os.path.isdir(student_path):
            profile_path = os.path.join(student_path, 'profile.json')
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile = json.load(f)
                    
                    # Get phone number
                    phone = None
                    for phone_num, sid in phone_manager.phone_mapping.items():
                        if sid == student_id:
                            phone = phone_num
                            break
                    
                    # Get session count
                    sessions_dir = os.path.join(student_path, 'sessions')
                    session_count = 0
                    if os.path.exists(sessions_dir):
                        session_count = len([f for f in os.listdir(sessions_dir) if f.endswith('_session.json')])
                    
                    students.append({
                        'id': student_id,
                        'name': profile.get('name', 'Unknown'),
                        'age': profile.get('age', 'Unknown'),
                        'grade': profile.get('grade', 'Unknown'),
                        'phone': phone,
                        'session_count': session_count,
                        'profile': profile
                    })
                except Exception as e:
                    print(f"Error loading student {student_id}: {e}")
    
    return sorted(students, key=lambda x: x['name'])

def get_student_data(student_id):
    """Get detailed student data"""
    student_dir = f'../data/students/{student_id}'
    if not os.path.exists(student_dir):
        return None
    
    student_data = {
        'id': student_id,
        'profile': None,
        'progress': None,
        'sessions': []
    }
    
    # Load profile
    profile_path = os.path.join(student_dir, 'profile.json')
    if os.path.exists(profile_path):
        with open(profile_path, 'r', encoding='utf-8') as f:
            student_data['profile'] = json.load(f)
    
    # Load progress
    progress_path = os.path.join(student_dir, 'progress.json')
    if os.path.exists(progress_path):
        with open(progress_path, 'r', encoding='utf-8') as f:
            student_data['progress'] = json.load(f)
    
    # Load sessions
    sessions_dir = os.path.join(student_dir, 'sessions')
    if os.path.exists(sessions_dir):
        for session_file in os.listdir(sessions_dir):
            if session_file.endswith('_session.json'):
                session_path = os.path.join(sessions_dir, session_file)
                try:
                    with open(session_path, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    student_data['sessions'].append(session_data)
                except Exception as e:
                    print(f"Error loading session {session_file}: {e}")
    
    # Sort sessions by start time (newest first)
    student_data['sessions'].sort(key=lambda x: x.get('start_time', ''), reverse=True)
    
    return student_data

def get_system_stats():
    """Get system statistics for dashboard"""
    students = get_all_students()
    
    # Count sessions today
    today = datetime.now().strftime('%Y-%m-%d')
    sessions_today = 0
    
    for student in students:
        sessions_dir = f'../data/students/{student["id"]}/sessions'
        if os.path.exists(sessions_dir):
            for session_file in os.listdir(sessions_dir):
                if session_file.endswith('_session.json') and today in session_file:
                    sessions_today += 1
    
    # Get server status
    server_status = "Online" if os.path.exists('../data') else "Offline"
    
    return {
        'total_students': len(students),
        'sessions_today': sessions_today,
        'total_sessions': sum(s['session_count'] for s in students),
        'server_status': server_status,
        'phone_mappings': len(phone_manager.phone_mapping)
    }

# Root route for health checks
@app.route('/')
def index():
    """Root route for health checks and redirects"""
    return redirect(url_for('admin_dashboard'))

# Authentication routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form['password']
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if password_hash == ADMIN_PASSWORD_HASH:
            session['admin_logged_in'] = True
            session['admin_username'] = 'admin'
            log_admin_action('login', 'admin',
                           ip_address=request.remote_addr,
                           user_agent=request.headers.get('User-Agent', 'Unknown'))
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            log_admin_action('failed_login', 'admin',
                           ip_address=request.remote_addr,
                           user_agent=request.headers.get('User-Agent', 'Unknown'),
                           level='WARNING')
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    log_admin_action('logout', session.get('admin_username', 'unknown'),
                    ip_address=request.remote_addr)
    session.clear()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('admin_login'))

# Dashboard routes
@app.route('/admin')
@app.route('/admin/')
def admin_dashboard():
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    stats = get_system_stats()
    recent_students = get_all_students()[:5]  # Get 5 most recent
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_students=recent_students)

# Student management routes
@app.route('/admin/students')
def admin_students():
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    students = get_all_students()
    return render_template('students.html', students=students)

@app.route('/admin/students/<student_id>')
def admin_student_detail(student_id):
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    student_data = get_student_data(student_id)
    if not student_data:
        flash(f'Student {student_id} not found', 'error')
        return redirect(url_for('admin_students'))
    
    # Get phone number
    phone = None
    for phone_num, sid in phone_manager.phone_mapping.items():
        if sid == student_id:
            phone = phone_num
            break
    
    # Extract data for template
    profile = student_data.get('profile', {})
    progress = student_data.get('progress', {})
    sessions = student_data.get('sessions', [])
    
    # Create student object for template
    student = {
        'id': student_id,
        'name': profile.get('name', 'Unknown'),
        'age': profile.get('age', 'Unknown'),
        'grade': profile.get('grade', 'Unknown'),
        'phone': phone,
        'interests': profile.get('interests', []),
        'learning_preferences': profile.get('learning_preferences', [])
    }
    
    # Process sessions for recent sessions display
    recent_sessions = []
    for session in sessions[:5]:  # Last 5 sessions
        recent_sessions.append({
            'date': session.get('start_time', '').split('T')[0] if session.get('start_time') else 'Unknown',
            'duration': session.get('duration_minutes', session.get('duration_seconds', 0) // 60 if session.get('duration_seconds') else 'Unknown'),
            'topics': session.get('topics_covered', ['General']),
            'engagement': session.get('engagement_score', 75),
            'file': session.get('transcript_file', '')
        })
    
    return render_template('student_detail.html',
                         student=student,
                         phone=phone,
                         progress=progress,
                         recent_sessions=recent_sessions,
                         session_count=len(sessions),
                         last_session=recent_sessions[0]['date'] if recent_sessions else None)

# File browser routes
@app.route('/admin/files')
def admin_files():
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    path = request.args.get('path', '../data')
    
    # Security: ensure path is within data directory
    if not path.startswith('../data'):
        path = '../data'
    
    files = []
    directories = []
    
    if os.path.exists(path):
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                directories.append({
                    'name': item,
                    'path': item_path,
                    'type': 'directory'
                })
            else:
                stat = os.stat(item_path)
                files.append({
                    'name': item,
                    'path': item_path,
                    'type': 'file',
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    # Calculate directory stats
    total_items = len(directories) + len(files)
    stats = {
        'total_items': total_items,
        'folders': len(directories),
        'files': len(files),
        'total_size': f"{sum(f.get('size', 0) for f in files)} bytes"
    }
    
    # Build breadcrumb for navigation
    breadcrumb_parts = []
    if path != '../data':
        path_parts = path.split('/')
        for i, part in enumerate(path_parts):
            breadcrumb_parts.append({
                'name': part,
                'path': '/'.join(path_parts[:i+1])
            })
    
    # Calculate parent path for back button
    parent_path = '/'.join(path.split('/')[:-1]) if '/' in path and path != '../data' else ''
    
    # Combine directories and files for unified display
    items = []
    for d in directories:
        items.append({
            'name': d['name'],
            'type': 'directory',
            'size': f"{len(os.listdir(d['path']))} items" if os.path.exists(d['path']) else "0 items",
            'modified': datetime.fromtimestamp(os.path.getctime(d['path'])).strftime('%Y-%m-%d %H:%M') if os.path.exists(d['path']) else 'Unknown',
            'count': len(os.listdir(d['path'])) if os.path.exists(d['path']) else 0
        })
    
    for f in files:
        items.append({
            'name': f['name'],
            'type': 'file',
            'size': f"{f['size']} bytes",
            'modified': f['modified']
        })
    
    return render_template('files.html',
                         current_path=path,
                         items=items,
                         stats=stats,
                         breadcrumb_parts=breadcrumb_parts,
                         parent_path=parent_path)

@app.route('/admin/files/view')
def admin_file_view():
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    file_path = request.args.get('path')
    if not file_path or not file_path.startswith('../data'):
        flash('Invalid file path', 'error')
        return redirect(url_for('admin_files'))
    
    if not os.path.exists(file_path):
        flash('File not found', 'error')
        return redirect(url_for('admin_files'))
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse as JSON for pretty display
        try:
            json_data = json.loads(content)
            content = json.dumps(json_data, indent=2, ensure_ascii=False)
            file_type = 'json'
        except:
            file_type = 'text'
        
        return render_template('file_view.html',
                             file_path=file_path,
                             content=content,
                             file_type=file_type)
    
    except Exception as e:
        flash(f'Error reading file: {e}', 'error')
        return redirect(url_for('admin_files'))

# System info route
@app.route('/admin/system')
def admin_system():
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    stats = get_system_stats()
    phone_mappings = dict(phone_manager.phone_mapping)
    
    # Get students info for phone mapping display
    students = get_all_students()
    students_info = {}
    for student in students:
        students_info[student['id']] = {
            'name': student['name'],
            'id': student['id'],
            'grade': student['grade']
        }
    
    return render_template('system.html',
                         stats=stats,
                         phone_mappings=phone_mappings,
                         students_info=students_info,
                         system_stats=stats,
                         mcp_port=3001,
                         vapi_status=False,
                         system_events=[])

# Phone Mapping Management
@app.route('/admin/phone-mappings/remove', methods=['POST'])
def remove_phone_mapping():
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    phone_number = request.form.get('phone_number')
    if not phone_number:
        return jsonify({'error': 'Phone number is required'}), 400
    
    if phone_number in phone_manager.phone_mapping:
        del phone_manager.phone_mapping[phone_number]
        phone_manager.save_mappings()
        flash(f'Phone mapping for {phone_number} removed successfully', 'success')
        return jsonify({'success': True, 'message': 'Phone mapping removed'})
    else:
        return jsonify({'error': 'Phone mapping not found'}), 404

@app.route('/admin/phone-mappings/add', methods=['POST'])
def add_phone_mapping():
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    phone_number = request.form.get('phone_number')
    student_id = request.form.get('student_id')
    
    if not phone_number or not student_id:
        return jsonify({'error': 'Phone number and student ID are required'}), 400
    
    # Check if student exists
    if not os.path.exists(f'../data/students/{student_id}'):
        return jsonify({'error': 'Student not found'}), 404
    
    phone_manager.phone_mapping[phone_number] = student_id
    phone_manager.save_mappings()
    flash(f'Phone mapping added: {phone_number} → {student_id}', 'success')
    return jsonify({'success': True, 'message': 'Phone mapping added'})

# Student CRUD Operations
@app.route('/admin/students/add', methods=['GET', 'POST'])
def add_student():
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        age = request.form.get('age')
        grade = request.form.get('grade')
        phone = request.form.get('phone')
        interests = request.form.get('interests', '').split(',')
        interests = [i.strip() for i in interests if i.strip()]
        
        if not name or not age or not grade:
            flash('Name, age, and grade are required', 'error')
            return render_template('add_student.html')
        
        # Generate student ID
        student_id = name.lower().replace(' ', '_').replace('.', '')
        counter = 1
        base_id = student_id
        while os.path.exists(f'../data/students/{student_id}'):
            student_id = f"{base_id}_{counter}"
            counter += 1
        
        # Create student directory
        student_dir = f'../data/students/{student_id}'
        os.makedirs(student_dir, exist_ok=True)
        os.makedirs(f'{student_dir}/sessions', exist_ok=True)
        
        # Create profile
        profile = {
            'name': name,
            'age': int(age),
            'grade': int(grade),
            'interests': interests,
            'learning_preferences': [],
            'curriculum': 'International School Greece',
            'created_date': datetime.now().isoformat()
        }
        
        with open(f'{student_dir}/profile.json', 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        # Create initial progress
        progress = {
            'overall_progress': 0,
            'subjects': {},
            'goals': [],
            'streak_days': 0,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(f'{student_dir}/progress.json', 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)
        
        # Add phone mapping if provided
        if phone:
            phone_manager.phone_mapping[phone] = student_id
            phone_manager.save_mappings()
        
        flash(f'Student {name} added successfully!', 'success')
        return redirect(url_for('admin_student_detail', student_id=student_id))
    
    return render_template('add_student.html')

@app.route('/admin/students/<student_id>/edit', methods=['GET', 'POST'])
def edit_student(student_id):
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    student_data = get_student_data(student_id)
    if not student_data:
        flash(f'Student {student_id} not found', 'error')
        return redirect(url_for('admin_students'))
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        age = request.form.get('age')
        grade = request.form.get('grade')
        phone = request.form.get('phone')
        interests = request.form.get('interests', '').split(',')
        interests = [i.strip() for i in interests if i.strip()]
        
        if not name or not age or not grade:
            flash('Name, age, and grade are required', 'error')
            return render_template('edit_student.html', student=student_data, student_id=student_id)
        
        # Update profile
        profile = student_data.get('profile', {})
        profile.update({
            'name': name,
            'age': int(age),
            'grade': int(grade),
            'interests': interests,
            'last_updated': datetime.now().isoformat()
        })
        
        profile_path = f'../data/students/{student_id}/profile.json'
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        # Update phone mapping
        # Remove old phone mapping for this student
        old_phone = None
        for phone_num, sid in list(phone_manager.phone_mapping.items()):
            if sid == student_id:
                old_phone = phone_num
                del phone_manager.phone_mapping[phone_num]
                break
        
        # Add new phone mapping
        if phone:
            phone_manager.phone_mapping[phone] = student_id
        
        phone_manager.save_mappings()
        
        flash(f'Student {name} updated successfully!', 'success')
        return redirect(url_for('admin_student_detail', student_id=student_id))
    
    # Get current phone
    phone = None
    for phone_num, sid in phone_manager.phone_mapping.items():
        if sid == student_id:
            phone = phone_num
            break
    
    return render_template('edit_student.html',
                         student=student_data.get('profile', {}),
                         student_id=student_id,
                         phone=phone)

@app.route('/admin/students/<student_id>/delete', methods=['POST'])
def delete_student(student_id):
    """Delete a student and all associated data"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        import shutil
        
        # Check if student exists
        student_dir = f'../data/students/{student_id}'
        if not os.path.exists(student_dir):
            return jsonify({'error': 'Student not found'}), 404
        
        # Get student name for logging
        student_name = 'Unknown'
        profile_path = os.path.join(student_dir, 'profile.json')
        if os.path.exists(profile_path):
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                student_name = profile.get('name', 'Unknown')
            except:
                pass
        
        # Remove phone mapping for this student
        phone_to_remove = None
        for phone_num, sid in list(phone_manager.phone_mapping.items()):
            if sid == student_id:
                phone_to_remove = phone_num
                del phone_manager.phone_mapping[phone_num]
                break
        
        if phone_to_remove:
            phone_manager.save_mappings()
        
        # Remove the entire student directory
        shutil.rmtree(student_dir)
        
        log_admin_action('delete_student', session.get('admin_username', 'unknown'),
                        student_id=student_id,
                        student_name=student_name,
                        phone_removed=phone_to_remove,
                        ip_address=request.remote_addr)
        
        return jsonify({
            'success': True,
            'message': f'Student {student_name} deleted successfully',
            'student_id': student_id,
            'redirect': url_for('admin_students')
        })
        
    except Exception as e:
        log_error('ADMIN', f'Error deleting student {student_id}', e,
                 student_id=student_id,
                 admin_user=session.get('admin_username', 'unknown'))
        return jsonify({'error': f'Failed to delete student: {str(e)}'}), 500

# All Sessions Overview Route
@app.route('/admin/sessions')
def admin_all_sessions():
    """View all sessions across all students"""
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    # Get all students and their sessions
    all_sessions = []
    students = get_all_students()
    
    for student in students:
        student_id = student['id']
        sessions_dir = f'../data/students/{student_id}/sessions'
        
        if os.path.exists(sessions_dir):
            for file in os.listdir(sessions_dir):
                if file.endswith('_session.json') or file.endswith('_summary.json'):
                    file_path = os.path.join(sessions_dir, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Check if there's a corresponding transcript
                        transcript_file = file.replace('_session.json', '_transcript.txt').replace('_summary.json', '_transcript.txt')
                        transcript_path = os.path.join(sessions_dir, transcript_file)
                        has_transcript = os.path.exists(transcript_path)
                        
                        # Check if there's a corresponding AI analysis
                        analysis_file = file.replace('_session.json', '_ai_analysis.json').replace('_summary.json', '_ai_analysis.json')
                        analysis_path = os.path.join(sessions_dir, analysis_file)
                        has_analysis = os.path.exists(analysis_path)
                        
                        session_info = {
                            'student_id': student_id,
                            'student_name': student['name'],
                            'student_grade': student['grade'],
                            'file': file,
                            'date': data.get('start_time', '').split('T')[0] if data.get('start_time') else 'Unknown',
                            'time': data.get('start_time', '').split('T')[1][:8] if data.get('start_time') and 'T' in data.get('start_time', '') else '',
                            'duration': data.get('duration_minutes', data.get('duration_seconds', 0) // 60 if data.get('duration_seconds') else 'Unknown'),
                            'type': 'VAPI Call' if 'vapi' in file else 'Regular Session',
                            'has_transcript': has_transcript,
                            'has_analysis': has_analysis,
                            'data': data
                        }
                        all_sessions.append(session_info)
                        
                    except Exception as e:
                        print(f"Error loading session file {file} for student {student_id}: {e}")
    
    # Sort by date and time (newest first)
    all_sessions.sort(key=lambda x: (x['date'], x['time']), reverse=True)
    
    # Calculate session statistics
    session_stats = {
        'total_sessions': len(all_sessions),
        'vapi_sessions': len([s for s in all_sessions if s['type'] == 'VAPI Call']),
        'regular_sessions': len([s for s in all_sessions if s['type'] == 'Regular Session']),
        'with_transcripts': len([s for s in all_sessions if s['has_transcript']]),
        'with_analysis': len([s for s in all_sessions if s['has_analysis']]),
        'total_students': len(students)
    }
    
    return render_template('all_sessions.html',
                         sessions=all_sessions,
                         session_stats=session_stats)

# Session and Assessment Viewer
@app.route('/admin/students/<student_id>/sessions')
def view_student_sessions(student_id):
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    student_data = get_student_data(student_id)
    if not student_data:
        flash(f'Student {student_id} not found', 'error')
        return redirect(url_for('admin_students'))
    
    sessions_dir = f'../data/students/{student_id}/sessions'
    sessions = []
    
    if os.path.exists(sessions_dir):
        for file in os.listdir(sessions_dir):
            if file.endswith('_session.json') or file.endswith('_summary.json'):
                file_path = os.path.join(sessions_dir, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Check if there's a corresponding transcript
                    transcript_file = file.replace('_session.json', '_transcript.txt').replace('_summary.json', '_transcript.txt')
                    transcript_path = os.path.join(sessions_dir, transcript_file)
                    has_transcript = os.path.exists(transcript_path)
                    
                    # Check if there's a corresponding AI analysis
                    analysis_file = file.replace('_session.json', '_ai_analysis.json').replace('_summary.json', '_ai_analysis.json')
                    analysis_path = os.path.join(sessions_dir, analysis_file)
                    has_analysis = os.path.exists(analysis_path)
                    
                    sessions.append({
                        'file': file,
                        'date': data.get('start_time', '').split('T')[0] if data.get('start_time') else 'Unknown',
                        'time': data.get('start_time', '').split('T')[1][:8] if data.get('start_time') and 'T' in data.get('start_time', '') else '',
                        'duration': data.get('duration_minutes', data.get('duration_seconds', 0) // 60 if data.get('duration_seconds') else 'Unknown'),
                        'type': 'VAPI Call' if 'vapi' in file else 'Regular Session',
                        'has_transcript': has_transcript,
                        'has_analysis': has_analysis,
                        'data': data
                    })
                except Exception as e:
                    print(f"Error loading session file {file}: {e}")
    
    # Sort by date (newest first)
    sessions.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template('session_list.html',
                         student=student_data.get('profile', {}),
                         student_id=student_id,
                         sessions=sessions)

@app.route('/admin/sessions/<student_id>/<session_file>')
def view_session_detail(student_id, session_file):
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    session_path = f'../data/students/{student_id}/sessions/{session_file}'
    if not os.path.exists(session_path):
        flash('Session file not found', 'error')
        return redirect(url_for('view_student_sessions', student_id=student_id))
    
    try:
        with open(session_path, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        # Load transcript if available
        transcript_file = session_file.replace('_session.json', '_transcript.txt').replace('_summary.json', '_transcript.txt')
        transcript_path = f'../data/students/{student_id}/sessions/{transcript_file}'
        transcript = None
        if os.path.exists(transcript_path):
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript = f.read()
        
        # Load AI analysis if available
        analysis_file = session_file.replace('_session.json', '_ai_analysis.json').replace('_summary.json', '_ai_analysis.json')
        analysis_path = f'../data/students/{student_id}/sessions/{analysis_file}'
        analysis = None
        if os.path.exists(analysis_path):
            with open(analysis_path, 'r', encoding='utf-8') as f:
                analysis = json.load(f)
        
        return render_template('session_detail.html',
                             student_id=student_id,
                             session_file=session_file,
                             session_data=session_data,
                             transcript=transcript,
                             analysis=analysis)
        
    except Exception as e:
        flash(f'Error loading session: {e}', 'error')
        return redirect(url_for('view_student_sessions', student_id=student_id))

# AI Post-Processing Routes (POC)
@app.route('/admin/ai-analysis')
def ai_analysis_dashboard():
    """AI Analysis POC Dashboard"""
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    if not AI_POC_AVAILABLE:
        flash('AI Post-Processing POC is not available', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Get provider status
    current_provider = provider_manager.get_current_provider()
    available_providers = provider_manager.get_available_providers()
    provider_info = {}
    
    for provider_name in available_providers:
        provider_info[provider_name] = provider_manager.get_provider_info(provider_name)
    
    # Get processing stats
    processing_stats = session_processor.get_processing_stats()
    
    return render_template('ai_analysis.html',
                         current_provider=current_provider,
                         available_providers=available_providers,
                         provider_info=provider_info,
                         processing_stats=processing_stats,
                         ai_poc_available=AI_POC_AVAILABLE)

@app.route('/admin/ai-analysis/switch-provider', methods=['POST'])
def switch_ai_provider():
    """Switch AI provider"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    if not AI_POC_AVAILABLE:
        return jsonify({'error': 'AI POC not available'}), 503
    
    new_provider = request.form.get('provider')
    
    if provider_manager.switch_provider(new_provider):
        flash(f'Successfully switched to {new_provider} provider', 'success')
        return jsonify({'success': True, 'message': f'Switched to {new_provider}'})
    else:
        return jsonify({'error': f'Provider {new_provider} not available'}), 400

@app.route('/admin/ai-analysis/test-sample', methods=['POST'])
def test_sample_analysis():
    """Test AI analysis with sample data"""
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    if not AI_POC_AVAILABLE:
        flash('AI POC not available', 'error')
        return redirect(url_for('ai_analysis_dashboard'))
    
    try:
        # Use the sample data from session_processor
        from ai_poc.session_processor import SAMPLE_TRANSCRIPT, SAMPLE_STUDENT_CONTEXT
        
        # Run async analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        analysis, validation = loop.run_until_complete(
            session_processor.process_session_transcript(
                transcript=SAMPLE_TRANSCRIPT,
                student_context=SAMPLE_STUDENT_CONTEXT,
                save_results=False
            )
        )
        
        loop.close()
        
        flash('Sample analysis completed successfully!', 'success')
        
        return render_template('ai_analysis_result.html',
                             analysis=analysis,
                             validation=validation,
                             transcript=SAMPLE_TRANSCRIPT,
                             student_context=SAMPLE_STUDENT_CONTEXT,
                             is_sample=True)
        
    except Exception as e:
        flash(f'Analysis failed: {str(e)}', 'error')
        return redirect(url_for('ai_analysis_dashboard'))

@app.route('/admin/ai-analysis/analyze-student/<student_id>')
def analyze_student_session(student_id):
    """Analyze a real student session"""
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    if not AI_POC_AVAILABLE:
        flash('AI POC not available', 'error')
        return redirect(url_for('ai_analysis_dashboard'))
    
    try:
        # Run async analysis for real student session
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        analysis, validation = loop.run_until_complete(
            session_processor.process_student_session_file(student_id)
        )
        
        loop.close()
        
        flash(f'Analysis completed for {student_id}!', 'success')
        
        return render_template('ai_analysis_result.html',
                             analysis=analysis,
                             validation=validation,
                             student_id=student_id,
                             is_sample=False)
        
    except FileNotFoundError as e:
        flash(f'Student session not found: {str(e)}', 'error')
        return redirect(url_for('ai_analysis_dashboard'))
    except Exception as e:
        flash(f'Analysis failed: {str(e)}', 'error')
        return redirect(url_for('ai_analysis_dashboard'))

@app.route('/admin/ai-analysis/reset-stats', methods=['POST'])
def reset_ai_stats():
    """Reset AI processing statistics"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    if not AI_POC_AVAILABLE:
        return jsonify({'error': 'AI POC not available'}), 503
    
    session_processor.reset_stats()
    flash('AI processing statistics reset', 'success')
    return jsonify({'success': True})

# API routes for AJAX requests
@app.route('/admin/api/stats')
def api_stats():
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    return jsonify(get_system_stats())

@app.route('/admin/api/ai-stats')
def api_ai_stats():
    """Get AI processing statistics"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    if not AI_POC_AVAILABLE:
        return jsonify({'error': 'AI POC not available'}), 503
    
    return jsonify(session_processor.get_processing_stats())

# VAPI Webhook Routes
def verify_vapi_signature(payload_body, signature, headers_info):
    """Verify VAPI webhook signature using HMAC"""
    # If VAPI secret is not configured, allow webhooks but log warning
    if VAPI_SECRET == 'your_vapi_secret_here':
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
            VAPI_SECRET.encode('utf-8'),
            payload_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        log_error('WEBHOOK', f"Error verifying VAPI signature: {str(e)}", e,
                 signature_length=len(signature) if signature else 0,
                 payload_size=len(payload_body))
        return False

@app.route('/vapi/webhook', methods=['POST'])
def vapi_webhook():
    """Handle VAPI webhook events for transcripts and call data"""
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
        
        # Verify signature (now more permissive)
        if not verify_vapi_signature(payload, signature, headers_info):
            log_webhook('SECURITY_FAILURE', 'VAPI webhook signature verification failed',
                       ip_address=request.remote_addr,
                       signature_provided=bool(signature),
                       payload_size=len(payload),
                       headers_info=headers_info)
            print(f"🚨 VAPI webhook signature verification failed")
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse the webhook data
        data = request.get_json()
        if not data:
            log_webhook('INVALID_PAYLOAD', 'VAPI webhook received empty or invalid payload',
                       ip_address=request.remote_addr,
                       payload_size=len(payload))
            return jsonify({'error': 'Invalid payload'}), 400
        
        # Debug logging to see the actual webhook structure
        log_webhook('webhook-structure-debug', f"Webhook data keys: {list(data.keys()) if isinstance(data, dict) else 'not-dict'}",
                   data_type=type(data).__name__,
                   data_preview=str(data)[:500])
        
        message = data.get('message', {})
        message_type = message.get('type')
        
        # More debug logging
        log_webhook('message-structure-debug', f"Message type: {type(message).__name__}, message_type: {message_type}",
                   message_keys=list(message.keys()) if isinstance(message, dict) else 'not-dict',
                   message_preview=str(message)[:200])
        
        log_webhook(message_type or 'unknown-event', f"VAPI webhook received: {message_type}",
                   ip_address=request.remote_addr,
                   call_id=message.get('call', {}).get('id') if isinstance(message, dict) else None,
                   payload_size=len(payload))
        print(f"📞 VAPI webhook received: {message_type}")
        
        if message_type == 'speech-update':
            handle_speech_update(message)
        elif message_type == 'conversation-update':
            handle_conversation_update(message)
        elif message_type == 'end-of-call-report':
            # Debug logging to see what we're actually getting
            log_webhook('end-of-call-debug', f"End-of-call message type: {type(message)}, content preview: {str(message)[:200]}",
                       call_id=message.get('call', {}).get('id') if isinstance(message, dict) else 'unknown',
                       message_type_received=type(message).__name__)
            handle_end_of_call(message)
        elif message_type == 'status-update':
            handle_status_update(message)
        else:
            log_webhook('UNHANDLED_EVENT', f"Unhandled VAPI event: {message_type}")
            print(f"📝 Unhandled VAPI event: {message_type}")
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        log_error('WEBHOOK', f"VAPI webhook error: {str(e)}", e,
                 ip_address=request.remote_addr,
                 payload_size=len(payload) if 'payload' in locals() else 0)
        print(f"❌ VAPI webhook error: {e}")
        return jsonify({'error': str(e)}), 500

def handle_speech_update(message):
    """Handle real-time speech updates from VAPI"""
    call_info = message.get('call', {})
    call_id = call_info.get('id')
    speaker = message.get('speaker')  # 'user' or 'assistant'
    text = message.get('text')
    is_final = message.get('final', False)
    
    if is_final and speaker == 'user':
        print(f"🗣️  Final user speech in call {call_id}: {text}")
        # Store partial transcript for potential real-time analysis
        # This could be used for live feedback or progress tracking

def handle_conversation_update(message):
    """Handle conversation updates from VAPI during active calls"""
    call_info = message.get('call', {})
    call_id = call_info.get('id')
    
    # Log conversation updates for debugging
    log_webhook('conversation-update', f"Conversation update for call {call_id}",
               call_id=call_id,
               update_type='conversation-update')
    
    print(f"💬 Conversation update for call {call_id}")
    # These are real-time updates during the call - we don't need to process them for student creation
    # Student creation happens in handle_end_of_call

def handle_status_update(message):
    """Handle call status updates from VAPI"""
    call_info = message.get('call', {})
    call_id = call_info.get('id')
    status = message.get('status')
    
    print(f"📊 Call {call_id} status: {status}")

def handle_end_of_call(message):
    """Handle complete call transcript from VAPI and trigger AI analysis"""
    try:
        # Handle case where message might be a string or dict
        if isinstance(message, str):
            log_error('WEBHOOK', f"handle_end_of_call received string instead of dict: {message}",
                     ValueError("Expected dict, got string"))
            return
        
        if not isinstance(message, dict):
            log_error('WEBHOOK', f"handle_end_of_call received invalid type: {type(message)}",
                     ValueError(f"Expected dict, got {type(message)}"))
            return
        
        call_info = message.get('call', {})
        call_id = call_info.get('id')
        assistant_id = call_info.get('assistantId')
        customer_phone = call_info.get('customer', {}).get('number')
        duration = message.get('durationSeconds', 0)
        
        # Get transcript
        transcript_data = message.get('transcript', {})
        user_transcript = transcript_data.get('user', '')
        assistant_transcript = transcript_data.get('assistant', '')
        
        log_webhook('end-of-call-report', f"Processing end of call {call_id}",
                   call_id=call_id,
                   phone=customer_phone,
                   duration_seconds=duration,
                   user_transcript_length=len(user_transcript),
                   assistant_transcript_length=len(assistant_transcript))
        
        print(f"📝 End of call {call_id}: {duration}s duration")
        print(f"📞 Phone: {customer_phone}")
        print(f"📄 User transcript: {len(user_transcript)} chars")
        print(f"🤖 Assistant transcript: {len(assistant_transcript)} chars")
        
        # Find student by phone number
        student_id = None
        if customer_phone:
            # Clean phone number (remove country codes, formatting)
            clean_phone = customer_phone.replace('+', '').replace('-', '').replace(' ', '')
            if clean_phone.startswith('1') and len(clean_phone) == 11:
                clean_phone = clean_phone[1:]  # Remove US country code
            
            # Look up student
            for phone, sid in phone_manager.phone_mapping.items():
                if phone.replace('-', '').replace(' ', '') == clean_phone:
                    student_id = sid
                    break
        
        if not student_id:
            log_webhook('student-not-found', f"No student found for phone: {customer_phone}",
                       call_id=call_id,
                       phone=customer_phone,
                       clean_phone=clean_phone if customer_phone else None,
                       level='WARNING')
            print(f"⚠️  No student found for phone: {customer_phone}")
            # Create unknown student record
            student_id = f"unknown_{clean_phone}" if customer_phone else f"unknown_{call_id}"
        else:
            log_webhook('student-identified', f"Student {student_id} identified for call {call_id}",
                       call_id=call_id,
                       student_id=student_id,
                       phone=customer_phone)
        
        # Save the session data
        save_vapi_session(call_id, student_id, customer_phone, duration,
                         user_transcript, assistant_transcript, message)
        
        # Trigger AI analysis if we have a valid student and transcript
        if student_id and user_transcript and AI_POC_AVAILABLE:
            try:
                trigger_ai_analysis_async(student_id, user_transcript, call_id)
            except Exception as e:
                log_error('WEBHOOK', f"AI analysis failed for call {call_id}", e,
                         call_id=call_id,
                         student_id=student_id)
                print(f"⚠️  AI analysis failed: {e}")
        
    except Exception as e:
        # Safely get call_id for error logging
        try:
            error_call_id = call_info.get('id') if 'call_info' in locals() and isinstance(call_info, dict) else None
        except:
            error_call_id = None
            
        log_error('WEBHOOK', f"Error handling end of call: {str(e)}", e,
                 call_id=error_call_id)
        print(f"❌ Error handling end of call: {e}")

def save_vapi_session(call_id, student_id, phone, duration, user_transcript, assistant_transcript, full_message):
    """Save VAPI session data to student directory"""
    try:
        # Create student directory if it doesn't exist
        student_dir = f'../data/students/{student_id}'
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
        
        print(f"💾 Saved VAPI session: {session_file}")
        
    except Exception as e:
        print(f"❌ Error saving VAPI session: {e}")

def trigger_ai_analysis_async(student_id, transcript, call_id):
    """Trigger AI analysis for VAPI transcript (async)"""
    if not AI_POC_AVAILABLE:
        log_ai_analysis("AI POC not available for analysis",
                       call_id=call_id,
                       student_id=student_id,
                       level='WARNING')
        return
    
    try:
        log_ai_analysis("Starting AI analysis for VAPI transcript",
                       call_id=call_id,
                       student_id=student_id,
                       transcript_length=len(transcript))
        
        # Get student context
        student_data = get_student_data(student_id)
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
        
        # Run async analysis in background
        def run_analysis():
            try:
                log_ai_analysis("Running AI analysis in background thread",
                               call_id=call_id,
                               student_id=student_id)
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                analysis, validation = loop.run_until_complete(
                    session_processor.process_session_transcript(
                        transcript=transcript,
                        student_context=student_context,
                        save_results=True,
                        session_id=call_id
                    )
                )
                
                loop.close()
                
                log_ai_analysis("AI analysis completed successfully",
                               call_id=call_id,
                               student_id=student_id,
                               analysis_summary=analysis.get('summary', 'No summary') if analysis else 'No analysis')
                print(f"✅ AI analysis completed for call {call_id}")
                
            except Exception as e:
                log_error('AI_ANALYSIS', f"AI analysis failed for call {call_id}", e,
                         call_id=call_id,
                         student_id=student_id)
                print(f"❌ AI analysis failed for call {call_id}: {e}")
        
        # Run in background thread to not block webhook response
        import threading
        thread = threading.Thread(target=run_analysis)
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        log_error('AI_ANALYSIS', f"Error triggering AI analysis for call {call_id}", e,
                 call_id=call_id,
                 student_id=student_id)
        print(f"❌ Error triggering AI analysis: {e}")

# System Logs Routes
@app.route('/admin/logs')
def admin_system_logs():
    """View system logs with filtering"""
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    # Get filter parameters
    days = int(request.args.get('days', 7))
    category = request.args.get('category', '')
    level = request.args.get('level', '')
    
    # Get logs
    logs = system_logger.get_logs(days=days, category=category, level=level)
    
    # Get log statistics
    log_stats = system_logger.get_log_statistics()
    
    # Get available categories and levels for filtering
    available_categories = list(log_stats.get('categories', {}).keys())
    available_levels = list(log_stats.get('levels', {}).keys())
    
    log_admin_action('view_logs', session.get('admin_username', 'unknown'),
                    days_filter=days,
                    category_filter=category,
                    level_filter=level,
                    log_count=len(logs))
    
    return render_template('system_logs.html',
                         logs=logs,
                         log_stats=log_stats,
                         available_categories=available_categories,
                         available_levels=available_levels,
                         current_filters={
                             'days': days,
                             'category': category,
                             'level': level
                         })

@app.route('/admin/logs/cleanup', methods=['POST'])
def cleanup_system_logs():
    """Manually trigger log cleanup"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    log_admin_action('manual_log_cleanup', session.get('admin_username', 'unknown'))
    
    try:
        cleanup_stats = system_logger.cleanup_old_logs()
        flash(f"Log cleanup completed: {cleanup_stats['deleted_files']} files deleted", 'success')
        return jsonify({'success': True, 'stats': cleanup_stats})
    except Exception as e:
        log_error('ADMIN', 'Manual log cleanup failed', e)
        return jsonify({'error': str(e)}), 500

# Periodic cleanup function
import threading
import time

def periodic_log_cleanup():
    """Run log cleanup every 24 hours"""
    while True:
        try:
            time.sleep(24 * 60 * 60)  # Wait 24 hours
            log_system("Running scheduled log cleanup")
            cleanup_stats = system_logger.cleanup_old_logs()
            log_system("Scheduled log cleanup completed", **cleanup_stats)
        except Exception as e:
            log_error('SYSTEM', 'Scheduled log cleanup failed', e)

# Start cleanup thread in production
if FLASK_ENV == 'production':
    cleanup_thread = threading.Thread(target=periodic_log_cleanup, daemon=True)
    cleanup_thread.start()
    log_system("Started periodic log cleanup thread")

if __name__ == '__main__':
    # Create required directories
    os.makedirs('../frontend/templates', exist_ok=True)
    os.makedirs('../frontend/static', exist_ok=True)
    
    # Get port from environment
    port = int(os.getenv('PORT', 5000))
    
    print("🖥️  AI Tutor Admin Dashboard Starting...")
    print(f"🔑 Admin login: {ADMIN_USERNAME} / {'[SECURE]' if ADMIN_PASSWORD != 'admin123' else 'admin123'}")
    print(f"📊 Dashboard: http://localhost:{port}/admin")
    
    if ADMIN_PASSWORD == 'admin123':
        print("⚠️  CHANGE DEFAULT PASSWORD IN PRODUCTION!")
    
    # Run initial cleanup
    try:
        cleanup_stats = system_logger.cleanup_old_logs()
        if cleanup_stats['deleted_files'] > 0:
            print(f"🧹 Initial cleanup: {cleanup_stats['deleted_files']} old log files removed")
    except Exception as e:
        print(f"⚠️  Initial cleanup failed: {e}")
    
    # Production vs Development settings
    if FLASK_ENV == 'production':
        print("🔒 Running in PRODUCTION mode")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("🛠️  Running in DEVELOPMENT mode")
        app.run(host='0.0.0.0', port=port, debug=True)