"""
History middleware for proper integration between StateManager and HistoryManager.
Handles automatic history recording with proper before/after state capture.
"""

import logging
from typing import List, Optional

from .state_manager import Middleware
from .history_manager import HistoryManager
from .state_types import Action, ActionType, AppState, Change

logger = logging.getLogger(__name__)


class HistoryMiddleware(Middleware):
    """
    Middleware that automatically records actions in history.
    Captures before/after states and manages undo/redo integration.
    """
    
    def __init__(self, history_manager: HistoryManager):
        self.history_manager = history_manager
        self._state_before_cache = {}  # action_id -> state_before
        logger.info("HistoryMiddleware initialized")
    
    async def before_action(
        self,
        action: Action,
        state: AppState
    ) -> Optional[Action]:
        """Capture state before action for history recording"""
        # Skip history actions to prevent recursion
        if action.type in [ActionType.UNDO, ActionType.REDO]:
            return action
        
        # Cache the current state for later history recording
        # We need a deep copy since state will be mutated
        self._state_before_cache[action.id] = self._deep_copy_state(state)
        
        logger.debug(f"Captured before state for action {action.type.name}")
        return action
    
    async def after_action(
        self,
        action: Action,
        state: AppState,
        changes: List[Change]
    ) -> None:
        """Record action in history after successful execution"""
        # Skip history actions to prevent recursion
        if action.type in [ActionType.UNDO, ActionType.REDO]:
            return
        
        # Skip if no changes occurred
        if not changes:
            logger.debug(f"Skipping history recording for {action.type.name} - no changes")
            return
        
        # Get cached before state
        state_before = self._state_before_cache.pop(action.id, None)
        if state_before is None:
            logger.warning(f"No before state cached for action {action.id}")
            return
        
        try:
            # Record in history
            await self.history_manager.record(action, state_before, changes)
            logger.debug(f"Recorded action {action.type.name} in history")
            
        except Exception as e:
            logger.error(f"Failed to record action in history: {e}")
    
    def _deep_copy_state(self, state: AppState) -> AppState:
        """Create deep copy of state for history storage"""
        # Use the state's serialization for deep copying
        return AppState.from_dict(state.to_dict())
    
    def cleanup_cache(self):
        """Clean up any stale cached states"""
        if self._state_before_cache:
            logger.warning(f"Cleaning up {len(self._state_before_cache)} stale state cache entries")
            self._state_before_cache.clear()


class PerformanceEnforcementMiddleware(Middleware):
    """
    Middleware that enforces performance requirements.
    Rejects or warns about actions that may exceed performance limits.
    """
    
    def __init__(
        self,
        max_update_time_ms: float = 16.0,
        max_undo_time_ms: float = 100.0,
        strict_mode: bool = False
    ):
        self.max_update_time = max_update_time_ms / 1000.0  # Convert to seconds
        self.max_undo_time = max_undo_time_ms / 1000.0
        self.strict_mode = strict_mode  # If True, reject slow actions
        
        # Performance estimation models
        self.action_complexity = {
            ActionType.ADD_COMPONENT: 1.0,
            ActionType.UPDATE_COMPONENT: 0.5,
            ActionType.DELETE_COMPONENT: 1.5,
            ActionType.MOVE_COMPONENT: 2.0,
            ActionType.DUPLICATE_COMPONENT: 3.0,
            ActionType.SELECT_COMPONENT: 0.1,
            ActionType.CLEAR_SELECTION: 0.2,
            ActionType.CHANGE_THEME: 0.3,
            ActionType.ZOOM_CANVAS: 0.1,
            ActionType.PAN_CANVAS: 0.1,
        }
        
        logger.info(f"PerformanceEnforcementMiddleware initialized (strict_mode: {strict_mode})")
    
    async def before_action(
        self,
        action: Action,
        state: AppState
    ) -> Optional[Action]:
        """Estimate and validate action performance before execution"""
        
        # Get complexity factor for this action type
        base_complexity = self.action_complexity.get(action.type, 1.0)
        
        # Adjust based on state size
        component_count = len(state.components.component_map)
        size_factor = 1.0 + (component_count / 1000.0)  # Scale with component count
        
        # Estimate processing time
        estimated_time = base_complexity * size_factor * 0.001  # Base 1ms per unit
        
        # Check for undo/redo specific limits
        max_time = self.max_undo_time if action.type in [ActionType.UNDO, ActionType.REDO] else self.max_update_time
        
        if estimated_time > max_time:
            warning_msg = (
                f"Action {action.type.name} estimated to take {estimated_time*1000:.1f}ms "
                f"(limit: {max_time*1000:.1f}ms, components: {component_count})"
            )
            
            if self.strict_mode:
                logger.error(f"REJECTED: {warning_msg}")
                return None  # Reject the action
            else:
                logger.warning(f"PERFORMANCE WARNING: {warning_msg}")
        
        # Add performance metadata to action
        action.metadata.update({
            'estimated_time_ms': estimated_time * 1000,
            'component_count': component_count,
            'complexity_factor': base_complexity * size_factor
        })
        
        return action
    
    async def after_action(
        self,
        action: Action,
        state: AppState,
        changes: List[Change]
    ) -> None:
        """Validate actual performance against estimates"""
        
        # Get actual timing from performance metadata (set by PerformanceMiddleware)
        actual_time = action.metadata.get('_actual_duration', 0)
        estimated_time = action.metadata.get('estimated_time_ms', 0) / 1000
        
        if actual_time and estimated_time:
            accuracy = abs(actual_time - estimated_time) / max(estimated_time, 0.001)
            
            if accuracy > 2.0:  # Off by more than 200%
                logger.warning(
                    f"Performance estimation inaccurate for {action.type.name}: "
                    f"estimated {estimated_time*1000:.1f}ms, actual {actual_time*1000:.1f}ms"
                )


class StateIntegrityMiddleware(Middleware):
    """
    Middleware that validates state integrity after each action.
    Ensures state remains consistent and catches corruption early.
    """
    
    def __init__(self, enable_deep_validation: bool = False):
        self.enable_deep_validation = enable_deep_validation
        self.validation_errors = []
        logger.info(f"StateIntegrityMiddleware initialized (deep_validation: {enable_deep_validation})")
    
    async def before_action(
        self,
        action: Action,
        state: AppState
    ) -> Optional[Action]:
        """No validation before action"""
        return action
    
    async def after_action(
        self,
        action: Action,
        state: AppState,
        changes: List[Change]
    ) -> None:
        """Validate state integrity after action execution"""
        
        errors = self._validate_state_integrity(state)
        
        if errors:
            self.validation_errors.extend(errors)
            logger.error(
                f"State integrity violations after {action.type.name}: {errors}"
            )
            
            # In strict mode, this could raise an exception
            # raise StateIntegrityError(f"State corruption detected: {errors}")
    
    def _validate_state_integrity(self, state: AppState) -> List[str]:
        """Validate state for consistency issues"""
        errors = []
        
        # Validate component tree integrity
        self._validate_component_tree(state.components, errors)
        
        # Validate selection integrity
        self._validate_selection_integrity(state.selection, state.components, errors)
        
        # Validate project integrity
        if state.project:
            self._validate_project_integrity(state.project, errors)
        
        # Deep validation if enabled
        if self.enable_deep_validation:
            self._deep_validate_state(state, errors)
        
        return errors
    
    def _validate_component_tree(self, components, errors):
        """Validate component tree structure"""
        # Check parent-child relationships
        for component_id in components.component_map:
            if component_id in components.parent_map:
                parent_id = components.parent_map[component_id]
                if parent_id not in components.component_map:
                    errors.append(f"Component {component_id} has invalid parent {parent_id}")
        
        # Check root components
        for root_id in components.root_components:
            if root_id not in components.component_map:
                errors.append(f"Root component {root_id} does not exist")
            if root_id in components.parent_map:
                errors.append(f"Root component {root_id} has a parent")
    
    def _validate_selection_integrity(self, selection, components, errors):
        """Validate selection state"""
        for selected_id in selection.selected_ids:
            if selected_id not in components.component_map:
                errors.append(f"Selected component {selected_id} does not exist")
        
        if selection.last_selected and selection.last_selected not in components.component_map:
            errors.append(f"Last selected component {selection.last_selected} does not exist")
    
    def _validate_project_integrity(self, project, errors):
        """Validate project state"""
        if not project.id:
            errors.append("Project missing required ID")
        
        if not project.name:
            errors.append("Project missing required name")
    
    def _deep_validate_state(self, state, errors):
        """Perform deep validation checks"""
        # Check for circular references
        visited = set()
        
        def check_component_cycles(component_id, path):
            if component_id in path:
                errors.append(f"Circular reference detected: {' -> '.join(path + [component_id])}")
                return
            
            if component_id in visited:
                return
            
            visited.add(component_id)
            
            # Check children (would need to implement component children tracking)
            # This would require additional state structure
        
        for root_id in state.components.root_components:
            check_component_cycles(root_id, [])
    
    def get_validation_summary(self) -> dict:
        """Get summary of validation issues"""
        return {
            'total_errors': len(self.validation_errors),
            'recent_errors': self.validation_errors[-10:],  # Last 10 errors
            'error_types': list(set(type(e).__name__ for e in self.validation_errors if hasattr(e, '__class__')))
        }