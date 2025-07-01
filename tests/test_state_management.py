"""
Comprehensive tests for the state management system.
Tests all components including StateManager, HistoryManager, middleware, and integrations.
"""

import asyncio
import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

# Import state management components
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from managers.state_types import (
    Action, ActionType, AppState, Change, ChangeType,
    ComponentTreeState, WindowState, CanvasState
)
from managers.state_manager import StateManager, StateStorage
from managers.state_middleware import (
    ValidationMiddleware, LoggingMiddleware, PerformanceMiddleware,
    AutoSaveMiddleware, SecurityMiddleware
)
from managers.history_manager import HistoryManager
from managers.action_creators import ActionCreators
from managers.state_integration import StateManagementSystem, StateContext
from managers.history_middleware import HistoryMiddleware, PerformanceEnforcementMiddleware
from managers.state_migration import StateMigrationManager
from managers.spatial_index import SpatialIndex, BoundingBox


class TestStateTypes:
    """Test state type definitions and validation"""
    
    def test_action_creation(self):
        """Test action creation and validation"""
        action = Action(
            type=ActionType.ADD_COMPONENT,
            description="Test action",
            payload={"component_id": "test-123"}
        )
        
        assert action.type == ActionType.ADD_COMPONENT
        assert action.description == "Test action"
        assert action.payload["component_id"] == "test-123"
        assert action.id is not None
        assert isinstance(action.timestamp, datetime)
    
    def test_action_validation(self):
        """Test action validation"""
        # Valid action
        action = Action(
            type=ActionType.ADD_COMPONENT,
            payload={
                "component_data": {"id": "test-123", "type": "button"},
                "component_id": "test-123"
            }
        )
        validation = action.validate()
        assert validation.is_valid
        
        # Invalid action - missing component_id
        invalid_action = Action(
            type=ActionType.ADD_COMPONENT,
            payload={"component_data": {"type": "button"}}
        )
        validation = invalid_action.validate()
        assert not validation.is_valid
    
    def test_change_creation(self):
        """Test change object creation"""
        change = Change(
            path="components.button1.style.color",
            type=ChangeType.UPDATE,
            old_value="red",
            new_value="blue"
        )
        
        assert change.path == "components.button1.style.color"
        assert change.type == ChangeType.UPDATE
        assert change.old_value == "red"
        assert change.new_value == "blue"
    
    def test_change_validation(self):
        """Test change path validation"""
        # Valid path
        Change(path="components.button1.style", type=ChangeType.UPDATE)
        
        # Invalid paths should raise ValueError
        with pytest.raises(ValueError):
            Change(path="", type=ChangeType.UPDATE)
        
        with pytest.raises(ValueError):
            Change(path="invalid..path", type=ChangeType.UPDATE)
    
    def test_app_state_serialization(self):
        """Test AppState serialization and deserialization"""
        state = AppState()
        state.window.width = 1200
        state.theme.mode = "dark"
        state.canvas.zoom = 1.5
        
        # Serialize
        data = state.to_dict()
        assert data["window"]["width"] == 1200
        assert data["theme"]["mode"] == "dark"
        assert data["canvas"]["zoom"] == 1.5
        
        # Deserialize
        restored_state = AppState.from_dict(data)
        assert restored_state.window.width == 1200
        assert restored_state.theme.mode == "dark"
        assert restored_state.canvas.zoom == 1.5
    
    def test_component_tree_operations(self):
        """Test component tree state operations"""
        tree = ComponentTreeState()
        
        # Add root component
        component_data = {"id": "root", "type": "div", "name": "Root"}
        tree.add_component(component_data)
        
        assert "root" in tree.component_map
        assert "root" in tree.root_components
        assert "root" in tree.dirty_components
        
        # Add child component
        child_data = {"id": "child", "type": "button", "name": "Child"}
        tree.add_component(child_data, parent_id="root")
        
        assert "child" in tree.component_map
        assert tree.parent_map["child"] == "root"
        assert "child" not in tree.root_components
        
        # Remove component
        tree.remove_component("child")
        assert "child" not in tree.component_map
        assert "child" not in tree.parent_map


class TestStateStorage:
    """Test state persistence functionality"""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield StateStorage(Path(temp_dir))
    
    @pytest.mark.asyncio
    async def test_save_and_load_state(self, temp_storage):
        """Test saving and loading state data"""
        test_data = {
            "window": {"width": 1200, "height": 800},
            "theme": {"mode": "dark"},
            "timestamp": "2024-01-01T12:00:00"
        }
        
        # Save state
        success = await temp_storage.save_state("test_state", test_data)
        assert success
        
        # Load state
        loaded_data = await temp_storage.load_state("test_state")
        assert loaded_data == test_data
    
    @pytest.mark.asyncio
    async def test_load_nonexistent_state(self, temp_storage):
        """Test loading non-existent state returns None"""
        result = await temp_storage.load_state("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_atomic_save(self, temp_storage):
        """Test that saves are atomic (no corruption on failure)"""
        # This would be tested with mocked file operations
        # For now, just test basic functionality
        test_data = {"test": "data"}
        success = await temp_storage.save_state("atomic_test", test_data)
        assert success


class TestStateManager:
    """Test core state manager functionality"""
    
    @pytest.fixture
    def state_manager(self):
        """Create state manager for testing"""
        return StateManager()
    
    @pytest.mark.asyncio
    async def test_state_manager_lifecycle(self, state_manager):
        """Test state manager start and stop"""
        await state_manager.start()
        assert state_manager._running
        
        await state_manager.stop()
        assert not state_manager._running
    
    @pytest.mark.asyncio
    async def test_action_dispatch(self, state_manager):
        """Test action dispatching"""
        await state_manager.start()
        
        # Create test action
        action = ActionCreators.change_theme("dark")
        
        # Dispatch action
        await state_manager.dispatch(action)
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Verify state change
        theme_mode = state_manager.get_state("theme.mode")
        assert theme_mode == "dark"
        
        await state_manager.stop()
    
    @pytest.mark.asyncio
    async def test_state_subscription(self, state_manager):
        """Test state change subscriptions"""
        await state_manager.start()
        
        # Track changes
        changes = []
        
        def on_change(old_val, new_val):
            changes.append((old_val, new_val))
        
        # Subscribe to theme changes
        unsubscribe = state_manager.subscribe("theme.mode", on_change)
        
        # Change theme
        action = ActionCreators.change_theme("dark")
        await state_manager.dispatch(action)
        await asyncio.sleep(0.1)
        
        # Verify subscription was called
        assert len(changes) > 0
        
        # Unsubscribe and verify no more changes
        unsubscribe()
        changes.clear()
        
        action = ActionCreators.change_theme("light")
        await state_manager.dispatch(action)
        await asyncio.sleep(0.1)
        
        assert len(changes) == 0
        
        await state_manager.stop()
    
    def test_get_state(self, state_manager):
        """Test getting state at different paths"""
        # Get full state
        full_state = state_manager.get_state()
        assert isinstance(full_state, AppState)
        
        # Get nested state
        theme_mode = state_manager.get_state("theme.mode")
        assert theme_mode == "light"  # default
        
        # Get non-existent path
        result = state_manager.get_state("nonexistent.path")
        assert result is None
    
    def test_path_validation(self, state_manager):
        """Test state path validation for security"""
        # Valid paths should work
        state_manager.get_state("theme.mode")
        state_manager.get_state("components.component_map")
        
        # Invalid paths should raise ValueError
        with pytest.raises(ValueError):
            state_manager.get_state("../etc/passwd")
        
        with pytest.raises(ValueError):
            state_manager.get_state("/absolute/path")


class TestMiddleware:
    """Test middleware functionality"""
    
    @pytest.mark.asyncio
    async def test_validation_middleware(self):
        """Test validation middleware"""
        middleware = ValidationMiddleware()
        state = AppState()
        
        # Valid action should pass
        valid_action = ActionCreators.add_component({
            "id": "test-123",
            "type": "button",
            "name": "Test Button"
        })
        
        result = await middleware.before_action(valid_action, state)
        assert result is not None
        
        # Invalid action should be rejected
        invalid_action = Action(
            type=ActionType.ADD_COMPONENT,
            payload={"component_data": {}}  # Missing ID
        )
        
        result = await middleware.before_action(invalid_action, state)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_logging_middleware(self):
        """Test logging middleware"""
        middleware = LoggingMiddleware()
        state = AppState()
        action = ActionCreators.change_theme("dark")
        
        # Should not raise exceptions
        result = await middleware.before_action(action, state)
        assert result == action
        
        await middleware.after_action(action, state, [])
    
    @pytest.mark.asyncio
    async def test_performance_middleware(self):
        """Test performance monitoring middleware"""
        middleware = PerformanceMiddleware(slow_threshold_ms=1)
        state = AppState()
        action = ActionCreators.change_theme("dark")
        
        # Before action should add timing
        result = await middleware.before_action(action, state)
        assert result == action
        assert "_start_time" in action.metadata
        
        # Simulate slow operation
        await asyncio.sleep(0.002)  # 2ms > 1ms threshold
        
        # After action should log warning for slow action
        with patch('managers.state_middleware.logger') as mock_logger:
            await middleware.after_action(action, state, [])
            mock_logger.warning.assert_called()
    
    @pytest.mark.asyncio
    async def test_security_middleware(self):
        """Test security middleware"""
        middleware = SecurityMiddleware(max_actions_per_second=2)
        state = AppState()
        
        # First few actions should pass
        for i in range(2):
            action = ActionCreators.change_theme(f"theme-{i}")
            result = await middleware.before_action(action, state)
            assert result is not None
        
        # Rapid actions should be rate limited
        action = ActionCreators.change_theme("rate-limited")
        result = await middleware.before_action(action, state)
        assert result is None  # Should be rate limited


class TestHistoryManager:
    """Test undo/redo functionality"""
    
    @pytest.fixture
    def history_manager(self):
        """Create history manager for testing"""
        return HistoryManager(max_history=100, max_memory_mb=10)
    
    def test_history_recording(self, history_manager):
        """Test recording actions in history"""
        state = AppState()
        action = ActionCreators.change_theme("dark")
        changes = [Change(path="theme.mode", type=ChangeType.UPDATE, new_value="dark")]
        
        # Record action
        history_manager.record(action, state, changes)
        
        assert len(history_manager.entries) == 1
        assert history_manager.current_index == 0
        assert history_manager.can_undo()
        assert not history_manager.can_redo()
    
    @pytest.mark.asyncio
    async def test_undo_redo(self, history_manager):
        """Test undo and redo operations"""
        state = AppState()
        
        # Record multiple actions
        for i in range(3):
            action = ActionCreators.change_theme(f"theme-{i}")
            changes = [Change(path="theme.mode", type=ChangeType.UPDATE, new_value=f"theme-{i}")]
            history_manager.record(action, state, changes)
        
        assert history_manager.current_index == 2
        assert len(history_manager.entries) == 3
        
        # Undo operations
        undo_action = await history_manager.undo()
        assert undo_action is not None
        assert undo_action.type == ActionType.UNDO
        assert history_manager.current_index == 1
        
        # Redo operation
        redo_action = await history_manager.redo()
        assert redo_action is not None
        assert redo_action.type == ActionType.REDO
        assert history_manager.current_index == 2
    
    def test_batch_operations(self, history_manager):
        """Test batch operation grouping"""
        # Start batch
        batch_id = history_manager.start_batch("Test Batch")
        assert len(history_manager.batch_stack) == 1
        
        # End batch
        history_manager.end_batch(batch_id)
        assert len(history_manager.batch_stack) == 0
    
    def test_history_timeline(self, history_manager):
        """Test history timeline generation"""
        state = AppState()
        
        # Record some actions
        for i in range(5):
            action = ActionCreators.change_theme(f"theme-{i}")
            changes = [Change(path="theme.mode", type=ChangeType.UPDATE)]
            history_manager.record(action, state, changes)
        
        # Get timeline
        timeline = history_manager.get_history_timeline(start=0, limit=10)
        assert len(timeline) == 5
        
        # Check timeline item structure
        item = timeline[0]
        assert hasattr(item, 'index')
        assert hasattr(item, 'description')
        assert hasattr(item, 'timestamp')
        assert hasattr(item, 'is_current')
    
    def test_memory_management(self, history_manager):
        """Test history memory management"""
        state = AppState()
        
        # Fill up history
        for i in range(150):  # More than max_history
            action = ActionCreators.change_theme(f"theme-{i}")
            changes = [Change(path="theme.mode", type=ChangeType.UPDATE)]
            history_manager.record(action, state, changes)
        
        # Should not exceed max_history
        assert len(history_manager.entries) <= history_manager.max_history


class TestActionCreators:
    """Test action creator functions"""
    
    def test_component_actions(self):
        """Test component-related action creators"""
        component_data = {"id": "test-123", "type": "button", "name": "Test"}
        
        # Add component
        action = ActionCreators.add_component(component_data, parent_id="parent-123")
        assert action.type == ActionType.ADD_COMPONENT
        assert action.payload["component_data"] == component_data
        assert action.payload["parent_id"] == "parent-123"
        
        # Update component
        updates = {"name": "Updated Name"}
        action = ActionCreators.update_component("test-123", updates)
        assert action.type == ActionType.UPDATE_COMPONENT
        assert action.payload["component_id"] == "test-123"
        assert action.payload["updates"] == updates
        
        # Delete component
        action = ActionCreators.delete_component("test-123")
        assert action.type == ActionType.DELETE_COMPONENT
        assert action.payload["component_id"] == "test-123"
    
    def test_selection_actions(self):
        """Test selection-related action creators"""
        # Select component
        action = ActionCreators.select_component("test-123", multi_select=True)
        assert action.type == ActionType.SELECT_COMPONENT
        assert action.payload["component_id"] == "test-123"
        assert action.payload["multi_select"] is True
        
        # Clear selection
        action = ActionCreators.clear_selection()
        assert action.type == ActionType.CLEAR_SELECTION
    
    def test_ui_actions(self):
        """Test UI-related action creators"""
        # Change theme
        action = ActionCreators.change_theme("dark")
        assert action.type == ActionType.CHANGE_THEME
        assert action.payload["mode"] == "dark"
        
        # Resize panel
        action = ActionCreators.resize_panel("sidebar", 120)
        assert action.type == ActionType.RESIZE_PANEL
        assert action.payload["panel"] == "sidebar"
        assert action.payload["width"] == 120
        
        # Zoom canvas
        action = ActionCreators.zoom_canvas(0.1, {"x": 100, "y": 200})
        assert action.type == ActionType.ZOOM_CANVAS
        assert action.payload["delta"] == 0.1
        assert action.payload["center"]["x"] == 100


class TestStateIntegration:
    """Test complete state management system integration"""
    
    @pytest.mark.asyncio
    async def test_system_initialization(self):
        """Test system initialization and shutdown"""
        with tempfile.TemporaryDirectory() as temp_dir:
            system = StateManagementSystem(
                storage_path=Path(temp_dir),
                enable_debug=True
            )
            
            await system.initialize()
            assert system.running
            assert system.debugger is not None
            
            await system.shutdown()
            assert not system.running
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test state system context manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            async with StateContext(storage_path=Path(temp_dir)) as system:
                assert system.running
                
                # Test basic operation
                await system.change_theme("dark")
                theme = system.get_state("theme.mode")
                assert theme == "dark"
            
            # System should be stopped after context exit
            assert not system.running
    
    @pytest.mark.asyncio
    async def test_component_operations(self):
        """Test high-level component operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            async with StateContext(storage_path=Path(temp_dir)) as system:
                # Add component
                component_data = {"id": "test-123", "type": "button", "name": "Test"}
                await system.add_component(component_data)
                
                # Verify component was added
                component = system.get_component("test-123")
                assert component is not None
                assert component["name"] == "Test"
                
                # Update component
                await system.update_component("test-123", {"name": "Updated"})
                
                # Select component
                await system.select_component("test-123")
                selected = system.get_selected_components()
                assert "test-123" in selected
                
                # Test undo
                success = await system.undo()
                assert success
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self):
        """Test performance monitoring"""
        with tempfile.TemporaryDirectory() as temp_dir:
            async with StateContext(storage_path=Path(temp_dir)) as system:
                # Perform some operations
                for i in range(10):
                    await system.change_theme(f"theme-{i}")
                
                # Get metrics
                metrics = system.get_performance_metrics()
                assert "state_metrics" in metrics
                assert "history_stats" in metrics
                assert "synchronizer_info" in metrics
    
    @pytest.mark.asyncio
    async def test_debug_export(self):
        """Test debug information export"""
        with tempfile.TemporaryDirectory() as temp_dir:
            async with StateContext(
                storage_path=Path(temp_dir),
                enable_debug=True
            ) as system:
                # Perform operations
                await system.change_theme("dark")
                await system.add_component({"id": "test", "type": "button"})
                
                # Export debug info
                debug_info = system.export_debug_info()
                assert "state_summary" in debug_info
                assert "performance_metrics" in debug_info
                assert "system_status" in debug_info
                assert "state_snapshot" in debug_info


class TestHistoryMiddleware:
    """Test history middleware integration"""
    
    @pytest.mark.asyncio
    async def test_history_middleware_integration(self):
        """Test history middleware properly records actions"""
        history_manager = HistoryManager(max_history=100)
        middleware = HistoryMiddleware(history_manager)
        state = AppState()
        
        # Create action
        action = ActionCreators.change_theme("dark")
        
        # Process through middleware
        result = await middleware.before_action(action, state)
        assert result == action
        
        # Simulate state change
        new_state = AppState()
        new_state.theme.mode = "dark"
        changes = [Change(path="theme.mode", type=ChangeType.UPDATE, new_value="dark")]
        
        # Process after action
        await middleware.after_action(action, new_state, changes)
        
        # Verify history was recorded
        assert len(history_manager.entries) == 1
        assert history_manager.can_undo()


class TestPerformanceEnforcement:
    """Test performance enforcement middleware"""
    
    @pytest.mark.asyncio
    async def test_performance_enforcement_warnings(self):
        """Test performance warnings for complex actions"""
        middleware = PerformanceEnforcementMiddleware(
            max_update_time_ms=1.0,  # Very low threshold for testing
            strict_mode=False
        )
        
        # Create state with many components
        state = AppState()
        for i in range(1000):
            state.components.component_map[f"comp_{i}"] = {"id": f"comp_{i}", "type": "button"}
        
        action = ActionCreators.add_component({"id": "new_comp", "type": "button"})
        
        # Should generate warning but not reject
        result = await middleware.before_action(action, state)
        assert result is not None
        assert 'estimated_time_ms' in action.metadata
    
    @pytest.mark.asyncio
    async def test_performance_enforcement_strict_mode(self):
        """Test strict mode rejection of slow actions"""
        middleware = PerformanceEnforcementMiddleware(
            max_update_time_ms=0.1,  # Very low threshold
            strict_mode=True
        )
        
        # Create state with many components
        state = AppState()
        for i in range(2000):  # Large number to trigger rejection
            state.components.component_map[f"comp_{i}"] = {"id": f"comp_{i}", "type": "button"}
        
        action = ActionCreators.duplicate_component("comp_0", {"id": "new_comp", "type": "button"})
        
        # Should reject action in strict mode
        result = await middleware.before_action(action, state)
        assert result is None  # Action rejected


class TestSpatialIndex:
    """Test spatial indexing functionality"""
    
    def test_spatial_index_basic_operations(self):
        """Test basic spatial index operations"""
        index = SpatialIndex(grid_size=100)
        
        # Insert component
        bounds = BoundingBox(x=50, y=50, width=100, height=100)
        index.insert("comp1", bounds)
        
        assert "comp1" in index.component_bounds
        
        # Query point
        results = index.query_point(75, 75)
        assert "comp1" in results
        
        # Query point outside
        results = index.query_point(200, 200)
        assert "comp1" not in results
        
        # Remove component
        index.remove("comp1")
        assert "comp1" not in index.component_bounds
    
    def test_spatial_index_region_queries(self):
        """Test spatial region queries"""
        index = SpatialIndex(grid_size=50)
        
        # Insert multiple components
        components = [
            ("comp1", BoundingBox(0, 0, 50, 50)),
            ("comp2", BoundingBox(100, 100, 50, 50)),
            ("comp3", BoundingBox(25, 25, 50, 50))  # Overlaps with comp1
        ]
        
        for comp_id, bounds in components:
            index.insert(comp_id, bounds)
        
        # Query region that intersects comp1 and comp3
        region = BoundingBox(0, 0, 60, 60)
        results = index.query_region(region)
        
        assert "comp1" in results
        assert "comp3" in results
        assert "comp2" not in results
    
    def test_spatial_index_selection_box(self):
        """Test selection box queries"""
        index = SpatialIndex()
        
        # Insert components
        index.insert("comp1", BoundingBox(10, 10, 20, 20))
        index.insert("comp2", BoundingBox(50, 50, 20, 20))
        index.insert("comp3", BoundingBox(15, 15, 10, 10))  # Inside comp1 area
        
        # Selection box that includes comp1 and comp3
        selection = BoundingBox(5, 5, 30, 30)
        
        # Test intersection-based selection
        results = index.query_selection_box(selection, fully_contained=False)
        assert "comp1" in results
        assert "comp3" in results
        assert "comp2" not in results
        
        # Test fully-contained selection
        results = index.query_selection_box(selection, fully_contained=True)
        assert "comp1" not in results  # Only partially contained
        assert "comp3" in results      # Fully contained


class TestStateMigration:
    """Test state migration system"""
    
    def test_migration_manager_initialization(self):
        """Test migration manager setup"""
        manager = StateMigrationManager()
        
        assert manager.current_version == "1.0.0"
        assert len(manager.migrations) > 0
        
        # Check built-in migrations exist
        assert "0.1.0->0.2.0" in manager.migrations
        assert "0.2.0->1.0.0" in manager.migrations
    
    def test_version_detection(self):
        """Test version detection from state data"""
        manager = StateMigrationManager()
        
        # Test explicit version
        state_with_version = {"_schema_version": "0.2.0", "components": {}}
        version = manager._detect_version(state_with_version)
        assert version == "0.2.0"
        
        # Test structure-based detection
        old_state = {"components": [{"id": "comp1", "type": "button"}]}
        version = manager._detect_version(old_state)
        assert version == "0.1.0"
    
    def test_migration_from_0_1_0_to_0_2_0(self):
        """Test migration from components list to tree structure"""
        manager = StateMigrationManager()
        
        # Old state with components as list
        old_state = {
            "components": [
                {"id": "comp1", "type": "button", "name": "Button 1"},
                {"id": "comp2", "type": "text", "name": "Text 1"}
            ]
        }
        
        # Migrate
        migrated = manager.migrate_state(old_state, "0.1.0")
        
        # Verify new structure
        assert "components" in migrated
        components = migrated["components"]
        assert "component_map" in components
        assert "root_components" in components
        assert "parent_map" in components
        
        # Verify component data preserved
        assert "comp1" in components["component_map"]
        assert "comp2" in components["component_map"]
        assert components["component_map"]["comp1"]["name"] == "Button 1"
    
    def test_migration_validation(self):
        """Test migrated state validation"""
        manager = StateMigrationManager()
        
        # Valid migrated state
        valid_state = {
            "window": {},
            "panels": {},
            "theme": {},
            "components": {
                "root_components": ["comp1"],
                "component_map": {"comp1": {"id": "comp1", "type": "button"}},
                "parent_map": {}
            },
            "selection": {},
            "canvas": {}
        }
        
        assert manager.validate_migrated_state(valid_state)
        
        # Invalid state (missing required keys)
        invalid_state = {"components": {}}
        assert not manager.validate_migrated_state(invalid_state)


class TestEnhancedIntegration:
    """Test the complete enhanced state management system"""
    
    @pytest.mark.asyncio
    async def test_complete_system_with_all_features(self):
        """Test the complete system with all enhanced features"""
        with tempfile.TemporaryDirectory() as temp_dir:
            system = StateManagementSystem(
                storage_path=Path(temp_dir),
                enable_debug=True,
                enforce_performance=True,
                strict_performance=False
            )
            
            await system.initialize()
            
            # Test component operations with spatial indexing
            component_data = {
                "id": "test-button",
                "type": "button",
                "name": "Test Button",
                "style": {"left": "100", "top": "100", "width": "80", "height": "30"}
            }
            
            await system.add_component(component_data)
            
            # Test spatial queries
            components_at_point = system.get_state("components").get_components_at_point(120, 110)
            assert "test-button" in components_at_point
            
            # Test history recording
            assert system.can_undo()
            
            # Test performance monitoring
            metrics = system.get_performance_metrics()
            assert "state_metrics" in metrics
            
            # Test debug information
            debug_info = system.export_debug_info()
            assert "state_summary" in debug_info
            assert "integrity_issues" in debug_info
            
            await system.shutdown()
    
    @pytest.mark.asyncio
    async def test_state_persistence_with_migration(self):
        """Test state persistence with automatic migration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir)
            
            # Save old format state
            old_state = {
                "components": [{"id": "comp1", "type": "button"}],
                "_schema_version": "0.1.0"
            }
            
            # Save manually to simulate old format
            with open(storage_path / "app_state.json", "w") as f:
                json.dump(old_state, f)
            
            # Initialize system - should automatically migrate
            system = StateManagementSystem(storage_path=storage_path)
            await system.initialize()
            
            # Verify migration occurred
            state = system.get_state()
            assert hasattr(state.components, 'component_map')
            assert "comp1" in state.components.component_map
            
            await system.shutdown()


# Integration test with mocked Flet components
class TestUIIntegration:
    """Test UI component integration (mocked)"""
    
    @pytest.mark.asyncio
    async def test_component_binding(self):
        """Test binding UI components to state"""
        with tempfile.TemporaryDirectory() as temp_dir:
            async with StateContext(storage_path=Path(temp_dir)) as system:
                # Mock Flet component
                mock_text = Mock()
                mock_text.value = ""
                mock_text.update = Mock()
                
                # Bind component to state
                unsubscribe = system.bind_text(mock_text, "theme.mode")
                
                # Change theme
                await system.change_theme("dark")
                await asyncio.sleep(0.1)  # Allow time for update
                
                # Verify component was updated
                mock_text.update.assert_called()
                
                # Cleanup
                unsubscribe()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])