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
from typing import Dict, Any
from flask import Flask, render_template, session, redirect, request, flash, url_for, jsonify, send_file
import secrets

# Import database models and repositories
from app import db
from app.models.student import Student
from app.models.profile import Profile
from app.models.school import School
from app.models.curriculum import Curriculum
from app.models.session import Session
from app.models.assessment import Assessment
from app.repositories import student_repository, session_repository

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

# Import PhoneMappingManager from session-enhanced-server.py (robust path)
import importlib.util
script_dir = os.path.dirname(os.path.abspath(__file__))
ses_path = os.path.join(script_dir, "session-enhanced-server.py")
spec = importlib.util.spec_from_file_location("session_enhanced_server", ses_path)
session_enhanced_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(session_enhanced_server)

PhoneMappingManager = session_enhanced_server.PhoneMappingManager
SessionTracker = session_enhanced_server.SessionTracker

# Import System Logger
from system_logger import system_logger, log_admin_action, log_webhook, log_ai_analysis, log_error, log_system
from system_logger import SystemLogRepository

# Import VAPI Client
from vapi_client import vapi_client

# Import TokenService
try:
    from app.services.token_service import TokenService
    print("🔑 TokenService imported from app.services.token_service")
except ImportError:
    # Fallback to local implementation if module not found
    print("⚠️ TokenService module not found, using local implementation")
    from datetime import datetime, timedelta
    import secrets
    import uuid
    
    class TokenService:
        """Simple local implementation of TokenService for token management."""
        
        # Define available scopes and their descriptions
        AVAILABLE_SCOPES = {
            'api:read': 'Read access to API endpoints',
            'api:write': 'Write access to API endpoints',
            'logs:read': 'Read access to system logs',
            'mcp:access': 'Access to MCP server functionality',
            'admin:read': 'Read access to admin dashboard',
        }
        
        def __init__(self):
            """Initialize with empty tokens storage."""
            self.tokens = {}  # token_id -> token_data
        
        def generate_token(self, name="Debug Token", scopes=None, expiration_hours=4):
            """Generate a simple token with the given scopes and expiration."""
            if scopes is None:
                scopes = ['api:read']
                
            # Generate a token ID
            token_id = str(uuid.uuid4())
            
            # Generate a simple token
            token = secrets.token_urlsafe(32)
            
            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(hours=expiration_hours)
            
            # Store token data
            token_data = {
                'id': token_id,
                'token': token,
                'name': name,
                'scopes': scopes,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': expires_at.isoformat(),
                'is_active': True
            }
            
            self.tokens[token_id] = token_data
            
            return token_data
        
        def get_active_tokens(self):
            """Get all active tokens."""
            now = datetime.utcnow()
            active_tokens = []
            
            for token_id, token_data in self.tokens.items():
                if not token_data.get('is_active', False):
                    continue
                    
                # Parse expiration time
                expires_at = datetime.fromisoformat(token_data['expires_at'])
                
                # Check if token is expired
                if expires_at < now:
                    token_data['is_active'] = False
                    continue
                    
                # Add remaining time
                token_data['expires_in'] = (expires_at - now).total_seconds() // 60
                active_tokens.append(token_data)
                
            return active_tokens
        
        def revoke_token(self, token_id):
            """Revoke a token by ID."""
            if token_id in self.tokens:
                self.tokens[token_id]['is_active'] = False
                return True
            return False

# Token authentication decorator
def token_required(required_scopes=None):
    """
    Decorator for routes that require token authentication.
    Verifies the token and checks if it has the required scopes.
    
    Args:
        required_scopes: List of scopes required for this endpoint
    """
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing or invalid Authorization header'}), 401
            
            token = auth_header.split(' ')[1]
            
            # Verify token
            for token_id, token_data in token_service.tokens.items():
                if not token_data.get('is_active', False):
                    continue
                
                # Check if token matches
                if token_data.get('token') == token:
                    # Check if token is expired
                    expires_at = datetime.fromisoformat(token_data['expires_at'])
                    if expires_at < datetime.utcnow():
                        return jsonify({'error': 'Token expired'}), 401
                    
                    # Check if token has required scopes
                    if required_scopes:
                        token_scopes = token_data.get('scopes', [])
                        if not all(scope in token_scopes for scope in required_scopes):
                            return jsonify({'error': 'Token does not have required scopes'}), 403
                    
                    # Token is valid
                    return f(*args, **kwargs)
            
            # No matching token found
            return jsonify({'error': 'Invalid token'}), 401
        
        return decorated_function
    
    return decorator

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
token_service = TokenService()

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
    """Get list of all students from database"""
    try:
        # Get all students from repository
        students = student_repository.get_all()
        
        # Get phone mappings
        phone_mappings = phone_manager.load_phone_mapping()
        
        # Add phone numbers to students
        for student in students:
            student_id = str(student['id'])
            # Find phone number for this student
            phone = None
            for phone_num, sid in phone_mappings.items():
                if sid == student_id:
                    phone = phone_num
                    break
            student['phone'] = phone
            
            # Get session count
            student_sessions = session_repository.get_by_student_id(student_id)
            student['session_count'] = len(student_sessions)
        
        return sorted(students, key=lambda x: x.get('full_name', ''))
    except Exception as e:
        print(f"Error getting students from database: {e}")
        log_error('DATABASE', 'Error getting students', e)
        return []

def get_student_data(student_id):
    """Get detailed student data from database"""
    try:
        # Get student from repository
        student = student_repository.get_by_id(student_id)
        if not student:
            return None
        
        # Get student sessions
        sessions = session_repository.get_by_student_id(student_id)
        
        # Get student assessments
        assessments = Assessment.query.filter_by(student_id=student_id).all()
        assessments_data = [assessment.to_dict() for assessment in assessments]
        
        # Create student data object
        student_data = {
            'id': student_id,
            'profile': student,
            'progress': {
                'overall_progress': 0,  # Default value
                'subjects': {},
                'goals': [],
                'streak_days': 0,
                'last_updated': datetime.now().isoformat()
            },
            'assessment': assessments_data[0] if assessments_data else None,
            'sessions': sessions
        }
        
        # Sort sessions by start time (newest first)
        student_data['sessions'].sort(key=lambda x: x.get('start_datetime', ''), reverse=True)
        
        return student_data
    except Exception as e:
        print(f"Error getting student data from database: {e}")
        log_error('DATABASE', 'Error getting student data', e, student_id=student_id)
        return None

def get_system_stats():
    """Get system statistics for dashboard from database"""
    try:
        # Get counts from database
        total_students = Student.query.count()
        
        # Count sessions today
        today = datetime.now().date()
        sessions_today = Session.query.filter(
            Session.start_datetime >= today,
            Session.start_datetime < today + timedelta(days=1)
        ).count()
        
        # Get total sessions
        total_sessions = Session.query.count()
        
        # Get server status
        server_status = "Online"  # Assume online if we can query the database
        
        return {
            'total_students': total_students,
            'sessions_today': sessions_today,
            'total_sessions': total_sessions,
            'server_status': server_status,
            'phone_mappings': len(phone_manager.phone_mapping)
        }
    except Exception as e:
        print(f"Error getting system stats from database: {e}")
        log_error('DATABASE', 'Error getting system stats', e)
        return {
            'total_students': 0,
            'sessions_today': 0,
            'total_sessions': 0,
            'server_status': "Error",
            'phone_mappings': 0
        }

def get_all_schools():
    """Get list of all schools from database"""
    try:
        schools = School.query.all()
        return [school.to_dict() for school in schools]
    except Exception as e:
        print(f"Error getting schools from database: {e}")
        log_error('DATABASE', 'Error getting schools', e)
        return []

def save_school(school_data):
    """Save a school to the database"""
    try:
        # Check if school exists
        school = School.query.filter_by(id=school_data.get('id')).first()
        
        if school:
            # Update existing school
            for key, value in school_data.items():
                if hasattr(school, key):
                    setattr(school, key, value)
        else:
            # Create new school
            school = School(**school_data)
            db.session.add(school)
        
        db.session.commit()
        return school.to_dict()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving school to database: {e}")
        log_error('DATABASE', 'Error saving school', e)
        return None

def delete_school(school_id):
    """Delete a school from the database"""
    try:
        school = School.query.get(school_id)
        if school:
            db.session.delete(school)
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting school from database: {e}")
        log_error('DATABASE', 'Error deleting school', e)
        return False

def get_all_curriculums():
    """Get list of all curriculums from database"""
    try:
        curriculums = Curriculum.query.all()
        return [curriculum.to_dict() for curriculum in curriculums]
    except Exception as e:
        print(f"Error getting curriculums from database: {e}")
        log_error('DATABASE', 'Error getting curriculums', e)
        return []

def save_curriculum(curriculum_data):
    """Save a curriculum to the database"""
    try:
        # Check if curriculum exists
        curriculum = Curriculum.query.filter_by(id=curriculum_data.get('id')).first()
        
        if curriculum:
            # Update existing curriculum
            for key, value in curriculum_data.items():
                if hasattr(curriculum, key):
                    setattr(curriculum, key, value)
        else:
            # Create new curriculum
            curriculum = Curriculum(**curriculum_data)
            db.session.add(curriculum)
        
        db.session.commit()
        return curriculum.to_dict()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving curriculum to database: {e}")
        log_error('DATABASE', 'Error saving curriculum', e)
        return None

def delete_curriculum(curriculum_id):
    """Delete a curriculum from the database"""
    try:
        curriculum = Curriculum.query.get(curriculum_id)
        if curriculum:
            db.session.delete(curriculum)
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting curriculum from database: {e}")
        log_error('DATABASE', 'Error deleting curriculum', e)
        return False

def get_school_curriculums(school_id):
    """Get all curriculums for a specific school"""
    try:
        curriculums = Curriculum.query.filter_by(school_id=school_id).all()
        return [curriculum.to_dict() for curriculum in curriculums]
    except Exception as e:
        print(f"Error getting school curriculums from database: {e}")
        log_error('DATABASE', 'Error getting school curriculums', e)
        return []

def get_curriculum_by_id(curriculum_id):
    """Get a specific curriculum by ID"""
    try:
        curriculum = Curriculum.query.get(curriculum_id)
        return curriculum.to_dict() if curriculum else None
    except Exception as e:
        print(f"Error getting curriculum from database: {e}")
        log_error('DATABASE', 'Error getting curriculum', e)
        return None

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
    phone_mappings = dict(phone_manager.phone_mapping)
    students_info = {s['id']: s for s in get_all_students()}
    
    return render_template('dashboard.html',
                         stats=stats,
                         recent_students=recent_students,
                         phone_mappings=phone_mappings,
                         students_info=students_info)

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
    
    # Get phone number from the latest mapping
    phone = None
    current_mapping = phone_manager.load_phone_mapping()
    for phone_num, sid in current_mapping.items():
        if sid == student_id:
            phone = phone_num
            break
    
    # Extract data for template
    profile = student_data.get('profile', {})
    progress = student_data.get('progress', {})
    assessment = student_data.get('assessment', {})
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

# School management routes
@app.route('/admin/schools')
def admin_schools():
   if not check_auth():
       return redirect(url_for('admin_login'))
   
   schools = get_all_schools()
   return render_template('schools.html', schools=schools)

@app.route('/admin/schools/add', methods=['GET', 'POST'])
def add_school():
   if not check_auth():
       return redirect(url_for('admin_login'))
   
   if request.method == 'POST':
       try:
           # Create school data
           new_school = {
               "id": None,  # Auto-generated by database
               "name": request.form['name'],
               "country": request.form['country'] if 'country' in request.form else '',
               "city": request.form['city'] if 'city' in request.form else request.form.get('location', ''),
               "description": request.form['description'] if 'description' in request.form else request.form.get('background', '')
           }
           
           # Save to database
           saved_school = save_school(new_school)
           if not saved_school:
               flash('Error saving school to database', 'error')
               return render_template('add_school.html')
           
           flash('School added successfully!', 'success')
           
           # Redirect to curriculum management for this school
           return redirect(url_for('school_curriculum', school_id=saved_school['id']))
       
       except Exception as e:
           flash(f'Error adding school: {str(e)}', 'error')
           log_error('DATABASE', 'Error adding school', e)
           return render_template('add_school.html')
       
   return render_template('add_school.html')

@app.route('/admin/schools/edit/<school_id>', methods=['GET', 'POST'])
def edit_school(school_id):
   if not check_auth():
       return redirect(url_for('admin_login'))

   # Get school from database
   school = School.query.get(school_id)
   if not school:
       flash('School not found!', 'error')
       return redirect(url_for('admin_schools'))

   if request.method == 'POST':
       try:
           # Update school data
           school_data = {
               "id": school_id,
               "name": request.form['name'],
               "country": request.form['country'] if 'country' in request.form else '',
               "city": request.form['city'] if 'city' in request.form else request.form.get('location', ''),
               "description": request.form['description'] if 'description' in request.form else request.form.get('background', '')
           }
           
           # Save to database
           updated_school = save_school(school_data)
           if not updated_school:
               flash('Error updating school in database', 'error')
               return render_template('edit_school.html', school=school.to_dict())
           
           flash('School updated successfully!', 'success')
           
           # Redirect to curriculum management for this school
           return redirect(url_for('school_curriculum', school_id=school_id))
       
       except Exception as e:
           flash(f'Error updating school: {str(e)}', 'error')
           log_error('DATABASE', 'Error updating school', e, school_id=school_id)
           return render_template('edit_school.html', school=school.to_dict())

   return render_template('edit_school.html', school=school.to_dict())

@app.route('/admin/schools/delete/<school_id>', methods=['POST'])
def delete_school(school_id):
   if not check_auth():
       return redirect(url_for('admin_login'))
   
   try:
       # Delete school from database
       if delete_school(school_id):
           flash('School deleted successfully!', 'success')
       else:
           flash('Error deleting school from database', 'error')
   except Exception as e:
       flash(f'Error deleting school: {str(e)}', 'error')
       log_error('DATABASE', 'Error deleting school', e, school_id=school_id)
   
   return redirect(url_for('admin_schools'))

# Curriculum Management Routes
@app.route('/admin/curriculum')
def admin_curriculum():
    """View all curriculums"""
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    curriculums = get_all_curriculums()
    schools = get_all_schools()
    schools_dict = {s['school_id']: s for s in schools}
    
    return render_template('curriculum.html',
                          curriculums=curriculums,
                          schools=schools,
                          schools_dict=schools_dict)

@app.route('/admin/curriculum/add', methods=['GET', 'POST'])
def add_curriculum():
    """Add a new curriculum"""
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    schools = get_all_schools()
    
    if request.method == 'POST':
        try:
            school_id = request.form['school_id']
            
            # Validate school exists
            school = School.query.get(school_id)
            if not school:
                flash('School not found', 'error')
                return render_template('add_curriculum.html', schools=schools)
            
            # Create new curriculum
            new_curriculum = {
                'id': None,  # Auto-generated by database
                'school_id': int(school_id),
                'grade': int(request.form['grade']),
                'subject': request.form['subject'],
                'student_type': request.form['student_type'],
                'goals': request.form['goals']
            }
            
            # Save to database
            saved_curriculum = save_curriculum(new_curriculum)
            if not saved_curriculum:
                flash('Error saving curriculum to database', 'error')
                return render_template('add_curriculum.html', schools=schools)
            
            flash('Curriculum added successfully!', 'success')
            return redirect(url_for('admin_curriculum'))
        
        except Exception as e:
            flash(f'Error adding curriculum: {str(e)}', 'error')
            log_error('DATABASE', 'Error adding curriculum', e)
            return render_template('add_curriculum.html', schools=schools)
    
    return render_template('add_curriculum.html', schools=schools)

@app.route('/admin/curriculum/edit/<curriculum_id>', methods=['GET', 'POST'])
def edit_curriculum(curriculum_id):
    """Edit an existing curriculum"""
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    curriculum = get_curriculum_by_id(curriculum_id)
    if not curriculum:
        flash('Curriculum not found', 'error')
        return redirect(url_for('admin_curriculum'))
    
    schools = get_all_schools()
    
    if request.method == 'POST':
        try:
            # Update curriculum
            updated_curriculum = {
                'id': curriculum_id,
                'school_id': int(request.form['school_id']),
                'grade': int(request.form['grade']),
                'subject': request.form['subject'],
                'student_type': request.form['student_type'],
                'goals': request.form['goals']
            }
            
            # Save to database
            saved_curriculum = save_curriculum(updated_curriculum)
            if not saved_curriculum:
                flash('Error updating curriculum in database', 'error')
                return render_template('edit_curriculum.html', curriculum=curriculum, schools=schools)
            
            flash('Curriculum updated successfully!', 'success')
            return redirect(url_for('admin_curriculum'))
        
        except Exception as e:
            flash(f'Error updating curriculum: {str(e)}', 'error')
            log_error('DATABASE', 'Error updating curriculum', e, curriculum_id=curriculum_id)
            return render_template('edit_curriculum.html', curriculum=curriculum, schools=schools)
    
    return render_template('edit_curriculum.html',
                          curriculum=curriculum,
                          schools=schools)

@app.route('/admin/curriculum/delete/<curriculum_id>', methods=['POST'])
def delete_curriculum_route(curriculum_id):
    """Delete a curriculum"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Delete curriculum from database
        if delete_curriculum(curriculum_id):
            flash('Curriculum deleted successfully!', 'success')
        else:
            flash('Error deleting curriculum from database', 'error')
    except Exception as e:
        flash(f'Error deleting curriculum: {str(e)}', 'error')
        log_error('DATABASE', 'Error deleting curriculum', e, curriculum_id=curriculum_id)
    
    return redirect(url_for('admin_curriculum'))

@app.route('/admin/schools/<school_id>/curriculum')
def school_curriculum(school_id):
    """View curriculums for a specific school"""
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    school = next((s for s in get_all_schools() if s['school_id'] == school_id), None)
    if not school:
        flash('School not found', 'error')
        return redirect(url_for('admin_schools'))
    
    curriculums = get_school_curriculums(school_id)
    
    return render_template('school_curriculum.html',
                          school=school,
                          curriculums=curriculums)

# Database browser routes
@app.route('/admin/database')
def admin_database():
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    try:
        # Get counts of each model
        stats = {
            'students': Student.query.count(),
            'schools': School.query.count(),
            'curriculums': Curriculum.query.count(),
            'sessions': Session.query.count(),
            'assessments': Assessment.query.count()
        }
        
        # Get list of tables
        tables = [
            {'name': 'Students', 'count': stats['students'], 'url': url_for('admin_database_table', table='students')},
            {'name': 'Schools', 'count': stats['schools'], 'url': url_for('admin_database_table', table='schools')},
            {'name': 'Curriculums', 'count': stats['curriculums'], 'url': url_for('admin_database_table', table='curriculums')},
            {'name': 'Sessions', 'count': stats['sessions'], 'url': url_for('admin_database_table', table='sessions')},
            {'name': 'Assessments', 'count': stats['assessments'], 'url': url_for('admin_database_table', table='assessments')}
        ]
        
        return render_template('database.html',
                             tables=tables,
                             stats=stats)
    except Exception as e:
        flash(f'Error accessing database: {str(e)}', 'error')
        log_error('DATABASE', 'Error accessing database browser', e)
        return render_template('database.html', tables=[], stats={})

@app.route('/admin/database/<table>')
def admin_database_table(table):
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    try:
        # Get table data based on table name
        if table == 'students':
            items = Student.query.all()
            items = [item.to_dict() for item in items]
        elif table == 'schools':
            items = School.query.all()
            items = [item.to_dict() for item in items]
        elif table == 'curriculums':
            items = Curriculum.query.all()
            items = [item.to_dict() for item in items]
        elif table == 'sessions':
            items = Session.query.all()
            items = [item.to_dict() for item in items]
        elif table == 'assessments':
            items = Assessment.query.all()
            items = [item.to_dict() for item in items]
        else:
            flash(f'Unknown table: {table}', 'error')
            return redirect(url_for('admin_database'))
        
        # Get column names from first item
        columns = []
        if items:
            columns = list(items[0].keys())
        
        return render_template('database_table.html',
                             table_name=table,
                             items=items,
                             columns=columns)
    except Exception as e:
        flash(f'Error accessing table {table}: {str(e)}', 'error')
        log_error('DATABASE', f'Error accessing database table {table}', e)
        return render_template('database_table.html', table_name=table, items=[], columns=[])

@app.route('/admin/database/view/<table>/<item_id>')
def admin_database_view(table, item_id):
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    try:
        # Get item data based on table name and ID
        item = None
        if table == 'students':
            item = Student.query.get(item_id)
        elif table == 'schools':
            item = School.query.get(item_id)
        elif table == 'curriculums':
            item = Curriculum.query.get(item_id)
        elif table == 'sessions':
            item = Session.query.get(item_id)
        elif table == 'assessments':
            item = Assessment.query.get(item_id)
        
        if not item:
            flash(f'Item not found: {table}/{item_id}', 'error')
            return redirect(url_for('admin_database_table', table=table))
        
        # Convert to dictionary
        item_data = item.to_dict()
        
        # Format as JSON for display
        content = json.dumps(item_data, indent=2, ensure_ascii=False)
        
        return render_template('database_view.html',
                             table_name=table,
                             item_id=item_id,
                             content=content)
    except Exception as e:
        flash(f'Error viewing item {table}/{item_id}: {str(e)}', 'error')
        log_error('DATABASE', f'Error viewing database item {table}/{item_id}', e)
        return redirect(url_for('admin_database_table', table=table))

# System info route
@app.route('/admin/system')
def admin_system():
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    stats = get_system_stats()
    
    # Get the latest phone mappings from disk to ensure we have the most up-to-date data
    phone_mappings = dict(phone_manager.load_phone_mapping())
    
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
                         vapi_status=vapi_client.is_configured(),
                         system_events=[])

# Phone Mapping Management
@app.route('/admin/phone-mappings/remove', methods=['POST'])
def remove_phone_mapping():
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    phone_number = request.form.get('phone_number')
    if not phone_number:
        return jsonify({'error': 'Phone number is required'}), 400
    
    # Get the latest mapping from disk
    current_mapping = phone_manager.load_phone_mapping()
    
    if phone_number in current_mapping:
        # Update the in-memory mapping with the latest from disk
        phone_manager.phone_mapping = current_mapping
        # Remove the mapping
        del phone_manager.phone_mapping[phone_number]
        phone_manager.save_phone_mapping()
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
    
    # Use the add_phone_mapping method which handles loading the latest mapping
    phone_manager.add_phone_mapping(phone_number, student_id)
    
    flash(f'Phone mapping added: {phone_number} → {student_id}', 'success')
    return jsonify({'success': True, 'message': 'Phone mapping added'})

# Student CRUD Operations
@app.route('/admin/students/add', methods=['GET', 'POST'])
def add_student():
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    # Get schools for the dropdown
    schools = get_all_schools()
    
    if request.method == 'POST':
        try:
            # Get form data
            name_parts = request.form.get('name', '').split()
            first_name = name_parts[0] if name_parts else ''
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            age = request.form.get('age')
            grade = request.form.get('grade')
            phone = request.form.get('phone')
            school_id = request.form.get('school_id')
            interests = request.form.get('interests', '').split(',')
            interests = [i.strip() for i in interests if i.strip()]
            
            if not first_name or not age or not grade:
                flash('Name, age, and grade are required', 'error')
                return render_template('add_student.html', schools=schools)
            
            # Create student data
            student_data = {
                'first_name': first_name,
                'last_name': last_name,
                'date_of_birth': None,  # Calculate from age if needed
                'phone_number': phone,
                'student_type': 'International',  # Default value
                'school_id': int(school_id) if school_id else None,
                'interests': interests,
                'learning_preferences': []
            }
            
            # Create student in database
            new_student = student_repository.create(student_data)
            
            if not new_student:
                flash('Error creating student', 'error')
                return render_template('add_student.html', schools=schools)
            
            student_id = new_student['id']
            
            # Add phone mapping if provided
            if phone:
                phone_manager.phone_mapping[phone] = str(student_id)
                phone_manager.save_phone_mapping()
            
            flash(f'Student {first_name} {last_name} added successfully!', 'success')
            return redirect(url_for('admin_student_detail', student_id=student_id))
            
        except Exception as e:
            flash(f'Error creating student: {str(e)}', 'error')
            log_error('DATABASE', 'Error creating student', e)
            return render_template('add_student.html', schools=schools)
    
    return render_template('add_student.html', schools=schools)

@app.route('/admin/students/<student_id>/edit', methods=['GET', 'POST'])
def edit_student(student_id):
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    # Get schools for the dropdown
    schools = get_all_schools()
    
    # Get student data
    student = student_repository.get_by_id(student_id)
    if not student:
        flash(f'Student {student_id} not found', 'error')
        return redirect(url_for('admin_students'))
    
    if request.method == 'POST':
        try:
            # Get form data
            name_parts = request.form.get('name', '').split()
            first_name = name_parts[0] if name_parts else ''
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            age = request.form.get('age')
            grade = request.form.get('grade')
            phone = request.form.get('phone')
            school_id = request.form.get('school_id')
            interests = request.form.get('interests', '').split(',')
            interests = [i.strip() for i in interests if i.strip()]
            
            if not first_name or not age or not grade:
                flash('Name, age, and grade are required', 'error')
                return render_template('edit_student.html', student=student, student_id=student_id, phone=phone, schools=schools)
            
            # Update student data
            student_data = {
                'first_name': first_name,
                'last_name': last_name,
                'school_id': int(school_id) if school_id else None,
                'interests': interests
            }
            
            # Update student in database
            updated_student = student_repository.update(student_id, student_data)
            
            if not updated_student:
                flash('Error updating student', 'error')
                return render_template('edit_student.html', student=student, student_id=student_id, phone=phone, schools=schools)
            
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
            
            phone_manager.save_phone_mapping()
            
            flash(f'Student {first_name} {last_name} updated successfully!', 'success')
            return redirect(url_for('admin_student_detail', student_id=student_id))
            
        except Exception as e:
            flash(f'Error updating student: {str(e)}', 'error')
            log_error('DATABASE', 'Error updating student', e, student_id=student_id)
            return render_template('edit_student.html', student=student, student_id=student_id, phone=phone, schools=schools)
    
    # Get current phone from the latest mapping
    phone = None
    current_mapping = phone_manager.load_phone_mapping()
    for phone_num, sid in current_mapping.items():
        if sid == student_id:
            phone = phone_num
            break
    
    # Format student data for template
    student_display = {
        'name': f"{student.get('first_name', '')} {student.get('last_name', '')}".strip(),
        'age': student.get('age', ''),
        'grade': student.get('grade', ''),
        'interests': student.get('interests', []),
        'learning_preferences': student.get('learning_preferences', []),
        'school_id': student.get('school_id', '')
    }
    
    return render_template('edit_student.html',
                         student=student_display,
                         student_id=student_id,
                         phone=phone,
                         schools=schools)

@app.route('/admin/students/<student_id>/delete', methods=['POST'])
def delete_student(student_id):
    """Delete a student and all associated data from database"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get student for logging
        student = student_repository.get_by_id(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        student_name = f"{student.get('first_name', '')} {student.get('last_name', '')}".strip()
        
        # Remove phone mapping for this student
        phone_to_remove = None
        current_mapping = phone_manager.load_phone_mapping()
        
        for phone_num, sid in list(current_mapping.items()):
            if sid == student_id:
                phone_to_remove = phone_num
                # Update the in-memory mapping with the latest from disk
                phone_manager.phone_mapping = current_mapping
                del phone_manager.phone_mapping[phone_num]
                break
        
        if phone_to_remove:
            phone_manager.save_phone_mapping()
        
        # Delete student from database
        if student_repository.delete(student_id):
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
        else:
            return jsonify({'error': 'Failed to delete student from database'}), 500
        
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
    
    try:
        # Get all sessions from database
        all_sessions = session_repository.get_all()
        
        # Get all students for additional information
        students = get_all_students()
        students_dict = {s['id']: s for s in students}
        
        # Enhance session data with student information
        for session in all_sessions:
            student_id = session.get('student_id')
            student = students_dict.get(student_id, {})
            
            session['student_name'] = student.get('full_name', 'Unknown')
            session['student_grade'] = student.get('grade', 'Unknown')
            
            # Format date and time
            start_datetime = session.get('start_datetime', '')
            if start_datetime:
                if isinstance(start_datetime, str) and 'T' in start_datetime:
                    session['date'] = start_datetime.split('T')[0]
                    session['time'] = start_datetime.split('T')[1][:8]
                else:
                    session['date'] = str(start_datetime).split(' ')[0]
                    session['time'] = str(start_datetime).split(' ')[1][:8] if ' ' in str(start_datetime) else ''
            else:
                session['date'] = 'Unknown'
                session['time'] = ''
            
            # Set session type
            session['type'] = 'VAPI Call' if session.get('session_type') == 'phone' else 'Regular Session'
            
            # Set duration
            session['duration'] = session.get('duration_minutes', session.get('duration', 0) // 60 if session.get('duration') else 'Unknown')
            
            # Set transcript and analysis flags
            session['has_transcript'] = bool(session.get('transcript'))
            session['has_analysis'] = False  # Set based on your database schema
        
        # Sort by date and time (newest first)
        all_sessions.sort(key=lambda x: (x.get('date', ''), x.get('time', '')), reverse=True)
        
        # Calculate session statistics
        session_stats = {
            'total_sessions': len(all_sessions),
            'vapi_sessions': len([s for s in all_sessions if s.get('type') == 'VAPI Call']),
            'regular_sessions': len([s for s in all_sessions if s.get('type') == 'Regular Session']),
            'with_transcripts': len([s for s in all_sessions if s.get('has_transcript')]),
            'with_analysis': len([s for s in all_sessions if s.get('has_analysis')]),
            'total_students': len(students)
        }
        
        return render_template('all_sessions.html',
                             sessions=all_sessions,
                             session_stats=session_stats)
    
    except Exception as e:
        flash(f'Error loading sessions: {str(e)}', 'error')
        log_error('DATABASE', 'Error loading all sessions', e)
        return render_template('all_sessions.html', sessions=[], session_stats={})

# Session and Assessment Viewer
@app.route('/admin/students/<student_id>/sessions')
def view_student_sessions(student_id):
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    try:
        # Get student data
        student_data = get_student_data(student_id)
        if not student_data:
            flash(f'Student {student_id} not found', 'error')
            return redirect(url_for('admin_students'))
        
        # Get sessions for this student from database
        sessions = session_repository.get_by_student_id(student_id)
        
        # Format session data for template
        for session in sessions:
            # Format date and time
            start_datetime = session.get('start_datetime', '')
            if start_datetime:
                if isinstance(start_datetime, str) and 'T' in start_datetime:
                    session['date'] = start_datetime.split('T')[0]
                    session['time'] = start_datetime.split('T')[1][:8]
                else:
                    session['date'] = str(start_datetime).split(' ')[0]
                    session['time'] = str(start_datetime).split(' ')[1][:8] if ' ' in str(start_datetime) else ''
            else:
                session['date'] = 'Unknown'
                session['time'] = ''
            
            # Set session type
            session['type'] = 'VAPI Call' if session.get('session_type') == 'phone' else 'Regular Session'
            
            # Set duration
            session['duration'] = session.get('duration_minutes', session.get('duration', 0) // 60 if session.get('duration') else 'Unknown')
            
            # Set transcript and analysis flags
            session['has_transcript'] = bool(session.get('transcript'))
            session['has_analysis'] = False  # Set based on your database schema
            
            # Set file name for compatibility with template
            session['file'] = f"session_{session.get('id')}"
        
        # Sort by date (newest first)
        sessions.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return render_template('session_list.html',
                             student=student_data.get('profile', {}),
                             student_id=student_id,
                             sessions=sessions)
    
    except Exception as e:
        flash(f'Error loading sessions: {str(e)}', 'error')
        log_error('DATABASE', 'Error loading student sessions', e, student_id=student_id)
        return render_template('session_list.html', student={}, student_id=student_id, sessions=[])

@app.route('/admin/sessions/<student_id>/<session_id>')
def view_session_detail(student_id, session_id):
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    try:
        # Get session from database
        session_data = session_repository.get_by_id(session_id)
        if not session_data:
            flash('Session not found', 'error')
            return redirect(url_for('view_student_sessions', student_id=student_id))
        
        # Get transcript from session data
        transcript = session_data.get('transcript')
        
        # Get analysis if available (implement based on your database schema)
        analysis = None
        
        return render_template('session_detail.html',
                             student_id=student_id,
                             session_file=f"session_{session_id}",  # For compatibility with template
                             session_data=session_data,
                             transcript=transcript,
                             analysis=analysis)
        
    except Exception as e:
        flash(f'Error loading session: {str(e)}', 'error')
        log_error('DATABASE', 'Error loading session detail', e, student_id=student_id, session_id=session_id)
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

@app.route('/api/v1/logs', methods=['GET'])
@token_required(['logs:read'])
def get_logs_api():
    """API endpoint to retrieve logs from the database"""
    try:
        # Get query parameters
        date = request.args.get('date')
        level = request.args.get('level')
        category = request.args.get('category')
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 100))
        
        # Use the system_logger directly instead of creating a new repository
        if date:
            # Parse date string to date object
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                # For date-specific queries, we need to use the repository
                log_repository = SystemLogRepository(db.session)
                logs = log_repository.get_logs_by_date(date_obj, category, level)
                # Convert logs to dictionaries
                log_dicts = [log.to_dict() for log in logs]
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }), 400
        else:
            # Get logs for the specified number of days using system_logger
            log_dicts = system_logger.get_logs(days, category, level, limit)
        
        return jsonify({
            'success': True,
            'data': {
                'count': len(log_dicts),
                'logs': log_dicts
            }
        })
        
    except Exception as e:
        log_error('API', 'Error retrieving logs', e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
    """Save VAPI session data to database"""
    try:
        # Combine transcripts
        combined_transcript = f"=== VAPI Call Transcript ===\n"
        combined_transcript += f"Call ID: {call_id}\n"
        combined_transcript += f"Duration: {duration} seconds\n"
        combined_transcript += f"Phone: {phone}\n"
        combined_transcript += f"Timestamp: {datetime.now().isoformat()}\n\n"
        combined_transcript += f"=== User Transcript ===\n{user_transcript}\n\n"
        combined_transcript += f"=== Assistant Transcript ===\n{assistant_transcript}\n"
        
        # Create session data for database
        session_data = {
            'student_id': student_id,
            'call_id': call_id,
            'session_type': 'phone',
            'start_datetime': datetime.now().isoformat(),
            'duration': duration,
            'transcript': combined_transcript,
            'summary': ''  # No summary available from webhook
        }
        
        # Save session to database
        new_session = session_repository.create(session_data)
        
        if not new_session:
            log_error('DATABASE', f"Failed to create session in database", ValueError("Database operation failed"),
                     call_id=call_id, student_id=student_id)
            print(f"❌ Failed to save session to database")
            return
        
        # Analyze transcript and update student profile
        if user_transcript:
            try:
                from transcript_analyzer import TranscriptAnalyzer
                analyzer = TranscriptAnalyzer()
                # Use only the user transcript for profile extraction
                extracted_info = analyzer.analyze_transcript(user_transcript, student_id)
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
        
        print(f"💾 Saved VAPI session to database: {new_session.get('id')}")
        
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
    
    # The phone manager now handles normalization and ensures fresh data
    student_id = phone_manager.get_student_by_phone(clean_phone)
    if student_id:
        log_webhook('student-identified', f"Found student {student_id}",
                   call_id=call_id, student_id=student_id, phone=clean_phone)
        return student_id
    
    # Create new student if not found
    log_webhook('student-not-found', f"No student found for phone: {clean_phone}",
               call_id=call_id, phone=clean_phone)
    
    # Pass the normalized phone to create_student_from_call
    new_student_id = create_student_from_call(clean_phone, call_id)
    log_webhook('student-created', f"Created new student {new_student_id}",
               call_id=call_id, student_id=new_student_id, phone=clean_phone)
    
    return new_student_id

def create_student_from_call(phone: str, call_id: str) -> str:
    """Create a new student from phone call data using database"""
    try:
        # Ensure phone is normalized for consistent lookup and storage
        normalized_phone = normalize_phone_number(phone)
        
        # Use last 4 digits of normalized phone for name creation
        phone_suffix = normalized_phone[-4:] if normalized_phone else ""
        first_name = f"Student"
        last_name = phone_suffix if phone else f"Unknown_{call_id[-6:]}"
        
        # Create student data
        student_data = {
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': None,
            'phone_number': normalized_phone,
            'student_type': 'International',  # Default value
            'school_id': None,
            'interests': [],
            'learning_preferences': []
        }
        
        # Create student in database
        new_student = student_repository.create(student_data)
        
        if not new_student:
            log_error('DATABASE', f"Failed to create student in database", ValueError("Database operation failed"),
                     call_id=call_id, phone=normalized_phone)
            # Return a temporary ID for fallback
            return f"temp_{call_id[-6:]}"
        
        student_id = str(new_student['id'])
        
        # Add phone mapping using normalized phone number
        if normalized_phone:
            # Log the exact phone number being mapped for debugging
            log_webhook('phone-mapping', f"Adding phone mapping: {normalized_phone} → {student_id}",
                        phone=normalized_phone, student_id=student_id)
            phone_manager.add_phone_mapping(normalized_phone, student_id)
        
        return student_id
        
    except Exception as e:
        log_error('DATABASE', f"Error creating student from call", e,
                 call_id=call_id, phone=phone)
        # Return a temporary ID for fallback
        return f"temp_{call_id[-6:]}"

def save_api_driven_session(call_id: str, student_id: str, phone: str,
                            duration: int, transcript: str, call_data: Dict[Any, Any]):
    """Save VAPI session data using API-fetched data to database"""
    try:
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
        
        # Prepare session data for database
        session_data = {
            'student_id': student_id,
            'call_id': call_id,
            'session_type': 'phone',
            'start_datetime': metadata.get('created_at', datetime.now().isoformat()),
            'duration': effective_duration,
            'transcript': transcript,
            'summary': metadata.get('analysis_summary', '')
        }
        
        # Save session to database
        new_session = session_repository.create(session_data)
        
        if not new_session:
            log_error('DATABASE', f"Failed to create session in database", ValueError("Database operation failed"),
                     call_id=call_id, student_id=student_id)
            print(f"❌ Failed to save session to database")
            return
        
        # Always analyze transcript for profile information if there's content
        if transcript and len(transcript) > 100:  # Only analyze if there's meaningful content
            try:
                from transcript_analyzer import TranscriptAnalyzer
                analyzer = TranscriptAnalyzer()
                log_webhook('transcript-analysis-start', f"Starting transcript analysis for profile extraction",
                            call_id=call_id, student_id=student_id,
                            transcript_length=len(transcript))
                print(f"🔍 Analyzing transcript for student {student_id} profile information...")
                
                extracted_info = analyzer.analyze_transcript(transcript, student_id)
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
        
        print(f"💾 Saved API-driven session to database: {new_session.get('id')}")
        log_webhook('session-saved', f"Saved session for call {call_id}",
                    call_id=call_id,
                    student_id=student_id,
                    session_id=new_session.get('id'),
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
                from transcript_analyzer import TranscriptAnalyzer
                analyzer = TranscriptAnalyzer()
                log_webhook('transcript-analysis-start', f"Starting webhook transcript analysis for profile extraction",
                           call_id=call_id, student_id=student_id,
                           transcript_length=len(combined_transcript))
                print(f"🔍 Analyzing webhook transcript for student {student_id} profile information...")
                
                extracted_info = analyzer.analyze_transcript(combined_transcript, student_id)
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
                
                # Construct the correct path for the analysis results
                analysis_filename = f"ai_analysis_{call_id}.json"
                analysis_path = os.path.join('../data/students', student_id, 'sessions', analysis_filename)

                analysis, validation = loop.run_until_complete(
                    session_processor.process_session_transcript(
                        transcript=transcript,
                        student_context=student_context,
                        save_results=True,
                        session_file_path=analysis_path
                    )
                )
                
                loop.close()
                
                log_ai_analysis("AI analysis completed successfully",
                               call_id=call_id,
                               student_id=student_id,
                               analysis_summary=analysis.conceptual_understanding if analysis else 'No analysis')
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
    
    try:
        # Use the system_logger directly instead of creating a new repository
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
    except Exception as e:
        flash(f'Error retrieving logs: {str(e)}', 'error')
        log_error('DATABASE', 'Error retrieving logs', e)
        return render_template('system_logs.html',
                            logs=[],
                            log_stats={},
                            available_categories=[],
                            available_levels=[],
                            current_filters={
                                'days': days,
                                'category': category,
                                'level': level
                            })

@app.route('/admin/logs/export')
def export_logs():
    """Export logs as JSON file"""
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    try:
        # Get filter parameters
        days = int(request.args.get('days', 7))
        category = request.args.get('category', '')
        level = request.args.get('level', '')
        
        # Use the system_logger directly
        logs_dict = system_logger.get_logs(days=days, category=category, level=level)
        
        # Create a temporary file
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_file.write(json.dumps(logs_dict, indent=2).encode('utf-8'))
        temp_file.close()
        
        # Log the export
        log_admin_action('export_logs', session.get('admin_username', 'unknown'),
                        days_filter=days,
                        category_filter=category,
                        level_filter=level,
                        log_count=len(logs_dict))
        
        # Send the file
        return send_file(temp_file.name,
                        as_attachment=True,
                        download_name=f'logs_{datetime.now().strftime("%Y-%m-%d")}.json')
    except Exception as e:
        flash(f'Error exporting logs: {str(e)}', 'error')
        log_error('DATABASE', 'Error exporting logs', e)
        return redirect(url_for('admin_system_logs'))


@app.route('/admin/logs/cleanup', methods=['POST'])
def cleanup_system_logs():
    """Manually trigger log cleanup"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    log_admin_action('manual_log_cleanup', session.get('admin_username', 'unknown'))
    
    try:
        # Import and use the Celery task for log cleanup
        from app.tasks.maintenance_tasks import cleanup_old_logs
        from app.config import Config
        
        # Run cleanup task directly (not as a Celery task)
        deleted_count = cleanup_old_logs(days=Config.LOG_RETENTION_DAYS)
        
        flash(f"Log cleanup completed: {deleted_count} log entries deleted", 'success')
        return jsonify({'success': True, 'stats': {'deleted_entries': deleted_count}})
    except Exception as e:
        log_error('ADMIN', 'Manual log cleanup failed', e)
        return jsonify({'error': str(e)}), 500

# Token Management Routes
@app.route('/admin/tokens')
def admin_tokens():
    """Token generation page for debugging and testing"""
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    # Get active tokens
    active_tokens = token_service.get_active_tokens()
    
    return render_template('admin/generate_token.html',
                         active_tokens=active_tokens)

@app.route('/admin/tokens/generate', methods=['POST'])
def generate_token():
    """Generate a new access token"""
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    # Get form data
    token_name = request.form.get('token_name', 'Unnamed Token')
    scopes = request.form.getlist('scopes')
    expiration_hours = int(request.form.get('expiration', 4))
    
    if not scopes:
        flash('At least one scope must be selected', 'error')
        return redirect(url_for('admin_tokens'))
    
    # Generate token
    token_data = token_service.generate_token(
        name=token_name,
        scopes=scopes,
        expiration_hours=expiration_hours
    )
    
    log_admin_action('generate_token', session.get('admin_username', 'unknown'),
                    token_name=token_name,
                    scopes=scopes,
                    expiration_hours=expiration_hours,
                    token_id=token_data['id'])
    
    flash('Token generated successfully', 'success')
    
    # Get active tokens for display
    active_tokens = token_service.get_active_tokens()
    
    return render_template('admin/generate_token.html',
                         token=token_data['token'],
                         token_name=token_name,
                         token_scopes=scopes,
                         token_expires=token_data['expires_at'],
                         active_tokens=active_tokens)

@app.route('/admin/tokens/revoke/<token_id>', methods=['POST'])
def revoke_token(token_id):
    """Revoke an access token"""
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    # Revoke token
    if token_service.revoke_token(token_id):
        log_admin_action('revoke_token', session.get('admin_username', 'unknown'),
                        token_id=token_id)
        flash('Token revoked successfully', 'success')
    else:
        flash('Token not found or already revoked', 'error')
    
    return redirect(url_for('admin_tokens'))

# Periodic cleanup function
import threading
import time

def periodic_log_cleanup():
    """Run log cleanup every 24 hours"""
    while True:
        try:
            time.sleep(24 * 60 * 60)  # Wait 24 hours
            log_system("Running scheduled log cleanup")
            
            # Import and use the Celery task for log cleanup
            from app.tasks.maintenance_tasks import cleanup_old_logs
            deleted_count = cleanup_old_logs.delay(days=Config.LOG_RETENTION_DAYS).get()
            
            log_system("Scheduled log cleanup completed", deleted_entries=deleted_count)
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
    
    # Initialize database
    try:
        # Create database tables if they don't exist
        db.create_all()
        print("🗄️  Database tables created/verified")
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
    
    # Run initial cleanup
    try:
        # Import and use the Celery task for log cleanup
        from app.tasks.maintenance_tasks import cleanup_old_logs
        from app.config import Config
        
        # Run cleanup task directly (not as a Celery task)
        deleted_count = cleanup_old_logs(days=Config.LOG_RETENTION_DAYS)
        
        if deleted_count > 0:
            print(f"🧹 Initial cleanup: {deleted_count} old log entries removed")
    except Exception as e:
        print(f"⚠️  Initial cleanup failed: {e}")
    
    # Production vs Development settings
    if FLASK_ENV == 'production':
        print("🔒 Running in PRODUCTION mode")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("🛠️  Running in DEVELOPMENT mode")
        app.run(host='0.0.0.0', port=port, debug=True)