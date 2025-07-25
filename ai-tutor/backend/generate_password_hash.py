#!/usr/bin/env python3
"""
Password Hash Generator for AI Tutor Admin Authentication
Usage: python generate_password_hash.py [password]
"""

import sys
import hashlib
import getpass

def generate_hash(password):
    """Generate SHA256 hash of password"""
    return hashlib.sha256(password.encode()).hexdigest()

def main():
    if len(sys.argv) > 1:
        # Password provided as argument
        password = sys.argv[1]
    else:
        # Prompt for password securely
        password = getpass.getpass("Enter admin password: ")
    
    if not password:
        print("Error: Password cannot be empty")
        sys.exit(1)
    
    password_hash = generate_hash(password)
    
    print(f"\nPassword: {password}")
    print(f"SHA256 Hash: {password_hash}")
    print(f"\nAdd this to your Render.com environment variables:")
    print(f"ADMIN_PASSWORD_HASH={password_hash}")
    print(f"\nOr use the plain password (will be auto-hashed):")
    print(f"ADMIN_PASSWORD={password}")

if __name__ == "__main__":
    main()