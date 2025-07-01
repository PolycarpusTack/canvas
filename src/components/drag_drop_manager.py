"""
Enhanced Drag and Drop Manager for Component Library
Handles drag-and-drop operations with visual feedback and spatial indexing
Following CLAUDE.md guidelines for enterprise-grade drag & drop
"""

from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import logging
import time
from uuid import uuid4

from component_types import ComponentDefinition, ValidationResult
from component_registry import ComponentRegistry, get_component_registry
from component_factory import ComponentFactory, get_component_factory
from models.component import Component
from drag_visual_feedback import DragVisualFeedback, VisualFeedbackConfig, FeedbackState, get_visual_feedback
from spatial_drag_index import SpatialDragIndex, DropZone, get_spatial_drag_index
from managers.spatial_index import BoundingBox


logger = logging.getLogger(__name__)


class DropZoneType(Enum):
    """Types of drop zones"""
    CANVAS = "canvas"
    COMPONENT = "component"
    SLOT = "slot"
    TRASH = "trash"


class DragOperation(Enum):
    """Types of drag operations"""
    COPY = "copy"
    MOVE = "move"
    CLONE = "clone"


@dataclass
class DragData:
    """Data carried during drag operation"""
    operation: DragOperation
    source_type: str  # "library", "canvas", "tree"
    component_id: Optional[str] = None  # For library components
    instance_id: Optional[str] = None   # For canvas instances
    component_data: Optional[Dict[str, Any]] = None
    properties: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_json(self) -> str:
        """Serialize drag data to JSON"""
        return json.dumps({
            "operation": self.operation.value,
            "source_type": self.source_type,
            "component_id": self.component_id,
            "instance_id": self.instance_id,
            "component_data": self.component_data,
            "properties": self.properties,
            "metadata": self.metadata
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DragData':
        """Deserialize drag data from JSON"""
        data = json.loads(json_str)
        return cls(
            operation=DragOperation(data["operation"]),
            source_type=data["source_type"],
            component_id=data.get("component_id"),
            instance_id=data.get("instance_id"),
            component_data=data.get("component_data"),
            properties=data.get("properties"),
            metadata=data.get("metadata")
        )


@dataclass
class DropTarget:
    """Information about a drop target"""
    zone_type: DropZoneType
    target_id: Optional[str] = None  # Component or slot ID
    slot_name: Optional[str] = None
    position: Optional[int] = None   # Insert position
    accepts: List[str] = None        # Accepted component types
    
    def can_accept(self, component_type: str) -> bool:
        """Check if target can accept component type"""
        if not self.accepts:
            return True
        return "*" in self.accepts or component_type in self.accepts


@dataclass
class DragDropEvent:
    """Drag and drop event data"""
    event_type: str  # "drag_start", "drag_over", "drop", "drag_end"
    drag_data: DragData
    drop_target: Optional[DropTarget] = None
    mouse_position: Optional[Tuple[int, int]] = None
    modifiers: Optional[List[str]] = None  # "ctrl", "shift", "alt"
    timestamp: float = 0.0


class DragDropManager:
    """
    Enhanced drag and drop manager with visual feedback and spatial indexing
    CLAUDE.md #1.5: Optimize for common operations
    CLAUDE.md #9.1: Accessible drag operations
    CLAUDE.md #12.1: Performance monitoring
    """
    
    def __init__(
        self,
        registry: Optional[ComponentRegistry] = None,
        factory: Optional[ComponentFactory] = None,
        visual_config: Optional[VisualFeedbackConfig] = None
    ):
        """Initialize the enhanced drag and drop manager"""
        self.registry = registry or get_component_registry()
        self.factory = factory or get_component_factory()
        
        # Enhanced systems
        self.visual_feedback = get_visual_feedback(visual_config)
        self.spatial_index = get_spatial_drag_index()
        
        # Event handlers
        self._drag_start_handlers: List[Callable[[DragDropEvent], None]] = []
        self._drag_over_handlers: List[Callable[[DragDropEvent], bool]] = []
        self._drop_handlers: List[Callable[[DragDropEvent], bool]] = []
        self._drag_end_handlers: List[Callable[[DragDropEvent], None]] = []
        
        # Current drag state
        self._current_drag: Optional[DragData] = None
        self._current_drop_target: Optional[DropTarget] = None
        self._valid_drop_targets: List[DropTarget] = []
        self._preview_component: Optional[Component] = None
        self._drag_start_time: float = 0.0
        
        # Drop zone registry (maintained for compatibility)
        self._drop_zones: Dict[str, DropTarget] = {}
        
        # Drag constraints
        self._max_drag_distance = 1000  # pixels
        self._min_drop_zone_size = (20, 20)  # width, height
        self._snap_threshold = 10  # pixels for snapping
        
        # Performance metrics
        self._drag_count = 0
        self._successful_drops = 0
        self._avg_drag_duration = 0.0
        
        logger.info("Enhanced drag and drop manager initialized")
    
    def start_drag(
        self,
        component_id: Optional[str] = None,
        instance_id: Optional[str] = None,
        operation: DragOperation = DragOperation.COPY,
        source_type: str = "library",
        properties: Optional[Dict[str, Any]] = None,
        mouse_position: Optional[Tuple[float, float]] = None
    ) -> DragData:
        """
        Start an enhanced drag operation with visual feedback
        CLAUDE.md #2.1.1: Validate all inputs
        CLAUDE.md #12.1: Track performance metrics
        
        Args:
            component_id: ID of component definition (for library drags)
            instance_id: ID of component instance (for canvas drags)
            operation: Type of drag operation
            source_type: Source of the drag ("library", "canvas", "tree")
            properties: Optional component properties
            mouse_position: Current mouse position for visual feedback
            
        Returns:
            DragData object for the operation
        """
        try:
            # Validate inputs
            if not component_id and not instance_id:
                raise ValueError("Either component_id or instance_id must be provided")
            
            # Start performance tracking
            self._drag_start_time = time.perf_counter()
            self._drag_count += 1
            
            # Create drag data
            drag_data = DragData(
                operation=operation,
                source_type=source_type,
                component_id=component_id,
                instance_id=instance_id,
                properties=properties,
                metadata={
                    "start_time": self._get_timestamp(),
                    "mouse_position": mouse_position
                }
            )
            
            # Store current drag state
            self._current_drag = drag_data
            
            # Generate preview component
            source_component = None
            if component_id:
                try:
                    self._preview_component = self.factory.create_component(
                        component_id, properties
                    )
                    source_component = self._preview_component
                except Exception as e:
                    logger.error(f"Failed to create preview component: {e}")
                    self._preview_component = None
            
            # Start visual feedback
            self.visual_feedback.start_drag_feedback(
                drag_data,
                source_component,
                mouse_position
            )
            
            # Calculate valid drop targets using spatial index
            self._calculate_valid_drop_targets_enhanced(drag_data)
            
            # Notify handlers
            event = DragDropEvent(
                event_type="drag_start",
                drag_data=drag_data,
                mouse_position=mouse_position,
                timestamp=self._get_timestamp()
            )
            self._notify_drag_start_handlers(event)
            
            logger.info(
                f"Started enhanced drag operation",
                extra={
                    "operation": drag_data.operation.value,
                    "source_type": source_type,
                    "component_id": component_id,
                    "has_mouse_position": mouse_position is not None
                }
            )
            
            return drag_data
            
        except Exception as e:
            logger.error(f"Failed to start drag operation: {e}")
            # Cleanup on failure
            self.end_drag()
            raise
    
    def handle_drag_over(
        self,
        mouse_position: Tuple[float, float],
        modifiers: Optional[List[str]] = None
    ) -> bool:
        """
        Enhanced drag over handling with spatial indexing and visual feedback
        CLAUDE.md #1.5: Efficient spatial queries
        
        Args:
            mouse_position: Current mouse position
            modifiers: Keyboard modifiers (ctrl, shift, alt)
            
        Returns:
            True if drop is allowed, False otherwise
        """
        if not self._current_drag:
            return False
        
        try:
            # Update ghost position
            self.visual_feedback.update_ghost_position(mouse_position)
            
            # Find drop zones at mouse position using spatial index
            component_type = self._current_drag.component_id
            query_result = self.spatial_index.find_drop_zones_at_point(
                mouse_position[0],
                mouse_position[1],
                component_type
            )
            
            # Get the best drop target (deepest valid zone)
            best_drop_zone = None
            best_drop_target = None
            
            for drop_zone in query_result.drop_zones:
                # Validate drop target
                if self._validate_drop_target_enhanced(self._current_drag, drop_zone):
                    best_drop_zone = drop_zone
                    best_drop_target = drop_zone.target
                    break  # Take first (deepest) valid zone
            
            # Update visual feedback
            if best_drop_zone != self._current_drop_target:
                # Clear previous feedback
                if self._current_drop_target:
                    self.visual_feedback.update_drop_zone_feedback(
                        self._current_drop_target,
                        FeedbackState.HOVER,
                        None  # Clear bounds
                    )
                
                # Set new feedback
                if best_drop_zone:
                    bounds = (
                        best_drop_zone.bounds.x,
                        best_drop_zone.bounds.y,
                        best_drop_zone.bounds.width,
                        best_drop_zone.bounds.height
                    )
                    
                    insertion_point = self._calculate_insertion_point(
                        best_drop_zone,
                        mouse_position
                    )
                    
                    self.visual_feedback.update_drop_zone_feedback(
                        best_drop_zone.target,
                        FeedbackState.VALID,
                        bounds,
                        insertion_point
                    )
                
                self._current_drop_target = best_drop_zone.target if best_drop_zone else None
            
            # Create event for handlers
            event = DragDropEvent(
                event_type="drag_over",
                drag_data=self._current_drag,
                drop_target=best_drop_target,
                mouse_position=mouse_position,
                modifiers=modifiers or [],
                timestamp=self._get_timestamp()
            )
            
            # Notify handlers (they can override validation)
            is_valid = best_drop_target is not None
            for handler in self._drag_over_handlers:
                try:
                    handler_result = handler(event)
                    if handler_result is not None:
                        is_valid = handler_result
                except Exception as e:
                    logger.error(f"Error in drag over handler: {e}")
            
            # Show invalid feedback if needed
            if not is_valid and query_result.drop_zones:
                # Found zones but none are valid
                invalid_zone = query_result.drop_zones[0]
                self.visual_feedback.show_invalid_drop_feedback(
                    invalid_zone.target,
                    "Component type not accepted"
                )
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error in drag over handling: {e}")
            return False
    
    def handle_drop(
        self,
        mouse_position: Optional[Tuple[float, float]] = None,
        modifiers: Optional[List[str]] = None
    ) -> bool:
        """
        Enhanced drop handling with spatial indexing and visual feedback
        CLAUDE.md #2.1.1: Validate all drop operations
        CLAUDE.md #12.1: Track performance metrics
        
        Args:
            mouse_position: Current mouse position for drop
            modifiers: Keyboard modifiers (ctrl, shift, alt)
            
        Returns:
            True if drop was successful, False otherwise
        """
        if not self._current_drag:
            logger.warning("Drop attempted with no active drag")
            self.visual_feedback.show_invalid_drop_feedback(
                DropTarget(zone_type=DropZoneType.CANVAS),
                "No active drag operation"
            )
            return False
        
        try:
            start_time = time.perf_counter()
            
            # Find drop target at current position using spatial index
            drop_target = None
            if mouse_position:
                component_type = self._current_drag.component_id
                query_result = self.spatial_index.find_drop_zones_at_point(
                    mouse_position[0],
                    mouse_position[1],
                    component_type
                )
                
                # Get the best (deepest) valid drop zone
                for drop_zone in query_result.drop_zones:
                    if self._validate_drop_target_enhanced(self._current_drag, drop_zone):
                        drop_target = drop_zone.target
                        break
            
            if not drop_target:
                logger.warning("No valid drop target found")
                self.visual_feedback.show_invalid_drop_feedback(
                    self._current_drop_target or DropTarget(zone_type=DropZoneType.CANVAS),
                    "Invalid drop location"
                )
                return False
            
            # Final validation
            if not self._validate_drop_target(self._current_drag, drop_target):
                logger.warning(f"Drop validation failed: {drop_target}")
                self.visual_feedback.show_invalid_drop_feedback(
                    drop_target,
                    "Drop not allowed here"
                )
                return False
            
            # Create drop event
            event = DragDropEvent(
                event_type="drop",
                drag_data=self._current_drag,
                drop_target=drop_target,
                mouse_position=mouse_position,
                modifiers=modifiers or [],
                timestamp=self._get_timestamp()
            )
            
            # Show success feedback
            self.visual_feedback.update_drop_zone_feedback(
                drop_target,
                FeedbackState.VALID
            )
            
            # Process the drop
            success = self._process_drop(event)
            
            # Notify handlers (they can override the result)
            for handler in self._drop_handlers:
                try:
                    handler_result = handler(event)
                    if handler_result is not None:
                        success = handler_result
                except Exception as e:
                    logger.error(f"Error in drop handler: {e}")
            
            # Update performance metrics
            if success:
                self._successful_drops += 1
                
                # Calculate drag duration
                if self._drag_start_time > 0:
                    drag_duration = time.perf_counter() - self._drag_start_time
                    
                    # Update rolling average
                    if self._avg_drag_duration == 0:
                        self._avg_drag_duration = drag_duration
                    else:
                        # Exponential moving average
                        alpha = 0.1
                        self._avg_drag_duration = (
                            alpha * drag_duration + 
                            (1 - alpha) * self._avg_drag_duration
                        )
                
                logger.info(
                    f"Drop successful: {self._current_drag.operation.value} to {drop_target.zone_type.value}",
                    extra={
                        "operation": self._current_drag.operation.value,
                        "target_type": drop_target.zone_type.value,
                        "target_id": drop_target.target_id,
                        "duration_ms": (time.perf_counter() - start_time) * 1000
                    }
                )
            else:
                logger.warning("Drop operation failed")
                self.visual_feedback.show_invalid_drop_feedback(
                    drop_target,
                    "Drop operation failed"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error in drop handling: {e}")
            if drop_target:
                self.visual_feedback.show_invalid_drop_feedback(
                    drop_target,
                    f"Drop error: {str(e)}"
                )
            return False
        finally:
            # Always clean up drag state
            self.end_drag()
    
    def end_drag(self):
        """
        End the current drag operation with proper cleanup
        CLAUDE.md #2.1.4: Proper resource cleanup
        """
        if not self._current_drag:
            return
        
        try:
            # Create end event
            event = DragDropEvent(
                event_type="drag_end",
                drag_data=self._current_drag,
                timestamp=self._get_timestamp()
            )
            
            # Clear all visual feedback
            self.visual_feedback.clear_all_feedback()
            
            # Notify handlers
            self._notify_drag_end_handlers(event)
            
            # Clear drag state
            drag_data = self._current_drag
            self._current_drag = None
            self._current_drop_target = None
            self._valid_drop_targets.clear()
            self._preview_component = None
            self._drag_start_time = 0.0
            
            logger.debug(
                f"Drag operation ended",
                extra={
                    "operation": drag_data.operation.value,
                    "source_type": drag_data.source_type,
                    "component_id": drag_data.component_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error ending drag operation: {e}")
    
    def register_drop_zone(self, zone_id: str, drop_target: DropTarget):
        """Register a drop zone"""
        self._drop_zones[zone_id] = drop_target
        logger.debug(f"Registered drop zone: {zone_id}")
    
    def unregister_drop_zone(self, zone_id: str):
        """Unregister a drop zone"""
        if zone_id in self._drop_zones:
            del self._drop_zones[zone_id]
            logger.debug(f"Unregistered drop zone: {zone_id}")
    
    def get_valid_drop_targets(self) -> List[DropTarget]:
        """Get list of valid drop targets for current drag"""
        return self._valid_drop_targets.copy()
    
    def get_preview_component(self) -> Optional[Component]:
        """Get preview component for current drag"""
        return self._preview_component
    
    def is_dragging(self) -> bool:
        """Check if there's an active drag operation"""
        return self._current_drag is not None
    
    def get_current_drag(self) -> Optional[DragData]:
        """Get current drag data"""
        return self._current_drag
    
    # Event handler registration
    
    def add_drag_start_handler(self, handler: Callable[[DragDropEvent], None]):
        """Add drag start event handler"""
        self._drag_start_handlers.append(handler)
    
    def add_drag_over_handler(self, handler: Callable[[DragDropEvent], bool]):
        """Add drag over event handler (returns True if drop allowed)"""
        self._drag_over_handlers.append(handler)
    
    def add_drop_handler(self, handler: Callable[[DragDropEvent], bool]):
        """Add drop event handler (returns True if drop successful)"""
        self._drop_handlers.append(handler)
    
    def add_drag_end_handler(self, handler: Callable[[DragDropEvent], None]):
        """Add drag end event handler"""
        self._drag_end_handlers.append(handler)
    
    # Private methods
    
    def _validate_drop_target(self, drag_data: DragData, drop_target: DropTarget) -> bool:
        """Validate if a drop operation is allowed"""
        # Check if drag data is valid
        if not drag_data.component_id and not drag_data.instance_id:
            return False
        
        # Get component definition
        component_def = None
        if drag_data.component_id:
            component_def = self.registry.get(drag_data.component_id)
            if not component_def:
                return False
        
        # Check component constraints
        if component_def:
            # Check if target accepts the component type
            if not drop_target.can_accept(component_def.id):
                return False
            
            # Validate parent-child relationships
            if drop_target.target_id:
                validation = self.registry.validate_parent_child(
                    drop_target.target_id,
                    component_def.id
                )
                if not validation.is_valid:
                    return False
        
        # Check drop zone type specific rules
        if drop_target.zone_type == DropZoneType.TRASH:
            # Only allow move operations to trash
            return drag_data.operation == DragOperation.MOVE
        
        elif drop_target.zone_type == DropZoneType.SLOT:
            # Check slot constraints
            if drop_target.slot_name and component_def:
                # This would need integration with the canvas component tree
                # For now, assume slot validation is handled elsewhere
                pass
        
        return True
    
    def _calculate_valid_drop_targets_enhanced(self, drag_data: DragData):
        """
        Calculate valid drop targets using spatial index and component registry
        CLAUDE.md #1.5: Optimize drop target calculation
        """
        try:
            self._valid_drop_targets.clear()
            
            # Get component definition for validation
            component_def = None
            if drag_data.component_id:
                component_def = self.registry.get(drag_data.component_id)
                if not component_def:
                    logger.warning(f"Component definition not found: {drag_data.component_id}")
                    return
            
            # Query spatial index for all potential drop zones
            all_drop_zones = self.spatial_index.find_drop_zones_in_region(
                self.spatial_index._get_canvas_bounds(),  # Get full canvas bounds
                drag_data.component_id
            )
            
            # Validate each potential drop zone
            for drop_zone in all_drop_zones.drop_zones:
                if self._validate_drop_target_enhanced(drag_data, drop_zone):
                    self._valid_drop_targets.append(drop_zone.target)
            
            # Add registered drop zones (legacy compatibility)
            for zone_id, drop_target in self._drop_zones.items():
                if self._validate_drop_target(drag_data, drop_target):
                    if drop_target not in self._valid_drop_targets:
                        self._valid_drop_targets.append(drop_target)
            
            # Add default canvas drop zone for library components
            if component_def and drag_data.source_type == "library":
                canvas_target = DropTarget(
                    zone_type=DropZoneType.CANVAS,
                    accepts=["*"]
                )
                if canvas_target not in self._valid_drop_targets:
                    self._valid_drop_targets.append(canvas_target)
            
            logger.debug(
                f"Found {len(self._valid_drop_targets)} valid drop targets",
                extra={
                    "component_id": drag_data.component_id,
                    "source_type": drag_data.source_type
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating drop targets: {e}")
            self._valid_drop_targets.clear()
    
    def _validate_drop_target_enhanced(self, drag_data: DragData, drop_zone) -> bool:
        """
        Enhanced drop target validation using spatial indexing
        CLAUDE.md #2.1.1: Comprehensive validation
        """
        try:
            # Basic validation using existing method
            if not self._validate_drop_target(drag_data, drop_zone.target):
                return False
            
            # Additional spatial validation
            component_def = None
            if drag_data.component_id:
                component_def = self.registry.get(drag_data.component_id)
            
            # Check component-specific constraints
            if component_def and drop_zone.accepts:
                # Check if zone accepts this component type
                if "*" not in drop_zone.accepts and drag_data.component_id not in drop_zone.accepts:
                    return False
            
            # Check depth constraints (prevent infinite nesting)
            if drop_zone.depth > 10:  # Maximum nesting level
                return False
            
            # Check for circular dependencies (component can't be dropped into itself)
            if drag_data.instance_id and drop_zone.target.target_id:
                if self._would_create_circular_reference(
                    drag_data.instance_id, 
                    drop_zone.target.target_id
                ):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating drop target: {e}")
            return False
    
    def _would_create_circular_reference(self, component_id: str, target_id: str) -> bool:
        """
        Check if dropping component into target would create circular reference
        CLAUDE.md #2.1.1: Prevent invalid hierarchies
        """
        # This would need integration with the component tree to check ancestry
        # For now, simple check if trying to drop into self
        return component_id == target_id
    
    def _calculate_insertion_point(
        self,
        drop_zone,
        mouse_position: Tuple[float, float]
    ) -> Optional[Tuple[float, float, str]]:
        """
        Calculate insertion point for visual feedback
        CLAUDE.md #1.5: Efficient geometric calculations
        """
        try:
            bounds = drop_zone.bounds
            x, y = mouse_position
            
            # Calculate relative position within the drop zone
            rel_x = (x - bounds.x) / bounds.width
            rel_y = (y - bounds.y) / bounds.height
            
            # Determine insertion orientation based on zone type
            if drop_zone.target.zone_type == DropZoneType.CANVAS:
                # For canvas, show insertion at mouse position
                return (x, y, "point")
            
            elif drop_zone.target.zone_type == DropZoneType.COMPONENT:
                # For components, show insertion line based on position
                if rel_y < 0.2:  # Top 20%
                    return (bounds.x + bounds.width / 2, bounds.y, "horizontal")
                elif rel_y > 0.8:  # Bottom 20%
                    return (bounds.x + bounds.width / 2, bounds.y + bounds.height, "horizontal")
                elif rel_x < 0.2:  # Left 20%
                    return (bounds.x, bounds.y + bounds.height / 2, "vertical")
                elif rel_x > 0.8:  # Right 20%
                    return (bounds.x + bounds.width, bounds.y + bounds.height / 2, "vertical")
                else:  # Center - child insertion
                    return (bounds.x + bounds.width / 2, bounds.y + bounds.height / 2, "child")
            
            else:
                # Default to center point
                return (bounds.x + bounds.width / 2, bounds.y + bounds.height / 2, "point")
            
        except Exception as e:
            logger.error(f"Error calculating insertion point: {e}")
            return None
    
    def _process_drop(self, event: DragDropEvent) -> bool:
        """Process the actual drop operation"""
        drag_data = event.drag_data
        drop_target = event.drop_target
        
        if not drop_target:
            return False
        
        try:
            if drop_target.zone_type == DropZoneType.CANVAS:
                return self._handle_canvas_drop(drag_data, drop_target, event)
            
            elif drop_target.zone_type == DropZoneType.COMPONENT:
                return self._handle_component_drop(drag_data, drop_target, event)
            
            elif drop_target.zone_type == DropZoneType.SLOT:
                return self._handle_slot_drop(drag_data, drop_target, event)
            
            elif drop_target.zone_type == DropZoneType.TRASH:
                return self._handle_trash_drop(drag_data, drop_target, event)
            
            else:
                logger.warning(f"Unknown drop zone type: {drop_target.zone_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing drop: {e}")
            return False
    
    def _handle_canvas_drop(
        self,
        drag_data: DragData,
        drop_target: DropTarget,
        event: DragDropEvent
    ) -> bool:
        """Handle drop onto canvas"""
        if drag_data.source_type == "library" and drag_data.component_id:
            # Create new component instance
            try:
                component = self.factory.create_component(
                    drag_data.component_id,
                    drag_data.properties
                )
                
                # Set position if mouse position available
                if event.mouse_position:
                    component.style.position = "absolute"
                    component.style.left = f"{event.mouse_position[0]}px"
                    component.style.top = f"{event.mouse_position[1]}px"
                
                # The actual canvas integration would happen here
                # For now, we just log the successful creation
                logger.info(f"Created component on canvas: {component.id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to create component: {e}")
                return False
        
        return False
    
    def _handle_component_drop(
        self,
        drag_data: DragData,
        drop_target: DropTarget,
        event: DragDropEvent
    ) -> bool:
        """Handle drop onto another component"""
        # This would integrate with the canvas component tree
        # to add the dragged component as a child
        logger.info(f"Component drop onto {drop_target.target_id}")
        return True
    
    def _handle_slot_drop(
        self,
        drag_data: DragData,
        drop_target: DropTarget,
        event: DragDropEvent
    ) -> bool:
        """Handle drop into a component slot"""
        # This would integrate with the slot system
        logger.info(f"Slot drop into {drop_target.slot_name}")
        return True
    
    def _handle_trash_drop(
        self,
        drag_data: DragData,
        drop_target: DropTarget,
        event: DragDropEvent
    ) -> bool:
        """Handle drop into trash (delete)"""
        if drag_data.operation == DragOperation.MOVE and drag_data.instance_id:
            # This would integrate with the canvas to remove the component
            logger.info(f"Deleted component: {drag_data.instance_id}")
            return True
        return False
    
    def _notify_drag_start_handlers(self, event: DragDropEvent):
        """Notify drag start handlers"""
        for handler in self._drag_start_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in drag start handler: {e}")
    
    def _notify_drag_end_handlers(self, event: DragDropEvent):
        """Notify drag end handlers"""
        for handler in self._drag_end_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in drag end handler: {e}")
    
    def _get_timestamp(self) -> float:
        """Get current timestamp"""
        import time
        return time.time()
    
    def cleanup(self) -> None:
        """
        Clean up drag & drop manager resources
        
        CLAUDE.md Implementation:
        - #2.1.4: Proper resource cleanup
        - #12.1: Clean performance metrics
        """
        try:
            # End any active drag operation
            if self._current_drag:
                self.end_drag()
            
            # Clear visual feedback
            if self.visual_feedback:
                self.visual_feedback.clear_all_feedback()
            
            # Clear spatial index
            if self.spatial_index:
                self.spatial_index.clear()
            
            # Clear event handlers
            self._drag_start_handlers.clear()
            self._drag_over_handlers.clear()
            self._drop_handlers.clear()
            self._drag_end_handlers.clear()
            
            # Clear drop zones
            self._drop_zones.clear()
            
            # Clear performance metrics
            self.metrics["frame_times"].clear()
            self.metrics["component_counts"].clear()
            self.metrics["cache_hits"] = 0
            self.metrics["cache_misses"] = 0
            self.metrics["culled_components"] = 0
            
            # Reset counters
            self._drag_count = 0
            self._successful_drops = 0
            self._avg_drag_duration = 0.0
            
            logger.info("Drag & drop manager cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during drag & drop cleanup: {e}")


# Global drag drop manager instance
_drag_drop_manager_instance: Optional[DragDropManager] = None


def get_drag_drop_manager() -> DragDropManager:
    """Get the global drag drop manager instance"""
    global _drag_drop_manager_instance
    if _drag_drop_manager_instance is None:
        _drag_drop_manager_instance = DragDropManager()
    return _drag_drop_manager_instance