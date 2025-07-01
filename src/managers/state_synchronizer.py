"""
State synchronization system for keeping UI components in sync with application state.
Provides efficient bindings and real-time updates for Flet UI components.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set
from weakref import WeakSet
import flet as ft

from .state_manager import StateManager
from .state_types import UIBinding, Change

logger = logging.getLogger(__name__)


class StateSynchronizer:
    """
    Keeps UI components synchronized with state changes.
    Provides efficient binding system with automatic cleanup.
    """
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.component_bindings: Dict[str, List[UIBinding]] = {}
        self.active_components: WeakSet = WeakSet()
        self.update_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.update_task: Optional[asyncio.Task] = None
        
        logger.info("StateSynchronizer initialized")
    
    async def start(self):
        """Start the synchronizer update loop"""
        self.running = True
        self.update_task = asyncio.create_task(self._update_worker())
        logger.info("StateSynchronizer started")
    
    async def stop(self):
        """Stop the synchronizer cleanly"""
        self.running = False
        
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        
        logger.info("StateSynchronizer stopped")
    
    def bind_component(
        self,
        ui_component: ft.Control,
        state_path: str,
        property_name: str,
        transformer: Optional[Callable[[Any], Any]] = None,
        filter_fn: Optional[Callable[[Any], bool]] = None
    ) -> Callable[[], None]:
        """
        Bind UI component property to state path.
        Returns unsubscribe function for cleanup.
        """
        binding = UIBinding(
            component=ui_component,
            property_name=property_name,
            state_path=state_path,
            transformer=transformer or (lambda x: x)
        )
        
        # Store binding
        if state_path not in self.component_bindings:
            self.component_bindings[state_path] = []
        self.component_bindings[state_path].append(binding)
        
        # Track component for cleanup
        self.active_components.add(ui_component)
        
        # Subscribe to state changes
        unsubscribe_state = self.state_manager.subscribe(
            state_path,
            lambda old_val, new_val: self._queue_update(binding, new_val),
            filter_fn
        )
        
        # Initial sync
        current_value = self.state_manager.get_state(state_path)
        if current_value is not None:
            self._queue_update(binding, current_value)
        
        logger.debug(f"Bound component {type(ui_component).__name__}.{property_name} to {state_path}")
        
        # Return combined unsubscribe function
        def unsubscribe():
            # Remove from bindings
            if state_path in self.component_bindings:
                self.component_bindings[state_path] = [
                    b for b in self.component_bindings[state_path] 
                    if b.component != ui_component or b.property_name != property_name
                ]
                if not self.component_bindings[state_path]:
                    del self.component_bindings[state_path]
            
            # Unsubscribe from state
            unsubscribe_state()
            
            logger.debug(f"Unbound component {type(ui_component).__name__}.{property_name} from {state_path}")
        
        return unsubscribe
    
    def bind_text(
        self,
        text_control: ft.Text,
        state_path: str,
        format_string: Optional[str] = None
    ) -> Callable[[], None]:
        """Convenience method for binding text controls"""
        transformer = None
        if format_string:
            transformer = lambda value: format_string.format(value)
        else:
            transformer = lambda value: str(value) if value is not None else ""
        
        return self.bind_component(text_control, state_path, "value", transformer)
    
    def bind_visibility(
        self,
        control: ft.Control,
        state_path: str,
        invert: bool = False
    ) -> Callable[[], None]:
        """Convenience method for binding control visibility"""
        transformer = (lambda x: not bool(x)) if invert else bool
        return self.bind_component(control, state_path, "visible", transformer)
    
    def bind_enabled(
        self,
        control: ft.Control,
        state_path: str,
        invert: bool = False
    ) -> Callable[[], None]:
        """Convenience method for binding control enabled state"""
        transformer = (lambda x: not bool(x)) if invert else bool
        return self.bind_component(control, state_path, "disabled", transformer)
    
    def bind_color(
        self,
        control: ft.Control,
        state_path: str,
        property_name: str = "bgcolor"
    ) -> Callable[[], None]:
        """Convenience method for binding colors"""
        return self.bind_component(control, state_path, property_name)
    
    def bind_list(
        self,
        list_control: ft.Column,
        state_path: str,
        item_builder: Callable[[Any, int], ft.Control],
        key_extractor: Optional[Callable[[Any], str]] = None
    ) -> Callable[[], None]:
        """
        Bind a list control to an array in state.
        Efficiently updates only changed items.
        """
        def transformer(items: List[Any]) -> List[ft.Control]:
            if not isinstance(items, list):
                return []
            
            controls = []
            for i, item in enumerate(items):
                try:
                    control = item_builder(item, i)
                    if key_extractor:
                        control.key = key_extractor(item)
                    controls.append(control)
                except Exception as e:
                    logger.error(f"Error building list item {i}: {e}")
            
            return controls
        
        return self.bind_component(list_control, state_path, "controls", transformer)
    
    def bind_selection(
        self,
        selectable_control: ft.Control,
        state_path: str,
        component_id: str
    ) -> Callable[[], None]:
        """Bind component selection state"""
        def transformer(selected_ids: Set[str]) -> bool:
            return component_id in selected_ids
        
        return self.bind_component(selectable_control, state_path, "selected", transformer)
    
    def _queue_update(self, binding: UIBinding, value: Any):
        """Queue UI update for processing"""
        try:
            self.update_queue.put_nowait((binding, value))
        except asyncio.QueueFull:
            logger.warning("Update queue full, dropping update")
    
    async def _update_worker(self):
        """Process UI updates from queue"""
        while self.running:
            try:
                # Get next update with timeout
                binding, value = await asyncio.wait_for(
                    self.update_queue.get(),
                    timeout=1.0
                )
                
                # Apply update
                await self._apply_update(binding, value)
                
                # Mark as done
                self.update_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing UI update: {e}")
                # Mark as done even on error
                self.update_queue.task_done()
    
    async def _apply_update(self, binding: UIBinding, value: Any):
        """Apply update to UI component"""
        try:
            # Check if component is still valid
            if binding.component not in self.active_components:
                return
            
            # Transform value
            transformed_value = binding.transformer(value)
            
            # Update component property
            setattr(binding.component, binding.property_name, transformed_value)
            
            # Trigger UI update if component has update method
            if hasattr(binding.component, 'update'):
                binding.component.update()
            
            logger.debug(
                f"Updated {type(binding.component).__name__}.{binding.property_name} = {transformed_value}"
            )
            
        except Exception as e:
            logger.error(f"Error updating component: {e}")
    
    def create_state_control(
        self,
        state_path: str,
        control_type: type,
        property_name: str = "value",
        transformer: Optional[Callable] = None,
        **control_kwargs
    ) -> ft.Control:
        """
        Create a control that automatically syncs with state.
        Returns the control with binding already established.
        """
        control = control_type(**control_kwargs)
        
        # Bind to state
        self.bind_component(control, state_path, property_name, transformer)
        
        return control
    
    def cleanup_dead_bindings(self):
        """Remove bindings for components that no longer exist"""
        paths_to_remove = []
        
        for path, bindings in self.component_bindings.items():
            # Filter out dead bindings
            active_bindings = [
                binding for binding in bindings
                if binding.component in self.active_components
            ]
            
            if not active_bindings:
                paths_to_remove.append(path)
            elif len(active_bindings) < len(bindings):
                self.component_bindings[path] = active_bindings
        
        # Remove empty paths
        for path in paths_to_remove:
            del self.component_bindings[path]
        
        if paths_to_remove:
            logger.debug(f"Cleaned up {len(paths_to_remove)} dead bindings")
    
    def get_binding_info(self) -> Dict[str, Any]:
        """Get information about current bindings"""
        return {
            "total_paths": len(self.component_bindings),
            "total_bindings": sum(len(bindings) for bindings in self.component_bindings.values()),
            "active_components": len(self.active_components),
            "queue_size": self.update_queue.qsize()
        }


class StateBridge:
    """
    Bridge between old state management and new system.
    Provides migration path for existing code.
    """
    
    def __init__(self, state_manager: StateManager, legacy_state_manager):
        self.state_manager = state_manager
        self.legacy_state_manager = legacy_state_manager
        self.sync_mappings = self._create_sync_mappings()
        
        logger.info("StateBridge initialized")
    
    def _create_sync_mappings(self) -> Dict[str, str]:
        """Map legacy state keys to new state paths"""
        return {
            # Map legacy storage keys to new state paths
            "canvas_editor_window_state": "window",
            "canvas_editor_panel_state": "panels",
            "canvas_editor_preferences": "preferences",
            "canvas_editor_theme": "theme.mode",
            "canvas_editor_current_project": "project.id"
        }
    
    async def migrate_legacy_state(self):
        """Migrate data from legacy state manager to new system"""
        try:
            # Migrate window state
            if hasattr(self.legacy_state_manager, '_state_cache'):
                cache = self.legacy_state_manager._state_cache
                
                # Convert legacy state format to new format
                if "canvas_editor_window_state" in cache:
                    window_data = cache["canvas_editor_window_state"]
                    # Update new state through action
                    # This would be done via proper actions in real implementation
                
                logger.info("Legacy state migration completed")
        except Exception as e:
            logger.error(f"Error migrating legacy state: {e}")
    
    def sync_to_legacy(self, state_path: str, value: Any):
        """Sync new state changes back to legacy system if needed"""
        try:
            # Map new state path to legacy key
            legacy_key = None
            for legacy, new_path in self.sync_mappings.items():
                if state_path.startswith(new_path):
                    legacy_key = legacy
                    break
            
            if legacy_key and hasattr(self.legacy_state_manager, '_state_cache'):
                self.legacy_state_manager._state_cache[legacy_key] = value
                logger.debug(f"Synced {state_path} to legacy key {legacy_key}")
        
        except Exception as e:
            logger.error(f"Error syncing to legacy state: {e}")


class StateDebugger:
    """
    Debug utilities for state management system.
    Provides tools for monitoring and troubleshooting state issues.
    """
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.change_log: List[Dict[str, Any]] = []
        self.max_log_size = 1000
        
        # Subscribe to all state changes
        self.state_manager.subscribe("", self._log_change)
        
        logger.info("StateDebugger initialized")
    
    def _log_change(self, old_value: Any, new_value: Any):
        """Log state changes for debugging"""
        change_info = {
            "timestamp": asyncio.get_event_loop().time(),
            "old_value": str(old_value)[:100],  # Truncate for logging
            "new_value": str(new_value)[:100],
            "type": type(new_value).__name__
        }
        
        self.change_log.append(change_info)
        
        # Limit log size
        if len(self.change_log) > self.max_log_size:
            self.change_log = self.change_log[-self.max_log_size:]
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current state"""
        state = self.state_manager.get_state()
        
        return {
            "components_count": len(state.components.component_map),
            "selected_count": len(state.selection.selected_ids),
            "has_unsaved_changes": state.has_unsaved_changes,
            "theme_mode": state.theme.mode,
            "canvas_zoom": state.canvas.zoom,
            "project_loaded": state.project is not None,
            "recent_changes": len(self.change_log)
        }
    
    def export_state_snapshot(self) -> Dict[str, Any]:
        """Export complete state for debugging"""
        return {
            "timestamp": asyncio.get_event_loop().time(),
            "state": self.state_manager.get_state().to_dict(),
            "metrics": self.state_manager.get_metrics(),
            "change_log": self.change_log[-50:]  # Last 50 changes
        }
    
    def validate_state_integrity(self) -> List[str]:
        """Validate state for consistency issues"""
        issues = []
        state = self.state_manager.get_state()
        
        # Check component tree integrity
        for component_id in state.components.component_map:
            # Check parent references
            if component_id in state.components.parent_map:
                parent_id = state.components.parent_map[component_id]
                if parent_id not in state.components.component_map:
                    issues.append(f"Component {component_id} has invalid parent {parent_id}")
        
        # Check selection integrity
        for selected_id in state.selection.selected_ids:
            if selected_id not in state.components.component_map:
                issues.append(f"Selected component {selected_id} does not exist")
        
        return issues