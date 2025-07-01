"""
History Manager implementation with undo/redo functionality.
Provides comprehensive action history with efficient memory management.
"""

import logging
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .state_types import (
    Action, ActionType, AppState, Change, ChangeType, 
    HistoryEntry, HistoryItem, HistoryItemType
)

logger = logging.getLogger(__name__)


class HistoryManager:
    """
    Manages undo/redo functionality with memory-efficient history storage.
    Supports batch operations and intelligent memory management.
    """
    
    def __init__(
        self,
        max_history: int = 1000,
        max_memory_mb: int = 100
    ):
        self.max_history = max_history
        self.max_memory = max_memory_mb * 1024 * 1024  # Convert to bytes
        self.entries: List[HistoryEntry] = []
        self.current_index = -1
        self.batch_stack: List[str] = []  # For grouping actions
        
        # Memory tracking
        self.current_memory = 0
        
        # Statistics
        self.stats = {
            'total_actions': 0,
            'undo_count': 0,
            'redo_count': 0,
            'memory_cleanups': 0
        }
        
        logger.info(f"HistoryManager initialized (max_history: {max_history}, max_memory: {max_memory_mb}MB)")
    
    async def record(
        self,
        action: Action,
        state_before: AppState,
        changes: List[Change]
    ) -> None:
        """
        Record action in history with memory optimization.
        Handles batch operations and memory limits.
        """
        # Skip recording internal history actions
        if action.type in [ActionType.UNDO, ActionType.REDO]:
            return
        
        # Handle batch operations
        if self._is_in_batch() and action.type != ActionType.BATCH_END:
            action.batch_id = self.batch_stack[-1]
            return
        
        # Clear future history if not at end
        if self.current_index < len(self.entries) - 1:
            removed_entries = self.entries[self.current_index + 1:]
            self.entries = self.entries[:self.current_index + 1]
            
            # Update memory tracking
            for entry in removed_entries:
                self.current_memory -= entry.memory_size
        
        # Create history entry
        entry = self._create_history_entry(action, state_before, changes)
        
        # Manage memory before adding new entry
        await self._manage_memory(entry.memory_size)
        
        # Add entry
        self.entries.append(entry)
        self.current_index += 1
        self.current_memory += entry.memory_size
        
        # Limit history size
        if len(self.entries) > self.max_history:
            removed = self.entries.pop(0)
            self.current_memory -= removed.memory_size
            self.current_index -= 1
        
        # Update statistics
        self.stats['total_actions'] += 1
        
        logger.debug(
            f"Recorded action in history: {action.type.name}",
            extra={
                "action_type": action.type.name,
                "history_size": len(self.entries),
                "memory_mb": self.current_memory / 1024 / 1024,
                "current_index": self.current_index
            }
        )
    
    def _create_history_entry(
        self,
        action: Action,
        state_before: AppState,
        changes: List[Change]
    ) -> HistoryEntry:
        """Create efficient history entry with minimal memory footprint"""
        
        # Calculate inverse changes for undo
        inverse_changes = self._calculate_inverse_changes(changes)
        
        # Create minimal state snapshot only if needed
        snapshot = None
        if self._should_create_snapshot(action):
            snapshot = self._create_minimal_snapshot(state_before, changes)
        
        entry = HistoryEntry(
            action=action,
            changes=changes,
            inverse_changes=inverse_changes,
            snapshot=snapshot,
            timestamp=datetime.now()
        )
        
        # Calculate memory size
        entry.memory_size = self._calculate_memory_size(entry)
        
        return entry
    
    def _calculate_inverse_changes(self, changes: List[Change]) -> List[Change]:
        """Calculate inverse changes for undo operations"""
        inverse_changes = []
        
        for change in changes:
            if change.type == ChangeType.CREATE:
                # To undo create, we delete
                inverse_changes.append(Change(
                    path=change.path,
                    type=ChangeType.DELETE,
                    old_value=change.new_value
                ))
            elif change.type == ChangeType.DELETE:
                # To undo delete, we create
                inverse_changes.append(Change(
                    path=change.path,
                    type=ChangeType.CREATE,
                    new_value=change.old_value
                ))
            elif change.type == ChangeType.UPDATE:
                # To undo update, we restore old value
                inverse_changes.append(Change(
                    path=change.path,
                    type=ChangeType.UPDATE,
                    old_value=change.new_value,
                    new_value=change.old_value
                ))
        
        return inverse_changes
    
    def _should_create_snapshot(self, action: Action) -> bool:
        """Determine if a full snapshot is needed for this action"""
        # Create snapshots for complex operations that can't be easily reversed
        snapshot_actions = {
            ActionType.CREATE_PROJECT,
            ActionType.OPEN_PROJECT,
            ActionType.BATCH_END
        }
        return action.type in snapshot_actions
    
    def _create_minimal_snapshot(self, state: AppState, changes: List[Change]) -> Dict[str, Any]:
        """Create minimal state snapshot for complex undo operations"""
        # Only snapshot the parts of state that were affected
        snapshot = {}
        
        affected_paths = set()
        for change in changes:
            parts = change.path.split('.')
            # Add top-level path
            if parts:
                affected_paths.add(parts[0])
        
        state_dict = state.to_dict()
        for path in affected_paths:
            if path in state_dict:
                snapshot[path] = state_dict[path]
        
        return snapshot
    
    def _calculate_memory_size(self, entry: HistoryEntry) -> int:
        """Estimate memory size of history entry"""
        try:
            # Rough estimation based on string representation
            action_size = sys.getsizeof(str(entry.action))
            changes_size = sum(sys.getsizeof(str(change)) for change in entry.changes)
            inverse_size = sum(sys.getsizeof(str(change)) for change in entry.inverse_changes)
            snapshot_size = sys.getsizeof(str(entry.snapshot)) if entry.snapshot else 0
            
            return action_size + changes_size + inverse_size + snapshot_size
        except:
            # Fallback to conservative estimate
            return 1024  # 1KB default
    
    async def _manage_memory(self, new_entry_size: int):
        """Manage memory by removing old entries if needed"""
        if self.current_memory + new_entry_size <= self.max_memory:
            return
        
        # Calculate how much memory we need to free
        target_memory = self.max_memory * 0.8  # Keep 20% buffer
        memory_to_free = (self.current_memory + new_entry_size) - target_memory
        
        removed_count = 0
        while self.entries and memory_to_free > 0:
            # Remove oldest entry
            removed = self.entries.pop(0)
            memory_to_free -= removed.memory_size
            self.current_memory -= removed.memory_size
            removed_count += 1
            
            # Adjust current index
            if self.current_index > 0:
                self.current_index -= 1
        
        if removed_count > 0:
            self.stats['memory_cleanups'] += 1
            logger.info(f"Memory cleanup: removed {removed_count} old history entries")
    
    async def undo(self) -> Optional[Action]:
        """
        Undo last action and return the undo action.
        Returns None if nothing to undo.
        """
        if not self.can_undo():
            logger.debug("Nothing to undo")
            return None
        
        entry = self.entries[self.current_index]
        self.current_index -= 1
        
        # Create undo action
        undo_action = Action(
            type=ActionType.UNDO,
            description=f"Undo: {entry.action.description}",
            changes=entry.inverse_changes,
            metadata={
                "original_action_id": entry.action.id,
                "original_action_type": entry.action.type.name
            }
        )
        
        self.stats['undo_count'] += 1
        
        logger.info(
            f"Undoing action: {entry.action.description}",
            extra={
                "original_action": entry.action.type.name,
                "changes_count": len(entry.inverse_changes),
                "new_index": self.current_index
            }
        )
        
        return undo_action
    
    async def redo(self) -> Optional[Action]:
        """
        Redo next action and return the redo action.
        Returns None if nothing to redo.
        """
        if not self.can_redo():
            logger.debug("Nothing to redo")
            return None
        
        self.current_index += 1
        entry = self.entries[self.current_index]
        
        # Create redo action
        redo_action = Action(
            type=ActionType.REDO,
            description=f"Redo: {entry.action.description}",
            changes=entry.changes,
            metadata={
                "original_action_id": entry.action.id,
                "original_action_type": entry.action.type.name
            }
        )
        
        self.stats['redo_count'] += 1
        
        logger.info(
            f"Redoing action: {entry.action.description}",
            extra={
                "original_action": entry.action.type.name,
                "changes_count": len(entry.changes),
                "new_index": self.current_index
            }
        )
        
        return redo_action
    
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """Check if redo is available"""
        return self.current_index < len(self.entries) - 1
    
    def get_history_timeline(
        self,
        start: int = 0,
        limit: int = 50
    ) -> List[HistoryItem]:
        """
        Get visual history timeline for UI display.
        Groups batch operations and provides navigation info.
        """
        items = []
        
        # Calculate range
        end = min(start + limit, len(self.entries))
        
        batch_groups = self._group_batch_actions()
        
        for i in range(start, end):
            entry = self.entries[i]
            
            # Check if this is part of a batch
            if entry.action.batch_id and entry.action.batch_id in batch_groups:
                batch_info = batch_groups[entry.action.batch_id]
                
                # Only show the first action in each batch
                if i == batch_info['start_index']:
                    items.append(HistoryItem(
                        index=i,
                        type=HistoryItemType.BATCH,
                        description=f"Batch: {batch_info['count']} actions",
                        timestamp=entry.timestamp,
                        is_current=i == self.current_index,
                        can_jump_to=True,
                        metadata={
                            "batch_id": entry.action.batch_id,
                            "batch_size": batch_info['count'],
                            "batch_actions": batch_info['action_types']
                        }
                    ))
            else:
                # Single action
                items.append(HistoryItem(
                    index=i,
                    type=HistoryItemType.SINGLE,
                    description=entry.action.description,
                    timestamp=entry.timestamp,
                    is_current=i == self.current_index,
                    can_jump_to=True,
                    action_type=entry.action.type.name,
                    changes_count=len(entry.changes)
                ))
        
        return items
    
    def _group_batch_actions(self) -> Dict[str, Dict[str, Any]]:
        """Group actions by batch ID for display"""
        batch_groups = {}
        
        for i, entry in enumerate(self.entries):
            if entry.action.batch_id:
                batch_id = entry.action.batch_id
                
                if batch_id not in batch_groups:
                    batch_groups[batch_id] = {
                        'start_index': i,
                        'count': 0,
                        'action_types': []
                    }
                
                batch_groups[batch_id]['count'] += 1
                batch_groups[batch_id]['action_types'].append(entry.action.type.name)
        
        return batch_groups
    
    def start_batch(self, description: str = "Batch Operation") -> str:
        """
        Start grouping actions into a batch.
        Supports nested batches.
        """
        batch_id = str(uuid4())
        self.batch_stack.append(batch_id)
        
        logger.debug(f"Started batch: {description} ({batch_id})")
        
        return batch_id
    
    def end_batch(self, batch_id: str) -> None:
        """End action grouping for specified batch"""
        if not self.batch_stack or self.batch_stack[-1] != batch_id:
            logger.warning(f"Invalid batch end: {batch_id}")
            return
        
        self.batch_stack.pop()
        
        logger.debug(f"Ended batch: {batch_id}")
    
    def _is_in_batch(self) -> bool:
        """Check if currently in a batch operation"""
        return len(self.batch_stack) > 0
    
    async def jump_to_history_point(self, target_index: int) -> List[Action]:
        """
        Jump to specific point in history.
        Returns list of actions needed to reach target state.
        """
        if target_index < -1 or target_index >= len(self.entries):
            raise ValueError(f"Invalid history index: {target_index}")
        
        actions = []
        
        if target_index > self.current_index:
            # Redo to target
            while self.current_index < target_index:
                action = await self.redo()
                if action:
                    actions.append(action)
        elif target_index < self.current_index:
            # Undo to target
            while self.current_index > target_index:
                action = await self.undo()
                if action:
                    actions.append(action)
        
        logger.info(f"Jumped to history point {target_index}")
        
        return actions
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get history statistics"""
        return {
            **self.stats,
            'current_index': self.current_index,
            'total_entries': len(self.entries),
            'memory_usage_mb': self.current_memory / 1024 / 1024,
            'memory_limit_mb': self.max_memory / 1024 / 1024,
            'can_undo': self.can_undo(),
            'can_redo': self.can_redo()
        }
    
    def clear_history(self):
        """Clear all history (use with caution)"""
        self.entries.clear()
        self.current_index = -1
        self.current_memory = 0
        self.batch_stack.clear()
        
        logger.info("History cleared")
    
    def compress_history(self, keep_recent: int = 100):
        """
        Compress old history entries to save memory.
        Keeps recent entries intact for normal undo/redo.
        """
        if len(self.entries) <= keep_recent:
            return
        
        # Keep recent entries
        recent_entries = self.entries[-keep_recent:]
        
        # Compress older entries (remove detailed snapshots)
        compressed_count = 0
        for entry in self.entries[:-keep_recent]:
            if entry.snapshot:
                entry.snapshot = None  # Remove snapshot to save memory
                compressed_count += 1
        
        # Recalculate memory usage
        self.current_memory = sum(
            self._calculate_memory_size(entry) for entry in self.entries
        )
        
        logger.info(f"Compressed {compressed_count} history entries")


class HistoryMiddleware:
    """Middleware integration for history manager"""
    
    def __init__(self, history_manager: HistoryManager):
        self.history_manager = history_manager
    
    async def before_action(self, action: Action, state: AppState) -> Optional[Action]:
        """Record state before action for history"""
        # Don't record history actions in history
        if action.type not in [ActionType.UNDO, ActionType.REDO]:
            # State will be recorded after action is applied
            pass
        return action
    
    async def after_action(self, action: Action, state: AppState, changes: List[Change]):
        """Record action in history after successful application"""
        if action.type not in [ActionType.UNDO, ActionType.REDO]:
            # We need the state before the action, but we only have it after
            # This would require the state manager to provide the before state
            # For now, we'll skip detailed history recording in middleware
            pass