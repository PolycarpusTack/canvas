#!/usr/bin/env python3
"""
Critical functionality test - what actually works vs what's fake
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_project_manager_functionality():
    """Test if ProjectManager actually works"""
    print("🔍 Testing ProjectManager functionality...")
    
    try:
        from main import ProjectManager, ProjectMetadata, ProjectFile
        
        # Check if classes are properly defined
        print("✓ ProjectManager class imported successfully")
        print("✓ ProjectMetadata dataclass imported successfully") 
        print("✓ ProjectFile dataclass imported successfully")
        
        # Test if methods exist and are callable
        methods_to_test = [
            'create_new_project',
            'import_folder', 
            'save_project',
            'load_project',
            '_validate_project_file',
            'get_recent_projects',
            'add_to_recent_projects'
        ]
        
        missing_methods = []
        for method in methods_to_test:
            if hasattr(ProjectManager, method):
                print(f"✓ {method} method exists")
            else:
                print(f"✗ {method} method missing")
                missing_methods.append(method)
        
        return len(missing_methods) == 0
        
    except Exception as e:
        print(f"✗ ProjectManager test failed: {e}")
        return False

def test_canvas_editor_core_methods():
    """Test if core editor methods actually work or are stubs"""
    print("\n🔍 Testing CanvasEditor core functionality...")
    
    try:
        from main import CanvasEditor
        import inspect
        
        editor = CanvasEditor()
        issues = []
        
        # Check save_project implementation
        save_code = inspect.getsource(editor.save_project)
        if 'self.project_manager' in save_code:
            print("✓ save_project uses ProjectManager - REAL implementation")
        else:
            print("✗ save_project is stub - just shows messages")
            issues.append("save_project")
        
        # Check if component filtering works
        if hasattr(editor, 'filter_components'):
            filter_code = inspect.getsource(editor.filter_components)
            if 'full implementation' in filter_code:
                print("✗ filter_components is stub - contains 'full implementation' comment")
                issues.append("filter_components")
            else:
                print("✓ filter_components appears to be implemented")
        
        # Check drag and drop
        if hasattr(editor, 'on_component_drop'):
            drop_code = inspect.getsource(editor.on_component_drop)
            if 'show_snack_bar' in drop_code and 'Dropped:' in drop_code:
                print("✗ on_component_drop is stub - only shows snack bar")
                issues.append("on_component_drop")
            else:
                print("✓ on_component_drop has real implementation")
        
        # Check property updates
        if hasattr(editor, 'update_property'):
            prop_code = inspect.getsource(editor.update_property)
            if 'full implementation' in prop_code:
                print("✗ update_property is stub - contains 'full implementation' comment")
                issues.append("update_property")
            else:
                print("✓ update_property appears to be implemented")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"✗ CanvasEditor test failed: {e}")
        return False

def test_file_structure():
    """Test what files exist and their sizes"""
    print("\n🔍 Testing file structure...")
    
    files_to_check = [
        'src/main.py',
        'requirements.txt',
        'verify_implementation.py',
        'run_canvas_editor.py'
    ]
    
    missing_files = []
    for file in files_to_check:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✓ {file} exists ({size:,} bytes)")
            
            if file == 'src/main.py':
                # Count lines to see if it's substantive
                with open(file, 'r') as f:
                    lines = len(f.readlines())
                print(f"  → {lines:,} lines of code")
        else:
            print(f"✗ {file} missing")
            missing_files.append(file)
    
    return len(missing_files) == 0

def test_imports():
    """Test if all imports work"""
    print("\n🔍 Testing imports...")
    
    try:
        # Test basic imports
        import flet as ft
        print("✓ Flet imported successfully")
        
        import json, asyncio, os, uuid, shutil, mimetypes
        from pathlib import Path
        from datetime import datetime
        from typing import Optional, Dict, Any, Callable, List
        from dataclasses import dataclass, asdict
        print("✓ All standard library imports work")
        
        # Test main module import
        from main import CanvasEditor, ProjectManager, StateManager
        print("✓ Main classes imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Canvas Editor Critical Functionality Test")
    print("=" * 50)
    
    results = []
    
    results.append(test_imports())
    results.append(test_file_structure())
    results.append(test_project_manager_functionality())
    results.append(test_canvas_editor_core_methods())
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n{'='*50}")
    print(f"TEST RESULTS: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All basic tests passed - proceeding to detailed analysis...")
    else:
        print("❌ Some tests failed - implementation has issues")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)