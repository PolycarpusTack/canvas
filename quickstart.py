#!/usr/bin/env python3
"""
Canvas Editor - Quick Start Script
Checks dependencies and launches the editor
"""

import sys
import subprocess
import os

def check_python_version():
    """Ensure Python 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        print(f"   You have: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required = ['flet', 'beautifulsoup4', 'cssutils', 'watchdog', 'PIL']
    missing = []
    
    for package in required:
        try:
            if package == 'PIL':
                __import__('PIL')
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    return missing

def install_dependencies():
    """Install missing packages"""
    print("\n📦 Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Dependencies installed!")

def main():
    print("🎨 Canvas Editor - Quick Start\n")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    print("\n📋 Checking dependencies:")
    missing = check_dependencies()
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        response = input("\nInstall missing packages? (y/n): ")
        if response.lower() == 'y':
            install_dependencies()
        else:
            print("❌ Cannot run without dependencies")
            sys.exit(1)
    
    # Launch the editor
    print("\n🚀 Launching Canvas Editor...")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([sys.executable, "src/main.py"])

if __name__ == "__main__":
    main()