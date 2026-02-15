#!/usr/bin/env python3

# Deployment Fix Script - Ensures consistent behavior across all devices
import os
import sys

def check_deployment_environment():
    """Check and fix deployment environment issues"""
    print("🔍 DEPLOYMENT ENVIRONMENT CHECK 🔍")
    print("=" * 50)
    
    # Check Python version
    print(f"🐍 Python Version: {sys.version}")
    
    # Check Flask environment
    flask_env = os.environ.get('FLASK_ENV', 'development')
    print(f"🌍 Flask Environment: {flask_env}")
    
    # Check secret key
    secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')
    if secret_key == 'your_secret_key_here':
        print("⚠️  WARNING: Using default secret key!")
    else:
        print("✅ Secret key configured")
    
    # Check upload folder
    upload_folder = os.environ.get('UPLOAD_FOLDER', '/tmp')
    print(f"📁 Upload Folder: {upload_folder}")
    
    # Check if upload folder exists
    if not os.path.exists(upload_folder):
        print(f"❌ Upload folder does not exist: {upload_folder}")
        try:
            os.makedirs(upload_folder, exist_ok=True)
            print(f"✅ Created upload folder: {upload_folder}")
        except Exception as e:
            print(f"❌ Failed to create upload folder: {e}")
    else:
        print(f"✅ Upload folder exists: {upload_folder}")
    
    # Check database
    db_path = os.path.join(os.getcwd(), 'resumes.db')
    print(f"🗄️  Database Path: {db_path}")
    
    if os.path.exists(db_path):
        print("✅ Database exists")
    else:
        print("❌ Database not found - will be created on startup")
    
    # Check dependencies
    print("\n📦 DEPENDENCY CHECK:")
    dependencies = [
        'flask', 'pdfplumber', 'PyPDF2', 'python-docx', 
        'google-generativeai', 'python-dotenv'
    ]
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - NOT INSTALLED")
    
    print("\n🔧 RECOMMENDED FIXES:")
    print("1. Set environment variables on deployment server:")
    print("   export SECRET_KEY='your_unique_secret_key_here'")
    print("   export FLASK_ENV='production'")
    print("   export UPLOAD_FOLDER='/app/uploads'")
    print("\n2. Ensure all dependencies are installed:")
    print("   pip install -r requirements.txt")
    print("\n3. Check file permissions on deployment server")
    print("   chmod 755 /app/uploads")
    print("\n4. Use absolute paths for database and uploads")

if __name__ == "__main__":
    check_deployment_environment()
