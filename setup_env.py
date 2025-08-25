#!/usr/bin/env python3
"""
Environment Setup Script for AI Tour System
This script helps you set up your environment variables for local development.
"""

import os
import secrets
from pathlib import Path

def generate_secret_key():
    """Generate a secure Django secret key"""
    return ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50))

def setup_env_file():
    """Create or update .env file with proper configuration"""
    env_file = Path('.env')
    template_file = Path('env_template.txt')
    
    if not template_file.exists():
        print("❌ env_template.txt not found!")
        return False
    
    # Read template
    with open(template_file, 'r') as f:
        template_content = f.read()
    
    # Generate secret key if not already set
    if 'your-django-secret-key-here' in template_content:
        secret_key = generate_secret_key()
        template_content = template_content.replace('your-django-secret-key-here', secret_key)
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write(template_content)
    
    print("✅ .env file created successfully!")
    print("📝 Please edit .env file and add your GEMINI_API_KEY")
    return True

def check_env_variables():
    """Check if required environment variables are set"""
    required_vars = ['SECRET_KEY', 'DEBUG', 'ALLOWED_HOSTS']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set!")
        return True

if __name__ == "__main__":
    print("🚀 AI Tour System Environment Setup")
    print("=" * 40)
    
    # Setup .env file
    if setup_env_file():
        print("\n📋 Next steps:")
        print("1. Edit .env file and add your GEMINI_API_KEY")
        print("2. Run: python manage.py migrate")
        print("3. Run: python manage.py runserver")
    
    print("\n🔧 Environment Variables Guide:")
    print("- ALLOWED_HOSTS: Comma-separated list of allowed hosts")
    print("  Local: localhost,127.0.0.1,0.0.0.0")
    print("  Production: your-app-name.onrender.com,.render.com")
    print("- DEBUG: True for development, False for production")
    print("- SECRET_KEY: Auto-generated secure key")
