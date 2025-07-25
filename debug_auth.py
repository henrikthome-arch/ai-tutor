#!/usr/bin/env python3
"""
Debug script to verify admin authentication setup
"""

import hashlib
import os

# Test the default admin password hash
default_password = "admin123"
default_hash = hashlib.sha256(default_password.encode()).hexdigest()

print("=== Admin Authentication Debug ===")
print(f"Default password: {default_password}")
print(f"Default password hash: {default_hash}")
print()

# Check for environment variables
print("Environment variables:")
print(f"ADMIN_USERNAME: {os.getenv('ADMIN_USERNAME', 'Not set')}")
print(f"ADMIN_PASSWORD: {os.getenv('ADMIN_PASSWORD', 'Not set')}")  
print(f"ADMIN_PASSWORD_HASH: {os.getenv('ADMIN_PASSWORD_HASH', 'Not set')}")
print()

# Test different potential passwords
test_passwords = ["admin123", "admin", "password", "admin123!"]
print("Testing password hashes:")
for pwd in test_passwords:
    hash_val = hashlib.sha256(pwd.encode()).hexdigest()
    print(f"'{pwd}' -> {hash_val}")