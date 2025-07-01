# Canvas Rendering - Solution Design Document

## Overview
The Canvas Rendering system is responsible for displaying components visually, handling selection, showing visual guides, and managing the real-time preview of the user's design.

## Functional Requirements

### 1. Component Rendering
- Display components with proper styling
- Handle nested component hierarchies
- Apply responsive breakpoints
- Show component boundaries when selected

### 2. Visual Guides
- Grid overlay (optional)
- Ruler guides
- Alignment guides
- Spacing indicators
- Component dimensions

### 3. Selection System
- Click to select components
- Multi-select with Ctrl/Cmd
- Selection box with handles
- Parent/child navigation

### 4. Interactive Features
- Hover states
- Resize handles
- Inline text editing
- Context menus
- Component toolbar

### 5. Preview Modes
- Design mode (with guides)
- Preview mode (clean)
- Device preview (responsive)
- Dark mode toggle

## Technical Specifications

### Canvas Architecture

```python
@dataclass
class CanvasState:
    components: List[Component]     # Component tree
    selected_ids: Set[str]         # Selected component IDs
    hovered_id: Optional[str]      # Hovered component ID
    zoom_level: float              # Canvas zoom (0.25 to 4.0)
    viewport: Rectangle            # Visible area
    guides: List[Guide]           # Ruler guides
    show_grid: bool               # Grid visibility
    grid_size: int                # Grid spacing
    device_frame: Optional[str]    # Device preview frame
    
@dataclass
class Rectangle:
    x: float
    y: float
    width: float
    height: float
    
@dataclass
class Guide:
    id: str
    orientation: str  # "horizontal" or "vertical"
    position: float
    locked: bool
```

### Rendering Pipeline

```python
class CanvasRenderer:
    def render(self, state: CanvasState) -> ft.Control:
        """Main rendering pipeline"""
        
        # 1. Create canvas container
        canvas = ft.Stack([
            # Background layers
            self._render_background(state),
            self._render_grid(state),
            self._render_guides(state),
            
            # Component layer
            self._render_components(state),
            
            # Overlay layers
            self._render_selection(state),
            self._render_hover(state),
            self._render_dimensions(state),
            self._render_toolbar(state),
            
            # Device frame (if active)
            self._render_device_frame(state)
        ])
        
        return ft.Container(
            content=canvas,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            on_hover=self._handle_hover,
            on_click=self._handle_click,
            on_pan_update=self._handle_pan,
            on_scroll=self._handle_zoom
        )
```

### Component Rendering

```python
def render_component(component: Component, state: CanvasState) -> ft.Control:
    """Render a single component with its children"""
    
    # 1. Create base container
    container = ft.Container(
        key=component.id,
        width=_calculate_width(component),
        height=_calculate_height(component),
        padding=_parse_padding(component.style.padding),
        margin=_parse_margin(component.style.margin),
        bgcolor=component.style.background_color,
        border_radius=_parse_border_radius(component.style.border_radius),
        border=_parse_border(component.style.border),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS
    )
    
    # 2. Apply positioning
    if component.style.position == "absolute":
        container.left = _parse_unit(component.style.left)
        container.top = _parse_unit(component.style.top)
    
    # 3. Add content based on component type
    if component.type == "text":
        content = ft.Text(
            component.content or "Text",
            size=_parse_unit(component.style.font_size, 16),
            color=component.style.color,
            weight=_get_font_weight(component.style.font_weight)
        )
    elif component.type == "image":
        content = ft.Image(
            src=component.attributes.get("src", ""),
            fit=ft.ImageFit.CONTAIN
        )
    elif component.type == "button":
        content = ft.ElevatedButton(
            text=component.content or "Button",
            style=_get_button_style(component)
        )
    else:
        # Container type - render children
        content = _render_layout(component, state)
    
    container.content = content
    
    # 4. Add interaction handlers
    container.on_hover = lambda e: _handle_component_hover(e, component.id)
    container.on_click = lambda e: _handle_component_click(e, component.id)
    
    # 5. Apply selection/hover effects
    if component.id in state.selected_ids:
        container = _apply_selection_effect(container)
    elif component.id == state.hovered_id:
        container = _apply_hover_effect(container)
    
    return container
```

### Layout Rendering

```python
def _render_layout(component: Component, state: CanvasState) -> ft.Control:
    """Render component children with proper layout"""
    
    if not component.children:
        return _render_empty_container()
    
    children = [render_component(child, state) for child in component.children]
    
    if component.style.display == "flex":
        return ft.Row(
            controls=children,
            alignment=_get_flex_alignment(component.style.justify_content),
            vertical_alignment=_get_flex_alignment(component.style.align_items),
            spacing=_parse_unit(component.style.gap, 0),
            wrap=component.style.flex_wrap == "wrap"
        ) if component.style.flex_direction in ["row", None] else ft.Column(
            controls=children,
            horizontal_alignment=_get_flex_alignment(component.style.align_items),
            alignment=_get_flex_alignment(component.style.justify_content),
            spacing=_parse_unit(component.style.gap, 0)
        )
    elif component.style.display == "grid":
        # Simplified grid (Flet doesn't have native CSS Grid)
        return ft.GridView(
            controls=children,
            runs_count=_parse_grid_columns(component.style.grid_template_columns),
            spacing=_parse_unit(component.style.gap, 0)
        )
    else:
        # Default block layout
        return ft.Column(controls=children, spacing=0)
```

### Selection Rendering

```python
class SelectionRenderer:
    """Renders selection indicators and handles"""
    
    def render_selection(self, component: Component, bounds: Rectangle) -> ft.Control:
        return ft.Stack([
            # Selection outline
            ft.Container(
                left=bounds.x - 1,
                top=bounds.y - 1,
                width=bounds.width + 2,
                height=bounds.height + 2,
                border=ft.border.all(2, "#5E6AD2"),
                bgcolor=None,
                disabled=True  # Click-through
            ),
            
            # Resize handles
            self._create_handle(bounds.x - 4, bounds.y - 4, "nw"),
            self._create_handle(bounds.x + bounds.width/2 - 4, bounds.y - 4, "n"),
            self._create_handle(bounds.x + bounds.width - 4, bounds.y - 4, "ne"),
            self._create_handle(bounds.x + bounds.width - 4, bounds.y + bounds.height/2 - 4, "e"),
            self._create_handle(bounds.x + bounds.width - 4, bounds.y + bounds.height - 4, "se"),
            self._create_handle(bounds.x + bounds.width/2 - 4, bounds.y + bounds.height - 4, "s"),
            self._create_handle(bounds.x - 4, bounds.y + bounds.height - 4, "sw"),
            self._create_handle(bounds.x - 4, bounds.y + bounds.height/2 - 4, "w"),
            
            # Dimension labels
            ft.Container(
                left=bounds.x,
                top=bounds.y - 20,
                content=ft.Text(f"{int(bounds.width)} × {int(bounds.height)}", size=10),
                bgcolor="black",
                padding=ft.padding.symmetric(4, 2),
                border_radius=2
            )
        ])
    
    def _create_handle(self, x: float, y: float, position: str) -> ft.Container:
        return ft.Container(
            left=x,
            top=y,
            width=8,
            height=8,
            bgcolor="white",
            border=ft.border.all(1, "#5E6AD2"),
            border_radius=1,
            on_hover=lambda e: self._set_resize_cursor(position),
            on_pan_start=lambda e: self._start_resize(position, e),
            on_pan_update=lambda e: self._update_resize(e),
            on_pan_end=lambda e: self._end_resize(e)
        )
```

### Visual Guides

```python
class GuideRenderer:
    """Renders grid, rulers, and alignment guides"""
    
    def render_grid(self, width: float, height: float, size: int = 20) -> ft.Control:
        """Render grid pattern"""
        return ft.CustomPaint(
            width=width,
            height=height,
            painter=GridPainter(size)
        )
    
    def render_rulers(self, viewport: Rectangle) -> Tuple[ft.Control, ft.Control]:
        """Render horizontal and vertical rulers"""
        h_ruler = ft.Container(
            height=20,
            width=viewport.width,
            content=ft.CustomPaint(
                painter=RulerPainter("horizontal", viewport.x)
            )
        )
        
        v_ruler = ft.Container(
            width=20,
            height=viewport.height,
            content=ft.CustomPaint(
                painter=RulerPainter("vertical", viewport.y)
            )
        )
        
        return h_ruler, v_ruler
    
    def render_alignment_guides(self, dragging: Component, 
                                targets: List[Component]) -> List[ft.Control]:
        """Render smart alignment guides while dragging"""
        guides = []
        drag_bounds = get_component_bounds(dragging)
        
        for target in targets:
            if target.id == dragging.id:
                continue
                
            target_bounds = get_component_bounds(target)
            
            # Check edge alignment
            if abs(drag_bounds.left - target_bounds.left) < 5:
                guides.append(self._vertical_guide(target_bounds.left))
            if abs(drag_bounds.right - target_bounds.right) < 5:
                guides.append(self._vertical_guide(target_bounds.right))
            if abs(drag_bounds.top - target_bounds.top) < 5:
                guides.append(self._horizontal_guide(target_bounds.top))
            if abs(drag_bounds.bottom - target_bounds.bottom) < 5:
                guides.append(self._horizontal_guide(target_bounds.bottom))
            
            # Check center alignment
            if abs(drag_bounds.center_x - target_bounds.center_x) < 5:
                guides.append(self._vertical_guide(target_bounds.center_x, dashed=True))
            if abs(drag_bounds.center_y - target_bounds.center_y) < 5:
                guides.append(self._horizontal_guide(target_bounds.center_y, dashed=True))
        
        return guides
```

### Device Preview

```python
class DeviceFrame:
    """Renders device frames for responsive preview"""
    
    DEVICES = {
        "iphone_14": {
            "width": 390,
            "height": 844,
            "scale": 3,
            "frame": "assets/frames/iphone_14.png",
            "screen_offset": (20, 60)
        },
        "ipad": {
            "width": 820,
            "height": 1180,
            "scale": 2,
            "frame": "assets/frames/ipad.png",
            "screen_offset": (40, 80)
        }
        # More devices...
    }
    
    def render_device(self, device_name: str, content: ft.Control) -> ft.Control:
        device = self.DEVICES[device_name]
        
        return ft.Stack([
            # Device frame image
            ft.Image(
                src=device["frame"],
                fit=ft.ImageFit.CONTAIN
            ),
            
            # Screen content
            ft.Container(
                left=device["screen_offset"][0],
                top=device["screen_offset"][1],
                width=device["width"],
                height=device["height"],
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Transform(
                    scale=1 / device["scale"],
                    content=content
                )
            )
        ])
```

## Performance Optimization

### 1. Viewport Culling
```python
def cull_components(components: List[Component], viewport: Rectangle) -> List[Component]:
    """Only render components visible in viewport"""
    visible = []
    for component in components:
        bounds = get_component_bounds(component)
        if rectangles_intersect(bounds, viewport):
            visible.append(component)
    return visible
```

### 2. Render Caching
```python
class RenderCache:
    def __init__(self):
        self._cache = {}
    
    def get_or_render(self, component: Component) -> ft.Control:
        cache_key = f"{component.id}:{component.last_modified}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        rendered = render_component(component)
        self._cache[cache_key] = rendered
        return rendered
```

### 3. Debounced Updates
```python
class DebouncedCanvas:
    def __init__(self, canvas: Canvas, delay: float = 0.016):  # 60fps
        self.canvas = canvas
        self.delay = delay
        self._pending_update = None
    
    def update(self):
        if self._pending_update:
            self._pending_update.cancel()
        
        self._pending_update = Timer(self.delay, self._do_update)
        self._pending_update.start()
```

## Testing Requirements

### Unit Tests
- Component rendering accuracy
- Style parsing functions
- Bounds calculations
- Hit testing

### Integration Tests
- Selection system
- Zoom and pan
- Device preview
- Guide snapping

### Performance Tests
- Render 1000+ components
- Smooth dragging
- Zoom performance
- Memory usage

## Future Enhancements

1. **3D Transforms**: Support for perspective and 3D rotation
2. **Filters**: Blur, drop-shadow, etc.
3. **Blend Modes**: Layer blending options
4. **Animation Preview**: Play CSS animations
5. **Component States**: Show hover/active states
6. **Accessibility Overlay**: Show ARIA labels and roles
7. **Performance Monitor**: FPS and render time display
8. **Export Views**: Export canvas as image/PDF

## Example Usage

```python
# Initialize canvas
canvas = CanvasRenderer()
state = CanvasState(
    components=load_components(),
    show_grid=True,
    grid_size=20
)

# Render
canvas_ui = canvas.render(state)

# Handle selection
canvas.on_select = lambda ids: update_property_panel(ids)

# Toggle preview mode
state.show_guides = False
canvas.update(state)

# Device preview
state.device_frame = "iphone_14"
canvas.update(state)
```