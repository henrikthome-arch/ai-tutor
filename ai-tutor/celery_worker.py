"""
Celery worker entry point for the AI Tutor application.

This script initializes the Flask application and Celery worker.
Run this script to start the Celery worker process:

    celery -A celery_worker.celery worker --loglevel=info

For monitoring, you can also run Flower:

    celery -A celery_worker.celery flower
"""

import os
from app import create_app, celery

# Create Flask application context
app = create_app(os.getenv('FLASK_ENV', 'development'))
app_context = app.app_context()
app_context.push()

# Import tasks to ensure they are registered with Celery
import app.tasks.ai_tasks
import app.tasks.maintenance_tasks

# Export the Celery app for the worker to use
celery = app.celery