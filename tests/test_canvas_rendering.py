"""
Comprehensive Tests for Canvas Rendering System
Tests performance, correctness, and integration of the rendering pipeline
Following CLAUDE.md guidelines for thorough testing
"""

import pytest
import unittest
from unittest.mock import Mock, MagicMock, patch
import time
import asyncio
from typing import List, Dict, Any
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rendering.canvas_renderer import CanvasRenderer, RenderContext
from rendering.viewport_manager import ViewportManager, ViewportBounds
from rendering.render_cache import RenderCache, CachedRender
from rendering.component_renderer import ComponentRenderer
from rendering.selection_renderer import SelectionRenderer, HandlePosition
from rendering.grid_renderer import GridRenderer, GridConfig
from rendering.render_object import RenderObject, RenderObjectFactory, RenderLayer
from rendering.render_pipeline import RenderPipeline, RenderPipelineConfig, RenderPhase
from models.component import Component, ComponentStyle
from managers.state_types import ComponentTreeState, CanvasState, SelectionState
from managers.spatial_index import BoundingBox, SpatialIndex


class TestViewportManager(unittest.TestCase):
    """Test viewport coordinate transformations and culling"""
    
    def setUp(self):
        """Set up test viewport"""
        self.viewport = ViewportManager(1200, 800)
    
    def test_viewport_initialization(self):
        """Test viewport initializes correctly"""
        self.assertEqual(self.viewport.screen_width, 1200)
        self.assertEqual(self.viewport.screen_height, 800)
        self.assertEqual(self.viewport.zoom, 1.0)
        self.assertEqual(self.viewport.pan_x, 0.0)
        self.assertEqual(self.viewport.pan_y, 0.0)
    
    def test_world_to_screen_transform(self):
        """Test world to screen coordinate transformation"""
        # At default zoom/pan
        sx, sy = self.viewport.world_to_screen(100, 50)
        self.assertEqual(sx, 100)
        self.assertEqual(sy, 50)
        
        # With zoom
        self.viewport.zoom = 2.0
        sx, sy = self.viewport.world_to_screen(100, 50)
        self.assertEqual(sx, 200)
        self.assertEqual(sy, 100)
        
        # With pan
        self.viewport.pan_x = 50
        self.viewport.pan_y = 25
        sx, sy = self.viewport.world_to_screen(100, 50)
        self.assertEqual(sx, 100)  # (100-50)*2
        self.assertEqual(sy, 50)   # (50-25)*2
    
    def test_screen_to_world_transform(self):
        """Test screen to world coordinate transformation"""
        # Set zoom and pan
        self.viewport.zoom = 2.0
        self.viewport.pan_x = 50
        self.viewport.pan_y = 25
        
        # Transform
        wx, wy = self.viewport.screen_to_world(100, 50)
        self.assertEqual(wx, 100)  # 100/2 + 50
        self.assertEqual(wy, 50)   # 50/2 + 25
    
    def test_viewport_bounds(self):
        """Test viewport bounds calculation"""
        bounds = self.viewport.get_bounds()
        self.assertEqual(bounds.left, 0)
        self.assertEqual(bounds.top, 0)
        self.assertEqual(bounds.right, 1200)
        self.assertEqual(bounds.bottom, 800)
        
        # With zoom
        self.viewport.zoom = 2.0
        bounds = self.viewport.get_bounds()
        self.assertEqual(bounds.right, 600)  # 1200/2
        self.assertEqual(bounds.bottom, 400)  # 800/2
    
    def test_zoom_with_focus(self):
        """Test zooming with focal point"""
        # Zoom in centered at (600, 400)
        self.viewport.apply_zoom(1.0, 600, 400)
        
        # Focal point should remain at same screen position
        wx, wy = self.viewport.screen_to_world(600, 400)
        self.viewport.apply_zoom(1.0, 600, 400)
        wx2, wy2 = self.viewport.screen_to_world(600, 400)
        
        self.assertAlmostEqual(wx, wx2, places=2)
        self.assertAlmostEqual(wy, wy2, places=2)
    
    def test_fit_to_bounds(self):
        """Test fitting viewport to bounds"""
        bbox = BoundingBox(100, 100, 400, 300)
        self.viewport.fit_to_bounds(bbox, padding=50)
        
        # Should zoom to fit with padding
        self.assertGreater(self.viewport.zoom, 1.0)
        
        # Should be centered
        bounds = self.viewport.get_bounds()
        center_x = (bounds.left + bounds.right) / 2
        center_y = (bounds.top + bounds.bottom) / 2
        
        self.assertAlmostEqual(center_x, 300, delta=10)  # Center of bbox
        self.assertAlmostEqual(center_y, 250, delta=10)


class TestRenderCache(unittest.TestCase):
    """Test render caching system"""
    
    def setUp(self):
        """Set up test cache"""
        self.cache = RenderCache(max_size=10, max_memory_mb=1)
        self.mock_render_func = Mock()
        self.mock_render_func.return_value = Mock(spec=['width', 'height'])
    
    def test_cache_miss_and_hit(self):
        """Test cache miss followed by hit"""
        component = self._create_test_component("test1")
        
        # First call - cache miss
        control1, was_cached1 = self.cache.get_or_render(
            component, self.mock_render_func
        )
        
        self.assertFalse(was_cached1)
        self.assertEqual(self.cache.metrics["misses"], 1)
        self.assertEqual(self.cache.metrics["hits"], 0)
        self.mock_render_func.assert_called_once()
        
        # Second call - cache hit
        control2, was_cached2 = self.cache.get_or_render(
            component, self.mock_render_func
        )
        
        self.assertTrue(was_cached2)
        self.assertEqual(self.cache.metrics["hits"], 1)
        self.assertEqual(self.mock_render_func.call_count, 1)  # Not called again
    
    def test_cache_invalidation(self):
        """Test cache invalidation on component change"""
        component = self._create_test_component("test1")
        
        # Cache component
        self.cache.get_or_render(component, self.mock_render_func)
        
        # Change component
        component.style.background_color = "#FF0000"
        
        # Should be cache miss
        control, was_cached = self.cache.get_or_render(
            component, self.mock_render_func
        )
        
        self.assertFalse(was_cached)
        self.assertEqual(self.mock_render_func.call_count, 2)
    
    def test_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        # Fill cache
        for i in range(10):
            component = self._create_test_component(f"test{i}")
            self.cache.get_or_render(component, self.mock_render_func)
        
        self.assertEqual(len(self.cache.cache), 10)
        
        # Add one more - should evict oldest
        component = self._create_test_component("test11")
        self.cache.get_or_render(component, self.mock_render_func)
        
        self.assertEqual(len(self.cache.cache), 10)
        self.assertEqual(self.cache.metrics["evictions"], 1)
        
        # First component should be evicted
        first_key = self.cache._generate_cache_key(
            self._create_test_component("test0")
        )
        self.assertNotIn(first_key, self.cache.cache)
    
    def test_memory_limit(self):
        """Test memory-based eviction"""
        # Create large component
        large_component = self._create_test_component("large")
        
        # Mock large size
        with patch.object(self.cache, '_estimate_control_size', return_value=500000):
            self.cache.get_or_render(large_component, self.mock_render_func)
        
        # Add more components - should trigger memory eviction
        for i in range(5):
            component = self._create_test_component(f"small{i}")
            with patch.object(self.cache, '_estimate_control_size', return_value=100000):
                self.cache.get_or_render(component, self.mock_render_func)
        
        # Should have evicted some entries
        self.assertGreater(self.cache.metrics["evictions"], 0)
        self.assertLess(self.cache.total_memory_estimate, self.cache.max_memory_bytes)
    
    def _create_test_component(self, id: str) -> Component:
        """Create test component"""
        return Component(
            id=id,
            type="div",
            name=f"Test {id}",
            style=ComponentStyle(
                width="100px",
                height="50px",
                background_color="#FFFFFF"
            )
        )


class TestComponentRenderer(unittest.TestCase):
    """Test component to visual rendering"""
    
    def setUp(self):
        """Set up test renderer"""
        self.renderer = ComponentRenderer()
        self.context = RenderContext(
            component=None,
            zoom_level=1.0,
            viewport_offset=(0, 0)
        )
    
    def test_render_text_component(self):
        """Test rendering text component"""
        component = Component(
            id="text1",
            type="text",
            name="Test Text",
            style=ComponentStyle(
                font_size="16px",
                color="#333333"
            ),
            properties={"text": "Hello World"}
        )
        
        self.context.component = component
        control = self.renderer.render_component(component, self.context)
        
        self.assertIsNotNone(control)
        # Should be wrapped in container
        self.assertTrue(hasattr(control, 'content'))
    
    def test_render_button_component(self):
        """Test rendering button component"""
        component = Component(
            id="btn1",
            type="button",
            name="Test Button",
            style=ComponentStyle(
                background_color="#5E6AD2"
            ),
            properties={
                "text": "Click Me",
                "variant": "primary"
            }
        )
        
        self.context.component = component
        control = self.renderer.render_component(component, self.context)
        
        self.assertIsNotNone(control)
    
    def test_css_dimension_parsing(self):
        """Test CSS dimension parsing"""
        # Pixels
        self.assertEqual(self.renderer._parse_dimension("100px", self.context), 100)
        
        # Percentage with parent
        context_with_parent = RenderContext(
            component=None,
            parent_width=500,
            zoom_level=1.0,
            viewport_offset=(0, 0)
        )
        self.assertEqual(
            self.renderer._parse_dimension("50%", context_with_parent), 
            250
        )
        
        # Auto
        self.assertIsNone(self.renderer._parse_dimension("auto", self.context))
    
    def test_render_with_children(self):
        """Test rendering component with children"""
        child1 = Component(
            id="child1",
            type="text",
            name="Child 1",
            style=ComponentStyle()
        )
        
        parent = Component(
            id="parent1",
            type="container",
            name="Parent",
            style=ComponentStyle(
                display="flex",
                flex_direction="row"
            ),
            children=[child1]
        )
        
        self.context.component = parent
        control = self.renderer.render_component(parent, self.context)
        
        self.assertIsNotNone(control)


@pytest.mark.performance
class TestRenderingPerformance(unittest.TestCase):
    """Test rendering performance requirements"""
    
    def setUp(self):
        """Set up performance tests"""
        self.renderer = CanvasRenderer((1920, 1080))
        self.pipeline = RenderPipeline(RenderPipelineConfig(
            target_fps=60,
            enable_culling=True,
            enable_caching=True
        ))
    
    def test_render_1000_components(self):
        """Test rendering 1000 components maintains 60fps"""
        # Create component tree with 1000 components
        component_tree = self._create_large_component_tree(1000)
        canvas_state = CanvasState()
        selection_state = SelectionState()
        
        # Warm up
        for _ in range(5):
            self.renderer.render(component_tree, canvas_state, selection_state)
        
        # Measure render time
        times = []
        for _ in range(60):  # 1 second worth of frames
            start = time.perf_counter()
            self.renderer.render(component_tree, canvas_state, selection_state)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        # Check performance
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"\nPerformance Results:")
        print(f"Average frame time: {avg_time:.2f}ms")
        print(f"Max frame time: {max_time:.2f}ms")
        print(f"FPS: {1000/avg_time:.1f}")
        
        # Assert 60fps target (16.67ms per frame)
        self.assertLess(avg_time, 16.67, "Average frame time exceeds 60fps target")
        self.assertLess(max_time, 20.0, "Max frame time too high")
    
    def test_viewport_culling_performance(self):
        """Test viewport culling reduces render load"""
        # Create large component tree
        component_tree = self._create_large_component_tree(5000)
        
        # Create spatial index
        spatial_index = SpatialIndex()
        for comp_id, comp_data in component_tree.component_map.items():
            x = float(comp_data.get('style', {}).get('left', 0))
            y = float(comp_data.get('style', {}).get('top', 0))
            width = float(comp_data.get('style', {}).get('width', 100))
            height = float(comp_data.get('style', {}).get('height', 50))
            
            spatial_index.insert(comp_id, BoundingBox(x, y, width, height))
        
        component_tree._spatial_index_manager = Mock()
        component_tree._spatial_index_manager.get_index.return_value = spatial_index
        
        # Render with culling
        canvas_state = CanvasState(zoom=1.0, pan_x=0, pan_y=0)
        selection_state = SelectionState()
        
        start = time.perf_counter()
        output = self.renderer.render(component_tree, canvas_state, selection_state)
        culled_time = time.perf_counter() - start
        
        # Get culling stats
        stats = self.renderer.get_performance_stats()
        culled_count = stats.get("culled_components", 0)
        
        print(f"\nCulling Performance:")
        print(f"Total components: 5000")
        print(f"Culled components: {culled_count}")
        print(f"Render time: {culled_time*1000:.2f}ms")
        
        # Should cull most components
        self.assertGreater(culled_count, 4000, "Not enough components culled")
        self.assertLess(culled_time, 0.05, "Culling taking too long")
    
    def test_cache_performance_impact(self):
        """Test cache improves performance"""
        component_tree = self._create_large_component_tree(500)
        canvas_state = CanvasState()
        selection_state = SelectionState()
        
        # Clear cache
        self.renderer.clear_cache()
        
        # First render - no cache
        times_no_cache = []
        for _ in range(10):
            self.renderer.clear_cache()
            start = time.perf_counter()
            self.renderer.render(component_tree, canvas_state, selection_state)
            times_no_cache.append(time.perf_counter() - start)
        
        # Warm up cache
        for _ in range(5):
            self.renderer.render(component_tree, canvas_state, selection_state)
        
        # Render with cache
        times_with_cache = []
        for _ in range(10):
            start = time.perf_counter()
            self.renderer.render(component_tree, canvas_state, selection_state)
            times_with_cache.append(time.perf_counter() - start)
        
        avg_no_cache = sum(times_no_cache) / len(times_no_cache)
        avg_with_cache = sum(times_with_cache) / len(times_with_cache)
        improvement = (avg_no_cache - avg_with_cache) / avg_no_cache * 100
        
        print(f"\nCache Performance:")
        print(f"Avg without cache: {avg_no_cache*1000:.2f}ms")
        print(f"Avg with cache: {avg_with_cache*1000:.2f}ms")
        print(f"Improvement: {improvement:.1f}%")
        
        # Cache should improve performance
        self.assertLess(avg_with_cache, avg_no_cache)
        self.assertGreater(improvement, 20)  # At least 20% improvement
    
    def _create_large_component_tree(self, count: int) -> ComponentTreeState:
        """Create component tree with many components"""
        tree = ComponentTreeState()
        
        # Create grid of components
        cols = int(count ** 0.5)
        rows = (count + cols - 1) // cols
        
        for i in range(count):
            row = i // cols
            col = i % cols
            
            component_data = {
                "id": f"comp_{i}",
                "type": "div",
                "style": {
                    "left": str(col * 120),
                    "top": str(row * 80),
                    "width": "100",
                    "height": "60",
                    "background_color": f"#{'%06x' % (i * 12345 % 0xFFFFFF)}"
                }
            }
            
            tree.add_component(component_data)
        
        return tree


class TestSelectionRenderer(unittest.TestCase):
    """Test selection UI rendering"""
    
    def setUp(self):
        """Set up test renderer"""
        self.renderer = SelectionRenderer()
        self.viewport = ViewportManager(1200, 800)
    
    def test_single_selection_rendering(self):
        """Test rendering single selection"""
        component = Component(
            id="comp1",
            type="div",
            name="Selected",
            style=ComponentStyle(
                left="100",
                top="100",
                width="200",
                height="100"
            )
        )
        
        control = self.renderer.render_selection(
            selected_ids=["comp1"],
            component_map={"comp1": component},
            viewport=self.viewport
        )
        
        self.assertIsNotNone(control)
    
    def test_multi_selection_rendering(self):
        """Test rendering multiple selection"""
        components = {
            "comp1": self._create_component("comp1", 100, 100),
            "comp2": self._create_component("comp2", 200, 200),
            "comp3": self._create_component("comp3", 300, 300)
        }
        
        control = self.renderer.render_selection(
            selected_ids=list(components.keys()),
            component_map=components,
            viewport=self.viewport
        )
        
        self.assertIsNotNone(control)
    
    def test_handle_visibility(self):
        """Test handle visibility based on constraints"""
        locked_component = Component(
            id="locked",
            type="div",
            name="Locked",
            style=ComponentStyle(),
            editor_locked=True
        )
        
        # Should not show handles for locked component
        self.assertFalse(
            self.renderer._can_resize(locked_component, HandlePosition.NORTH)
        )
    
    def _create_component(self, id: str, x: float, y: float) -> Component:
        """Create test component at position"""
        return Component(
            id=id,
            type="div",
            name=f"Component {id}",
            style=ComponentStyle(
                left=str(x),
                top=str(y),
                width="100",
                height="50"
            )
        )


class TestGridRenderer(unittest.TestCase):
    """Test grid and guide rendering"""
    
    def setUp(self):
        """Set up test renderer"""
        self.renderer = GridRenderer()
        self.viewport_bounds = ViewportBounds(0, 0, 1200, 800)
    
    def test_grid_rendering(self):
        """Test basic grid rendering"""
        grid = self.renderer.render_grid(
            viewport=self.viewport_bounds,
            grid_size=20,
            zoom=1.0
        )
        
        self.assertIsNotNone(grid)
    
    def test_grid_caching(self):
        """Test grid caching for performance"""
        # First render
        grid1 = self.renderer.render_grid(
            viewport=self.viewport_bounds,
            grid_size=20,
            zoom=1.0
        )
        
        # Second render - should hit cache
        grid2 = self.renderer.render_grid(
            viewport=self.viewport_bounds,
            grid_size=20,
            zoom=1.0
        )
        
        stats = self.renderer.get_metrics()
        self.assertGreater(stats["cache_hit_rate"], 0)
    
    def test_alignment_guides(self):
        """Test alignment guide detection"""
        active = BoundingBox(100, 100, 100, 50)
        targets = [
            BoundingBox(300, 100, 100, 50),  # Aligned top
            BoundingBox(100, 200, 100, 50),  # Aligned left
        ]
        
        guides = self.renderer.render_alignment_guides(
            active_bounds=active,
            target_bounds=targets,
            viewport=self.viewport_bounds,
            zoom=1.0
        )
        
        self.assertIsNotNone(guides)


class TestRenderPipeline(unittest.TestCase):
    """Test render pipeline orchestration"""
    
    def setUp(self):
        """Set up test pipeline"""
        self.pipeline = RenderPipeline(RenderPipelineConfig(
            enable_culling=True,
            enable_caching=True,
            debug_mode=True
        ))
        
        # Mock render handler
        self.mock_render_handler = Mock()
        self.mock_render_handler.return_value = Mock()
        self.pipeline.set_render_handler(self.mock_render_handler)
    
    def test_pipeline_phases(self):
        """Test all pipeline phases execute"""
        component_tree = ComponentTreeState()
        component_tree.add_component({
            "id": "test1",
            "type": "div",
            "style": {"left": "0", "top": "0", "width": "100", "height": "50"}
        })
        
        canvas_state = CanvasState()
        selection_state = SelectionState()
        viewport = ViewportManager()
        
        # Execute pipeline
        result = self.pipeline.execute(
            component_tree=component_tree,
            canvas_state=canvas_state,
            selection_state=selection_state,
            viewport=viewport
        )
        
        # Check phases executed
        self.assertEqual(len(self.pipeline.phase_metrics), len(RenderPhase))
        
        # Check render handler called
        self.mock_render_handler.assert_called_once()
    
    def test_pipeline_error_handling(self):
        """Test pipeline handles errors gracefully"""
        # Mock render handler that fails
        failing_handler = Mock(side_effect=Exception("Render failed"))
        self.pipeline.set_render_handler(failing_handler)
        
        component_tree = ComponentTreeState()
        canvas_state = CanvasState()
        selection_state = SelectionState()
        viewport = ViewportManager()
        
        # Should raise on critical phase failure
        with self.assertRaises(Exception):
            self.pipeline.execute(
                component_tree=component_tree,
                canvas_state=canvas_state,
                selection_state=selection_state,
                viewport=viewport
            )
    
    def test_pipeline_metrics(self):
        """Test pipeline performance metrics"""
        component_tree = ComponentTreeState()
        for i in range(100):
            component_tree.add_component({
                "id": f"test{i}",
                "type": "div",
                "style": {"left": str(i*10), "top": str(i*10)}
            })
        
        canvas_state = CanvasState()
        selection_state = SelectionState()
        viewport = ViewportManager()
        
        # Execute multiple frames
        for _ in range(10):
            self.pipeline.execute(
                component_tree=component_tree,
                canvas_state=canvas_state,
                selection_state=selection_state,
                viewport=viewport
            )
        
        # Check metrics
        metrics = self.pipeline.get_metrics()
        self.assertEqual(metrics["frame_count"], 10)
        self.assertGreater(metrics["average_frame_time_ms"], 0)
        
        # Check phase breakdown
        phase_breakdown = self.pipeline.get_phase_breakdown()
        self.assertEqual(len(phase_breakdown), len(RenderPhase))


if __name__ == '__main__':
    # Run performance tests separately
    if '--performance' in sys.argv:
        # Run only performance tests
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add performance test classes
        suite.addTests(loader.loadTestsFromTestCase(TestRenderingPerformance))
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
    else:
        # Run all tests
        unittest.main(verbosity=2)