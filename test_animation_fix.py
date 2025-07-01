#!/usr/bin/env python3
"""
Test Flet animation API fix
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def test_animation_api():
    """Test that animation API works correctly"""
    print("🔍 Testing Flet animation API...")
    
    try:
        import flet as ft
        
        # Test Animation class
        test_animation = ft.Animation(200, ft.AnimationCurve.EASE_OUT)
        print(f"✅ ft.Animation works: {type(test_animation)}")
        
        # Test AnimationCurve enum
        curve = ft.AnimationCurve.EASE_OUT
        print(f"✅ ft.AnimationCurve.EASE_OUT = {curve}")
        
        # Test main classes import
        from main import CanvasEditor
        print("✅ Canvas Editor imports successfully")
        
        # Test instantiation
        editor = CanvasEditor()
        print("✅ Canvas Editor instantiates without animation errors")
        
        print("\n🎉 Animation API fix verified!")
        return True
        
    except AttributeError as e:
        if "has no attribute 'animation'" in str(e):
            print(f"❌ Still have ft.animation issue: {e}")
        else:
            print(f"❌ Animation API error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_animation_api()
    if not success:
        sys.exit(1)