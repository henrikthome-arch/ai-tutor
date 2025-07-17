#!/usr/bin/env python3
"""
AI Tutor Production Start Script
Starts the Flask admin server from the reorganized ai-tutor directory structure
"""

import os
import sys
import subprocess

def main():
    """Start the AI Tutor admin server"""
    # Change to the backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'ai-tutor', 'backend')
    
    if not os.path.exists(backend_dir):
        print(f"❌ Backend directory not found: {backend_dir}")
        sys.exit(1)
    
    admin_server_path = os.path.join(backend_dir, 'admin-server.py')
    
    if not os.path.exists(admin_server_path):
        print(f"❌ Admin server not found: {admin_server_path}")
        sys.exit(1)
    
    print(f"🚀 Starting AI Tutor Admin Server from: {backend_dir}")
    print(f"📝 Running: python admin-server.py")
    
    # Change working directory and run the admin server
    os.chdir(backend_dir)
    os.execv(sys.executable, [sys.executable, 'admin-server.py'])

if __name__ == '__main__':
    main()