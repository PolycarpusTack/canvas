#!/usr/bin/env python3
"""
Test script to verify export system imports work correctly
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_models_import():
    """Test model imports"""
    print("Testing model imports...")
    try:
        from src.models import (
            Component, Project, Asset, ProjectPage,
            ExportCompatibleComponent, ExportCompatibleProject
        )
        print("✓ Models imported successfully")
        return True
    except Exception as e:
        print(f"✗ Model import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_export_import():
    """Test export system imports"""
    print("Testing export system imports...")
    try:
        from src.export import (
            ExportPipeline, ExportConfig, ExportFormat,
            ExportOptions, OptimizationSettings
        )
        print("✓ Export system imported successfully")
        return True
    except Exception as e:
        print(f"✗ Export system import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_generators_import():
    """Test generator imports"""
    print("Testing generator imports...")
    try:
        from src.export.generators import (
            HTMLGenerator, ReactGenerator, VueGenerator
        )
        print("✓ Generators imported successfully")
        return True
    except Exception as e:
        print(f"✗ Generator import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_processors_import():
    """Test processor imports"""
    print("Testing processor imports...")
    try:
        from src.export.processors import (
            AssetProcessor, CodeOptimizer
        )
        print("✓ Processors imported successfully")
        
        # Test optional image processor
        try:
            from src.export.processors import ImageProcessor
            print("✓ Image processor available")
        except ImportError:
            print("⚠ Image processor not available (Pillow not installed)")
        
        return True
    except Exception as e:
        print(f"✗ Processor import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality"""
    print("Testing basic functionality...")
    try:
        from src.models import Project, Component
        from src.export import ExportConfig, ExportFormat, ExportPipeline
        from pathlib import Path
        
        # Create a simple project
        component = Component(
            type="text",
            content="Hello World",
            properties={"class": "greeting"}
        )
        
        project = Project(
            name="Test Project",
            components=[component]
        )
        
        # Create export config
        config = ExportConfig(
            format=ExportFormat.HTML,
            output_path=Path("/tmp/test_export")
        )
        
        # Create pipeline
        pipeline = ExportPipeline()
        
        print("✓ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Canvas Export System - Import Tests")
    print("=" * 40)
    
    tests = [
        test_models_import,
        test_export_import,
        test_generators_import,
        test_processors_import,
        test_basic_functionality
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 40)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All import tests passed!")
        return True
    else:
        print("❌ Some import tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)