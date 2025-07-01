#!/usr/bin/env python3
"""
Simple Canvas Editor launcher - desktop mode
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def main():
    print("🚀 Launching Canvas Editor (Desktop Mode)...")
    
    try:
        import flet as ft
        from main import CanvasEditor
        
        print("✓ All imports successful")
        
        # Create editor instance
        editor = CanvasEditor()
        print("✓ Canvas Editor instantiated")
        
        print("\n🎨 Starting Canvas Editor...")
        print("   ↳ Application window will open")
        print("   ↳ Close window to exit")
        
        # Launch in desktop mode
        ft.app(
            target=editor.main,
            view=ft.AppView.FLET_APP  # Desktop app mode
        )
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)