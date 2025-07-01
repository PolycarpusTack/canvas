#!/usr/bin/env python3
"""
Debug Canvas Editor launch with detailed logging
"""

import sys
import os
from pathlib import Path
import traceback

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def debug_main():
    print("🔍 Canvas Editor Debug Launch")
    print("=" * 50)
    
    try:
        print("1. Testing Flet import...")
        import flet as ft
        print(f"   ✓ Flet version: {ft.__version__}")
        
        print("2. Testing main module import...")
        from main import CanvasEditor, ProjectManager, StateManager
        print("   ✓ All classes imported")
        
        print("3. Testing CanvasEditor instantiation...")
        editor = CanvasEditor()
        print("   ✓ CanvasEditor created")
        
        print("4. Testing main method...")
        # Test if main method exists and is callable
        if hasattr(editor, 'main') and callable(editor.main):
            print("   ✓ main method exists and is callable")
        else:
            print("   ❌ main method issue")
            return False
            
        print("5. Testing basic UI components...")
        # Try to create a simple test page
        test_page = ft.Page()
        test_page.title = "Test"
        test_page.add(ft.Text("Test"))
        print("   ✓ Basic Flet components work")
        
        print("\n6. Starting Canvas Editor with debug output...")
        
        # Launch with more verbose output
        ft.app(
            target=editor.main,
            view=ft.AppView.WEB_BROWSER,
            port=8551,  # Different port for debug
            assets_dir=None
        )
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error at step: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_main()
    if not success:
        sys.exit(1)