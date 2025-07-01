"""
Render Cache for Canvas Performance Optimization
Implements LRU caching for rendered components to avoid redundant rendering
Following CLAUDE.md guidelines for memory-efficient caching
"""

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Optional, Callable, Dict, Tuple
import time
import hashlib
import logging
import flet as ft

from models.component import Component

logger = logging.getLogger(__name__)


@dataclass
class CachedRender:
    """Represents a cached render result"""
    control: ft.Control
    component_hash: str
    timestamp: float
    render_time: float  # Time taken to render (for metrics)
    size_estimate: int  # Estimated memory size
    access_count: int = 0
    last_accessed: float = 0
    
    def is_valid(self, component: Component, max_age: Optional[float] = None) -> bool:
        """Check if cached render is still valid"""
        # Check hash match
        current_hash = _generate_component_hash(component)
        if current_hash != self.component_hash:
            return False
        
        # Check age if max_age specified
        if max_age is not None:
            age = time.time() - self.timestamp
            if age > max_age:
                return False
        
        return True
    
    def access(self) -> None:
        """Record access for LRU tracking"""
        self.access_count += 1
        self.last_accessed = time.time()


class RenderCache:
    """
    LRU Cache for rendered components
    CLAUDE.md #1.5: Memory-efficient caching
    CLAUDE.md #12.1: Cache performance metrics
    CLAUDE.md #2.1.4: Proper resource cleanup
    """
    
    def __init__(
        self, 
        max_size: int = 1000,
        max_memory_mb: int = 100,
        ttl_seconds: Optional[float] = None
    ):
        """
        Initialize render cache
        
        Args:
            max_size: Maximum number of cached items
            max_memory_mb: Maximum memory usage in MB
            ttl_seconds: Time-to-live for cached items (None = no expiry)
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.ttl_seconds = ttl_seconds
        
        # LRU cache using OrderedDict
        self.cache: OrderedDict[str, CachedRender] = OrderedDict()
        
        # Memory tracking
        self.total_memory_estimate = 0
        
        # Performance metrics
        self.metrics = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_render_time_saved": 0.0,
            "memory_high_water_mark": 0
        }
        
        logger.info(
            f"RenderCache initialized: max_size={max_size}, "
            f"max_memory={max_memory_mb}MB, ttl={ttl_seconds}s"
        )
    
    def get_or_render(
        self,
        component: Component,
        render_func: Callable[[Component], ft.Control],
        force_render: bool = False
    ) -> Tuple[ft.Control, bool]:
        """
        Get cached render or create new one
        
        Returns:
            Tuple of (control, was_cached)
        """
        if force_render:
            return self._render_and_cache(component, render_func), False
        
        # Generate cache key
        cache_key = self._generate_cache_key(component)
        
        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            
            # Validate cache entry
            if cached.is_valid(component, self.ttl_seconds):
                # Cache hit
                self.metrics["hits"] += 1
                self.metrics["total_render_time_saved"] += cached.render_time
                
                # Move to end for LRU
                self.cache.move_to_end(cache_key)
                cached.access()
                
                logger.debug(f"Cache hit for component {component.id}")
                return cached.control, True
            else:
                # Invalid entry - remove it
                self._evict_entry(cache_key)
        
        # Cache miss - render component
        self.metrics["misses"] += 1
        control = self._render_and_cache(component, render_func)
        return control, False
    
    def _render_and_cache(
        self,
        component: Component,
        render_func: Callable[[Component], ft.Control]
    ) -> ft.Control:
        """Render component and add to cache"""
        start_time = time.perf_counter()
        
        # Render component
        control = render_func(component)
        
        render_time = time.perf_counter() - start_time
        
        # Estimate memory size
        size_estimate = self._estimate_control_size(control)
        
        # Check if we have space
        if self._should_cache(size_estimate):
            # Create cache entry
            cache_key = self._generate_cache_key(component)
            cached_render = CachedRender(
                control=control,
                component_hash=_generate_component_hash(component),
                timestamp=time.time(),
                render_time=render_time,
                size_estimate=size_estimate
            )
            
            # Add to cache
            self.cache[cache_key] = cached_render
            self.total_memory_estimate += size_estimate
            
            # Update metrics
            self.metrics["memory_high_water_mark"] = max(
                self.metrics["memory_high_water_mark"],
                self.total_memory_estimate
            )
            
            # Evict if necessary
            self._evict_if_needed()
            
            logger.debug(
                f"Cached component {component.id} "
                f"(render_time={render_time*1000:.1f}ms, size={size_estimate}B)"
            )
        
        return control
    
    def _should_cache(self, size_estimate: int) -> bool:
        """Determine if item should be cached based on size"""
        # Don't cache if single item exceeds limits
        if size_estimate > self.max_memory_bytes * 0.1:  # 10% of total
            logger.debug(f"Item too large to cache: {size_estimate}B")
            return False
        return True
    
    def _evict_if_needed(self) -> None:
        """Evict items if cache exceeds limits"""
        # Check size limit
        while len(self.cache) > self.max_size:
            self._evict_oldest()
        
        # Check memory limit
        while self.total_memory_estimate > self.max_memory_bytes and self.cache:
            self._evict_oldest()
    
    def _evict_oldest(self) -> None:
        """Evict oldest item (LRU)"""
        if not self.cache:
            return
        
        # Get oldest key (first in OrderedDict)
        oldest_key = next(iter(self.cache))
        self._evict_entry(oldest_key)
    
    def _evict_entry(self, cache_key: str) -> None:
        """Evict specific cache entry"""
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            self.total_memory_estimate -= entry.size_estimate
            del self.cache[cache_key]
            self.metrics["evictions"] += 1
            
            logger.debug(f"Evicted cache entry: {cache_key}")
    
    def _generate_cache_key(self, component: Component) -> str:
        """Generate stable cache key for component"""
        # Include ID and relevant style properties that affect rendering
        key_parts = [
            component.id,
            component.type,
            str(component.style.width),
            str(component.style.height),
            str(component.style.background_color),
            str(component.style.border),
            str(component.style.border_radius),
            str(component.style.opacity),
            # Add more properties as needed
        ]
        
        return ":".join(key_parts)
    
    def _estimate_control_size(self, control: ft.Control) -> int:
        """
        Estimate memory size of a Flet control
        This is a rough estimate based on control complexity
        """
        base_size = 1024  # Base size for any control
        
        # Add size based on control type
        if isinstance(control, ft.Container):
            base_size += 512
            if control.content:
                base_size += self._estimate_control_size(control.content)
        elif isinstance(control, ft.Column) or isinstance(control, ft.Row):
            base_size += 256
            if hasattr(control, 'controls'):
                for child in control.controls:
                    base_size += self._estimate_control_size(child)
        elif isinstance(control, ft.Text):
            base_size += len(control.value or "") * 2 if hasattr(control, 'value') else 0
        elif isinstance(control, ft.Image):
            base_size += 4096  # Images are memory intensive
        elif isinstance(control, ft.Canvas):
            base_size += 8192  # Canvas is very memory intensive
        
        return base_size
    
    def invalidate(self, component_id: str) -> None:
        """Invalidate all cache entries for a component"""
        keys_to_remove = [
            key for key in self.cache
            if key.startswith(f"{component_id}:")
        ]
        
        for key in keys_to_remove:
            self._evict_entry(key)
        
        if keys_to_remove:
            logger.debug(f"Invalidated {len(keys_to_remove)} cache entries for component {component_id}")
    
    def invalidate_all(self) -> None:
        """Clear entire cache"""
        self.cache.clear()
        self.total_memory_estimate = 0
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.metrics["hits"] + self.metrics["misses"]
        hit_rate = self.metrics["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "memory_usage_mb": self.total_memory_estimate / (1024 * 1024),
            "memory_limit_mb": self.max_memory_bytes / (1024 * 1024),
            "hit_rate": hit_rate,
            "hits": self.metrics["hits"],
            "misses": self.metrics["misses"],
            "evictions": self.metrics["evictions"],
            "render_time_saved_ms": self.metrics["total_render_time_saved"] * 1000,
            "memory_high_water_mark_mb": self.metrics["memory_high_water_mark"] / (1024 * 1024)
        }
    
    def cleanup_expired(self) -> int:
        """Remove expired entries if TTL is set"""
        if self.ttl_seconds is None:
            return 0
        
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry.timestamp > self.ttl_seconds
        ]
        
        for key in expired_keys:
            self._evict_entry(key)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_memory_pressure(self) -> float:
        """Get current memory pressure (0.0 - 1.0)"""
        return self.total_memory_estimate / self.max_memory_bytes
    
    def resize(self, new_max_size: Optional[int] = None, new_max_memory_mb: Optional[int] = None) -> None:
        """Dynamically resize cache limits"""
        if new_max_size is not None:
            self.max_size = new_max_size
        
        if new_max_memory_mb is not None:
            self.max_memory_bytes = new_max_memory_mb * 1024 * 1024
        
        # Evict if needed with new limits
        self._evict_if_needed()
        
        logger.info(f"Cache resized: max_size={self.max_size}, max_memory={self.max_memory_bytes/(1024*1024):.1f}MB")


def _generate_component_hash(component: Component) -> str:
    """Generate hash of component state for validation"""
    # Create a string representation of component state
    state_str = f"{component.id}:{component.type}:{component.style.to_css()}"
    
    # Add relevant properties
    if hasattr(component, 'properties'):
        for key, value in sorted(component.properties.items()):
            state_str += f":{key}={value}"
    
    # Generate hash
    return hashlib.md5(state_str.encode()).hexdigest()


# Singleton cache instance
_global_cache: Optional[RenderCache] = None


def get_render_cache() -> RenderCache:
    """Get global render cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = RenderCache()
    return _global_cache


def clear_render_cache() -> None:
    """Clear global render cache"""
    global _global_cache
    if _global_cache is not None:
        _global_cache.invalidate_all()