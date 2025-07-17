#!/usr/bin/env python3
"""
Temporary wrapper for Render.com deployment
Redirects to the new start.py script
"""

import subprocess
import sys
import os

def main():
    """Redirect to start.py"""
    print("🔄 Redirecting to start.py...")
    
    # Run start.py in the same directory
    start_script = os.path.join(os.path.dirname(__file__), 'start.py')
    
    if not os.path.exists(start_script):
        print(f"❌ start.py not found at: {start_script}")
        sys.exit(1)
    
    # Execute start.py
    os.execv(sys.executable, [sys.executable, start_script])

if __name__ == '__main__':
    main()