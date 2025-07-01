# Drag & Drop System - Solution Design Document

## Overview
The Drag & Drop system enables users to drag components from the component panel and drop them onto the canvas to build their UI visually.

## Functional Requirements

### 1. Drag Initiation
- Make component items draggable
- Visual feedback on drag start
- Create ghost image of component
- Store component data for drop

### 2. Drag Over Canvas
- Highlight valid drop zones
- Show insertion indicators
- Snap to grid (optional)
- Preview component placement

### 3. Drop Handling
- Validate drop location
- Create component instance
- Insert at correct position
- Select newly dropped component

### 4. Drag Constraints
- Prevent invalid drops
- Respect container rules
- Handle nested components
- Support reordering

## Technical Specifications

### Component Data Structure

```python
# Data passed during drag operation
@dataclass
class DragData:
    component_type: str         # e.g., "button", "section"
    component_name: str         # Display name
    component_category: str     # e.g., "Layout", "Forms"
    default_props: Dict[str, Any]  # Initial properties
    constraints: Dict[str, Any]     # Drop constraints
```

### Drag States

```python
class DragState(Enum):
    IDLE = "idle"
    DRAGGING = "dragging"
    HOVERING = "hovering"
    INVALID = "invalid"
    DROPPED = "dropped"
```

### API Interface

```python
class DragDropManager:
    def start_drag(component_data: Dict[str, Any]) -> None
    def update_drag_position(x: float, y: float) -> None
    def get_drop_target(x: float, y: float) -> Optional[DropTarget]
    def validate_drop(target: DropTarget, data: DragData) -> bool
    def execute_drop(target: DropTarget, data: DragData) -> Component
    def cancel_drag() -> None
    
class DropTarget:
    container_id: str           # ID of container component
    index: int                  # Insertion index
    position: Tuple[float, float]  # Drop coordinates
    orientation: str            # "horizontal" or "vertical"
```

### Visual Feedback System

```python
class DragVisualizer:
    def show_drag_ghost(component_data: DragData) -> None
    def update_ghost_position(x: float, y: float) -> None
    def show_drop_indicator(target: DropTarget) -> None
    def highlight_drop_zone(container_id: str) -> None
    def show_invalid_drop() -> None
    def cleanup_visuals() -> None
```

## Implementation Guidelines

### 1. Flet Drag & Drop Implementation

```python
# Draggable component
class DraggableComponent(ft.Draggable):
    def __init__(self, component_data: Dict):
        self.component_data = component_data
        super().__init__(
            content=self._build_content(),
            data=json.dumps(component_data),
            on_drag_start=self._on_drag_start,
            on_drag_complete=self._on_drag_complete
        )
    
    def _on_drag_start(self, e):
        # Visual feedback
        self.opacity = 0.5
        self.update()

# Drop target
class CanvasDropZone(ft.DragTarget):
    def __init__(self):
        super().__init__(
            on_accept=self._on_drop,
            on_will_accept=self._on_will_accept,
            on_leave=self._on_leave
        )
    
    def _on_will_accept(self, e):
        # Validate and show feedback
        data = json.loads(e.data)
        if self._validate_drop(data):
            self.bgcolor = "blue100"
            return True
        return False
```

### 2. Drop Zone Detection

```python
def find_drop_target(x: float, y: float, component_tree: List[Component]):
    """Find the deepest valid drop target at coordinates"""
    
    # 1. Convert global coordinates to canvas-relative
    canvas_x, canvas_y = global_to_canvas_coords(x, y)
    
    # 2. Traverse component tree depth-first
    def check_component(comp: Component, px: float, py: float):
        # Check if point is inside component bounds
        if not point_in_bounds(px, py, comp.bounds):
            return None
            
        # Check children first (deepest match)
        for child in comp.children:
            target = check_component(child, px, py)
            if target:
                return target
        
        # Check if this component can accept drops
        if comp.can_accept_children:
            return DropTarget(
                container_id=comp.id,
                index=find_insertion_index(comp, px, py),
                position=(px, py),
                orientation=comp.layout_orientation
            )
        
        return None
    
    # 3. Find target starting from root
    for root_component in component_tree:
        target = check_component(root_component, canvas_x, canvas_y)
        if target:
            return target
    
    # 4. Default to canvas root
    return DropTarget(
        container_id="canvas_root",
        index=len(component_tree),
        position=(canvas_x, canvas_y),
        orientation="vertical"
    )
```

### 3. Component Constraints

```python
# Define which components can contain others
CONTAINER_COMPONENTS = {
    "section": {"allowed_children": "*"},
    "grid": {"allowed_children": "*"},
    "form": {"allowed_children": ["input", "select", "button", "text"]},
    "button": {"allowed_children": None},  # No children
    "input": {"allowed_children": None}
}

def validate_drop(parent_type: str, child_type: str) -> bool:
    constraints = CONTAINER_COMPONENTS.get(parent_type, {})
    allowed = constraints.get("allowed_children", None)
    
    if allowed is None:
        return False
    elif allowed == "*":
        return True
    elif isinstance(allowed, list):
        return child_type in allowed
    return False
```

### 4. Insertion Indicators

```python
class InsertionIndicator:
    """Visual indicator for where component will be inserted"""
    
    def show_between(before_component: Component, after_component: Component):
        # Calculate position between components
        if before_component.orientation == "vertical":
            y = (before_component.bottom + after_component.top) / 2
            show_horizontal_line(y)
        else:
            x = (before_component.right + after_component.left) / 2
            show_vertical_line(x)
    
    def show_inside_empty(container: Component):
        # Show dashed outline inside empty container
        show_dashed_rect(container.bounds, "Drop component here")
```

### 5. Grid Snapping

```python
def snap_to_grid(x: float, y: float, grid_size: int = 20) -> Tuple[float, float]:
    """Snap coordinates to nearest grid point"""
    snapped_x = round(x / grid_size) * grid_size
    snapped_y = round(y / grid_size) * grid_size
    return (snapped_x, snapped_y)

# Use in drop handling
if settings.snap_to_grid:
    drop_x, drop_y = snap_to_grid(drop_x, drop_y, settings.grid_size)
```

## Error Handling

- **Invalid drop target**: Show red outline, prevent drop
- **Circular nesting**: Detect and prevent component containing itself
- **Maximum depth**: Limit nesting depth to prevent UI issues
- **Drop outside canvas**: Cancel operation gracefully

## Performance Optimization

- Debounce drag move events
- Cache component bounds
- Use spatial indexing for large component trees
- Lazy render drop indicators

## Testing Requirements

### Unit Tests
- Drag data serialization
- Drop validation logic
- Coordinate transformation
- Grid snapping

### Integration Tests
- Full drag & drop flow
- Multi-level nesting
- Edge cases (drop on edges)
- Keyboard cancellation (ESC)

### UI Tests
- Visual feedback appears/disappears
- Drop zones highlight correctly
- Ghost image follows cursor
- Insertion indicators position correctly

## Accessibility

- Keyboard alternative for drag & drop
- Screen reader announcements
- Focus management after drop
- Clear visual indicators

## Future Enhancements

1. **Multi-select drag**: Drag multiple components
2. **Copy on drag**: Hold Alt to copy instead of move
3. **Drag from canvas**: Reorder existing components
4. **Smart guides**: Alignment guides while dragging
5. **Drag preview**: Live preview of component
6. **Undo/Redo**: Full drag operation undo
7. **Animation**: Smooth component insertion
8. **Templates**: Drag complete templates

## Example Usage

```python
# In ComponentPanel
component_item = DraggableComponent({
    "type": "button",
    "name": "Button",
    "category": "Forms",
    "default_props": {
        "text": "Click me",
        "variant": "primary"
    }
})

# In Canvas
canvas = CanvasDropZone()
canvas.on_drop = lambda data, pos: create_component(data, pos)

# Handle drop
def create_component(drag_data: Dict, position: Tuple[float, float]):
    component = ComponentService.create_from_type(
        drag_data["type"],
        position=position
    )
    canvas.add_component(component)
    canvas.select_component(component.id)
```