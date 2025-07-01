# Canvas Rendering - Development Plan

## Phase 1: Solution Design Analysis & Validation

### 1. Initial Understanding
- **Goal**: Implement high-performance visual rendering system for components
- **Stack**: Flet rendering, Python graphics, Custom painting
- **Components**: CanvasRenderer, SelectionSystem, GuideRenderer, DevicePreview
- **User Personas**: Designers viewing and interacting with their designs

### 2. Clarity Assessment
- **Component Rendering**: High (3) - Clear component-to-visual mapping
- **Selection System**: High (3) - Standard selection patterns
- **Visual Guides**: Medium (2) - Complex alignment calculations
- **Performance Requirements**: Medium (2) - Need specific benchmarks
- **Device Preview**: High (3) - Well-defined device specifications
- **Overall Clarity**: High (3)

### 3. Technical Feasibility
- **Basic Rendering**: Low risk (1) - Flet provides rendering primitives
- **Performance at Scale**: High risk (3) - 1000+ components challenging
- **Custom Painting**: Medium risk (2) - Grid/guides need custom implementation
- **Selection Handles**: Medium risk (2) - Interactive resize complex

### 4. Security Assessment
- **Component Isolation**: Prevent components from breaking canvas
- **Resource Limits**: Prevent memory exhaustion with many components
- **Safe Rendering**: Sanitize component content

### 5. Performance Requirements
- **Frame Rate**: 60fps during interactions
- **Render Time**: < 16ms for updates
- **Memory**: < 500MB for 1000 components

**Recommendation**: PROCEEDING with backlog generation

---

## EPIC A: Core Rendering Pipeline

Implement fundamental component rendering with performance optimization.

**Definition of Done:**
- ✓ Components render accurately with all styles
- ✓ 60fps maintained during scroll/zoom
- ✓ Memory usage within bounds

**Business Value:** Core visual feedback for design work

**Risk Assessment:**
- Performance degradation (High/3) - Implement viewport culling
- Memory leaks (Medium/2) - Proper component lifecycle
- Cross-platform rendering (Medium/2) - Test all platforms

**Cross-Functional Requirements:**
- Performance: 60fps with 1000 components
- Accessibility: Screen reader describes canvas state
- Security: Prevent render exploits
- Observability: Render performance metrics

---

### USER STORY A-1: Basic Component Rendering

**ID & Title:** A-1: Render Components with Styles
**User Persona Narrative:** As a designer, I want to see my components rendered accurately so I can design visually
**Business Value:** High (3)
**Priority Score:** 5
**Story Points:** L

**Acceptance Criteria:**
```gherkin
Given I have a component with styles
When the canvas renders
Then I see the component with correct size, color, and position
And nested components render in correct order
And text renders with proper fonts

Given I have 100 components
When I scroll the canvas
Then scrolling is smooth at 60fps
And components outside viewport are culled
```

**External Dependencies:** Flet rendering API
**Technical Debt Considerations:** May need custom renderer for complex styles
**Test Data Requirements:** Various component hierarchies

---

#### TASK A-1-T1: Implement Render Pipeline Architecture

**Goal:** Create efficient rendering pipeline with lifecycle management

**Token Budget:** 10,000 tokens

**Architecture:**
```python
class CanvasRenderer:
    """
    CLAUDE.md #1.5: Profile before optimizing
    CLAUDE.md #2.1.4: Proper resource management
    """
    def __init__(self, viewport_size: Size):
        self.viewport = viewport_size
        self.render_cache = RenderCache()
        self.spatial_index = SpatialIndex()
        self.frame_budget = 16  # ms for 60fps
        self._render_queue = []
        self._dirty_regions = []
        
    def render(self, state: CanvasState) -> ft.Control:
        """
        Main render pipeline with performance tracking
        """
        start_time = time.perf_counter()
        
        try:
            # Phase 1: Update spatial index if needed
            if state.components_changed:
                self._update_spatial_index(state.components)
            
            # Phase 2: Determine visible components (viewport culling)
            visible_components = self._cull_invisible_components(
                state.components,
                state.viewport
            )
            
            # Phase 3: Build render tree
            render_tree = self._build_render_tree(visible_components)
            
            # Phase 4: Apply optimizations
            render_tree = self._optimize_render_tree(render_tree)
            
            # Phase 5: Generate UI controls
            canvas_content = self._render_components(render_tree)
            
            # Phase 6: Add overlays (selection, guides)
            final_content = self._apply_overlays(canvas_content, state)
            
            # Performance tracking
            render_time = (time.perf_counter() - start_time) * 1000
            if render_time > self.frame_budget:
                logger.warning(f"Frame budget exceeded: {render_time:.1f}ms")
                self._record_performance_issue(render_time, len(visible_components))
            
            return final_content
            
        except Exception as e:
            logger.error(f"Render failed: {e}")
            return self._render_error_state(str(e))
```

**Viewport Culling:**
```python
def _cull_invisible_components(
    self,
    components: List[Component],
    viewport: Rectangle
) -> List[Component]:
    """
    CLAUDE.md #1.5: Algorithmic efficiency
    Only render components visible in viewport
    """
    # Expand viewport slightly for smooth scrolling
    expanded_viewport = viewport.expand(100)  # 100px buffer
    
    # Use spatial index for efficient culling
    visible_ids = self.spatial_index.query_rectangle(expanded_viewport)
    
    # Build visible component list maintaining hierarchy
    visible = []
    for component in components:
        if self._is_component_visible(component, visible_ids, expanded_viewport):
            visible.append(component)
    
    logger.debug(f"Culled {len(components) - len(visible)} invisible components")
    return visible
```

**Deliverables:**
- Complete rendering pipeline
- Viewport culling implementation
- Performance monitoring
- Error recovery

**Quality Gates:**
- ✓ < 16ms render time for 100 components
- ✓ Proper cleanup of removed components
- ✓ No memory leaks in render cycle
- ✓ Graceful degradation on overload

**Unblocks:** [A-1-T2, A-1-T3]
**Confidence Score:** Medium (2) - Performance optimization complex

---

#### TASK A-1-T2: Component to Visual Mapping

**Goal:** Convert component models to visual representations

**Token Budget:** 12,000 tokens

**Component Renderer:**
```python
class ComponentRenderer:
    """
    CLAUDE.md #3.4: Follow established patterns
    CLAUDE.md #7.2: Output encoding for safety
    """
    
    def render_component(
        self,
        component: Component,
        parent_context: RenderContext
    ) -> ft.Control:
        """Convert component to Flet control"""
        
        # Create render context
        context = RenderContext(
            component=component,
            parent=parent_context,
            depth=parent_context.depth + 1 if parent_context else 0
        )
        
        # Base container with positioning
        container = ft.Container(
            key=component.id,  # For efficient updates
            width=self._calculate_width(component, context),
            height=self._calculate_height(component, context),
            left=self._calculate_left(component, context),
            top=self._calculate_top(component, context),
            padding=self._parse_padding(component.style.padding),
            margin=self._parse_margin(component.style.margin),
            bgcolor=component.style.background_color,
            border_radius=self._parse_border_radius(component.style.border_radius),
            border=self._parse_border(component.style.border),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            animate=self._should_animate(component)
        )
        
        # Add content based on type
        content = self._render_content(component, context)
        if content:
            container.content = content
        
        # Apply visual effects
        container = self._apply_effects(container, component)
        
        # Add interaction handlers
        container = self._add_interactions(container, component)
        
        return container
```

**Style Parsing:**
```python
def _parse_css_value(self, value: str, context: RenderContext) -> Any:
    """
    CLAUDE.md #2.1.1: Validate CSS values
    Parse CSS values with unit support
    """
    if not value:
        return None
        
    # Cache parsed values for performance
    cache_key = f"{value}:{context.parent_width}"
    if cache_key in self._parse_cache:
        return self._parse_cache[cache_key]
    
    try:
        # Handle different unit types
        if value.endswith('px'):
            result = float(value[:-2])
        elif value.endswith('%'):
            if context.parent_width:
                result = float(value[:-1]) / 100 * context.parent_width
            else:
                result = None
        elif value.endswith('rem'):
            result = float(value[:-3]) * 16  # Base font size
        elif value.endswith('em'):
            parent_font = context.parent.font_size if context.parent else 16
            result = float(value[:-2]) * parent_font
        elif value == 'auto':
            result = None  # Flet handles auto
        else:
            # Try as number
            result = float(value)
            
        self._parse_cache[cache_key] = result
        return result
        
    except ValueError:
        logger.warning(f"Invalid CSS value: {value}")
        return None
```

**Layout Systems:**
```python
def _render_layout(self, component: Component, context: RenderContext) -> ft.Control:
    """Render component children with proper layout"""
    
    if not component.children:
        return self._render_empty_container(component)
    
    # Render all children first
    child_controls = []
    for child in component.children:
        child_control = self.render_component(child, context)
        if child_control:
            child_controls.append(child_control)
    
    # Apply layout based on display type
    if component.style.display == "flex":
        return self._render_flex_layout(component, child_controls)
    elif component.style.display == "grid":
        return self._render_grid_layout(component, child_controls)
    else:
        return self._render_block_layout(component, child_controls)
```

**Unblocks:** [A-1-T3]
**Confidence Score:** High (3)

---

#### TASK A-1-T3: Implement Render Caching

**Goal:** Cache rendered components for performance

**Token Budget:** 8,000 tokens

**Cache Implementation:**
```python
class RenderCache:
    """
    CLAUDE.md #1.5: Memory-efficient caching
    CLAUDE.md #12.1: Cache performance metrics
    """
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, CachedRender] = OrderedDict()
        self.hit_count = 0
        self.miss_count = 0
        self.eviction_count = 0
        
    def get_or_render(
        self,
        component: Component,
        render_func: Callable
    ) -> ft.Control:
        """Get cached render or create new"""
        
        # Generate cache key
        cache_key = self._generate_cache_key(component)
        
        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if cached.is_valid(component):
                self.hit_count += 1
                # Move to end (LRU)
                self.cache.move_to_end(cache_key)
                return cached.control
        
        # Cache miss - render component
        self.miss_count += 1
        control = render_func(component)
        
        # Store in cache
        self.cache[cache_key] = CachedRender(
            control=control,
            component_hash=self._hash_component(component),
            timestamp=time.time()
        )
        
        # Evict if necessary
        if len(self.cache) > self.max_size:
            self._evict_oldest()
        
        return control
    
    def _generate_cache_key(self, component: Component) -> str:
        """Generate stable cache key"""
        # Include ID and style hash for cache invalidation
        style_hash = hash(frozenset(component.style.__dict__.items()))
        return f"{component.id}:{style_hash}"
```

**Cache Invalidation:**
```python
def invalidate_component(self, component_id: str):
    """Remove component from cache when changed"""
    keys_to_remove = [
        key for key in self.cache
        if key.startswith(f"{component_id}:")
    ]
    
    for key in keys_to_remove:
        del self.cache[key]
    
    logger.debug(f"Invalidated {len(keys_to_remove)} cache entries")
```

**Unblocks:** [A-2-T1]
**Confidence Score:** High (3)

---

### USER STORY A-2: Selection System

**ID & Title:** A-2: Visual Component Selection
**User Persona Narrative:** As a designer, I want to select components visually so I can edit their properties
**Business Value:** High (3)
**Priority Score:** 5
**Story Points:** M

**Acceptance Criteria:**
```gherkin
Given I click on a component
When the component is selected
Then I see a selection outline
And I see resize handles
And the properties panel updates

Given I drag-select multiple components
When I release the mouse
Then all components in the area are selected
And I see a bounding box around all
```

---

#### TASK A-2-T1: Implement Selection Rendering

**Goal:** Create visual selection indicators with handles

**Token Budget:** 9,000 tokens

**Selection Renderer:**
```python
class SelectionRenderer:
    """
    CLAUDE.md #9.1: Accessible selection indicators
    CLAUDE.md #1.2: DRY - Reusable selection styles
    """
    
    def render_selection(
        self,
        selected_components: List[Component],
        canvas_state: CanvasState
    ) -> ft.Control:
        """Render selection indicators"""
        
        if not selected_components:
            return ft.Container()  # Empty
        
        overlays = []
        
        # Single selection
        if len(selected_components) == 1:
            component = selected_components[0]
            bounds = self._get_component_bounds(component)
            
            overlays.extend([
                # Selection outline
                self._create_selection_outline(bounds),
                # Resize handles
                *self._create_resize_handles(bounds, component),
                # Dimension labels
                self._create_dimension_label(bounds),
                # Rotation handle (if applicable)
                self._create_rotation_handle(bounds) if component.rotatable else None
            ])
            
        # Multi-selection
        else:
            # Calculate bounding box
            bounds = self._calculate_group_bounds(selected_components)
            
            overlays.extend([
                # Group selection outline
                self._create_group_outline(bounds),
                # Group resize handles
                *self._create_group_handles(bounds)
            ])
        
        return ft.Stack(
            controls=[c for c in overlays if c is not None],
            clip_behavior=ft.ClipBehavior.NONE  # Allow handles outside bounds
        )
    
    def _create_resize_handles(
        self,
        bounds: Rectangle,
        component: Component
    ) -> List[ft.Control]:
        """Create interactive resize handles"""
        
        handles = []
        handle_positions = [
            ("nw", bounds.left - 4, bounds.top - 4, "nw-resize"),
            ("n", bounds.left + bounds.width/2 - 4, bounds.top - 4, "n-resize"),
            ("ne", bounds.right - 4, bounds.top - 4, "ne-resize"),
            ("e", bounds.right - 4, bounds.top + bounds.height/2 - 4, "e-resize"),
            ("se", bounds.right - 4, bounds.bottom - 4, "se-resize"),
            ("s", bounds.left + bounds.width/2 - 4, bounds.bottom - 4, "s-resize"),
            ("sw", bounds.left - 4, bounds.bottom - 4, "sw-resize"),
            ("w", bounds.left - 4, bounds.top + bounds.height/2 - 4, "w-resize")
        ]
        
        for position, x, y, cursor in handle_positions:
            # Skip handles based on resize constraints
            if not self._can_resize(component, position):
                continue
                
            handle = ft.Container(
                left=x,
                top=y,
                width=8,
                height=8,
                bgcolor="white",
                border=ft.border.all(1, "#5E6AD2"),
                border_radius=1,
                on_hover=lambda e, c=cursor: self._set_cursor(c),
                on_pan_start=lambda e, p=position: self._start_resize(p, e),
                on_pan_update=self._update_resize,
                on_pan_end=self._end_resize,
                # Accessibility
                tooltip=f"Resize {position}",
                semantics_label=f"Resize handle {position}"
            )
            
            handles.append(handle)
        
        return handles
```

**Accessible Selection:**
```python
def _announce_selection(self, components: List[Component]):
    """
    CLAUDE.md #9.4: Screen reader announcements
    """
    if len(components) == 1:
        announcement = f"Selected {components[0].type} component: {components[0].name}"
    else:
        announcement = f"Selected {len(components)} components"
    
    # Use ARIA live region
    self.live_region.announce(announcement, priority="polite")
```

**Unblocks:** [A-2-T2]
**Confidence Score:** High (3)

---

## EPIC B: Visual Guides and Helpers

Implement grid, rulers, alignment guides, and dimension indicators.

**Definition of Done:**
- ✓ Grid overlay toggleable and performant
- ✓ Smart guides appear during drag
- ✓ Rulers show accurate measurements

**Business Value:** Precision design tools

**Risk Assessment:**
- Performance with guides (Medium/2) - Use efficient rendering
- Guide accuracy (Low/1) - Simple math calculations

---

### USER STORY B-1: Grid and Alignment System

**ID & Title:** B-1: Visual Grid and Smart Guides
**User Persona Narrative:** As a designer, I want visual guides to help me align components precisely
**Business Value:** Medium (2)
**Priority Score:** 3
**Story Points:** M

---

#### TASK B-1-T1: Implement Grid Overlay

**Goal:** Create efficient grid rendering system

**Token Budget:** 7,000 tokens

**Grid Renderer:**
```python
class GridRenderer:
    """
    CLAUDE.md #1.5: Optimize grid rendering
    """
    def __init__(self):
        self.grid_cache = {}
        
    def render_grid(
        self,
        viewport: Rectangle,
        grid_size: int = 20,
        show_major: bool = True
    ) -> ft.Control:
        """Render grid pattern efficiently"""
        
        # Check cache
        cache_key = f"{viewport.width}x{viewport.height}:{grid_size}"
        if cache_key in self.grid_cache:
            return self.grid_cache[cache_key]
        
        # Create custom paint for grid
        grid_painter = GridPainter(
            grid_size=grid_size,
            minor_color="#E5E7EB",  # Gray-200
            major_color="#D1D5DB",  # Gray-300
            major_interval=grid_size * 5
        )
        
        grid_control = ft.CustomPaint(
            width=viewport.width,
            height=viewport.height,
            painter=grid_painter,
            # Low priority rendering
            opacity=0.5
        )
        
        # Cache for reuse
        self.grid_cache[cache_key] = grid_control
        
        return grid_control


class GridPainter(ft.CustomPainter):
    """Custom painter for efficient grid rendering"""
    
    def paint(self, canvas: ft.Canvas, size: ft.Size):
        """
        CLAUDE.md #1.5: Efficient drawing algorithm
        """
        # Only draw visible grid lines
        start_x = 0
        start_y = 0
        
        # Minor grid lines
        canvas.save()
        canvas.stroke_paint.color = self.minor_color
        canvas.stroke_paint.stroke_width = 0.5
        
        # Vertical lines
        x = start_x
        while x <= size.width:
            canvas.draw_line(x, 0, x, size.height)
            x += self.grid_size
        
        # Horizontal lines
        y = start_y
        while y <= size.height:
            canvas.draw_line(0, y, size.width, y)
            y += self.grid_size
        
        canvas.restore()
        
        # Major grid lines
        if self.major_interval:
            canvas.save()
            canvas.stroke_paint.color = self.major_color
            canvas.stroke_paint.stroke_width = 1
            
            # Draw major lines...
```

**Unblocks:** [B-1-T2]
**Confidence Score:** High (3)

---

## Technical Debt Management

```yaml
# Canvas Rendering Debt Tracking
rendering_debt:
  items:
    - id: CR-001
      description: "WebGL renderer for better performance"
      impact: "10x performance improvement possible"
      effort: "XL"
      priority: 1
      
    - id: CR-002
      description: "Render worker threads"
      impact: "Non-blocking rendering"
      effort: "L"
      priority: 2
      
    - id: CR-003
      description: "Level-of-detail rendering"
      impact: "Better performance when zoomed out"
      effort: "M"
      priority: 3
```

---

## Performance Testing Strategy

```python
class RenderingPerformanceTests:
    """CLAUDE.md #6.5: Performance testing"""
    
    @pytest.mark.performance
    def test_render_1000_components(self, benchmark):
        """Must maintain 60fps with 1000 components"""
        components = generate_component_tree(count=1000)
        renderer = CanvasRenderer()
        
        result = benchmark.pedantic(
            renderer.render,
            args=(CanvasState(components=components),),
            iterations=100,
            rounds=5
        )
        
        # 16.67ms budget for 60fps
        assert result.stats['mean'] < 0.01667
        assert result.stats['max'] < 0.020  # Allow some variance
    
    def test_memory_usage(self):
        """Memory should stay under 500MB"""
        import tracemalloc
        tracemalloc.start()
        
        # Render many components
        components = generate_component_tree(count=5000)
        renderer = CanvasRenderer()
        
        for _ in range(10):
            renderer.render(CanvasState(components=components))
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        assert peak < 500 * 1024 * 1024  # 500MB
```

---

## Accessibility Requirements

```python
class CanvasAccessibility:
    """CLAUDE.md #9: Canvas accessibility"""
    
    def describe_canvas_state(self, state: CanvasState) -> str:
        """Generate screen reader description"""
        description = f"Canvas with {len(state.components)} components. "
        
        if state.selected_components:
            description += f"{len(state.selected_components)} selected. "
        
        if state.zoom_level != 1.0:
            description += f"Zoomed to {int(state.zoom_level * 100)}%. "
        
        return description
    
    def announce_changes(self, changes: List[CanvasChange]):
        """Announce canvas changes to screen readers"""
        for change in changes:
            if change.type == ChangeType.ADD:
                self.announce(f"Added {change.component.type}")
            elif change.type == ChangeType.DELETE:
                self.announce(f"Deleted {change.component.type}")
            elif change.type == ChangeType.MOVE:
                self.announce(f"Moved {change.component.type}")
```