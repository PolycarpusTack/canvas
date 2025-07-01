#!/usr/bin/env python3
"""
Verify Flet API fixes are working
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def verify_api_fixes():
    """Test that all Flet API calls work correctly"""
    print("🔍 Verifying Flet API fixes...")
    
    try:
        import flet as ft
        
        # Test Icons API
        test_icon = ft.Icons.DASHBOARD
        print(f"✅ ft.Icons.DASHBOARD = {test_icon}")
        
        # Test Colors API  
        test_color = ft.Colors.BLUE_400
        print(f"✅ ft.Colors.BLUE_400 = {test_color}")
        
        # Test DropdownOption API
        test_option = ft.DropdownOption("Test")
        print(f"✅ ft.DropdownOption works: {type(test_option)}")
        
        # Test main classes import
        from main import CanvasEditor, ProjectManager
        print("✅ Main classes import successfully")
        
        # Test instantiation
        editor = CanvasEditor()
        print("✅ CanvasEditor instantiates without errors")
        
        print("\n🎉 All API fixes verified successfully!")
        print("   Canvas Editor should now run without ft.icons errors")
        return True
        
    except AttributeError as e:
        if "has no attribute 'icons'" in str(e):
            print(f"❌ Still have ft.icons issue: {e}")
        else:
            print(f"❌ API error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_api_fixes()
    if not success:
        sys.exit(1)