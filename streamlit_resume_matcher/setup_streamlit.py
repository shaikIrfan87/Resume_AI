#!/usr/bin/env python3
"""
Setup script for Streamlit Resume Matcher
This script initializes the database and checks dependencies.
"""

import os
import sys
import sqlite3
from pathlib import Path

def create_database():
    """Initialize the SQLite database with required tables"""
    db_path = "resume_matcher.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create candidates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                resume_file TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
            )
        ''')
        
        # Create analysis_results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                relevance_score INTEGER NOT NULL,
                fit_verdict TEXT NOT NULL,
                summary TEXT NOT NULL,
                personalized_feedback TEXT NOT NULL,
                missing_skills TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database '{db_path}' created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'streamlit',
        'PyPDF2', 
        'google.generativeai',
        'dotenv',
        'plotly',
        'pandas'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'google.generativeai':
                import google.generativeai
            elif package == 'dotenv':
                import dotenv
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\nTo install missing packages, run:")
        print("   pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages are installed!")
        return True

def check_environment():
    """Check if environment variables are set up"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Please copy .env.example to .env and fill in your API keys.")
        return False
    
    # Load and check environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['GOOGLE_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == 'your_google_api_key_here':
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing or invalid environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease update your .env file with valid API keys.")
        return False
    else:
        print("✅ Environment variables are configured!")
        return True

def create_directories():
    """Create necessary directories"""
    dirs_to_create = ['data', 'uploads']
    
    for directory in dirs_to_create:
        Path(directory).mkdir(exist_ok=True)
    
    print(f"✅ Created directories: {', '.join(dirs_to_create)}")
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Streamlit Resume Matcher...")
    print("=" * 50)
    
    success = True
    
    # Check dependencies
    if not check_dependencies():
        success = False
    
    # Check environment
    if not check_environment():
        success = False
    
    # Create directories
    if not create_directories():
        success = False
    
    # Create database
    if not create_database():
        success = False
    
    print("=" * 50)
    
    if success:
        print("✅ Setup completed successfully!")
        print("\nTo start the application, run:")
        print("   streamlit run app.py")
    else:
        print("❌ Setup completed with errors. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())