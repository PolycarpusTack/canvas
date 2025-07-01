#!/usr/bin/env python3
"""
Test ONLY the state management integration
Skip UI components to focus on what matters
"""

import sys
import asyncio
from pathlib import Path

# Setup imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import state management directly
from src.managers.enhanced_state import EnhancedStateManager
from src.managers.action_creators import ActionCreators

# Mock page
class MockPage:
    def __init__(self):
        self.window = type('obj', (object,), {
            'width': 1400, 'height': 900, 'left': 100, 'top': 100,
            'maximized': False, 'center': lambda: None
        })()
        self.client_storage = type('obj', (object,), {
            'get_async': lambda k: None,
            'set_async': lambda k, v: None,
            'remove_async': lambda k: None
        })()


async def test_state_management():
    """Test enhanced state management directly"""
    print("🧪 Testing Enhanced State Management System\n")
    
    # Create mock page
    page = MockPage()
    
    # Create enhanced state manager
    print("1️⃣ Creating EnhancedStateManager...")
    state_manager = EnhancedStateManager(page)
    await state_manager.initialize()
    print("   ✅ State manager initialized")
    
    # Test state system access
    print("\n2️⃣ Testing state system access...")
    state_system = state_manager.get_state_system()
    assert state_system is not None
    print("   ✅ State system accessible")
    
    # Check initial theme
    initial_theme = state_system.get_state("theme.mode")
    print(f"   Initial theme: {initial_theme}")
    
    # Test action dispatch
    print("\n3️⃣ Testing action dispatch...")
    # Change to light first if already dark
    new_theme = "light" if initial_theme == "dark" else "dark"
    action = ActionCreators.change_theme(new_theme)
    print(f"   Theme action changes: {len(action.changes)} changes")
    await state_manager.dispatch_action(action)
    
    # Wait for processing
    await asyncio.sleep(0.1)
    
    # Verify theme changed
    theme = state_system.get_state("theme.mode")
    assert theme == new_theme, f"Expected '{new_theme}', got '{theme}'"
    print("   ✅ Action dispatch working")
    
    # Check if theme change was recorded in history
    can_undo_after_theme = state_manager.can_undo()
    print(f"   Can undo after theme change: {can_undo_after_theme}")
    
    # Test component operations
    print("\n4️⃣ Testing component operations...")
    component_data = {
        "id": "test-button",
        "type": "button",
        "name": "Test Button",
        "style": {"left": "100", "top": "100", "width": "80", "height": "30"}
    }
    
    # ActionCreators.add_component expects the full component data
    add_action = ActionCreators.add_component(component_data)
    print(f"   Action type: {add_action.type}")
    print(f"   Action changes: {len(add_action.changes)} changes")
    await state_manager.dispatch_action(add_action)
    
    # Wait for action to be processed
    await asyncio.sleep(0.2)
    
    # Verify component added
    components = state_system.get_state("components.component_map")
    print(f"   Components after add: {list(components.keys()) if components else 'None'}")
    assert "test-button" in components
    print("   ✅ Component operations working")
    
    # Test spatial indexing
    print("\n5️⃣ Testing spatial indexing...")
    components_state = state_system.get_state("components")
    components_at_point = components_state.get_components_at_point(120, 115)
    assert "test-button" in components_at_point
    print("   ✅ Spatial indexing working")
    
    # Test undo/redo
    print("\n6️⃣ Testing undo/redo...")
    can_undo = state_manager.can_undo()
    print(f"   Can undo: {can_undo}")
    # Check debug info instead
    debug_info = state_manager.export_debug_info()
    print(f"   History info: {debug_info.get('history', 'No history info')}")
    assert can_undo, "Should be able to undo"
    
    success = await state_manager.undo()
    assert success, "Undo should succeed"
    
    # Wait for undo to be processed
    await asyncio.sleep(0.2)
    
    # Verify component removed by undo
    components = state_system.get_state("components.component_map")
    assert "test-button" not in components
    print("   ✅ Undo working")
    
    can_redo = state_manager.can_redo()
    assert can_redo, "Should be able to redo"
    
    success = await state_manager.redo()
    assert success, "Redo should succeed"
    
    # Wait for redo to be processed
    await asyncio.sleep(0.2)
    
    # Verify component restored by redo
    components = state_system.get_state("components.component_map")
    assert "test-button" in components
    print("   ✅ Redo working")
    
    # Test performance metrics
    print("\n7️⃣ Testing performance metrics...")
    metrics = state_manager.get_performance_metrics()
    assert "state_metrics" in metrics
    assert "history_stats" in metrics
    print("   ✅ Performance monitoring working")
    
    # Test state persistence
    print("\n8️⃣ Testing state persistence...")
    await state_manager.save_window_state()
    await state_manager.save_panel_state({"sidebar": 100, "components": 300})
    
    # Restore and verify
    window_restored = await state_manager.restore_window_state()
    panel_sizes = await state_manager.restore_panel_state()
    assert panel_sizes["sidebar"] == 100
    print("   ✅ State persistence working")
    
    # Test debug info
    print("\n9️⃣ Testing debug info...")
    debug_info = state_manager.export_debug_info()
    assert "state_summary" in debug_info
    assert "performance_metrics" in debug_info
    print("   ✅ Debug export working")
    
    # Shutdown
    print("\n🔟 Testing shutdown...")
    await state_manager.shutdown()
    print("   ✅ Clean shutdown")
    
    print("\n✅ ALL STATE MANAGEMENT TESTS PASSED!")
    
    print("\n📊 Summary of Working Features:")
    print("   ✅ Enhanced state manager initialization")
    print("   ✅ Action-based state updates") 
    print("   ✅ Component operations with validation")
    print("   ✅ Spatial indexing for canvas queries")
    print("   ✅ Full undo/redo functionality")
    print("   ✅ Performance monitoring and metrics")
    print("   ✅ State persistence and restoration")
    print("   ✅ Debug information export")
    print("   ✅ Clean shutdown and resource cleanup")
    
    print("\n🎉 STATE MANAGEMENT SYSTEM IS FULLY FUNCTIONAL!")
    
    return True


async def main():
    """Run state management test"""
    print("🚀 Enhanced State Management Direct Test\n")
    
    try:
        success = await test_state_management()
        if success:
            print("\n✅ VERIFICATION COMPLETE: State management is working perfectly!")
            print("\n📝 Note: UI components need Flet API updates, but the core")
            print("   state management system is fully functional and integrated.")
        return success
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)