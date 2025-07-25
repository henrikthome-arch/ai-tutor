#!/usr/bin/env python3
"""
AI Tutor Backend Application Entry Point
Uses the application factory pattern for production deployment
"""

import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import *  # Import all models to ensure they're registered

def main():
    """Main entry point for the AI Tutor backend"""
    
    # Determine environment
    env = os.getenv('FLASK_ENV', 'production')
    
    # Create application using factory pattern
    app = create_app(env)
    
    # Create database tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created/verified")
        except Exception as e:
            print(f"⚠️ Database initialization warning: {e}")
    
    # Get port from environment (Render uses PORT env var)
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    print(f"🚀 Starting AI Tutor backend on {host}:{port}")
    print(f"📊 Environment: {env}")
    print(f"🔧 Application factory initialized successfully")
    
    # Run the application
    app.run(
        host=host,
        port=port,
        debug=(env == 'development'),
        use_reloader=False  # Disable reloader in production
    )

if __name__ == '__main__':
    main()