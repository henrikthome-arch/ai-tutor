#!/usr/bin/env python3
"""
Check if the system_logs table exists and has entries
"""

import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

def check_system_logs(database_url=None):
    """Check if the system_logs table exists and has entries"""
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
            # Check if table exists
            table_exists_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'system_logs'
            );
            """)
            
            table_exists = conn.execute(table_exists_query).scalar()
            
            if not table_exists:
                print("❌ system_logs table does not exist!")
                return False
            
            print("✅ system_logs table exists.")
            
            # Check table structure
            columns_query = text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'system_logs';
            """)
            
            columns = conn.execute(columns_query).fetchall()
            print(f"📋 Table structure: {columns}")
            
            # Count total entries
            count_query = text("SELECT COUNT(*) FROM system_logs;")
            total_count = conn.execute(count_query).scalar()
            print(f"📊 Total entries: {total_count}")
            
            # Get recent entries
            recent_query = text("""
            SELECT id, timestamp, level, category, message 
            FROM system_logs 
            ORDER BY timestamp DESC 
            LIMIT 5;
            """)
            
            recent_entries = conn.execute(recent_query).fetchall()
            print(f"📝 Recent entries: {len(recent_entries)}")
            for entry in recent_entries:
                print(f"  - [{entry.level}] {entry.timestamp} {entry.category}: {entry.message[:50]}...")
            
            # Check for webhook entries
            webhook_query = text("""
            SELECT COUNT(*) FROM system_logs 
            WHERE category = 'WEBHOOK' 
            AND timestamp > :since;
            """)
            
            since = datetime.now() - timedelta(days=1)
            webhook_count = conn.execute(webhook_query, {"since": since}).scalar()
            print(f"📞 Webhook entries in the last 24 hours: {webhook_count}")
            
            return True
    
    except Exception as e:
        print(f"❌ Error checking system_logs table: {e}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        return False

def main():
    """Main function"""
    # Get database URL from command line argument
    database_url = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Check system_logs table
    if check_system_logs(database_url):
        print("✅ System logs check completed successfully.")
        sys.exit(0)
    else:
        print("❌ System logs check failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()