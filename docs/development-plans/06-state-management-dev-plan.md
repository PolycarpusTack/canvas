# State Management - Development Plan

## Phase 1: Solution Design Analysis & Validation

### 1. Initial Understanding
- **Goal**: Implement comprehensive state management with persistence and undo/redo
- **Stack**: Python, asyncio, aiofiles, JSON/MessagePack serialization
- **Components**: StateManager, HistoryManager, StateSynchronizer, StateStorage
- **User Personas**: Developers needing reliable state management and history

### 2. Clarity Assessment
- **State Architecture**: High (3) - Well-defined state structure
- **Action System**: High (3) - Clear action/dispatch pattern
- **Undo/Redo**: High (3) - Comprehensive history management
- **Synchronization**: Medium (2) - UI binding complexity needs examples
- **Performance**: Medium (2) - Memory optimization strategies unclear
- **Overall Clarity**: High (3)

### 3. Technical Feasibility
- **Basic State Management**: Low risk (1) - Standard patterns
- **History Management**: Medium risk (2) - Memory constraints with large history
- **State Persistence**: Low risk (1) - JSON/async file operations
- **UI Synchronization**: Medium risk (2) - Flet binding complexity
- **Performance at Scale**: High risk (3) - Large state trees challenging

### 4. Security Assessment
- **State Validation**: Prevent invalid state mutations
- **Path Traversal**: Validate storage paths
- **Serialization**: Safe deserialization practices
- **Access Control**: State access permissions

### 5. Performance Requirements
- **State Updates**: < 16ms for UI responsiveness
- **History Operations**: < 100ms for undo/redo
- **Persistence**: < 1s for auto-save
- **Memory**: < 500MB for 1000 action history

**Recommendation**: PROCEEDING with backlog generation

---

## EPIC A: Core State Management

Implement fundamental state management system with actions, subscriptions, and middleware.

**Definition of Done:**
- ✓ State manager with dispatch system
- ✓ Action creators and reducers
- ✓ Subscription mechanism working
- ✓ Middleware pipeline implemented

**Business Value:** Foundation for all application state handling

**Risk Assessment:**
- State mutation bugs (High/3) - Enforce immutability
- Performance with deep nesting (Medium/2) - Efficient diffing
- Memory leaks from subscriptions (Medium/2) - Proper cleanup

**Cross-Functional Requirements:**
- Performance: < 16ms state update latency
- Security: Validate all state mutations
- Observability: State change logging
- Testing: 100% coverage for core logic

---

### USER STORY A-1: State Architecture Implementation

**ID & Title:** A-1: Build Core State Management System
**User Persona Narrative:** As a developer, I want a robust state management system so my application state is predictable
**Business Value:** High (3)
**Priority Score:** 5
**Story Points:** L

**Acceptance Criteria:**
```gherkin
Given I have a state manager
When I dispatch an action
Then the state is updated immutably
And all subscribers are notified
And the change is logged

Given I subscribe to a state path
When that path changes
Then my callback is invoked with the new value
And I can unsubscribe cleanly
```

**External Dependencies:** asyncio, dataclasses
**Technical Debt Considerations:** May need optimization for deep state trees
**Test Data Requirements:** Complex nested state structures

---

#### TASK A-1-T1: Create State Models and Types

**Goal:** Implement comprehensive state type system

**Token Budget:** 10,000 tokens

**Type Definitions:**
```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Union
import uuid

class ActionType(Enum):
    """
    CLAUDE.md #4.1: Explicit action types
    CLAUDE.md #1.4: Extensible for new actions
    """
    # Component actions
    ADD_COMPONENT = auto()
    UPDATE_COMPONENT = auto()
    DELETE_COMPONENT = auto()
    MOVE_COMPONENT = auto()
    DUPLICATE_COMPONENT = auto()
    
    # Selection actions
    SELECT_COMPONENT = auto()
    DESELECT_COMPONENT = auto()
    SELECT_ALL = auto()
    CLEAR_SELECTION = auto()
    
    # Project actions
    CREATE_PROJECT = auto()
    OPEN_PROJECT = auto()
    SAVE_PROJECT = auto()
    CLOSE_PROJECT = auto()
    UPDATE_PROJECT_META = auto()
    
    # UI actions
    RESIZE_PANEL = auto()
    TOGGLE_PANEL = auto()
    CHANGE_THEME = auto()
    UPDATE_PREFERENCES = auto()
    
    # Canvas actions
    ZOOM_CANVAS = auto()
    PAN_CANVAS = auto()
    TOGGLE_GRID = auto()
    TOGGLE_GUIDES = auto()
    
    # History actions (internal)
    UNDO = auto()
    REDO = auto()
    BATCH_START = auto()
    BATCH_END = auto()

@dataclass
class Change:
    """
    Represents a single state change
    CLAUDE.md #2.1.1: Validate change paths
    """
    path: str  # Dot-separated path like "components.button1.style.color"
    type: ChangeType
    old_value: Any = None
    new_value: Any = None
    
    def __post_init__(self):
        """Validate change on creation"""
        if not self.path:
            raise ValueError("Change path cannot be empty")
        
        # Validate path format
        if not all(part.replace('_', '').replace('-', '').isalnum() 
                  for part in self.path.split('.')):
            raise ValueError(f"Invalid path format: {self.path}")

@dataclass
class Action:
    """
    Represents a dispatchable action
    CLAUDE.md #12.1: Include metadata for logging
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: ActionType = field(default=ActionType.UPDATE_COMPONENT)
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    changes: List[Change] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    batch_id: Optional[str] = None
    
    def validate(self) -> ValidationResult:
        """
        CLAUDE.md #2.1.1: Comprehensive validation
        """
        errors = []
        
        # Validate required fields
        if not self.type:
            errors.append("Action type is required")
        
        # Validate payload based on action type
        validator = ActionValidators.get_validator(self.type)
        if validator:
            validation = validator(self.payload)
            errors.extend(validation.errors)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
```

**State Structure:**
```python
@dataclass
class AppState:
    """
    Root application state
    CLAUDE.md #1.2: Single source of truth
    """
    # UI State
    window: WindowState = field(default_factory=WindowState)
    panels: PanelState = field(default_factory=PanelState)
    theme: ThemeState = field(default_factory=ThemeState)
    
    # Project State
    project: Optional[ProjectState] = None
    components: ComponentTreeState = field(default_factory=ComponentTreeState)
    selection: SelectionState = field(default_factory=SelectionState)
    
    # Editor State
    canvas: CanvasState = field(default_factory=CanvasState)
    clipboard: ClipboardState = field(default_factory=ClipboardState)
    history: HistoryState = field(default_factory=HistoryState)
    
    # User State
    preferences: UserPreferences = field(default_factory=UserPreferences)
    recent_projects: List[ProjectMetadata] = field(default_factory=list)
    
    # Runtime State
    is_loading: bool = False
    has_unsaved_changes: bool = False
    last_saved: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for persistence"""
        return {
            'window': self.window.to_dict(),
            'panels': self.panels.to_dict(),
            'theme': self.theme.to_dict(),
            'project': self.project.to_dict() if self.project else None,
            'components': self.components.to_dict(),
            'preferences': self.preferences.to_dict(),
            'recent_projects': [p.to_dict() for p in self.recent_projects]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AppState:
        """Deserialize from dictionary"""
        return cls(
            window=WindowState.from_dict(data.get('window', {})),
            panels=PanelState.from_dict(data.get('panels', {})),
            theme=ThemeState.from_dict(data.get('theme', {})),
            project=ProjectState.from_dict(data['project']) if data.get('project') else None,
            components=ComponentTreeState.from_dict(data.get('components', {})),
            preferences=UserPreferences.from_dict(data.get('preferences', {})),
            recent_projects=[ProjectMetadata.from_dict(p) for p in data.get('recent_projects', [])]
        )

@dataclass
class ComponentTreeState:
    """
    CLAUDE.md #1.5: Optimize for fast lookups
    """
    root_components: List[str] = field(default_factory=list)  # IDs of root components
    component_map: Dict[str, Component] = field(default_factory=dict)
    parent_map: Dict[str, str] = field(default_factory=dict)  # child_id -> parent_id
    dirty_components: Set[str] = field(default_factory=set)
    
    # Performance optimization: spatial index for canvas
    spatial_index: Optional[SpatialIndex] = field(default=None, compare=False)
    
    def add_component(self, component: Component, parent_id: Optional[str] = None):
        """Add component with validation"""
        if component.id in self.component_map:
            raise ValueError(f"Component {component.id} already exists")
        
        self.component_map[component.id] = component
        
        if parent_id:
            if parent_id not in self.component_map:
                raise ValueError(f"Parent {parent_id} does not exist")
            self.parent_map[component.id] = parent_id
        else:
            self.root_components.append(component.id)
        
        self.dirty_components.add(component.id)
        
        # Update spatial index
        if self.spatial_index:
            self.spatial_index.insert(component.id, component.bounds)
```

**Deliverables:**
- Complete type system with all state models
- Serialization/deserialization methods
- Validation for all types
- Performance-optimized data structures

**Quality Gates:**
- ✓ All types have explicit type hints
- ✓ Immutable where possible
- ✓ Serialization round-trip works
- ✓ 100% test coverage

**Unblocks:** [A-1-T2, A-1-T3]
**Confidence Score:** High (3)

---

#### TASK A-1-T2: Implement State Manager Core

**Goal:** Create central state management with dispatch and subscriptions

**Token Budget:** 15,000 tokens

**State Manager Implementation:**
```python
class StateManager:
    """
    CLAUDE.md #6.1: Clear state ownership
    CLAUDE.md #2.1.4: Proper resource management
    CLAUDE.md #12.1: Comprehensive logging
    """
    
    def __init__(
        self,
        initial_state: Optional[AppState] = None,
        storage: Optional[StateStorage] = None
    ):
        self._state = initial_state or AppState()
        self._storage = storage
        self._subscribers: Dict[str, List[Subscriber]] = {}
        self._middleware: List[Middleware] = []
        self._lock = asyncio.Lock()
        self._dispatch_queue: asyncio.Queue[Action] = asyncio.Queue()
        self._running = False
        
        # Performance monitoring
        self._metrics = StateMetrics()
        
        # Start dispatch worker
        self._dispatch_task = None
        
    async def start(self):
        """Start the state manager"""
        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch_worker())
        
        # Load persisted state if available
        if self._storage:
            persisted = await self._storage.load_state("app_state")
            if persisted:
                self._state = AppState.from_dict(persisted)
                logger.info("Loaded persisted state")
    
    async def stop(self):
        """Stop the state manager cleanly"""
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
            await self._storage.save_state("app_state", self._state.to_dict())
    
    async def dispatch(self, action: Action) -> None:
        """
        Dispatch an action to update state
        CLAUDE.md #2.1.3: Async with proper error handling
        """
        # Validate action
        validation = action.validate()
        if not validation.is_valid:
            raise InvalidActionError(f"Invalid action: {validation.errors}")
        
        # Add to queue
        await self._dispatch_queue.put(action)
        
        # Log dispatch
        logger.debug(f"Dispatched {action.type.name}: {action.description}")
    
    async def _dispatch_worker(self):
        """
        Process actions from queue
        CLAUDE.md #2.1.2: Handle errors gracefully
        """
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
                
            except Exception as e:
                logger.error(f"Failed to process action {action.type}: {e}")
                raise
```

**Subscription System:**
```python
def subscribe(
    self,
    path: str,
    callback: Callable[[Any, Any], Awaitable[None]],
    filter_fn: Optional[Callable[[Any], bool]] = None
) -> Callable[[], None]:
    """
    Subscribe to state changes at path
    CLAUDE.md #2.1.4: Return cleanup function
    """
    subscriber = Subscriber(
        id=str(uuid.uuid4()),
        path=path,
        callback=callback,
        filter_fn=filter_fn
    )
    
    if path not in self._subscribers:
        self._subscribers[path] = []
    
    self._subscribers[path].append(subscriber)
    
    # Return unsubscribe function
    def unsubscribe():
        self._subscribers[path].remove(subscriber)
        if not self._subscribers[path]:
            del self._subscribers[path]
    
    return unsubscribe

async def _notify_subscribers(self, changes: List[Change]):
    """
    Notify all relevant subscribers
    CLAUDE.md #1.5: Optimize notification performance
    """
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
            value = self.get_state(path)
            
            for subscriber in self._subscribers[path]:
                # Apply filter if present
                if subscriber.filter_fn and not subscriber.filter_fn(value):
                    continue
                
                # Create notification task
                task = asyncio.create_task(
                    self._notify_subscriber(subscriber, value, path_changes)
                )
                tasks.append(task)
    
    # Wait for all notifications
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

def get_state(self, path: str = "") -> Any:
    """
    Get state at path
    CLAUDE.md #7.1: Validate path to prevent traversal
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
```

**State Diffing:**
```python
def _diff_states(
    self,
    old_state: AppState,
    new_state: AppState,
    path: str = ""
) -> List[Change]:
    """
    Calculate differences between states
    CLAUDE.md #1.5: Efficient deep comparison
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
```

**Unblocks:** [A-1-T3, A-2-T1]
**Confidence Score:** High (3)

---

#### TASK A-1-T3: Implement Middleware System

**Goal:** Create flexible middleware pipeline for cross-cutting concerns

**Token Budget:** 8,000 tokens

**Middleware Implementation:**
```python
class Middleware(ABC):
    """
    CLAUDE.md #1.4: Extensible middleware base
    """
    
    @abstractmethod
    async def before_action(
        self,
        action: Action,
        state: AppState
    ) -> Optional[Action]:
        """Process action before state update"""
        pass
    
    @abstractmethod
    async def after_action(
        self,
        action: Action,
        state: AppState,
        changes: List[Change]
    ) -> None:
        """Process after state update"""
        pass

class ValidationMiddleware(Middleware):
    """
    CLAUDE.md #2.1.1: Validate all state mutations
    """
    
    def __init__(self):
        self.validators = self._build_validators()
    
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
                    f"Action validation failed: {validation.errors}"
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
            ActionType.MOVE_COMPONENT: self._validate_move_component,
            # ... more validators
        }
    
    async def _validate_add_component(
        self,
        action: Action,
        state: AppState
    ) -> ValidationResult:
        """Validate component addition"""
        errors = []
        
        component_id = action.payload.get('component_id')
        parent_id = action.payload.get('parent_id')
        
        # Check duplicate
        if component_id in state.components.component_map:
            errors.append(f"Component {component_id} already exists")
        
        # Check parent exists
        if parent_id and parent_id not in state.components.component_map:
            errors.append(f"Parent {parent_id} does not exist")
        
        # Check nesting depth
        if parent_id:
            depth = self._calculate_depth(parent_id, state.components)
            if depth >= 10:
                errors.append("Maximum nesting depth exceeded")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

class LoggingMiddleware(Middleware):
    """
    CLAUDE.md #12.1: Structured logging for all actions
    """
    
    def __init__(self, log_level: str = "INFO"):
        self.log_level = getattr(logging, log_level)
    
    async def before_action(
        self,
        action: Action,
        state: AppState
    ) -> Optional[Action]:
        """Log action dispatch"""
        
        logger.log(
            self.log_level,
            f"Action dispatched",
            extra={
                "action_id": action.id,
                "action_type": action.type.name,
                "description": action.description,
                "user_id": action.user_id,
                "batch_id": action.batch_id,
                "timestamp": action.timestamp.isoformat()
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
            f"State updated",
            extra={
                "action_id": action.id,
                "changes_count": len(changes),
                "affected_paths": [c.path for c in changes[:10]],  # First 10
                "has_unsaved_changes": state.has_unsaved_changes
            }
        )

class PerformanceMiddleware(Middleware):
    """
    CLAUDE.md #1.5: Monitor and optimize performance
    """
    
    def __init__(self, slow_threshold_ms: float = 100):
        self.slow_threshold = slow_threshold_ms / 1000
        self.metrics = defaultdict(list)
    
    async def before_action(
        self,
        action: Action,
        state: AppState
    ) -> Optional[Action]:
        """Start timing"""
        action.metadata['_start_time'] = time.perf_counter()
        return action
    
    async def after_action(
        self,
        action: Action,
        state: AppState,
        changes: List[Change]
    ):
        """Record performance metrics"""
        
        start_time = action.metadata.get('_start_time', 0)
        duration = time.perf_counter() - start_time
        
        # Record metrics
        self.metrics[action.type].append(duration)
        
        # Log slow actions
        if duration > self.slow_threshold:
            logger.warning(
                f"Slow action detected",
                extra={
                    "action_type": action.type.name,
                    "duration_ms": duration * 1000,
                    "changes_count": len(changes),
                    "threshold_ms": self.slow_threshold * 1000
                }
            )
        
        # Clean up
        del action.metadata['_start_time']
```

**Unblocks:** [A-2-T1]
**Confidence Score:** High (3)

---

### USER STORY A-2: History and Undo/Redo

**ID & Title:** A-2: Implement Undo/Redo System
**User Persona Narrative:** As a designer, I want to undo/redo actions so I can experiment freely
**Business Value:** High (3)
**Priority Score:** 5
**Story Points:** L

**Acceptance Criteria:**
```gherkin
Given I perform several actions
When I press Ctrl+Z
Then the last action is undone
And the UI reflects the previous state
And I can redo with Ctrl+Y

Given I have a long history
When I view the history timeline
Then I see all my actions listed
And I can jump to any point
```

---

#### TASK A-2-T1: Implement History Manager

**Goal:** Create comprehensive history management with undo/redo

**Token Budget:** 12,000 tokens

**History Manager:**
```python
class HistoryManager:
    """
    CLAUDE.md #2.1.4: Memory-efficient history
    CLAUDE.md #1.2: DRY principle for history operations
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
        
        # Middleware integration
        self.middleware = HistoryMiddleware(self)
    
    def record(
        self,
        action: Action,
        state_before: AppState,
        changes: List[Change]
    ) -> None:
        """
        Record action in history
        CLAUDE.md #1.5: Optimize memory usage
        """
        # Skip if in batch
        if self.batch_stack and action.type not in [ActionType.BATCH_END]:
            action.batch_id = self.batch_stack[-1]
            return
        
        # Clear future if not at end
        if self.current_index < len(self.entries) - 1:
            # Remove future entries
            removed = self.entries[self.current_index + 1:]
            self.entries = self.entries[:self.current_index + 1]
            
            # Update memory
            for entry in removed:
                self.current_memory -= entry.memory_size
        
        # Create history entry
        entry = self._create_history_entry(action, state_before, changes)
        
        # Check memory limit
        while self.current_memory + entry.memory_size > self.max_memory and self.entries:
            # Remove oldest entries
            removed = self.entries.pop(0)
            self.current_memory -= removed.memory_size
            if self.current_index > 0:
                self.current_index -= 1
        
        # Add entry
        self.entries.append(entry)
        self.current_index += 1
        self.current_memory += entry.memory_size
        
        # Limit history size
        if len(self.entries) > self.max_history:
            removed = self.entries.pop(0)
            self.current_memory -= removed.memory_size
            self.current_index -= 1
        
        logger.debug(
            f"Recorded action in history",
            extra={
                "action_type": action.type.name,
                "history_size": len(self.entries),
                "memory_mb": self.current_memory / 1024 / 1024
            }
        )
    
    def _create_history_entry(
        self,
        action: Action,
        state_before: AppState,
        changes: List[Change]
    ) -> HistoryEntry:
        """Create efficient history entry"""
        
        # Calculate inverse changes for undo
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
        
        # Create minimal state snapshot
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
```

**Undo/Redo Operations:**
```python
async def undo(self) -> Optional[Action]:
    """
    Undo last action
    CLAUDE.md #2.1.2: Handle edge cases
    """
    if not self.can_undo():
        logger.info("Nothing to undo")
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
    
    logger.info(
        f"Undoing action",
        extra={
            "original_action": entry.action.description,
            "changes_count": len(entry.inverse_changes)
        }
    )
    
    return undo_action

async def redo(self) -> Optional[Action]:
    """
    Redo next action
    CLAUDE.md #2.1.2: Symmetric with undo
    """
    if not self.can_redo():
        logger.info("Nothing to redo")
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
    
    logger.info(
        f"Redoing action",
        extra={
            "original_action": entry.action.description,
            "changes_count": len(entry.changes)
        }
    )
    
    return redo_action

def get_history_timeline(
    self,
    start: int = 0,
    limit: int = 50
) -> List[HistoryItem]:
    """
    Get visual history timeline
    CLAUDE.md #9.1: Accessible history
    """
    items = []
    
    # Calculate range
    end = min(start + limit, len(self.entries))
    
    for i in range(start, end):
        entry = self.entries[i]
        
        # Group batch actions
        if entry.action.batch_id:
            # Check if this is the first in batch
            if i == 0 or self.entries[i-1].action.batch_id != entry.action.batch_id:
                # Count batch size
                batch_size = sum(
                    1 for e in self.entries[i:]
                    if e.action.batch_id == entry.action.batch_id
                )
                
                items.append(HistoryItem(
                    index=i,
                    type=HistoryItemType.BATCH,
                    description=f"Batch: {batch_size} actions",
                    timestamp=entry.timestamp,
                    is_current=i == self.current_index,
                    can_jump_to=True,
                    metadata={
                        "batch_id": entry.action.batch_id,
                        "batch_size": batch_size
                    }
                ))
        else:
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
```

**Batch Operations:**
```python
def start_batch(self, description: str = "Batch Operation") -> str:
    """
    Start grouping actions
    CLAUDE.md #1.3: Support nested batches
    """
    batch_id = str(uuid.uuid4())
    self.batch_stack.append(batch_id)
    
    logger.debug(f"Started batch: {description} ({batch_id})")
    
    return batch_id

def end_batch(self, batch_id: str) -> None:
    """End action grouping"""
    if not self.batch_stack or self.batch_stack[-1] != batch_id:
        logger.warning(f"Invalid batch end: {batch_id}")
        return
    
    self.batch_stack.pop()
    
    # Create batch summary action
    batch_action = Action(
        type=ActionType.BATCH_END,
        description=f"End batch: {batch_id}",
        batch_id=batch_id
    )
    
    # This will trigger recording of all batched actions
    logger.debug(f"Ended batch: {batch_id}")
```

**Unblocks:** [B-1-T1]
**Confidence Score:** Medium (2) - Memory optimization complexity

---

## EPIC B: State Persistence and Synchronization

Implement state persistence, auto-save, and UI synchronization.

**Definition of Done:**
- ✓ State persisted to disk
- ✓ Auto-save working reliably
- ✓ UI components stay synchronized
- ✓ Performance optimized

**Business Value:** Reliable state management and data persistence

---

### Technical Debt Management

```yaml
# State Management Debt Tracking
state_debt:
  items:
    - id: SM-001
      description: "Implement state compression for large history"
      impact: "Reduce memory usage by 50%"
      effort: "L"
      priority: 1
      
    - id: SM-002
      description: "Add state migration system"
      impact: "Handle state structure changes"
      effort: "M"
      priority: 2
      
    - id: SM-003
      description: "Optimize deep state diffing"
      impact: "Faster state updates"
      effort: "M"
      priority: 3
```

---

## Testing Strategy

### Unit Tests
```python
@pytest.mark.asyncio
async def test_state_manager_dispatch():
    """CLAUDE.md #6.2: Test core dispatch functionality"""
    manager = StateManager()
    await manager.start()
    
    # Subscribe to changes
    changes = []
    unsubscribe = manager.subscribe(
        "theme.mode",
        lambda old, new: changes.append((old, new))
    )
    
    # Dispatch action
    action = Action(
        type=ActionType.CHANGE_THEME,
        payload={"mode": "dark"}
    )
    await manager.dispatch(action)
    
    # Wait for processing
    await asyncio.sleep(0.1)
    
    # Verify
    assert manager.get_state("theme.mode") == "dark"
    assert len(changes) == 1
    
    # Cleanup
    unsubscribe()
    await manager.stop()

@pytest.mark.asyncio
async def test_history_undo_redo():
    """Test undo/redo functionality"""
    history = HistoryManager()
    
    # Record some actions
    for i in range(5):
        action = Action(
            type=ActionType.UPDATE_COMPONENT,
            description=f"Update {i}"
        )
        history.record(action, AppState(), [])
    
    # Test undo
    assert history.can_undo()
    undo_action = await history.undo()
    assert undo_action.type == ActionType.UNDO
    
    # Test redo
    assert history.can_redo()
    redo_action = await history.redo()
    assert redo_action.type == ActionType.REDO
```

---

## Performance Optimization

```python
class StateOptimizations:
    """CLAUDE.md #1.5: Performance optimizations"""
    
    @staticmethod
    def create_shallow_copy(state: AppState) -> AppState:
        """Create shallow copy for unchanged references"""
        return replace(state)  # dataclasses.replace
    
    @staticmethod
    def use_structural_sharing(
        old_state: Dict,
        updates: Dict[str, Any]
    ) -> Dict:
        """Reuse unchanged objects"""
        new_state = {}
        
        for key, value in old_state.items():
            if key in updates:
                new_state[key] = updates[key]
            else:
                new_state[key] = value  # Reuse reference
        
        # Add new keys
        for key, value in updates.items():
            if key not in new_state:
                new_state[key] = value
        
        return new_state
```

---

## Security Checklist

- [ ] Validate all action payloads
- [ ] Prevent state tampering
- [ ] Secure state persistence
- [ ] Validate file paths for storage
- [ ] Implement access control for actions
- [ ] Rate limit state updates

---

## State Management Best Practices

1. **Immutability**: Never mutate state directly
2. **Single Source of Truth**: All state in one place
3. **Predictable Updates**: Actions are the only way to change state
4. **Time Travel**: Full history for debugging
5. **Performance**: Optimize for common operations
6. **Type Safety**: Strong typing throughout