"""Sidebar navigation panel"""

import flet as ft
from typing import Callable, Optional, List, Dict


class SidebarItem:
    """Individual sidebar navigation item"""
    def __init__(self, icon: str, tooltip: str, view_name: str, active: bool = False):
        self.icon = icon
        self.tooltip = tooltip
        self.view_name = view_name
        self.active = active


class SidebarPanel(ft.Container):
    """Left sidebar navigation panel"""
    
    def __init__(self, on_navigation: Callable[[str], None]):
        self.on_navigation = on_navigation
        self.items: List[SidebarItem] = [
            SidebarItem("dashboard", "Page Builder", "page_builder", active=True),
            SidebarItem("article", "Content", "content"),
            SidebarItem("analytics", "Analytics", "analytics"),
            SidebarItem("settings", "Settings", "settings"),
        ]
        
        super().__init__(
            bgcolor="#212529",  # Gray-900
            padding=ft.padding.symmetric(vertical=24),
            content=self._build_content()
        )
    
    def _build_content(self) -> ft.Control:
        """Build the sidebar content"""
        nav_items = []
        
        # Top navigation items
        for item in self.items:
            nav_items.append(self._create_nav_item(item))
        
        # Spacer
        nav_items.append(ft.Container(expand=True))
        
        # Help button at bottom
        nav_items.append(self._create_nav_item(
            SidebarItem("help_outline", "Help", "help")
        ))
        
        return ft.Column(
            controls=nav_items,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
            expand=True
        )
    
    def _create_nav_item(self, item: SidebarItem) -> ft.Control:
        """Create a navigation item"""
        return ft.Container(
            width=48,
            height=48,
            bgcolor="#5E6AD2" if item.active else None,
            border_radius=12,
            on_hover=lambda e: self._on_hover(e, item),
            on_click=lambda e: self._on_click(e, item),
            content=ft.Icon(
                name=item.icon,
                color="white" if item.active else "#9CA3AF",  # Gray-400
                size=24
            ),
            tooltip=item.tooltip
        )
    
    def _on_hover(self, e: ft.ControlEvent, item: SidebarItem):
        """Handle hover effect"""
        if not item.active:
            e.control.bgcolor = "#374151" if e.data == "true" else None  # Gray-700
            e.control.update()
    
    def _on_click(self, e: ft.ControlEvent, item: SidebarItem):
        """Handle navigation click"""
        # Update active states
        for nav_item in self.items:
            nav_item.active = False
        item.active = True
        
        # Rebuild content to update UI
        self.content = self._build_content()
        self.update()
        
        # Trigger navigation callback
        self.on_navigation(item.view_name)
    
    def set_active_view(self, view_name: str):
        """Set the active view programmatically"""
        for item in self.items:
            item.active = item.view_name == view_name
        self.content = self._build_content()
        self.update()