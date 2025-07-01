"""
State Management Integration Module.
Provides a unified interface and initialization for the complete state management system.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import flet as ft

from .state_manager import StateManager, StateStorage
from .state_middleware import (
    ValidationMiddleware, LoggingMiddleware, PerformanceMiddleware,
    AutoSaveMiddleware, SecurityMiddleware
)
from .history_middleware import (
    HistoryMiddleware, PerformanceEnforcementMiddleware, StateIntegrityMiddleware
)
from .history_manager import HistoryManager
from .state_synchronizer import StateSynchronizer, StateBridge, StateDebugger
from .action_creators import ActionCreators
from .state_types import AppState

logger = logging.getLogger(__name__)


class StateManagementSystem:
    """
    Complete state management system integration.
    Provides unified interface for all state management functionality.
    """
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        max_history: int = 1000,
        max_memory_mb: int = 100,
        enable_debug: bool = False,
        enforce_performance: bool = True,
        strict_performance: bool = False
    ):
        # Core components
        self.storage = StateStorage(storage_path or Path.home() / ".canvas_editor")
        self.state_manager = StateManager(storage=self.storage)
        self.history_manager = HistoryManager(max_history, max_memory_mb)
        self.synchronizer = StateSynchronizer(self.state_manager)
        
        # Core middleware
        self.security_middleware = SecurityMiddleware()
        self.validation_middleware = ValidationMiddleware()
        self.history_middleware = HistoryMiddleware(self.history_manager)
        self.logging_middleware = LoggingMiddleware()
        self.performance_middleware = PerformanceMiddleware()
        self.autosave_middleware = AutoSaveMiddleware(self.storage)
        
        # Enhanced middleware
        self.performance_enforcement = None
        self.integrity_middleware = None
        
        if enforce_performance:
            self.performance_enforcement = PerformanceEnforcementMiddleware(
                strict_mode=strict_performance
            )
        
        if enable_debug:
            self.integrity_middleware = StateIntegrityMiddleware(enable_deep_validation=True)
        
        # Optional components
        self.debugger = StateDebugger(self.state_manager) if enable_debug else None
        self.bridge: Optional[StateBridge] = None
        
        # Action creators
        self.actions = ActionCreators()
        
        # State
        self.running = False
        
        logger.info("StateManagementSystem initialized")
    
    async def initialize(self, legacy_state_manager=None):
        """Initialize the complete state management system"""
        try:
            # Setup middleware pipeline in order of execution
            # 1. Security - first line of defense
            self.state_manager.add_middleware(self.security_middleware)
            
            # 2. Performance enforcement - reject slow actions early
            if self.performance_enforcement:
                self.state_manager.add_middleware(self.performance_enforcement)
            
            # 3. Validation - ensure action validity
            self.state_manager.add_middleware(self.validation_middleware)
            
            # 4. History - capture state before changes
            self.state_manager.add_middleware(self.history_middleware)
            
            # 5. Logging - audit trail
            self.state_manager.add_middleware(self.logging_middleware)
            
            # 6. Performance monitoring - track actual performance
            self.state_manager.add_middleware(self.performance_middleware)
            
            # 7. State integrity - validate after changes
            if self.integrity_middleware:
                self.state_manager.add_middleware(self.integrity_middleware)
            
            # 8. Auto-save - persist changes
            self.state_manager.add_middleware(self.autosave_middleware)
            
            # Start core components
            await self.state_manager.start()
            await self.synchronizer.start()
            
            # Setup legacy bridge if provided
            if legacy_state_manager:
                self.bridge = StateBridge(self.state_manager, legacy_state_manager)
                await self.bridge.migrate_legacy_state()
            
            self.running = True
            logger.info("StateManagementSystem initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing state management system: {e}")
            raise
    
    async def shutdown(self):
        """Gracefully shutdown the state management system"""
        try:
            self.running = False
            
            # Stop components
            await self.synchronizer.stop()
            await self.state_manager.stop()
            
            logger.info("StateManagementSystem shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    # State access methods
    def get_state(self, path: str = "") -> Any:
        """Get current state at path"""
        return self.state_manager.get_state(path)
    
    def subscribe(self, path: str, callback, filter_fn=None):
        """Subscribe to state changes"""
        return self.state_manager.subscribe(path, callback, filter_fn)
    
    # Action dispatch
    async def dispatch(self, action):
        """Dispatch an action through the complete middleware pipeline"""
        if self.running:
            await self.state_manager.dispatch(action)
        else:
            raise RuntimeError("State management system not running")
    
    # History operations
    async def undo(self):
        """Undo last action"""
        undo_action = await self.history_manager.undo()
        if undo_action:
            await self.state_manager.dispatch(undo_action)
        return undo_action is not None
    
    async def redo(self):
        """Redo next action"""
        redo_action = await self.history_manager.redo()
        if redo_action:
            await self.state_manager.dispatch(redo_action)
        return redo_action is not None
    
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return self.history_manager.can_undo()
    
    def can_redo(self) -> bool:
        """Check if redo is available"""
        return self.history_manager.can_redo()
    
    def get_history_timeline(self, start: int = 0, limit: int = 50):
        """Get history timeline for UI"""
        return self.history_manager.get_history_timeline(start, limit)
    
    # Batch operations
    def start_batch(self, description: str = "Batch Operation") -> str:
        """Start a batch operation"""
        return self.history_manager.start_batch(description)
    
    def end_batch(self, batch_id: str):
        """End a batch operation"""
        self.history_manager.end_batch(batch_id)
    
    # UI binding convenience methods
    def bind_component(self, ui_component, state_path: str, property_name: str, transformer=None):
        """Bind UI component to state"""
        return self.synchronizer.bind_component(ui_component, state_path, property_name, transformer)
    
    def bind_text(self, text_control: ft.Text, state_path: str, format_string: str = None):
        """Bind text control to state"""
        return self.synchronizer.bind_text(text_control, state_path, format_string)
    
    def bind_visibility(self, control: ft.Control, state_path: str, invert: bool = False):
        """Bind control visibility to state"""
        return self.synchronizer.bind_visibility(control, state_path, invert)
    
    def bind_list(self, list_control: ft.Column, state_path: str, item_builder, key_extractor=None):
        """Bind list control to state array"""
        return self.synchronizer.bind_list(list_control, state_path, item_builder, key_extractor)
    
    # Component operations
    async def add_component(self, component_data: Dict[str, Any], parent_id: str = None):
        """Add a new component"""
        action = self.actions.add_component(component_data, parent_id)
        await self.dispatch(action)
    
    async def update_component(self, component_id: str, updates: Dict[str, Any]):
        """Update component properties"""
        action = self.actions.update_component(component_id, updates)
        await self.dispatch(action)
    
    async def delete_component(self, component_id: str):
        """Delete a component"""
        action = self.actions.delete_component(component_id)
        await self.dispatch(action)
    
    async def select_component(self, component_id: str, multi_select: bool = False):
        """Select a component"""
        action = self.actions.select_component(component_id, multi_select)
        await self.dispatch(action)
    
    async def clear_selection(self):
        """Clear component selection"""
        action = self.actions.clear_selection()
        await self.dispatch(action)
    
    # Project operations
    async def create_project(self, project_data: Dict[str, Any]):
        """Create a new project"""
        action = self.actions.create_project(project_data)
        await self.dispatch(action)
    
    async def open_project(self, project_id: str, project_data: Dict[str, Any]):
        """Open an existing project"""
        action = self.actions.open_project(project_id, project_data)
        await self.dispatch(action)
    
    async def save_project(self, project_id: str = None):
        """Save the current project"""
        action = self.actions.save_project(project_id)
        await self.dispatch(action)
    
    # UI operations
    async def resize_panel(self, panel_name: str, new_width: float):
        """Resize a panel"""
        old_width = self.get_state(f"panels.{panel_name}_width")
        action = self.actions.resize_panel(panel_name, new_width, old_width)
        await self.dispatch(action)
    
    async def toggle_panel(self, panel_name: str, visible: bool):
        """Toggle panel visibility"""
        action = self.actions.toggle_panel(panel_name, visible)
        await self.dispatch(action)
    
    async def change_theme(self, theme_mode: str):
        """Change application theme"""
        action = self.actions.change_theme(theme_mode)
        await self.dispatch(action)
    
    # Canvas operations
    async def zoom_canvas(self, zoom_delta: float, zoom_center: Dict[str, float] = None):
        """Zoom the canvas"""
        action = self.actions.zoom_canvas(zoom_delta, zoom_center)
        await self.dispatch(action)
    
    async def pan_canvas(self, delta_x: float, delta_y: float):
        """Pan the canvas"""
        action = self.actions.pan_canvas(delta_x, delta_y)
        await self.dispatch(action)
    
    async def toggle_grid(self, show_grid: bool):
        """Toggle grid visibility"""
        action = self.actions.toggle_grid(show_grid)
        await self.dispatch(action)
    
    # Utility methods
    def get_component(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Get component data by ID"""
        components = self.get_state("components.component_map")
        return components.get(component_id) if components else None
    
    def get_selected_components(self) -> List[str]:
        """Get list of selected component IDs"""
        selected_ids = self.get_state("selection.selected_ids")
        return list(selected_ids) if selected_ids else []
    
    def get_component_tree(self) -> Dict[str, Any]:
        """Get the complete component tree"""
        return self.get_state("components")
    
    def get_canvas_state(self) -> Dict[str, Any]:
        """Get current canvas state"""
        return self.get_state("canvas")
    
    def get_project_info(self) -> Optional[Dict[str, Any]]:
        """Get current project information"""
        return self.get_state("project")
    
    # Performance and debugging
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            "state_metrics": self.state_manager.get_metrics(),
            "history_stats": self.history_manager.get_statistics(),
            "synchronizer_info": self.synchronizer.get_binding_info()
        }
    
    def cleanup_dead_references(self):
        """Clean up dead component references"""
        self.synchronizer.cleanup_dead_bindings()
    
    def export_debug_info(self) -> Dict[str, Any]:
        """Export comprehensive debug information"""
        debug_info = {
            "state_summary": self.debugger.get_state_summary() if self.debugger else {},
            "performance_metrics": self.get_performance_metrics(),
            "system_status": {
                "running": self.running,
                "components_active": len(self.synchronizer.active_components),
                "middleware_count": len(self.state_manager._middleware)
            }
        }
        
        if self.debugger:
            debug_info["state_snapshot"] = self.debugger.export_state_snapshot()
            debug_info["integrity_issues"] = self.debugger.validate_state_integrity()
        
        return debug_info


class StateContext:
    """
    Context manager for state management system.
    Provides clean setup and teardown.
    """
    
    def __init__(self, **kwargs):
        self.system = StateManagementSystem(**kwargs)
        self.legacy_state_manager = None
    
    async def __aenter__(self):
        await self.system.initialize(self.legacy_state_manager)
        return self.system
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.system.shutdown()
    
    def with_legacy_migration(self, legacy_state_manager):
        """Configure legacy state migration"""
        self.legacy_state_manager = legacy_state_manager
        return self


# Global instance for easy access (optional)
_global_state_system: Optional[StateManagementSystem] = None


def get_state_system() -> Optional[StateManagementSystem]:
    """Get the global state management system instance"""
    return _global_state_system


def set_state_system(system: StateManagementSystem):
    """Set the global state management system instance"""
    global _global_state_system
    _global_state_system = system


async def initialize_global_state_system(**kwargs) -> StateManagementSystem:
    """Initialize and set global state management system"""
    system = StateManagementSystem(**kwargs)
    await system.initialize()
    set_state_system(system)
    return system


# Convenience functions for common operations
async def dispatch_action(action):
    """Dispatch action using global state system"""
    system = get_state_system()
    if system:
        await system.dispatch(action)
    else:
        raise RuntimeError("State management system not initialized")


def get_current_state(path: str = ""):
    """Get current state using global system"""
    system = get_state_system()
    if system:
        return system.get_state(path)
    else:
        raise RuntimeError("State management system not initialized")


def subscribe_to_state(path: str, callback, filter_fn=None):
    """Subscribe to state changes using global system"""
    system = get_state_system()
    if system:
        return system.subscribe(path, callback, filter_fn)
    else:
        raise RuntimeError("State management system not initialized")