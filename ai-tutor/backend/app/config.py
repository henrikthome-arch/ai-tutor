"""
Configuration settings for the AI Tutor application
"""

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-please-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-dev-key-please-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Admin Authentication Configuration
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH')
    
    # VAPI Configuration
    VAPI_API_KEY = os.getenv('VAPI_API_KEY')
    VAPI_SECRET = os.getenv('VAPI_SECRET')
    
    # AI Provider Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    # Celery Configuration
    CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'UTC'
    
    # Logging Configuration
    LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', 30))  # Days to keep logs in database
    
    @staticmethod
    def init_app(app):
        """Initialize application configuration"""
        import hashlib
        
        # If ADMIN_PASSWORD_HASH is not set but ADMIN_PASSWORD is, hash it
        if not app.config.get('ADMIN_PASSWORD_HASH') and os.getenv('ADMIN_PASSWORD'):
            plain_password = os.getenv('ADMIN_PASSWORD')
            app.config['ADMIN_PASSWORD_HASH'] = hashlib.sha256(plain_password.encode()).hexdigest()
        
        # Set default admin password hash for development if none provided
        if not app.config.get('ADMIN_PASSWORD_HASH'):
            # Default password: "admin123" (for development only)
            app.config['ADMIN_PASSWORD_HASH'] = hashlib.sha256('admin123'.encode()).hexdigest()


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL', 'sqlite:///dev.db')
    

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///test.db')
    

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Override these in production
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    
    # Ensure HTTPS-only cookies in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True