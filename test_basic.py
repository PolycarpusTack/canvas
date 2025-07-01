#!/usr/bin/env python3
"""
Basic test script for Canvas Editor
Tests import and basic initialization
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import flet as ft
        print("✓ Flet imported successfully")
        
        from main import CanvasEditor, StateManager, ResizeHandle
        print("✓ Canvas Editor classes imported successfully")
        
        # Test basic initialization
        editor = CanvasEditor()
        print("✓ CanvasEditor initialized successfully")
        
        # Test constants
        from main import SIDEBAR_WIDTH, COMPONENTS_WIDTH, PROPERTIES_WIDTH
        print(f"✓ Panel widths: Sidebar={SIDEBAR_WIDTH}, Components={COMPONENTS_WIDTH}, Properties={PROPERTIES_WIDTH}")
        
        # Test state manager (without page)
        print("✓ All basic components initialized correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during import/initialization: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_panel_dimensions():
    """Test panel dimension constraints"""
    from main import (
        SIDEBAR_MIN_WIDTH, SIDEBAR_MAX_WIDTH,
        COMPONENTS_MIN_WIDTH, COMPONENTS_MAX_WIDTH,
        PROPERTIES_MIN_WIDTH, PROPERTIES_MAX_WIDTH
    )
    
    print("\nPanel Constraints:")
    print(f"Sidebar: {SIDEBAR_MIN_WIDTH}px - {SIDEBAR_MAX_WIDTH}px")
    print(f"Components: {COMPONENTS_MIN_WIDTH}px - {COMPONENTS_MAX_WIDTH}px") 
    print(f"Properties: {PROPERTIES_MIN_WIDTH}px - {PROPERTIES_MAX_WIDTH}px")
    
    # Test constraint logic
    if SIDEBAR_MIN_WIDTH < SIDEBAR_MAX_WIDTH:
        print("✓ Sidebar constraints valid")
    else:
        print("✗ Sidebar constraints invalid")
        return False
    
    if COMPONENTS_MIN_WIDTH < COMPONENTS_MAX_WIDTH:
        print("✓ Components constraints valid")
    else:
        print("✗ Components constraints invalid")
        return False
        
    if PROPERTIES_MIN_WIDTH < PROPERTIES_MAX_WIDTH:
        print("✓ Properties constraints valid")
    else:
        print("✗ Properties constraints invalid")
        return False
    
    return True

def test_keyboard_shortcuts():
    """Test keyboard shortcut definitions"""
    from main import CanvasEditor
    
    editor = CanvasEditor()
    shortcuts = editor.shortcuts
    
    print(f"\nKeyboard Shortcuts ({len(shortcuts)} defined):")
    for key, func in shortcuts.items():
        print(f"  {key}: {func.__name__}")
    
    # Test required shortcuts
    required_shortcuts = ['ctrl+s', 'ctrl+z', 'ctrl+y', 'f11', 'escape']
    missing = []
    
    for shortcut in required_shortcuts:
        if shortcut not in shortcuts:
            missing.append(shortcut)
    
    if missing:
        print(f"✗ Missing required shortcuts: {missing}")
        return False
    else:
        print("✓ All required shortcuts defined")
        return True

if __name__ == "__main__":
    print("Canvas Editor Basic Tests")
    print("=" * 30)
    
    tests_passed = 0
    total_tests = 3
    
    # Run tests
    if test_imports():
        tests_passed += 1
    
    if test_panel_dimensions():
        tests_passed += 1
    
    if test_keyboard_shortcuts():
        tests_passed += 1
    
    print(f"\nTest Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("✓ All tests passed! Canvas Editor is ready to run.")
        exit(0)
    else:
        print("✗ Some tests failed. Check the output above.")
        exit(1)