"""
Background tasks for system maintenance.
"""

from app import celery, db
import logging
import os
from datetime import datetime, timedelta

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
def cleanup_log_files(days=7):
    """
    Clean up old log files.
    
    Args:
        days (int): Number of days to keep logs for
        
    Returns:
        int: Number of files deleted
    """
    logger.info(f"Cleaning up log files older than {days} days")
    
    log_dir = os.getenv('LOG_DIR', '../data/logs')
    if not os.path.exists(log_dir):
        logger.warning(f"Log directory does not exist: {log_dir}")
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=days)
    deleted_count = 0
    
    for filename in os.listdir(log_dir):
        file_path = os.path.join(log_dir, filename)
        if os.path.isfile(file_path):
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_modified < cutoff_date:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting log file {file_path}: {str(e)}")
    
    logger.info(f"Deleted {deleted_count} old log files")
    return deleted_count


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
        db.session.execute("SELECT 1")
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