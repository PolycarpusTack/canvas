"""
Viewport Manager for Canvas Rendering
Handles viewport transformations, culling bounds, and coordinate systems
Following CLAUDE.md guidelines for performance optimization
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import logging
import math

from managers.spatial_index import BoundingBox

logger = logging.getLogger(__name__)


@dataclass
class ViewportBounds:
    """Viewport bounds in world coordinates"""
    left: float
    top: float
    right: float
    bottom: float
    
    @property
    def width(self) -> float:
        return self.right - self.left
    
    @property
    def height(self) -> float:
        return self.bottom - self.top
    
    def to_bounding_box(self) -> BoundingBox:
        """Convert to spatial index BoundingBox"""
        return BoundingBox(
            x=self.left,
            y=self.top,
            width=self.width,
            height=self.height
        )
    
    def expand(self, margin: float) -> 'ViewportBounds':
        """Expand bounds by margin on all sides"""
        return ViewportBounds(
            left=self.left - margin,
            top=self.top - margin,
            right=self.right + margin,
            bottom=self.bottom + margin
        )
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within bounds"""
        return self.left <= x <= self.right and self.top <= y <= self.bottom
    
    def intersects(self, bbox: BoundingBox) -> bool:
        """Check if bounds intersect with bounding box"""
        return not (
            bbox.x + bbox.width < self.left or
            bbox.x > self.right or
            bbox.y + bbox.height < self.top or
            bbox.y > self.bottom
        )


class ViewportManager:
    """
    Manages viewport state and coordinate transformations
    CLAUDE.md #1.5: Efficient viewport calculations
    CLAUDE.md #8.3: Proper coordinate system handling
    """
    
    def __init__(self, width: int = 1200, height: int = 800):
        """Initialize viewport with screen dimensions"""
        self.screen_width = width
        self.screen_height = height
        
        # Viewport state
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        
        # Zoom constraints
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.zoom_step = 0.1
        
        # Pan constraints (optional)
        self.min_pan_x: Optional[float] = None
        self.max_pan_x: Optional[float] = None
        self.min_pan_y: Optional[float] = None
        self.max_pan_y: Optional[float] = None
        
        # Performance optimization
        self._cached_bounds: Optional[ViewportBounds] = None
        self._cached_transform_matrix: Optional[Tuple[float, ...]] = None
        self._cache_valid = False
        
        logger.info(f"ViewportManager initialized: {width}x{height}")
    
    def update(self, zoom: float, pan_x: float, pan_y: float) -> None:
        """Update viewport state with validation"""
        # Validate and constrain zoom
        new_zoom = max(self.min_zoom, min(self.max_zoom, zoom))
        
        # Validate and constrain pan
        new_pan_x = pan_x
        new_pan_y = pan_y
        
        if self.min_pan_x is not None:
            new_pan_x = max(self.min_pan_x, new_pan_x)
        if self.max_pan_x is not None:
            new_pan_x = min(self.max_pan_x, new_pan_x)
        if self.min_pan_y is not None:
            new_pan_y = max(self.min_pan_y, new_pan_y)
        if self.max_pan_y is not None:
            new_pan_y = min(self.max_pan_y, new_pan_y)
        
        # Check if state actually changed
        if (self.zoom != new_zoom or 
            self.pan_x != new_pan_x or 
            self.pan_y != new_pan_y):
            
            self.zoom = new_zoom
            self.pan_x = new_pan_x
            self.pan_y = new_pan_y
            self._invalidate_cache()
            
            logger.debug(f"Viewport updated: zoom={new_zoom:.2f}, pan=({new_pan_x:.1f}, {new_pan_y:.1f})")
    
    def resize(self, width: int, height: int) -> None:
        """Update screen dimensions"""
        if self.screen_width != width or self.screen_height != height:
            self.screen_width = width
            self.screen_height = height
            self._invalidate_cache()
            logger.info(f"Viewport resized: {width}x{height}")
    
    def get_bounds(self) -> ViewportBounds:
        """
        Get current viewport bounds in world coordinates
        Used for culling invisible components
        """
        if not self._cache_valid or self._cached_bounds is None:
            self._cached_bounds = self._calculate_bounds()
            self._cache_valid = True
        
        return self._cached_bounds
    
    def _calculate_bounds(self) -> ViewportBounds:
        """Calculate viewport bounds in world space"""
        # Calculate visible area in world coordinates
        # Screen space: (0, 0) to (screen_width, screen_height)
        # World space: Apply inverse transform
        
        # Top-left corner in world space
        left = self.pan_x
        top = self.pan_y
        
        # Bottom-right corner in world space
        right = self.pan_x + (self.screen_width / self.zoom)
        bottom = self.pan_y + (self.screen_height / self.zoom)
        
        return ViewportBounds(left, top, right, bottom)
    
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """
        Transform world coordinates to screen coordinates
        Used for rendering components at correct screen position
        """
        screen_x = (world_x - self.pan_x) * self.zoom
        screen_y = (world_y - self.pan_y) * self.zoom
        return (screen_x, screen_y)
    
    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """
        Transform screen coordinates to world coordinates
        Used for mouse interactions and hit testing
        """
        world_x = (screen_x / self.zoom) + self.pan_x
        world_y = (screen_y / self.zoom) + self.pan_y
        return (world_x, world_y)
    
    def world_to_screen_size(self, world_size: float) -> float:
        """Transform a size value from world to screen space"""
        return world_size * self.zoom
    
    def screen_to_world_size(self, screen_size: float) -> float:
        """Transform a size value from screen to world space"""
        return screen_size / self.zoom
    
    def world_to_screen_rect(
        self, 
        x: float, 
        y: float, 
        width: float, 
        height: float
    ) -> Tuple[float, float, float, float]:
        """Transform a rectangle from world to screen coordinates"""
        screen_x, screen_y = self.world_to_screen(x, y)
        screen_width = self.world_to_screen_size(width)
        screen_height = self.world_to_screen_size(height)
        return (screen_x, screen_y, screen_width, screen_height)
    
    def get_transform_matrix(self) -> Tuple[float, float, float, float, float, float]:
        """
        Get transformation matrix for canvas operations
        Returns (scale_x, skew_x, trans_x, skew_y, scale_y, trans_y)
        """
        if not self._cache_valid or self._cached_transform_matrix is None:
            self._cached_transform_matrix = (
                self.zoom,          # scale_x
                0,                  # skew_x
                -self.pan_x * self.zoom,  # trans_x
                0,                  # skew_y
                self.zoom,          # scale_y
                -self.pan_y * self.zoom   # trans_y
            )
        
        return self._cached_transform_matrix
    
    def apply_zoom(self, delta: float, focus_x: float, focus_y: float) -> None:
        """
        Apply zoom with a focal point
        Keeps the point under the mouse cursor stationary
        """
        # Calculate new zoom
        old_zoom = self.zoom
        new_zoom = max(self.min_zoom, min(self.max_zoom, self.zoom + delta))
        
        if new_zoom == old_zoom:
            return
        
        # Convert focus point to world coordinates before zoom
        world_focus_x, world_focus_y = self.screen_to_world(focus_x, focus_y)
        
        # Update zoom
        self.zoom = new_zoom
        
        # Calculate new pan to keep focus point stationary
        self.pan_x = world_focus_x - (focus_x / new_zoom)
        self.pan_y = world_focus_y - (focus_y / new_zoom)
        
        self._invalidate_cache()
        
        logger.debug(f"Zoom applied: {old_zoom:.2f} -> {new_zoom:.2f} at ({focus_x}, {focus_y})")
    
    def apply_zoom_factor(self, factor: float, focus_x: float, focus_y: float) -> None:
        """Apply zoom by multiplication factor (e.g., 1.1 for 10% zoom in)"""
        new_zoom = self.zoom * factor
        delta = new_zoom - self.zoom
        self.apply_zoom(delta, focus_x, focus_y)
    
    def pan_by(self, delta_x: float, delta_y: float) -> None:
        """Pan viewport by delta in screen coordinates"""
        # Convert screen delta to world delta
        world_delta_x = delta_x / self.zoom
        world_delta_y = delta_y / self.zoom
        
        # Update pan with constraints
        new_pan_x = self.pan_x - world_delta_x
        new_pan_y = self.pan_y - world_delta_y
        
        if self.min_pan_x is not None:
            new_pan_x = max(self.min_pan_x, new_pan_x)
        if self.max_pan_x is not None:
            new_pan_x = min(self.max_pan_x, new_pan_x)
        if self.min_pan_y is not None:
            new_pan_y = max(self.min_pan_y, new_pan_y)
        if self.max_pan_y is not None:
            new_pan_y = min(self.max_pan_y, new_pan_y)
        
        if self.pan_x != new_pan_x or self.pan_y != new_pan_y:
            self.pan_x = new_pan_x
            self.pan_y = new_pan_y
            self._invalidate_cache()
    
    def center_on(self, world_x: float, world_y: float) -> None:
        """Center viewport on a world coordinate"""
        # Calculate pan to center the given point
        self.pan_x = world_x - (self.screen_width / 2 / self.zoom)
        self.pan_y = world_y - (self.screen_height / 2 / self.zoom)
        self._invalidate_cache()
    
    def fit_to_bounds(self, bbox: BoundingBox, padding: float = 50) -> None:
        """Adjust viewport to fit the given bounding box"""
        # Add padding
        padded_width = bbox.width + (padding * 2)
        padded_height = bbox.height + (padding * 2)
        
        # Calculate zoom to fit
        zoom_x = self.screen_width / padded_width
        zoom_y = self.screen_height / padded_height
        new_zoom = min(zoom_x, zoom_y, self.max_zoom)
        
        # Update zoom
        self.zoom = new_zoom
        
        # Center on bounding box
        center_x = bbox.x + bbox.width / 2
        center_y = bbox.y + bbox.height / 2
        self.center_on(center_x, center_y)
        
        logger.info(f"Viewport fitted to bounds: zoom={new_zoom:.2f}")
    
    def reset(self) -> None:
        """Reset viewport to default state"""
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._invalidate_cache()
        logger.info("Viewport reset to default")
    
    def _invalidate_cache(self) -> None:
        """Invalidate cached calculations"""
        self._cache_valid = False
        self._cached_bounds = None
        self._cached_transform_matrix = None
    
    def get_visible_area_percentage(self, bbox: BoundingBox) -> float:
        """
        Calculate what percentage of a bounding box is visible
        Useful for LOD (Level of Detail) decisions
        """
        viewport = self.get_bounds()
        
        # Calculate intersection
        intersect_left = max(bbox.x, viewport.left)
        intersect_top = max(bbox.y, viewport.top)
        intersect_right = min(bbox.x + bbox.width, viewport.right)
        intersect_bottom = min(bbox.y + bbox.height, viewport.bottom)
        
        # Check if there's an intersection
        if intersect_left >= intersect_right or intersect_top >= intersect_bottom:
            return 0.0
        
        # Calculate intersection area
        intersect_width = intersect_right - intersect_left
        intersect_height = intersect_bottom - intersect_top
        intersect_area = intersect_width * intersect_height
        
        # Calculate percentage
        bbox_area = bbox.width * bbox.height
        if bbox_area == 0:
            return 0.0
        
        return intersect_area / bbox_area
    
    def is_fully_visible(self, bbox: BoundingBox) -> bool:
        """Check if bounding box is fully visible in viewport"""
        viewport = self.get_bounds()
        return (
            bbox.x >= viewport.left and
            bbox.y >= viewport.top and
            bbox.x + bbox.width <= viewport.right and
            bbox.y + bbox.height <= viewport.bottom
        )
    
    def get_zoom_percentage(self) -> int:
        """Get zoom level as percentage (100% = 1.0)"""
        return int(self.zoom * 100)
    
    def set_zoom_percentage(self, percentage: int) -> None:
        """Set zoom level from percentage"""
        new_zoom = percentage / 100.0
        center_x = self.screen_width / 2
        center_y = self.screen_height / 2
        delta = new_zoom - self.zoom
        self.apply_zoom(delta, center_x, center_y)