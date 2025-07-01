#!/usr/bin/env python3
"""
Canvas Editor - Web Browser Launch (no native dependencies)
"""

import sys
import os
from pathlib import Path
import webbrowser
import time

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def main():
    print("🚀 Canvas Editor - Web Launch")
    print("=" * 50)
    
    try:
        import flet as ft
        from main import CanvasEditor
        
        print("✓ Flet imported successfully")
        print("✓ Canvas Editor classes loaded")
        
        # Create editor instance
        editor = CanvasEditor()
        print("✓ Canvas Editor instantiated")
        
        print("\n🌐 Starting web server...")
        print("   ↳ Server will start on http://localhost:8554")
        print("   ↳ Browser will open automatically")
        print("   ↳ Press Ctrl+C to stop server")
        print("=" * 50)
        
        # Launch web server
        ft.app(
            target=editor.main,
            view=ft.AppView.WEB_BROWSER,
            port=8554,
            assets_dir=None
        )
        
        return True
        
    except KeyboardInterrupt:
        print("\n👋 Canvas Editor stopped by user")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nFull traceback:")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💡 Try installing required dependencies or check error messages")
        sys.exit(1)