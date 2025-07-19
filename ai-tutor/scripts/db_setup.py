#!/usr/bin/env python3
"""
Database Setup Script
Initialize and run database migrations for the AI Tutor application
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add the parent directory to the path so we can import the app
sys.path.append(str(Path(__file__).parent.parent))

def setup_environment():
    """Set up the environment variables for the Flask application"""
    os.environ['FLASK_APP'] = 'run.py'
    
    # Use development environment by default
    if 'FLASK_ENV' not in os.environ:
        os.environ['FLASK_ENV'] = 'development'
    
    print(f"Using environment: {os.environ.get('FLASK_ENV')}")

def run_command(command):
    """Run a shell command and print the output"""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print(f"Error: {result.stderr}", file=sys.stderr)
    
    return result.returncode == 0

def init_migrations():
    """Initialize the database migrations"""
    return run_command(['flask', 'db', 'init'])

def create_migration(message=None):
    """Create a new migration"""
    command = ['flask', 'db', 'migrate']
    if message:
        command.extend(['-m', message])
    
    return run_command(command)

def upgrade_database():
    """Apply all pending migrations"""
    return run_command(['flask', 'db', 'upgrade'])

def downgrade_database(steps=1):
    """Rollback migrations"""
    return run_command(['flask', 'db', 'downgrade', f'-{steps}'])

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Database setup script for AI Tutor')
    parser.add_argument('--init', action='store_true', help='Initialize migrations')
    parser.add_argument('--migrate', action='store_true', help='Create a new migration')
    parser.add_argument('--message', '-m', help='Migration message')
    parser.add_argument('--upgrade', action='store_true', help='Apply migrations')
    parser.add_argument('--downgrade', type=int, help='Rollback migrations (number of steps)')
    parser.add_argument('--env', help='Environment (development, testing, production)')
    
    args = parser.parse_args()
    
    # Set environment
    if args.env:
        os.environ['FLASK_ENV'] = args.env
    
    setup_environment()
    
    # Check if any action was specified
    if not (args.init or args.migrate or args.upgrade or args.downgrade is not None):
        # Default behavior: run all steps
        print("No specific action specified. Running full setup...")
        
        # Check if migrations directory exists
        migrations_dir = Path(__file__).parent.parent / 'migrations'
        if not migrations_dir.exists():
            print("Initializing migrations...")
            if not init_migrations():
                return 1
        
        print("Creating migration...")
        if not create_migration("Initial migration"):
            return 1
        
        print("Applying migrations...")
        if not upgrade_database():
            return 1
        
        print("Database setup complete!")
        return 0
    
    # Run specific actions
    if args.init:
        if not init_migrations():
            return 1
    
    if args.migrate:
        if not create_migration(args.message):
            return 1
    
    if args.upgrade:
        if not upgrade_database():
            return 1
    
    if args.downgrade is not None:
        if not downgrade_database(args.downgrade):
            return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())