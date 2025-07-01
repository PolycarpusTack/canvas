#!/usr/bin/env python3
"""
Simple test launcher for Canvas Editor
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def main():
    print("🚀 Launching Canvas Editor...")
    print("📁 Working directory:", os.getcwd())
    print("🐍 Python path:", sys.path[0])
    
    try:
        # Import and check version compatibility
        import flet as ft
        print("✓ Flet imported successfully")
        
        # Import main classes
        from main import CanvasEditor, ProjectManager, StateManager
        print("✓ All classes imported successfully")
        
        # Test basic instantiation
        editor = CanvasEditor()
        print("✓ CanvasEditor instantiated")
        
        # Launch the app
        print("\n🎨 Starting Canvas Editor GUI...")
        print("   ↳ Window should open shortly...")
        print("   ↳ Press Ctrl+C to close")
        
        # Launch the app
        print("   ↳ Starting Canvas Editor...")
        ft.app(
            target=editor.main,
            view=ft.AppView.FLET_APP_WEB,
            port=8080,
            assets_dir=None  # No assets needed for basic test
        )
        
    except KeyboardInterrupt:
        print("\n👋 Canvas Editor closed by user")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💡 Check error messages above for troubleshooting")
        sys.exit(1)