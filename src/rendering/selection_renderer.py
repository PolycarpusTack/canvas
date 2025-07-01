"""
Selection Renderer for Canvas
Renders visual selection indicators, resize handles, and dimension labels
Following CLAUDE.md guidelines for accessible selection UI
"""

import flet as ft
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from models.component import Component
from managers.spatial_index import BoundingBox
from .viewport_manager import ViewportManager

logger = logging.getLogger(__name__)


class HandlePosition(Enum):
    """Resize handle positions"""
    NORTH_WEST = "nw"
    NORTH = "n"
    NORTH_EAST = "ne"
    EAST = "e"
    SOUTH_EAST = "se"
    SOUTH = "s"
    SOUTH_WEST = "sw"
    WEST = "w"
    ROTATION = "rotation"


@dataclass
class SelectionHandle:
    """Represents a selection handle"""
    position: HandlePosition
    x: float
    y: float
    cursor: str
    enabled: bool = True
    
    def get_screen_position(self, viewport: ViewportManager) -> Tuple[float, float]:
        """Convert to screen coordinates"""
        return viewport.world_to_screen(self.x, self.y)


class SelectionRenderer:
    """
    Renders selection UI elements
    CLAUDE.md #9.1: Accessible selection indicators
    CLAUDE.md #1.2: DRY - Reusable selection styles
    """
    
    def __init__(self):
        """Initialize selection renderer"""
        # Selection styling
        self.selection_color = "#5E6AD2"
        self.selection_width = 2
        self.handle_size = 8
        self.handle_color = "white"
        self.handle_border_color = "#5E6AD2"
        
        # Multi-selection styling
        self.multi_selection_color = "#5E6AD2"
        self.multi_selection_dash_pattern = [4, 4]
        
        # Dimension label styling
        self.dimension_bg_color = "#1F2937"
        self.dimension_text_color = "white"
        self.dimension_font_size = 11
        
        # Handle constraints
        self.handle_constraints = {
            HandlePosition.NORTH: ["height"],
            HandlePosition.SOUTH: ["height"],
            HandlePosition.EAST: ["width"],
            HandlePosition.WEST: ["width"],
            HandlePosition.NORTH_WEST: ["width", "height"],
            HandlePosition.NORTH_EAST: ["width", "height"],
            HandlePosition.SOUTH_WEST: ["width", "height"],
            HandlePosition.SOUTH_EAST: ["width", "height"],
            HandlePosition.ROTATION: ["rotation"]
        }
        
        # Callbacks for resize and rotation
        self.on_resize = None  # Callback: (component_id: str, new_bounds: dict) -> None
        self.on_rotate = None  # Callback: (component_id: str, angle: float) -> None
        
        # Internal state
        self._current_selection_id = None
        self._rotation_start_angle = None
        self._rotation_initial = None
        self._component_map = {}  # Cache for component lookups
        
        logger.info("SelectionRenderer initialized")
    
    def render_selection(
        self,
        selected_ids: List[str],
        component_map: Dict[str, Component],
        viewport: ViewportManager,
        zoom: float = 1.0
    ) -> ft.Control:
        """
        Render selection indicators for selected components
        Returns overlay control with all selection UI
        """
        if not selected_ids:
            return ft.Container()  # Empty selection
        
        # Cache component map for helper methods
        self._component_map = component_map
        self._current_selection_id = selected_ids[0] if len(selected_ids) == 1 else None
        
        overlays = []
        
        # Single selection - full UI
        if len(selected_ids) == 1:
            component_id = selected_ids[0]
            component = component_map.get(component_id)
            
            if component:
                bounds = self._get_component_bounds(component)
                
                # Selection outline
                overlays.append(self._create_selection_outline(bounds, viewport, zoom))
                
                # Resize handles
                handles = self._create_resize_handles(bounds, component, viewport, zoom)
                overlays.extend(handles)
                
                # Dimension labels
                dimension_label = self._create_dimension_label(bounds, viewport, zoom)
                if dimension_label:
                    overlays.append(dimension_label)
                
                # Rotation handle (if rotatable)
                if self._can_rotate(component):
                    rotation_handle = self._create_rotation_handle(bounds, viewport, zoom)
                    if rotation_handle:
                        overlays.append(rotation_handle)
        
        # Multi-selection - simplified UI
        else:
            # Calculate combined bounds
            bounds = self._calculate_multi_selection_bounds(selected_ids, component_map)
            if bounds:
                # Multi-selection outline
                overlays.append(self._create_multi_selection_outline(bounds, viewport, zoom))
                
                # Group resize handles (corners only)
                handles = self._create_group_handles(bounds, viewport, zoom)
                overlays.extend(handles)
                
                # Selection count badge
                count_badge = self._create_selection_count_badge(len(selected_ids), bounds, viewport, zoom)
                if count_badge:
                    overlays.append(count_badge)
        
        # Stack all overlays
        return ft.Stack(
            controls=overlays,
            clip_behavior=ft.ClipBehavior.NONE  # Allow handles outside bounds
        )
    
    def _get_component_bounds(self, component: Component) -> BoundingBox:
        """Get component bounding box in world coordinates"""
        # Parse dimensions
        x = float(component.style.left or 0)
        y = float(component.style.top or 0)
        
        # Parse width/height with defaults
        width_str = component.style.width or "100"
        height_str = component.style.height or "50"
        
        width = self._parse_dimension(width_str)
        height = self._parse_dimension(height_str)
        
        return BoundingBox(x=x, y=y, width=width, height=height)
    
    def _parse_dimension(self, value: str) -> float:
        """Parse dimension value (simplified)"""
        if isinstance(value, (int, float)):
            return float(value)
        
        # Remove units for now
        if isinstance(value, str):
            if value.endswith('px'):
                return float(value[:-2])
            try:
                return float(value)
            except ValueError:
                return 100  # Default
        
        return 100
    
    def _create_selection_outline(
        self,
        bounds: BoundingBox,
        viewport: ViewportManager,
        zoom: float
    ) -> ft.Control:
        """Create selection outline rectangle"""
        # Convert to screen coordinates
        x, y, w, h = viewport.world_to_screen_rect(
            bounds.x, bounds.y, bounds.width, bounds.height
        )
        
        # Create canvas for outline
        canvas = ft.Canvas(
            width=w + 4,  # Extra space for border
            height=h + 4,
            left=x - 2,
            top=y - 2
        )
        
        def draw_outline(e):
            """Draw selection outline"""
            canvas.stroke_paint.color = self.selection_color
            canvas.stroke_paint.stroke_width = self.selection_width
            canvas.draw_rect(1, 1, w, h)
        
        canvas.on_paint = draw_outline
        
        return canvas
    
    def _create_multi_selection_outline(
        self,
        bounds: BoundingBox,
        viewport: ViewportManager,
        zoom: float
    ) -> ft.Control:
        """Create dashed outline for multi-selection"""
        # Convert to screen coordinates
        x, y, w, h = viewport.world_to_screen_rect(
            bounds.x, bounds.y, bounds.width, bounds.height
        )
        
        # Create canvas for dashed outline
        canvas = ft.Canvas(
            width=w + 4,
            height=h + 4,
            left=x - 2,
            top=y - 2
        )
        
        def draw_dashed_outline(e):
            """Draw dashed selection outline"""
            canvas.stroke_paint.color = self.multi_selection_color
            canvas.stroke_paint.stroke_width = self.selection_width
            # Note: Flet Canvas doesn't support dash patterns directly
            # We'll use a solid line for now
            canvas.draw_rect(1, 1, w, h)
        
        canvas.on_paint = draw_dashed_outline
        
        return canvas
    
    def _create_resize_handles(
        self,
        bounds: BoundingBox,
        component: Component,
        viewport: ViewportManager,
        zoom: float
    ) -> List[ft.Control]:
        """Create resize handles for single selection"""
        handles = []
        
        # Calculate handle positions
        handle_data = [
            (HandlePosition.NORTH_WEST, bounds.x, bounds.y, "nw-resize"),
            (HandlePosition.NORTH, bounds.x + bounds.width/2, bounds.y, "n-resize"),
            (HandlePosition.NORTH_EAST, bounds.x + bounds.width, bounds.y, "ne-resize"),
            (HandlePosition.EAST, bounds.x + bounds.width, bounds.y + bounds.height/2, "e-resize"),
            (HandlePosition.SOUTH_EAST, bounds.x + bounds.width, bounds.y + bounds.height, "se-resize"),
            (HandlePosition.SOUTH, bounds.x + bounds.width/2, bounds.y + bounds.height, "s-resize"),
            (HandlePosition.SOUTH_WEST, bounds.x, bounds.y + bounds.height, "sw-resize"),
            (HandlePosition.WEST, bounds.x, bounds.y + bounds.height/2, "w-resize")
        ]
        
        for position, wx, wy, cursor in handle_data:
            # Check if handle should be enabled
            if not self._can_resize(component, position):
                continue
            
            # Convert to screen coordinates
            sx, sy = viewport.world_to_screen(wx, wy)
            
            # Create handle
            handle = self._create_handle(
                sx - self.handle_size/2,
                sy - self.handle_size/2,
                cursor,
                position,
                zoom
            )
            handles.append(handle)
        
        return handles
    
    def _create_group_handles(
        self,
        bounds: BoundingBox,
        viewport: ViewportManager,
        zoom: float
    ) -> List[ft.Control]:
        """Create simplified handles for group selection"""
        handles = []
        
        # Only corner handles for groups
        corner_data = [
            (HandlePosition.NORTH_WEST, bounds.x, bounds.y, "nw-resize"),
            (HandlePosition.NORTH_EAST, bounds.x + bounds.width, bounds.y, "ne-resize"),
            (HandlePosition.SOUTH_EAST, bounds.x + bounds.width, bounds.y + bounds.height, "se-resize"),
            (HandlePosition.SOUTH_WEST, bounds.x, bounds.y + bounds.height, "sw-resize")
        ]
        
        for position, wx, wy, cursor in corner_data:
            # Convert to screen coordinates
            sx, sy = viewport.world_to_screen(wx, wy)
            
            # Create handle
            handle = self._create_handle(
                sx - self.handle_size/2,
                sy - self.handle_size/2,
                cursor,
                position,
                zoom
            )
            handles.append(handle)
        
        return handles
    
    def _create_handle(
        self,
        x: float,
        y: float,
        cursor: str,
        position: HandlePosition,
        zoom: float
    ) -> ft.Control:
        """Create individual resize handle"""
        handle_size = self.handle_size * min(zoom, 1.5)  # Scale with zoom but cap
        
        return ft.Container(
            left=x,
            top=y,
            width=handle_size,
            height=handle_size,
            bgcolor=self.handle_color,
            border=ft.border.all(1, self.handle_border_color),
            border_radius=1,
            on_hover=lambda e: self._on_handle_hover(e, cursor),
            on_pan_start=lambda e: self._on_resize_start(e, position),
            on_pan_update=lambda e: self._on_resize_update(e, position),
            on_pan_end=lambda e: self._on_resize_end(e, position),
            tooltip=f"Resize {position.value}",
            # Accessibility
            semantics_label=f"Resize handle {position.value}"
        )
    
    def _create_dimension_label(
        self,
        bounds: BoundingBox,
        viewport: ViewportManager,
        zoom: float
    ) -> Optional[ft.Control]:
        """Create dimension label showing size"""
        # Don't show if too small
        if bounds.width < 50 or bounds.height < 30:
            return None
        
        # Position above component
        wx = bounds.x + bounds.width / 2
        wy = bounds.y - 25
        
        # Convert to screen coordinates
        sx, sy = viewport.world_to_screen(wx, wy)
        
        # Format dimensions
        width = int(bounds.width)
        height = int(bounds.height)
        label_text = f"{width} × {height}"
        
        return ft.Container(
            content=ft.Text(
                label_text,
                size=self.dimension_font_size,
                color=self.dimension_text_color,
                weight=ft.FontWeight.W_500
            ),
            bgcolor=self.dimension_bg_color,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=4,
            left=sx - 40,  # Approximate centering
            top=sy
        )
    
    def _create_rotation_handle(
        self,
        bounds: BoundingBox,
        viewport: ViewportManager,
        zoom: float
    ) -> Optional[ft.Control]:
        """Create rotation handle above component"""
        # Position above component
        wx = bounds.x + bounds.width / 2
        wy = bounds.y - 40
        
        # Convert to screen coordinates
        sx, sy = viewport.world_to_screen(wx, wy)
        
        return ft.Container(
            content=ft.Icon(
                ft.Icons.ROTATE_90_DEGREES_CCW,
                size=16,
                color=self.selection_color
            ),
            width=24,
            height=24,
            bgcolor="white",
            border=ft.border.all(1, self.selection_color),
            border_radius=12,
            left=sx - 12,
            top=sy - 12,
            on_hover=lambda e: self._on_handle_hover(e, "grab"),
            on_pan_start=lambda e: self._on_rotation_start(e),
            on_pan_update=lambda e: self._on_rotation_update(e),
            on_pan_end=lambda e: self._on_rotation_end(e),
            tooltip="Rotate",
            semantics_label="Rotation handle"
        )
    
    def _create_selection_count_badge(
        self,
        count: int,
        bounds: BoundingBox,
        viewport: ViewportManager,
        zoom: float
    ) -> Optional[ft.Control]:
        """Create badge showing number of selected items"""
        # Position at top-left of selection
        wx = bounds.x
        wy = bounds.y - 25
        
        # Convert to screen coordinates
        sx, sy = viewport.world_to_screen(wx, wy)
        
        return ft.Container(
            content=ft.Text(
                f"{count} selected",
                size=12,
                color="white",
                weight=ft.FontWeight.W_500
            ),
            bgcolor=self.selection_color,
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            border_radius=12,
            left=sx,
            top=sy
        )
    
    def _calculate_multi_selection_bounds(
        self,
        selected_ids: List[str],
        component_map: Dict[str, Component]
    ) -> Optional[BoundingBox]:
        """Calculate combined bounds for multiple components"""
        if not selected_ids:
            return None
        
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for component_id in selected_ids:
            component = component_map.get(component_id)
            if not component:
                continue
            
            bounds = self._get_component_bounds(component)
            min_x = min(min_x, bounds.x)
            min_y = min(min_y, bounds.y)
            max_x = max(max_x, bounds.x + bounds.width)
            max_y = max(max_y, bounds.y + bounds.height)
        
        if min_x == float('inf'):
            return None
        
        return BoundingBox(
            x=min_x,
            y=min_y,
            width=max_x - min_x,
            height=max_y - min_y
        )
    
    def _can_resize(self, component: Component, position: HandlePosition) -> bool:
        """Check if component can be resized in given direction"""
        # Check if component is locked
        if component.editor_locked:
            return False
        
        # Check specific constraints
        constraints = self.handle_constraints.get(position, [])
        
        # For now, allow all resizing
        # Future: Check component-specific constraints
        return True
    
    def _can_rotate(self, component: Component) -> bool:
        """Check if component can be rotated"""
        if component.editor_locked:
            return False
        
        # Future: Check component type and rotation support
        return False  # Disabled for now
    
    # Event handlers (placeholders for interaction system)
    
    def _on_handle_hover(self, e: ft.HoverEvent, cursor: str) -> None:
        """Handle hover over resize handle"""
        if e.data == "true":
            # Future: Set cursor
            logger.debug(f"Handle hover: {cursor}")
    
    def _on_resize_start(self, e: ft.DragStartEvent, position: HandlePosition) -> None:
        """Handle resize start"""
        logger.debug(f"Resize start: {position.value}")
    
    def _on_resize_update(self, e: ft.DragUpdateEvent, position: HandlePosition) -> None:
        """Handle resize update"""
        try:
            if not self.on_resize or not self._current_selection_id:
                return
            
            # Calculate delta movement
            delta_x = e.delta_x
            delta_y = e.delta_y
            
            # Get current component bounds
            component = self._get_component_by_id(self._current_selection_id)
            if not component:
                return
            
            bounds = self._get_component_bounds(component)
            new_x = bounds.x
            new_y = bounds.y
            new_width = bounds.width
            new_height = bounds.height
            
            # Apply resize based on handle position
            if position in [HandlePosition.WEST, HandlePosition.NORTH_WEST, HandlePosition.SOUTH_WEST]:
                # Left side resize - move x and adjust width
                new_x += delta_x
                new_width -= delta_x
            
            if position in [HandlePosition.EAST, HandlePosition.NORTH_EAST, HandlePosition.SOUTH_EAST]:
                # Right side resize - adjust width
                new_width += delta_x
            
            if position in [HandlePosition.NORTH, HandlePosition.NORTH_WEST, HandlePosition.NORTH_EAST]:
                # Top side resize - move y and adjust height
                new_y += delta_y
                new_height -= delta_y
            
            if position in [HandlePosition.SOUTH, HandlePosition.SOUTH_WEST, HandlePosition.SOUTH_EAST]:
                # Bottom side resize - adjust height
                new_height += delta_y
            
            # Apply minimum size constraints
            min_size = 20
            if new_width < min_size:
                if position in [HandlePosition.WEST, HandlePosition.NORTH_WEST, HandlePosition.SOUTH_WEST]:
                    new_x = bounds.x + bounds.width - min_size
                new_width = min_size
            
            if new_height < min_size:
                if position in [HandlePosition.NORTH, HandlePosition.NORTH_WEST, HandlePosition.NORTH_EAST]:
                    new_y = bounds.y + bounds.height - min_size
                new_height = min_size
            
            # Notify resize callback with new bounds
            self.on_resize(
                self._current_selection_id,
                {
                    'x': new_x,
                    'y': new_y,
                    'width': new_width,
                    'height': new_height
                }
            )
            
            # Update visual feedback if needed
            if hasattr(self, '_update_selection_visuals'):
                self._update_selection_visuals()
                
        except Exception as ex:
            logger.error(f"Error in resize update: {ex}")
    
    def _on_resize_end(self, e: ft.DragEndEvent, position: HandlePosition) -> None:
        """Handle resize end"""
        logger.debug(f"Resize end: {position.value}")
    
    def _on_rotation_start(self, e: ft.DragStartEvent) -> None:
        """Handle rotation start"""
        logger.debug("Rotation start")
    
    def _on_rotation_update(self, e: ft.DragUpdateEvent) -> None:
        """Handle rotation update"""
        try:
            if not self.on_rotate or not self._current_selection_id:
                return
            
            # Get component and its center point
            component = self._get_component_by_id(self._current_selection_id)
            if not component:
                return
            
            bounds = self._get_component_bounds(component)
            center_x = bounds.x + bounds.width / 2
            center_y = bounds.y + bounds.height / 2
            
            # Calculate angle from center to current mouse position
            # Note: This is simplified - in practice you'd need viewport coordinates
            mouse_x = e.global_x
            mouse_y = e.global_y
            
            # Calculate angle in radians then convert to degrees
            import math
            angle_rad = math.atan2(mouse_y - center_y, mouse_x - center_x)
            angle_deg = math.degrees(angle_rad)
            
            # Normalize angle to 0-360 range
            angle_deg = (angle_deg + 360) % 360
            
            # Apply snap to 15-degree increments if shift is held
            if hasattr(e, 'shift_key') and e.shift_key:
                angle_deg = round(angle_deg / 15) * 15
            
            # Get current rotation and calculate delta
            current_rotation = getattr(component.style, 'transform_rotate', 0)
            if isinstance(current_rotation, str):
                # Parse rotation from string like "rotate(45deg)"
                import re
                match = re.search(r'rotate\(([-\d.]+)deg\)', current_rotation)
                if match:
                    current_rotation = float(match.group(1))
                else:
                    current_rotation = 0
            
            # Store initial angle on first update
            if not hasattr(self, '_rotation_start_angle'):
                self._rotation_start_angle = angle_deg
                self._rotation_initial = current_rotation
            
            # Calculate rotation delta from start
            delta_rotation = angle_deg - self._rotation_start_angle
            new_rotation = self._rotation_initial + delta_rotation
            
            # Normalize to 0-360 range
            new_rotation = new_rotation % 360
            
            # Notify rotation callback
            self.on_rotate(
                self._current_selection_id,
                new_rotation
            )
            
            # Update visual feedback
            if hasattr(self, '_update_rotation_visual'):
                self._update_rotation_visual(new_rotation)
                
        except Exception as ex:
            logger.error(f"Error in rotation update: {ex}")
    
    def _on_rotation_end(self, e: ft.DragEndEvent) -> None:
        """Handle rotation end"""
        logger.debug("Rotation end")
        # Clear rotation tracking state
        self._rotation_start_angle = None
        self._rotation_initial = None
    
    def _get_component_by_id(self, component_id: str) -> Optional[Component]:
        """Get component by ID from cached map"""
        return self._component_map.get(component_id)
    
    # Accessibility helpers
    
    def announce_selection(self, selected_ids: List[str], component_map: Dict[str, Component]) -> str:
        """
        Generate screen reader announcement for selection
        CLAUDE.md #9.4: Screen reader announcements
        """
        if not selected_ids:
            return "No components selected"
        
        if len(selected_ids) == 1:
            component = component_map.get(selected_ids[0])
            if component:
                return f"Selected {component.type} component: {component.name or component.id}"
            return "Selected component"
        
        return f"Selected {len(selected_ids)} components"
    
    def get_handle_description(self, position: HandlePosition) -> str:
        """Get accessible description for handle"""
        descriptions = {
            HandlePosition.NORTH: "top edge",
            HandlePosition.SOUTH: "bottom edge",
            HandlePosition.EAST: "right edge",
            HandlePosition.WEST: "left edge",
            HandlePosition.NORTH_WEST: "top-left corner",
            HandlePosition.NORTH_EAST: "top-right corner",
            HandlePosition.SOUTH_WEST: "bottom-left corner",
            HandlePosition.SOUTH_EAST: "bottom-right corner",
            HandlePosition.ROTATION: "rotation"
        }
        
        return f"Drag to resize {descriptions.get(position, 'component')}"