"""
Canvas Integration Module
Integrates the new rendering system with existing canvas UI
Following CLAUDE.md guidelines for clean integration
"""

import flet as ft
from typing import Optional, Dict, Any, Callable, List, Tuple
import logging
import asyncio

from models.component import Component
from managers.state_types import CanvasState, SelectionState, ComponentTreeState, ActionType, Action
from managers.canvas_actions import CanvasActionHandler
from components.drag_drop_manager import DragDropManager
from .canvas_renderer import CanvasRenderer
from .viewport_manager import ViewportManager
from .render_pipeline import RenderPipeline, RenderPipelineConfig

logger = logging.getLogger(__name__)


class CanvasRenderingSystem:
    """
    Main integration point for the canvas rendering system
    Connects rendering to state management and UI
    CLAUDE.md #3.1: Clear interfaces
    """
    
    def __init__(
        self,
        canvas_container: ft.Container,
        state_manager: Any,  # State manager instance
        drag_drop_manager: DragDropManager
    ):
        """Initialize canvas rendering system"""
        self.canvas_container = canvas_container
        self.state_manager = state_manager
        self.drag_drop_manager = drag_drop_manager
        
        # Get canvas dimensions
        width = int(canvas_container.width or 1200)
        height = int(canvas_container.height or 800)
        
        # Initialize rendering components
        self.viewport_manager = ViewportManager(width, height)
        self.canvas_renderer = CanvasRenderer((width, height))
        
        # Initialize render pipeline
        pipeline_config = RenderPipelineConfig(
            enable_culling=True,
            enable_caching=True,
            enable_batching=True,
            target_fps=60
        )
        self.render_pipeline = RenderPipeline(pipeline_config)
        
        # Set render handler
        self.render_pipeline.set_render_handler(self._render_handler)
        
        # Canvas action handler
        self.action_handler = CanvasActionHandler(state_manager)
        
        # Interaction state
        self.is_panning = False
        self.is_selecting = False
        self.selection_start: Optional[Tuple[float, float]] = None
        self.hover_component_id: Optional[str] = None
        
        # Render control
        self.render_task: Optional[asyncio.Task] = None
        self.needs_render = True
        
        logger.info(f"Canvas rendering system initialized: {width}x{height}")
    
    def start(self) -> None:
        """Start the rendering system"""
        # Subscribe to state changes
        self._subscribe_to_state()
        
        # Start render loop
        self.render_task = asyncio.create_task(self._render_loop())
        
        logger.info("Canvas rendering system started")
    
    def stop(self) -> None:
        """Stop the rendering system"""
        if self.render_task:
            self.render_task.cancel()
            self.render_task = None
        
        logger.info("Canvas rendering system stopped")
    
    async def _render_loop(self) -> None:
        """Main render loop"""
        try:
            while True:
                if self.needs_render:
                    await self._render_frame()
                    self.needs_render = False
                
                # Target 60fps
                await asyncio.sleep(1/60)
                
        except asyncio.CancelledError:
            logger.info("Render loop cancelled")
        except Exception as e:
            logger.error(f"Render loop error: {e}", exc_info=True)
    
    async def _render_frame(self) -> None:
        """Render a single frame"""
        try:
            # Get current state
            app_state = self.state_manager.get_state()
            component_tree = app_state.components
            canvas_state = app_state.canvas
            selection_state = app_state.selection
            
            # Update viewport from canvas state
            self.viewport_manager.update(
                zoom=canvas_state.zoom,
                pan_x=canvas_state.pan_x,
                pan_y=canvas_state.pan_y
            )
            
            # Execute render pipeline
            render_output = self.render_pipeline.execute(
                component_tree=component_tree,
                canvas_state=canvas_state,
                selection_state=selection_state,
                viewport=self.viewport_manager
            )
            
            # Update canvas container
            if render_output:
                self.canvas_container.content = render_output
                await self.canvas_container.update_async()
            
        except Exception as e:
            logger.error(f"Render frame error: {e}", exc_info=True)
    
    def _render_handler(
        self,
        visible_objects: List[Any],
        context: Dict[str, Any]
    ) -> ft.Control:
        """
        Custom render handler for the pipeline
        Delegates to CanvasRenderer
        """
        return self.canvas_renderer.render(
            context["component_tree"],
            context["canvas_state"],
            context["selection_state"]
        )
    
    def _subscribe_to_state(self) -> None:
        """Subscribe to relevant state changes"""
        # Subscribe to component changes
        self.state_manager.subscribe(
            "components",
            lambda old, new: self._on_components_changed()
        )
        
        # Subscribe to canvas state changes
        self.state_manager.subscribe(
            "canvas",
            lambda old, new: self._on_canvas_changed(old, new)
        )
        
        # Subscribe to selection changes
        self.state_manager.subscribe(
            "selection",
            lambda old, new: self._on_selection_changed()
        )
    
    def _on_components_changed(self) -> None:
        """Handle component tree changes"""
        self.needs_render = True
        self.canvas_renderer.clear_cache()
    
    def _on_canvas_changed(self, old_state: CanvasState, new_state: CanvasState) -> None:
        """Handle canvas state changes"""
        # Check what changed
        if (old_state.zoom != new_state.zoom or
            old_state.pan_x != new_state.pan_x or
            old_state.pan_y != new_state.pan_y):
            # Viewport changed
            self.viewport_manager.update(
                zoom=new_state.zoom,
                pan_x=new_state.pan_x,
                pan_y=new_state.pan_y
            )
        
        self.needs_render = True
    
    def _on_selection_changed(self) -> None:
        """Handle selection changes"""
        self.needs_render = True
    
    # Mouse/Touch Event Handlers
    
    def handle_pointer_down(self, e: ft.TapEvent) -> None:
        """Handle mouse/touch down"""
        # Convert screen to world coordinates
        world_x, world_y = self.viewport_manager.screen_to_world(e.local_x, e.local_y)
        
        # Check for component hit
        app_state = self.state_manager.get_state()
        hit_components = app_state.components.get_components_at_point(world_x, world_y)
        
        if hit_components:
            # Select component
            component_id = hit_components[-1]  # Top-most component
            
            if e.meta or e.ctrl:
                # Multi-select
                self._dispatch_action(Action(
                    type=ActionType.SELECT_COMPONENT,
                    payload={"component_id": component_id, "multi": True}
                ))
            else:
                # Single select
                self._dispatch_action(Action(
                    type=ActionType.SELECT_COMPONENT,
                    payload={"component_id": component_id}
                ))
        else:
            # Start selection box or pan
            if e.shift:
                # Start selection box
                self.is_selecting = True
                self.selection_start = (world_x, world_y)
            else:
                # Start pan
                self.is_panning = True
                self.pan_start = (e.local_x, e.local_y)
                self.pan_start_viewport = (
                    self.viewport_manager.pan_x,
                    self.viewport_manager.pan_y
                )
    
    def handle_pointer_move(self, e: ft.HoverEvent) -> None:
        """Handle mouse/touch move"""
        if self.is_panning and hasattr(self, 'pan_start'):
            # Update pan
            delta_x = e.local_x - self.pan_start[0]
            delta_y = e.local_y - self.pan_start[1]
            
            new_pan_x = self.pan_start_viewport[0] - delta_x / self.viewport_manager.zoom
            new_pan_y = self.pan_start_viewport[1] - delta_y / self.viewport_manager.zoom
            
            self._dispatch_action(Action(
                type=ActionType.PAN_CANVAS,
                payload={"pan_x": new_pan_x, "pan_y": new_pan_y}
            ))
        
        elif self.is_selecting and self.selection_start:
            # Update selection box
            world_x, world_y = self.viewport_manager.screen_to_world(e.local_x, e.local_y)
            
            selection_box = {
                "x": min(self.selection_start[0], world_x),
                "y": min(self.selection_start[1], world_y),
                "width": abs(world_x - self.selection_start[0]),
                "height": abs(world_y - self.selection_start[1])
            }
            
            # Update selection state
            app_state = self.state_manager.get_state()
            app_state.selection.selection_box = selection_box
            self.needs_render = True
        
        else:
            # Hover detection
            world_x, world_y = self.viewport_manager.screen_to_world(e.local_x, e.local_y)
            app_state = self.state_manager.get_state()
            hit_components = app_state.components.get_components_at_point(world_x, world_y)
            
            new_hover_id = hit_components[-1] if hit_components else None
            
            if new_hover_id != self.hover_component_id:
                self.hover_component_id = new_hover_id
                self.needs_render = True
    
    def handle_pointer_up(self, e: ft.TapEvent) -> None:
        """Handle mouse/touch up"""
        if self.is_selecting and self.selection_start:
            # Complete selection box
            world_x, world_y = self.viewport_manager.screen_to_world(e.local_x, e.local_y)
            
            selection_box = {
                "x": min(self.selection_start[0], world_x),
                "y": min(self.selection_start[1], world_y),
                "width": abs(world_x - self.selection_start[0]),
                "height": abs(world_y - self.selection_start[1])
            }
            
            # Find components in selection box
            app_state = self.state_manager.get_state()
            selected_ids = app_state.components.get_components_in_selection(
                selection_box,
                fully_contained=not e.alt  # Alt for partial selection
            )
            
            # Update selection
            if selected_ids:
                for component_id in selected_ids:
                    self._dispatch_action(Action(
                        type=ActionType.SELECT_COMPONENT,
                        payload={"component_id": component_id, "multi": True}
                    ))
            
            # Clear selection box
            app_state.selection.selection_box = None
        
        # Reset interaction state
        self.is_panning = False
        self.is_selecting = False
        self.selection_start = None
    
    def handle_scroll(self, e: ft.ScrollEvent) -> None:
        """Handle scroll for zoom"""
        # Calculate zoom delta
        zoom_factor = 1.1 if e.scroll_delta_y < 0 else 0.9
        
        # Zoom with mouse position as focus
        self.viewport_manager.apply_zoom_factor(
            zoom_factor,
            e.local_x,
            e.local_y
        )
        
        # Update canvas state
        self._dispatch_action(Action(
            type=ActionType.ZOOM_CANVAS,
            payload={
                "zoom": self.viewport_manager.zoom,
                "pan_x": self.viewport_manager.pan_x,
                "pan_y": self.viewport_manager.pan_y
            }
        ))
    
    def handle_key_down(self, e: ft.KeyboardEvent) -> None:
        """Handle keyboard shortcuts"""
        # Zoom shortcuts
        if e.ctrl:
            if e.key == "0":
                # Reset zoom
                self.viewport_manager.reset()
                self._update_canvas_state()
            elif e.key == "=" or e.key == "+":
                # Zoom in
                self.viewport_manager.apply_zoom_factor(1.1, 
                    self.viewport_manager.screen_width / 2,
                    self.viewport_manager.screen_height / 2
                )
                self._update_canvas_state()
            elif e.key == "-":
                # Zoom out
                self.viewport_manager.apply_zoom_factor(0.9,
                    self.viewport_manager.screen_width / 2,
                    self.viewport_manager.screen_height / 2
                )
                self._update_canvas_state()
    
    def _dispatch_action(self, action: Action) -> None:
        """Dispatch action through state manager"""
        self.state_manager.dispatch(action)
    
    def _update_canvas_state(self) -> None:
        """Update canvas state from viewport"""
        self._dispatch_action(Action(
            type=ActionType.ZOOM_CANVAS,
            payload={
                "zoom": self.viewport_manager.zoom,
                "pan_x": self.viewport_manager.pan_x,
                "pan_y": self.viewport_manager.pan_y
            }
        ))
    
    # Public API
    
    def resize(self, width: int, height: int) -> None:
        """Handle canvas resize"""
        self.viewport_manager.resize(width, height)
        self.canvas_renderer.set_viewport_size(width, height)
        self.needs_render = True
        
        logger.info(f"Canvas resized to {width}x{height}")
    
    def fit_to_content(self) -> None:
        """Fit viewport to show all content"""
        app_state = self.state_manager.get_state()
        
        # Calculate bounds of all components
        all_bounds = None
        for component_data in app_state.components.component_map.values():
            # Calculate component bounds
            x = float(component_data.get('style', {}).get('left', 0))
            y = float(component_data.get('style', {}).get('top', 0))
            width = float(component_data.get('style', {}).get('width', 100))
            height = float(component_data.get('style', {}).get('height', 50))
            
            from managers.spatial_index import BoundingBox
            bounds = BoundingBox(x, y, width, height)
            
            if all_bounds is None:
                all_bounds = bounds
            else:
                # Expand to include this component
                min_x = min(all_bounds.x, bounds.x)
                min_y = min(all_bounds.y, bounds.y)
                max_x = max(all_bounds.x + all_bounds.width, bounds.x + bounds.width)
                max_y = max(all_bounds.y + all_bounds.height, bounds.y + bounds.height)
                
                all_bounds = BoundingBox(
                    min_x, min_y,
                    max_x - min_x,
                    max_y - min_y
                )
        
        if all_bounds:
            self.viewport_manager.fit_to_bounds(all_bounds, padding=50)
            self._update_canvas_state()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get rendering performance statistics"""
        return {
            "renderer": self.canvas_renderer.get_performance_stats(),
            "pipeline": self.render_pipeline.get_metrics(),
            "viewport": {
                "zoom": self.viewport_manager.get_zoom_percentage(),
                "position": (self.viewport_manager.pan_x, self.viewport_manager.pan_y)
            }
        }
    
    def toggle_grid(self, enabled: bool) -> None:
        """Toggle grid visibility"""
        self._dispatch_action(Action(
            type=ActionType.TOGGLE_GRID,
            payload={"enabled": enabled}
        ))
    
    def set_grid_size(self, size: int) -> None:
        """Set grid size"""
        app_state = self.state_manager.get_state()
        app_state.canvas.grid_size = size
        self.needs_render = True