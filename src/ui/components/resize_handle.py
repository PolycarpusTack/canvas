"""Resizable handle component for panel resizing"""

import flet as ft
from typing import Callable
from config.constants import RESIZE_HANDLE_WIDTH, RESIZE_HANDLE_COLOR, RESIZE_HANDLE_HOVER_COLOR


class ResizeHandle(ft.Container):
    """Interactive resize handle between panels"""
    
    def __init__(self, 
                 on_drag: Callable[[float], None],
                 orientation: str = "vertical",
                 min_value: float = 0,
                 max_value: float = float('inf')):
        self.on_drag_callback = on_drag
        self.orientation = orientation
        self.min_value = min_value
        self.max_value = max_value
        self.is_dragging = False
        self.start_pos = 0
        self.start_value = 0
        
        super().__init__(
            width=RESIZE_HANDLE_WIDTH if orientation == "vertical" else None,
            height=RESIZE_HANDLE_WIDTH if orientation == "horizontal" else None,
            bgcolor=RESIZE_HANDLE_COLOR,
            on_hover=self._on_hover,
            on_click=self._on_click,
            expand=True if orientation == "vertical" else False,
        )
    
    def _on_hover(self, e):
        if e.data == "true":
            self.bgcolor = RESIZE_HANDLE_HOVER_COLOR
            e.page.window.mouse_cursor = ft.MouseCursor.RESIZE_LEFT_RIGHT if self.orientation == "vertical" else ft.MouseCursor.RESIZE_UP_DOWN
        else:
            if not self.is_dragging:
                self.bgcolor = RESIZE_HANDLE_COLOR
                e.page.window.mouse_cursor = ft.MouseCursor.BASIC
        self.update()
    
    def _on_click(self, e):
        # Start drag operation
        self.is_dragging = True
        self.start_pos = e.global_x if self.orientation == "vertical" else e.global_y
        # Store the current value as the starting point for drag calculations
        self.start_value = 0  # This will be set by the parent component
        self.bgcolor = RESIZE_HANDLE_HOVER_COLOR
        self.update()
        
        # Add global event handlers
        e.page.on_pointer_move = self._on_pointer_move
        e.page.on_pointer_up = self._on_pointer_up
    
    def _on_pointer_move(self, e):
        if self.is_dragging:
            current_pos = e.global_x if self.orientation == "vertical" else e.global_y
            delta = current_pos - self.start_pos
            
            # Apply constraints
            new_value = max(self.min_value, min(self.max_value, self.start_value + delta))
            
            # Smooth updates at 60fps
            self.on_drag_callback(new_value)
    
    def _on_pointer_up(self, e):
        self.is_dragging = False
        self.bgcolor = RESIZE_HANDLE_COLOR
        self.update()
        
        # Remove global event handlers
        e.page.on_pointer_move = None
        e.page.on_pointer_up = None
        e.page.window.mouse_cursor = ft.MouseCursor.BASIC
    
    def set_start_value(self, value: float):
        """Set the starting value for drag calculations"""
        self.start_value = value