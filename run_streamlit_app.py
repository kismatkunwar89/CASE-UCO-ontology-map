#!/usr/bin/env python3
"""
Simple script to run the Streamlit application.
This script handles the installation and execution of the Streamlit demo app.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_streamlit_installed():
    """Check if Streamlit is installed"""
    try:
        import streamlit
        return True
    except ImportError:
        return False

def install_streamlit():
    """Install Streamlit if not already installed"""
    print("Installing Streamlit...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit>=1.28.0"])
        print("✅ Streamlit installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Streamlit: {e}")
        return False

def run_app():
    """Run the Streamlit application"""
    app_path = Path(__file__).parent / "app.py"
    
    if not app_path.exists():
        print(f"❌ App file not found: {app_path}")
        return False
    
    print("🚀 Starting Streamlit application...")
    print("📱 The app will open in your default web browser")
    print("🔗 If it doesn't open automatically, look for the local URL in the terminal")
    print("⏹️  Press Ctrl+C to stop the application")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        return True
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        return True
    except Exception as e:
        print(f"❌ Failed to run application: {e}")
        return False

def main():
    """Main function"""
    print("🔍 CASE/UCO Ontology Mapping Agent - Streamlit Demo")
    print("=" * 50)
    
    # Check if Streamlit is installed
    if not check_streamlit_installed():
        print("📦 Streamlit not found. Installing...")
        if not install_streamlit():
            print("❌ Installation failed. Please install Streamlit manually:")
            print("   pip install streamlit>=1.28.0")
            return 1
    
    # Check if app.py exists
    app_path = Path(__file__).parent / "app.py"
    if not app_path.exists():
        print(f"❌ Application file not found: {app_path}")
        print("   Please ensure app.py is in the same directory as this script")
        return 1
    
    # Run the application
    if run_app():
        print("✅ Application completed successfully")
        return 0
    else:
        print("❌ Application failed to run")
        return 1

if __name__ == "__main__":
    sys.exit(main())
