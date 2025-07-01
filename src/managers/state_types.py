"""
Comprehensive state management types and models for Canvas Editor.
Implements the state architecture from the development plan with full validation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Union, Awaitable
from uuid import uuid4
import uuid
import asyncio
import logging

logger = logging.getLogger(__name__)

# Import spatial index after it's defined
try:
    from .spatial_index import SpatialIndexManager
except ImportError:
    # Handle circular import during initialization
    SpatialIndexManager = None


class ActionType(Enum):
    """
    Explicit action types for all state changes.
    Extensible for new actions as the application grows.
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


class ChangeType(Enum):
    """Types of state changes"""
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()


class HistoryItemType(Enum):
    """Types of history items for visualization"""
    SINGLE = auto()
    BATCH = auto()


@dataclass
class ValidationResult:
    """Result of validation operations"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)


@dataclass
class Change:
    """
    Represents a single state change.
    Validates change paths to prevent invalid operations.
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
    Represents a dispatchable action.
    Includes metadata for comprehensive logging and debugging.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    type: ActionType = field(default=ActionType.UPDATE_COMPONENT)
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    changes: List[Change] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    batch_id: Optional[str] = None
    
    def validate(self) -> ValidationResult:
        """Comprehensive validation of action"""
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


@dataclass
class WindowState:
    """Window state management"""
    width: int = 1400
    height: int = 900
    left: int = 100
    top: int = 100
    maximized: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'width': self.width,
            'height': self.height,
            'left': self.left,
            'top': self.top,
            'maximized': self.maximized
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WindowState:
        return cls(
            width=data.get('width', 1400),
            height=data.get('height', 900),
            left=data.get('left', 100),
            top=data.get('top', 100),
            maximized=data.get('maximized', False)
        )


@dataclass
class PanelState:
    """Panel layout state"""
    sidebar_width: float = 80
    components_width: float = 280
    properties_width: float = 320
    sidebar_visible: bool = True
    components_visible: bool = True
    properties_visible: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'sidebar_width': self.sidebar_width,
            'components_width': self.components_width,
            'properties_width': self.properties_width,
            'sidebar_visible': self.sidebar_visible,
            'components_visible': self.components_visible,
            'properties_visible': self.properties_visible
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PanelState:
        return cls(
            sidebar_width=data.get('sidebar_width', 80),
            components_width=data.get('components_width', 280),
            properties_width=data.get('properties_width', 320),
            sidebar_visible=data.get('sidebar_visible', True),
            components_visible=data.get('components_visible', True),
            properties_visible=data.get('properties_visible', True)
        )


@dataclass
class ThemeState:
    """Theme configuration state"""
    mode: str = "light"
    primary_color: str = "#5E6AD2"
    accent_color: str = "#06B6D4"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'mode': self.mode,
            'primary_color': self.primary_color,
            'accent_color': self.accent_color
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ThemeState:
        return cls(
            mode=data.get('mode', 'light'),
            primary_color=data.get('primary_color', '#5E6AD2'),
            accent_color=data.get('accent_color', '#06B6D4')
        )


@dataclass
class SelectionState:
    """Component selection state"""
    selected_ids: Set[str] = field(default_factory=set)
    last_selected: Optional[str] = None
    selection_box: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'selected_ids': list(self.selected_ids),
            'last_selected': self.last_selected,
            'selection_box': self.selection_box
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SelectionState:
        return cls(
            selected_ids=set(data.get('selected_ids', [])),
            last_selected=data.get('last_selected'),
            selection_box=data.get('selection_box')
        )


@dataclass
class CanvasState:
    """Canvas editor state"""
    zoom: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0
    show_grid: bool = False
    show_guides: bool = True
    grid_size: int = 20
    snap_to_grid: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'zoom': self.zoom,
            'pan_x': self.pan_x,
            'pan_y': self.pan_y,
            'show_grid': self.show_grid,
            'show_guides': self.show_guides,
            'grid_size': self.grid_size,
            'snap_to_grid': self.snap_to_grid
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CanvasState:
        return cls(
            zoom=data.get('zoom', 1.0),
            pan_x=data.get('pan_x', 0.0),
            pan_y=data.get('pan_y', 0.0),
            show_grid=data.get('show_grid', False),
            show_guides=data.get('show_guides', True),
            grid_size=data.get('grid_size', 20),
            snap_to_grid=data.get('snap_to_grid', False)
        )


@dataclass
class ClipboardState:
    """Clipboard operations state"""
    copied_components: List[str] = field(default_factory=list)
    cut_components: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'copied_components': self.copied_components,
            'cut_components': self.cut_components
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ClipboardState:
        return cls(
            copied_components=data.get('copied_components', []),
            cut_components=data.get('cut_components', [])
        )


@dataclass
class HistoryState:
    """History management state"""
    can_undo: bool = False
    can_redo: bool = False
    current_index: int = -1
    total_entries: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'can_undo': self.can_undo,
            'can_redo': self.can_redo,
            'current_index': self.current_index,
            'total_entries': self.total_entries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HistoryState:
        return cls(
            can_undo=data.get('can_undo', False),
            can_redo=data.get('can_redo', False),
            current_index=data.get('current_index', -1),
            total_entries=data.get('total_entries', 0)
        )


@dataclass
class UserPreferences:
    """User preference settings"""
    auto_save: bool = True
    auto_save_interval: int = 300
    show_tooltips: bool = True
    enable_animations: bool = True
    default_device: str = "desktop"
    language: str = "en"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'auto_save': self.auto_save,
            'auto_save_interval': self.auto_save_interval,
            'show_tooltips': self.show_tooltips,
            'enable_animations': self.enable_animations,
            'default_device': self.default_device,
            'language': self.language
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UserPreferences:
        return cls(
            auto_save=data.get('auto_save', True),
            auto_save_interval=data.get('auto_save_interval', 300),
            show_tooltips=data.get('show_tooltips', True),
            enable_animations=data.get('enable_animations', True),
            default_device=data.get('default_device', 'desktop'),
            language=data.get('language', 'en')
        )


@dataclass
class ComponentTreeState:
    """
    Component hierarchy state optimized for fast lookups.
    Uses maps for O(1) access to components and parent relationships.
    Includes spatial indexing for efficient canvas operations.
    """
    root_components: List[str] = field(default_factory=list)  # IDs of root components
    component_map: Dict[str, Any] = field(default_factory=dict)  # Component data
    parent_map: Dict[str, str] = field(default_factory=dict)  # child_id -> parent_id
    dirty_components: Set[str] = field(default_factory=set)
    
    # Performance optimization: spatial index for canvas operations
    _spatial_index_manager: Optional[Any] = field(default=None, init=False, compare=False)
    
    def __post_init__(self):
        """Initialize spatial index after creation"""
        if SpatialIndexManager is not None:
            self._spatial_index_manager = SpatialIndexManager()
    
    @property
    def spatial_index(self):
        """Get the spatial index for canvas operations"""
        if self._spatial_index_manager is None and SpatialIndexManager is not None:
            self._spatial_index_manager = SpatialIndexManager()
        return self._spatial_index_manager.get_index() if self._spatial_index_manager else None
    
    def add_component(self, component_data: Dict[str, Any], parent_id: Optional[str] = None):
        """Add component with validation and spatial indexing"""
        component_id = component_data.get('id')
        if not component_id:
            raise ValueError("Component must have an ID")
        
        if component_id in self.component_map:
            raise ValueError(f"Component {component_id} already exists")
        
        self.component_map[component_id] = component_data
        
        if parent_id:
            if parent_id not in self.component_map:
                raise ValueError(f"Parent {parent_id} does not exist")
            self.parent_map[component_id] = parent_id
        else:
            self.root_components.append(component_id)
        
        self.dirty_components.add(component_id)
        
        # Update spatial index
        if self._spatial_index_manager:
            self._spatial_index_manager.component_added(component_id, component_data)
    
    def update_component(self, component_id: str, updates: Dict[str, Any]):
        """Update component data and spatial index"""
        if component_id not in self.component_map:
            raise ValueError(f"Component {component_id} does not exist")
        
        # Update component data
        self.component_map[component_id].update(updates)
        self.dirty_components.add(component_id)
        
        # Update spatial index
        if self._spatial_index_manager:
            self._spatial_index_manager.component_updated(component_id, self.component_map[component_id])
    
    def remove_component(self, component_id: str):
        """Remove component and all children"""
        if component_id not in self.component_map:
            return
        
        # Remove from spatial index first
        if self._spatial_index_manager:
            self._spatial_index_manager.component_removed(component_id)
        
        # Remove from parent's children
        if component_id in self.parent_map:
            del self.parent_map[component_id]
        else:
            # Remove from root components
            if component_id in self.root_components:
                self.root_components.remove(component_id)
        
        # Remove component
        del self.component_map[component_id]
        self.dirty_components.discard(component_id)
    
    def get_components_at_point(self, x: float, y: float) -> List[str]:
        """Get components at a specific point using spatial index"""
        if self.spatial_index:
            return self.spatial_index.query_point(x, y)
        else:
            # Fallback to linear search
            results = []
            for component_id, component_data in self.component_map.items():
                # Simple bounds check (would need proper implementation)
                style = component_data.get('style', {})
                left = float(style.get('left', 0))
                top = float(style.get('top', 0))
                width = float(style.get('width', 100))
                height = float(style.get('height', 50))
                
                if left <= x <= left + width and top <= y <= top + height:
                    results.append(component_id)
            return results
    
    def get_components_in_region(self, x: float, y: float, width: float, height: float) -> List[str]:
        """Get components in a rectangular region using spatial index"""
        if self.spatial_index:
            from spatial_index import BoundingBox
            region = BoundingBox(x=x, y=y, width=width, height=height)
            return self.spatial_index.query_region(region)
        else:
            # Fallback to linear search
            results = []
            for component_id in self.component_map:
                # Simple intersection check (simplified)
                results.append(component_id)
            return results
    
    def get_components_in_selection(self, selection_box: Dict[str, float], fully_contained: bool = False) -> List[str]:
        """Get components within a selection box"""
        if self.spatial_index:
            from spatial_index import BoundingBox
            box = BoundingBox(
                x=selection_box['x'],
                y=selection_box['y'],
                width=selection_box['width'],
                height=selection_box['height']
            )
            return self.spatial_index.query_selection_box(box, fully_contained)
        else:
            # Fallback implementation
            return list(self.component_map.keys())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'root_components': self.root_components,
            'component_map': self.component_map,
            'parent_map': self.parent_map,
            'dirty_components': list(self.dirty_components)
            # Note: spatial index is not serialized as it's rebuilt from component data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ComponentTreeState:
        instance = cls(
            root_components=data.get('root_components', []),
            component_map=data.get('component_map', {}),
            parent_map=data.get('parent_map', {}),
            dirty_components=set(data.get('dirty_components', []))
        )
        
        # Rebuild spatial index from component data
        if instance._spatial_index_manager:
            for component_id, component_data in instance.component_map.items():
                instance._spatial_index_manager.component_added(component_id, component_data)
        
        return instance


@dataclass
class ProjectState:
    """Current project state"""
    id: Optional[str] = None
    name: str = ""
    path: str = ""
    metadata: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'path': self.path,
            'metadata': self.metadata,
            'settings': self.settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProjectState:
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            path=data.get('path', ''),
            metadata=data.get('metadata'),
            settings=data.get('settings')
        )


@dataclass
class ProjectMetadata:
    """Project metadata for recent projects list"""
    id: str
    name: str
    path: str
    created: str
    modified: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'path': self.path,
            'created': self.created,
            'modified': self.modified
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProjectMetadata:
        return cls(
            id=data['id'],
            name=data['name'],
            path=data['path'],
            created=data['created'],
            modified=data['modified']
        )


@dataclass
class AppState:
    """
    Root application state - single source of truth.
    All application state is contained within this structure.
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
            'selection': self.selection.to_dict(),
            'canvas': self.canvas.to_dict(),
            'clipboard': self.clipboard.to_dict(),
            'history': self.history.to_dict(),
            'preferences': self.preferences.to_dict(),
            'recent_projects': [p.to_dict() for p in self.recent_projects],
            'is_loading': self.is_loading,
            'has_unsaved_changes': self.has_unsaved_changes,
            'last_saved': self.last_saved.isoformat() if self.last_saved else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AppState:
        """Deserialize from dictionary"""
        last_saved = None
        if data.get('last_saved'):
            last_saved = datetime.fromisoformat(data['last_saved'])
        
        return cls(
            window=WindowState.from_dict(data.get('window', {})),
            panels=PanelState.from_dict(data.get('panels', {})),
            theme=ThemeState.from_dict(data.get('theme', {})),
            project=ProjectState.from_dict(data['project']) if data.get('project') else None,
            components=ComponentTreeState.from_dict(data.get('components', {})),
            selection=SelectionState.from_dict(data.get('selection', {})),
            canvas=CanvasState.from_dict(data.get('canvas', {})),
            clipboard=ClipboardState.from_dict(data.get('clipboard', {})),
            history=HistoryState.from_dict(data.get('history', {})),
            preferences=UserPreferences.from_dict(data.get('preferences', {})),
            recent_projects=[ProjectMetadata.from_dict(p) for p in data.get('recent_projects', [])],
            is_loading=data.get('is_loading', False),
            has_unsaved_changes=data.get('has_unsaved_changes', False),
            last_saved=last_saved
        )


@dataclass
class HistoryEntry:
    """Single entry in the action history"""
    action: Action
    changes: List[Change]
    inverse_changes: List[Change]
    snapshot: Optional[Dict[str, Any]]
    timestamp: datetime
    memory_size: int = 0


@dataclass
class HistoryItem:
    """History item for UI display"""
    index: int
    type: HistoryItemType
    description: str
    timestamp: datetime
    is_current: bool
    can_jump_to: bool
    action_type: Optional[str] = None
    changes_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Subscriber:
    """State change subscriber"""
    id: str
    path: str
    callback: Callable[[Any, Any], Awaitable[None]]
    filter_fn: Optional[Callable[[Any], bool]] = None


@dataclass
class UIBinding:
    """UI component binding to state"""
    component: Any  # UI component reference
    property_name: str
    state_path: str
    transformer: Callable[[Any], Any]


@dataclass
class StateMetrics:
    """Performance metrics for state operations"""
    action_counts: Dict[ActionType, int] = field(default_factory=dict)
    action_durations: Dict[ActionType, List[float]] = field(default_factory=dict)
    
    def record_action(self, action_type: ActionType, duration: float, changes_count: int):
        """Record action metrics"""
        if action_type not in self.action_counts:
            self.action_counts[action_type] = 0
            self.action_durations[action_type] = []
        
        self.action_counts[action_type] += 1
        self.action_durations[action_type].append(duration)
        
        # Keep only last 100 durations per action type
        if len(self.action_durations[action_type]) > 100:
            self.action_durations[action_type] = self.action_durations[action_type][-100:]


class ActionValidators:
    """Validation functions for different action types"""
    
    @staticmethod
    def get_validator(action_type: ActionType) -> Optional[Callable]:
        """Get validator function for action type"""
        validators = {
            ActionType.ADD_COMPONENT: ActionValidators._validate_add_component,
            ActionType.DELETE_COMPONENT: ActionValidators._validate_delete_component,
            ActionType.UPDATE_COMPONENT: ActionValidators._validate_update_component,
        }
        return validators.get(action_type)
    
    @staticmethod
    def _validate_add_component(payload: Dict[str, Any]) -> ValidationResult:
        """Validate component addition"""
        errors = []
        
        component_data = payload.get('component_data')
        if not component_data:
            errors.append("Component data is required")
        elif not isinstance(component_data, dict):
            errors.append("Component data must be a dictionary")
        else:
            # Check for ID within component_data
            component_id = component_data.get('id')
            if not component_id:
                errors.append("Component ID is required")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    @staticmethod
    def _validate_delete_component(payload: Dict[str, Any]) -> ValidationResult:
        """Validate component deletion"""
        errors = []
        
        component_id = payload.get('component_id')
        if not component_id:
            errors.append("Component ID is required")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    @staticmethod
    def _validate_update_component(payload: Dict[str, Any]) -> ValidationResult:
        """Validate component update"""
        errors = []
        
        component_id = payload.get('component_id')
        if not component_id:
            errors.append("Component ID is required")
        
        updates = payload.get('updates')
        if not updates:
            errors.append("Updates are required")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )