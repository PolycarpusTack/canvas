"""
Enhanced Visual Feedback System for Drag & Drop Operations
Following CLAUDE.md guidelines for enterprise-grade visual feedback
"""

import flet as ft
from typing import Optional, List, Dict, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import math
import time
import logging

from drag_drop_manager import DragData, DropTarget, DropZoneType, DragOperation
from models.component import Component

logger = logging.getLogger(__name__)


class FeedbackState(Enum):
    """Visual feedback states"""
    VALID = auto()
    INVALID = auto()
    HOVER = auto()
    DRAGGING = auto()


@dataclass
class VisualFeedbackConfig:
    """
    Configuration for visual feedback system
    CLAUDE.md #1.4: Extensible configuration
    """
    # Drop zone highlighting
    valid_highlight_color: str = "#5E6AD2"
    invalid_highlight_color: str = "#EF4444"
    hover_highlight_color: str = "#06B6D4"
    highlight_opacity: float = 0.2
    
    # Insertion indicators
    insertion_line_color: str = "#5E6AD2"
    insertion_line_width: float = 2.0
    insertion_animation_duration: int = 300
    
    # Ghost component
    ghost_opacity: float = 0.7
    ghost_scale: float = 0.9
    ghost_offset_x: float = 10.0
    ghost_offset_y: float = 10.0
    
    # Performance settings
    animation_duration: int = 200
    fps_limit: int = 60
    
    def __post_init__(self):
        """Validate configuration"""
        if not (0.0 <= self.highlight_opacity <= 1.0):
            raise ValueError("Highlight opacity must be between 0.0 and 1.0")
        
        if not (0.0 <= self.ghost_opacity <= 1.0):
            raise ValueError("Ghost opacity must be between 0.0 and 1.0")
        
        if self.fps_limit < 30 or self.fps_limit > 120:
            raise ValueError("FPS limit must be between 30 and 120")


class DragVisualFeedback:
    """
    Comprehensive visual feedback system for drag operations
    CLAUDE.md #1.5: Profile before optimizing
    CLAUDE.md #9.1: WCAG compliance for visual indicators
    """
    
    def __init__(self, config: Optional[VisualFeedbackConfig] = None):
        self.config = config or VisualFeedbackConfig()
        
        # Visual state
        self._current_feedback: Dict[str, ft.Control] = {}
        self._ghost_component: Optional[ft.Control] = None
        self._insertion_indicators: List[ft.Control] = []
        self._highlight_overlays: Dict[str, ft.Control] = {}
        
        # Animation state
        self._animations: Dict[str, ft.AnimationController] = {}
        self._frame_time_budget = 1000 / self.config.fps_limit
        self._last_frame_time = 0.0
        
        # Performance tracking
        self._feedback_count = 0
        self._avg_render_time = 0.0
        
    def start_drag_feedback(
        self,
        drag_data: DragData,
        source_component: Optional[Component] = None,
        mouse_position: Optional[Tuple[float, float]] = None
    ) -> None:
        """
        Start visual feedback for drag operation
        CLAUDE.md #2.1.4: Proper resource management
        """
        try:
            # Clear any existing feedback
            self.clear_all_feedback()
            
            # Create ghost component
            if source_component:
                self._create_ghost_component(
                    source_component,
                    mouse_position or (0, 0)
                )
            
            # Set up accessibility announcements
            self._announce_drag_start(drag_data)
            
            logger.debug(f"Started drag feedback for {drag_data.source_type}")
            
        except Exception as e:
            logger.error(f"Failed to start drag feedback: {e}")
    
    def update_drop_zone_feedback(
        self,
        drop_target: DropTarget,
        state: FeedbackState,
        bounds: Optional[Tuple[float, float, float, float]] = None,
        insertion_point: Optional[Tuple[float, float, str]] = None
    ) -> None:
        """
        Update visual feedback for drop zones
        CLAUDE.md #12.3: Performance monitoring
        """
        start_time = time.perf_counter()
        
        try:
            target_id = drop_target.target_id or "canvas"
            
            # Remove existing feedback for this target
            self._clear_target_feedback(target_id)
            
            if bounds:
                # Create highlight overlay
                highlight = self._create_highlight_overlay(
                    bounds,
                    state,
                    drop_target.zone_type
                )
                self._highlight_overlays[target_id] = highlight
            
            # Create insertion indicator if provided
            if insertion_point:
                indicator = self._create_insertion_indicator(
                    insertion_point[0],
                    insertion_point[1],
                    insertion_point[2]  # orientation
                )
                self._insertion_indicators.append(indicator)
            
            # Update accessibility announcements
            self._announce_drop_zone_state(drop_target, state)
            
            # Track performance
            render_time = (time.perf_counter() - start_time) * 1000
            self._update_performance_metrics(render_time)
            
        except Exception as e:
            logger.error(f"Failed to update drop zone feedback: {e}")
    
    def update_ghost_position(
        self,
        mouse_position: Tuple[float, float]
    ) -> None:
        """
        Update ghost component position following mouse
        CLAUDE.md #1.5: Optimize frequent operations
        """
        if not self._ghost_component:
            return
        
        # Throttle updates based on frame budget
        current_time = time.perf_counter() * 1000
        if current_time - self._last_frame_time < self._frame_time_budget:
            return
        
        try:
            # Apply offset for better visual feedback
            x = mouse_position[0] + self.config.ghost_offset_x
            y = mouse_position[1] + self.config.ghost_offset_y
            
            # Update ghost position
            self._ghost_component.left = x
            self._ghost_component.top = y
            self._ghost_component.update()
            
            self._last_frame_time = current_time
            
        except Exception as e:
            logger.error(f"Failed to update ghost position: {e}")
    
    def show_invalid_drop_feedback(
        self,
        drop_target: DropTarget,
        reason: str = "Invalid drop target"
    ) -> None:
        """
        Show feedback for invalid drop attempts
        CLAUDE.md #9.4: Screen reader announcements
        """
        try:
            # Show visual "not allowed" indicator
            if drop_target.target_id:
                self.update_drop_zone_feedback(
                    drop_target,
                    FeedbackState.INVALID
                )
            
            # Create temporary "not allowed" cursor overlay
            not_allowed_indicator = ft.Container(
                content=ft.Icon(
                    ft.Icons.BLOCK,
                    size=24,
                    color=self.config.invalid_highlight_color
                ),
                bgcolor="#FFFFFF",
                border_radius=12,
                padding=4,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=4,
                    color="#00000020"
                ),
                animate_opacity=self.config.animation_duration
            )
            
            # Auto-remove after brief display
            self._schedule_feedback_removal(
                "not_allowed",
                not_allowed_indicator,
                1000  # 1 second
            )
            
            # Announce to screen readers
            self._announce_invalid_drop(reason)
            
        except Exception as e:
            logger.error(f"Failed to show invalid drop feedback: {e}")
    
    def clear_all_feedback(self) -> None:
        """
        Clear all visual feedback
        CLAUDE.md #2.1.4: Proper cleanup
        """
        try:
            # Clear ghost component
            if self._ghost_component:
                self._ghost_component.visible = False
                self._ghost_component = None
            
            # Clear insertion indicators
            for indicator in self._insertion_indicators:
                indicator.visible = False
            self._insertion_indicators.clear()
            
            # Clear highlight overlays
            for overlay in self._highlight_overlays.values():
                overlay.visible = False
            self._highlight_overlays.clear()
            
            # Clear other feedback
            for feedback in self._current_feedback.values():
                feedback.visible = False
            self._current_feedback.clear()
            
            # Stop animations
            for animation in self._animations.values():
                animation.stop()
            self._animations.clear()
            
            logger.debug("Cleared all drag feedback")
            
        except Exception as e:
            logger.error(f"Failed to clear feedback: {e}")
    
    def _create_ghost_component(
        self,
        component: Component,
        mouse_position: Tuple[float, float]
    ) -> None:
        """
        Create ghost representation of dragged component
        CLAUDE.md #7.2: Safe content rendering
        """
        try:
            # Create simplified version of component
            ghost_content = ft.Container(
                content=ft.Text(
                    component.name or component.type,
                    size=14,
                    color="#374151",
                    weight=ft.FontWeight.W_500
                ),
                bgcolor=component.style.background_color or "#FFFFFF",
                border=ft.border.all(1, "#D1D5DB"),
                border_radius=4,
                padding=8,
                width=min(200, float(component.style.width or 100)),
                height=min(100, float(component.style.height or 40)),
                opacity=self.config.ghost_opacity,
                scale=ft.Scale(self.config.ghost_scale),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=8,
                    color="#00000030"
                )
            )
            
            # Position at mouse with offset
            x = mouse_position[0] + self.config.ghost_offset_x
            y = mouse_position[1] + self.config.ghost_offset_y
            
            self._ghost_component = ft.Container(
                content=ghost_content,
                left=x,
                top=y,
                animate_position=self.config.animation_duration
            )
            
        except Exception as e:
            logger.error(f"Failed to create ghost component: {e}")
    
    def _create_highlight_overlay(
        self,
        bounds: Tuple[float, float, float, float],
        state: FeedbackState,
        zone_type: DropZoneType
    ) -> ft.Control:
        """
        Create highlight overlay for drop zones
        CLAUDE.md #9.1: High contrast mode support
        """
        x, y, width, height = bounds
        
        # Choose color based on state
        if state == FeedbackState.VALID:
            color = self.config.valid_highlight_color
            border_style = ft.BorderSide(2, color)
        elif state == FeedbackState.INVALID:
            color = self.config.invalid_highlight_color
            border_style = ft.BorderSide(2, color, ft.BorderStyle.DASHED)
        else:  # HOVER
            color = self.config.hover_highlight_color
            border_style = ft.BorderSide(1, color)
        
        # Create overlay with subtle animation
        overlay = ft.Container(
            left=x - 2,
            top=y - 2,
            width=width + 4,
            height=height + 4,
            bgcolor=f"{color}{int(self.config.highlight_opacity * 255):02x}",
            border=ft.border.all(border_style.width, border_style.color, border_style.style),
            border_radius=4,
            animate_opacity=self.config.animation_duration,
            data={
                "feedback_type": "highlight",
                "zone_type": zone_type.value,
                "state": state.name
            }
        )
        
        return overlay
    
    def _create_insertion_indicator(
        self,
        x: float,
        y: float,
        orientation: str = "horizontal"
    ) -> ft.Control:
        """
        Create insertion line indicator
        CLAUDE.md #9.1: Don't rely on color alone
        """
        if orientation == "horizontal":
            # Horizontal insertion line
            indicator = ft.Container(
                left=x - 20,
                top=y - 1,
                width=40,
                height=self.config.insertion_line_width,
                bgcolor=self.config.insertion_line_color,
                border_radius=1,
                animate_opacity=self.config.insertion_animation_duration
            )
            
            # Add small arrows on ends
            left_arrow = ft.Container(
                left=x - 25,
                top=y - 4,
                width=8,
                height=8,
                content=ft.Icon(
                    ft.Icons.PLAY_ARROW,
                    size=8,
                    color=self.config.insertion_line_color
                ),
                rotate=ft.Rotate(math.pi)  # Point right
            )
            
            right_arrow = ft.Container(
                left=x + 20,
                top=y - 4,
                width=8,
                height=8,
                content=ft.Icon(
                    ft.Icons.PLAY_ARROW,
                    size=8,
                    color=self.config.insertion_line_color
                )
            )
            
            return ft.Stack([indicator, left_arrow, right_arrow])
        
        else:  # vertical
            # Vertical insertion line
            indicator = ft.Container(
                left=x - 1,
                top=y - 20,
                width=self.config.insertion_line_width,
                height=40,
                bgcolor=self.config.insertion_line_color,
                border_radius=1,
                animate_opacity=self.config.insertion_animation_duration
            )
            
            return indicator
    
    def _clear_target_feedback(self, target_id: str) -> None:
        """Clear feedback for specific target"""
        if target_id in self._highlight_overlays:
            self._highlight_overlays[target_id].visible = False
            del self._highlight_overlays[target_id]
        
        if target_id in self._current_feedback:
            self._current_feedback[target_id].visible = False
            del self._current_feedback[target_id]
    
    def _schedule_feedback_removal(
        self,
        feedback_id: str,
        control: ft.Control,
        delay_ms: int
    ) -> None:
        """Schedule automatic removal of feedback"""
        import threading
        
        def remove_after_delay():
            time.sleep(delay_ms / 1000)
            try:
                control.visible = False
                if feedback_id in self._current_feedback:
                    del self._current_feedback[feedback_id]
            except Exception as e:
                logger.error(f"Error removing scheduled feedback: {e}")
        
        thread = threading.Thread(target=remove_after_delay)
        thread.daemon = True
        thread.start()
    
    def _update_performance_metrics(self, render_time: float) -> None:
        """
        Track rendering performance
        CLAUDE.md #12.1: Performance monitoring
        """
        self._feedback_count += 1
        
        # Update rolling average
        if self._avg_render_time == 0:
            self._avg_render_time = render_time
        else:
            # Exponential moving average
            alpha = 0.1
            self._avg_render_time = (alpha * render_time) + ((1 - alpha) * self._avg_render_time)
        
        # Warn if performance degrades
        if render_time > 16.0:  # 60fps budget
            logger.warning(
                f"Slow feedback render: {render_time:.1f}ms "
                f"(avg: {self._avg_render_time:.1f}ms)"
            )
    
    # Accessibility methods
    def _announce_drag_start(self, drag_data: DragData) -> None:
        """
        Announce drag start to screen readers
        CLAUDE.md #9.4: Screen reader announcements
        """
        if drag_data.source_type == "library":
            message = f"Started dragging {drag_data.component_id} component from library"
        elif drag_data.source_type == "canvas":
            message = f"Started moving component on canvas"
        else:
            message = "Started drag operation"
        
        # In a real implementation, this would use ARIA live regions
        logger.info(f"Accessibility: {message}")
    
    def _announce_drop_zone_state(
        self,
        drop_target: DropTarget,
        state: FeedbackState
    ) -> None:
        """Announce drop zone state changes"""
        if state == FeedbackState.VALID:
            message = f"Valid drop zone: {drop_target.zone_type.value}"
        elif state == FeedbackState.INVALID:
            message = f"Invalid drop zone"
        else:
            message = f"Hovering over {drop_target.zone_type.value}"
        
        logger.info(f"Accessibility: {message}")
    
    def _announce_invalid_drop(self, reason: str) -> None:
        """Announce invalid drop attempt"""
        message = f"Drop not allowed: {reason}"
        logger.info(f"Accessibility: {message}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "feedback_count": self._feedback_count,
            "avg_render_time_ms": self._avg_render_time,
            "fps_limit": self.config.fps_limit,
            "frame_budget_ms": self._frame_time_budget
        }
    
    def get_all_feedback_controls(self) -> List[ft.Control]:
        """
        Get all current feedback controls for rendering
        Used by the canvas renderer to overlay feedback
        """
        controls = []
        
        if self._ghost_component:
            controls.append(self._ghost_component)
        
        controls.extend(self._highlight_overlays.values())
        controls.extend(self._insertion_indicators)
        controls.extend(self._current_feedback.values())
        
        return [c for c in controls if c.visible]


# Global instance for easy access
_visual_feedback_instance: Optional[DragVisualFeedback] = None


def get_visual_feedback(config: Optional[VisualFeedbackConfig] = None) -> DragVisualFeedback:
    """Get or create global visual feedback instance"""
    global _visual_feedback_instance
    if _visual_feedback_instance is None:
        _visual_feedback_instance = DragVisualFeedback(config)
    return _visual_feedback_instance


def reset_visual_feedback() -> None:
    """Reset global visual feedback instance"""
    global _visual_feedback_instance
    if _visual_feedback_instance:
        _visual_feedback_instance.clear_all_feedback()
    _visual_feedback_instance = None