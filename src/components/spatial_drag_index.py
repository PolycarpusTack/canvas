"""
Spatial Indexing System for Efficient Drag & Drop Operations
Implements R-tree based spatial index for fast drop zone detection
Following CLAUDE.md guidelines for algorithmic efficiency
"""

from typing import List, Dict, Set, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import time
from collections import defaultdict

from drag_drop_manager import DropTarget, DropZoneType
from managers.spatial_index import BoundingBox

logger = logging.getLogger(__name__)


@dataclass
class DropZone:
    """
    Drop zone with spatial bounds
    CLAUDE.md #2.1.1: Validate drop zone data
    """
    id: str
    target: DropTarget
    bounds: BoundingBox
    depth: int = 0
    parent_id: Optional[str] = None
    accepts: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """Validate drop zone"""
        if not self.id:
            raise ValueError("Drop zone ID cannot be empty")
        
        if self.bounds.width <= 0 or self.bounds.height <= 0:
            raise ValueError("Drop zone must have positive dimensions")
        
        if self.depth < 0:
            raise ValueError("Drop zone depth cannot be negative")
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within drop zone"""
        return (
            self.bounds.x <= x <= self.bounds.x + self.bounds.width and
            self.bounds.y <= y <= self.bounds.y + self.bounds.height
        )
    
    def intersects(self, other_bounds: BoundingBox) -> bool:
        """Check if drop zone intersects with bounds"""
        return self.bounds.intersects(other_bounds)


class QueryType(Enum):
    """Types of spatial queries"""
    POINT = auto()
    REGION = auto()
    NEAREST = auto()


@dataclass
class QueryResult:
    """Result of spatial query"""
    drop_zones: List[DropZone]
    query_time_ms: float
    total_checked: int
    cache_hit: bool = False


class SpatialDragIndex:
    """
    Efficient spatial index for drag & drop operations
    CLAUDE.md #1.5: Optimize for common operations
    CLAUDE.md #12.1: Performance monitoring
    """
    
    def __init__(self, max_depth: int = 8, max_items_per_node: int = 16):
        """
        Initialize spatial index with R-tree parameters
        
        Args:
            max_depth: Maximum tree depth
            max_items_per_node: Maximum items per node before split
        """
        self.max_depth = max_depth
        self.max_items_per_node = max_items_per_node
        
        # Storage
        self._drop_zones: Dict[str, DropZone] = {}
        self._root_node: Optional[IndexNode] = None
        self._dirty = False
        
        # Performance tracking
        self._query_count = 0
        self._total_query_time = 0.0
        self._cache: Dict[str, QueryResult] = {}
        self._cache_hits = 0
        
        # Spatial hierarchy for nested components
        self._depth_map: Dict[int, List[str]] = defaultdict(list)
        self._parent_child_map: Dict[str, List[str]] = defaultdict(list)
        
        logger.info(
            f"Initialized spatial drag index "
            f"(max_depth={max_depth}, max_items={max_items_per_node})"
        )
    
    def add_drop_zone(
        self,
        zone_id: str,
        target: DropTarget,
        bounds: BoundingBox,
        depth: int = 0,
        parent_id: Optional[str] = None,
        accepts: Optional[Set[str]] = None
    ) -> None:
        """
        Add drop zone to spatial index
        CLAUDE.md #2.1.1: Validate inputs
        """
        try:
            # Validate inputs
            if zone_id in self._drop_zones:
                raise ValueError(f"Drop zone {zone_id} already exists")
            
            # Create drop zone
            drop_zone = DropZone(
                id=zone_id,
                target=target,
                bounds=bounds,
                depth=depth,
                parent_id=parent_id,
                accepts=accepts or set()
            )
            
            # Store in maps
            self._drop_zones[zone_id] = drop_zone
            self._depth_map[depth].append(zone_id)
            
            if parent_id:
                self._parent_child_map[parent_id].append(zone_id)
            
            # Mark for rebuild
            self._dirty = True
            
            # Clear cache
            self._cache.clear()
            
            logger.debug(f"Added drop zone: {zone_id} at depth {depth}")
            
        except Exception as e:
            logger.error(f"Failed to add drop zone {zone_id}: {e}")
            raise
    
    def remove_drop_zone(self, zone_id: str) -> bool:
        """
        Remove drop zone from index
        CLAUDE.md #2.1.4: Proper cleanup
        """
        try:
            if zone_id not in self._drop_zones:
                return False
            
            drop_zone = self._drop_zones[zone_id]
            
            # Remove from maps
            del self._drop_zones[zone_id]
            self._depth_map[drop_zone.depth].remove(zone_id)
            
            if drop_zone.parent_id:
                self._parent_child_map[drop_zone.parent_id].remove(zone_id)
            
            # Remove children recursively
            children = self._parent_child_map.pop(zone_id, [])
            for child_id in children:
                self.remove_drop_zone(child_id)
            
            # Mark for rebuild
            self._dirty = True
            
            # Clear cache
            self._cache.clear()
            
            logger.debug(f"Removed drop zone: {zone_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove drop zone {zone_id}: {e}")
            return False
    
    def update_drop_zone_bounds(
        self,
        zone_id: str,
        new_bounds: BoundingBox
    ) -> bool:
        """Update drop zone bounds"""
        try:
            if zone_id not in self._drop_zones:
                return False
            
            drop_zone = self._drop_zones[zone_id]
            drop_zone.bounds = new_bounds
            
            # Mark for rebuild
            self._dirty = True
            
            # Clear cache
            self._cache.clear()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update drop zone bounds {zone_id}: {e}")
            return False
    
    def find_drop_zones_at_point(
        self,
        x: float,
        y: float,
        component_type: Optional[str] = None
    ) -> QueryResult:
        """
        Find all drop zones containing a point
        CLAUDE.md #1.5: Optimize point queries
        """
        start_time = time.perf_counter()
        self._query_count += 1
        
        try:
            # Check cache
            cache_key = f"point_{x}_{y}_{component_type}"
            if cache_key in self._cache:
                self._cache_hits += 1
                result = self._cache[cache_key]
                result.cache_hit = True
                return result
            
            # Rebuild index if needed
            if self._dirty:
                self._rebuild_index()
            
            # Find zones at point
            matching_zones = []
            total_checked = 0
            
            # Start from deepest level and work up for proper ordering
            max_depth = max(self._depth_map.keys()) if self._depth_map else 0
            
            for depth in range(max_depth, -1, -1):
                zone_ids = self._depth_map.get(depth, [])
                
                for zone_id in zone_ids:
                    total_checked += 1
                    zone = self._drop_zones[zone_id]
                    
                    if zone.contains_point(x, y):
                        # Check component type acceptance
                        if component_type and zone.accepts:
                            if "*" not in zone.accepts and component_type not in zone.accepts:
                                continue
                        
                        matching_zones.append(zone)
            
            # Sort by depth (deepest first) and area (smallest first)
            matching_zones.sort(
                key=lambda z: (-z.depth, z.bounds.width * z.bounds.height)
            )
            
            # Create result
            query_time = (time.perf_counter() - start_time) * 1000
            result = QueryResult(
                drop_zones=matching_zones,
                query_time_ms=query_time,
                total_checked=total_checked
            )
            
            # Cache result
            self._cache[cache_key] = result
            
            # Update metrics
            self._total_query_time += query_time
            
            return result
            
        except Exception as e:
            logger.error(f"Point query failed at ({x}, {y}): {e}")
            return QueryResult([], 0, 0)
    
    def find_drop_zones_in_region(
        self,
        bounds: BoundingBox,
        component_type: Optional[str] = None,
        fully_contained: bool = False
    ) -> QueryResult:
        """
        Find drop zones intersecting or contained in region
        CLAUDE.md #1.5: Efficient region queries
        """
        start_time = time.perf_counter()
        self._query_count += 1
        
        try:
            # Check cache
            cache_key = f"region_{bounds.x}_{bounds.y}_{bounds.width}_{bounds.height}_{component_type}_{fully_contained}"
            if cache_key in self._cache:
                self._cache_hits += 1
                result = self._cache[cache_key]
                result.cache_hit = True
                return result
            
            # Rebuild index if needed
            if self._dirty:
                self._rebuild_index()
            
            matching_zones = []
            total_checked = 0
            
            for zone in self._drop_zones.values():
                total_checked += 1
                
                # Check intersection or containment
                if fully_contained:
                    # Zone must be fully contained in region
                    if bounds.contains(zone.bounds):
                        if self._check_component_acceptance(zone, component_type):
                            matching_zones.append(zone)
                else:
                    # Zone must intersect with region
                    if zone.intersects(bounds):
                        if self._check_component_acceptance(zone, component_type):
                            matching_zones.append(zone)
            
            # Sort by depth and area
            matching_zones.sort(
                key=lambda z: (-z.depth, z.bounds.width * z.bounds.height)
            )
            
            # Create result
            query_time = (time.perf_counter() - start_time) * 1000
            result = QueryResult(
                drop_zones=matching_zones,
                query_time_ms=query_time,
                total_checked=total_checked
            )
            
            # Cache result
            self._cache[cache_key] = result
            
            # Update metrics
            self._total_query_time += query_time
            
            return result
            
        except Exception as e:
            logger.error(f"Region query failed for {bounds}: {e}")
            return QueryResult([], 0, 0)
    
    def find_nearest_drop_zone(
        self,
        x: float,
        y: float,
        max_distance: float = 100.0,
        component_type: Optional[str] = None
    ) -> Optional[DropZone]:
        """
        Find nearest drop zone to a point
        CLAUDE.md #1.5: Efficient nearest neighbor search
        """
        try:
            # Rebuild index if needed
            if self._dirty:
                self._rebuild_index()
            
            nearest_zone = None
            min_distance = max_distance
            
            for zone in self._drop_zones.values():
                # Calculate distance to zone center
                zone_center_x = zone.bounds.x + zone.bounds.width / 2
                zone_center_y = zone.bounds.y + zone.bounds.height / 2
                
                distance = ((x - zone_center_x) ** 2 + (y - zone_center_y) ** 2) ** 0.5
                
                if distance < min_distance:
                    if self._check_component_acceptance(zone, component_type):
                        nearest_zone = zone
                        min_distance = distance
            
            return nearest_zone
            
        except Exception as e:
            logger.error(f"Nearest search failed at ({x}, {y}): {e}")
            return None
    
    def get_zone_hierarchy(self, zone_id: str) -> List[DropZone]:
        """
        Get hierarchy path from root to zone
        CLAUDE.md #1.2: DRY hierarchy traversal
        """
        try:
            if zone_id not in self._drop_zones:
                return []
            
            hierarchy = []
            current_id = zone_id
            
            while current_id:
                zone = self._drop_zones[current_id]
                hierarchy.insert(0, zone)  # Prepend for root-to-leaf order
                current_id = zone.parent_id
            
            return hierarchy
            
        except Exception as e:
            logger.error(f"Failed to get hierarchy for {zone_id}: {e}")
            return []
    
    def get_child_zones(self, zone_id: str) -> List[DropZone]:
        """Get immediate child zones"""
        try:
            child_ids = self._parent_child_map.get(zone_id, [])
            return [self._drop_zones[child_id] for child_id in child_ids]
        except Exception as e:
            logger.error(f"Failed to get children for {zone_id}: {e}")
            return []
    
    def clear(self) -> None:
        """
        Clear all drop zones
        CLAUDE.md #2.1.4: Proper cleanup
        """
        try:
            self._drop_zones.clear()
            self._depth_map.clear()
            self._parent_child_map.clear()
            self._cache.clear()
            self._root_node = None
            self._dirty = False
            
            logger.info("Cleared spatial drag index")
            
        except Exception as e:
            logger.error(f"Failed to clear index: {e}")
    
    def _rebuild_index(self) -> None:
        """
        Rebuild spatial index tree
        CLAUDE.md #1.5: Efficient index rebuilding
        """
        try:
            if not self._dirty:
                return
            
            start_time = time.perf_counter()
            
            # For now, we use a simple list-based approach
            # In a full implementation, this would build an R-tree
            
            # Sort zones by depth for efficient queries
            for depth_zones in self._depth_map.values():
                depth_zones.sort(key=lambda zone_id: (
                    self._drop_zones[zone_id].bounds.x,
                    self._drop_zones[zone_id].bounds.y
                ))
            
            self._dirty = False
            
            rebuild_time = (time.perf_counter() - start_time) * 1000
            logger.debug(
                f"Rebuilt spatial index in {rebuild_time:.1f}ms "
                f"({len(self._drop_zones)} zones)"
            )
            
        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}")
    
    def _check_component_acceptance(
        self,
        zone: DropZone,
        component_type: Optional[str]
    ) -> bool:
        """Check if zone accepts component type"""
        if not component_type or not zone.accepts:
            return True
        
        return "*" in zone.accepts or component_type in zone.accepts
    
    def get_performance_stats(self) -> Dict[str, float]:
        """
        Get performance statistics
        CLAUDE.md #12.1: Performance monitoring
        """
        cache_hit_rate = (
            self._cache_hits / max(self._query_count, 1)
        ) * 100
        
        avg_query_time = (
            self._total_query_time / max(self._query_count, 1)
        )
        
        return {
            "total_zones": len(self._drop_zones),
            "total_queries": self._query_count,
            "avg_query_time_ms": avg_query_time,
            "cache_hit_rate_percent": cache_hit_rate,
            "cache_size": len(self._cache),
            "max_depth": max(self._depth_map.keys()) if self._depth_map else 0
        }
    
    def _get_canvas_bounds(self) -> BoundingBox:
        """
        Get the full canvas bounds for region queries
        CLAUDE.md #1.5: Efficient bounds calculation
        """
        if not self._drop_zones:
            # Default canvas size
            return BoundingBox(x=0, y=0, width=2000, height=2000)
        
        # Calculate bounding box of all drop zones
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for zone in self._drop_zones.values():
            min_x = min(min_x, zone.bounds.x)
            min_y = min(min_y, zone.bounds.y)
            max_x = max(max_x, zone.bounds.x + zone.bounds.width)
            max_y = max(max_y, zone.bounds.y + zone.bounds.height)
        
        # Add padding
        padding = 100
        return BoundingBox(
            x=min_x - padding,
            y=min_y - padding,
            width=(max_x - min_x) + 2 * padding,
            height=(max_y - min_y) + 2 * padding
        )
    
    def optimize_cache(self, max_cache_size: int = 1000) -> None:
        """Optimize cache by removing least recently used entries"""
        if len(self._cache) > max_cache_size:
            # Simple LRU implementation - remove oldest half
            items = list(self._cache.items())
            keep_count = max_cache_size // 2
            
            self._cache = dict(items[-keep_count:])
            
            logger.debug(
                f"Optimized cache: kept {keep_count} of {len(items)} entries"
            )


@dataclass
class IndexNode:
    """
    Node in spatial index tree (for future R-tree implementation)
    CLAUDE.md #1.4: Extensible for R-tree
    """
    bounds: BoundingBox
    children: List['IndexNode'] = field(default_factory=list)
    zones: List[str] = field(default_factory=list)
    is_leaf: bool = True
    depth: int = 0
    
    def add_zone(self, zone_id: str, zone_bounds: BoundingBox) -> None:
        """Add zone to node"""
        if self.is_leaf:
            self.zones.append(zone_id)
            self.bounds = self.bounds.union(zone_bounds)
        else:
            # Find best child node
            # Implementation would go here for R-tree
            pass


# Global instance for the drag system
_spatial_drag_index_instance: Optional[SpatialDragIndex] = None


def get_spatial_drag_index() -> SpatialDragIndex:
    """Get or create global spatial drag index"""
    global _spatial_drag_index_instance
    if _spatial_drag_index_instance is None:
        _spatial_drag_index_instance = SpatialDragIndex()
    return _spatial_drag_index_instance


def reset_spatial_drag_index() -> None:
    """Reset global spatial drag index"""
    global _spatial_drag_index_instance
    if _spatial_drag_index_instance:
        _spatial_drag_index_instance.clear()
    _spatial_drag_index_instance = None