"""
Spatial indexing system for efficient canvas operations.
Provides fast spatial queries for component selection, collision detection, and rendering optimization.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Represents a bounding box for spatial indexing"""
    x: float
    y: float
    width: float
    height: float
    
    @property
    def left(self) -> float:
        return self.x
    
    @property
    def right(self) -> float:
        return self.x + self.width
    
    @property
    def top(self) -> float:
        return self.y
    
    @property
    def bottom(self) -> float:
        return self.y + self.height
    
    @property
    def center_x(self) -> float:
        return self.x + self.width / 2
    
    @property
    def center_y(self) -> float:
        return self.y + self.height / 2
    
    def intersects(self, other: 'BoundingBox') -> bool:
        """Check if this bounding box intersects with another"""
        return (
            self.left < other.right and
            self.right > other.left and
            self.top < other.bottom and
            self.bottom > other.top
        )
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside this bounding box"""
        return (
            self.left <= x <= self.right and
            self.top <= y <= self.bottom
        )
    
    def contains_box(self, other: 'BoundingBox') -> bool:
        """Check if this bounding box completely contains another"""
        return (
            self.left <= other.left and
            self.right >= other.right and
            self.top <= other.top and
            self.bottom >= other.bottom
        )
    
    def expand(self, margin: float) -> 'BoundingBox':
        """Return a new bounding box expanded by the given margin"""
        return BoundingBox(
            x=self.x - margin,
            y=self.y - margin,
            width=self.width + 2 * margin,
            height=self.height + 2 * margin
        )


class SpatialIndex:
    """
    Efficient spatial index for canvas components using a grid-based approach.
    Provides fast spatial queries for large numbers of components.
    """
    
    def __init__(self, grid_size: float = 100.0):
        self.grid_size = grid_size
        self.component_bounds: Dict[str, BoundingBox] = {}
        self.grid_cells: Dict[Tuple[int, int], Set[str]] = defaultdict(set)
        self.dirty_components: Set[str] = set()
        
        logger.info(f"SpatialIndex initialized with grid size: {grid_size}")
    
    def insert(self, component_id: str, bounds: BoundingBox):
        """Insert or update a component in the spatial index"""
        # Remove old entries if component already exists
        if component_id in self.component_bounds:
            self.remove(component_id)
        
        # Store bounds
        self.component_bounds[component_id] = bounds
        
        # Add to grid cells
        cells = self._get_grid_cells(bounds)
        for cell in cells:
            self.grid_cells[cell].add(component_id)
        
        logger.debug(f"Inserted component {component_id} into {len(cells)} grid cells")
    
    def remove(self, component_id: str):
        """Remove a component from the spatial index"""
        if component_id not in self.component_bounds:
            return
        
        bounds = self.component_bounds[component_id]
        cells = self._get_grid_cells(bounds)
        
        # Remove from grid cells
        for cell in cells:
            self.grid_cells[cell].discard(component_id)
            if not self.grid_cells[cell]:
                del self.grid_cells[cell]
        
        # Remove bounds
        del self.component_bounds[component_id]
        self.dirty_components.discard(component_id)
        
        logger.debug(f"Removed component {component_id}")
    
    def update(self, component_id: str, bounds: BoundingBox):
        """Update a component's position in the spatial index"""
        self.insert(component_id, bounds)  # insert handles removal of old entries
    
    def query_point(self, x: float, y: float) -> List[str]:
        """Find all components that contain the given point"""
        cell = self._point_to_cell(x, y)
        candidates = self.grid_cells.get(cell, set())
        
        results = []
        for component_id in candidates:
            bounds = self.component_bounds[component_id]
            if bounds.contains_point(x, y):
                results.append(component_id)
        
        logger.debug(f"Point query ({x}, {y}) found {len(results)} components")
        return results
    
    def query_region(self, region: BoundingBox) -> List[str]:
        """Find all components that intersect with the given region"""
        cells = self._get_grid_cells(region)
        candidates = set()
        
        for cell in cells:
            candidates.update(self.grid_cells.get(cell, set()))
        
        results = []
        for component_id in candidates:
            bounds = self.component_bounds[component_id]
            if bounds.intersects(region):
                results.append(component_id)
        
        logger.debug(f"Region query found {len(results)} components from {len(candidates)} candidates")
        return results
    
    def query_selection_box(self, selection_box: BoundingBox, fully_contained: bool = False) -> List[str]:
        """Find components within a selection box"""
        cells = self._get_grid_cells(selection_box)
        candidates = set()
        
        for cell in cells:
            candidates.update(self.grid_cells.get(cell, set()))
        
        results = []
        for component_id in candidates:
            bounds = self.component_bounds[component_id]
            
            if fully_contained:
                # Component must be fully inside selection box
                if selection_box.contains_box(bounds):
                    results.append(component_id)
            else:
                # Component just needs to intersect selection box
                if bounds.intersects(selection_box):
                    results.append(component_id)
        
        logger.debug(f"Selection query found {len(results)} components (fully_contained: {fully_contained})")
        return results
    
    def get_nearest_components(self, x: float, y: float, max_distance: float, limit: int = 10) -> List[Tuple[str, float]]:
        """Find nearest components to a point within max_distance"""
        search_box = BoundingBox(
            x=x - max_distance,
            y=y - max_distance,
            width=2 * max_distance,
            height=2 * max_distance
        )
        
        candidates = self.query_region(search_box)
        distances = []
        
        for component_id in candidates:
            bounds = self.component_bounds[component_id]
            # Calculate distance to center of component
            dx = bounds.center_x - x
            dy = bounds.center_y - y
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance <= max_distance:
                distances.append((component_id, distance))
        
        # Sort by distance and limit results
        distances.sort(key=lambda x: x[1])
        results = distances[:limit]
        
        logger.debug(f"Nearest query found {len(results)} components within {max_distance} units")
        return results
    
    def get_components_in_viewport(self, viewport: BoundingBox, margin: float = 50.0) -> List[str]:
        """Get components visible in the viewport with optional margin for pre-loading"""
        expanded_viewport = viewport.expand(margin)
        return self.query_region(expanded_viewport)
    
    def detect_overlaps(self, component_id: str, overlap_threshold: float = 1.0) -> List[str]:
        """Detect components that overlap with the given component"""
        if component_id not in self.component_bounds:
            return []
        
        bounds = self.component_bounds[component_id]
        candidates = self.query_region(bounds)
        
        overlaps = []
        for candidate_id in candidates:
            if candidate_id == component_id:
                continue
                
            candidate_bounds = self.component_bounds[candidate_id]
            if bounds.intersects(candidate_bounds):
                # Calculate overlap area
                overlap_x = min(bounds.right, candidate_bounds.right) - max(bounds.left, candidate_bounds.left)
                overlap_y = min(bounds.bottom, candidate_bounds.bottom) - max(bounds.top, candidate_bounds.top)
                overlap_area = overlap_x * overlap_y
                
                if overlap_area >= overlap_threshold:
                    overlaps.append(candidate_id)
        
        return overlaps
    
    def _get_grid_cells(self, bounds: BoundingBox) -> Set[Tuple[int, int]]:
        """Get all grid cells that intersect with the given bounds"""
        min_x = int(bounds.left // self.grid_size)
        max_x = int(bounds.right // self.grid_size)
        min_y = int(bounds.top // self.grid_size)
        max_y = int(bounds.bottom // self.grid_size)
        
        cells = set()
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                cells.add((x, y))
        
        return cells
    
    def _point_to_cell(self, x: float, y: float) -> Tuple[int, int]:
        """Convert a point to its grid cell coordinates"""
        return (int(x // self.grid_size), int(y // self.grid_size))
    
    def get_statistics(self) -> Dict[str, any]:
        """Get spatial index statistics for debugging and optimization"""
        non_empty_cells = len([cell for cell in self.grid_cells.values() if cell])
        total_components = len(self.component_bounds)
        
        if self.grid_cells:
            avg_components_per_cell = sum(len(cell) for cell in self.grid_cells.values()) / len(self.grid_cells)
            max_components_per_cell = max(len(cell) for cell in self.grid_cells.values())
        else:
            avg_components_per_cell = 0
            max_components_per_cell = 0
        
        return {
            'total_components': total_components,
            'non_empty_cells': non_empty_cells,
            'avg_components_per_cell': avg_components_per_cell,
            'max_components_per_cell': max_components_per_cell,
            'grid_size': self.grid_size,
            'dirty_components': len(self.dirty_components)
        }
    
    def optimize(self):
        """Optimize the spatial index by cleaning up empty cells and adjusting grid size if needed"""
        # Remove empty cells
        empty_cells = [cell for cell, components in self.grid_cells.items() if not components]
        for cell in empty_cells:
            del self.grid_cells[cell]
        
        # Clear dirty components set
        self.dirty_components.clear()
        
        stats = self.get_statistics()
        logger.info(f"Spatial index optimized: {stats}")
    
    def clear(self):
        """Clear all data from the spatial index"""
        self.component_bounds.clear()
        self.grid_cells.clear()
        self.dirty_components.clear()
        logger.info("Spatial index cleared")


class SpatialIndexManager:
    """
    Manager for spatial indices with automatic updates and optimization.
    Integrates with the component tree state to maintain spatial consistency.
    """
    
    def __init__(self, grid_size: float = 100.0, auto_optimize_interval: int = 1000):
        self.spatial_index = SpatialIndex(grid_size)
        self.auto_optimize_interval = auto_optimize_interval
        self.operations_since_optimize = 0
        
        logger.info("SpatialIndexManager initialized")
    
    def component_added(self, component_id: str, component_data: Dict):
        """Handle component addition - extract bounds and add to index"""
        bounds = self._extract_bounds_from_component(component_data)
        if bounds:
            self.spatial_index.insert(component_id, bounds)
            self._maybe_optimize()
    
    def component_updated(self, component_id: str, component_data: Dict):
        """Handle component update - update bounds in index"""
        bounds = self._extract_bounds_from_component(component_data)
        if bounds:
            self.spatial_index.update(component_id, bounds)
            self._maybe_optimize()
    
    def component_removed(self, component_id: str):
        """Handle component removal - remove from index"""
        self.spatial_index.remove(component_id)
        self._maybe_optimize()
    
    def _extract_bounds_from_component(self, component_data: Dict) -> Optional[BoundingBox]:
        """Extract bounding box from component data"""
        try:
            # Try to get position and size from component style
            style = component_data.get('style', {})
            
            # Get position
            x = self._parse_css_value(style.get('left', '0'))
            y = self._parse_css_value(style.get('top', '0'))
            
            # Get size
            width = self._parse_css_value(style.get('width', '100'))
            height = self._parse_css_value(style.get('height', '50'))
            
            return BoundingBox(x=x, y=y, width=width, height=height)
            
        except Exception as e:
            logger.warning(f"Failed to extract bounds from component: {e}")
            return None
    
    def _parse_css_value(self, value: str) -> float:
        """Parse CSS value to float (simplified - assumes px values)"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove 'px' suffix if present
            value = value.replace('px', '').strip()
            try:
                return float(value)
            except ValueError:
                return 0.0
        
        return 0.0
    
    def _maybe_optimize(self):
        """Optimize spatial index if enough operations have occurred"""
        self.operations_since_optimize += 1
        
        if self.operations_since_optimize >= self.auto_optimize_interval:
            self.spatial_index.optimize()
            self.operations_since_optimize = 0
    
    def get_index(self) -> SpatialIndex:
        """Get the underlying spatial index"""
        return self.spatial_index