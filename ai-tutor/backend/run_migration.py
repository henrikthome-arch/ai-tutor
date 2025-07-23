#!/usr/bin/env python3
"""
Simple script to run curriculum schema migration on production
This script can be run directly on render.com or any production environment
"""

import subprocess
import sys
import os

def run_migration():
    """Run the curriculum schema migration"""
    print("🚀 Starting curriculum schema migration...")
    
    # Check if we're in the right directory
    if not os.path.exists('migrate_curriculum_schema.py'):
        print("❌ migrate_curriculum_schema.py not found in current directory")
        print("Please run this script from ai-tutor/backend/ directory")
        sys.exit(1)
    
    # Run the migration script
    try:
        result = subprocess.run([sys.executable, 'migrate_curriculum_schema.py'], 
                              capture_output=True, text=True, check=True)
        print("✅ Migration output:")
        print(result.stdout)
        if result.stderr:
            print("⚠️ Migration warnings:")
            print(result.stderr)
        print("🎉 Migration completed successfully!")
        
    except subprocess.CalledProcessError as e:
        print("❌ Migration failed!")
        print("Error output:", e.stderr)
        print("Standard output:", e.stdout)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()