#!/usr/bin/env python3
"""
Entry point for the AI Tutor application
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('data', 'logs', f"{os.getenv('ENVIRONMENT', 'development')}.log"))
    ]
)

# Import the Flask app factory
from backend.app import create_app

# Create the Flask app
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment variables
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Log startup information
    logging.info(f"Starting AI Tutor application on {host}:{port} (debug={debug})")
    logging.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    # Run the Flask app
    app.run(host=host, port=port, debug=debug)