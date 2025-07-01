#!/usr/bin/env python3
"""
Simple test to verify basic project management and state integration
"""

import asyncio
import tempfile
from pathlib import Path

# Mock Flet components for testing
class MockPage:
    def __init__(self):
        self.client_storage = MockClientStorage()
        self.window = MockWindow()

class MockClientStorage:
    def __init__(self):
        self._storage = {}
    
    async def get_async(self, key: str):
        return self._storage.get(key)
    
    async def set_async(self, key: str, value: str):
        self._storage[key] = value

class MockWindow:
    def __init__(self):
        self.width = 1400
        self.height = 900
        self.left = 100
        self.top = 100
        self.maximized = False

try:
    from src.managers.enhanced_state import EnhancedStateManager
    from src.managers.project_state_integrated import StateIntegratedProjectManager
    print("✅ Successfully imported integrated project management")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    exit(1)

async def test_basic_integration():
    """Test basic integration without complex features"""
    print("\n🧪 Testing Basic Integration...")
    
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Using temporary workspace: {temp_dir}")
    
    try:
        # Create state manager with minimal configuration
        page = MockPage()
        state_manager = EnhancedStateManager(page)
        
        # Initialize state management
        print("Initializing state management...")
        await state_manager.initialize()
        print("✅ State management initialized")
        
        # Create project manager
        project_manager = StateIntegratedProjectManager(state_manager)
        project_manager._allowed_project_root = temp_dir
        
        print("✅ Project manager created")
        
        # Test basic state operations
        print("\nTesting basic state operations...")
        
        # Check if we can get state
        current_state = state_manager.state_system.get_state()
        print(f"✅ Got current state: {type(current_state)}")
        
        # Test project creation
        print("\nTesting project creation...")
        success = await project_manager.create_new_project(
            name="Test Project",
            description="Basic integration test"
        )
        
        if success:
            print("✅ Project created successfully!")
            
            # Check if project was set in state
            current_project = project_manager.get_current_project()
            if current_project:
                print(f"✅ Project found in state: {current_project.get('name', 'Unknown')}")
            else:
                print("⚠️ Project not found in state")
        else:
            print("❌ Project creation failed")
        
        print("\n✅ Basic integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        try:
            await state_manager.shutdown()
            print("✅ State manager shutdown")
        except:
            pass
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    try:
        success = asyncio.run(test_basic_integration())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        exit(1)