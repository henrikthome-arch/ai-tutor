"""
Admin UI Blueprint
Flask routes for the admin web interface
"""

import os
import json
import hashlib
from datetime import datetime
import asyncio
from flask import Blueprint, render_template, session, redirect, request, flash, url_for, jsonify, send_file
from flask import current_app

# Import system components
from system_logger import system_logger, log_admin_action, log_webhook, log_ai_analysis, log_error, log_system
from vapi.client import vapi_client
from app.services.token_service import TokenService

# Import AI components
try:
    from ai.session_processor import session_processor
    from ai.providers import provider_manager
    from ai.validator import validator
    AI_POC_AVAILABLE = True
except ImportError as e:
    AI_POC_AVAILABLE = False
    print(f"⚠️  AI POC not available: {e}")

# Import services and repositories
from app.services.student_service import StudentService
from app.services.session_service import SessionService
from app.services.analytics_service import AnalyticsService
from app.services.mcp_interaction_service import MCPInteractionService

# Import the blueprint from __init__.py
from app.main import bp as main

# Initialize services
student_service = StudentService()
session_service = SessionService()
analytics_service = AnalyticsService(None)  # Will be initialized with db session in each request
token_service = TokenService()
mcp_interaction_service = MCPInteractionService()

# Authentication helper
def check_auth():
    """Check if user is authenticated"""
    return session.get('admin_logged_in', False)

# Root route for health checks
@main.route('/')
def index():
    """Root route for health checks and redirects"""
    return redirect(url_for('main.admin_dashboard'))

# Authentication routes
@main.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form['password']
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Get admin credentials from app config
        admin_username = current_app.config['ADMIN_USERNAME']
        admin_password_hash = current_app.config['ADMIN_PASSWORD_HASH']
        
        if password_hash == admin_password_hash:
            session['admin_logged_in'] = True
            session['admin_username'] = admin_username
            log_admin_action('login', admin_username,
                           ip_address=request.remote_addr,
                           user_agent=request.headers.get('User-Agent', 'Unknown'))
            flash('Successfully logged in!', 'success')
            return redirect(url_for('main.admin_dashboard'))
        else:
            log_admin_action('failed_login', admin_username,
                           ip_address=request.remote_addr,
                           user_agent=request.headers.get('User-Agent', 'Unknown'),
                           level='WARNING')
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@main.route('/admin/logout')
def admin_logout():
    log_admin_action('logout', session.get('admin_username', 'unknown'),
                    ip_address=request.remote_addr)
    session.clear()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('main.admin_login'))

# Dashboard routes
@main.route('/admin')
@main.route('/admin/')
def admin_dashboard():
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    stats = student_service.get_system_stats()
    recent_students = student_service.get_all_students()[:5]  # Get 5 most recent
    phone_mappings = student_service.get_phone_mappings()
    students_info = {s.id: s for s in student_service.get_all_students()}
    
    return render_template('dashboard.html',
                         stats=stats,
                         recent_students=recent_students,
                         phone_mappings=phone_mappings,
                         students_info=students_info)

# Student management routes
@main.route('/admin/students')
def admin_students():
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    students = student_service.get_all_students()
    return render_template('students.html', students=students)

@main.route('/admin/students/<student_id>')
def admin_student_detail(student_id):
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    student_data = student_service.get_student_data(student_id)
    if not student_data:
        flash(f'Student {student_id} not found', 'error')
        return redirect(url_for('main.admin_students'))
    
    # Get phone number from the latest mapping
    phone = student_service.get_student_phone(student_id)
    
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
                         profile=profile,
                         phone=phone,
                         progress=progress,
                         recent_sessions=recent_sessions,
                         session_count=len(sessions),
                         last_session=recent_sessions[0]['date'] if recent_sessions else None)

# School management routes
@main.route('/admin/schools')
def admin_schools():
   if not check_auth():
       return redirect(url_for('main.admin_login'))
   
   schools = student_service.get_all_schools()
   return render_template('schools.html', schools=schools)

@main.route('/admin/schools/add', methods=['GET', 'POST'])
def add_school():
   if not check_auth():
       return redirect(url_for('main.admin_login'))
   
   if request.method == 'POST':
       schools = student_service.get_all_schools()
       new_school = {
           "school_id": request.form['school_id'],
           "name": request.form['name'],
           "location": request.form['location'],
           "background": request.form['background'],
           "curriculum_type": request.form['curriculum_type']
       }
       schools.append(new_school)
       student_service.save_all_schools(schools)
       flash('School added successfully!', 'success')
       return redirect(url_for('main.admin_schools'))
       
   return render_template('add_school.html')

@main.route('/admin/schools/edit/<school_id>', methods=['GET', 'POST'])
def edit_school(school_id):
   if not check_auth():
       return redirect(url_for('main.admin_login'))

   schools = student_service.get_all_schools()
   school = next((s for s in schools if s['school_id'] == school_id), None)

   if not school:
       flash('School not found!', 'error')
       return redirect(url_for('main.admin_schools'))

   if request.method == 'POST':
       school['name'] = request.form['name']
       school['location'] = request.form['location']
       school['background'] = request.form['background']
       school['curriculum_type'] = request.form['curriculum_type']
       student_service.save_all_schools(schools)
       flash('School updated successfully!', 'success')
       return redirect(url_for('main.admin_schools'))

   return render_template('edit_school.html', school=school)

@main.route('/admin/schools/delete/<school_id>', methods=['POST'])
def delete_school(school_id):
   if not check_auth():
       return redirect(url_for('main.admin_login'))
       
   schools = student_service.get_all_schools()
   schools = [s for s in schools if s['school_id'] != school_id]
   student_service.save_all_schools(schools)
   flash('School deleted successfully!', 'success')
   return redirect(url_for('main.admin_schools'))

# File browser routes
@main.route('/admin/files')
def admin_files():
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    path = request.args.get('path', 'data')
    
    # Security: ensure path is within data directory
    if not path.startswith('data'):
        path = 'data'
    
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
    if path != 'data':
        path_parts = path.split('/')
        for i, part in enumerate(path_parts):
            breadcrumb_parts.append({
                'name': part,
                'path': '/'.join(path_parts[:i+1])
            })
    
    # Calculate parent path for back button
    parent_path = '/'.join(path.split('/')[:-1]) if '/' in path and path != 'data' else ''
    
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

@main.route('/admin/files/view')
def admin_file_view():
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    file_path = request.args.get('path')
    if not file_path or not file_path.startswith('data'):
        flash('Invalid file path', 'error')
        return redirect(url_for('main.admin_files'))
    
    if not os.path.exists(file_path):
        flash('File not found', 'error')
        return redirect(url_for('main.admin_files'))
    
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
        return redirect(url_for('main.admin_files'))

# System info route
@main.route('/admin/system')
def admin_system():
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    stats = student_service.get_system_stats()
    
    # Get the latest phone mappings
    phone_mappings = student_service.get_phone_mappings()
    
    # Get students info for phone mapping display
    students = student_service.get_all_students()
    students_info = {}
    for student in students:
        students_info[student.id] = {
            'name': student.name,
            'id': student.id,
            'grade': student.grade
        }
    
    # Get recent system events from system logs
    try:
        recent_events = system_logger.get_logs(days=1, limit=10)  # Last 24 hours, max 10 events
        system_events = []
        
        for log_entry in recent_events:
            # Convert log entry to system event format
            event = {
                'timestamp': log_entry.get('timestamp', ''),
                'message': log_entry.get('message', ''),
                'user': log_entry.get('metadata', {}).get('admin_user', log_entry.get('metadata', {}).get('user', 'System')),
                'status': 'success' if log_entry.get('level', '').upper() in ['INFO', 'DEBUG'] else 'warning' if log_entry.get('level', '').upper() == 'WARNING' else 'error'
            }
            system_events.append(event)
        
        print(f"📋 Loaded {len(system_events)} recent system events for display")
        
    except Exception as e:
        print(f"⚠️ Error fetching system events: {e}")
        system_events = []
    
    return render_template('system.html',
                         stats=stats,
                         phone_mappings=phone_mappings,
                         students_info=students_info,
                         system_stats=stats,
                         mcp_port=3001,
                         vapi_status=vapi_client.is_configured(),
                         system_events=system_events)

# Phone Mapping Management
@main.route('/admin/phone-mappings/remove', methods=['POST'])
def remove_phone_mapping():
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    phone_number = request.form.get('phone_number')
    if not phone_number:
        return jsonify({'error': 'Phone number is required'}), 400
    
    if student_service.remove_phone_mapping(phone_number):
        flash(f'Phone mapping for {phone_number} removed successfully', 'success')
        return jsonify({'success': True, 'message': 'Phone mapping removed'})
    else:
        return jsonify({'error': 'Phone mapping not found'}), 404

@main.route('/admin/phone-mappings/add', methods=['POST'])
def add_phone_mapping():
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    phone_number = request.form.get('phone_number')
    student_id = request.form.get('student_id')
    
    if not phone_number or not student_id:
        return jsonify({'error': 'Phone number and student ID are required'}), 400
    
    # Check if student exists
    if not student_service.student_exists(student_id):
        return jsonify({'error': 'Student not found'}), 404
    
    student_service.add_phone_mapping(phone_number, student_id)
    
    flash(f'Phone mapping added: {phone_number} → {student_id}', 'success')
    return jsonify({'success': True, 'message': 'Phone mapping added'})

# Student CRUD Operations
@main.route('/admin/students/add', methods=['GET', 'POST'])
def add_student():
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
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
        
        # Create student
        student_id = student_service.create_student(
            name=name,
            age=int(age),
            grade=int(grade),
            interests=interests,
            phone=phone
        )
        
        flash(f'Student {name} added successfully!', 'success')
        return redirect(url_for('main.admin_student_detail', student_id=student_id))
    
    return render_template('add_student.html')

@main.route('/admin/students/<student_id>/edit', methods=['GET', 'POST'])
def edit_student(student_id):
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    student_data = student_service.get_student_data(student_id)
    if not student_data:
        flash(f'Student {student_id} not found', 'error')
        return redirect(url_for('main.admin_students'))
    
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
        
        # Update student
        student_service.update_student(
            student_id=student_id,
            name=name,
            age=int(age),
            grade=int(grade),
            interests=interests,
            phone=phone
        )
        
        flash(f'Student {name} updated successfully!', 'success')
        return redirect(url_for('main.admin_student_detail', student_id=student_id))
    
    # Get current phone
    phone = student_service.get_student_phone(student_id)
    
    return render_template('edit_student.html',
                         student=student_data.get('profile', {}),
                         student_id=student_id,
                         phone=phone)

@main.route('/admin/students/<student_id>/delete', methods=['POST'])
def delete_student(student_id):
    """Delete a student and all associated data"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Check if student exists
        if not student_service.student_exists(student_id):
            return jsonify({'error': 'Student not found'}), 404
        
        # Get student name for logging
        student_name = student_service.get_student_name(student_id)
        
        # Delete student
        student_service.delete_student(student_id)
        
        log_admin_action('delete_student', session.get('admin_username', 'unknown'),
                        student_id=student_id,
                        student_name=student_name,
                        ip_address=request.remote_addr)
        
        return jsonify({
            'success': True,
            'message': f'Student {student_name} deleted successfully',
            'student_id': student_id,
            'redirect': url_for('main.admin_students')
        })
        
    except Exception as e:
        log_error('ADMIN', f'Error deleting student {student_id}', e,
                 student_id=student_id,
                 admin_user=session.get('admin_username', 'unknown'))
        return jsonify({'error': f'Failed to delete student: {str(e)}'}), 500

# All Sessions Overview Route
@main.route('/admin/sessions')
def admin_all_sessions():
    """View all sessions across all students"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    # Get all sessions
    all_sessions = session_service.get_all_sessions()
    
    # Calculate session statistics
    session_stats = session_service.get_session_stats()
    
    return render_template('all_sessions.html',
                         sessions=all_sessions,
                         session_stats=session_stats)

# Session and Assessment Viewer
@main.route('/admin/students/<student_id>/sessions')
def view_student_sessions(student_id):
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    student_data = student_service.get_student_data(student_id)
    if not student_data:
        flash(f'Student {student_id} not found', 'error')
        return redirect(url_for('main.admin_students'))
    
    # Get student sessions
    sessions = session_service.get_student_sessions(student_id)
    
    return render_template('session_list.html',
                         student=student_data.get('profile', {}),
                         student_id=student_id,
                         sessions=sessions)

@main.route('/admin/sessions/<student_id>/<session_file>')
def view_session_detail(student_id, session_file):
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    # Get session details
    session_data, transcript, analysis = session_service.get_session_details(student_id, session_file)
    
    if not session_data:
        flash('Session file not found', 'error')
        return redirect(url_for('main.view_student_sessions', student_id=student_id))
    
    return render_template('session_detail.html',
                         student_id=student_id,
                         session_file=session_file,
                         session_data=session_data,
                         transcript=transcript,
                         analysis=analysis)

# AI Post-Processing Routes (POC)
@main.route('/admin/ai-analysis')
def ai_analysis_dashboard():
    """AI Analysis POC Dashboard"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    if not AI_POC_AVAILABLE:
        flash('AI Post-Processing POC is not available', 'error')
        return redirect(url_for('main.admin_dashboard'))
    
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

@main.route('/admin/ai-analysis/switch-provider', methods=['POST'])
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

@main.route('/admin/ai-analysis/test-sample', methods=['POST'])
def test_sample_analysis():
    """Test AI analysis with sample data"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    if not AI_POC_AVAILABLE:
        flash('AI POC not available', 'error')
        return redirect(url_for('main.ai_analysis_dashboard'))
    
    try:
        # Use the sample data from session_processor
        from ai.session_processor import SAMPLE_TRANSCRIPT, SAMPLE_STUDENT_CONTEXT
        
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
        return redirect(url_for('main.ai_analysis_dashboard'))

@main.route('/admin/ai-analysis/analyze-student/<student_id>')
def analyze_student_session(student_id):
    """Analyze a real student session"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    if not AI_POC_AVAILABLE:
        flash('AI POC not available', 'error')
        return redirect(url_for('main.ai_analysis_dashboard'))
    
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
        return redirect(url_for('main.ai_analysis_dashboard'))
    except Exception as e:
        flash(f'Analysis failed: {str(e)}', 'error')
        return redirect(url_for('main.ai_analysis_dashboard'))

@main.route('/admin/ai-analysis/reset-stats', methods=['POST'])
def reset_ai_stats():
    """Reset AI processing statistics"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    if not AI_POC_AVAILABLE:
        return jsonify({'error': 'AI POC not available'}), 503
    
    session_processor.reset_stats()
    flash('AI processing statistics reset', 'success')
    return jsonify({'success': True})

# System Logs Routes
@main.route('/admin/logs')
def admin_system_logs():
    """View system logs with filtering"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
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

@main.route('/admin/logs/export')
def export_logs():
    """Export logs as JSON file"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    try:
        # Get filter parameters
        days = int(request.args.get('days', 7))
        category = request.args.get('category', '')
        level = request.args.get('level', '')
        
        # Get logs from system_logger
        logs = system_logger.get_logs(days=days, category=category, level=level)
        
        # Create a temporary file
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_file.write(json.dumps(logs, indent=2).encode('utf-8'))
        temp_file.close()
        
        # Log the export
        log_admin_action('export_logs', session.get('admin_username', 'unknown'),
                        days_filter=days,
                        category_filter=category,
                        level_filter=level,
                        log_count=len(logs))
        
        # Send the file
        return send_file(temp_file.name,
                        as_attachment=True,
                        download_name=f'logs_{datetime.now().strftime("%Y-%m-%d")}.json')
    except Exception as e:
        flash(f'Error exporting logs: {str(e)}', 'error')
        log_error('DATABASE', 'Error exporting logs', e)
        return redirect(url_for('main.admin_system_logs'))

@main.route('/admin/logs/cleanup', methods=['POST'])
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
@main.route('/admin/tokens')
def admin_tokens():
    """Token generation page for debugging and testing"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    # Get active tokens
    active_tokens = token_service.get_active_tokens()
    
    return render_template('admin/generate_token.html',
                         active_tokens=active_tokens)

@main.route('/admin/tokens/generate', methods=['POST'])
def generate_token():
    """Generate a new access token"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    # Get form data
    token_name = request.form.get('token_name', 'Unnamed Token')
    scopes = request.form.getlist('scopes')
    expiration_hours = int(request.form.get('expiration', 4))
    
    if not scopes:
        flash('At least one scope must be selected', 'error')
        return redirect(url_for('main.admin_tokens'))
    
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

@main.route('/admin/tokens/revoke/<token_id>', methods=['POST'])
def revoke_token(token_id):
    """Revoke an access token"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    # Revoke token
    if token_service.revoke_token(token_id):
        log_admin_action('revoke_token', session.get('admin_username', 'unknown'),
                        token_id=token_id)
        flash('Token revoked successfully', 'success')
    else:
        flash('Token not found or already revoked', 'error')
    
    return redirect(url_for('main.admin_tokens'))

# Analytics Dashboard Routes
@main.route('/admin/analytics')
def analytics_dashboard():
    """Analytics dashboard with system-wide metrics"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    # Initialize analytics service with db session
    from app import db
    analytics_service.repository.session = db.session
    
    # Get time range from query parameters
    time_range = request.args.get('range', 'week')
    
    # Get dashboard data
    dashboard_data = analytics_service.get_dashboard_data(time_range)
    
    log_admin_action('view_analytics', session.get('admin_username', 'unknown'),
                    time_range=time_range)
    
    return render_template('admin/analytics.html',
                         data=dashboard_data,
                         time_range=time_range)

@main.route('/admin/analytics/student/<student_id>')
def student_analytics(student_id):
    """Analytics for a specific student"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    # Initialize analytics service with db session
    from app import db
    analytics_service.repository.session = db.session
    
    # Check if student exists
    if not student_service.student_exists(student_id):
        flash(f'Student {student_id} not found', 'error')
        return redirect(url_for('main.admin_students'))
    
    # Get student data
    student_data = student_service.get_student_data(student_id)
    
    # Get analytics data
    analytics_data = analytics_service.get_student_analytics(student_id)
    
    log_admin_action('view_student_analytics', session.get('admin_username', 'unknown'),
                    student_id=student_id)
    
    return render_template('admin/student_analytics.html',
                         student=student_data.get('profile', {}),
                         student_id=student_id,
                         analytics=analytics_data)

@main.route('/admin/analytics/report')
def system_report():
    """Generate and view system reports"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    # Initialize analytics service with db session
    from app import db
    analytics_service.repository.session = db.session
    
    # Get days parameter
    days = int(request.args.get('days', 30))
    
    # Check if there's a task ID for a report generation
    task_id = request.args.get('task_id')
    
    if task_id:
        # Check task status
        task_status = analytics_service.get_aggregation_task_status(task_id)
        
        if task_status['status'] == 'completed':
            # Task completed, show the report
            report_data = task_status['result']
            return render_template('admin/system_report.html',
                                 report=report_data,
                                 days=days,
                                 task_id=None)
        elif task_status['status'] == 'processing':
            # Task still processing, show waiting page
            flash('Report generation in progress...', 'info')
            return render_template('admin/report_processing.html',
                                 task_id=task_id,
                                 days=days)
        else:
            # Task failed
            flash(f'Report generation failed: {task_status.get("error", "Unknown error")}', 'error')
    
    # No task ID or task failed, show form to generate a new report
    return render_template('admin/generate_report.html', days=days)

@main.route('/admin/analytics/report/generate', methods=['POST'])
def generate_system_report():
    """Generate a new system report"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Initialize analytics service with db session
    from app import db
    analytics_service.repository.session = db.session
    
    # Get days parameter
    days = int(request.form.get('days', 30))
    
    # Import the task directly
    from app.tasks.analytics_tasks import generate_system_report
    
    # Start the task
    task = generate_system_report.delay(days=days)
    
    log_admin_action('generate_system_report', session.get('admin_username', 'unknown'),
                    days=days,
                    task_id=task.id)
    
    return jsonify({
        'success': True,
        'task_id': task.id,
        'redirect': url_for('main.system_report', task_id=task.id, days=days)
    })

@main.route('/admin/analytics/tasks')
def analytics_tasks():
    """Manage analytics tasks"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    # Initialize analytics service with db session
    from app import db
    analytics_service.repository.session = db.session
    
    # Get task ID if provided
    task_id = request.args.get('task_id')
    task_status = None
    
    if task_id:
        # Get task status
        task_status = analytics_service.get_aggregation_task_status(task_id)
    
    return render_template('admin/analytics_tasks.html',
                         task_id=task_id,
                         task_status=task_status)

@main.route('/admin/analytics/tasks/aggregate', methods=['POST'])
def run_aggregation_task():
    """Run daily stats aggregation task"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Initialize analytics service with db session
    from app import db
    analytics_service.repository.session = db.session
    
    # Get date parameter if provided
    date = request.form.get('date')
    
    # Schedule the task
    task_id = analytics_service.schedule_metrics_aggregation()
    
    log_admin_action('run_aggregation_task', session.get('admin_username', 'unknown'),
                    date=date,
                    task_id=task_id)
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'redirect': url_for('main.analytics_tasks', task_id=task_id)
    })

@main.route('/admin/analytics/tasks/status/<task_id>')
def check_task_status(task_id):
    """Check the status of an analytics task"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Initialize analytics service with db session
    from app import db
    analytics_service.repository.session = db.session
    
    # Get task status
    task_status = analytics_service.get_aggregation_task_status(task_id)
    
    return jsonify(task_status)

# Database Management Routes
@main.route('/admin/database')
def admin_database():
    """Database management interface"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    # Get database statistics
    from app import db
    from sqlalchemy import inspect, text
    
    try:
        # Use SQLAlchemy inspector to auto-discover all tables
        inspector = inspect(db.engine)
        all_table_names = inspector.get_table_names()
        
        print(f"📊 Auto-discovered {len(all_table_names)} database tables: {all_table_names}")
        
        # All tables will use the generic table viewer
        
        # Auto-discover all tables and get their counts
        tables = []
        stats = {}
        total_records = 0
        
        for table_name in sorted(all_table_names):
            try:
                # Get record count for each table using raw SQL
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                total_records += count
                
                # Add to tables list
                tables.append({
                    'name': table_name,
                    'count': count
                })
                
                # Add to stats for main tables
                if table_name in ['students', 'schools', 'curriculums', 'sessions', 'student_subjects']:
                    if table_name == 'student_subjects':
                        stats['assessments'] = count
                    else:
                        stats[table_name] = count
                
            except Exception as e:
                print(f"⚠️ Error counting records in table {table_name}: {e}")
                tables.append({
                    'name': table_name,
                    'count': 0
                })
        
        # Ensure all required stats fields exist
        required_stats = ['students', 'schools', 'curriculums', 'sessions', 'assessments']
        for stat in required_stats:
            if stat not in stats:
                stats[stat] = 0
        
        # Check for default curriculum
        default_curriculum = None
        default_curriculum_name = None
        
        if 'curriculums' in all_table_names:
            try:
                result = db.session.execute(text("SELECT name FROM curriculums WHERE is_default = true LIMIT 1"))
                default_row = result.fetchone()
                if default_row:
                    default_curriculum_name = default_row[0]
                    default_curriculum = True
                else:
                    default_curriculum = False
            except Exception as e:
                print(f"⚠️ Error checking default curriculum: {e}")
                default_curriculum = False
        else:
            default_curriculum = False
        
        # Database stats for detailed info
        db_stats = {
            'total_tables': len(all_table_names),
            'total_records': total_records,
            'curriculum_count': stats.get('curriculums', 0),
            'student_count': stats.get('students', 0),
            'session_count': stats.get('sessions', 0),
            'has_default_curriculum': default_curriculum,
            'default_curriculum_name': default_curriculum_name
        }
        
        print(f"✅ Database discovery complete: {len(tables)} tables found, {total_records} total records")
        
    except Exception as e:
        print(f"❌ Error in admin_database: {e}")
        stats = {
            'students': 0,
            'schools': 0,
            'curriculums': 0,
            'sessions': 0,
            'assessments': 0
        }
        
        db_stats = {
            'total_tables': 0,
            'total_records': 0,
            'curriculum_count': 0,
            'student_count': 0,
            'session_count': 0,
            'has_default_curriculum': False,
            'default_curriculum_name': None,
            'error': str(e)
        }
        
        tables = []
    
    return render_template('database.html', stats=stats, db_stats=db_stats, tables=tables)

@main.route('/admin/database/reset', methods=['POST'])
def reset_database():
    """Reset database and reload curriculum data"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        from app import db
        from app.models.curriculum import Curriculum, Subject, CurriculumDetail
        from app.models.student import Student
        from app.models.assessment import StudentSubject
        from app.models.session import Session
        from app.models.analytics import SessionMetrics, DailyStats
        from app.models.school import School
        from app.models.system_log import SystemLog
        from app.models.token import Token
        
        # Import requests for GitHub data fetching
        import requests
        import urllib.request
        import urllib.error
        
        log_admin_action('database_reset_start', session.get('admin_username', 'unknown'))
        
        # Drop all tables with CASCADE to handle foreign key constraints
        print("🗑️ Dropping all tables with CASCADE...")
        
        # Use raw SQL to drop entire schema and recreate
        from sqlalchemy import text
        try:
            # Drop all tables at once with CASCADE to handle all dependencies
            print("🗑️ Dropping all tables with CASCADE in one command...")
            db.session.execute(text('DROP SCHEMA public CASCADE'))
            db.session.execute(text('CREATE SCHEMA public'))
            db.session.execute(text('GRANT ALL ON SCHEMA public TO postgres'))
            db.session.execute(text('GRANT ALL ON SCHEMA public TO public'))
            db.session.commit()
            print("✅ Schema dropped and recreated successfully")
            
        except Exception as schema_error:
            print(f"⚠️ Schema drop failed: {schema_error}, trying individual table drops...")
            db.session.rollback()
            
            try:
                # Fallback: Get all table names and drop in reverse dependency order
                inspector = inspect(db.engine)
                all_table_names = inspector.get_table_names()
                print(f"📋 Found {len(all_table_names)} tables to drop: {all_table_names}")
                
                # Drop each table individually with CASCADE
                for table_name in all_table_names:
                    try:
                        print(f"🗑️ Dropping table: {table_name}")
                        db.session.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
                        db.session.commit()
                    except Exception as table_error:
                        print(f"⚠️ Error dropping table {table_name}: {table_error}")
                        db.session.rollback()
                
                print("✅ All tables dropped successfully with individual CASCADE")
                
            except Exception as drop_error:
                print(f"⚠️ Error in individual drops, trying db.drop_all(): {drop_error}")
                db.session.rollback()
                # Final fallback to standard drop_all
                db.drop_all()
                print("✅ Tables dropped with db.drop_all()")
        
        # Create all tables fresh
        print("🏗️ Creating fresh database schema...")
        db.create_all()
        print("✅ Fresh schema created successfully")
        
        # Load Cambridge Primary 2025 curriculum data
        print("📚 Loading Cambridge Primary 2025 curriculum data...")
        
        # GitHub raw URL for the curriculum data
        github_url = "https://raw.githubusercontent.com/henrikthome-arch/ai-tutor/main/ai-tutor/data/curriculum/cambridge_primary_2025.txt"
        
        try:
            # Try with requests first
            print(f"🔍 Fetching curriculum data from GitHub: {github_url}")
            response = requests.get(github_url, timeout=30)
            response.raise_for_status()
            curriculum_data = response.text
            print(f"✅ Successfully downloaded curriculum data ({len(curriculum_data)} characters)")
        except Exception as e:
            print(f"⚠️ Requests failed: {e}, trying urllib...")
            try:
                with urllib.request.urlopen(github_url, timeout=30) as response:
                    curriculum_data = response.read().decode('utf-8')
                print(f"✅ Successfully downloaded curriculum data with urllib ({len(curriculum_data)} characters)")
            except Exception as e2:
                print(f"❌ Failed to download curriculum data: {e2}")
                return jsonify({'error': f'Failed to download curriculum data: {str(e2)}'}), 500
        
        # Create the default Cambridge curriculum
        cambridge_curriculum = Curriculum(
            name='Cambridge Primary 2025',
            description='Cambridge Primary Programme for Grades 1-6 with comprehensive subject coverage',
            curriculum_type='Cambridge',
            grade_levels=[1, 2, 3, 4, 5, 6],
            is_template=True,
            is_default=True,
            created_by='system'
        )
        
        db.session.add(cambridge_curriculum)
        db.session.flush()  # Get the curriculum ID
        print(f"📚 Curriculum created with ID: {cambridge_curriculum.id}")
        
        # Parse the downloaded TSV data and create subjects and curriculum details
        lines = curriculum_data.strip().split('\n')
        print(f"📄 Processing {len(lines)} lines from downloaded curriculum data")
        
        # Track unique subjects
        subjects_dict = {}
        curriculum_details = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                # Parse TSV format: Grade	Subject	Mandatory	Details
                parts = line.split('\t')
                if len(parts) < 4:
                    print(f"⚠️ Line {line_num}: Not enough columns ({len(parts)}), skipping")
                    continue
                
                grade_level = int(parts[0])
                subject_name = parts[1].strip()
                is_mandatory_str = parts[2].strip()
                details = parts[3].strip()
                
                # Convert mandatory field
                is_mandatory = is_mandatory_str.lower() == 'yes'
                
                # Create or get subject
                if subject_name not in subjects_dict:
                    # Determine subject category
                    subject_category = 'General'
                    if subject_name.lower() in ['mathematics', 'maths', 'math', 'science', 'computing', 'ict']:
                        subject_category = 'STEM'
                    elif subject_name.lower() in ['english', 'language', 'literacy', 'writing', 'reading']:
                        subject_category = 'Language Arts'
                    elif subject_name.lower() in ['art', 'music', 'drama', 'creative']:
                        subject_category = 'Arts'
                    elif subject_name.lower() in ['history', 'geography', 'social studies', 'pshe']:
                        subject_category = 'Humanities'
                    elif subject_name.lower() in ['pe', 'physical education', 'sports']:
                        subject_category = 'Physical Education'
                    
                    # Create new subject
                    subject = Subject(
                        name=subject_name,
                        description=f'{subject_name} curriculum for primary education',
                        category=subject_category,
                        is_core=True
                    )
                    
                    db.session.add(subject)
                    db.session.flush()  # Get the subject ID
                    subjects_dict[subject_name] = subject
                    print(f"📖 Created subject: {subject_name} (ID: {subject.id})")
                else:
                    subject = subjects_dict[subject_name]
                
                # Create curriculum detail with proper relationships
                detail = CurriculumDetail(
                    curriculum_id=cambridge_curriculum.id,
                    subject_id=subject.id,
                    grade_level=grade_level,
                    is_mandatory=is_mandatory,
                    learning_objectives=[details] if details else [],
                    assessment_criteria=[],
                    recommended_hours_per_week=None,
                    prerequisites=[],
                    resources=[],
                    goals_description=details
                )
                
                curriculum_details.append(detail)
                
            except (ValueError, IndexError) as e:
                print(f"⚠️ Line {line_num}: Parse error - {e}")
                continue
        
        # Bulk insert curriculum details
        if curriculum_details:
            db.session.bulk_save_objects(curriculum_details)
            print(f"📚 Added {len(curriculum_details)} curriculum details")
        
        # Commit all changes
        db.session.commit()
        
        log_admin_action('database_reset_complete', session.get('admin_username', 'unknown'),
                        curriculum_count=len(curriculum_details),
                        subjects_count=len(subjects_dict))
        
        return jsonify({
            'success': True,
            'message': f'Database reset successfully. Created {len(subjects_dict)} subjects and {len(curriculum_details)} curriculum entries.',
            'curriculum_id': cambridge_curriculum.id,
            'subjects_count': len(subjects_dict),
            'curriculum_details_count': len(curriculum_details),
            'results': {
                'tables_dropped': True,
                'tables_created': True,
                'curriculum_loaded': True,
                'curriculum_details': len(curriculum_details),
                'total_subjects': len(subjects_dict)
            }
        })
        
    except Exception as e:
        db.session.rollback()
        log_error('DATABASE', 'Database reset failed', e)
        print(f"❌ Database reset failed: {str(e)}")
        return jsonify({'error': f'Database reset failed: {str(e)}'}), 500

# Curriculum Management Routes
@main.route('/admin/curriculum')
def admin_curriculum():
    """Curriculum management interface"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    from app import db
    from app.models.curriculum import Curriculum, CurriculumDetail
    
    try:
        from app.models.curriculum import Subject
        
        # Get all curriculums with their details count and subjects count
        curriculums = db.session.query(Curriculum).all()
        
        curriculum_data = []
        total_details = 0
        default_curriculum = None
        
        for curriculum in curriculums:
            details_count = db.session.query(CurriculumDetail).filter_by(curriculum_id=curriculum.id).count()
            
            # Get unique subjects for this curriculum
            subjects_count = db.session.query(Subject.id)\
                                    .join(CurriculumDetail, Subject.id == CurriculumDetail.subject_id)\
                                    .filter(CurriculumDetail.curriculum_id == curriculum.id)\
                                    .distinct().count()
            
            total_details += details_count
            
            curriculum_info = {
                'id': curriculum.id,
                'name': curriculum.name,
                'description': curriculum.description,
                'curriculum_type': curriculum.curriculum_type,
                'grade_levels': curriculum.grade_levels,
                'is_default': curriculum.is_default,
                'is_template': curriculum.is_template,
                'created_by': curriculum.created_by,
                'created_at': curriculum.created_at,
                'details_count': details_count,
                'subjects_count': subjects_count
            }
            
            curriculum_data.append(curriculum_info)
            
            if curriculum.is_default:
                default_curriculum = curriculum_info
                
            print(f"📚 Curriculum {curriculum.name}: {subjects_count} subjects, {details_count} details")
        
        stats = {
            'total_curriculums': len(curriculums),
            'total_curriculum_details': total_details,
            'has_default': default_curriculum is not None,
            'default_curriculum': default_curriculum
        }
        
    except Exception as e:
        curriculum_data = []
        stats = {
            'total_curriculums': 0,
            'total_curriculum_details': 0,
            'has_default': False,
            'default_curriculum': None,
            'error': str(e)
        }
    
    return render_template('curriculum.html',
                         curriculums=curriculum_data,
                         curriculum_stats=stats)

@main.route('/admin/curriculum/<int:curriculum_id>')
def curriculum_details(curriculum_id):
    """View curriculum details"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    try:
        from app import db
        from app.models.curriculum import Curriculum, CurriculumDetail
        from app.models.curriculum import Subject
        
        curriculum = db.session.query(Curriculum).get(curriculum_id)
        if not curriculum:
            flash('Curriculum not found', 'error')
            return redirect(url_for('main.admin_curriculum'))
        
        print(f"📋 Loading curriculum details for curriculum {curriculum_id}: {curriculum.name}")
        
        # Get curriculum details with eager loading of subject relationship
        details = db.session.query(CurriculumDetail)\
                           .join(Subject, CurriculumDetail.subject_id == Subject.id)\
                           .filter(CurriculumDetail.curriculum_id == curriculum_id)\
                           .order_by(CurriculumDetail.grade_level)\
                           .all()
        
        print(f"📊 Found {len(details)} curriculum details")
        
        # Group details by subject (as expected by template)
        details_by_subject = {}
        for detail in details:
            try:
                subject_name = detail.subject.name if detail.subject else 'Unknown Subject'
                grade = detail.grade_level
                
                print(f"📖 Processing {subject_name} for grade {grade}")
                
                # Initialize subject if not exists
                if subject_name not in details_by_subject:
                    details_by_subject[subject_name] = {
                        'subject': detail.subject,
                        'grades': {}
                    }
                
                # Add grade-specific detail to subject
                details_by_subject[subject_name]['grades'][grade] = {
                    'id': detail.id,
                    'subject_name': subject_name,
                    'goals_description': detail.goals_description,
                    'learning_objectives': detail.learning_objectives or [],
                    'is_mandatory': detail.is_mandatory,
                    'recommended_hours_per_week': detail.recommended_hours_per_week
                }
            except Exception as detail_error:
                print(f"❌ Error processing detail {detail.id}: {detail_error}")
                continue
        
        print(f"✅ Successfully grouped {len(details_by_subject)} subjects")
        
        return render_template('curriculum_details.html',
                             curriculum=curriculum,
                             details_by_subject=details_by_subject,
                             total_details=len(details))
                             
    except Exception as e:
        print(f"❌ Error in curriculum_details for curriculum {curriculum_id}: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error loading curriculum details: {str(e)}', 'error')
        return redirect(url_for('main.admin_curriculum'))

# MCP Interactions Management Routes
@main.route('/admin/mcp-interactions')
def admin_mcp_interactions():
    """MCP interactions monitoring and management"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    # Get query parameters for filtering and pagination
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 50)), 200)  # Max 200 per page
    session_id = request.args.get('session_id')
    token_id = request.args.get('token_id', type=int)
    
    # Get interactions with pagination
    interactions_data = mcp_interaction_service.get_interactions(
        page=page,
        per_page=per_page,
        session_id=session_id,
        token_id=token_id
    )
    
    # Get summary statistics
    summary_stats = mcp_interaction_service.get_summary_statistics(hours=24)
    
    # Get health metrics
    health_metrics = mcp_interaction_service.get_system_health_metrics()
    
    # Get endpoint statistics
    endpoint_stats = mcp_interaction_service.get_endpoint_statistics(hours=24)
    
    # Get active tokens for filtering
    active_tokens = token_service.get_active_tokens()
    
    log_admin_action('view_mcp_interactions', session.get('admin_username', 'unknown'),
                    page=page,
                    per_page=per_page,
                    session_filter=session_id,
                    token_filter=token_id,
                    total_interactions=interactions_data.get('total', 0))
    
    return render_template('mcp_interactions.html',
                         interactions=interactions_data,
                         summary_stats=summary_stats,
                         health_metrics=health_metrics,
                         endpoint_stats=endpoint_stats,
                         active_tokens=active_tokens,
                         current_filters={
                             'session_id': session_id,
                             'token_id': token_id,
                             'page': page,
                             'per_page': per_page
                         })

@main.route('/admin/mcp-interactions/<int:interaction_id>')
def mcp_interaction_detail(interaction_id):
    """View detailed information about a specific MCP interaction"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    # Get interaction details
    interaction = mcp_interaction_service.get_interaction_details(
        interaction_id=interaction_id,
        include_payloads=True
    )
    
    if not interaction:
        flash('MCP interaction not found', 'error')
        return redirect(url_for('main.admin_mcp_interactions'))
    
    log_admin_action('view_mcp_interaction_detail', session.get('admin_username', 'unknown'),
                    interaction_id=interaction_id)
    
    return render_template('mcp_interaction_detail.html',
                         interaction=interaction)

@main.route('/admin/mcp-interactions/cleanup', methods=['POST'])
def cleanup_mcp_interactions():
    """Clean up old MCP interaction records"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get days parameter
    days = int(request.form.get('days', 30))
    
    if days < 1:
        return jsonify({'error': 'Days must be at least 1'}), 400
    
    try:
        # Clean up old interactions
        deleted_count = mcp_interaction_service.cleanup_old_interactions(days)
        
        log_admin_action('cleanup_mcp_interactions', session.get('admin_username', 'unknown'),
                        days=days,
                        deleted_count=deleted_count)
        
        flash(f'Cleaned up {deleted_count} old MCP interactions', 'success')
        return jsonify({
            'success': True,
            'message': f'Cleaned up {deleted_count} old interactions',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        log_error('ADMIN', f'Error cleaning up MCP interactions: {str(e)}', e,
                 days=days,
                 admin_user=session.get('admin_username', 'unknown'))
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500

@main.route('/admin/mcp-interactions/search')
def search_mcp_interactions():
    """Search MCP interactions with advanced filters"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    # Get search parameters
    endpoint = request.args.get('endpoint')
    status_code = request.args.get('status_code', type=int)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    limit = min(int(request.args.get('limit', 100)), 1000)  # Max 1000 results
    
    # Parse dates if provided
    start_date = None
    end_date = None
    try:
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
    except ValueError as e:
        flash(f'Invalid date format: {str(e)}', 'error')
        return redirect(url_for('main.admin_mcp_interactions'))
    
    # Search interactions
    interactions = mcp_interaction_service.search_interactions(
        endpoint=endpoint,
        status_code=status_code,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    log_admin_action('search_mcp_interactions', session.get('admin_username', 'unknown'),
                    endpoint=endpoint,
                    status_code=status_code,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    result_count=len(interactions))
    
    return render_template('mcp_interactions_search.html',
                         interactions=interactions,
                         search_filters={
                             'endpoint': endpoint,
                             'status_code': status_code,
                             'start_date': start_date_str,
                             'end_date': end_date_str,
                             'limit': limit
                         },
                         result_count=len(interactions))

# Generic Database Table Viewer Route
@main.route('/admin/database/table/<table_name>')
def view_database_table(table_name):
   """Generic database table viewer for any table"""
   if not check_auth():
       return redirect(url_for('main.admin_login'))
   
   from app import db
   from sqlalchemy import text, inspect
   
   try:
       # Validate table exists using SQLAlchemy inspector
       inspector = inspect(db.engine)
       all_table_names = inspector.get_table_names()
       
       if table_name not in all_table_names:
           flash(f'Table "{table_name}" not found in database', 'error')
           return redirect(url_for('main.admin_database'))
       
       # Get table columns
       columns_info = inspector.get_columns(table_name)
       columns = [col['name'] for col in columns_info]
       
       # Get all rows from the table
       query = text(f"SELECT * FROM {table_name} ORDER BY {columns[0]} DESC LIMIT 1000")  # Limit to 1000 rows for performance
       result = db.session.execute(query)
       
       # Convert rows to dictionaries
       rows = []
       for row in result:
           row_dict = {}
           for i, column in enumerate(columns):
               row_dict[column] = row[i]
           rows.append(row_dict)
       
       log_admin_action('view_database_table', session.get('admin_username', 'unknown'),
                       table_name=table_name,
                       row_count=len(rows))
       
       return render_template('generic_table.html',
                            table_name=table_name,
                            columns=columns,
                            rows=rows)
       
   except Exception as e:
       log_error('DATABASE', f'Error viewing table {table_name}', e)
       flash(f'Error loading table "{table_name}": {str(e)}', 'error')
       return redirect(url_for('main.admin_database'))