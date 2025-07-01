"""
Canvas Rendering Module
High-performance visual rendering system for the Canvas Editor
Following CLAUDE.md guidelines for enterprise-grade performance
"""

from .canvas_renderer import CanvasRenderer, RenderContext
from .viewport_manager import ViewportManager, ViewportBounds
from .render_cache import RenderCache, CachedRender
from .selection_renderer import SelectionRenderer, SelectionHandle
from .grid_renderer import GridRenderer, GridPainter
from .render_object import RenderObject, RenderLayer
from .render_pipeline import RenderPipeline, RenderPhase

__all__ = [
    # Core rendering
    'CanvasRenderer',
    'RenderContext',
    'RenderPipeline',
    'RenderPhase',
    
    # Viewport management
    'ViewportManager',
    'ViewportBounds',
    
    # Caching
    'RenderCache',
    'CachedRender',
    
    # Visual features
    'SelectionRenderer',
    'SelectionHandle',
    'GridRenderer',
    'GridPainter',
    
    # Render objects
    'RenderObject',
    'RenderLayer'
]
