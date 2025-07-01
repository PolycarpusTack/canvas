# State Management - Solution Design Document

## Overview
The State Management system handles application state persistence, undo/redo functionality, real-time synchronization, and maintains consistency across all UI components.

## Functional Requirements

### 1. State Persistence
- Save window size/position
- Save panel layouts
- Save user preferences
- Save project state
- Auto-save functionality

### 2. Undo/Redo System
- Track all user actions
- Unlimited undo/redo
- Visual history timeline
- Batch operations
- Selective undo

### 3. State Synchronization
- Keep UI components in sync
- Handle concurrent updates
- Resolve conflicts
- Real-time updates

### 4. Performance
- Efficient state updates
- Minimal re-renders
- State diffing
- Lazy loading
- Memory optimization

## Technical Specifications

### State Architecture

```python
@dataclass
class AppState:
    """Root application state"""
    # UI State
    window: WindowState
    panels: PanelState
    theme: ThemeState
    
    # Project State
    project: Optional[ProjectState]
    components: ComponentTreeState
    selection: SelectionState
    
    # Editor State
    canvas: CanvasState
    clipboard: ClipboardState
    history: HistoryState
    
    # User State
    preferences: UserPreferences
    recent_projects: List[ProjectMetadata]
    
@dataclass
class ComponentTreeState:
    """Component hierarchy state"""
    root_components: List[Component]
    component_map: Dict[str, Component]  # Fast lookup by ID
    parent_map: Dict[str, str]  # Child ID -> Parent ID
    dirty_components: Set[str]  # Modified components
    
@dataclass
class HistoryState:
    """Undo/redo state"""
    past: List[Action]
    future: List[Action]
    current_index: int
    max_history: int = 1000
    
@dataclass
class Action:
    """Represents a state change"""
    id: str
    type: ActionType
    timestamp: datetime
    description: str
    changes: List[Change]
    metadata: Dict[str, Any]
```

### State Manager Implementation

```python
class StateManager:
    """Central state management"""
    
    def __init__(self, storage: StateStorage):
        self.storage = storage
        self.state = self._initialize_state()
        self.subscribers: Dict[str, List[Callable]] = {}
        self.middleware: List[Middleware] = []
        
    def dispatch(self, action: Action) -> None:
        """Dispatch an action through middleware"""
        
        # Run through middleware
        for middleware in self.middleware:
            action = middleware.before_action(action, self.state)
            if action is None:
                return  # Action cancelled
        
        # Apply action
        old_state = self._deep_copy(self.state)
        new_state = self._apply_action(action, old_state)
        
        # Calculate changes
        changes = self._diff_states(old_state, new_state)
        
        # Update state
        self.state = new_state
        
        # Record in history
        self._record_history(action, changes)
        
        # Notify subscribers
        self._notify_subscribers(changes)
        
        # Run after middleware
        for middleware in self.middleware:
            middleware.after_action(action, self.state, changes)
    
    def subscribe(self, path: str, callback: Callable) -> Callable:
        """Subscribe to state changes at path"""
        
        if path not in self.subscribers:
            self.subscribers[path] = []
        
        self.subscribers[path].append(callback)
        
        # Return unsubscribe function
        def unsubscribe():
            self.subscribers[path].remove(callback)
        
        return unsubscribe
    
    def get_state(self, path: str = "") -> Any:
        """Get state at path"""
        
        if not path:
            return self.state
        
        # Navigate path (e.g., "project.components.0.style.width")
        current = self.state
        for part in path.split('.'):
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                current = current[int(part)]
            else:
                current = getattr(current, part)
        
        return current
```

### Action System

```python
class ActionType(Enum):
    # Component actions
    ADD_COMPONENT = "ADD_COMPONENT"
    UPDATE_COMPONENT = "UPDATE_COMPONENT"
    DELETE_COMPONENT = "DELETE_COMPONENT"
    MOVE_COMPONENT = "MOVE_COMPONENT"
    
    # Selection actions
    SELECT_COMPONENT = "SELECT_COMPONENT"
    DESELECT_COMPONENT = "DESELECT_COMPONENT"
    SELECT_ALL = "SELECT_ALL"
    
    # Project actions
    CREATE_PROJECT = "CREATE_PROJECT"
    OPEN_PROJECT = "OPEN_PROJECT"
    SAVE_PROJECT = "SAVE_PROJECT"
    CLOSE_PROJECT = "CLOSE_PROJECT"
    
    # UI actions
    RESIZE_PANEL = "RESIZE_PANEL"
    TOGGLE_PANEL = "TOGGLE_PANEL"
    CHANGE_THEME = "CHANGE_THEME"
    
    # Canvas actions
    ZOOM_CANVAS = "ZOOM_CANVAS"
    PAN_CANVAS = "PAN_CANVAS"
    TOGGLE_GRID = "TOGGLE_GRID"

class ActionCreators:
    """Factory functions for creating actions"""
    
    @staticmethod
    def add_component(component: Component, parent_id: Optional[str] = None) -> Action:
        return Action(
            id=str(uuid.uuid4()),
            type=ActionType.ADD_COMPONENT,
            timestamp=datetime.now(),
            description=f"Add {component.name}",
            changes=[
                Change(
                    path=f"components.{component.id}",
                    type=ChangeType.CREATE,
                    new_value=component
                )
            ],
            metadata={
                "component_id": component.id,
                "parent_id": parent_id
            }
        )
    
    @staticmethod
    def update_component_property(component_id: str, property_path: str, value: Any) -> Action:
        return Action(
            id=str(uuid.uuid4()),
            type=ActionType.UPDATE_COMPONENT,
            timestamp=datetime.now(),
            description=f"Update {property_path}",
            changes=[
                Change(
                    path=f"components.{component_id}.{property_path}",
                    type=ChangeType.UPDATE,
                    new_value=value
                )
            ],
            metadata={
                "component_id": component_id,
                "property": property_path
            }
        )
```

### Undo/Redo System

```python
class HistoryManager:
    """Manages undo/redo functionality"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.history: List[HistoryEntry] = []
        self.current_index = -1
        
    def record(self, action: Action, state_before: AppState, state_after: AppState):
        """Record an action in history"""
        
        # Remove any future history if we're not at the end
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # Create history entry
        entry = HistoryEntry(
            action=action,
            state_snapshot=self._create_snapshot(state_before),
            inverse_changes=self._calculate_inverse_changes(action.changes, state_before)
        )
        
        # Add to history
        self.history.append(entry)
        self.current_index += 1
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1
    
    def undo(self) -> Optional[List[Change]]:
        """Undo last action"""
        
        if not self.can_undo():
            return None
        
        entry = self.history[self.current_index]
        self.current_index -= 1
        
        return entry.inverse_changes
    
    def redo(self) -> Optional[Action]:
        """Redo next action"""
        
        if not self.can_redo():
            return None
        
        self.current_index += 1
        entry = self.history[self.current_index]
        
        return entry.action
    
    def get_history_timeline(self) -> List[HistoryItem]:
        """Get visual history timeline"""
        
        return [
            HistoryItem(
                index=i,
                action=entry.action,
                is_current=i == self.current_index,
                can_jump_to=True
            )
            for i, entry in enumerate(self.history)
        ]
```

### State Persistence

```python
class StateStorage:
    """Handles state persistence to disk"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    async def save_state(self, key: str, state: Any) -> bool:
        """Save state to disk"""
        
        try:
            file_path = self.storage_path / f"{key}.json"
            
            # Serialize state
            data = self._serialize_state(state)
            
            # Write atomically
            temp_file = file_path.with_suffix('.tmp')
            async with aiofiles.open(temp_file, 'w') as f:
                await f.write(json.dumps(data, indent=2))
            
            # Move to final location
            temp_file.replace(file_path)
            
            return True
            
        except Exception as e:
            print(f"Error saving state: {e}")
            return False
    
    async def load_state(self, key: str) -> Optional[Any]:
        """Load state from disk"""
        
        try:
            file_path = self.storage_path / f"{key}.json"
            
            if not file_path.exists():
                return None
            
            async with aiofiles.open(file_path, 'r') as f:
                data = json.loads(await f.read())
            
            return self._deserialize_state(data)
            
        except Exception as e:
            print(f"Error loading state: {e}")
            return None
    
    def _serialize_state(self, state: Any) -> Dict:
        """Convert state objects to JSON-serializable format"""
        
        if hasattr(state, 'to_dict'):
            return state.to_dict()
        elif isinstance(state, (list, tuple)):
            return [self._serialize_state(item) for item in state]
        elif isinstance(state, dict):
            return {k: self._serialize_state(v) for k, v in state.items()}
        else:
            return state
```

### State Synchronization

```python
class StateSynchronizer:
    """Keeps UI components synchronized with state"""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.component_bindings: Dict[str, List[UIBinding]] = {}
        
    def bind_component(self, ui_component: ft.Control, state_path: str, 
                       property_name: str, transformer: Optional[Callable] = None):
        """Bind UI component property to state"""
        
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
        
        # Subscribe to state changes
        self.state_manager.subscribe(state_path, 
            lambda value: self._update_component(binding, value))
        
        # Initial sync
        current_value = self.state_manager.get_state(state_path)
        self._update_component(binding, current_value)
    
    def _update_component(self, binding: UIBinding, value: Any):
        """Update UI component when state changes"""
        
        try:
            # Transform value if needed
            transformed_value = binding.transformer(value)
            
            # Update component property
            setattr(binding.component, binding.property_name, transformed_value)
            
            # Trigger UI update
            binding.component.update()
            
        except Exception as e:
            print(f"Error updating component: {e}")
```

### Middleware System

```python
class Middleware:
    """Base class for state middleware"""
    
    def before_action(self, action: Action, state: AppState) -> Optional[Action]:
        """Process action before it's applied"""
        return action
    
    def after_action(self, action: Action, state: AppState, changes: List[Change]):
        """Process after action is applied"""
        pass

class LoggingMiddleware(Middleware):
    """Logs all state changes"""
    
    def after_action(self, action: Action, state: AppState, changes: List[Change]):
        print(f"[{action.timestamp}] {action.type.value}: {action.description}")
        for change in changes:
            print(f"  - {change.path}: {change.type.value}")

class ValidationMiddleware(Middleware):
    """Validates actions before applying"""
    
    def before_action(self, action: Action, state: AppState) -> Optional[Action]:
        # Validate component actions
        if action.type == ActionType.ADD_COMPONENT:
            component_id = action.metadata.get("component_id")
            if component_id in state.components.component_map:
                print(f"Component {component_id} already exists")
                return None  # Cancel action
        
        return action

class AutoSaveMiddleware(Middleware):
    """Auto-saves state periodically"""
    
    def __init__(self, storage: StateStorage, interval: int = 300):
        self.storage = storage
        self.interval = interval
        self.last_save = datetime.now()
        
    def after_action(self, action: Action, state: AppState, changes: List[Change]):
        # Check if it's time to save
        if (datetime.now() - self.last_save).seconds >= self.interval:
            asyncio.create_task(self.storage.save_state("auto_save", state))
            self.last_save = datetime.now()
```

## State Flow Example

```python
# Initialize state management
storage = StateStorage(Path("~/.canvas-editor/state"))
state_manager = StateManager(storage)

# Add middleware
state_manager.add_middleware(ValidationMiddleware())
state_manager.add_middleware(LoggingMiddleware())
state_manager.add_middleware(AutoSaveMiddleware(storage))

# Create UI binding
synchronizer = StateSynchronizer(state_manager)
synchronizer.bind_component(
    ui_component=theme_selector,
    state_path="theme.mode",
    property_name="value"
)

# Dispatch action
action = ActionCreators.add_component(
    Component(name="Button", type="button")
)
state_manager.dispatch(action)

# Undo
state_manager.undo()

# Get current state
current_theme = state_manager.get_state("theme.mode")
```

## Performance Optimization

### 1. Immutable Updates
```python
def update_nested_state(state: Dict, path: List[str], value: Any) -> Dict:
    """Immutably update nested state"""
    
    if not path:
        return value
    
    key = path[0]
    remaining_path = path[1:]
    
    # Create new object
    new_state = state.copy()
    
    if remaining_path:
        new_state[key] = update_nested_state(state.get(key, {}), remaining_path, value)
    else:
        new_state[key] = value
    
    return new_state
```

### 2. Selective Updates
```python
def calculate_affected_paths(changes: List[Change]) -> Set[str]:
    """Calculate which state paths are affected"""
    
    affected = set()
    for change in changes:
        parts = change.path.split('.')
        # Add all parent paths
        for i in range(1, len(parts) + 1):
            affected.add('.'.join(parts[:i]))
    
    return affected
```

### 3. State Snapshots
```python
class SnapshotManager:
    """Efficient state snapshots for history"""
    
    def create_snapshot(self, state: AppState) -> StateSnapshot:
        # Only snapshot mutable parts
        return StateSnapshot(
            components=self._snapshot_components(state.components),
            timestamp=datetime.now()
        )
    
    def restore_snapshot(self, snapshot: StateSnapshot, current_state: AppState) -> AppState:
        # Restore only changed parts
        new_state = copy(current_state)
        new_state.components = self._restore_components(snapshot.components)
        return new_state
```

## Testing Requirements

### Unit Tests
- Action creators
- State reducers
- History operations
- State persistence

### Integration Tests
- Full state flow
- Middleware chain
- UI synchronization
- Undo/redo sequences

### Performance Tests
- Large state updates
- History with 1000+ actions
- Concurrent updates
- Memory usage

## Future Enhancements

1. **Time-travel debugging**: Visual state timeline
2. **State branching**: Multiple history branches
3. **Collaborative editing**: Conflict-free replicated data types (CRDTs)
4. **State compression**: Efficient storage of large states
5. **Remote state sync**: Cloud backup and sync
6. **State migrations**: Handle state structure changes
7. **Performance monitoring**: State update metrics
8. **Plugin system**: Third-party state extensions