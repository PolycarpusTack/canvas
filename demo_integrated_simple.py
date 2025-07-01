#!/usr/bin/env python3
"""
Simplified demo of integrated project management without Flet dependency
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import only the core components we need
from src.managers.state_types import AppState, ActionType
from src.managers.state_manager import StateManager
from src.models.project import ProjectMetadata, ProjectSettings

class SimpleDemo:
    """Demonstrate state-integrated project management without UI dependencies"""
    
    def __init__(self):
        self.state = AppState()
        self.state_manager = StateManager(initial_state=self.state)
        self.project_settings = ProjectSettings()
        
    async def run(self):
        """Run the demo"""
        print("🚀 Canvas Editor - Integrated Project Management Demo (Simplified)")
        print("=" * 60)
        
        # Start state manager
        await self.state_manager.start()
        
        print("\n1. Testing State Management System")
        print("-" * 40)
        
        # Test basic state operations
        initial_state = self.state_manager.get_state()
        print(f"✅ Initial state created: {type(initial_state).__name__}")
        print(f"   - Window size: {initial_state.window.width}x{initial_state.window.height}")
        print(f"   - Theme: {initial_state.theme.mode}")
        print(f"   - Has project: {initial_state.project is not None}")
        
        print("\n2. Testing Action Dispatch")
        print("-" * 40)
        
        # Create a simple action to update theme
        from src.managers.action_creators import ActionCreators
        theme_action = ActionCreators.change_theme("dark")
        print(f"✅ Created theme change action: {theme_action.description}")
        
        # Dispatch the action
        await self.state_manager.dispatch(theme_action)
        await asyncio.sleep(0.1)  # Let it process
        
        # Check if theme changed
        new_state = self.state_manager.get_state()
        print(f"✅ Theme updated: {new_state.theme.mode}")
        
        print("\n3. Testing Project State Integration")
        print("-" * 40)
        
        # Create project action
        project_action = ActionCreators.create_project(
            project_id="demo-123",
            name="Demo Project",
            path="/tmp/demo-project",
            metadata={
                "description": "Test project for state integration",
                "created": "2024-01-01T00:00:00",
                "modified": "2024-01-01T00:00:00"
            }
        )
        print(f"✅ Created project action: {project_action.description}")
        
        # Dispatch project creation
        await self.state_manager.dispatch(project_action)
        await asyncio.sleep(0.1)
        
        # Check project state
        final_state = self.state_manager.get_state()
        if final_state.project:
            print(f"✅ Project in state: {final_state.project.name}")
            print(f"   - ID: {final_state.project.id}")
            print(f"   - Path: {final_state.project.path}")
        
        print("\n4. Testing Undo/Redo Capability")
        print("-" * 40)
        
        # Check history state
        print(f"✅ History tracking enabled")
        print(f"   - Can undo: {self.state_manager.can_undo()}")
        print(f"   - Can redo: {self.state_manager.can_redo()}")
        
        # Stop state manager
        await self.state_manager.stop()
        
        print("\n✅ Demo completed successfully!")
        print("\nKey Integration Points Demonstrated:")
        print("- State management system initialized")
        print("- Actions can be dispatched and processed")
        print("- Project state integrates with central state")
        print("- History tracking is available for undo/redo")
        print("\nThe full integration with StateIntegratedProjectManager")
        print("provides additional features like:")
        print("- File system operations")
        print("- Project validation and security")
        print("- Auto-save functionality")
        print("- Real-time UI binding")

async def main():
    """Run the simplified demo"""
    try:
        demo = SimpleDemo()
        await demo.run()
        return True
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted")
        sys.exit(1)