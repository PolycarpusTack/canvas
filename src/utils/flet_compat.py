"""
Flet Compatibility Layer
Handles API differences between Flet versions
"""

import flet as ft
from typing import Any, Callable, List, Optional

class FletCompat:
    """
    Base class that replaces ft.UserControl pattern
    Use this instead of UserControl for custom controls
    """
    
    def __init__(self, **kwargs):
        # Store properties
        self._props = kwargs
        self._content = None
        
    def build(self):
        """Override this method to build your control"""
        raise NotImplementedError("Subclasses must implement build()")
    
    def get_control(self) -> ft.Control:
        """Get the actual Flet control"""
        if self._content is None:
            self._content = self.build()
        return self._content
    
    def update(self):
        """Update the control if it's attached to a page"""
        if self._content and hasattr(self._content, 'update'):
            self._content.update()


def create_container_control(build_func: Callable[[], ft.Control], **kwargs) -> ft.Container:
    """
    Helper to create a container-based control
    Replaces the UserControl pattern
    """
    container = ft.Container(**kwargs)
    container.content = build_func()
    return container


class CompatPropertyInput(ft.Container):
    """
    Compatible property input control
    Replaces UserControl-based PropertyInput
    """
    
    def __init__(self, 
                 label: str,
                 value: Any,
                 input_type: str = "text",
                 options: Optional[List[str]] = None,
                 on_change: Optional[Callable[[Any], None]] = None,
                 **kwargs):
        super().__init__(**kwargs)
        
        self.label = label
        self.value = value
        self.input_type = input_type
        self.options = options
        self.on_change_handler = on_change
        
        # Build content
        self.content = self._build_content()
    
    def _build_content(self):
        """Build the property input content"""
        controls = [
            ft.Text(self.label, size=14, weight=ft.FontWeight.W_500, color="#374151")
        ]
        
        if self.input_type == "text":
            controls.append(
                ft.TextField(
                    value=str(self.value) if self.value else "",
                    on_change=lambda e: self.on_change_handler(e.control.value) if self.on_change_handler else None,
                    border_radius=6,
                    height=40,
                    text_size=14,
                    border_color="#D1D5DB",
                    focused_border_color="#5E6AD2"
                )
            )
        elif self.input_type == "textarea":
            controls.append(
                ft.TextField(
                    value=str(self.value) if self.value else "",
                    multiline=True,
                    min_lines=3,
                    max_lines=5,
                    on_change=lambda e: self.on_change_handler(e.control.value) if self.on_change_handler else None,
                    border_radius=6,
                    text_size=14,
                    border_color="#D1D5DB",
                    focused_border_color="#5E6AD2"
                )
            )
        elif self.input_type == "dropdown" and self.options:
            controls.append(
                ft.Dropdown(
                    value=str(self.value) if self.value else None,
                    options=[ft.dropdown.Option(opt) for opt in self.options],
                    on_change=lambda e: self.on_change_handler(e.control.value) if self.on_change_handler else None,
                    border_radius=6,
                    height=40,
                    text_size=14,
                    border_color="#D1D5DB",
                    focused_border_color="#5E6AD2"
                )
            )
        elif self.input_type == "color":
            controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            width=40,
                            height=40,
                            bgcolor=self.value if self.value else "#FFFFFF",
                            border_radius=6,
                            border=ft.border.all(1, "#D1D5DB")
                        ),
                        ft.TextField(
                            value=self.value if self.value else "",
                            on_change=lambda e: self._on_color_change(e.control.value),
                            width=100,
                            height=40,
                            text_size=14,
                            border_radius=6,
                            border_color="#D1D5DB"
                        )
                    ], spacing=10)
                )
            )
            
        return ft.Column(controls, spacing=8)
    
    def _on_color_change(self, value: str):
        """Handle color change"""
        if self.on_change_handler:
            self.on_change_handler(value)
        # Update color preview
        if self.content.controls and len(self.content.controls) > 1:
            color_row = self.content.controls[1].content
            if color_row and hasattr(color_row, 'controls'):
                color_preview = color_row.controls[0]
                color_preview.bgcolor = value
                self.update()


# Drag event compatibility
def get_drag_data(event) -> Any:
    """Get data from drag event (compatible wrapper)"""
    return event.data if hasattr(event, 'data') else None


def get_drag_position(event) -> ft.Offset:
    """Get position from drag event (compatible wrapper)"""
    if hasattr(event, 'x') and hasattr(event, 'y'):
        return ft.Offset(event.x, event.y)
    elif hasattr(event, 'local_x') and hasattr(event, 'local_y'):
        return ft.Offset(event.local_x, event.local_y)
    else:
        return ft.Offset(0, 0)


# Export compatibility items
__all__ = [
    'FletCompat',
    'create_container_control',
    'CompatPropertyInput',
    'get_drag_data',
    'get_drag_position'
]