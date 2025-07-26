#!/usr/bin/env python3
"""
Database Migration: Add AI Tutor Assessment Columns to Sessions Table

This migration adds the following columns to the sessions table:
- tutor_assessment (TEXT): AI-generated assessment of tutor performance
- prompt_suggestions (TEXT): AI-generated suggestions for prompt improvements

Usage:
    python migrate_tutor_assessment_columns.py

This script will:
1. Check if the columns already exist in the database
2. Add the missing columns if they don't exist
3. Provide detailed logging of the migration process
4. Handle errors gracefully with rollback capability
"""

import os
import sys
import logging
from sqlalchemy import text, create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment variables"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not found")
        sys.exit(1)
    return database_url

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in the specified table"""
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        column_names = [col['name'] for col in columns]
        return column_name in column_names
    except Exception as e:
        logger.error(f"Error checking if column {column_name} exists: {e}")
        return False

def migrate_tutor_assessment_columns():
    """Main migration function"""
    logger.info("Starting AI Tutor Assessment columns migration")
    
    # Get database connection
    database_url = get_database_url()
    logger.info(f"Connecting to database...")
    
    try:
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
        
        # Define the columns to add
        columns_to_add = [
            {
                'name': 'tutor_assessment',
                'definition': 'tutor_assessment TEXT',
                'description': 'AI-generated assessment of tutor performance'
            },
            {
                'name': 'prompt_suggestions', 
                'definition': 'prompt_suggestions TEXT',
                'description': 'AI-generated suggestions for prompt improvements'
            }
        ]
        
        migration_needed = False
        columns_to_migrate = []
        
        # Check which columns need to be added
        logger.info("Checking current database schema...")
        for column in columns_to_add:
            exists = check_column_exists(engine, 'sessions', column['name'])
            if exists:
                logger.info(f"✓ Column '{column['name']}' already exists in sessions table")
            else:
                logger.info(f"✗ Column '{column['name']}' missing from sessions table")
                migration_needed = True
                columns_to_migrate.append(column)
        
        if not migration_needed:
            logger.info("🎉 All AI Tutor Assessment columns already exist. No migration needed.")
            return True
        
        # Perform migration
        logger.info(f"Migration needed for {len(columns_to_migrate)} columns")
        
        with engine.begin() as conn:
            for column in columns_to_migrate:
                logger.info(f"Adding column '{column['name']}' to sessions table...")
                
                sql = f"ALTER TABLE sessions ADD COLUMN {column['definition']}"
                logger.info(f"Executing: {sql}")
                
                try:
                    conn.execute(text(sql))
                    logger.info(f"✓ Successfully added column '{column['name']}' - {column['description']}")
                except SQLAlchemyError as e:
                    logger.error(f"✗ Failed to add column '{column['name']}': {e}")
                    raise
            
            logger.info("🎉 Migration completed successfully!")
            
            # Verify the migration
            logger.info("Verifying migration results...")
            for column in columns_to_migrate:
                exists = check_column_exists(engine, 'sessions', column['name'])
                if exists:
                    logger.info(f"✓ Verified: Column '{column['name']}' now exists")
                else:
                    logger.error(f"✗ Verification failed: Column '{column['name']}' still missing")
                    raise Exception(f"Migration verification failed for column '{column['name']}'")
        
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during migration: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        return False

def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("AI TUTOR ASSESSMENT COLUMNS MIGRATION")
    logger.info("=" * 60)
    
    try:
        success = migrate_tutor_assessment_columns()
        if success:
            logger.info("Migration completed successfully!")
            sys.exit(0)
        else:
            logger.error("Migration failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()