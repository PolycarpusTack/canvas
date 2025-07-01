#!/usr/bin/env python3
"""
Runtime and Type Validation for Canvas Editor State Management
Tests actual runtime behavior and type consistency
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_runtime_imports():
    """Test that all modules can be imported at runtime"""
    print("🧪 Testing Runtime Imports...")
    
    imports_tested = []
    import_errors = []
    
    # Test each manager module
    managers = [
        "action_creators", "enhanced_state", "history_manager",
        "history_middleware", "spatial_index", "state_integration",
        "state_manager", "state_middleware", "state_migration",
        "state_synchronizer", "state_types"
    ]
    
    for module_name in managers:
        try:
            module = __import__(f"src.managers.{module_name}", fromlist=[module_name])
            imports_tested.append((module_name, "✅"))
        except Exception as e:
            imports_tested.append((module_name, "❌"))
            import_errors.append((module_name, str(e)))
    
    # Display results
    for name, status in imports_tested:
        print(f"  {status} {name}")
    
    return len(import_errors) == 0, import_errors

async def test_basic_functionality():
    """Test basic state management functionality"""
    print("\n🧪 Testing Basic State Management Functionality...")
    
    try:
        from src.managers.state_types import ActionType, Action, Change, ChangeType
        from src.managers.action_creators import ActionCreators
        from src.managers.state_manager import StateManager
        from src.managers.history_manager import HistoryManager
        
        # Test 1: Action creation
        print("  1️⃣ Testing action creation...")
        actions = ActionCreators()
        test_action = actions.add_component({
            "id": "test-123",
            "name": "Test Component",
            "type": "button"
        })
        assert test_action.type == ActionType.ADD_COMPONENT
        print("     ✅ Action creation works")
        
        # Test 2: State manager instantiation
        print("  2️⃣ Testing state manager...")
        state_mgr = StateManager()
        assert state_mgr is not None
        print("     ✅ State manager instantiation works")
        
        # Test 3: History manager
        print("  3️⃣ Testing history manager...")
        history_mgr = HistoryManager(max_history=100)
        assert history_mgr.max_history == 100
        print("     ✅ History manager instantiation works")
        
        # Test 4: Action validation
        print("  4️⃣ Testing action validation...")
        validation_result = test_action.validate()
        assert validation_result.is_valid
        print("     ✅ Action validation works")
        
        return True, []
        
    except Exception as e:
        import traceback
        return False, [f"Runtime error: {str(e)}\n{traceback.format_exc()}"]

async def test_async_operations():
    """Test async operations work correctly"""
    print("\n🧪 Testing Async Operations...")
    
    try:
        from src.managers.state_integration import StateManagementSystem
        
        # Test async initialization
        print("  1️⃣ Testing async state system initialization...")
        system = StateManagementSystem(enable_debug=False)
        await system.initialize()
        print("     ✅ Async initialization successful")
        
        # Test async dispatch
        print("  2️⃣ Testing async action dispatch...")
        from src.managers.action_creators import ActionCreators
        actions = ActionCreators()
        test_action = actions.toggle_grid(True)
        await system.dispatch(test_action)
        print("     ✅ Async dispatch successful")
        
        # Test state retrieval
        print("  3️⃣ Testing state retrieval...")
        canvas_state = system.get_state("canvas")
        assert canvas_state is not None
        print("     ✅ State retrieval successful")
        
        # Clean shutdown
        print("  4️⃣ Testing async shutdown...")
        await system.shutdown()
        print("     ✅ Async shutdown successful")
        
        return True, []
        
    except Exception as e:
        import traceback
        return False, [f"Async error: {str(e)}\n{traceback.format_exc()}"]

def check_type_consistency():
    """Check type hints and consistency"""
    print("\n🧪 Checking Type Consistency...")
    
    issues = []
    
    try:
        from src.managers.state_types import (
            Action, ActionType, AppState, Change, ChangeType,
            ComponentTreeState, SelectionState, CanvasState
        )
        
        # Test dataclass instantiation
        print("  1️⃣ Testing dataclass types...")
        
        # Test Action
        action = Action(
            type=ActionType.ADD_COMPONENT,
            description="Test",
            payload={"test": True}
        )
        assert hasattr(action, 'id')
        assert hasattr(action, 'timestamp')
        print("     ✅ Action dataclass valid")
        
        # Test Change
        change = Change(
            path="test.path",
            type=ChangeType.CREATE,
            old_value=None,
            new_value={"test": True}
        )
        assert change.path == "test.path"
        print("     ✅ Change dataclass valid")
        
        # Test enum values
        print("  2️⃣ Testing enum types...")
        assert ActionType.ADD_COMPONENT.value > 0
        assert ChangeType.CREATE.value > 0
        print("     ✅ Enum types valid")
        
        return True, issues
        
    except Exception as e:
        import traceback
        issues.append(f"Type error: {str(e)}\n{traceback.format_exc()}")
        return False, issues

def check_error_handling():
    """Check error handling patterns"""
    print("\n🧪 Checking Error Handling...")
    
    results = []
    
    try:
        from src.managers.state_types import Change
        
        # Test validation errors
        print("  1️⃣ Testing validation errors...")
        try:
            # Should raise ValueError for empty path
            change = Change(path="", type=1, old_value=None, new_value=None)
            results.append("❌ Empty path validation failed")
        except ValueError:
            results.append("✅ Empty path validation works")
        
        # Test invalid path format
        print("  2️⃣ Testing path format validation...")
        try:
            # Should raise ValueError for invalid characters
            change = Change(path="test..invalid", type=1, old_value=None, new_value=None)
            results.append("❌ Path format validation failed")
        except ValueError:
            results.append("✅ Path format validation works")
        
        return all("✅" in r for r in results), results
        
    except Exception as e:
        results.append(f"Error handling check failed: {str(e)}")
        return False, results

async def main():
    """Run all validation tests"""
    print("🎯 Canvas Editor State Management - Runtime Validation")
    print("=" * 70)
    
    all_passed = True
    all_issues = []
    
    # 1. Runtime imports
    passed, issues = await test_runtime_imports()
    all_passed &= passed
    all_issues.extend(issues)
    
    # 2. Basic functionality
    passed, issues = await test_basic_functionality()
    all_passed &= passed
    all_issues.extend(issues)
    
    # 3. Async operations
    passed, issues = await test_async_operations()
    all_passed &= passed
    all_issues.extend(issues)
    
    # 4. Type consistency
    passed, issues = check_type_consistency()
    all_passed &= passed
    all_issues.extend(issues)
    
    # 5. Error handling
    passed, issues = check_error_handling()
    all_passed &= passed
    all_issues.extend(issues)
    
    # Summary
    print("\n" + "=" * 70)
    print("## Validation Summary")
    
    if all_passed:
        print("✅ ALL RUNTIME VALIDATIONS PASSED!")
        print("\nKey Validations:")
        print("✅ All modules import successfully")
        print("✅ Basic state management operations work")
        print("✅ Async operations function correctly")
        print("✅ Type system is consistent")
        print("✅ Error handling is robust")
    else:
        print("❌ Some validations failed:")
        for issue in all_issues:
            if isinstance(issue, tuple):
                print(f"  - {issue[0]}: {issue[1]}")
            else:
                print(f"  - {issue}")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)