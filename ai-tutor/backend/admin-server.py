#!/usr/bin/env python3
"""
AI Tutor Admin Dashboard
Flask web interface for managing students, sessions, and system data
"""

import os
import json
import hashlib
import hmac
import re
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

# Create Flask app directly
app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

# Security Configuration with Environment Variables
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')  # Default for development only
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
FLASK_ENV = os.getenv('FLASK_ENV', 'development')

# Set SQLAlchemy configuration
# Get database URL from environment variable, with a fallback for local development
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("⚠️ DATABASE_URL environment variable not found. Using default SQLite database.")
    print("⚠️ This is only for local development. In production, set DATABASE_URL to a PostgreSQL connection string.")
    log_system("DATABASE_URL environment variable not found", level="ERROR")
    
    # In production, we should never use SQLite
    if FLASK_ENV == 'production':
        print("🚨 CRITICAL ERROR: Running in production mode but DATABASE_URL is not set!")
        print("🚨 PostgreSQL is required for production. SQLite should not be used.")
        log_system("Production environment detected but DATABASE_URL not set", level="CRITICAL")
        # Still use SQLite as fallback to allow startup, but log the error
    
    database_url = 'sqlite:///:memory:'  # Fallback to in-memory SQLite for local development
else:
    print(f"🗄️ Using database URL from environment: {database_url[:10]}...")
    # Ensure the URL starts with postgresql:// (Render might provide postgres://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        print("🔄 Converted postgres:// to postgresql:// in database URL")
    
    # Verify this is a PostgreSQL URL in production
    if FLASK_ENV == 'production' and not database_url.startswith('postgresql://'):
        print(f"🚨 WARNING: Production environment but DATABASE_URL doesn't start with postgresql://")
        print(f"🚨 Current prefix: {database_url.split('://')[0] if '://' in database_url else 'unknown'}://")
        log_system(f"Invalid DATABASE_URL format in production",
                  prefix=database_url.split('://')[0] if '://' in database_url else 'unknown',
                  level="WARNING")

# Log the database configuration
log_system("Database configuration",
          database_type=database_url.split('://')[0] if '://' in database_url else 'unknown',
          is_production=(FLASK_ENV == 'production'),
          flask_env=FLASK_ENV)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
try:
    db.init_app(app)
    print("🗄️ Database initialized with app")
    
    # Create database tables if they don't exist
    with app.app_context():
        # Check if we're using SQLite (development) or PostgreSQL (production)
        if database_url.startswith('sqlite'):
            # For SQLite, we can use create_all() directly
            db.create_all()
            print("🗄️ Database tables created using create_all() (SQLite)")
        else:
            # For PostgreSQL, we should use migrations
            try:
                # Import Flask-Migrate components
                from flask_migrate import Migrate, upgrade
                
                # Initialize Flask-Migrate
                migrate = Migrate(app, db)
                
                # Check if migrations directory exists
                migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../migrations')
                if not os.path.exists(migrations_dir):
                    print("⚠️ Migrations directory not found, creating initial migration")
                    # Import commands to create initial migration
                    from flask_migrate import init, migrate as migrate_cmd
                    
                    # Initialize migrations
                    init(directory=migrations_dir)
                    
                    # Create initial migration
                    with app.app_context():
                        migrate_cmd(directory=migrations_dir, message="Initial migration")
                
                # Run migrations
                print("🗄️ Running database migrations")
                upgrade(directory=migrations_dir)
                print("🗄️ Database migrations completed")
            except ImportError:
                print("⚠️ Flask-Migrate not installed, falling back to create_all()")
                # Fallback to create_all if Flask-Migrate is not available
                db.create_all()
                print("🗄️ Database tables created using create_all() (fallback)")
            except Exception as migration_error:
                print(f"⚠️ Error running migrations: {migration_error}")
                print("⚠️ Falling back to create_all()")
                # Fallback to create_all if migrations fail
                db.create_all()
                print("🗄️ Database tables created using create_all() (fallback)")
        
        print("🗄️ Database tables created/verified")
except Exception as e:
    print(f"⚠️ Error initializing database with app: {e}")

# VAPI Configuration
VAPI_SECRET = os.getenv('VAPI_SECRET', 'your_vapi_secret_here')

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
        
        # Get phone mappings with error handling
        try:
            # Try to get phone mappings from memory first
            phone_mappings = dict(phone_manager.phone_mapping)
        except Exception as e:
            # If that fails, try to load from disk
            try:
                phone_mappings = phone_manager.load_phone_mapping()
            except Exception as load_error:
                # If both fail, use an empty dictionary
                log_error('DATABASE', f'Error loading phone mappings for students: {str(load_error)}', load_error)
                print(f"⚠️ Error loading phone mappings: {load_error}")
                phone_mappings = {}
        
        # Add phone numbers to students with error handling
        for student in students:
            try:
                student_id = str(student['id'])
                # Find phone number for this student
                phone = None
                for phone_num, sid in phone_mappings.items():
                    if sid == student_id:
                        phone = phone_num
                        break
                student['phone'] = phone
            except Exception as e:
                log_error('DATABASE', f'Error processing phone mapping for student', e, student_id=student.get('id'))
                student['phone'] = None
            
            # Get session count
            student_sessions = session_repository.get_by_student_id(student_id)
            student['session_count'] = len(student_sessions)
            
            # Create display name for templates
            first_name = student.get('first_name', '')
            last_name = student.get('last_name', '')
            student['display_name'] = f"{first_name} {last_name}".strip() or 'Unknown'
        
        # Sort by ID (most recent first) instead of name
        return sorted(students, key=lambda x: x.get('id', 0), reverse=True)
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
        # Get counts from database - ensure we're in an app context
        # for all database operations
        total_students = 0
        sessions_today = 0
        total_sessions = 0
        
        # Count students
        try:
            total_students = Student.query.count()
        except Exception as e:
            log_error('DATABASE', 'Error counting students', e)
        
        # Count sessions today - handle datetime format issues
        try:
            today = datetime.now().date()
            today_str = today.isoformat()
            
            # Try multiple approaches to filter by date
            try:
                # First try with string comparison (most reliable with SQL)
                sessions_today = Session.query.filter(
                    Session.start_datetime.like(f"{today_str}%")
                ).count()
                
                # If no results, try with datetime objects
                if sessions_today == 0:
                    # Convert strings to datetime objects for comparison
                    today_start = datetime.combine(today, datetime.min.time())
                    today_end = datetime.combine(today, datetime.max.time())
                    
                    sessions_today = Session.query.filter(
                        Session.start_datetime >= today_start.isoformat(),
                        Session.start_datetime <= today_end.isoformat()
                    ).count()
                    
                    if sessions_today > 0:
                        log_system('Used datetime object comparison for sessions_today', count=sessions_today)
            except Exception as date_error:
                # Last resort: manual filtering
                log_error('DATABASE', 'Using manual filtering for sessions_today', date_error)
                all_sessions = Session.query.all()
                sessions_today = 0
                
                for session in all_sessions:
                    try:
                        session_date_str = str(session.start_datetime).split('T')[0].split(' ')[0]
                        if session_date_str == today_str:
                            sessions_today += 1
                    except:
                        pass
        except Exception as e:
            log_error('DATABASE', 'Error counting sessions today', e)
        
        # Get total sessions
        try:
            total_sessions = Session.query.count()
        except Exception as e:
            log_error('DATABASE', 'Error counting total sessions', e)
        
        # Get server status
        server_status = "Online"  # Assume online if we can query the database
        
        # Get phone mappings count with error handling
        try:
            phone_mappings_count = len(phone_manager.phone_mapping) if hasattr(phone_manager, 'phone_mapping') else 0
        except Exception as e:
            log_error('DATABASE', 'Error counting phone mappings', e)
            phone_mappings_count = 0
        
        return {
            'total_students': total_students,
            'sessions_today': sessions_today,
            'total_sessions': total_sessions,
            'server_status': server_status,
            'phone_mappings': phone_mappings_count
        }
    except Exception as e:
        print(f"Error getting system stats from database: {e}")
        log_error('DATABASE', 'Error getting system stats', e)
        return {
            'total_students': 0,
            'sessions_today': 0,
            'total_sessions': 0,
            'server_status': "Error",
            'phone_mappings': 0  # Default to 0 on error
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

@app.route('/health')
def health_check():
    """Enhanced health check that provides detailed information about the database connection"""
    try:
        # Basic health data
        health_data = {
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'environment': FLASK_ENV,
            'server': 'AI Tutor Admin Server',
            'database': {
                'type': 'unknown',
                'connection_status': 'unknown',
                'url_info': 'unknown'
            }
        }
        
        # Get database URL from app config
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        
        # Determine database type
        if db_url.startswith('sqlite'):
            health_data['database']['type'] = 'sqlite'
            health_data['database']['url_info'] = 'sqlite database'
        elif db_url.startswith('postgresql'):
            health_data['database']['type'] = 'postgresql'
            # Mask sensitive information in the URL
            url_parts = db_url.split('@')
            if len(url_parts) > 1:
                # Only show host and database name, not credentials
                masked_url = f"postgresql://****:****@{url_parts[1]}"
                health_data['database']['url_info'] = masked_url
            else:
                health_data['database']['url_info'] = 'postgresql database (url format error)'
        else:
            health_data['database']['type'] = 'unknown'
            health_data['database']['url_info'] = 'unknown database type'
        
        # Test database connection
        try:
            with app.app_context():
                # Try a simple query to test connection
                from sqlalchemy import text
                db.session.execute(text('SELECT 1')).fetchall()
                health_data['database']['connection_status'] = 'connected'
        except Exception as db_error:
            health_data['database']['connection_status'] = 'error'
            health_data['database']['error'] = str(db_error)
            log_error('HEALTH', 'Database connection test failed', db_error)
        
        # Add environment variables status (without exposing values)
        health_data['environment_variables'] = {
            'DATABASE_URL': 'set' if os.getenv('DATABASE_URL') else 'not set',
            'FLASK_ENV': FLASK_ENV,
            'ADMIN_USERNAME': 'set' if ADMIN_USERNAME != 'admin' else 'default',
            'ADMIN_PASSWORD': 'secure' if ADMIN_PASSWORD != 'admin123' else 'default (insecure)',
            'FLASK_SECRET_KEY': 'set' if FLASK_SECRET_KEY != secrets.token_hex(32) else 'default'
        }
        
        return jsonify(health_data)
    except Exception as e:
        log_error('HEALTH', 'Health check failed', e)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

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
    
    try:
        # Get system stats with error handling - force refresh from database
        try:
            # Force refresh of stats from database
            stats = get_system_stats()
            print(f"Dashboard stats: {stats}")
        except Exception as e:
            log_error('ADMIN', 'Error getting system stats for dashboard', e)
            print(f"Dashboard error: Failed to get system stats: {e}")
            stats = {
                'total_students': 0,
                'sessions_today': 0,
                'total_sessions': 0,
                'server_status': "Error",
                'phone_mappings': 0
            }
        
        # Get students with error handling
        try:
            # Get all students from database
            all_students = get_all_students()
            
            # Sort by most recently added (highest ID first)
            all_students.sort(key=lambda s: s.get('id', 0), reverse=True)
            recent_students = all_students[:5] if all_students else []  # Get 5 most recent
            
            # Create students_info with proper field access
            students_info = {}
            for student in all_students:
                # Create proper name from first_name and last_name
                first_name = student.get('first_name', '')
                last_name = student.get('last_name', '')
                full_name = f"{first_name} {last_name}".strip() or 'Unknown'
                
                # Add session count if available
                session_count = student.get('session_count', 0)
                
                students_info[student['id']] = {
                    'name': full_name,
                    'id': student['id'],
                    'grade': student.get('grade', 'Unknown'),
                    'phone': student.get('phone', 'None'),
                    'session_count': session_count
                }
                
                # Update display name in recent_students for template
                if student in recent_students:
                    student['display_name'] = full_name
        except Exception as e:
            log_error('ADMIN', 'Error getting students for dashboard', e)
            print(f"Dashboard error: Failed to get students: {e}")
            recent_students = []
            students_info = {}
        
        # Get phone mappings safely - use in-memory mapping
        try:
            phone_mappings = dict(phone_manager.phone_mapping)
        except Exception as e:
            log_error('ADMIN', 'Error getting phone mappings for dashboard', e)
            print(f"Dashboard error: Failed to get phone mappings: {e}")
            phone_mappings = {}
        
        return render_template('dashboard.html',
                             stats=stats,
                             recent_students=recent_students,
                             phone_mappings=phone_mappings,
                             students_info=students_info)
    except Exception as e:
        log_error('ADMIN', 'Critical error in admin dashboard', e)
        print(f"Critical dashboard error: {e}")
        # Return a simple error page instead of trying to render the full dashboard
        return f"""
        <html>
            <head><title>Admin Dashboard - Error</title></head>
            <body>
                <h1>Admin Dashboard Error</h1>
                <p>There was an error loading the dashboard. Please check the server logs.</p>
                <p>Error: {str(e)}</p>
                <p><a href="/admin/login">Return to login</a></p>
            </body>
        </html>
        """, 500

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
   
   try:
       # Use app context without reinitializing db
       with app.app_context():
           schools = get_all_schools()
           return render_template('schools.html', schools=schools)
   except Exception as e:
       log_error('ADMIN', 'Error loading schools page', e)
       flash(f'Error loading system information: {str(e)}', 'error')
       return render_template('schools.html', schools=[])

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
def delete_school_route(school_id):
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
        # Use app context for all database operations
        with app.app_context():
            # Initialize stats with default values
            stats = {
                'students': 0,
                'schools': 0,
                'curriculums': 0,
                'sessions': 0,
                'assessments': 0
            }
            
            # Get counts of each model with error handling for each query
            try:
                stats['students'] = Student.query.count()
            except Exception as e:
                log_error('DATABASE', 'Error counting students in database browser', e)
                
            try:
                stats['schools'] = School.query.count()
            except Exception as e:
                log_error('DATABASE', 'Error counting schools in database browser', e)
                
            try:
                stats['curriculums'] = Curriculum.query.count()
            except Exception as e:
                log_error('DATABASE', 'Error counting curriculums in database browser', e)
                
            try:
                stats['sessions'] = Session.query.count()
            except Exception as e:
                log_error('DATABASE', 'Error counting sessions in database browser', e)
                
            try:
                stats['assessments'] = Assessment.query.count()
            except Exception as e:
                log_error('DATABASE', 'Error counting assessments in database browser', e)
        
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
        # Use app context for all database operations
        with app.app_context():
            items = []
            
            # Get table data based on table name with error handling
            try:
                if table == 'students':
                    query_items = Student.query.all()
                    items = [item.to_dict() for item in query_items]
                elif table == 'schools':
                    query_items = School.query.all()
                    items = [item.to_dict() for item in query_items]
                elif table == 'curriculums':
                    query_items = Curriculum.query.all()
                    items = [item.to_dict() for item in query_items]
                elif table == 'sessions':
                    query_items = Session.query.all()
                    items = [item.to_dict() for item in query_items]
                elif table == 'assessments':
                    query_items = Assessment.query.all()
                    items = [item.to_dict() for item in query_items]
                else:
                    flash(f'Unknown table: {table}', 'error')
                    return redirect(url_for('admin_database'))
            except Exception as query_error:
                log_error('DATABASE', f'Error querying {table} table', query_error)
                flash(f'Error querying {table} table: {str(query_error)}', 'error')
        
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
        # Use app context for all database operations
        with app.app_context():
            # Get item data based on table name and ID with error handling
            item = None
            try:
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
            except Exception as query_error:
                log_error('DATABASE', f'Error querying {table}/{item_id}', query_error)
                flash(f'Error querying {table}/{item_id}: {str(query_error)}', 'error')
                return redirect(url_for('admin_database_table', table=table))
            
            if not item:
                flash(f'Item not found: {table}/{item_id}', 'error')
                return redirect(url_for('admin_database_table', table=table))
            
            # Convert to dictionary with error handling
            try:
                item_data = item.to_dict()
            except Exception as dict_error:
                log_error('DATABASE', f'Error converting {table}/{item_id} to dictionary', dict_error)
                flash(f'Error converting item to dictionary: {str(dict_error)}', 'error')
                return redirect(url_for('admin_database_table', table=table))
        
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

def check_environmental_issues():
    """
    Check for common environmental issues that might affect the application.
    Returns a list of issues with severity and instructions on how to fix them.
    """
    issues = []
    
    # Check database configuration
    database_url = os.getenv('DATABASE_URL')
    if FLASK_ENV == 'production':
        if not database_url:
            issues.append({
                'severity': 'critical',
                'title': 'Missing DATABASE_URL in Production',
                'description': 'The DATABASE_URL environment variable is not set in production environment.',
                'fix': 'Set the DATABASE_URL environment variable to a PostgreSQL connection string in your deployment environment.',
                'docs_link': '/DATABASE_CONFIGURATION_GUIDE.md'
            })
        elif not database_url.startswith('postgresql://'):
            issues.append({
                'severity': 'critical',
                'title': 'Invalid Database URL Format',
                'description': f'The DATABASE_URL does not use the postgresql:// prefix: {database_url.split("://")[0] if "://" in database_url else "unknown"}://',
                'fix': 'Update the DATABASE_URL to use the postgresql:// prefix instead of postgres:// or other prefixes.',
                'docs_link': '/DATABASE_CONFIGURATION_GUIDE.md'
            })
    
    # Check security configuration
    if ADMIN_PASSWORD == 'admin123':
        issues.append({
            'severity': 'high',
            'title': 'Default Admin Password',
            'description': 'The application is using the default admin password.',
            'fix': 'Set the ADMIN_PASSWORD environment variable to a secure password.',
            'docs_link': '/PRODUCTION_DEPLOYMENT_GUIDE.md'
        })
    
    if FLASK_SECRET_KEY == secrets.token_hex(32):
        issues.append({
            'severity': 'medium',
            'title': 'Default Flask Secret Key',
            'description': 'The application is using a dynamically generated Flask secret key, which will change on restart.',
            'fix': 'Set the FLASK_SECRET_KEY environment variable to a static secure value.',
            'docs_link': '/PRODUCTION_DEPLOYMENT_GUIDE.md'
        })
    
    # Check VAPI configuration
    if VAPI_SECRET == 'your_vapi_secret_here':
        issues.append({
            'severity': 'medium',
            'title': 'Missing VAPI Secret',
            'description': 'The VAPI_SECRET environment variable is not set or is using the default value.',
            'fix': 'Set the VAPI_SECRET environment variable to your VAPI webhook secret for secure webhook verification.',
            'docs_link': '/VAPI_WEBHOOK_INTEGRATION_GUIDE.md'
        })
    
    # Check Flask-Migrate installation
    try:
        import flask_migrate
    except ImportError:
        if FLASK_ENV == 'production':
            issues.append({
                'severity': 'high',
                'title': 'Flask-Migrate Not Installed',
                'description': 'Flask-Migrate is not installed, which is required for database migrations in production.',
                'fix': 'Install Flask-Migrate using pip: pip install Flask-Migrate',
                'docs_link': '/RENDER_DEPLOYMENT_GUIDE.md'
            })
    
    # Check for SQLAlchemy installation
    try:
        import flask_sqlalchemy
    except ImportError:
        issues.append({
            'severity': 'critical',
            'title': 'Flask-SQLAlchemy Not Installed',
            'description': 'Flask-SQLAlchemy is not installed, which is required for database operations.',
            'fix': 'Install Flask-SQLAlchemy using pip: pip install Flask-SQLAlchemy',
            'docs_link': '/DATABASE_CONFIGURATION_GUIDE.md'
        })
    
    return issues

# System info route
@app.route('/admin/system')
def admin_system():
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    try:
        # Get system stats using app context to ensure SQLAlchemy is properly registered
        with app.app_context():
            stats = get_system_stats()
        
        # Get database health information from health_check endpoint
        try:
            # Get database URL from app config
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            
            # Determine database type
            if db_url.startswith('sqlite'):
                db_type = 'sqlite'
                db_url_info = 'sqlite database'
            elif db_url.startswith('postgresql'):
                db_type = 'postgresql'
                # Mask sensitive information in the URL
                url_parts = db_url.split('@')
                if len(url_parts) > 1:
                    # Only show host and database name, not credentials
                    db_url_info = f"postgresql://****:****@{url_parts[1]}"
                else:
                    db_url_info = 'postgresql database (url format error)'
            else:
                db_type = 'unknown'
                db_url_info = 'unknown database type'
            
            # Test database connection
            db_connection_status = 'unknown'
            db_error = None
            try:
                with app.app_context():
                    # Try a simple query to test connection
                    from sqlalchemy import text
                    db.session.execute(text('SELECT 1')).fetchall()
                    db_connection_status = 'connected'
            except Exception as e:
                db_connection_status = 'error'
                db_error = str(e)
                log_error('SYSTEM', 'Database connection test failed', e)
            
            # Add database information to stats
            stats['database'] = {
                'type': db_type,
                'url_info': db_url_info,
                'connection_status': db_connection_status,
                'error': db_error
            }
            
            # Add environment information
            stats['environment'] = FLASK_ENV
            stats['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            log_error('SYSTEM', 'Error getting database health information', e)
            stats['database'] = {
                'type': 'unknown',
                'connection_status': 'error',
                'error': str(e)
            }
        
        # Get the phone mappings with error handling
        try:
            # Try to get phone mappings from memory first
            phone_mappings = dict(phone_manager.phone_mapping)
        except Exception as e:
            # If that fails, try to load from disk
            try:
                phone_mappings = phone_manager.load_phone_mapping()
            except Exception as load_error:
                # If both fail, use an empty dictionary
                log_error('ADMIN', f'Error loading phone mappings: {str(load_error)}', load_error)
                phone_mappings = {}
        
        # Get students info for phone mapping display with proper field access
        students = get_all_students()
        students_info = {}
        for student in students:
            # Create proper name from first_name and last_name
            first_name = student.get('first_name', '')
            last_name = student.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip() or 'Unknown'
            
            students_info[student['id']] = {
                'name': full_name,
                'id': student['id'],
                'grade': student.get('grade', 'Unknown')
            }
        
        # Check for environmental issues
        environmental_issues = check_environmental_issues()
        
        # Create some system events for the Recent events section
        system_events = [
            {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'SYSTEM',
                'message': 'System page loaded successfully',
                'user': session.get('admin_username', 'System'),
                'status': 'success'
            }
        ]
        
        # Add database connection status to system events
        if db_connection_status == 'connected':
            system_events.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'DATABASE',
                'message': f'PostgreSQL database connection successful',
                'user': 'System',
                'status': 'success'
            })
        elif db_connection_status == 'error':
            system_events.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'DATABASE',
                'message': f'PostgreSQL database connection error: {db_error}',
                'user': 'System',
                'status': 'error'
            })
        
        # Add environmental issues to system events
        for issue in environmental_issues:
            status = 'error' if issue['severity'] in ['critical', 'high'] else 'warning'
            system_events.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'ENVIRONMENT',
                'message': f"Environmental issue detected: {issue['title']}",
                'user': 'System',
                'status': status
            })
        
        # Set feature flags to disable ALL unsupported features
        feature_flags = {
            'clear_logs_enabled': False,      # Disable Clear Sessions Log button
            'backup_enabled': False,          # Disable backup options
            'restore_enabled': False,         # Disable restore options
            'admin_password_enabled': False,  # Disable admin password change
            'session_timeout_enabled': False, # Disable session timeout settings
            'auto_backup_enabled': False,     # Disable auto backup settings
            'view_logs_enabled': False,       # Disable view logs button
            'system_logs_enabled': False      # Disable system logs section
        }
        
        # Make sure server_status and status are set in stats
        # First ensure stats is a dictionary
        if not isinstance(stats, dict):
            print(f"⚠️ Stats is not a dictionary: {type(stats)}")
            stats = {
                'total_students': 0,
                'sessions_today': 0,
                'total_sessions': 0,
                'server_status': 'Error',
                'phone_mappings': 0
            }
            
        # Now we can safely set the server_status and status fields
        if 'server_status' not in stats:
            stats['server_status'] = 'Online'
            
        # Add status attribute for compatibility with template
        stats['status'] = stats.get('server_status', 'Online')
        
        return render_template('system.html',
                            stats=stats,
                            phone_mappings=phone_mappings,
                            students_info=students_info,
                            system_stats=stats,
                            mcp_port=3001,
                            vapi_status=vapi_client.is_configured(),
                            system_events=system_events,
                            feature_flags=feature_flags,
                            environmental_issues=environmental_issues)  # Pass environmental issues to template
    except Exception as e:
        log_error('ADMIN', 'Error loading system page', e)
        flash(f'Error loading system information: {str(e)}', 'error')
        # Return a simple error page instead of trying to render the full system page
        return f"""
        <html>
            <head><title>System Information - Error</title></head>
            <body>
                <h1>System Information Error</h1>
                <p>There was an error loading the system information. Please check the server logs.</p>
                <p>Error: {str(e)}</p>
                <p><a href="/admin">Return to dashboard</a></p>
            </body>
        </html>
        """, 500

# Phone Mapping Management
@app.route('/admin/phone-mappings/remove', methods=['POST'])
def remove_phone_mapping():
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    phone_number = request.form.get('phone_number')
    if not phone_number:
        return jsonify({'error': 'Phone number is required'}), 400
    
    # Get the latest mapping with error handling
    try:
        current_mapping = phone_manager.load_phone_mapping()
    except Exception as e:
        log_error('ADMIN', f'Error loading phone mappings for removal: {str(e)}', e)
        current_mapping = {}
    
    if phone_number in current_mapping:
        # Update the in-memory mapping with the latest from disk
        try:
            phone_manager.phone_mapping = current_mapping
        except Exception as e:
            log_error('ADMIN', f'Error updating in-memory phone mapping: {str(e)}', e)
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
    
    # Check if student exists in database
    student = student_repository.get_by_id(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Use the add_phone_mapping method with error handling
    try:
        phone_manager.add_phone_mapping(phone_number, student_id)
        flash(f'Phone mapping added: {phone_number} → {student_id}', 'success')
        return jsonify({'success': True, 'message': 'Phone mapping added'})
    except Exception as e:
        log_error('ADMIN', f'Error adding phone mapping: {str(e)}', e,
                 phone_number=phone_number, student_id=student_id)
        flash(f'Error adding phone mapping: {str(e)}', 'error')
        return jsonify({'error': f'Failed to add phone mapping: {str(e)}'}), 500

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
            
            # Add phone mapping if provided with error handling
            if phone:
                try:
                    phone_manager.add_phone_mapping(phone, str(student_id))
                    print(f"📱 Added phone mapping: {phone} → {student_id}")
                except Exception as e:
                    log_error('DATABASE', 'Error adding phone mapping for new student', e,
                             student_id=student_id, phone=phone)
                    print(f"⚠️ Error adding phone mapping: {e}")
            
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
            # Remove old phone mapping for this student with error handling
            old_phone = None
            try:
                # First find the old phone number
                for phone_num, sid in list(phone_manager.phone_mapping.items()):
                    if sid == student_id:
                        old_phone = phone_num
                        break
                
                # If found, remove it
                if old_phone:
                    try:
                        del phone_manager.phone_mapping[old_phone]
                        print(f"📱 Removed old phone mapping: {old_phone} → {student_id}")
                    except Exception as e:
                        log_error('DATABASE', 'Error removing old phone mapping', e,
                                 student_id=student_id, phone=old_phone)
                        print(f"⚠️ Error removing old phone mapping: {e}")
            except Exception as e:
                log_error('DATABASE', 'Error accessing phone mappings', e, student_id=student_id)
                print(f"⚠️ Error accessing phone mappings: {e}")
            
            # Add new phone mapping with error handling
            if phone:
                try:
                    phone_manager.add_phone_mapping(phone, student_id)
                    print(f"📱 Added new phone mapping: {phone} → {student_id}")
                except Exception as e:
                    log_error('DATABASE', 'Error adding new phone mapping', e,
                             student_id=student_id, phone=phone)
                    print(f"⚠️ Error adding new phone mapping: {e}")
            
            # Save phone mappings with error handling
            try:
                phone_manager.save_phone_mapping()
            except Exception as e:
                log_error('DATABASE', 'Error saving phone mappings', e, student_id=student_id)
                print(f"⚠️ Error saving phone mappings: {e}")
            
            flash(f'Student {first_name} {last_name} updated successfully!', 'success')
            return redirect(url_for('admin_student_detail', student_id=student_id))
            
        except Exception as e:
            flash(f'Error updating student: {str(e)}', 'error')
            log_error('DATABASE', 'Error updating student', e, student_id=student_id)
            return render_template('edit_student.html', student=student, student_id=student_id, phone=phone, schools=schools)
    
    # Get current phone from the latest mapping with error handling
    phone = None
    try:
        current_mapping = phone_manager.load_phone_mapping()
        for phone_num, sid in current_mapping.items():
            if sid == student_id:
                phone = phone_num
                break
    except Exception as e:
        log_error('ADMIN', f'Error loading phone mappings for student: {str(e)}', e, student_id=student_id)
    
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
        
        # Remove phone mapping for this student with error handling
        phone_to_remove = None
        try:
            current_mapping = phone_manager.load_phone_mapping()
            
            for phone_num, sid in list(current_mapping.items()):
                if sid == student_id:
                    phone_to_remove = phone_num
                    # Update the in-memory mapping with the latest from disk
                    try:
                        phone_manager.phone_mapping = current_mapping
                        del phone_manager.phone_mapping[phone_num]
                    except Exception as e:
                        log_error('ADMIN', f'Error updating in-memory phone mapping for deletion: {str(e)}', e, student_id=student_id)
                    break
        except Exception as e:
            log_error('ADMIN', f'Error loading phone mappings for student deletion: {str(e)}', e, student_id=student_id)
        
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
        # Get all sessions from database directly without using app context
        # This avoids SQLAlchemy registration issues
        all_sessions = []
        try:
            # Use app context to ensure SQLAlchemy is properly registered
            with app.app_context():
                all_sessions = session_repository.get_all()
        except Exception as db_error:
            log_error('DATABASE', f'Error getting sessions from repository: {str(db_error)}', db_error)
            flash(f'Error getting sessions from database: {str(db_error)}', 'error')
        
        # Get all students for additional information
        students = []
        try:
            # Use app context to ensure SQLAlchemy is properly registered
            with app.app_context():
                students = get_all_students()
        except Exception as student_error:
            log_error('DATABASE', f'Error getting students: {str(student_error)}', student_error)
            flash(f'Error getting student information: {str(student_error)}', 'warning')
            
        students_dict = {s['id']: s for s in students}
        
        # Enhance session data with student information
        for session in all_sessions:
            student_id = session.get('student_id')
            student = students_dict.get(student_id, {})
            
            # Create full name from first_name and last_name
            first_name = student.get('first_name', '')
            last_name = student.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip() or 'Unknown'
            
            # Safely assign student name
            session['student_name'] = full_name if full_name else 'Unknown'
            session['student_grade'] = student.get('grade', 'Unknown')
            
            # Ensure session ID is set
            if 'id' not in session and session.get('_id'):
                session['id'] = session.get('_id')
            
            # Format date and time - handle different datetime formats safely
            start_datetime = session.get('start_datetime', '')
            try:
                if start_datetime:
                    # Convert to string if it's not already
                    start_datetime_str = str(start_datetime) if not isinstance(start_datetime, str) else start_datetime
                    
                    # Handle ISO format with T separator
                    if 'T' in start_datetime_str:
                        session['date'] = start_datetime_str.split('T')[0]
                        session['time'] = start_datetime_str.split('T')[1][:8]
                    # Handle space separator
                    elif ' ' in start_datetime_str:
                        parts = start_datetime_str.split(' ')
                        session['date'] = parts[0]
                        session['time'] = parts[1][:8] if len(parts) > 1 else ''
                    # Handle date-only string
                    else:
                        session['date'] = start_datetime_str[:10]
                        session['time'] = ''
                else:
                    session['date'] = 'Unknown'
                    session['time'] = ''
            except Exception as e:
                # Fallback for any datetime parsing errors
                session['date'] = str(start_datetime)[:10] if start_datetime else 'Unknown'
                session['time'] = ''
                log_error('ADMIN', f'Error formatting session datetime: {e}', e,
                         session_id=session.get('id'), datetime_value=str(start_datetime))
            
            # Set session type
            session['type'] = 'VAPI Call' if session.get('session_type') == 'phone' else 'Regular Session'
            
            # Set duration - handle different duration formats safely
            try:
                if session.get('duration_minutes') is not None:
                    session['duration'] = session.get('duration_minutes')
                elif session.get('duration') is not None:
                    # Convert seconds to minutes if needed
                    session['duration'] = session.get('duration') // 60
                else:
                    session['duration'] = 'Unknown'
            except Exception:
                session['duration'] = 'Unknown'
            
            # Set transcript and analysis flags
            session['has_transcript'] = bool(session.get('transcript'))
            session['has_analysis'] = False  # Set based on your database schema
        
        # Sort by date and time (newest first) - with error handling
        try:
            all_sessions.sort(key=lambda x: (x.get('date', ''), x.get('time', '')), reverse=True)
        except Exception as e:
            log_error('ADMIN', f'Error sorting sessions: {e}', e)
            # Alternative sorting by ID if date sorting fails
            all_sessions.sort(key=lambda x: x.get('id', 0), reverse=True)
        
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
    
    try:
        # Ensure we're in an app context for all operations
        with app.app_context():
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
    except Exception as e:
        log_error('ADMIN', f'Error loading AI analysis dashboard: {str(e)}', e)
        flash(f'Error loading AI analysis dashboard: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

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
        
        # Enhanced logging for webhook debugging
        log_webhook('webhook-received', 'VAPI webhook received - starting processing',
                   ip_address=request.remote_addr,
                   headers=str(headers_info),
                   payload_size=len(payload))
        print(f"📞 VAPI webhook received - payload size: {len(payload)} bytes")
        
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
        call_id = message.get('call', {}).get('id') if isinstance(message, dict) else None
        
        log_webhook(message_type or 'unknown-event', f"VAPI webhook received: {message_type}",
                   ip_address=request.remote_addr,
                   call_id=call_id,
                   payload_size=len(payload))
        print(f"📞 VAPI webhook received: {message_type} (Call ID: {call_id})")
        
        # Only handle end-of-call-report - ignore all other events
        if message_type == 'end-of-call-report':
            # Use app context for database operations
            with app.app_context():
                log_webhook('processing-call', f"Processing end-of-call-report with app context",
                           call_id=call_id)
                print(f"📞 Processing end-of-call-report with app context (Call ID: {call_id})")
                handle_end_of_call_api_driven(message)
                # Explicitly commit any pending database transactions
                try:
                    db.session.commit()
                    log_webhook('db-commit-success', f"Database transaction committed successfully",
                               call_id=call_id)
                    print(f"💾 Database transaction committed successfully (Call ID: {call_id})")
                except Exception as commit_error:
                    db.session.rollback()
                    log_error('WEBHOOK', f"Error committing database transaction: {str(commit_error)}",
                             commit_error, call_id=call_id)
                    print(f"❌ Error committing database transaction: {commit_error}")
        else:
            # Log but ignore other events
            log_webhook('ignored-event', f"Ignored VAPI event: {message_type}",
                       call_id=call_id)
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
        # We should already be in an app context from the vapi_webhook function
        import flask
        if not flask.has_app_context():
            log_webhook('app-context-missing', f"No app context in handle_end_of_call_api_driven",
                       call_id=call_id)
            print(f"⚠️ No app context in handle_end_of_call_api_driven - this should not happen")
            # We should already be in an app context, but just in case, create one
            with app.app_context():
                student_id = identify_or_create_student(customer_phone, call_id)
                if student_id:
                    save_api_driven_session(call_id, student_id, customer_phone,
                                          duration, transcript, call_data)
        else:
            # Normal flow - we're already in an app context
            student_id = identify_or_create_student(customer_phone, call_id)
            if student_id:
                log_webhook('student-identified', f"Student identified/created: {student_id}",
                           call_id=call_id, phone=customer_phone)
                print(f"👤 Student identified/created: {student_id}")
                
                # Save session data
                save_api_driven_session(call_id, student_id, customer_phone,
                                       duration, transcript, call_data)
            else:
                log_error('WEBHOOK', f"Failed to identify or create student for call {call_id}",
                         ValueError("No student_id returned"), call_id=call_id, phone=customer_phone)
                print(f"❌ Failed to identify or create student for call {call_id}")
        
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
        # Rollback any failed database transactions
        try:
            db.session.rollback()
            log_webhook('db-rollback', f"Database transaction rolled back due to error",
                       call_id=call_id if 'call_id' in locals() else None)
            print(f"🔄 Database transaction rolled back due to error")
        except Exception as rollback_error:
            log_error('WEBHOOK', f"Error rolling back database transaction: {str(rollback_error)}",
                     rollback_error, call_id=call_id if 'call_id' in locals() else None)
            print(f"❌ Error rolling back database transaction: {rollback_error}")

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
                    # Ensure student_id is a string
                    student_id_str = str(student_id)
                    analyzer.update_student_profile(student_id_str, extracted_info)
                    log_webhook('profile-updated', f"Updated student profile from webhook session",
                                call_id=call_id, student_id=student_id_str,
                                extracted_info=extracted_info)
                    print(f"👤 Updated profile for student {student_id_str} with extracted information")
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
    # Check if we're in an application context
    import flask
    has_app_context = flask.has_app_context()
    if not has_app_context:
        log_webhook('app-context-missing', f"No app context in identify_or_create_student - creating one",
                   call_id=call_id)
        print(f"⚠️ No app context in identify_or_create_student - creating one for call {call_id}")
    
    try:
        # Wrap everything in an app context if needed
        context = app.app_context() if not has_app_context else None
        if context:
            context.push()
            log_webhook('app-context-created', f"Created app context for identify_or_create_student",
                       call_id=call_id)
            print(f"🔄 Created app context for identify_or_create_student (Call ID: {call_id})")
        
        if not phone_number:
            return f"unknown_caller_{call_id}"
        
        # Clean and normalize phone number
        clean_phone = normalize_phone_number(phone_number)
        
        # Log the exact lookup for debugging
        log_webhook('phone-lookup', f"Looking up student by phone: {clean_phone}",
                   call_id=call_id, phone=clean_phone, original_phone=phone_number)
        
        # First check if we have a mapping in memory
        student_id = phone_manager.get_student_by_phone(clean_phone)
        
        # If found, verify the student exists in the database
        if student_id:
            try:
                # Verify student exists in database - ensure student_id is a string
                student_id_str = str(student_id)
                
                # Explicitly use database transaction
                try:
                    student = student_repository.get_by_id(student_id_str)
                    
                    if student:
                        log_webhook('student-identified', f"Found student {student_id_str} in database",
                                   call_id=call_id, student_id=student_id_str, phone=clean_phone)
                        
                        # Get student name for logging
                        first_name = student.get('first_name', '')
                        last_name = student.get('last_name', '')
                        full_name = f"{first_name} {last_name}".strip() or 'Unknown'
                        
                        print(f"👤 Found existing student: {full_name} (ID: {student_id_str})")
                        return student_id_str
                    else:
                        # Student mapping exists but student doesn't exist in database
                        log_webhook('student-mapping-orphaned', f"Phone mapping exists but student {student_id_str} not found in database",
                                   call_id=call_id, student_id=student_id_str, phone=clean_phone)
                        print(f"⚠️ Phone mapping exists but student {student_id_str} not found in database")
                        
                        # Remove orphaned mapping
                        if clean_phone in phone_manager.phone_mapping:
                            del phone_manager.phone_mapping[clean_phone]
                            phone_manager.save_phone_mapping()
                except Exception as db_error:
                    # Rollback transaction on error
                    db.session.rollback()
                    log_error('DATABASE', f"Database error verifying student", db_error,
                             call_id=call_id, student_id=student_id_str, phone=clean_phone)
                    print(f"❌ Database error verifying student: {db_error}")
                    raise  # Re-raise to be caught by outer exception handler
            except Exception as e:
                log_error('DATABASE', f"Error verifying student in database", e,
                         call_id=call_id, student_id=student_id, phone=clean_phone)
                print(f"⚠️ Error verifying student {student_id}: {e}")
                
                # Remove potentially problematic mapping
                if clean_phone in phone_manager.phone_mapping:
                    del phone_manager.phone_mapping[clean_phone]
                    phone_manager.save_phone_mapping()
        
        # Create new student if not found
        log_webhook('student-not-found', f"No student found for phone: {clean_phone}",
                   call_id=call_id, phone=clean_phone)
        
        # Pass the normalized phone to create_student_from_call
        new_student_id = create_student_from_call(clean_phone, call_id)
        log_webhook('student-created', f"Created new student {new_student_id}",
                   call_id=call_id, student_id=new_student_id, phone=clean_phone)
        
        return new_student_id
    
    except Exception as e:
        log_error('WEBHOOK', f"Error in identify_or_create_student", e,
                 call_id=call_id, phone=phone_number)
        print(f"❌ Error in identify_or_create_student: {e}")
        
        # Ensure any transaction is rolled back
        try:
            db.session.rollback()
            log_webhook('db-rollback', f"Database transaction rolled back due to error",
                       call_id=call_id)
            print(f"🔄 Database transaction rolled back due to error")
        except Exception as rollback_error:
            log_error('DATABASE', f"Error rolling back database transaction", rollback_error,
                     call_id=call_id)
            print(f"❌ Error rolling back database transaction: {rollback_error}")
        
        # Return a temporary ID as fallback
        return f"temp_{call_id[-6:]}"
    
    finally:
        # Pop the app context if we created one
        if not has_app_context and 'context' in locals() and context:
            context.pop()
            log_webhook('app-context-removed', f"Removed app context for identify_or_create_student",
                       call_id=call_id)
            print(f"🔄 Removed app context for identify_or_create_student (Call ID: {call_id})")

def create_student_from_call(phone: str, call_id: str) -> str:
    """Create a new student from phone call data using database"""
    # Check if we're in an application context
    import flask
    has_app_context = flask.has_app_context()
    if not has_app_context:
        log_webhook('app-context-missing', f"No app context in create_student_from_call - creating one",
                   call_id=call_id)
        print(f"⚠️ No app context in create_student_from_call - creating one for call {call_id}")
    
    try:
        # Wrap everything in an app context if needed
        context = app.app_context() if not has_app_context else None
        if context:
            context.push()
            log_webhook('app-context-created', f"Created app context for create_student_from_call",
                       call_id=call_id)
            print(f"🔄 Created app context for create_student_from_call (Call ID: {call_id})")
        
        # Ensure phone is normalized for consistent lookup and storage
        normalized_phone = normalize_phone_number(phone)
        
        # Use last 4 digits of normalized phone for name creation
        phone_suffix = normalized_phone[-4:] if normalized_phone else ""
        first_name = f"Student"
        last_name = phone_suffix if phone else f"Unknown_{call_id[-6:]}"
        
        # Get current timestamp for created_at field
        current_time = datetime.now().isoformat()
        
        # Create student data with SQL-compatible fields
        student_data = {
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': None,
            'phone_number': normalized_phone,
            'student_type': 'International',  # Default value
            'school_id': None,
            'interests': [],
            'learning_preferences': [],
            'created_at': current_time,
            'updated_at': current_time,
            'grade': 'Unknown',  # Default grade
            'age': None  # Default age
        }
        
        log_webhook('creating-student', f"Creating student in database",
                   call_id=call_id, phone=normalized_phone)
        print(f"👤 Creating new student for phone: {normalized_phone} (Call ID: {call_id})")
        
        # Create student in database with explicit transaction management
        try:
            new_student = student_repository.create(student_data)
            
            # Explicitly commit the transaction
            db.session.commit()
            log_webhook('db-commit-success', f"Student database transaction committed successfully",
                       call_id=call_id, phone=normalized_phone)
            print(f"💾 Student database transaction committed successfully (Call ID: {call_id})")
            
            if not new_student:
                log_error('DATABASE', f"Failed to create student in database", ValueError("Database operation failed"),
                         call_id=call_id, phone=normalized_phone)
                # Return a temporary ID for fallback
                return f"temp_{call_id[-6:]}"
        except Exception as db_error:
            # Rollback transaction on error
            db.session.rollback()
            log_error('DATABASE', f"Error creating student in database", db_error,
                     call_id=call_id, phone=normalized_phone)
            print(f"❌ Error creating student in database: {db_error}")
            
            # Re-raise to be caught by outer exception handler
            raise
        
        # Ensure student_id is a string
        student_id = str(new_student['id'])
        
        # Add phone mapping using normalized phone number
        if normalized_phone:
            try:
                # Log the exact phone number being mapped for debugging
                log_webhook('phone-mapping', f"Adding phone mapping: {normalized_phone} → {student_id}",
                            phone=normalized_phone, student_id=student_id)
                
                # Explicitly use string ID for phone mapping
                phone_manager.add_phone_mapping(normalized_phone, student_id)
                
                # Log student creation for debugging
                log_webhook('student-created', f"Created new student in database: {first_name} {last_name}",
                           call_id=call_id, student_id=student_id, phone=normalized_phone)
                print(f"👤 Created new student in database: {first_name} {last_name} (ID: {student_id})")
            except Exception as mapping_error:
                log_error('DATABASE', f"Error adding phone mapping for new student", mapping_error,
                         call_id=call_id, student_id=student_id, phone=normalized_phone)
                print(f"⚠️ Error adding phone mapping: {mapping_error}")
        
        return student_id
        
    except Exception as e:
        log_error('DATABASE', f"Error creating student from call", e,
                 call_id=call_id, phone=phone)
        
        # Ensure any transaction is rolled back
        try:
            db.session.rollback()
            log_webhook('db-rollback', f"Database transaction rolled back due to error",
                       call_id=call_id)
            print(f"🔄 Database transaction rolled back due to error")
        except Exception as rollback_error:
            log_error('DATABASE', f"Error rolling back database transaction", rollback_error,
                     call_id=call_id)
            print(f"❌ Error rolling back database transaction: {rollback_error}")
        
        # Return a temporary ID for fallback
        return f"temp_{call_id[-6:]}"
    
    finally:
        # Pop the app context if we created one
        if not has_app_context and 'context' in locals() and context:
            context.pop()
            log_webhook('app-context-removed', f"Removed app context for create_student_from_call",
                       call_id=call_id)
            print(f"🔄 Removed app context for create_student_from_call (Call ID: {call_id})")

def save_api_driven_session(call_id: str, student_id: str, phone: str,
                              duration: int, transcript: str, call_data: Dict[Any, Any]):
    """Save VAPI session data using API-fetched data to database"""
    # Check if we're in an application context
    import flask
    has_app_context = flask.has_app_context()
    if not has_app_context:
        log_webhook('app-context-missing', f"No app context in save_api_driven_session - creating one",
                   call_id=call_id, student_id=student_id)
        print(f"⚠️ No app context in save_api_driven_session - creating one for call {call_id}")
    
    try:
        # Wrap everything in an app context if needed
        context = app.app_context() if not has_app_context else None
        if context:
            context.push()
            log_webhook('app-context-created', f"Created app context for save_api_driven_session",
                       call_id=call_id, student_id=student_id)
            print(f"🔄 Created app context for save_api_driven_session (Call ID: {call_id})")
        
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
        
        # Get current timestamp for created_at field
        current_time = datetime.now()
        
        # Format start_datetime properly for SQL storage
        try:
            start_time = metadata.get('created_at')
            if start_time and isinstance(start_time, str):
                # Try to parse the datetime string
                start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            else:
                # Use current time if no valid start time
                start_datetime = current_time
        except Exception as e:
            log_error('WEBHOOK', f"Error parsing start_datetime, using current time", e,
                     call_id=call_id, start_time=metadata.get('created_at'))
            start_datetime = current_time
        
        # Prepare session data for database with SQL-compatible fields
        session_data = {
            'student_id': student_id,
            'call_id': call_id,
            'session_type': 'phone',
            'start_datetime': start_datetime.isoformat(),
            'duration': effective_duration,
            'transcript': transcript,
            'summary': metadata.get('analysis_summary', ''),
            'created_at': current_time.isoformat(),
            'updated_at': current_time.isoformat(),
            'topics_covered': ['Phone Call'],  # Default topics
            'engagement_score': 75  # Default engagement score
        }
        
        log_webhook('creating-session', f"Creating session in database",
                   call_id=call_id, student_id=student_id,
                   session_type='phone', duration=effective_duration)
        
        # Save session to database
        try:
            new_session = session_repository.create(session_data)
            
            # Explicitly commit the transaction
            db.session.commit()
            log_webhook('db-commit-success', f"Session database transaction committed successfully",
                       call_id=call_id, student_id=student_id)
            print(f"💾 Session database transaction committed successfully (Call ID: {call_id})")
            
            if not new_session:
                log_error('DATABASE', f"Failed to create session in database", ValueError("Database operation failed"),
                         call_id=call_id, student_id=student_id)
                print(f"❌ Failed to save session to database")
                return
        except Exception as db_error:
            # Rollback transaction on error
            db.session.rollback()
            log_error('DATABASE', f"Error creating session in database", db_error,
                     call_id=call_id, student_id=student_id)
            print(f"❌ Error creating session in database: {db_error}")
            
            # Re-raise to be caught by outer exception handler
            raise
        
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
                    # Wrap profile update in try-except to handle database errors
                    try:
                        analyzer.update_student_profile(student_id, extracted_info)
                        # Explicitly commit the profile update transaction
                        db.session.commit()
                        log_webhook('profile-updated', f"Updated student profile from transcript",
                                    call_id=call_id, student_id=student_id,
                                    extracted_info=extracted_info)
                        print(f"👤 Updated profile for student {student_id} with extracted information: {extracted_info}")
                    except Exception as profile_error:
                        # Rollback transaction on error
                        db.session.rollback()
                        log_error('DATABASE', f"Error updating student profile", profile_error,
                                 call_id=call_id, student_id=student_id)
                        print(f"❌ Error updating student profile: {profile_error}")
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
        
        # Ensure any transaction is rolled back
        try:
            db.session.rollback()
            log_webhook('db-rollback', f"Database transaction rolled back due to error",
                       call_id=call_id, student_id=student_id)
            print(f"🔄 Database transaction rolled back due to error")
        except Exception as rollback_error:
            log_error('DATABASE', f"Error rolling back database transaction", rollback_error,
                     call_id=call_id, student_id=student_id)
            print(f"❌ Error rolling back database transaction: {rollback_error}")
    finally:
        # Pop the app context if we created one
        if not has_app_context and 'context' in locals() and context:
            context.pop()
            log_webhook('app-context-removed', f"Removed app context for save_api_driven_session",
                       call_id=call_id, student_id=student_id)
            print(f"🔄 Removed app context for save_api_driven_session (Call ID: {call_id})")

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
        
        # Ensure student_id is a string
        student_id_str = str(student_id)
        
        # Get student context
        student_data = get_student_data(student_id_str)
        student_context = {}
        
        if student_data and student_data.get('profile'):
            profile = student_data['profile']
            student_context = {
                'name': profile.get('name', profile.get('first_name', '') + ' ' + profile.get('last_name', '')).strip() or 'Unknown',
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
        # Use app context without reinitializing db
        with app.app_context():
            # Don't reinitialize db, just use the existing instance
            
            # Use the system_logger directly instead of creating a new repository
            logs = []
            log_stats = {'categories': {}, 'levels': {}}
            
            try:
                logs = system_logger.get_logs(days=days, category=category, level=level)
                log_stats = system_logger.get_log_statistics()
            except Exception as log_error:
                log_error('DATABASE', f'Error accessing system logs: {str(log_error)}', log_error)
                flash(f'Error accessing system logs: {str(log_error)}', 'error')
                logs = []  # Ensure logs is an empty list if there was an error
            
            # Get available categories and levels for filtering
            available_categories = list(log_stats.get('categories', {}).keys())
            available_levels = list(log_stats.get('levels', {}).keys())
            
            try:
                log_admin_action('view_logs', session.get('admin_username', 'unknown'),
                                days_filter=days,
                                category_filter=category,
                                level_filter=level,
                                log_count=len(logs))
            except Exception as action_error:
                # Don't let logging the action prevent viewing logs
                print(f"Error logging admin action: {action_error}")
            
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
    
    try:
        # Use app context without reinitializing db
        with app.app_context():
            # Get active tokens - handle the case where get_active_tokens might not exist
            if hasattr(token_service, 'get_active_tokens'):
                active_tokens = token_service.get_active_tokens()
            else:
                # Fallback implementation if get_active_tokens doesn't exist
                active_tokens = []
                # Log the issue
                log_error('ADMIN', 'TokenService missing get_active_tokens method, using empty list',
                         ValueError('Method not found'))
                
            return render_template('tokens.html',
                                active_tokens=active_tokens)
    except Exception as e:
        log_error('ADMIN', f'Error loading tokens page: {str(e)}', e)
        flash(f'Error loading tokens page: {str(e)}', 'error')
        # Return a simple error page instead of trying to render the full tokens page
        return f"""
        <html>
            <head><title>Tokens - Error</title></head>
            <body>
                <h1>Tokens Page Error</h1>
                <p>There was an error loading the tokens page. Please check the server logs.</p>
                <p>Error: {str(e)}</p>
                <p><a href="/admin">Return to dashboard</a></p>
            </body>
        </html>
        """, 500

@app.route('/admin/tokens/generate', methods=['POST'])
def generate_token():
    """Generate a new access token"""
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    try:
        # Use app context without reinitializing db
        with app.app_context():
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
            
            # Get active tokens for display - handle the case where get_active_tokens might not exist
            if hasattr(token_service, 'get_active_tokens'):
                active_tokens = token_service.get_active_tokens()
            else:
                # Fallback implementation if get_active_tokens doesn't exist
                active_tokens = []
                # Log the issue
                log_error('ADMIN', 'TokenService missing get_active_tokens method, using empty list',
                         ValueError('Method not found'))
            
            return render_template('tokens.html',
                                token=token_data['token'],
                                token_name=token_name,
                                token_scopes=scopes,
                                token_expires=token_data['expires_at'],
                                active_tokens=active_tokens)
    except Exception as e:
        log_error('ADMIN', f'Error generating token: {str(e)}', e)
        flash(f'Error generating token: {str(e)}', 'error')
        return redirect(url_for('admin_tokens'))

@app.route('/admin/tokens/revoke/<token_id>', methods=['POST'])
def revoke_token(token_id):
    """Revoke an access token"""
    if not check_auth():
        return redirect(url_for('admin_login'))
    
    try:
        # Use app context without reinitializing db
        with app.app_context():
            # Revoke token
            if token_service.revoke_token(token_id):
                log_admin_action('revoke_token', session.get('admin_username', 'unknown'),
                                token_id=token_id)
                flash('Token revoked successfully', 'success')
            else:
                flash('Token not found or already revoked', 'error')
    except Exception as e:
        log_error('ADMIN', f'Error revoking token: {str(e)}', e)
        flash(f'Error revoking token: {str(e)}', 'error')
    
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
        with app.app_context():
            db.create_all()
            print("🗄️  Database tables created/verified")
            
            # Run initial cleanup in the same app context
            try:
                # Import and use the Celery task for log cleanup
                from app.tasks.maintenance_tasks import cleanup_old_logs
                from app.config import Config
                
                # Run cleanup task directly (not as a Celery task)
                deleted_count = cleanup_old_logs(days=Config.LOG_RETENTION_DAYS)
                
                if deleted_count > 0:
                    print(f"🧹 Initial cleanup: {deleted_count} old log entries removed")
            except Exception as cleanup_e:
                print(f"⚠️  Initial cleanup failed: {cleanup_e}")
                log_error('DATABASE', 'Initial log cleanup failed', cleanup_e)
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
        log_error('DATABASE', 'Database initialization failed', e)
    except Exception as e:
        print(f"⚠️  Initial cleanup failed: {e}")
        log_error('DATABASE', 'Initial log cleanup failed', e)
    
    # Production vs Development settings
    if FLASK_ENV == 'production':
        print("🔒 Running in PRODUCTION mode")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("🛠️  Running in DEVELOPMENT mode")
        app.run(host='0.0.0.0', port=port, debug=True)