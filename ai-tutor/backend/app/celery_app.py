"""
Celery application configuration for background task processing.
"""
from celery import Celery

def create_celery_app(app=None):
    """
    Create and configure Celery app with Flask application context.
    
    Args:
        app: Flask application instance
        
    Returns:
        Configured Celery application
    """
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        """Task that runs within Flask application context"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery