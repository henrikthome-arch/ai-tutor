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
from backend.system_logger import system_logger, log_admin_action, log_webhook, log_ai_analysis, log_error, log_system
from backend.vapi.client import vapi_client

# Import AI components
try:
    from backend.ai.session_processor import session_processor
    from backend.ai.providers import provider_manager
    from backend.ai.validator import validator
    AI_POC_AVAILABLE = True
except ImportError as e:
    AI_POC_AVAILABLE = False
    print(f"⚠️  AI POC not available: {e}")

# Import services and repositories
from backend.app.services.student_service import StudentService
from backend.app.services.session_service import SessionService

# Create blueprint
main = Blueprint('main', __name__)

# Initialize services
student_service = StudentService()
session_service = SessionService()

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
    students_info = {s['id']: s for s in student_service.get_all_students()}
    
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
        from backend.ai.session_processor import SAMPLE_TRANSCRIPT, SAMPLE_STUDENT_CONTEXT
        
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

@main.route('/admin/logs/download/<log_file>')
def download_log_file(log_file):
    """Download a specific log file"""
    if not check_auth():
        return redirect(url_for('main.admin_login'))
    
    # Security: Ensure the file is within the logs directory
    log_path = os.path.join(system_logger.log_dir, log_file)
    if not os.path.exists(log_path) or not log_path.startswith(system_logger.log_dir):
        flash('Log file not found or access denied', 'error')
        return redirect(url_for('main.admin_system_logs'))

    return send_file(log_path, as_attachment=True)

@main.route('/admin/logs/cleanup', methods=['POST'])
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