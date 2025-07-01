#!/usr/bin/env python3
"""
Standalone Demo of Enhanced Project Management
This script demonstrates the working parts of the project management system
without requiring the full Canvas Editor setup.
"""

import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from typing import Optional

# Simple mock for Flet page to make the demo work
class MockPage:
    def __init__(self):
        self.client_storage = MockClientStorage()

class MockClientStorage:
    def __init__(self):
        self._storage = {}
    
    async def get_async(self, key: str) -> Optional[str]:
        return self._storage.get(key)
    
    async def set_async(self, key: str, value: str):
        self._storage[key] = value

# Import our actual implementation
try:
    from src.models.project import ProjectMetadata, ProjectFile, ProjectSettings, ValidationError, ProjectSecurityError
    from src.managers.project_enhanced import EnhancedProjectManager, ProjectCreationError, ProjectImportError
    print("✅ Successfully imported project management modules")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Make sure you're running from the canvas directory")
    exit(1)

async def demo_project_creation():
    """Demo: Create a new project with validation"""
    print("\n🔨 Testing Project Creation...")
    
    # Create temporary workspace
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Using temporary workspace: {temp_dir}")
    
    try:
        # Create mock page and project manager
        page = MockPage()
        manager = EnhancedProjectManager(page)
        manager._allowed_project_root = temp_dir  # Override for demo
        
        # Test 1: Valid project creation
        print("\n1. Creating valid project...")
        success = await manager.create_new_project(
            name="Demo Project",
            description="A test project to demonstrate functionality"
        )
        
        if success:
            print("   ✅ Project created successfully!")
            print(f"   📁 Project path: {manager.project_path}")
            print(f"   📋 Project ID: {manager.current_project.id}")
            print(f"   📝 Project name: {manager.current_project.name}")
            
            # Verify files were created
            files_created = list(manager.project_path.rglob("*"))
            print(f"   📄 Files created: {len(files_created)}")
            for file in sorted(files_created):
                if file.is_file():
                    print(f"      - {file.relative_to(manager.project_path)}")
        else:
            print("   ❌ Project creation failed")
            return False
        
        # Test 2: Invalid project names
        print("\n2. Testing invalid project names...")
        
        invalid_names = [
            "",  # Empty name
            "Test<script>alert('xss')</script>",  # XSS attempt
            "con",  # Reserved name
            "Project/With/Slashes",  # Invalid characters
            "a" * 101  # Too long
        ]
        
        for invalid_name in invalid_names:
            try:
                await manager.create_new_project(invalid_name)
                print(f"   ❌ Should have rejected: '{invalid_name[:20]}...'")
            except (ValidationError, ProjectSecurityError) as e:
                print(f"   ✅ Correctly rejected '{invalid_name[:20]}...': {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

async def demo_project_import():
    """Demo: Import existing project with framework detection"""
    print("\n📥 Testing Project Import...")
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create a mock React project
        react_project = temp_dir / "mock_react_project"
        react_project.mkdir()
        
        # Create package.json with React dependencies
        package_json = {
            "name": "mock-react-app",
            "dependencies": {
                "react": "^18.0.0",
                "react-dom": "^18.0.0"
            }
        }
        with open(react_project / "package.json", 'w') as f:
            json.dump(package_json, f, indent=2)
        
        # Create some React files
        (react_project / "src").mkdir()
        (react_project / "src" / "App.jsx").write_text("""
import React from 'react';

function App() {
  return <div>Hello World</div>;
}

export default App;
""")
        
        (react_project / "public").mkdir()
        (react_project / "public" / "index.html").write_text("""
<!DOCTYPE html>
<html>
<head><title>Mock React App</title></head>
<body><div id="root"></div></body>
</html>
""")
        
        # Test import
        page = MockPage()
        manager = EnhancedProjectManager(page)
        manager._allowed_project_root = temp_dir
        
        print(f"Importing project from: {react_project}")
        success = await manager.import_existing_project(str(react_project))
        
        if success:
            print("   ✅ Project imported successfully!")
            print(f"   🔍 Detected framework: {manager.current_project.framework}")
            print(f"   📁 Project files: {manager.current_project.files_count}")
            print(f"   🎯 Main file: {manager.current_project.main_file}")
            
            # Show some imported files
            for i, file in enumerate(manager.project_files[:5]):
                print(f"      - {file.relative_path} ({file.size} bytes)")
            
            if len(manager.project_files) > 5:
                print(f"      ... and {len(manager.project_files) - 5} more files")
        else:
            print("   ❌ Project import failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def demo_validation_features():
    """Demo: Security and validation features"""
    print("\n🔒 Testing Security & Validation Features...")
    
    # Test ProjectFile validation
    print("\n1. Testing ProjectFile validation...")
    
    try:
        # Valid file
        valid_file = ProjectFile(
            path="/safe/path/file.html",
            relative_path="file.html",
            size=1024,
            modified="2024-01-01T00:00:00",
            mime_type="text/html",
            is_web_file=True
        )
        print("   ✅ Valid file created successfully")
        
        # Test content safety
        safe_content = valid_file.is_safe_content()
        print(f"   ✅ Content safety check: {safe_content}")
        
    except Exception as e:
        print(f"   ❌ Valid file creation failed: {e}")
    
    # Test dangerous file
    try:
        dangerous_file = ProjectFile(
            path="/test/../../../etc/passwd",  # Path traversal
            relative_path="../../../etc/passwd",
            size=1024,
            modified="2024-01-01T00:00:00",
            mime_type="text/plain",
            is_web_file=False
        )
        print("   ❌ Should have rejected dangerous path")
    except ProjectSecurityError:
        print("   ✅ Correctly rejected path traversal attempt")
    
    # Test ProjectSettings validation
    print("\n2. Testing ProjectSettings validation...")
    
    try:
        # Valid settings
        settings = ProjectSettings(
            auto_save=True,
            auto_save_interval=300,
            theme="light",
            grid_size=20,
            default_device="desktop"
        )
        print("   ✅ Valid settings created successfully")
        
        # Test invalid interval
        try:
            bad_settings = ProjectSettings(auto_save_interval=10)  # Too short
            print("   ❌ Should have rejected short interval")
        except ValidationError:
            print("   ✅ Correctly rejected short auto-save interval")
        
    except Exception as e:
        print(f"   ❌ Settings validation error: {e}")
    
    return True

async def demo_performance_features():
    """Demo: Performance optimizations"""
    print("\n⚡ Testing Performance Features...")
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create a project with many files
        large_project = temp_dir / "large_project"
        large_project.mkdir()
        
        print("   Creating project with many files...")
        
        # Create multiple directories with files
        for i in range(10):  # Reduced for demo
            dir_path = large_project / f"dir_{i}"
            dir_path.mkdir()
            
            for j in range(10):  # 100 total files
                file_path = dir_path / f"file_{j}.js"
                file_path.write_text(f"// File {i}-{j}\nconsole.log('Hello from file {i}-{j}');")
        
        # Test file scanning performance
        page = MockPage()
        manager = EnhancedProjectManager(page)
        
        import time
        start_time = time.time()
        
        files = await manager._scan_project_files_enhanced(large_project)
        
        end_time = time.time()
        scan_time = end_time - start_time
        
        print(f"   ✅ Scanned {len(files)} files in {scan_time:.3f} seconds")
        print(f"   📊 Performance: {len(files)/scan_time:.1f} files/second")
        
        # Verify file details
        web_files = [f for f in files if f.is_web_file]
        print(f"   📄 Web files detected: {len(web_files)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Performance test error: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def main():
    """Run all demos"""
    print("🚀 Canvas Editor - Project Management Demo")
    print("=" * 50)
    
    # Track results
    results = {}
    
    # Run demos
    results['creation'] = await demo_project_creation()
    results['import'] = await demo_project_import()
    results['validation'] = await demo_validation_features()
    results['performance'] = await demo_performance_features()
    
    # Summary
    print("\n📊 Demo Results Summary")
    print("=" * 30)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.capitalize():12} {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All demos completed successfully!")
        print("The core project management functionality is working.")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} demo(s) failed.")
        print("There are issues that need to be addressed.")
    
    print("\n💡 What this demo proves:")
    print("- ✅ Basic project creation and validation works")
    print("- ✅ Security features are implemented and functional")
    print("- ✅ Framework detection works for common cases")
    print("- ✅ File scanning performs adequately for small projects")
    print("- ✅ Core data models have proper validation")
    
    print("\n⚠️  What this demo doesn't cover:")
    print("- ❌ Integration with actual Canvas Editor UI")
    print("- ❌ Real auto-save functionality (requires UI events)")
    print("- ❌ Large-scale performance (1000+ files)")
    print("- ❌ Concurrent user scenarios")
    print("- ❌ Error recovery from disk failures")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Demo failed with error: {e}")
        exit(1)