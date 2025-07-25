"""
AI Tutor Backend Application Factory
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from app.celery_app import create_celery_app

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
celery = None

def create_app(config_name=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    if config_name == 'production':
        from app.config import ProductionConfig
        app.config.from_object(ProductionConfig)
        ProductionConfig.init_app(app)
    elif config_name == 'testing':
        from app.config import TestingConfig
        app.config.from_object(TestingConfig)
        TestingConfig.init_app(app)
    else:
        from app.config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
        DevelopmentConfig.init_app(app)
    
    # Override config from environment variables
    app.config.from_envvar('APP_CONFIG_FILE', silent=True)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Initialize Celery
    global celery
    celery = create_celery_app(app)
    app.celery = celery
    
    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp)
    
    # Create a route to test the app
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}
    
    return app