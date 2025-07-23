#!/usr/bin/env python3
"""
Verify database connection and tables
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect

def verify_database(database_url=None):
    """Verify database connection and tables"""
    # Get database URL from environment variable if not provided
    if not database_url:
        database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not found.")
        return False
    
    # Ensure the URL starts with postgresql:// (Render might provide postgres://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        print("🔄 Converted postgres:// to postgresql:// in database URL")
    
    try:
        # Create engine
        print(f"🔌 Connecting to database: {database_url[:10]}...")
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            print(f"✅ Database connection successful: {result}")
            
            # Get database type
            db_type = engine.dialect.name
            print(f"🗄️ Database type: {db_type}")
            
            # Get list of tables
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"📋 Tables in database: {len(tables)}")
            for table in tables:
                print(f"  - {table}")
            
            # Expected tables based on new comprehensive schema
            expected_tables = [
                'system_logs', 'sessions', 'students', 'schools',
                'curriculums', 'subjects', 'curriculum_details', 'school_default_subjects',
                'student_subjects', 'tokens', 'profiles'
            ]
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
            else:
                print("✅ All expected tables exist.")
            
            # Check table structures
            for table in tables:
                columns = inspector.get_columns(table)
                print(f"📊 Table {table} has {len(columns)} columns:")
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
            
            return True
    
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        return False

def main():
    """Main function"""
    # Get database URL from command line argument
    database_url = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Verify database
    if verify_database(database_url):
        print("✅ Database verification completed successfully.")
        sys.exit(0)
    else:
        print("❌ Database verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()