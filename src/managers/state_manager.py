"""
Core State Manager implementation with dispatch system, subscriptions, and middleware.
Implements the central state management architecture from the development plan.
"""

import asyncio
import copy
import json
import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from pathlib import Path

from .state_types import (
    Action, ActionType, AppState, Change, ChangeType, Subscriber, 
    StateMetrics, ValidationResult, UIBinding, ComponentTreeState, SelectionState
)
from .state_migration import StateMigrationManager

logger = logging.getLogger(__name__)


class InvalidActionError(Exception):
    """Raised when an invalid action is dispatched"""
    pass


class StateStorage:
    """Handles state persistence to disk with async operations and automatic migration"""
    
    def __init__(self, storage_path: Path, enable_migration: bool = True):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.migration_manager = StateMigrationManager() if enable_migration else None
        
        logger.info(f"StateStorage initialized at {storage_path}")
        
    async def save_state(self, key: str, state_data: Dict[str, Any]) -> bool:
        """Save state to disk atomically with versioning"""
        try:
            file_path = self.storage_path / f"{key}.json"
            temp_file = file_path.with_suffix('.tmp')
            
            # Add schema version to state data
            versioned_data = state_data.copy()
            if self.migration_manager:
                versioned_data['_schema_version'] = self.migration_manager.current_version
                versioned_data['_saved_at'] = time.time()
            
            # Write to temp file first
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(versioned_data, f, indent=2, default=str)
            
            # Atomic move to final location
            temp_file.replace(file_path)
            
            logger.debug(f"Successfully saved state to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving state {key}: {e}")
            return False
    
    async def load_state(self, key: str, auto_migrate: bool = True) -> Optional[Dict[str, Any]]:
        """Load state from disk with automatic migration"""
        try:
            file_path = self.storage_path / f"{key}.json"
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Migrate state if needed
            if auto_migrate and self.migration_manager:
                migrated_data = await self._migrate_state_if_needed(data, key)
                if migrated_data is not data:  # Migration occurred
                    # Save migrated state
                    await self.save_state(f"{key}_migrated_backup", data)  # Backup original
                    await self.save_state(key, migrated_data)  # Save migrated
                    data = migrated_data
            
            logger.debug(f"Successfully loaded state from {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading state {key}: {e}")
            return None
    
    async def _migrate_state_if_needed(self, state_data: Dict[str, Any], key: str) -> Dict[str, Any]:
        """Migrate state if it's from an older version"""
        if not self.migration_manager:
            return state_data
        
        try:
            # Detect current version
            current_version = state_data.get('_schema_version')
            target_version = self.migration_manager.current_version
            
            if current_version == target_version:
                return state_data  # Already current
            
            logger.info(f"Migrating state {key} from {current_version or 'unknown'} to {target_version}")
            
            # Create backup before migration
            backup_data = self.migration_manager.create_backup(state_data, current_version or 'unknown')
            backup_path = self.storage_path / f"{key}_backup_{int(time.time())}.json"
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Perform migration
            migrated_data = self.migration_manager.migrate_state(state_data, current_version)
            
            # Validate migrated state
            if not self.migration_manager.validate_migrated_state(migrated_data):
                logger.error("Migrated state validation failed, keeping original")
                return state_data
            
            logger.info(f"State migration completed successfully for {key}")
            return migrated_data
            
        except Exception as e:
            logger.error(f"State migration failed for {key}: {e}")
            return state_data  # Return original on failure
    
    def get_migration_info(self) -> Optional[Dict[str, Any]]:
        """Get migration system information"""
        return self.migration_manager.get_migration_info() if self.migration_manager else None


class StateManager:
    """
    Central state management with dispatch system, subscriptions, and middleware.
    Provides single source of truth for all application state.
    """
    
    def __init__(
        self,
        initial_state: Optional[AppState] = None,
        storage: Optional[StateStorage] = None
    ):
        self._state = initial_state or AppState()
        self._storage = storage
        self._subscribers: Dict[str, List[Subscriber]] = {}
        self._middleware: List['Middleware'] = []
        self._lock = asyncio.Lock()
        self._dispatch_queue: asyncio.Queue[Action] = asyncio.Queue()
        self._running = False
        
        # Performance monitoring
        self._metrics = StateMetrics()
        
        # Dispatch worker task
        self._dispatch_task: Optional[asyncio.Task] = None
        
        logger.info("StateManager initialized")
    
    async def start(self):
        """Start the state manager and load persisted state"""
        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch_worker())
        
        # Load persisted state if available
        if self._storage:
            try:
                persisted = await self._storage.load_state("app_state")
                if persisted:
                    self._state = AppState.from_dict(persisted)
                    logger.info("Loaded persisted state")
            except Exception as e:
                logger.error(f"Error loading persisted state: {e}")
        
        logger.info("StateManager started")
    
    async def stop(self):
        """Stop the state manager cleanly"""
        logger.info("Stopping StateManager...")
        self._running = False
        
        # Process remaining actions
        await self._dispatch_queue.join()
        
        # Cancel worker
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
        
        # Final save
        if self._storage:
            try:
                await self._storage.save_state("app_state", self._state.to_dict())
                logger.info("Saved final state")
            except Exception as e:
                logger.error(f"Error saving final state: {e}")
        
        logger.info("StateManager stopped")
    
    async def dispatch(self, action: Action) -> None:
        """
        Dispatch an action to update state.
        Actions are queued and processed asynchronously.
        """
        # Validate action
        validation = action.validate()
        if not validation.is_valid:
            raise InvalidActionError(f"Invalid action: {validation.errors}")
        
        # Add to dispatch queue
        await self._dispatch_queue.put(action)
        
        logger.debug(f"Dispatched {action.type.name}: {action.description}")
    
    async def _dispatch_worker(self):
        """Process actions from queue with error handling"""
        while self._running:
            try:
                # Get next action with timeout
                action = await asyncio.wait_for(
                    self._dispatch_queue.get(),
                    timeout=1.0
                )
                
                # Process action
                await self._process_action(action)
                
                # Mark as done
                self._dispatch_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing action: {e}", exc_info=True)
                # Mark as done even on error to prevent queue blocking
                self._dispatch_queue.task_done()
    
    async def _process_action(self, action: Action):
        """Process a single action through middleware and reducers"""
        start_time = time.perf_counter()
        
        async with self._lock:
            try:
                # Before middleware
                for middleware in self._middleware:
                    action = await middleware.before_action(action, self._state)
                    if action is None:
                        logger.info(f"Action cancelled by {middleware.__class__.__name__}")
                        return
                
                # Calculate next state
                old_state = self._deep_copy_state(self._state)
                new_state = await self._apply_action(action, old_state)
                
                # Calculate changes
                changes = self._diff_states(old_state, new_state)
                
                # Update state
                self._state = new_state
                
                # Notify subscribers
                await self._notify_subscribers(changes)
                
                # After middleware
                for middleware in self._middleware:
                    await middleware.after_action(action, self._state, changes)
                
                # Update metrics
                duration = time.perf_counter() - start_time
                self._metrics.record_action(action.type, duration, len(changes))
                
                logger.debug(f"Processed {action.type.name} in {duration:.3f}s")
                
            except Exception as e:
                logger.error(f"Failed to process action {action.type}: {e}")
                raise
    
    async def _apply_action(self, action: Action, state: AppState) -> AppState:
        """Apply action to state and return new state"""
        # Create a deep copy for immutable updates
        new_state = self._deep_copy_state(state)
        
        # Apply changes based on action type
        if action.type == ActionType.ADD_COMPONENT:
            await self._apply_add_component(action, new_state)
        elif action.type == ActionType.UPDATE_COMPONENT:
            await self._apply_update_component(action, new_state)
        elif action.type == ActionType.DELETE_COMPONENT:
            await self._apply_delete_component(action, new_state)
        elif action.type == ActionType.SELECT_COMPONENT:
            await self._apply_select_component(action, new_state)
        elif action.type == ActionType.DESELECT_COMPONENT:
            await self._apply_deselect_component(action, new_state)
        elif action.type == ActionType.CLEAR_SELECTION:
            await self._apply_clear_selection(action, new_state)
        elif action.type == ActionType.CHANGE_THEME:
            await self._apply_change_theme(action, new_state)
        elif action.type == ActionType.RESIZE_PANEL:
            await self._apply_resize_panel(action, new_state)
        elif action.type == ActionType.ZOOM_CANVAS:
            await self._apply_zoom_canvas(action, new_state)
        elif action.type == ActionType.PAN_CANVAS:
            await self._apply_pan_canvas(action, new_state)
        elif action.type == ActionType.CREATE_PROJECT:
            await self._apply_create_project(action, new_state)
        elif action.type == ActionType.OPEN_PROJECT:
            await self._apply_open_project(action, new_state)
        elif action.type == ActionType.SAVE_PROJECT:
            await self._apply_save_project(action, new_state)
        elif action.type == ActionType.CLOSE_PROJECT:
            await self._apply_close_project(action, new_state)
        elif action.type == ActionType.UPDATE_PROJECT_META:
            await self._apply_update_project_meta(action, new_state)
        # Add more action handlers as needed
        
        # Update modification timestamp
        new_state.has_unsaved_changes = True
        
        return new_state
    
    async def _apply_add_component(self, action: Action, state: AppState):
        """Apply add component action"""
        component_data = action.payload.get('component_data', {})
        parent_id = action.payload.get('parent_id')
        
        state.components.add_component(component_data, parent_id)
    
    async def _apply_update_component(self, action: Action, state: AppState):
        """Apply update component action"""
        component_id = action.payload.get('component_id')
        updates = action.payload.get('updates', {})
        
        if component_id in state.components.component_map:
            component = state.components.component_map[component_id]
            component.update(updates)
            state.components.dirty_components.add(component_id)
    
    async def _apply_delete_component(self, action: Action, state: AppState):
        """Apply delete component action"""
        component_id = action.payload.get('component_id')
        state.components.remove_component(component_id)
        
        # Remove from selection if selected
        state.selection.selected_ids.discard(component_id)
        if state.selection.last_selected == component_id:
            state.selection.last_selected = None
    
    async def _apply_select_component(self, action: Action, state: AppState):
        """Apply select component action"""
        component_id = action.payload.get('component_id')
        multi_select = action.payload.get('multi_select', False)
        
        if not multi_select:
            state.selection.selected_ids.clear()
        
        state.selection.selected_ids.add(component_id)
        state.selection.last_selected = component_id
    
    async def _apply_deselect_component(self, action: Action, state: AppState):
        """Apply deselect component action"""
        component_id = action.payload.get('component_id')
        state.selection.selected_ids.discard(component_id)
        
        if state.selection.last_selected == component_id:
            state.selection.last_selected = None
    
    async def _apply_clear_selection(self, action: Action, state: AppState):
        """Apply clear selection action"""
        state.selection.selected_ids.clear()
        state.selection.last_selected = None
    
    async def _apply_change_theme(self, action: Action, state: AppState):
        """Apply theme change action"""
        theme_mode = action.payload.get('mode')
        if theme_mode:
            state.theme.mode = theme_mode
    
    async def _apply_resize_panel(self, action: Action, state: AppState):
        """Apply panel resize action"""
        panel_name = action.payload.get('panel')
        new_width = action.payload.get('width')
        
        if panel_name == 'sidebar':
            state.panels.sidebar_width = new_width
        elif panel_name == 'components':
            state.panels.components_width = new_width
        elif panel_name == 'properties':
            state.panels.properties_width = new_width
    
    async def _apply_zoom_canvas(self, action: Action, state: AppState):
        """Apply canvas zoom action"""
        zoom_delta = action.payload.get('delta', 0)
        zoom_center = action.payload.get('center')
        
        new_zoom = max(0.1, min(5.0, state.canvas.zoom + zoom_delta))
        state.canvas.zoom = new_zoom
    
    async def _apply_pan_canvas(self, action: Action, state: AppState):
        """Apply canvas pan action"""
        delta_x = action.payload.get('delta_x', 0)
        delta_y = action.payload.get('delta_y', 0)
        
        state.canvas.pan_x += delta_x
        state.canvas.pan_y += delta_y
    
    async def _apply_create_project(self, action: Action, state: AppState):
        """Apply create project action"""
        from state_types import ProjectState
        
        state.project = ProjectState(
            id=action.payload.get('project_id'),
            name=action.payload.get('name'),
            path=action.payload.get('path'),
            metadata=action.payload.get('metadata'),
            settings=action.payload.get('metadata', {}).get('settings')
        )
    
    async def _apply_open_project(self, action: Action, state: AppState):
        """Apply open project action"""
        from state_types import ProjectState
        
        state.project = ProjectState(
            id=action.payload.get('project_id'),
            name=action.payload.get('name'),
            path=action.payload.get('path'),
            metadata=action.payload.get('metadata'),
            settings=action.payload.get('metadata', {}).get('settings')
        )
    
    async def _apply_save_project(self, action: Action, state: AppState):
        """Apply save project action"""
        if state.project:
            state.has_unsaved_changes = False
            state.last_saved = datetime.now()
    
    async def _apply_close_project(self, action: Action, state: AppState):
        """Apply close project action"""
        state.project = None
        state.components = ComponentTreeState()  # Clear components
        state.selection = SelectionState()  # Clear selection
        state.has_unsaved_changes = False
    
    async def _apply_update_project_meta(self, action: Action, state: AppState):
        """Apply update project metadata action"""
        if state.project:
            updates = action.payload.get('updates', {})
            if state.project.metadata is None:
                state.project.metadata = {}
            state.project.metadata.update(updates)
            
            # Handle special updates
            if 'has_unsaved_changes' in updates:
                state.has_unsaved_changes = updates['has_unsaved_changes']
            if 'last_saved' in updates:
                state.last_saved = updates['last_saved']
    
    def subscribe(
        self,
        path: str,
        callback: Callable[[Any, Any], None],
        filter_fn: Optional[Callable[[Any], bool]] = None
    ) -> Callable[[], None]:
        """
        Subscribe to state changes at specified path.
        Returns unsubscribe function for cleanup.
        """
        subscriber = Subscriber(
            id=str(time.time()),  # Simple ID for now
            path=path,
            callback=self._make_async_callback(callback),
            filter_fn=filter_fn
        )
        
        if path not in self._subscribers:
            self._subscribers[path] = []
        
        self._subscribers[path].append(subscriber)
        
        logger.debug(f"Added subscriber for path: {path}")
        
        # Return unsubscribe function
        def unsubscribe():
            if path in self._subscribers:
                self._subscribers[path] = [
                    s for s in self._subscribers[path] if s.id != subscriber.id
                ]
                if not self._subscribers[path]:
                    del self._subscribers[path]
            logger.debug(f"Removed subscriber for path: {path}")
        
        return unsubscribe
    
    def _make_async_callback(self, callback: Callable) -> Callable:
        """Convert sync callback to async if needed"""
        if asyncio.iscoroutinefunction(callback):
            return callback
        else:
            async def async_wrapper(old_value, new_value):
                callback(old_value, new_value)
            return async_wrapper
    
    async def _notify_subscribers(self, changes: List[Change]):
        """Notify all relevant subscribers of state changes"""
        # Group changes by path prefix for efficiency
        changes_by_path = defaultdict(list)
        for change in changes:
            parts = change.path.split('.')
            for i in range(1, len(parts) + 1):
                prefix = '.'.join(parts[:i])
                changes_by_path[prefix].append(change)
        
        # Notify subscribers
        tasks = []
        for path, path_changes in changes_by_path.items():
            if path in self._subscribers:
                old_value = self._get_old_value_from_changes(path_changes)
                new_value = self.get_state(path)
                
                for subscriber in self._subscribers[path]:
                    # Apply filter if present
                    if subscriber.filter_fn and not subscriber.filter_fn(new_value):
                        continue
                    
                    # Create notification task
                    task = asyncio.create_task(
                        self._notify_subscriber(subscriber, old_value, new_value)
                    )
                    tasks.append(task)
        
        # Wait for all notifications
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _notify_subscriber(self, subscriber: Subscriber, old_value: Any, new_value: Any):
        """Notify individual subscriber with error handling"""
        try:
            await subscriber.callback(old_value, new_value)
        except Exception as e:
            logger.error(f"Error in subscriber callback: {e}")
    
    def _get_old_value_from_changes(self, changes: List[Change]) -> Any:
        """Extract old value from changes"""
        if changes:
            return changes[0].old_value
        return None
    
    def get_state(self, path: str = "") -> Any:
        """
        Get state at specified path.
        Validates path to prevent traversal attacks.
        """
        if not path:
            return self._state
        
        # Validate path
        if '..' in path or path.startswith('/'):
            raise ValueError(f"Invalid path: {path}")
        
        # Navigate path
        current = self._state
        for part in path.split('.'):
            if hasattr(current, '__getitem__'):
                # Dict or list
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    try:
                        current = current[int(part)]
                    except (ValueError, IndexError):
                        return None
            else:
                # Object attribute
                current = getattr(current, part, None)
            
            if current is None:
                return None
        
        return current
    
    def add_middleware(self, middleware: 'Middleware'):
        """Add middleware to the pipeline"""
        self._middleware.append(middleware)
        logger.info(f"Added middleware: {middleware.__class__.__name__}")
    
    def remove_middleware(self, middleware: 'Middleware'):
        """Remove middleware from the pipeline"""
        if middleware in self._middleware:
            self._middleware.remove(middleware)
            logger.info(f"Removed middleware: {middleware.__class__.__name__}")
    
    def _deep_copy_state(self, state: AppState) -> AppState:
        """Create deep copy of state for immutable updates"""
        return AppState.from_dict(state.to_dict())
    
    def _diff_states(
        self,
        old_state: AppState,
        new_state: AppState,
        path: str = ""
    ) -> List[Change]:
        """
        Calculate differences between states efficiently.
        Returns list of changes for notification purposes.
        """
        changes = []
        
        # Use __dict__ for dataclasses
        old_dict = old_state.__dict__ if hasattr(old_state, '__dict__') else old_state
        new_dict = new_state.__dict__ if hasattr(new_state, '__dict__') else new_state
        
        if isinstance(old_dict, dict) and isinstance(new_dict, dict):
            # Compare dictionaries
            all_keys = set(old_dict.keys()) | set(new_dict.keys())
            
            for key in all_keys:
                child_path = f"{path}.{key}" if path else key
                
                if key not in old_dict:
                    # Added
                    changes.append(Change(
                        path=child_path,
                        type=ChangeType.CREATE,
                        new_value=new_dict[key]
                    ))
                elif key not in new_dict:
                    # Removed
                    changes.append(Change(
                        path=child_path,
                        type=ChangeType.DELETE,
                        old_value=old_dict[key]
                    ))
                elif old_dict[key] != new_dict[key]:
                    # Check if we need to recurse
                    if self._should_recurse(old_dict[key], new_dict[key]):
                        changes.extend(
                            self._diff_states(old_dict[key], new_dict[key], child_path)
                        )
                    else:
                        # Changed
                        changes.append(Change(
                            path=child_path,
                            type=ChangeType.UPDATE,
                            old_value=old_dict[key],
                            new_value=new_dict[key]
                        ))
        
        return changes
    
    def _should_recurse(self, old_value: Any, new_value: Any) -> bool:
        """Determine if we should recurse into nested objects"""
        return (
            isinstance(old_value, (dict, list)) and
            isinstance(new_value, (dict, list)) and
            type(old_value) == type(new_value)
        )
    
    def get_metrics(self) -> StateMetrics:
        """Get performance metrics"""
        return self._metrics
    
    def clear_metrics(self):
        """Clear performance metrics"""
        self._metrics = StateMetrics()


# Abstract base class for middleware
class Middleware:
    """Base class for state middleware"""
    
    async def before_action(
        self,
        action: Action,
        state: AppState
    ) -> Optional[Action]:
        """Process action before it's applied"""
        return action
    
    async def after_action(
        self,
        action: Action,
        state: AppState,
        changes: List[Change]
    ) -> None:
        """Process after action is applied"""
        pass