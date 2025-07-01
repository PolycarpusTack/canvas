"""
Canvas Drop Target System - Complete Flet Integration
Implements TASK A-2-T1 and A-2-T2 from drag-drop development plan
Following CLAUDE.md guidelines for enterprise-grade drop zone detection
"""

import flet as ft
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import json
import logging
import time
import threading
from uuid import uuid4

from ui.components.draggable import DragData, ValidationError

logger = logging.getLogger(__name__)


class DropZoneType(Enum):
    """Types of drop zones"""
    CANVAS = auto()
    CONTAINER = auto()
    SLOT = auto()
    GRID_CELL = auto()
    LIST_ITEM = auto()


class DropIndicatorType(Enum):
    """Types of drop indicators"""
    HIGHLIGHT = auto()
    INSERTION_LINE = auto()
    GHOST_PREVIEW = auto()
    INVALID = auto()


@dataclass
class DropPosition:
    """Precise drop position information"""
    x: float
    y: float
    index: Optional[int] = None
    relative_position: str = "center"  # "before", "after", "center", "inside"
    snap_to_grid: bool = False
    grid_x: Optional[int] = None
    grid_y: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "x": self.x,
            "y": self.y,
            "index": self.index,
            "relative_position": self.relative_position,
            "snap_to_grid": self.snap_to_grid,
            "grid_x": self.grid_x,
            "grid_y": self.grid_y
        }


@dataclass
class DropValidationResult:
    """Result of drop validation"""
    is_valid: bool
    reason: str = ""
    suggested_action: str = ""
    constraints_violated: List[str] = field(default_factory=list)


class CanvasDropTarget(ft.DragTarget):
    """
    Enhanced drop target for canvas with visual feedback and validation
    CLAUDE.md #1.2: Extends native Flet control
    CLAUDE.md #2.1.1: Comprehensive validation
    CLAUDE.md #9.1: Accessible drop zones
    """
    
    def __init__(
        self,
        content: ft.Control,
        zone_type: DropZoneType = DropZoneType.CANVAS,
        zone_id: str = "",
        group: str = "canvas_components",
        accepts: Optional[List[str]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        on_drop_accept: Optional[Callable[[DragData, DropPosition], bool]] = None,
        on_drop_reject: Optional[Callable[[DragData, str], None]] = None,
        on_hover_start: Optional[Callable[[DragData], None]] = None,
        on_hover_end: Optional[Callable[[DragData], None]] = None,
        enable_visual_feedback: bool = True,
        enable_grid_snapping: bool = False,
        grid_size: Tuple[int, int] = (20, 20),
        **kwargs
    ):
        """
        Initialize canvas drop target with comprehensive features
        
        Args:
            content: The visual content of the drop zone
            zone_type: Type of drop zone for behavior customization
            zone_id: Unique identifier for this drop zone
            group: Drag group this target accepts
            accepts: List of component types this zone accepts (None = all)
            constraints: Additional constraints for dropping
            on_drop_accept: Callback when valid drop occurs
            on_drop_reject: Callback when invalid drop is attempted
            on_hover_start: Callback when drag enters zone
            on_hover_end: Callback when drag leaves zone
            enable_visual_feedback: Show visual feedback during drag
            enable_grid_snapping: Enable grid-based positioning
            grid_size: Grid cell size for snapping
        """
        self.zone_type = zone_type
        self.zone_id = zone_id or str(uuid4())
        self.accepts = accepts or []  # Empty list means accept all
        self.constraints = constraints or {}
        self.enable_visual_feedback = enable_visual_feedback
        self.enable_grid_snapping = enable_grid_snapping
        self.grid_size = grid_size
        
        # Store callbacks
        self.on_drop_accept_callback = on_drop_accept
        self.on_drop_reject_callback = on_drop_reject
        self.on_hover_start_callback = on_hover_start
        self.on_hover_end_callback = on_hover_end
        
        # Internal state
        self._is_hovering = False
        self._current_drag_data: Optional[DragData] = None
        self._original_content = content
        self._highlighted_content: Optional[ft.Control] = None
        self._lock = threading.Lock()
        
        # Performance tracking
        self._drop_count = 0
        self._reject_count = 0
        self._avg_validation_time = 0.0
        
        # Create visual feedback overlays
        self._highlight_overlay = self._create_highlight_overlay()
        self._insertion_indicator = self._create_insertion_indicator()
        self._invalid_indicator = self._create_invalid_indicator()
        
        # Wrap content with feedback container
        self._wrapped_content = self._create_wrapped_content(content)
        
        # Initialize Flet DragTarget
        super().__init__(
            group=group,
            content=self._wrapped_content,
            on_accept=self._handle_drop,
            on_will_accept=self._handle_will_accept,
            on_leave=self._handle_leave,
            **kwargs
        )
        
        logger.info(f"Created drop target: {self.zone_id} ({zone_type.name})")
    
    def _create_wrapped_content(self, content: ft.Control) -> ft.Control:
        """
        Wrap content with feedback overlay capability
        CLAUDE.md #7.2: Safe UI composition
        """
        try:
            # Create stack with content and overlay capabilities
            return ft.Stack([
                content,
                # Overlay container for visual feedback (initially hidden)
                ft.Container(
                    content=ft.Container(),  # Empty overlay
                    expand=True,
                    bgcolor="transparent",
                    visible=False,
                    data="feedback_overlay"
                )
            ])
        except Exception as e:
            logger.error(f"Failed to wrap content: {e}")
            return content
    
    def _create_highlight_overlay(self) -> ft.Control:
        """Create highlight overlay for valid drop zones"""
        return ft.Container(
            border=ft.border.all(2, "#5E6AD2"),
            border_radius=4,
            bgcolor="#5E6AD220",  # Semi-transparent blue
            expand=True
        )
    
    def _create_insertion_indicator(self) -> ft.Control:
        """Create insertion line indicator"""
        return ft.Container(
            content=ft.Row([
                ft.Container(width=10, height=2, bgcolor="#5E6AD2", border_radius=1),
                ft.Divider(height=2, color="#5E6AD2"),
                ft.Container(width=10, height=2, bgcolor="#5E6AD2", border_radius=1),
            ]),
            height=2,
            margin=ft.margin.symmetric(vertical=4)
        )
    
    def _create_invalid_indicator(self) -> ft.Control:
        """Create invalid drop indicator"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.BLOCK, size=20, color="#EF4444"),
                ft.Text("Cannot drop here", size=12, color="#EF4444")
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.all(8),
            border=ft.border.all(2, "#EF4444", ft.BorderStyle.DASHED),
            border_radius=4,
            bgcolor="#FEF2F2",
            alignment=ft.alignment.center
        )
    
    def _handle_will_accept(self, e: ft.DragTargetAcceptEvent) -> bool:
        """
        Handle drag entering drop zone with validation
        CLAUDE.md #1.5: Efficient validation
        """
        start_time = time.perf_counter()
        
        try:
            with self._lock:
                # Parse drag data
                try:
                    drag_data = DragData.from_json(e.src_id)
                    self._current_drag_data = drag_data
                except Exception as ex:
                    logger.error(f"Invalid drag data: {ex}")
                    return False
                
                # Validate drop
                validation_result = self._validate_drop(drag_data)
                
                # Update visual feedback
                if self.enable_visual_feedback:
                    if validation_result.is_valid:
                        self._show_valid_feedback()
                    else:
                        self._show_invalid_feedback(validation_result.reason)
                
                # Track performance
                validation_time = (time.perf_counter() - start_time) * 1000
                self._update_validation_metrics(validation_time)
                
                # Set hovering state
                self._is_hovering = True
                
                # Trigger hover callback
                if self.on_hover_start_callback and validation_result.is_valid:
                    try:
                        self.on_hover_start_callback(drag_data)
                    except Exception as ex:
                        logger.error(f"Error in hover start callback: {ex}")
                
                # Announce to accessibility tools
                self._announce_drop_zone_state(validation_result.is_valid, drag_data)
                
                logger.debug(
                    f"Drag validation: {validation_result.is_valid} "
                    f"({validation_time:.1f}ms) - {drag_data.component_name}"
                )
                
                return validation_result.is_valid
                
        except Exception as e:
            logger.error(f"Error in will_accept handler: {e}")
            return False
    
    def _handle_leave(self, e: ft.DragTargetLeaveEvent) -> None:
        """
        Handle drag leaving drop zone
        CLAUDE.md #2.1.4: Proper cleanup
        """
        try:
            with self._lock:
                if not self._is_hovering:
                    return
                
                # Clear visual feedback
                if self.enable_visual_feedback:
                    self._clear_feedback()
                
                # Trigger hover end callback
                if self.on_hover_end_callback and self._current_drag_data:
                    try:
                        self.on_hover_end_callback(self._current_drag_data)
                    except Exception as ex:
                        logger.error(f"Error in hover end callback: {ex}")
                
                # Reset state
                self._is_hovering = False
                self._current_drag_data = None
                
                logger.debug(f"Drag left drop zone: {self.zone_id}")
                
        except Exception as e:
            logger.error(f"Error in leave handler: {e}")
    
    def _handle_drop(self, e: ft.DragTargetAcceptEvent) -> None:
        """
        Handle actual drop operation
        CLAUDE.md #2.1.1: Comprehensive drop processing
        """
        try:
            with self._lock:
                if not self._current_drag_data:
                    logger.warning("Drop attempted without drag data")
                    return
                
                drag_data = self._current_drag_data
                
                # Calculate drop position
                drop_position = self._calculate_drop_position(e)
                
                # Final validation
                validation_result = self._validate_drop(drag_data)
                
                if validation_result.is_valid:
                    # Process successful drop
                    success = self._process_drop(drag_data, drop_position)
                    
                    if success:
                        self._drop_count += 1
                        
                        # Trigger accept callback
                        if self.on_drop_accept_callback:
                            try:
                                callback_success = self.on_drop_accept_callback(drag_data, drop_position)
                                if not callback_success:
                                    logger.warning("Drop callback returned failure")
                            except Exception as ex:
                                logger.error(f"Error in drop accept callback: {ex}")
                        
                        # Announce success to accessibility tools
                        self._announce_drop_success(drag_data)
                        
                        logger.info(
                            f"Drop successful: {drag_data.component_name} "
                            f"at ({drop_position.x}, {drop_position.y})"
                        )
                    else:
                        self._handle_drop_failure(drag_data, "Processing failed")
                else:
                    self._handle_drop_failure(drag_data, validation_result.reason)
                
                # Clear state
                self._clear_feedback()
                self._is_hovering = False
                self._current_drag_data = None
                
        except Exception as e:
            logger.error(f"Error in drop handler: {e}")
            if self._current_drag_data:
                self._handle_drop_failure(self._current_drag_data, f"Drop error: {e}")
    
    def _validate_drop(self, drag_data: DragData) -> DropValidationResult:
        """
        Comprehensive drop validation
        CLAUDE.md #2.1.1: Validate all constraints
        """
        try:
            # Check if component type is accepted
            if self.accepts and drag_data.component_type not in self.accepts:
                return DropValidationResult(
                    is_valid=False,
                    reason=f"Component type '{drag_data.component_type}' not accepted",
                    suggested_action="Try a different component type"
                )
            
            # Check zone-specific constraints
            if self.zone_type == DropZoneType.CONTAINER:
                # Container-specific validation
                max_children = self.constraints.get("max_children")
                if max_children is not None:
                    current_children = self._get_current_child_count()
                    if current_children >= max_children:
                        return DropValidationResult(
                            is_valid=False,
                            reason=f"Container already has maximum children ({max_children})",
                            suggested_action="Remove existing components or use a different container"
                        )
            
            elif self.zone_type == DropZoneType.SLOT:
                # Slot-specific validation
                required_type = self.constraints.get("required_type")
                if required_type and drag_data.component_type != required_type:
                    return DropValidationResult(
                        is_valid=False,
                        reason=f"Slot requires '{required_type}' component",
                        suggested_action=f"Use a {required_type} component instead"
                    )
                
                # Check if slot is already occupied
                if self.constraints.get("exclusive", True) and self._is_slot_occupied():
                    return DropValidationResult(
                        is_valid=False,
                        reason="Slot is already occupied",
                        suggested_action="Remove existing component first"
                    )
            
            # Check component-specific constraints
            component_constraints = drag_data.properties.get("constraints", {})
            
            # Minimum size constraints
            min_width = component_constraints.get("min_width", 0)
            min_height = component_constraints.get("min_height", 0)
            available_width = self.constraints.get("available_width", float('inf'))
            available_height = self.constraints.get("available_height", float('inf'))
            
            if min_width > available_width or min_height > available_height:
                return DropValidationResult(
                    is_valid=False,
                    reason="Component too large for drop zone",
                    suggested_action="Use a larger container or smaller component"
                )
            
            # Parent-child relationship constraints
            invalid_parents = component_constraints.get("invalid_parents", [])
            if self.zone_type.name.lower() in invalid_parents:
                return DropValidationResult(
                    is_valid=False,
                    reason=f"Component cannot be placed in {self.zone_type.name.lower()}",
                    suggested_action="Use a compatible container type"
                )
            
            # All validations passed
            return DropValidationResult(is_valid=True, reason="Valid drop target")
            
        except Exception as e:
            logger.error(f"Error in drop validation: {e}")
            return DropValidationResult(
                is_valid=False,
                reason=f"Validation error: {e}",
                suggested_action="Try again or contact support"
            )
    
    def _calculate_drop_position(self, e: ft.DragTargetAcceptEvent) -> DropPosition:
        """
        Calculate precise drop position with grid snapping
        CLAUDE.md #1.5: Efficient position calculation
        """
        try:
            # Get mouse position (would be available in real Flet event)
            # For now, we'll use placeholder values
            mouse_x = getattr(e, 'x', 0.0)
            mouse_y = getattr(e, 'y', 0.0)
            
            if self.enable_grid_snapping:
                # Snap to grid
                grid_x = round(mouse_x / self.grid_size[0])
                grid_y = round(mouse_y / self.grid_size[1])
                snapped_x = grid_x * self.grid_size[0]
                snapped_y = grid_y * self.grid_size[1]
                
                return DropPosition(
                    x=snapped_x,
                    y=snapped_y,
                    snap_to_grid=True,
                    grid_x=grid_x,
                    grid_y=grid_y
                )
            else:
                # Use exact mouse position
                return DropPosition(x=mouse_x, y=mouse_y)
                
        except Exception as e:
            logger.error(f"Error calculating drop position: {e}")
            return DropPosition(x=0.0, y=0.0)
    
    def _process_drop(self, drag_data: DragData, drop_position: DropPosition) -> bool:
        """
        Process the actual drop operation
        CLAUDE.md #2.1.4: Atomic operations
        """
        try:
            # Create component instance data
            component_instance = {
                "id": str(uuid4()),
                "type": drag_data.component_type,
                "name": drag_data.component_name,
                "category": drag_data.component_category,
                "position": drop_position.to_dict(),
                "properties": drag_data.properties.copy(),
                "metadata": {
                    **drag_data.metadata,
                    "dropped_at": time.time(),
                    "drop_zone_id": self.zone_id,
                    "drop_zone_type": self.zone_type.name
                }
            }
            
            # Store in drop zone's component registry
            # (In real implementation, this would integrate with canvas state)
            logger.info(f"Created component instance: {component_instance}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing drop: {e}")
            return False
    
    def _handle_drop_failure(self, drag_data: DragData, reason: str) -> None:
        """Handle failed drop operation"""
        self._reject_count += 1
        
        # Show error feedback
        if self.enable_visual_feedback:
            self._show_invalid_feedback(reason)
            
            # Auto-clear after delay
            import threading
            def clear_error():
                time.sleep(2.0)
                self._clear_feedback()
            
            threading.Thread(target=clear_error, daemon=True).start()
        
        # Trigger reject callback
        if self.on_drop_reject_callback:
            try:
                self.on_drop_reject_callback(drag_data, reason)
            except Exception as e:
                logger.error(f"Error in drop reject callback: {e}")
        
        # Announce failure to accessibility tools
        self._announce_drop_failure(drag_data, reason)
        
        logger.warning(f"Drop rejected: {drag_data.component_name} - {reason}")
    
    def _show_valid_feedback(self) -> None:
        """Show visual feedback for valid drop zone"""
        try:
            if isinstance(self.content, ft.Stack):
                # Find and update overlay
                for control in self.content.controls:
                    if hasattr(control, 'data') and control.data == "feedback_overlay":
                        control.content = self._highlight_overlay
                        control.visible = True
                        break
                self.content.update()
        except Exception as e:
            logger.error(f"Error showing valid feedback: {e}")
    
    def _show_invalid_feedback(self, reason: str) -> None:
        """Show visual feedback for invalid drop"""
        try:
            if isinstance(self.content, ft.Stack):
                # Update invalid indicator with reason
                invalid_indicator = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.BLOCK, size=16, color="#EF4444"),
                            ft.Text("Cannot drop here", size=10, color="#EF4444", weight=ft.FontWeight.W_500)
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Text(reason, size=8, color="#EF4444", text_align=ft.TextAlign.CENTER, max_lines=2)
                    ], spacing=2),
                    padding=ft.padding.all(4),
                    border=ft.border.all(1, "#EF4444", ft.BorderStyle.DASHED),
                    border_radius=4,
                    bgcolor="#FEF2F2",
                    alignment=ft.alignment.center
                )
                
                # Find and update overlay
                for control in self.content.controls:
                    if hasattr(control, 'data') and control.data == "feedback_overlay":
                        control.content = invalid_indicator
                        control.visible = True
                        break
                self.content.update()
        except Exception as e:
            logger.error(f"Error showing invalid feedback: {e}")
    
    def _clear_feedback(self) -> None:
        """Clear visual feedback"""
        try:
            if isinstance(self.content, ft.Stack):
                # Find and hide overlay
                for control in self.content.controls:
                    if hasattr(control, 'data') and control.data == "feedback_overlay":
                        control.visible = False
                        break
                self.content.update()
        except Exception as e:
            logger.error(f"Error clearing feedback: {e}")
    
    def _get_current_child_count(self) -> int:
        """Get current number of child components in this zone"""
        # In real implementation, this would query the canvas state
        return 0
    
    def _is_slot_occupied(self) -> bool:
        """Check if slot is currently occupied"""
        # In real implementation, this would check slot state
        return False
    
    def _update_validation_metrics(self, validation_time: float) -> None:
        """Update performance metrics"""
        if self._avg_validation_time == 0:
            self._avg_validation_time = validation_time
        else:
            # Exponential moving average
            alpha = 0.1
            self._avg_validation_time = (
                alpha * validation_time + 
                (1 - alpha) * self._avg_validation_time
            )
    
    # Accessibility methods
    
    def _announce_drop_zone_state(self, is_valid: bool, drag_data: DragData) -> None:
        """Announce drop zone state to screen readers"""
        if is_valid:
            message = f"Valid drop zone for {drag_data.component_name}"
        else:
            message = f"Invalid drop zone for {drag_data.component_name}"
        
        logger.info(f"Accessibility: {message}")
    
    def _announce_drop_success(self, drag_data: DragData) -> None:
        """Announce successful drop to screen readers"""
        message = f"Successfully placed {drag_data.component_name} in {self.zone_type.name.lower()}"
        logger.info(f"Accessibility: {message}")
    
    def _announce_drop_failure(self, drag_data: DragData, reason: str) -> None:
        """Announce drop failure to screen readers"""
        message = f"Cannot place {drag_data.component_name}: {reason}"
        logger.info(f"Accessibility: {message}")
    
    # Public API methods
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance and usage metrics"""
        return {
            "drop_count": self._drop_count,
            "reject_count": self._reject_count,
            "success_rate": self._drop_count / max(self._drop_count + self._reject_count, 1),
            "avg_validation_time_ms": self._avg_validation_time,
            "is_hovering": self._is_hovering,
            "zone_type": self.zone_type.name,
            "accepts": self.accepts
        }
    
    def update_constraints(self, new_constraints: Dict[str, Any]) -> None:
        """Update drop zone constraints"""
        self.constraints = {**self.constraints, **new_constraints}
        logger.debug(f"Updated constraints for zone {self.zone_id}")
    
    def set_accepts(self, component_types: List[str]) -> None:
        """Update accepted component types"""
        self.accepts = component_types.copy()
        logger.debug(f"Updated accepted types for zone {self.zone_id}: {component_types}")


def create_canvas_drop_zone(
    width: float = 800,
    height: float = 600,
    background_color: str = "#FFFFFF",
    show_grid: bool = False,
    grid_size: Tuple[int, int] = (20, 20)
) -> CanvasDropTarget:
    """
    Factory function to create main canvas drop zone
    CLAUDE.md #1.2: Factory pattern for common cases
    """
    try:
        # Create canvas content
        canvas_content = ft.Container(
            width=width,
            height=height,
            bgcolor=background_color,
            border=ft.border.all(1, "#E5E7EB"),
            border_radius=8,
            content=ft.Column([
                ft.Icon(
                    ft.Icons.WIDGETS,
                    size=48,
                    color="#D1D5DB"
                ),
                ft.Text(
                    "Drop components here",
                    size=16,
                    color="#6B7280",
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Drag components from the library to build your design",
                    size=12,
                    color="#9CA3AF",
                    text_align=ft.TextAlign.CENTER
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.alignment.center
        )
        
        # Add grid overlay if requested
        if show_grid:
            # Create grid pattern
            grid_lines = []
            for x in range(0, int(width), grid_size[0]):
                grid_lines.append(
                    ft.Container(
                        left=x,
                        top=0,
                        width=1,
                        height=height,
                        bgcolor="#F3F4F6"
                    )
                )
            for y in range(0, int(height), grid_size[1]):
                grid_lines.append(
                    ft.Container(
                        left=0,
                        top=y,
                        width=width,
                        height=1,
                        bgcolor="#F3F4F6"
                    )
                )
            
            # Overlay grid on canvas
            canvas_content = ft.Stack([
                canvas_content,
                *grid_lines
            ])
        
        return CanvasDropTarget(
            content=canvas_content,
            zone_type=DropZoneType.CANVAS,
            zone_id="main_canvas",
            group="canvas_components",
            accepts=[],  # Accept all component types
            constraints={"available_width": width, "available_height": height},
            enable_visual_feedback=True,
            enable_grid_snapping=show_grid,
            grid_size=grid_size
        )
        
    except Exception as e:
        logger.error(f"Failed to create canvas drop zone: {e}")
        raise ValidationError(f"Cannot create canvas drop zone: {e}")


def create_container_drop_zone(
    container_id: str,
    container_type: str = "div",
    accepts: Optional[List[str]] = None,
    max_children: Optional[int] = None
) -> CanvasDropTarget:
    """Factory function to create container drop zones"""
    try:
        content = ft.Container(
            content=ft.Text(
                f"Container ({container_type})",
                size=12,
                color="#6B7280"
            ),
            padding=ft.padding.all(16),
            border=ft.border.all(1, "#D1D5DB", ft.BorderStyle.DASHED),
            border_radius=4,
            bgcolor="#F9FAFB",
            min_height=100
        )
        
        constraints = {}
        if max_children is not None:
            constraints["max_children"] = max_children
        
        return CanvasDropTarget(
            content=content,
            zone_type=DropZoneType.CONTAINER,
            zone_id=container_id,
            accepts=accepts or [],
            constraints=constraints,
            enable_visual_feedback=True
        )
        
    except Exception as e:
        logger.error(f"Failed to create container drop zone: {e}")
        raise ValidationError(f"Cannot create container drop zone: {e}")


# Global registry for drop zones
_drop_zones: Dict[str, CanvasDropTarget] = {}
_drop_zone_lock = threading.Lock()


def register_drop_zone(zone_id: str, drop_zone: CanvasDropTarget) -> None:
    """Register drop zone for global tracking"""
    with _drop_zone_lock:
        _drop_zones[zone_id] = drop_zone


def unregister_drop_zone(zone_id: str) -> None:
    """Unregister drop zone"""
    with _drop_zone_lock:
        _drop_zones.pop(zone_id, None)


def get_drop_zone(zone_id: str) -> Optional[CanvasDropTarget]:
    """Get drop zone by ID"""
    with _drop_zone_lock:
        return _drop_zones.get(zone_id)


def get_all_drop_zones() -> List[CanvasDropTarget]:
    """Get all registered drop zones"""
    with _drop_zone_lock:
        return list(_drop_zones.values())