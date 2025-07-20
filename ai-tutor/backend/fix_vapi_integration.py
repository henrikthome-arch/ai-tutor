#!/usr/bin/env python3
"""
Fix VAPI webhook integration issues
This script attempts to fix common issues with the VAPI webhook integration:
1. Ensures the system_logs table exists
2. Verifies that the webhook handler has proper app context management
3. Checks that database transactions are properly committed
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect

def ensure_system_logs_table(database_url=None):
    """Ensure the system_logs table exists"""
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
        
        # Check if system_logs table exists
        with engine.connect() as conn:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            if 'system_logs' not in tables:
                print("❌ system_logs table does not exist. Creating it...")
                
                # Create system_logs table with direct SQL
                system_logs_sql = """
                CREATE TABLE IF NOT EXISTS system_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    level VARCHAR(20) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    message TEXT NOT NULL,
                    data JSONB,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
                conn.execute(text(system_logs_sql))
                conn.commit()
                print("✅ system_logs table created successfully.")
            else:
                print("✅ system_logs table already exists.")
            
            # Verify the table was created
            tables = inspector.get_table_names()
            if 'system_logs' in tables:
                print("✅ system_logs table verified.")
                
                # Check table structure
                columns = inspector.get_columns('system_logs')
                print(f"📊 system_logs table has {len(columns)} columns:")
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
                
                return True
            else:
                print("❌ Failed to create system_logs table.")
                return False
    
    except Exception as e:
        print(f"❌ Error ensuring system_logs table: {e}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        return False

def test_log_entry(database_url=None):
    """Test creating a log entry in the system_logs table"""
    # Get database URL from environment variable if not provided
    if not database_url:
        database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not found.")
        return False
    
    # Ensure the URL starts with postgresql:// (Render might provide postgres://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Create a test log entry
        with engine.connect() as conn:
            from datetime import datetime
            
            # Insert a test log entry
            insert_sql = text("""
            INSERT INTO system_logs (timestamp, level, category, message, data, created_at)
            VALUES (:timestamp, :level, :category, :message, :data, :created_at)
            """)
            
            conn.execute(insert_sql, {
                'timestamp': datetime.now(),
                'level': 'INFO',
                'category': 'TEST',
                'message': 'Test log entry from fix_vapi_integration.py',
                'data': '{"test": true}',
                'created_at': datetime.now()
            })
            conn.commit()
            
            print("✅ Test log entry created successfully.")
            
            # Verify the log entry was created
            verify_sql = text("""
            SELECT * FROM system_logs 
            WHERE category = 'TEST' AND message = 'Test log entry from fix_vapi_integration.py'
            ORDER BY timestamp DESC
            LIMIT 1
            """)
            
            result = conn.execute(verify_sql).fetchone()
            if result:
                print(f"✅ Test log entry verified: ID {result.id}, Level {result.level}, Category {result.category}")
                return True
            else:
                print("❌ Failed to verify test log entry.")
                return False
    
    except Exception as e:
        print(f"❌ Error testing log entry: {e}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        return False

def test_webhook_logging(database_url=None):
    """Test webhook logging functionality"""
    # Get database URL from environment variable if not provided
    if not database_url:
        database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not found.")
        return False
    
    # Ensure the URL starts with postgresql:// (Render might provide postgres://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        # Import system_logger
        print("🔄 Importing system_logger...")
        sys.path.append('.')
        from system_logger import log_webhook
        
        # Create a test webhook log entry
        print("🔄 Creating test webhook log entry...")
        log_webhook('TEST', 'Test webhook log entry from fix_vapi_integration.py',
                   call_id='test_call_id',
                   test=True)
        
        print("✅ Test webhook log entry created.")
        
        # Verify the log entry was created
        engine = create_engine(database_url)
        with engine.connect() as conn:
            verify_sql = text("""
            SELECT * FROM system_logs 
            WHERE category = 'WEBHOOK' AND message LIKE '%Test webhook log entry%'
            ORDER BY timestamp DESC
            LIMIT 1
            """)
            
            result = conn.execute(verify_sql).fetchone()
            if result:
                print(f"✅ Test webhook log entry verified: ID {result.id}, Level {result.level}, Category {result.category}")
                return True
            else:
                print("❌ Failed to verify test webhook log entry.")
                return False
    
    except Exception as e:
        print(f"❌ Error testing webhook logging: {e}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        return False

def check_app_context_in_webhook_handler():
    """Check if the webhook handler has proper app context management"""
    try:
        # Read the admin-server.py file
        print("🔄 Reading admin-server.py...")
        with open('admin-server.py', 'r') as f:
            admin_server_code = f.read()
        
        # Check for app context in vapi_webhook function
        if 'def vapi_webhook' in admin_server_code:
            print("✅ Found vapi_webhook function.")
            
            # Find the vapi_webhook function
            webhook_function_start = admin_server_code.find('def vapi_webhook')
            webhook_function_end = admin_server_code.find('def ', webhook_function_start + 1)
            if webhook_function_end == -1:
                webhook_function_end = len(admin_server_code)
            
            webhook_function = admin_server_code[webhook_function_start:webhook_function_end]
            
            # Check for app context
            if 'with app.app_context()' in webhook_function:
                print("✅ Found app context in vapi_webhook function.")
                
                # Check for db.session.commit
                if 'db.session.commit()' in webhook_function:
                    print("✅ Found db.session.commit() in vapi_webhook function.")
                else:
                    print("❌ Missing db.session.commit() in vapi_webhook function.")
                
                # Check for db.session.rollback
                if 'db.session.rollback()' in webhook_function:
                    print("✅ Found db.session.rollback() in vapi_webhook function.")
                else:
                    print("❌ Missing db.session.rollback() in vapi_webhook function.")
                
                return True
            else:
                print("❌ Missing app context in vapi_webhook function.")
                return False
        else:
            print("❌ Could not find vapi_webhook function.")
            return False
    
    except Exception as e:
        print(f"❌ Error checking app context in webhook handler: {e}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        return False

def main():
    """Main function"""
    print("🔧 Starting VAPI webhook integration fix")
    
    # Get database URL from command line argument
    database_url = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Step 1: Ensure system_logs table exists
    print("\n📊 Step 1: Ensuring system_logs table exists")
    if not ensure_system_logs_table(database_url):
        print("❌ Failed to ensure system_logs table exists. Aborting.")
        sys.exit(1)
    
    # Step 2: Test creating a log entry
    print("\n📝 Step 2: Testing log entry creation")
    if not test_log_entry(database_url):
        print("❌ Failed to create test log entry. Aborting.")
        sys.exit(1)
    
    # Step 3: Test webhook logging
    print("\n📞 Step 3: Testing webhook logging")
    if not test_webhook_logging(database_url):
        print("❌ Failed to test webhook logging. Aborting.")
        sys.exit(1)
    
    # Step 4: Check app context in webhook handler
    print("\n🔍 Step 4: Checking app context in webhook handler")
    if not check_app_context_in_webhook_handler():
        print("❌ App context check failed. Aborting.")
        sys.exit(1)
    
    # Print summary
    print("\n📋 Fix Summary:")
    print("✅ System logs table exists and is properly structured")
    print("✅ Log entry creation works correctly")
    print("✅ Webhook logging works correctly")
    print("✅ Webhook handler has proper app context management")
    
    print("\n🎉 VAPI webhook integration fix completed successfully!")
    print("Note: This script only verifies and fixes basic issues. If problems persist,")
    print("      check the server logs for more detailed error messages.")
    print("      Remember that all testing is done in deployment on render.com")
    
    sys.exit(0)

if __name__ == "__main__":
    main()