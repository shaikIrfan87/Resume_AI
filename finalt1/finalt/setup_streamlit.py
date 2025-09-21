#!/usr/bin/env python3
"""
Setup script for Pure Streamlit Resume Matching System
"""

import os
import sys
import subprocess
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("📦 Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    print("🔧 Checking environment configuration...")
    
    env_path = Path(".env")
    if not env_path.exists():
        print("⚠️ .env file not found. Creating template...")
        create_env_template()
        return False
    
    # Read and check key variables
    with open(env_path, 'r') as f:
        content = f.read()
    
    required_vars = ["GOOGLE_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if f"{var}=" not in content or f"{var}=your_" in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ Missing or incomplete environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with actual values.")
        return False
    
    print("✅ Environment configuration looks good!")
    return True

def create_env_template():
    """Create a template .env file"""
    template = """# Google Gemini AI Configuration
GOOGLE_API_KEY=your_google_api_key_here

# Email Configuration (Optional - for sending shortlist emails)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here
MAIL_DEFAULT_SENDER=your_email@gmail.com
"""
    
    with open(".env", "w") as f:
        f.write(template)
    
    print("📝 Created .env template file. Please update it with your actual API keys.")

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = ["uploads", ".streamlit"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Directories created!")

def cleanup_flask_files():
    """Remove any remaining Flask-specific files"""
    print("🧹 Cleaning up Flask files...")
    
    flask_files = [
        "init_db.py",
        "templates",
        "__pycache__"
    ]
    
    for item in flask_files:
        item_path = Path(item)
        if item_path.exists():
            if item_path.is_file():
                item_path.unlink()
                print(f"Removed file: {item}")
            elif item_path.is_dir():
                import shutil
                shutil.rmtree(item_path)
                print(f"Removed directory: {item}")
    
    print("✅ Cleanup complete!")

def run_streamlit():
    """Run the Streamlit app"""
    print("🚀 Starting Streamlit app...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\\n👋 Streamlit app stopped.")
    except Exception as e:
        print(f"❌ Error running Streamlit: {e}")

def main():
    """Main setup function"""
    print("🎯 Pure Streamlit Resume Matching System - Setup")
    print("=" * 60)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Install requirements
    if not install_requirements():
        print("❌ Setup failed at requirements installation.")
        return
    
    # Create directories
    create_directories()
    
    # Cleanup Flask files
    cleanup_flask_files()
    
    # Check environment
    env_ok = check_env_file()
    
    print("\\n" + "=" * 60)
    print("🎯 Setup Summary:")
    print("✅ Requirements installed")
    print("✅ Directories created")
    print("✅ Flask files cleaned up")
    print("✅ Environment file checked" if env_ok else "⚠️ Environment file needs configuration")
    
    if not env_ok:
        print("\\n📝 Next steps:")
        print("1. Edit the .env file with your Google API key")
        print("2. Run: python setup_streamlit.py")
        return
    
    print("\\n🚀 Ready to launch!")
    print("\\n💡 Available commands:")
    print("- Run app: streamlit run app.py")
    print("- Or use setup: python setup_streamlit.py")
    
    response = input("\\nStart Streamlit app now? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        run_streamlit()
    else:
        print("\\n💡 To start the app later, run:")
        print("streamlit run app.py")

if __name__ == "__main__":
    main()