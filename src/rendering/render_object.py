"""
Render Object and Layer Management
Provides abstraction for renderable objects with z-ordering and layering
Following CLAUDE.md guidelines for clean architecture
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict
from enum import Enum, auto
import logging

from models.component import Component
from managers.spatial_index import BoundingBox

logger = logging.getLogger(__name__)


class RenderLayer(Enum):
    """
    Rendering layers for proper z-ordering
    Lower values render first (behind higher values)
    """
    BACKGROUND = auto()      # Canvas background
    GRID = auto()           # Grid overlay
    COMPONENTS = auto()     # Main components
    EFFECTS = auto()        # Drop shadows, glows
    SELECTION = auto()      # Selection indicators
    HANDLES = auto()        # Resize/rotation handles
    GUIDES = auto()         # Alignment guides
    OVERLAY = auto()        # Top-level overlays
    DEBUG = auto()          # Debug information


@dataclass
class RenderObject:
    """
    Wrapper for components with render-specific metadata
    CLAUDE.md #1.3: Readable abstractions
    """
    
    # Core properties
    id: str
    component: Component
    bounds: BoundingBox
    layer: RenderLayer = RenderLayer.COMPONENTS
    
    # Render state
    visible: bool = True
    opacity: float = 1.0
    z_index: int = 0
    
    # Transform
    transform_matrix: Optional[List[float]] = None  # 2D transform matrix
    rotation: float = 0  # Degrees
    scale_x: float = 1.0
    scale_y: float = 1.0
    
    # Render hints
    needs_redraw: bool = True
    is_cached: bool = False
    cache_key: Optional[str] = None
    
    # Interaction state
    is_selected: bool = False
    is_hovered: bool = False
    is_dragging: bool = False
    is_resizing: bool = False
    
    # Performance hints
    is_complex: bool = False  # Complex rendering (many children, effects)
    estimated_render_cost: int = 1  # Relative render cost
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def effective_opacity(self) -> float:
        """Calculate effective opacity including component opacity"""
        component_opacity = self.component.style.opacity or 1.0
        return self.opacity * component_opacity
    
    @property
    def render_priority(self) -> int:
        """
        Calculate render priority for sorting
        Higher priority renders last (on top)
        """
        # Layer has highest precedence
        layer_priority = self.layer.value * 10000
        
        # Then z-index
        z_priority = (self.z_index + 1000) * 10
        
        # Then selection state
        selection_priority = 1 if self.is_selected else 0
        
        return layer_priority + z_priority + selection_priority
    
    def intersects_viewport(self, viewport_bounds: BoundingBox) -> bool:
        """Check if render object is visible in viewport"""
        if not self.visible or self.effective_opacity == 0:
            return False
        
        # Check bounds intersection
        return self.bounds.intersects(viewport_bounds)
    
    def get_screen_bounds(self, viewport_offset: tuple, zoom: float) -> BoundingBox:
        """Convert world bounds to screen bounds"""
        screen_x = (self.bounds.x - viewport_offset[0]) * zoom
        screen_y = (self.bounds.y - viewport_offset[1]) * zoom
        screen_width = self.bounds.width * zoom
        screen_height = self.bounds.height * zoom
        
        return BoundingBox(
            x=screen_x,
            y=screen_y,
            width=screen_width,
            height=screen_height
        )
    
    def mark_dirty(self) -> None:
        """Mark object as needing redraw"""
        self.needs_redraw = True
        self.is_cached = False
        logger.debug(f"RenderObject {self.id} marked dirty")
    
    def mark_clean(self) -> None:
        """Mark object as up-to-date"""
        self.needs_redraw = False
        logger.debug(f"RenderObject {self.id} marked clean")
    
    def update_bounds(self, new_bounds: BoundingBox) -> None:
        """Update bounds and mark dirty"""
        self.bounds = new_bounds
        self.mark_dirty()
    
    def update_transform(
        self,
        rotation: Optional[float] = None,
        scale_x: Optional[float] = None,
        scale_y: Optional[float] = None
    ) -> None:
        """Update transform properties"""
        if rotation is not None:
            self.rotation = rotation
        if scale_x is not None:
            self.scale_x = scale_x
        if scale_y is not None:
            self.scale_y = scale_y
        
        # Update transform matrix
        self._update_transform_matrix()
        self.mark_dirty()
    
    def _update_transform_matrix(self) -> None:
        """Calculate 2D transform matrix from properties"""
        # For now, simple transform
        # Future: Full 2D transform with rotation and scale
        self.transform_matrix = [
            self.scale_x, 0, 0,
            0, self.scale_y, 0
        ]
    
    def estimate_render_cost(self) -> int:
        """
        Estimate relative rendering cost
        Used for performance optimization decisions
        """
        cost = 1
        
        # Component type cost
        type_costs = {
            "image": 5,
            "video": 10,
            "canvas": 8,
            "text": 2,
            "button": 3,
            "container": 1
        }
        cost += type_costs.get(self.component.type, 2)
        
        # Effects cost
        if self.component.style.box_shadow:
            cost += 3
        if self.component.style.opacity and self.component.style.opacity < 1:
            cost += 2
        if self.rotation != 0:
            cost += 2
        if self.scale_x != 1 or self.scale_y != 1:
            cost += 2
        
        # Children cost
        cost += len(self.component.children)
        
        # Size cost (larger = more pixels to render)
        area = self.bounds.width * self.bounds.height
        if area > 10000:  # Large component
            cost += 3
        elif area > 50000:  # Very large
            cost += 5
        
        self.estimated_render_cost = cost
        return cost
    
    def should_use_lod(self, zoom: float) -> bool:
        """
        Determine if Level of Detail optimization should be used
        CLAUDE.md #1.5: Performance optimization
        """
        # Use simplified rendering when zoomed out
        if zoom < 0.5 and self.is_complex:
            return True
        
        # Use simplified rendering for very small components
        screen_size = max(self.bounds.width * zoom, self.bounds.height * zoom)
        if screen_size < 10:  # Less than 10 pixels
            return True
        
        return False
    
    def __lt__(self, other: 'RenderObject') -> bool:
        """Compare for sorting by render priority"""
        return self.render_priority < other.render_priority


class RenderObjectFactory:
    """
    Factory for creating render objects from components
    CLAUDE.md #10.2: Factory pattern
    """
    
    @staticmethod
    def create_from_component(
        component: Component,
        parent_bounds: Optional[BoundingBox] = None
    ) -> RenderObject:
        """Create render object from component"""
        # Calculate bounds
        bounds = RenderObjectFactory._calculate_bounds(component, parent_bounds)
        
        # Determine layer
        layer = RenderObjectFactory._determine_layer(component)
        
        # Extract z-index
        z_index = component.style.z_index or 0
        
        # Create render object
        render_obj = RenderObject(
            id=component.id,
            component=component,
            bounds=bounds,
            layer=layer,
            z_index=z_index,
            visible=component.editor_visible,
            opacity=component.style.opacity or 1.0
        )
        
        # Estimate complexity
        render_obj.is_complex = RenderObjectFactory._is_complex(component)
        render_obj.estimate_render_cost()
        
        return render_obj
    
    @staticmethod
    def _calculate_bounds(
        component: Component,
        parent_bounds: Optional[BoundingBox]
    ) -> BoundingBox:
        """Calculate component bounds"""
        # Parse position
        x = RenderObjectFactory._parse_position(
            component.style.left, 
            parent_bounds.x if parent_bounds else 0
        )
        y = RenderObjectFactory._parse_position(
            component.style.top,
            parent_bounds.y if parent_bounds else 0
        )
        
        # Parse dimensions
        width = RenderObjectFactory._parse_dimension(
            component.style.width,
            parent_bounds.width if parent_bounds else None,
            100  # default
        )
        height = RenderObjectFactory._parse_dimension(
            component.style.height,
            parent_bounds.height if parent_bounds else None,
            50  # default
        )
        
        return BoundingBox(x=x, y=y, width=width, height=height)
    
    @staticmethod
    def _parse_position(value: Optional[str], parent_pos: float) -> float:
        """Parse position value"""
        if value is None:
            return parent_pos
        
        if isinstance(value, (int, float)):
            return float(value) + parent_pos
        
        if isinstance(value, str):
            if value.endswith('px'):
                return float(value[:-2]) + parent_pos
            try:
                return float(value) + parent_pos
            except ValueError:
                return parent_pos
        
        return parent_pos
    
    @staticmethod
    def _parse_dimension(
        value: Optional[str],
        parent_size: Optional[float],
        default: float
    ) -> float:
        """Parse dimension value"""
        if value is None:
            return default
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            if value.endswith('px'):
                return float(value[:-2])
            elif value.endswith('%') and parent_size:
                return float(value[:-1]) / 100 * parent_size
            elif value == 'auto':
                return default
            else:
                try:
                    return float(value)
                except ValueError:
                    return default
        
        return default
    
    @staticmethod
    def _determine_layer(component: Component) -> RenderLayer:
        """Determine appropriate render layer"""
        # Selection state overrides
        if component.editor_selected:
            return RenderLayer.SELECTION
        
        # Component type based
        if component.type in ['grid', 'guides']:
            return RenderLayer.GRID
        elif component.type in ['tooltip', 'modal', 'popover']:
            return RenderLayer.OVERLAY
        else:
            return RenderLayer.COMPONENTS
    
    @staticmethod
    def _is_complex(component: Component) -> bool:
        """Determine if component is complex to render"""
        # Many children
        if len(component.children) > 20:
            return True
        
        # Complex effects
        if (component.style.box_shadow or 
            component.style.transform or
            component.style.filter):
            return True
        
        # Large size
        try:
            width = RenderObjectFactory._parse_dimension(component.style.width, None, 0)
            height = RenderObjectFactory._parse_dimension(component.style.height, None, 0)
            if width * height > 50000:  # Large area
                return True
        except:
            pass
        
        return False