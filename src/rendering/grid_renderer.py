"""
Grid Renderer for Canvas
Renders grid overlay, rulers, and alignment guides efficiently
Following CLAUDE.md guidelines for performance optimization
"""

import flet as ft
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
import logging
import math

from managers.spatial_index import BoundingBox
from .viewport_manager import ViewportBounds

logger = logging.getLogger(__name__)


@dataclass
class GridConfig:
    """Grid configuration settings"""
    size: int = 20  # Grid cell size in pixels
    minor_color: str = "#E5E7EB"  # Gray-200
    major_color: str = "#D1D5DB"  # Gray-300
    major_interval: int = 5  # Major line every N cells
    opacity: float = 0.5
    show_rulers: bool = False
    ruler_bg_color: str = "#F9FAFB"
    ruler_text_color: str = "#6B7280"
    ruler_size: int = 30


class GridPainter:
    """
    Custom painter for efficient grid rendering
    CLAUDE.md #1.5: Optimize grid rendering performance
    """
    
    def __init__(self, config: GridConfig, viewport_bounds: ViewportBounds, zoom: float):
        """Initialize grid painter with configuration"""
        self.config = config
        self.viewport_bounds = viewport_bounds
        self.zoom = zoom
        
        # Calculate visible grid range
        self.start_x = int(viewport_bounds.left / config.size) * config.size
        self.start_y = int(viewport_bounds.top / config.size) * config.size
        self.end_x = math.ceil(viewport_bounds.right / config.size) * config.size
        self.end_y = math.ceil(viewport_bounds.bottom / config.size) * config.size
    
    def paint(self, canvas: ft.Canvas, size: ft.Size) -> None:
        """
        Paint grid lines efficiently
        Only draws visible lines
        """
        # Save canvas state
        canvas.save()
        
        # Apply viewport transform
        canvas.translate(
            -self.viewport_bounds.left * self.zoom,
            -self.viewport_bounds.top * self.zoom
        )
        canvas.scale(self.zoom, self.zoom)
        
        # Draw minor grid lines
        self._draw_minor_lines(canvas, size)
        
        # Draw major grid lines
        self._draw_major_lines(canvas, size)
        
        # Restore canvas state
        canvas.restore()
    
    def _draw_minor_lines(self, canvas: ft.Canvas, size: ft.Size) -> None:
        """Draw minor grid lines"""
        canvas.stroke_paint.color = self.config.minor_color
        canvas.stroke_paint.stroke_width = 0.5
        
        # Vertical lines
        x = self.start_x
        while x <= self.end_x:
            if x % (self.config.size * self.config.major_interval) != 0:
                canvas.draw_line(x, self.start_y, x, self.end_y)
            x += self.config.size
        
        # Horizontal lines
        y = self.start_y
        while y <= self.end_y:
            if y % (self.config.size * self.config.major_interval) != 0:
                canvas.draw_line(self.start_x, y, self.end_x, y)
            y += self.config.size
    
    def _draw_major_lines(self, canvas: ft.Canvas, size: ft.Size) -> None:
        """Draw major grid lines"""
        canvas.stroke_paint.color = self.config.major_color
        canvas.stroke_paint.stroke_width = 1
        
        major_size = self.config.size * self.config.major_interval
        
        # Vertical lines
        x = int(self.start_x / major_size) * major_size
        while x <= self.end_x:
            canvas.draw_line(x, self.start_y, x, self.end_y)
            x += major_size
        
        # Horizontal lines
        y = int(self.start_y / major_size) * major_size
        while y <= self.end_y:
            canvas.draw_line(self.start_x, y, self.end_x, y)
            y += major_size


class GridRenderer:
    """
    Renders grid overlay and related visual helpers
    CLAUDE.md #1.5: Performance-optimized grid rendering
    CLAUDE.md #12.3: Grid performance metrics
    """
    
    def __init__(self):
        """Initialize grid renderer"""
        self.config = GridConfig()
        
        # Cache for performance
        self._grid_cache: Dict[str, ft.Control] = {}
        self._cache_size_limit = 10
        
        # Performance tracking
        self.metrics = {
            "render_count": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        logger.info("GridRenderer initialized")
    
    def render_grid(
        self,
        viewport: ViewportBounds,
        grid_size: int = 20,
        zoom: float = 1.0,
        show_rulers: bool = False
    ) -> ft.Control:
        """
        Render grid overlay
        Uses caching for performance
        """
        # Update config
        self.config.size = grid_size
        self.config.show_rulers = show_rulers
        
        # Check cache
        cache_key = f"{viewport.width}x{viewport.height}:{grid_size}:{zoom}"
        
        if cache_key in self._grid_cache and not show_rulers:
            self.metrics["cache_hits"] += 1
            return self._grid_cache[cache_key]
        
        self.metrics["cache_misses"] += 1
        self.metrics["render_count"] += 1
        
        # Create grid overlay
        overlays = []
        
        # Grid canvas
        grid_canvas = self._create_grid_canvas(viewport, zoom)
        overlays.append(grid_canvas)
        
        # Rulers (if enabled)
        if show_rulers:
            ruler_overlays = self._create_rulers(viewport, zoom)
            overlays.extend(ruler_overlays)
        
        # Stack overlays
        grid_overlay = ft.Stack(
            controls=overlays,
            width=viewport.width * zoom,
            height=viewport.height * zoom
        )
        
        # Cache result (only if rulers not shown)
        if not show_rulers:
            self._update_cache(cache_key, grid_overlay)
        
        return grid_overlay
    
    def _create_grid_canvas(
        self,
        viewport: ViewportBounds,
        zoom: float
    ) -> ft.Control:
        """Create canvas with grid lines"""
        # Create custom paint canvas
        canvas = ft.Canvas(
            width=viewport.width * zoom,
            height=viewport.height * zoom,
            content=GridPainter(self.config, viewport, zoom),
            opacity=self.config.opacity
        )
        
        return canvas
    
    def _create_rulers(
        self,
        viewport: ViewportBounds,
        zoom: float
    ) -> List[ft.Control]:
        """Create ruler overlays"""
        rulers = []
        
        # Horizontal ruler (top)
        h_ruler = self._create_horizontal_ruler(viewport, zoom)
        rulers.append(h_ruler)
        
        # Vertical ruler (left)
        v_ruler = self._create_vertical_ruler(viewport, zoom)
        rulers.append(v_ruler)
        
        # Corner square
        corner = ft.Container(
            width=self.config.ruler_size,
            height=self.config.ruler_size,
            bgcolor=self.config.ruler_bg_color,
            border=ft.border.all(1, "#E5E7EB")
        )
        rulers.append(corner)
        
        return rulers
    
    def _create_horizontal_ruler(
        self,
        viewport: ViewportBounds,
        zoom: float
    ) -> ft.Control:
        """Create horizontal ruler with measurements"""
        ruler_width = viewport.width * zoom
        
        # Create ruler canvas
        ruler = ft.Container(
            width=ruler_width,
            height=self.config.ruler_size,
            bgcolor=self.config.ruler_bg_color,
            border=ft.border.only(bottom=ft.BorderSide(1, "#E5E7EB")),
            left=self.config.ruler_size,  # Offset for vertical ruler
            content=self._create_ruler_marks_horizontal(viewport, zoom)
        )
        
        return ruler
    
    def _create_vertical_ruler(
        self,
        viewport: ViewportBounds,
        zoom: float
    ) -> ft.Control:
        """Create vertical ruler with measurements"""
        ruler_height = viewport.height * zoom
        
        # Create ruler canvas
        ruler = ft.Container(
            width=self.config.ruler_size,
            height=ruler_height,
            bgcolor=self.config.ruler_bg_color,
            border=ft.border.only(right=ft.BorderSide(1, "#E5E7EB")),
            top=self.config.ruler_size,  # Offset for horizontal ruler
            content=self._create_ruler_marks_vertical(viewport, zoom)
        )
        
        return ruler
    
    def _create_ruler_marks_horizontal(
        self,
        viewport: ViewportBounds,
        zoom: float
    ) -> ft.Control:
        """Create horizontal ruler markings"""
        marks = []
        
        # Calculate mark interval
        interval = self._calculate_ruler_interval(zoom)
        
        # Start position in world coordinates
        start = int(viewport.left / interval) * interval
        end = viewport.right
        
        x = start
        while x <= end:
            # Convert to screen position
            screen_x = (x - viewport.left) * zoom
            
            # Create mark
            mark_height = 10 if x % (interval * 5) == 0 else 5
            
            mark = ft.Container(
                width=1,
                height=mark_height,
                bgcolor=self.config.ruler_text_color,
                left=screen_x,
                bottom=0
            )
            marks.append(mark)
            
            # Add label for major marks
            if x % (interval * 5) == 0:
                label = ft.Text(
                    str(int(x)),
                    size=10,
                    color=self.config.ruler_text_color,
                    left=screen_x + 2,
                    top=2
                )
                marks.append(label)
            
            x += interval
        
        return ft.Stack(marks)
    
    def _create_ruler_marks_vertical(
        self,
        viewport: ViewportBounds,
        zoom: float
    ) -> ft.Control:
        """Create vertical ruler markings"""
        marks = []
        
        # Calculate mark interval
        interval = self._calculate_ruler_interval(zoom)
        
        # Start position in world coordinates
        start = int(viewport.top / interval) * interval
        end = viewport.bottom
        
        y = start
        while y <= end:
            # Convert to screen position
            screen_y = (y - viewport.top) * zoom
            
            # Create mark
            mark_width = 10 if y % (interval * 5) == 0 else 5
            
            mark = ft.Container(
                width=mark_width,
                height=1,
                bgcolor=self.config.ruler_text_color,
                right=0,
                top=screen_y
            )
            marks.append(mark)
            
            # Add label for major marks
            if y % (interval * 5) == 0:
                label = ft.Text(
                    str(int(y)),
                    size=10,
                    color=self.config.ruler_text_color,
                    left=2,
                    top=screen_y + 2
                )
                marks.append(label)
            
            y += interval
        
        return ft.Stack(marks)
    
    def _calculate_ruler_interval(self, zoom: float) -> int:
        """Calculate appropriate ruler interval based on zoom"""
        # Base interval
        base_interval = 50
        
        # Adjust based on zoom
        if zoom < 0.5:
            return base_interval * 4
        elif zoom < 1.0:
            return base_interval * 2
        elif zoom > 2.0:
            return base_interval // 2
        elif zoom > 4.0:
            return base_interval // 4
        
        return base_interval
    
    def _update_cache(self, key: str, control: ft.Control) -> None:
        """Update grid cache with LRU eviction"""
        self._grid_cache[key] = control
        
        # Evict oldest if cache too large
        if len(self._grid_cache) > self._cache_size_limit:
            oldest_key = next(iter(self._grid_cache))
            del self._grid_cache[oldest_key]
    
    def render_alignment_guides(
        self,
        active_bounds: BoundingBox,
        target_bounds: List[BoundingBox],
        viewport: ViewportBounds,
        zoom: float
    ) -> ft.Control:
        """
        Render smart alignment guides during drag operations
        Shows when components align with others
        """
        guides = []
        
        # Check for horizontal alignment
        h_guides = self._find_horizontal_alignments(active_bounds, target_bounds)
        for guide_y, guide_type in h_guides:
            guide = self._create_horizontal_guide(guide_y, viewport, zoom, guide_type)
            guides.append(guide)
        
        # Check for vertical alignment
        v_guides = self._find_vertical_alignments(active_bounds, target_bounds)
        for guide_x, guide_type in v_guides:
            guide = self._create_vertical_guide(guide_x, viewport, zoom, guide_type)
            guides.append(guide)
        
        # Check for spacing guides
        spacing_guides = self._find_spacing_guides(active_bounds, target_bounds)
        guides.extend(spacing_guides)
        
        return ft.Stack(guides) if guides else ft.Container()
    
    def _find_horizontal_alignments(
        self,
        active: BoundingBox,
        targets: List[BoundingBox]
    ) -> List[Tuple[float, str]]:
        """Find horizontal alignment points"""
        alignments = []
        threshold = 5  # Snap threshold in pixels
        
        for target in targets:
            # Top alignment
            if abs(active.y - target.y) < threshold:
                alignments.append((target.y, "top"))
            
            # Bottom alignment
            if abs(active.y + active.height - target.y - target.height) < threshold:
                alignments.append((target.y + target.height, "bottom"))
            
            # Center alignment
            active_center = active.y + active.height / 2
            target_center = target.y + target.height / 2
            if abs(active_center - target_center) < threshold:
                alignments.append((target_center, "center"))
        
        return alignments
    
    def _find_vertical_alignments(
        self,
        active: BoundingBox,
        targets: List[BoundingBox]
    ) -> List[Tuple[float, str]]:
        """Find vertical alignment points"""
        alignments = []
        threshold = 5  # Snap threshold in pixels
        
        for target in targets:
            # Left alignment
            if abs(active.x - target.x) < threshold:
                alignments.append((target.x, "left"))
            
            # Right alignment
            if abs(active.x + active.width - target.x - target.width) < threshold:
                alignments.append((target.x + target.width, "right"))
            
            # Center alignment
            active_center = active.x + active.width / 2
            target_center = target.x + target.width / 2
            if abs(active_center - target_center) < threshold:
                alignments.append((target_center, "center"))
        
        return alignments
    
    def _find_spacing_guides(
        self,
        active: BoundingBox,
        targets: List[BoundingBox]
    ) -> List[ft.Control]:
        """Find equal spacing opportunities"""
        # Future: Implement smart spacing detection
        return []
    
    def _create_horizontal_guide(
        self,
        y: float,
        viewport: ViewportBounds,
        zoom: float,
        guide_type: str
    ) -> ft.Control:
        """Create horizontal alignment guide"""
        screen_y = (y - viewport.top) * zoom
        
        return ft.Container(
            width=viewport.width * zoom,
            height=1,
            bgcolor="#5E6AD2",
            top=screen_y,
            opacity=0.6
        )
    
    def _create_vertical_guide(
        self,
        x: float,
        viewport: ViewportBounds,
        zoom: float,
        guide_type: str
    ) -> ft.Control:
        """Create vertical alignment guide"""
        screen_x = (x - viewport.left) * zoom
        
        return ft.Container(
            width=1,
            height=viewport.height * zoom,
            bgcolor="#5E6AD2",
            left=screen_x,
            opacity=0.6
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get rendering metrics"""
        total_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        hit_rate = self.metrics["cache_hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "render_count": self.metrics["render_count"],
            "cache_hit_rate": hit_rate,
            "cache_size": len(self._grid_cache)
        }
    
    def clear_cache(self) -> None:
        """Clear grid cache"""
        self._grid_cache.clear()
        logger.info("Grid cache cleared")