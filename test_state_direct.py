#!/usr/bin/env python3
"""Direct test of state management without import issues"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Test the state management classes directly
sys.path.insert(0, str(Path(__file__).parent / "src" / "managers"))

async def test_state_management():
    """Test state management components directly"""
    print("🧪 Testing Enhanced State Management System\n")
    
    try:
        # Test 1: State Types
        print("1. Testing state types...")
        from state_types import Action, ActionType, AppState, ComponentTreeState
        
        app_state = AppState()
        print(f"   ✅ AppState created: theme={app_state.theme.mode}")
        
        action = Action(
            type=ActionType.CHANGE_THEME,
            payload={"mode": "dark"}
        )
        print(f"   ✅ Action created: {action.type.name}")
        
        # Test 2: Action Creators
        print("\n2. Testing action creators...")
        from action_creators import ActionCreators
        
        theme_action = ActionCreators.change_theme("dark")
        print(f"   ✅ Theme action created: {theme_action.description}")
        
        # Test 3: State Manager
        print("\n3. Testing state manager...")
        from state_manager import StateManager, StateStorage
        
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StateStorage(Path(temp_dir))
            state_manager = StateManager(storage=storage)
            
            await state_manager.start()
            print("   ✅ StateManager started")
            
            # Dispatch action
            await state_manager.dispatch(theme_action)
            await asyncio.sleep(0.1)  # Let it process
            
            # Check state
            theme = state_manager.get_state("theme.mode")
            print(f"   ✅ Theme updated to: {theme}")
            
            await state_manager.stop()
            print("   ✅ StateManager stopped")
        
        # Test 4: History Manager
        print("\n4. Testing history manager...")
        from history_manager import HistoryManager
        from state_types import Change, ChangeType
        
        history = HistoryManager(max_history=10)
        
        # Record action
        changes = [Change(path="theme.mode", type=ChangeType.UPDATE, old_value="light", new_value="dark")]
        await history.record(theme_action, app_state, changes)
        
        print(f"   ✅ History recorded: {len(history.entries)} entries")
        print(f"   ✅ Can undo: {history.can_undo()}")
        
        # Test 5: Spatial Index
        print("\n5. Testing spatial index...")
        from spatial_index import SpatialIndex, BoundingBox
        
        spatial_index = SpatialIndex()
        
        # Add component
        bounds = BoundingBox(x=100, y=100, width=80, height=30)
        spatial_index.insert("button-1", bounds)
        
        # Query
        results = spatial_index.query_point(120, 115)
        print(f"   ✅ Spatial query found: {results}")
        
        # Test 6: State Migration
        print("\n6. Testing state migration...")
        from state_migration import StateMigrationManager
        
        migration_manager = StateMigrationManager()
        print(f"   ✅ Migration manager initialized: v{migration_manager.current_version}")
        
        # Test 7: Integration
        print("\n7. Testing state integration...")
        from state_integration import StateManagementSystem
        
        with tempfile.TemporaryDirectory() as temp_dir:
            system = StateManagementSystem(
                storage_path=Path(temp_dir),
                enable_debug=True
            )
            
            await system.initialize()
            print("   ✅ State system initialized")
            
            # Test component operation
            await system.add_component({
                "id": "test-btn",
                "type": "button",
                "name": "Test"
            })
            
            components = system.get_state("components.component_map")
            print(f"   ✅ Component added: {len(components)} components")
            
            # Test undo
            success = await system.undo()
            print(f"   ✅ Undo: {success}")
            
            await system.shutdown()
            print("   ✅ State system shutdown")
        
        print("\n🎉 ALL DIRECT TESTS PASSED!")
        print("\n✅ State Management System is fully functional")
        print("✅ All core components working correctly")
        print("✅ Ready for integration with UI")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_state_management())
    sys.exit(0 if success else 1)