#!/usr/bin/env python3
"""
Database migration script to update curriculum schema
Adds missing columns to match updated Curriculum, Subject, and CurriculumDetail models
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.exc import SQLAlchemyError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment variables"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not found")
        sys.exit(1)
    return database_url

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def check_table_exists(engine, table_name):
    """Check if a table exists"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def add_column_safe(engine, table_name, column_name, column_definition):
    """Safely add a column if it doesn't exist"""
    try:
        if not check_column_exists(engine, table_name, column_name):
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            logger.info(f"Adding column {column_name} to {table_name}")
            engine.execute(text(sql))
            logger.info(f"✓ Successfully added {column_name} to {table_name}")
        else:
            logger.info(f"✓ Column {column_name} already exists in {table_name}")
    except SQLAlchemyError as e:
        logger.error(f"✗ Error adding column {column_name} to {table_name}: {e}")
        raise

def migrate_curriculums_table(engine):
    """Add missing columns to curriculums table"""
    logger.info("Migrating curriculums table...")
    
    if not check_table_exists(engine, 'curriculums'):
        logger.error("curriculums table does not exist!")
        return False
    
    # Add missing columns
    columns_to_add = [
        ('name', 'VARCHAR(100)'),
        ('description', 'TEXT'),
        ('curriculum_type', 'VARCHAR(50)'),
        ('grade_levels', 'JSON'),
        ('is_template', 'BOOLEAN DEFAULT FALSE'),
        ('created_by', 'VARCHAR(50)'),
        ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ]
    
    for column_name, column_def in columns_to_add:
        add_column_safe(engine, 'curriculums', column_name, column_def)
    
    logger.info("✓ curriculums table migration completed")
    return True

def migrate_subjects_table(engine):
    """Add missing columns to subjects table"""
    logger.info("Migrating subjects table...")
    
    if not check_table_exists(engine, 'subjects'):
        logger.error("subjects table does not exist!")
        return False
    
    # Add missing columns
    columns_to_add = [
        ('name', 'VARCHAR(100) UNIQUE'),
        ('description', 'TEXT'),
        ('category', 'VARCHAR(50)'),
        ('is_core', 'BOOLEAN DEFAULT FALSE'),
        ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ]
    
    for column_name, column_def in columns_to_add:
        add_column_safe(engine, 'subjects', column_name, column_def)
    
    logger.info("✓ subjects table migration completed")
    return True

def migrate_curriculum_details_table(engine):
    """Add missing columns to curriculum_details table"""
    logger.info("Migrating curriculum_details table...")
    
    if not check_table_exists(engine, 'curriculum_details'):
        logger.error("curriculum_details table does not exist!")
        return False
    
    # Add missing columns
    columns_to_add = [
        ('curriculum_id', 'INTEGER REFERENCES curriculums(id)'),
        ('subject_id', 'INTEGER REFERENCES subjects(id)'),
        ('grade_level', 'INTEGER'),
        ('is_mandatory', 'BOOLEAN DEFAULT TRUE'),
        ('learning_objectives', 'JSON'),
        ('assessment_criteria', 'JSON'),
        ('recommended_hours_per_week', 'INTEGER'),
        ('prerequisites', 'JSON'),
        ('resources', 'JSON'),
        ('goals_description', 'TEXT'),
        ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ]
    
    for column_name, column_def in columns_to_add:
        add_column_safe(engine, 'curriculum_details', column_name, column_def)
    
    logger.info("✓ curriculum_details table migration completed")
    return True

def create_missing_tables(engine):
    """Create any missing curriculum-related tables"""
    logger.info("Checking for missing tables...")
    
    # Create school_default_subjects table if it doesn't exist
    if not check_table_exists(engine, 'school_default_subjects'):
        logger.info("Creating school_default_subjects table...")
        sql = """
        CREATE TABLE school_default_subjects (
            id SERIAL PRIMARY KEY,
            school_id INTEGER REFERENCES schools(id),
            curriculum_detail_id INTEGER REFERENCES curriculum_details(id),
            UNIQUE(school_id, curriculum_detail_id)
        )
        """
        engine.execute(text(sql))
        logger.info("✓ school_default_subjects table created")
    
    logger.info("✓ Table creation check completed")

def main():
    """Main migration function"""
    logger.info("Starting curriculum schema migration...")
    
    try:
        # Get database connection
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        # Test connection
        engine.execute(text("SELECT 1"))
        logger.info("✓ Database connection successful")
        
        # Run migrations
        success = True
        success &= migrate_curriculums_table(engine)
        success &= migrate_subjects_table(engine)
        success &= migrate_curriculum_details_table(engine)
        create_missing_tables(engine)
        
        if success:
            logger.info("🎉 Curriculum schema migration completed successfully!")
            logger.info("The database is now ready for Cambridge curriculum loading.")
        else:
            logger.error("❌ Migration completed with errors. Please check the logs above.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()