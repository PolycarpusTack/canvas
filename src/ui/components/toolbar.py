"""Floating toolbar component for element editing"""

import flet as ft
from typing import Callable, List, Dict, Optional


class ToolbarButton(ft.Container):
    """Individual toolbar button"""
    
    def __init__(self, 
                 icon: Optional[str] = None,
                 text: Optional[str] = None,
                 tooltip: str = "",
                 on_click: Optional[Callable] = None,
                 color: Optional[str] = None):
        self.icon = icon
        self.text = text
        self.tooltip_text = tooltip
        self.on_click_handler = on_click
        self.color = color or "white"
        
        content = None
        if icon:
            content = ft.Icon(icon, size=16, color=self.color)
        elif text:
            content = ft.Text(text, size=14, color=self.color, weight=ft.FontWeight.W_500)
        
        super().__init__(
            width=32,
            height=32,
            content=content,
            alignment=ft.alignment.center,
            border_radius=4,
            on_hover=self._on_hover,
            on_click=self._on_click,
            tooltip=tooltip
        )
    
    def _on_hover(self, e: ft.ControlEvent):
        """Handle hover effect"""
        if e.data == "true":
            self.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
        else:
            self.bgcolor = None
        self.update()
    
    def _on_click(self, e: ft.ControlEvent):
        """Handle click event"""
        if self.on_click_handler:
            self.on_click_handler()


class FloatingToolbar(ft.Container):
    """Floating toolbar for component editing"""
    
    def __init__(self, on_action: Callable[[str], None]):
        self.on_action = on_action
        
        super().__init__(
            bgcolor="#212529",  # Gray-900
            border_radius=8,
            padding=8,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
            ),
            visible=False,
            content=self._build_content()
        )
    
    def _build_content(self) -> ft.Control:
        """Build toolbar content"""
        return ft.Row([
            ToolbarButton(
                icon=ft.Icons.ARROW_UPWARD,
                tooltip="Move Up",
                on_click=lambda: self.on_action("move_up")
            ),
            ToolbarButton(
                icon=ft.Icons.ARROW_DOWNWARD,
                tooltip="Move Down",
                on_click=lambda: self.on_action("move_down")
            ),
            ToolbarButton(
                icon=ft.Icons.CONTENT_COPY,
                tooltip="Duplicate",
                on_click=lambda: self.on_action("duplicate")
            ),
            ft.Container(width=1, height=24, bgcolor="#374151"),  # Separator
            ToolbarButton(
                icon=ft.Icons.DELETE,
                tooltip="Delete",
                on_click=lambda: self.on_action("delete"),
                color="#EF4444"  # Red for delete
            )
        ], spacing=4)
    
    def show_at_position(self, x: float, y: float):
        """Show toolbar at specific position"""
        # Position toolbar above the element
        self.top = y - 45
        self.left = x
        self.visible = True
        self.update()
    
    def hide(self):
        """Hide the toolbar"""
        self.visible = False
        self.update()