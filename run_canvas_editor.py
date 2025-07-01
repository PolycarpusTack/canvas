#!/usr/bin/env python3
"""
Canvas Editor Launcher
Simple script to launch the Canvas Editor application
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def check_requirements():
    """Check if all required packages are installed"""
    try:
        import flet as ft
        print("✓ Flet is available")
        return True
    except ImportError:
        print("✗ Flet is not installed. Run: pip install -r requirements.txt")
        return False

def main():
    """Launch the Canvas Editor"""
    print("Canvas Editor Launcher")
    print("=" * 30)
    
    # Check requirements
    if not check_requirements():
        return False
    
    # Import and run the application
    try:
        print("🚀 Starting Canvas Editor...")
        from main import main as canvas_main
        canvas_main()
        return True
        
    except KeyboardInterrupt:
        print("\n👋 Canvas Editor closed by user")
        return True
        
    except Exception as e:
        print(f"❌ Error starting Canvas Editor: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💡 Try running 'pip install -r requirements.txt' first")
        sys.exit(1)