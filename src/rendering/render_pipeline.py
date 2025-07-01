"""
Render Pipeline Orchestration
Manages the complete rendering pipeline with proper phases and optimizations
Following CLAUDE.md guidelines for performance and extensibility
"""

from enum import Enum, auto
from typing import List, Dict, Any, Optional, Callable, Set
from dataclasses import dataclass
import time
import logging

from models.component import Component
from managers.state_types import ComponentTreeState, CanvasState, SelectionState
from managers.spatial_index import BoundingBox
from .render_object import RenderObject, RenderObjectFactory, RenderLayer
from .viewport_manager import ViewportManager

logger = logging.getLogger(__name__)


class RenderPhase(Enum):
    """
    Rendering pipeline phases
    CLAUDE.md #1.5: Profile before optimizing
    """
    PREPARE = auto()        # State preparation
    CULL = auto()          # Viewport culling
    BUILD = auto()         # Build render tree
    SORT = auto()          # Z-order sorting
    OPTIMIZE = auto()      # Apply optimizations
    RENDER = auto()        # Actual rendering
    COMPOSITE = auto()     # Layer compositing
    EFFECTS = auto()       # Post-processing effects
    OVERLAY = auto()       # UI overlays
    FINALIZE = auto()      # Cleanup and metrics


@dataclass
class RenderPhaseMetrics:
    """Metrics for a single render phase"""
    phase: RenderPhase
    duration_ms: float
    object_count: int
    memory_estimate: int = 0
    notes: str = ""


@dataclass
class RenderPipelineConfig:
    """Configuration for render pipeline"""
    enable_culling: bool = True
    enable_caching: bool = True
    enable_batching: bool = True
    enable_lod: bool = True
    enable_dirty_rects: bool = False  # Future
    max_render_objects: int = 10000
    target_fps: int = 60
    debug_mode: bool = False


class RenderPipeline:
    """
    Orchestrates the complete rendering pipeline
    CLAUDE.md #1.5: Performance-critical pipeline
    CLAUDE.md #12.1: Comprehensive metrics
    """
    
    def __init__(self, config: Optional[RenderPipelineConfig] = None):
        """Initialize render pipeline"""
        self.config = config or RenderPipelineConfig()
        
        # Pipeline phases
        self.phases: Dict[RenderPhase, Callable] = {
            RenderPhase.PREPARE: self._phase_prepare,
            RenderPhase.CULL: self._phase_cull,
            RenderPhase.BUILD: self._phase_build,
            RenderPhase.SORT: self._phase_sort,
            RenderPhase.OPTIMIZE: self._phase_optimize,
            RenderPhase.RENDER: self._phase_render,
            RenderPhase.COMPOSITE: self._phase_composite,
            RenderPhase.EFFECTS: self._phase_effects,
            RenderPhase.OVERLAY: self._phase_overlay,
            RenderPhase.FINALIZE: self._phase_finalize
        }
        
        # State
        self.render_objects: List[RenderObject] = []
        self.visible_objects: List[RenderObject] = []
        self.dirty_regions: Set[BoundingBox] = set()
        
        # Metrics
        self.frame_count = 0
        self.phase_metrics: List[RenderPhaseMetrics] = []
        self.total_metrics = {
            "frames_rendered": 0,
            "objects_culled": 0,
            "cache_hits": 0,
            "average_frame_time": 0,
            "dropped_frames": 0
        }
        
        # Phase-specific handlers
        self.render_handler: Optional[Callable] = None
        self.composite_handler: Optional[Callable] = None
        
        logger.info(f"RenderPipeline initialized with config: {config}")
    
    def execute(
        self,
        component_tree: ComponentTreeState,
        canvas_state: CanvasState,
        selection_state: SelectionState,
        viewport: ViewportManager
    ) -> Any:
        """
        Execute complete render pipeline
        Returns final rendered output
        """
        start_time = time.perf_counter()
        self.frame_count += 1
        self.phase_metrics.clear()
        
        # Pipeline context
        context = {
            "component_tree": component_tree,
            "canvas_state": canvas_state,
            "selection_state": selection_state,
            "viewport": viewport,
            "frame_number": self.frame_count,
            "render_output": None
        }
        
        # Execute each phase
        for phase in RenderPhase:
            phase_start = time.perf_counter()
            
            try:
                # Execute phase
                phase_handler = self.phases[phase]
                phase_handler(context)
                
                # Record metrics
                phase_duration = (time.perf_counter() - phase_start) * 1000
                self.phase_metrics.append(RenderPhaseMetrics(
                    phase=phase,
                    duration_ms=phase_duration,
                    object_count=len(self.visible_objects)
                ))
                
                if self.config.debug_mode:
                    logger.debug(f"Phase {phase.name} completed in {phase_duration:.2f}ms")
                
            except Exception as e:
                logger.error(f"Pipeline phase {phase.name} failed: {e}", exc_info=True)
                if phase in [RenderPhase.RENDER, RenderPhase.COMPOSITE]:
                    # Critical phases - abort pipeline
                    raise
        
        # Update total metrics
        total_time = (time.perf_counter() - start_time) * 1000
        self._update_total_metrics(total_time)
        
        # Check performance
        if total_time > (1000 / self.config.target_fps):
            self.total_metrics["dropped_frames"] += 1
            logger.warning(f"Frame {self.frame_count} took {total_time:.1f}ms (target: {1000/self.config.target_fps:.1f}ms)")
        
        return context.get("render_output")
    
    def _phase_prepare(self, context: Dict[str, Any]) -> None:
        """
        Phase 1: Prepare rendering state
        Validate inputs and prepare data structures
        """
        component_tree = context["component_tree"]
        
        # Clear previous state
        self.render_objects.clear()
        self.visible_objects.clear()
        
        # Validate state
        if not component_tree.component_map:
            logger.debug("No components to render")
            return
        
        # Update spatial index if needed
        if component_tree._spatial_index_manager:
            # Spatial index is already maintained by ComponentTreeState
            pass
    
    def _phase_cull(self, context: Dict[str, Any]) -> None:
        """
        Phase 2: Viewport culling
        Use spatial index to find visible components
        """
        if not self.config.enable_culling:
            # Skip culling - render everything
            self.visible_objects = self.render_objects
            return
        
        component_tree = context["component_tree"]
        viewport = context["viewport"]
        
        # Get viewport bounds with margin
        viewport_bounds = viewport.get_bounds()
        expanded_bounds = viewport_bounds.expand(100)  # 100px margin
        
        # Query spatial index
        visible_ids = component_tree.get_components_in_region(
            expanded_bounds.left,
            expanded_bounds.top,
            expanded_bounds.width,
            expanded_bounds.height
        )
        
        # Track culling metrics
        total_components = len(component_tree.component_map)
        culled_count = total_components - len(visible_ids)
        self.total_metrics["objects_culled"] += culled_count
        
        # Store visible IDs for build phase
        context["visible_ids"] = visible_ids
        
        logger.debug(f"Culled {culled_count} of {total_components} components")
    
    def _phase_build(self, context: Dict[str, Any]) -> None:
        """
        Phase 3: Build render tree
        Convert visible components to render objects
        """
        component_tree = context["component_tree"]
        selection_state = context["selection_state"]
        visible_ids = context.get("visible_ids", [])
        
        # Build render objects
        for component_id in visible_ids:
            component_data = component_tree.component_map.get(component_id)
            if not component_data:
                continue
            
            # Create component instance
            component = self._create_component_from_data(component_data)
            
            # Determine parent bounds
            parent_id = component_tree.parent_map.get(component_id)
            parent_bounds = None
            if parent_id:
                parent_obj = next((obj for obj in self.render_objects if obj.id == parent_id), None)
                if parent_obj:
                    parent_bounds = parent_obj.bounds
            
            # Create render object
            render_obj = RenderObjectFactory.create_from_component(component, parent_bounds)
            
            # Update interaction state
            render_obj.is_selected = component_id in selection_state.selected_ids
            
            self.render_objects.append(render_obj)
        
        # All objects are visible after culling
        self.visible_objects = self.render_objects.copy()
    
    def _phase_sort(self, context: Dict[str, Any]) -> None:
        """
        Phase 4: Sort by render order
        Sort objects by layer and z-index
        """
        # Sort by render priority (layer, z-index, selection)
        self.visible_objects.sort()
        
        # Group by layer for efficient rendering
        context["layers"] = self._group_by_layer(self.visible_objects)
    
    def _phase_optimize(self, context: Dict[str, Any]) -> None:
        """
        Phase 5: Apply rendering optimizations
        Batching, LOD, caching decisions
        """
        viewport = context["viewport"]
        
        for render_obj in self.visible_objects:
            # Level of Detail optimization
            if self.config.enable_lod:
                if render_obj.should_use_lod(viewport.zoom):
                    render_obj.metadata["use_lod"] = True
            
            # Mark objects that can be batched
            if self.config.enable_batching:
                if self._can_batch(render_obj):
                    render_obj.metadata["batchable"] = True
        
        # Identify render batches
        if self.config.enable_batching:
            context["render_batches"] = self._create_render_batches(self.visible_objects)
    
    def _phase_render(self, context: Dict[str, Any]) -> None:
        """
        Phase 6: Actual rendering
        Delegate to render handler
        """
        if not self.render_handler:
            logger.warning("No render handler set")
            return
        
        # Render objects
        render_output = self.render_handler(
            self.visible_objects,
            context
        )
        
        context["render_output"] = render_output
    
    def _phase_composite(self, context: Dict[str, Any]) -> None:
        """
        Phase 7: Layer compositing
        Combine rendered layers
        """
        if not self.composite_handler:
            # Default compositing is handled by render handler
            return
        
        layers = context.get("layers", {})
        render_output = context.get("render_output")
        
        # Composite layers
        composited = self.composite_handler(layers, render_output)
        context["render_output"] = composited
    
    def _phase_effects(self, context: Dict[str, Any]) -> None:
        """
        Phase 8: Post-processing effects
        Apply visual effects (blur, shadows, etc)
        """
        # Future: Implement post-processing pipeline
        pass
    
    def _phase_overlay(self, context: Dict[str, Any]) -> None:
        """
        Phase 9: UI overlays
        Add selection, guides, debug info
        """
        # Overlays are handled by the main renderer
        # This phase is for additional processing if needed
        pass
    
    def _phase_finalize(self, context: Dict[str, Any]) -> None:
        """
        Phase 10: Cleanup and metrics
        Clean up resources and record final metrics
        """
        # Clear dirty flags
        for render_obj in self.render_objects:
            if render_obj.needs_redraw:
                render_obj.mark_clean()
        
        # Clear dirty regions
        self.dirty_regions.clear()
        
        # Log performance if in debug mode
        if self.config.debug_mode:
            self._log_frame_metrics()
    
    def _create_component_from_data(self, data: Dict[str, Any]) -> Component:
        """Convert component data to Component instance"""
        from models.component import Component, ComponentStyle
        
        style = ComponentStyle(**data.get('style', {}))
        
        component = Component(
            id=data['id'],
            type=data.get('type', 'div'),
            name=data.get('name', ''),
            style=style,
            children=[]
        )
        
        # Set additional properties
        if 'properties' in data:
            component.properties = data['properties']
        if 'editor_selected' in data:
            component.editor_selected = data['editor_selected']
        if 'editor_locked' in data:
            component.editor_locked = data['editor_locked']
        if 'editor_visible' in data:
            component.editor_visible = data['editor_visible']
        
        return component
    
    def _group_by_layer(self, objects: List[RenderObject]) -> Dict[RenderLayer, List[RenderObject]]:
        """Group render objects by layer"""
        layers = {}
        for obj in objects:
            if obj.layer not in layers:
                layers[obj.layer] = []
            layers[obj.layer].append(obj)
        return layers
    
    def _can_batch(self, render_obj: RenderObject) -> bool:
        """Check if object can be batched with others"""
        # Simple components without effects can be batched
        component = render_obj.component
        
        if (not component.style.box_shadow and
            not component.style.transform and
            render_obj.opacity == 1.0 and
            render_obj.rotation == 0):
            return True
        
        return False
    
    def _create_render_batches(self, objects: List[RenderObject]) -> List[List[RenderObject]]:
        """Create batches of objects that can be rendered together"""
        batches = []
        current_batch = []
        
        for obj in objects:
            if obj.metadata.get("batchable") and len(current_batch) < 50:
                current_batch.append(obj)
            else:
                if current_batch:
                    batches.append(current_batch)
                current_batch = [obj] if obj.metadata.get("batchable") else []
        
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _update_total_metrics(self, frame_time: float) -> None:
        """Update running metrics"""
        self.total_metrics["frames_rendered"] += 1
        
        # Update average frame time
        avg = self.total_metrics["average_frame_time"]
        count = self.total_metrics["frames_rendered"]
        self.total_metrics["average_frame_time"] = (avg * (count - 1) + frame_time) / count
    
    def _log_frame_metrics(self) -> None:
        """Log detailed frame metrics"""
        total_time = sum(m.duration_ms for m in self.phase_metrics)
        
        logger.info(f"Frame {self.frame_count} metrics:")
        logger.info(f"  Total time: {total_time:.2f}ms")
        logger.info(f"  Objects rendered: {len(self.visible_objects)}")
        
        # Log slowest phases
        sorted_phases = sorted(self.phase_metrics, key=lambda m: m.duration_ms, reverse=True)
        for metric in sorted_phases[:3]:
            logger.info(f"  {metric.phase.name}: {metric.duration_ms:.2f}ms")
    
    # Public API
    
    def set_render_handler(self, handler: Callable) -> None:
        """Set the render phase handler"""
        self.render_handler = handler
    
    def set_composite_handler(self, handler: Callable) -> None:
        """Set the composite phase handler"""
        self.composite_handler = handler
    
    def mark_dirty(self, bounds: BoundingBox) -> None:
        """Mark a region as needing redraw"""
        self.dirty_regions.add(bounds)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get pipeline metrics"""
        return {
            "frame_count": self.frame_count,
            "average_frame_time_ms": self.total_metrics["average_frame_time"],
            "dropped_frames": self.total_metrics["dropped_frames"],
            "objects_culled_total": self.total_metrics["objects_culled"],
            "current_visible_objects": len(self.visible_objects),
            "dirty_regions": len(self.dirty_regions)
        }
    
    def get_phase_breakdown(self) -> Dict[str, float]:
        """Get time breakdown by phase for last frame"""
        breakdown = {}
        for metric in self.phase_metrics:
            breakdown[metric.phase.name] = metric.duration_ms
        return breakdown
    
    def reset_metrics(self) -> None:
        """Reset performance metrics"""
        self.frame_count = 0
        self.total_metrics = {
            "frames_rendered": 0,
            "objects_culled": 0,
            "cache_hits": 0,
            "average_frame_time": 0,
            "dropped_frames": 0
        }
        logger.info("Pipeline metrics reset")