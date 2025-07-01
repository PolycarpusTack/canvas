"""
Middleware system for state management with validation, logging, and performance monitoring.
Implements cross-cutting concerns for the state management system.
"""

import asyncio
import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from .state_manager import Middleware
from .state_types import Action, ActionType, AppState, Change, ValidationResult

logger = logging.getLogger(__name__)


class ValidationMiddleware(Middleware):
    """
    Validates all state mutations to ensure data integrity.
    Prevents invalid actions from corrupting application state.
    """
    
    def __init__(self):
        self.validators = self._build_validators()
        logger.info("ValidationMiddleware initialized")
    
    async def before_action(
        self,
        action: Action,
        state: AppState
    ) -> Optional[Action]:
        """Validate action against current state"""
        
        validator = self.validators.get(action.type)
        if not validator:
            return action  # No validation needed
        
        try:
            validation = await validator(action, state)
            if not validation.is_valid:
                logger.warning(
                    f"Action validation failed",
                    extra={
                        "action_type": action.type.name,
                        "action_id": action.id,
                        "errors": validation.errors
                    }
                )
                return None  # Cancel action
            
            return action
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return None
    
    async def after_action(self, action: Action, state: AppState, changes: List[Change]):
        """No-op for validation middleware"""
        pass
    
    def _build_validators(self) -> Dict[ActionType, Callable]:
        """Build validators for each action type"""
        return {
            ActionType.ADD_COMPONENT: self._validate_add_component,
            ActionType.DELETE_COMPONENT: self._validate_delete_component,
            ActionType.UPDATE_COMPONENT: self._validate_update_component,
            ActionType.MOVE_COMPONENT: self._validate_move_component,
            ActionType.SELECT_COMPONENT: self._validate_select_component,
            ActionType.RESIZE_PANEL: self._validate_resize_panel,
            ActionType.ZOOM_CANVAS: self._validate_zoom_canvas,
        }
    
    async def _validate_add_component(
        self,
        action: Action,
        state: AppState
    ) -> ValidationResult:
        """Validate component addition"""
        errors = []
        
        component_data = action.payload.get('component_data', {})
        component_id = component_data.get('id')
        parent_id = action.payload.get('parent_id')
        
        
        # Check required fields
        if not component_id:
            errors.append("Component ID is required")
        
        # Check duplicate
        if component_id and component_id in state.components.component_map:
            errors.append(f"Component {component_id} already exists")
        
        # Check parent exists
        if parent_id and parent_id not in state.components.component_map:
            errors.append(f"Parent {parent_id} does not exist")
        
        # Check nesting depth
        if parent_id:
            depth = self._calculate_depth(parent_id, state.components)
            if depth >= 10:
                errors.append("Maximum nesting depth exceeded")
        
        # Validate component data structure
        if not isinstance(component_data, dict):
            errors.append("Component data must be a dictionary")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    async def _validate_delete_component(
        self,
        action: Action,
        state: AppState
    ) -> ValidationResult:
        """Validate component deletion"""
        errors = []
        
        component_id = action.payload.get('component_id')
        
        if not component_id:
            errors.append("Component ID is required")
        elif component_id not in state.components.component_map:
            errors.append(f"Component {component_id} does not exist")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    async def _validate_update_component(
        self,
        action: Action,
        state: AppState
    ) -> ValidationResult:
        """Validate component update"""
        errors = []
        
        component_id = action.payload.get('component_id')
        updates = action.payload.get('updates', {})
        
        if not component_id:
            errors.append("Component ID is required")
        elif component_id not in state.components.component_map:
            errors.append(f"Component {component_id} does not exist")
        
        if not isinstance(updates, dict):
            errors.append("Updates must be a dictionary")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    async def _validate_move_component(
        self,
        action: Action,
        state: AppState
    ) -> ValidationResult:
        """Validate component move operation"""
        errors = []
        
        component_id = action.payload.get('component_id')
        new_parent_id = action.payload.get('new_parent_id')
        
        if not component_id:
            errors.append("Component ID is required")
        elif component_id not in state.components.component_map:
            errors.append(f"Component {component_id} does not exist")
        
        # Check new parent exists (if specified)
        if new_parent_id and new_parent_id not in state.components.component_map:
            errors.append(f"New parent {new_parent_id} does not exist")
        
        # Prevent moving component into itself or its descendants
        if new_parent_id and self._is_descendant(component_id, new_parent_id, state.components):
            errors.append("Cannot move component into itself or its descendants")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    async def _validate_select_component(
        self,
        action: Action,
        state: AppState
    ) -> ValidationResult:
        """Validate component selection"""
        errors = []
        
        component_id = action.payload.get('component_id')
        
        if not component_id:
            errors.append("Component ID is required")
        elif component_id not in state.components.component_map:
            errors.append(f"Component {component_id} does not exist")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    async def _validate_resize_panel(
        self,
        action: Action,
        state: AppState
    ) -> ValidationResult:
        """Validate panel resize operation"""
        errors = []
        
        panel_name = action.payload.get('panel')
        new_width = action.payload.get('width')
        
        valid_panels = {'sidebar', 'components', 'properties'}
        if panel_name not in valid_panels:
            errors.append(f"Invalid panel name: {panel_name}")
        
        if not isinstance(new_width, (int, float)):
            errors.append("Panel width must be a number")
        elif new_width < 50:
            errors.append("Panel width cannot be less than 50 pixels")
        elif new_width > 1000:
            errors.append("Panel width cannot exceed 1000 pixels")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    async def _validate_zoom_canvas(
        self,
        action: Action,
        state: AppState
    ) -> ValidationResult:
        """Validate canvas zoom operation"""
        errors = []
        
        zoom_delta = action.payload.get('delta')
        
        if zoom_delta is None:
            errors.append("Zoom delta is required")
        elif not isinstance(zoom_delta, (int, float)):
            errors.append("Zoom delta must be a number")
        
        # Check resulting zoom level
        if zoom_delta is not None:
            new_zoom = state.canvas.zoom + zoom_delta
            if new_zoom < 0.1:
                errors.append("Zoom level cannot be less than 0.1")
            elif new_zoom > 5.0:
                errors.append("Zoom level cannot exceed 5.0")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def _calculate_depth(self, component_id: str, components) -> int:
        """Calculate nesting depth of component"""
        depth = 0
        current_id = component_id
        
        while current_id in components.parent_map:
            depth += 1
            current_id = components.parent_map[current_id]
            if depth > 20:  # Prevent infinite loops
                break
        
        return depth
    
    def _is_descendant(self, ancestor_id: str, descendant_id: str, components) -> bool:
        """Check if descendant_id is a descendant of ancestor_id"""
        current_id = descendant_id
        
        while current_id in components.parent_map:
            parent_id = components.parent_map[current_id]
            if parent_id == ancestor_id:
                return True
            current_id = parent_id
        
        return False


class LoggingMiddleware(Middleware):
    """
    Logs all state changes with structured logging.
    Provides comprehensive audit trail for debugging and monitoring.
    """
    
    def __init__(self, log_level: str = "INFO"):
        self.log_level = getattr(logging, log_level)
        logger.info("LoggingMiddleware initialized")
    
    async def before_action(
        self,
        action: Action,
        state: AppState
    ) -> Optional[Action]:
        """Log action dispatch"""
        
        logger.log(
            self.log_level,
            f"Action dispatched: {action.type.name}",
            extra={
                "action_id": action.id,
                "action_type": action.type.name,
                "description": action.description,
                "user_id": action.user_id,
                "batch_id": action.batch_id,
                "timestamp": action.timestamp.isoformat(),
                "payload_keys": list(action.payload.keys())
            }
        )
        
        return action
    
    async def after_action(
        self,
        action: Action,
        state: AppState,
        changes: List[Change]
    ):
        """Log state changes"""
        
        logger.log(
            self.log_level,
            f"State updated: {action.type.name}",
            extra={
                "action_id": action.id,
                "changes_count": len(changes),
                "affected_paths": [c.path for c in changes[:10]],  # First 10 paths
                "has_unsaved_changes": state.has_unsaved_changes,
                "component_count": len(state.components.component_map),
                "selected_count": len(state.selection.selected_ids)
            }
        )


class PerformanceMiddleware(Middleware):
    """
    Monitors and logs performance metrics for state operations.
    Helps identify performance bottlenecks and slow operations.
    """
    
    def __init__(self, slow_threshold_ms: float = 100):
        self.slow_threshold = slow_threshold_ms / 1000
        self.metrics = defaultdict(list)
        self.start_times = {}
        logger.info(f"PerformanceMiddleware initialized (slow threshold: {slow_threshold_ms}ms)")
    
    async def before_action(
        self,
        action: Action,
        state: AppState
    ) -> Optional[Action]:
        """Start timing action"""
        self.start_times[action.id] = time.perf_counter()
        return action
    
    async def after_action(
        self,
        action: Action,
        state: AppState,
        changes: List[Change]
    ):
        """Record performance metrics"""
        
        start_time = self.start_times.pop(action.id, time.perf_counter())
        duration = time.perf_counter() - start_time
        
        # Store actual duration for other middleware
        action.metadata['_actual_duration'] = duration
        
        # Record metrics
        self.metrics[action.type].append(duration)
        
        # Keep only last 100 measurements per action type
        if len(self.metrics[action.type]) > 100:
            self.metrics[action.type] = self.metrics[action.type][-100:]
        
        # Log slow actions
        if duration > self.slow_threshold:
            logger.warning(
                f"Slow action detected: {action.type.name}",
                extra={
                    "action_type": action.type.name,
                    "action_id": action.id,
                    "duration_ms": duration * 1000,
                    "changes_count": len(changes),
                    "threshold_ms": self.slow_threshold * 1000,
                    "component_count": len(state.components.component_map)
                }
            )
        
        # Log periodic performance summary
        total_actions = sum(len(measurements) for measurements in self.metrics.values())
        if total_actions % 100 == 0:
            self._log_performance_summary()
    
    def _log_performance_summary(self):
        """Log performance summary"""
        summary = {}
        
        for action_type, durations in self.metrics.items():
            if durations:
                avg_duration = sum(durations) / len(durations)
                max_duration = max(durations)
                summary[action_type.name] = {
                    "count": len(durations),
                    "avg_ms": avg_duration * 1000,
                    "max_ms": max_duration * 1000
                }
        
        logger.info(
            "Performance summary",
            extra={
                "summary": summary,
                "total_actions": sum(len(d) for d in self.metrics.values())
            }
        )
    
    def get_metrics(self) -> Dict[ActionType, List[float]]:
        """Get current performance metrics"""
        return dict(self.metrics)
    
    def clear_metrics(self):
        """Clear performance metrics"""
        self.metrics.clear()


class AutoSaveMiddleware(Middleware):
    """
    Automatically saves state periodically and after significant changes.
    Ensures data persistence without manual intervention.
    """
    
    def __init__(self, storage, interval: int = 300, significant_actions: Optional[Set[ActionType]] = None):
        self.storage = storage
        self.interval = interval
        self.last_save = datetime.now()
        self.significant_actions = significant_actions or {
            ActionType.ADD_COMPONENT,
            ActionType.DELETE_COMPONENT,
            ActionType.UPDATE_COMPONENT,
            ActionType.CREATE_PROJECT,
            ActionType.SAVE_PROJECT
        }
        self.pending_save = False
        logger.info(f"AutoSaveMiddleware initialized (interval: {interval}s)")
    
    async def before_action(
        self,
        action: Action,
        state: AppState
    ) -> Optional[Action]:
        """No processing before action"""
        return action
    
    async def after_action(
        self,
        action: Action,
        state: AppState,
        changes: List[Change]
    ):
        """Handle auto-save logic"""
        
        should_save = False
        
        # Save immediately for significant actions
        if action.type in self.significant_actions:
            should_save = True
            logger.debug(f"Immediate save triggered by {action.type.name}")
        
        # Save based on time interval
        time_since_save = (datetime.now() - self.last_save).total_seconds()
        if time_since_save >= self.interval and state.has_unsaved_changes:
            should_save = True
            logger.debug(f"Interval save triggered ({time_since_save:.1f}s since last save)")
        
        if should_save and not self.pending_save:
            self.pending_save = True
            asyncio.create_task(self._save_state(state))
    
    async def _save_state(self, state: AppState):
        """Save state with error handling"""
        try:
            success = await self.storage.save_state("app_state", state.to_dict())
            if success:
                self.last_save = datetime.now()
                logger.debug("Auto-save completed successfully")
            else:
                logger.error("Auto-save failed")
        except Exception as e:
            logger.error(f"Auto-save error: {e}")
        finally:
            self.pending_save = False


class SecurityMiddleware(Middleware):
    """
    Enforces security policies and prevents malicious actions.
    Validates action sources and prevents unauthorized operations.
    """
    
    def __init__(self, max_actions_per_second: int = 100):
        self.max_actions_per_second = max_actions_per_second
        self.action_timestamps = defaultdict(list)
        logger.info("SecurityMiddleware initialized")
    
    async def before_action(
        self,
        action: Action,
        state: AppState
    ) -> Optional[Action]:
        """Apply security checks"""
        
        # Rate limiting
        if not self._check_rate_limit(action):
            logger.warning(
                f"Rate limit exceeded for action {action.type.name}",
                extra={
                    "action_id": action.id,
                    "user_id": action.user_id
                }
            )
            return None
        
        # Validate action integrity
        if not self._validate_action_integrity(action):
            logger.warning(
                f"Action integrity check failed for {action.type.name}",
                extra={
                    "action_id": action.id,
                    "user_id": action.user_id
                }
            )
            return None
        
        return action
    
    async def after_action(
        self,
        action: Action,
        state: AppState,
        changes: List[Change]
    ):
        """Log security events"""
        
        # Log privileged actions
        privileged_actions = {
            ActionType.DELETE_COMPONENT,
            ActionType.CREATE_PROJECT,
            ActionType.SAVE_PROJECT
        }
        
        if action.type in privileged_actions:
            logger.info(
                f"Privileged action executed: {action.type.name}",
                extra={
                    "action_id": action.id,
                    "user_id": action.user_id,
                    "changes_count": len(changes)
                }
            )
    
    def _check_rate_limit(self, action: Action) -> bool:
        """Check if action exceeds rate limit"""
        now = time.time()
        user_id = action.user_id or "anonymous"
        
        # Clean old timestamps
        cutoff = now - 1.0  # 1 second window
        self.action_timestamps[user_id] = [
            ts for ts in self.action_timestamps[user_id] if ts > cutoff
        ]
        
        # Check rate limit
        if len(self.action_timestamps[user_id]) >= self.max_actions_per_second:
            return False
        
        # Record this action
        self.action_timestamps[user_id].append(now)
        return True
    
    def _validate_action_integrity(self, action: Action) -> bool:
        """Validate action has not been tampered with"""
        # Basic integrity checks
        
        # Check required fields
        if not action.id or not action.type or not action.timestamp:
            return False
        
        # Check timestamp is reasonable (not too old or in future)
        age = datetime.now() - action.timestamp
        if age.total_seconds() > 300 or age.total_seconds() < -60:
            return False
        
        # Check payload structure
        if not isinstance(action.payload, dict):
            return False
        
        return True