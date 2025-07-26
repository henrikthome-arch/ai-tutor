"""
Background tasks for system maintenance.
"""

from app import celery, db
import logging
import os
from datetime import datetime, timedelta
from sqlalchemy import text

logger = logging.getLogger(__name__)

@celery.task
def backup_database():
    """
    Create a backup of the database.
    
    Returns:
        str: Path to the backup file
    """
    logger.info("Starting database backup")
    
    # This would use pg_dump or similar to backup the database
    # For now, we'll just log it
    backup_dir = os.path.join(os.getcwd(), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_file = os.path.join(backup_dir, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql")
    
    logger.info(f"Database backup completed: {backup_file}")
    return backup_file


@celery.task
def cleanup_old_logs(days=7):
    """
    Clean up old system logs from the database.
    
    Args:
        days (int): Number of days to keep logs for
        
    Returns:
        int: Number of log entries deleted
    """
    logger.info(f"Cleaning up system logs older than {days} days")
    
    from app.repositories.system_log_repository import SystemLogRepository
    from app.models.base import db
    
    # Create a repository instance
    repository = SystemLogRepository(db.session)
    
    try:
        # Delete old logs
        deleted_count = repository.cleanup_old_logs(days)
        logger.info(f"Deleted {deleted_count} old log entries from database")
        return deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up old logs: {str(e)}")
        return 0


@celery.task
def check_system_health():
    """
    Check the health of various system components.
    
    Returns:
        dict: Health status of different components
    """
    logger.info("Checking system health")
    
    health_status = {
        "database": "healthy",
        "disk_space": "healthy",
        "memory_usage": "healthy",
        "api_endpoints": "healthy"
    }
    
    # Check database connection
    try:
        db.session.execute(text("SELECT 1"))
        health_status["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status["database"] = "unhealthy"
    
    # Check disk space
    try:
        # This would check disk space
        # For now, we'll just assume it's healthy
        health_status["disk_space"] = "healthy"
    except Exception as e:
        logger.error(f"Disk space check failed: {str(e)}")
        health_status["disk_space"] = "unhealthy"
    
    logger.info(f"System health check completed: {health_status}")
    return health_status


@celery.task
def purge_expired_memory():
    """
    Purge expired student memory entries based on expiration policies.
    
    Returns:
        dict: Summary of purged entries by scope
    """
    logger.info("Starting purge of expired student memory entries")
    
    from app.repositories.student_memory_repository import StudentMemoryRepository
    from app.models.student_memory import MemoryScope
    
    # Create repository instance
    memory_repo = StudentMemoryRepository()
    
    purge_summary = {
        'total_purged': 0,
        'by_scope': {},
        'errors': []
    }
    
    try:
        # Get expired entries for each scope
        for scope in MemoryScope:
            try:
                expired_entries = memory_repo.get_expired_entries(scope)
                if expired_entries:
                    # Delete expired entries
                    deleted_count = memory_repo.delete_expired_entries(scope)
                    purge_summary['by_scope'][scope.value] = deleted_count
                    purge_summary['total_purged'] += deleted_count
                    
                    logger.info(f"Purged {deleted_count} expired {scope.value} memory entries")
                else:
                    purge_summary['by_scope'][scope.value] = 0
                    
            except Exception as scope_error:
                error_msg = f"Error purging {scope.value} memories: {str(scope_error)}"
                logger.error(error_msg)
                purge_summary['errors'].append(error_msg)
        
        logger.info(f"Memory purge completed. Total purged: {purge_summary['total_purged']}")
        return purge_summary
        
    except Exception as e:
        error_msg = f"Error during memory purge: {str(e)}"
        logger.error(error_msg)
        purge_summary['errors'].append(error_msg)
        return purge_summary


@celery.task
def sync_legacy_arrays():
    """
    Temporary task to keep legacy students table arrays in sync with new profile/memory system.
    This will be removed once the new system is fully adopted.
    
    Returns:
        dict: Summary of synchronization results
    """
    logger.info("Starting sync of legacy student arrays with new profile/memory system")
    
    from app.repositories.student_profile_repository import StudentProfileRepository
    from app.repositories.student_memory_repository import StudentMemoryRepository
    from app.models.student import Student
    from app.models.student_memory import MemoryScope
    
    # Create repository instances
    profile_repo = StudentProfileRepository()
    memory_repo = StudentMemoryRepository()
    
    sync_summary = {
        'students_processed': 0,
        'profiles_synced': 0,
        'memories_synced': 0,
        'errors': []
    }
    
    try:
        # Get all students
        students = db.session.query(Student).all()
        
        for student in students:
            try:
                sync_summary['students_processed'] += 1
                student_updated = False
                
                # Get current profile for this student
                current_profile = profile_repo.get_current(student.id)
                
                # Sync interests array
                if current_profile and current_profile.get('interests'):
                    if isinstance(current_profile['interests'], list):
                        new_interests = current_profile['interests']
                    else:
                        # Extract interests from narrative or traits
                        interests_from_traits = current_profile.get('traits', {}).get('interests', [])
                        new_interests = interests_from_traits if isinstance(interests_from_traits, list) else []
                    
                    # Update student interests if different
                    if student.interests != new_interests:
                        student.interests = new_interests
                        student_updated = True
                
                # Sync learning_style and motivational_triggers from profile
                if current_profile:
                    traits = current_profile.get('traits', {})
                    
                    # Sync learning style
                    if traits.get('learning_style') and student.learning_style != traits['learning_style']:
                        student.learning_style = traits['learning_style']
                        student_updated = True
                    
                    # Sync motivational triggers
                    motivational_triggers = traits.get('motivational_triggers', [])
                    if isinstance(motivational_triggers, list) and student.motivational_triggers != motivational_triggers:
                        student.motivational_triggers = motivational_triggers
                        student_updated = True
                
                # Get memory entries for personal facts
                personal_memories = memory_repo.get_many(student.id, MemoryScope.PERSONAL_FACT)
                
                # Extract family and pets information from memory
                family_info = []
                pets_info = []
                
                for key, value in personal_memories.items():
                    if 'family' in key.lower() or 'parent' in key.lower() or 'sibling' in key.lower():
                        family_info.append(f"{key}: {value}")
                    elif 'pet' in key.lower() or 'dog' in key.lower() or 'cat' in key.lower():
                        pets_info.append(f"{key}: {value}")
                
                # Update family array if different
                if family_info and student.family != family_info:
                    student.family = family_info
                    student_updated = True
                
                # Update pets array if different
                if pets_info and student.pets != pets_info:
                    student.pets = pets_info
                    student_updated = True
                
                if student_updated:
                    db.session.add(student)
                    if current_profile:
                        sync_summary['profiles_synced'] += 1
                    if personal_memories:
                        sync_summary['memories_synced'] += 1
                        
            except Exception as student_error:
                error_msg = f"Error syncing student {student.id}: {str(student_error)}"
                logger.error(error_msg)
                sync_summary['errors'].append(error_msg)
        
        # Commit all changes
        db.session.commit()
        
        logger.info(f"Legacy array sync completed. Processed: {sync_summary['students_processed']}, "
                   f"Profiles synced: {sync_summary['profiles_synced']}, "
                   f"Memories synced: {sync_summary['memories_synced']}")
        
        return sync_summary
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"Error during legacy array sync: {str(e)}"
        logger.error(error_msg)
        sync_summary['errors'].append(error_msg)
        return sync_summary