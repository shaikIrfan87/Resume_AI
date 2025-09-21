#!/usr/bin/env python3
"""
Test script to verify Streamlit Resume Matching System setup
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ Pandas imported successfully")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
        return False
    
    try:
        import pdfplumber
        print("✅ PDFplumber imported successfully")
    except ImportError as e:
        print(f"❌ PDFplumber import failed: {e}")
        return False
    
    try:
        from docx import Document
        print("✅ python-docx imported successfully")
    except ImportError as e:
        print(f"❌ python-docx import failed: {e}")
        return False
    
    try:
        import google.generativeai as genai
        print("✅ Google Generative AI imported successfully")
    except ImportError as e:
        print(f"❌ Google Generative AI import failed: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv imported successfully")
    except ImportError as e:
        print(f"❌ python-dotenv import failed: {e}")
        return False
    
    return True

def test_files():
    """Test if required files exist"""
    print("\n📁 Testing file structure...")
    
    required_files = [
        "streamlit_app.py",
        "requirements_streamlit.txt",
        "setup_streamlit.py",
        "README_STREAMLIT.md"
    ]
    
    required_dirs = [
        "services"
    ]
    
    all_good = True
    
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file} found")
        else:
            print(f"❌ {file} missing")
            all_good = False
    
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✅ {directory}/ directory found")
        else:
            print(f"❌ {directory}/ directory missing")
            all_good = False
    
    return all_good

def test_services():
    """Test if service modules can be imported"""
    print("\n🛠️ Testing services...")
    
    # Add services to path
    sys.path.append("services")
    
    try:
        from services.gemini_service import get_gemini_analysis, extract_job_title
        print("✅ Gemini service imported successfully")
    except ImportError as e:
        print(f"❌ Gemini service import failed: {e}")
        return False
    
    try:
        from services.email_service import send_shortlist_email
        print("✅ Email service imported successfully")
    except ImportError as e:
        print(f"❌ Email service import failed: {e}")
        return False
    
    return True

def test_env():
    """Test environment configuration"""
    print("\n🔧 Testing environment...")
    
    if not Path(".env").exists():
        print("⚠️ .env file not found - this is needed for API keys")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_google_api_key_here":
        print("⚠️ GOOGLE_API_KEY not configured in .env file")
        return False
    
    print("✅ Environment configuration looks good")
    return True

def test_database():
    """Test database functionality"""
    print("\n💾 Testing database...")
    
    try:
        import sqlite3
        
        # Test database connection
        conn = sqlite3.connect(':memory:')  # Use in-memory database for testing
        cursor = conn.cursor()
        
        # Test table creation
        cursor.execute('''
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        
        cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("test",))
        cursor.execute("SELECT * FROM test_table")
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            print("✅ Database functionality works")
            return True
        else:
            print("❌ Database test failed")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🎯 Resume Matching System - Setup Verification")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Files", test_files), 
        ("Services", test_services),
        ("Environment", test_env),
        ("Database", test_database)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("🎯 Test Summary:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("🎉 All tests passed! Your setup is ready.")
        print("\n🚀 To start the application, run:")
        print("   streamlit run streamlit_app.py")
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        print("\n💡 Common fixes:")
        print("   - Run: pip install -r requirements_streamlit.txt")
        print("   - Configure your .env file with valid API keys")
        print("   - Ensure all files are in the correct location")
    
    return all_passed

if __name__ == "__main__":
    main()