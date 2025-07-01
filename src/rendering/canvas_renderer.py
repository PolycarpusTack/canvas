"""
Core Canvas Rendering Engine
Implements high-performance component rendering with Flet Canvas
Following CLAUDE.md guidelines for 60fps performance
"""

import flet as ft
from typing import List, Optional, Dict, Any, Set, Tuple
from dataclasses import dataclass, field
import time
import logging
from collections import OrderedDict

from models.component import Component
from managers.state_types import CanvasState, SelectionState, ComponentTreeState
from managers.spatial_index import BoundingBox

logger = logging.getLogger(__name__)


@dataclass
class RenderContext:
    """Context passed through rendering pipeline"""
    component: Component
    parent: Optional['RenderContext'] = None
    depth: int = 0
    parent_width: Optional[float] = None
    parent_height: Optional[float] = None
    zoom_level: float = 1.0
    viewport_offset: Tuple[float, float] = (0, 0)
    is_selected: bool = False
    is_hovered: bool = False
    is_dragging: bool = False
    
    @property
    def absolute_position(self) -> Tuple[float, float]:
        """Calculate absolute position considering parent transforms"""
        x = float(self.component.style.left or 0)
        y = float(self.component.style.top or 0)
        
        if self.parent:
            parent_x, parent_y = self.parent.absolute_position
            x += parent_x
            y += parent_y
            
        return (x, y)


class CanvasRenderer:
    """
    Main canvas rendering engine
    CLAUDE.md #1.5: Profile before optimizing
    CLAUDE.md #2.1.4: Proper resource management
    CLAUDE.md #12.1: Performance tracking
    """
    
    def __init__(self, viewport_size: Tuple[int, int] = (1200, 800)):
        """Initialize renderer with viewport size"""
        self.viewport_width, self.viewport_height = viewport_size
        
        # Performance settings
        self.frame_budget_ms = 16.0  # Target 60fps
        self.enable_caching = True
        self.enable_culling = True
        self.enable_batching = True
        
        # Rendering state
        self._render_queue: List[Component] = []
        self._dirty_regions: Set[BoundingBox] = set()
        self._frame_count = 0
        self._last_render_time = 0.0
        
        # Performance metrics
        self.metrics = {
            "frame_times": [],
            "component_counts": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "culled_components": 0
        }
        
        # Initialize subsystems (will be created in separate files)
        self._init_subsystems()
        
    def _init_subsystems(self):
        """Initialize rendering subsystems"""
        # These will be imported once we create them
        from .viewport_manager import ViewportManager
        from .render_cache import RenderCache
        
        self.viewport_manager = ViewportManager(
            width=self.viewport_width,
            height=self.viewport_height
        )
        self.render_cache = RenderCache(max_size=1000)
        
        # Component renderer for style-to-visual mapping
        from .component_renderer import ComponentRenderer
        self.component_renderer = ComponentRenderer(self.render_cache)
        
        logger.info(f"Canvas renderer initialized with viewport {self.viewport_width}x{self.viewport_height}")
    
    def render(
        self, 
        component_tree: ComponentTreeState,
        canvas_state: CanvasState,
        selection_state: SelectionState
    ) -> ft.Control:
        """
        Main render method - orchestrates the rendering pipeline
        Returns a Flet Control that can be displayed
        """
        start_time = time.perf_counter()
        self._frame_count += 1
        
        try:
            # Phase 1: Update viewport with current zoom/pan
            self.viewport_manager.update(
                zoom=canvas_state.zoom,
                pan_x=canvas_state.pan_x,
                pan_y=canvas_state.pan_y
            )
            
            # Phase 2: Cull invisible components using spatial index
            visible_components = self._cull_components(
                component_tree,
                self.viewport_manager.get_bounds()
            )
            
            # Phase 3: Build render list with proper z-ordering
            render_list = self._build_render_list(
                visible_components,
                component_tree,
                selection_state
            )
            
            # Phase 4: Create canvas content
            canvas_content = self._render_to_canvas(
                render_list,
                canvas_state,
                selection_state
            )
            
            # Phase 5: Apply overlays (selection, grid, guides)
            final_content = self._apply_overlays(
                canvas_content,
                canvas_state,
                selection_state
            )
            
            # Phase 6: Track performance
            self._track_performance(start_time, len(visible_components))
            
            return final_content
            
        except Exception as e:
            logger.error(f"Render failed: {e}", exc_info=True)
            return self._render_error_state(str(e))
    
    def _cull_components(
        self,
        component_tree: ComponentTreeState,
        viewport_bounds: BoundingBox
    ) -> List[str]:
        """
        Use spatial index to find visible components
        CLAUDE.md #1.5: Algorithmic efficiency
        """
        if not self.enable_culling:
            return list(component_tree.component_map.keys())
        
        # Expand viewport slightly for smooth scrolling
        expanded_bounds = BoundingBox(
            x=viewport_bounds.x - 100,
            y=viewport_bounds.y - 100,
            width=viewport_bounds.width + 200,
            height=viewport_bounds.height + 200
        )
        
        # Use spatial index for efficient culling
        visible_ids = []
        if component_tree.spatial_index:
            visible_ids = component_tree.spatial_index.query_region(expanded_bounds)
            
            # Track culling metrics
            total_components = len(component_tree.component_map)
            self.metrics["culled_components"] = total_components - len(visible_ids)
            
            logger.debug(f"Culled {self.metrics['culled_components']} of {total_components} components")
        else:
            # Fallback if spatial index not available
            visible_ids = list(component_tree.component_map.keys())
            
        return visible_ids
    
    def _build_render_list(
        self,
        visible_ids: List[str],
        component_tree: ComponentTreeState,
        selection_state: SelectionState
    ) -> List[Tuple[Component, RenderContext]]:
        """Build ordered list of components to render with their contexts"""
        render_list = []
        
        # Build render contexts for visible components
        for component_id in visible_ids:
            component_data = component_tree.component_map.get(component_id)
            if not component_data:
                continue
                
            # Create component instance from data
            component = self._create_component_from_data(component_data)
            
            # Create render context
            context = RenderContext(
                component=component,
                zoom_level=self.viewport_manager.zoom,
                viewport_offset=(self.viewport_manager.pan_x, self.viewport_manager.pan_y),
                is_selected=component_id in selection_state.selected_ids,
                is_hovered=False  # Will be set by interaction system
            )
            
            # Determine parent context if needed
            parent_id = component_tree.parent_map.get(component_id)
            if parent_id:
                # Find parent in render list (if already added)
                for comp, ctx in render_list:
                    if comp.id == parent_id:
                        context.parent = ctx
                        context.depth = ctx.depth + 1
                        break
            
            render_list.append((component, context))
        
        # Sort by depth for proper z-ordering
        render_list.sort(key=lambda x: (x[1].depth, x[0].style.z_index or 0))
        
        return render_list
    
    def _render_to_canvas(
        self,
        render_list: List[Tuple[Component, RenderContext]],
        canvas_state: CanvasState,
        selection_state: SelectionState
    ) -> ft.Control:
        """
        Render components to a Flet Canvas
        This is where the actual drawing happens
        """
        # Create canvas with proper size
        canvas = ft.Canvas(
            width=self.viewport_width,
            height=self.viewport_height,
            on_pan_start=self._handle_pan_start,
            on_pan_update=self._handle_pan_update,
            on_pan_end=self._handle_pan_end,
            on_hover=self._handle_hover,
            on_tap_down=self._handle_tap_down,
            on_tap_up=self._handle_tap_up
        )
        
        # Render each component
        for component, context in render_list:
            self._render_component(canvas, component, context)
        
        return canvas
    
    def _render_component(
        self,
        canvas: ft.Canvas,
        component: Component,
        context: RenderContext
    ) -> None:
        """
        Render a single component to the canvas
        This will be expanded in component_renderer.py
        """
        # For now, simple rectangle rendering
        # This will be replaced with proper component rendering
        x, y = context.absolute_position
        
        # Apply viewport transform
        screen_x = (x - context.viewport_offset[0]) * context.zoom_level
        screen_y = (y - context.viewport_offset[1]) * context.zoom_level
        
        # Get dimensions
        width = self._parse_dimension(component.style.width, context.parent_width) or 100
        height = self._parse_dimension(component.style.height, context.parent_height) or 50
        
        # Scale by zoom
        width *= context.zoom_level
        height *= context.zoom_level
        
        # Draw component background
        with canvas:
            # Background
            if component.style.background_color:
                canvas.fill_paint.color = component.style.background_color
                canvas.fill_rect(screen_x, screen_y, width, height)
            
            # Border
            if component.style.border:
                canvas.stroke_paint.color = component.style.border_color or "#E5E7EB"
                canvas.stroke_paint.stroke_width = 1 * context.zoom_level
                canvas.draw_rect(screen_x, screen_y, width, height)
            
            # Selection highlight
            if context.is_selected:
                canvas.stroke_paint.color = "#5E6AD2"
                canvas.stroke_paint.stroke_width = 2 * context.zoom_level
                canvas.draw_rect(
                    screen_x - 1, 
                    screen_y - 1, 
                    width + 2, 
                    height + 2
                )
    
    def _apply_overlays(
        self,
        canvas_content: ft.Control,
        canvas_state: CanvasState,
        selection_state: SelectionState
    ) -> ft.Control:
        """Apply overlays like grid, guides, selection handles"""
        overlays = []
        
        # Grid overlay
        if canvas_state.show_grid:
            from .grid_renderer import GridRenderer
            grid_renderer = GridRenderer()
            grid_overlay = grid_renderer.render_grid(
                viewport=self.viewport_manager.get_bounds(),
                grid_size=canvas_state.grid_size,
                zoom=canvas_state.zoom
            )
            overlays.append(grid_overlay)
        
        # Selection overlay (handles, etc)
        if selection_state.selected_ids:
            from .selection_renderer import SelectionRenderer
            selection_renderer = SelectionRenderer()
            selection_overlay = selection_renderer.render_selection(
                selected_ids=list(selection_state.selected_ids),
                component_map=self._get_component_map(),
                viewport=self.viewport_manager,
                zoom=canvas_state.zoom
            )
            overlays.append(selection_overlay)
        
        # Stack all overlays on top of canvas
        return ft.Stack(
            controls=[canvas_content] + overlays,
            width=self.viewport_width,
            height=self.viewport_height
        )
    
    def _track_performance(self, start_time: float, component_count: int) -> None:
        """
        Track rendering performance metrics
        CLAUDE.md #12.1: Performance monitoring
        """
        render_time = (time.perf_counter() - start_time) * 1000
        
        # Update metrics
        self.metrics["frame_times"].append(render_time)
        self.metrics["component_counts"].append(component_count)
        
        # Keep only last 60 frames
        if len(self.metrics["frame_times"]) > 60:
            self.metrics["frame_times"] = self.metrics["frame_times"][-60:]
            self.metrics["component_counts"] = self.metrics["component_counts"][-60:]
        
        # Warn if frame budget exceeded
        if render_time > self.frame_budget_ms:
            logger.warning(
                f"Frame budget exceeded: {render_time:.1f}ms "
                f"(target: {self.frame_budget_ms}ms) "
                f"with {component_count} components"
            )
            
        # Log performance stats every 60 frames
        if self._frame_count % 60 == 0:
            avg_frame_time = sum(self.metrics["frame_times"]) / len(self.metrics["frame_times"])
            logger.info(
                f"Render performance - "
                f"Avg frame time: {avg_frame_time:.1f}ms, "
                f"Cache hit rate: {self._calculate_cache_hit_rate():.1%}, "
                f"Avg components: {sum(self.metrics['component_counts']) / len(self.metrics['component_counts']):.0f}"
            )
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        if total == 0:
            return 0.0
        return self.metrics["cache_hits"] / total
    
    def _parse_dimension(self, value: Optional[str], parent_size: Optional[float]) -> Optional[float]:
        """Parse CSS dimension value"""
        if not value:
            return None
            
        if isinstance(value, (int, float)):
            return float(value)
            
        if value.endswith('px'):
            return float(value[:-2])
        elif value.endswith('%') and parent_size:
            return float(value[:-1]) / 100 * parent_size
        else:
            try:
                return float(value)
            except ValueError:
                return None
    
    def _create_component_from_data(self, data: Dict[str, Any]) -> Component:
        """Create Component instance from raw data"""
        from models.component import Component, ComponentStyle
        
        # Create style object
        style_data = data.get('style', {})
        style = ComponentStyle(**style_data)
        
        # Create component
        component = Component(
            id=data['id'],
            type=data.get('type', 'div'),
            name=data.get('name', ''),
            style=style,
            children=[]  # Children handled separately in render tree
        )
        
        # Set additional properties
        if 'properties' in data:
            component.properties = data['properties']
        if 'attributes' in data:
            component.attributes = data['attributes']
            
        return component
    
    def _render_error_state(self, error: str) -> ft.Control:
        """Render error state when rendering fails"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(
                    ft.Icons.ERROR_OUTLINE,
                    size=48,
                    color="#EF4444"
                ),
                ft.Text(
                    "Canvas Render Error",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color="#EF4444"
                ),
                ft.Text(
                    error,
                    size=14,
                    color="#6B7280",
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            alignment=ft.alignment.center,
            width=self.viewport_width,
            height=self.viewport_height,
            bgcolor="#FEF2F2"
        )
    
    # Event handlers (will be connected to interaction system)
    def _handle_pan_start(self, e: ft.DragStartEvent) -> None:
        """Handle pan start for canvas drag"""
        try:
            # Store initial drag position for panning
            self._pan_start_position = (e.global_x, e.global_y)
            self._initial_viewport_offset = (
                self.viewport_manager.offset_x,
                self.viewport_manager.offset_y
            )
            self._is_panning = True
            logger.debug(f"Pan started at ({e.global_x}, {e.global_y})")
        except Exception as ex:
            logger.error(f"Error in pan start: {ex}")
    
    def _handle_pan_update(self, e: ft.DragUpdateEvent) -> None:
        """Handle pan update for canvas drag"""
        try:
            if not self._is_panning or not hasattr(self, '_pan_start_position'):
                return
            
            # Calculate drag delta
            delta_x = e.global_x - self._pan_start_position[0]
            delta_y = e.global_y - self._pan_start_position[1]
            
            # Update viewport offset
            new_offset_x = self._initial_viewport_offset[0] - delta_x
            new_offset_y = self._initial_viewport_offset[1] - delta_y
            
            # Apply constraints to prevent panning too far
            max_offset_x = max(0, self.render_pipeline.canvas_width - self.viewport_width)
            max_offset_y = max(0, self.render_pipeline.canvas_height - self.viewport_height)
            
            new_offset_x = max(0, min(new_offset_x, max_offset_x))
            new_offset_y = max(0, min(new_offset_y, max_offset_y))
            
            # Update viewport
            self.viewport_manager.pan(new_offset_x - self.viewport_manager.offset_x, 
                                     new_offset_y - self.viewport_manager.offset_y)
            
            # Trigger re-render if needed
            if hasattr(self, 'on_viewport_change'):
                self.on_viewport_change()
                
        except Exception as ex:
            logger.error(f"Error in pan update: {ex}")
    
    def _handle_pan_end(self, e: ft.DragEndEvent) -> None:
        """Handle pan end"""
        try:
            self._is_panning = False
            self._pan_start_position = None
            self._initial_viewport_offset = None
            logger.debug("Pan ended")
        except Exception as ex:
            logger.error(f"Error in pan end: {ex}")
    
    def _handle_hover(self, e: ft.HoverEvent) -> None:
        """Handle mouse hover for component highlighting"""
        try:
            # Convert screen coordinates to canvas coordinates
            canvas_x = e.local_x + self.viewport_manager.offset_x
            canvas_y = e.local_y + self.viewport_manager.offset_y
            
            # Find component at position
            component_id = self._find_component_at_position(canvas_x, canvas_y)
            
            # Update hover state if changed
            if component_id != self._hovered_component_id:
                self._hovered_component_id = component_id
                
                # Notify hover change callback if set
                if hasattr(self, 'on_component_hover'):
                    self.on_component_hover(component_id)
                
                # Mark dirty for re-render
                self.mark_dirty(component_id)
                
        except Exception as ex:
            logger.error(f"Error in hover handler: {ex}")
    
    def _handle_tap_down(self, e: ft.TapEvent) -> None:
        """Handle tap/click for selection"""
        try:
            # Convert screen coordinates to canvas coordinates
            canvas_x = e.local_x + self.viewport_manager.offset_x
            canvas_y = e.local_y + self.viewport_manager.offset_y
            
            # Store tap position for drag detection
            self._tap_down_position = (canvas_x, canvas_y)
            self._tap_down_time = time.time()
            
            # Find component at position
            component_id = self._find_component_at_position(canvas_x, canvas_y)
            
            if component_id:
                # Notify selection callback
                if hasattr(self, 'on_component_select'):
                    self.on_component_select(component_id)
                    
                logger.debug(f"Component selected: {component_id}")
            else:
                # Clear selection if clicking empty space
                if hasattr(self, 'on_component_select'):
                    self.on_component_select(None)
                    
        except Exception as ex:
            logger.error(f"Error in tap down: {ex}")
    
    def _handle_tap_up(self, e: ft.TapEvent) -> None:
        """Handle tap up"""
        try:
            # Check if this was a click or drag
            if hasattr(self, '_tap_down_position') and hasattr(self, '_tap_down_time'):
                elapsed_time = time.time() - self._tap_down_time
                
                # If quick tap and minimal movement, treat as click
                if elapsed_time < 0.3:  # 300ms threshold
                    # Click handled in tap_down
                    pass
                
            # Clear tap state
            self._tap_down_position = None
            self._tap_down_time = None
            
        except Exception as ex:
            logger.error(f"Error in tap up: {ex}")
    
    def _find_component_at_position(self, x: float, y: float) -> Optional[str]:
        """Find component at given canvas position"""
        try:
            components = self._get_component_map()
            
            # Check components in reverse order (top to bottom)
            for comp_id, component in reversed(list(components.items())):
                if self._is_point_in_component(x, y, component):
                    return comp_id
                    
            return None
            
        except Exception as ex:
            logger.error(f"Error finding component at position: {ex}")
            return None
    
    def _is_point_in_component(self, x: float, y: float, component: Component) -> bool:
        """Check if point is inside component bounds"""
        try:
            # Get component bounds
            comp_x = float(component.style.left or 0)
            comp_y = float(component.style.top or 0)
            comp_width = float(component.style.width or 100)
            comp_height = float(component.style.height or 50)
            
            # Check if point is inside bounds
            return (comp_x <= x <= comp_x + comp_width and
                    comp_y <= y <= comp_y + comp_height)
                    
        except Exception as ex:
            logger.error(f"Error checking point in component: {ex}")
            return False
    
    def _get_component_map(self) -> Dict[str, Component]:
        """Get current component map (will be connected to state)"""
        # Try to get from state manager if available
        if hasattr(self, 'state_manager') and self.state_manager:
            try:
                state = self.state_manager.get_state_system().get_state("components")
                if hasattr(state, 'component_map'):
                    return state.component_map
            except:
                pass
        
        # Fallback to empty map
        return {}
    
    # Public API
    
    def set_viewport_size(self, width: int, height: int) -> None:
        """Update viewport size"""
        self.viewport_width = width
        self.viewport_height = height
        self.viewport_manager.resize(width, height)
        logger.info(f"Viewport resized to {width}x{height}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        if not self.metrics["frame_times"]:
            return {"error": "No performance data available"}
            
        return {
            "avg_frame_time": sum(self.metrics["frame_times"]) / len(self.metrics["frame_times"]),
            "max_frame_time": max(self.metrics["frame_times"]),
            "min_frame_time": min(self.metrics["frame_times"]),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "culled_components": self.metrics["culled_components"],
            "total_frames": self._frame_count
        }
    
    def clear_cache(self) -> None:
        """Clear render cache"""
        if hasattr(self, 'render_cache'):
            self.render_cache.clear()
        logger.info("Render cache cleared")
    
    def mark_dirty(self, component_id: str, bounds: Optional[BoundingBox] = None) -> None:
        """Mark a region as needing redraw"""
        if bounds:
            self._dirty_regions.add(bounds)
        # In a full implementation, this would trigger incremental updates