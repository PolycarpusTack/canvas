"""Components panel for draggable elements"""

import flet as ft
from typing import Callable, List, Dict, Optional, Tuple
from config.constants import COMPONENT_CATEGORIES
from models.component import Component, ComponentCategory
from components.drag_drop_manager import get_drag_drop_manager, DragOperation


class ComponentItem(ft.Container):
    """Individual draggable component in the panel"""
    
    def __init__(self, component_data: Dict[str, str], on_drag_start: Callable):
        self.component_data = component_data
        self.on_drag_start = on_drag_start
        self.drag_manager = get_drag_drop_manager()
        
        super().__init__(
            bgcolor="#F9FAFB",  # Gray-50
            border=ft.border.all(1, "#E5E7EB"),  # Gray-200
            border_radius=8,
            padding=16,
            on_hover=self._on_hover,
            content=ft.Row([
                ft.Container(
                    width=36,
                    height=36,
                    bgcolor="white",
                    border_radius=6,
                    content=ft.Icon(
                        name=self._get_icon(),
                        color="#5E6AD2",  # Primary
                        size=20
                    ),
                    alignment=ft.alignment.center
                ),
                ft.Column([
                    ft.Text(
                        component_data["name"],
                        weight=ft.FontWeight.W_500,
                        size=14
                    ),
                    ft.Text(
                        component_data["description"],
                        size=12,
                        color="#6B7280"  # Gray-600
                    )
                ], spacing=2, tight=True)
            ], spacing=12)
        )
        
        # Make draggable with advanced drag manager
        self.draggable = ft.Draggable(
            content=self,
            on_drag_start=self._on_enhanced_drag_start
        )
    
    def _on_enhanced_drag_start(self, e: ft.DragStartEvent):
        """
        Enhanced drag start using DragDropManager
        
        CLAUDE.md Implementation:
        - #1.5: Performance-optimized drag operations
        - #9.1: Accessible drag operations
        """
        try:
            # Get mouse position from event if available
            mouse_position = None
            if hasattr(e, 'global_x') and hasattr(e, 'global_y'):
                mouse_position = (e.global_x, e.global_y)
            
            # Start advanced drag operation
            drag_data = self.drag_manager.start_drag(
                component_id=self.component_data.get("id"),
                operation=DragOperation.COPY,  # Library components are copied
                source_type="library",
                properties=self.component_data.copy(),
                mouse_position=mouse_position
            )
            
            # Store drag data for Flet's drag system
            e.data = drag_data.to_json()
            
            # Call original callback for compatibility
            self.on_drag_start(self.component_data)
            
        except Exception as ex:
            print(f"Error starting enhanced drag: {ex}")
            # Fallback to basic drag
            self.on_drag_start(self.component_data)
    
    def _get_icon(self) -> str:
        """Get icon for component type"""
        icon_map = {
            "section": "dashboard",
            "grid": "grid_view",
            "flex": "view_agenda",
            "stack": "layers",
            "tabs": "tab",
            "accordion": "expand_more",
            "kpi_chart": "insert_chart",
            "timeline": "timeline",
            "rich_text": "text_fields",
            "image": "image",
            "video": "videocam",
            "code": "code",
            "input": "input",
            "select": "arrow_drop_down",
            "checkbox": "check_box",
            "button": "smart_button"
        }
        return icon_map.get(self.component_data.get("type", ""), "widgets")
    
    def _on_hover(self, e: ft.ControlEvent):
        """Handle hover effect"""
        if e.data == "true":
            e.control.border = ft.border.all(1, "#5E6AD2")
            e.control.shadow = ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        else:
            e.control.border = ft.border.all(1, "#E5E7EB")
            e.control.shadow = None
        e.control.update()


class ComponentsPanel(ft.Container):
    """Components panel with search and categories"""
    
    def __init__(self, on_component_drag: Callable[[Dict[str, str]], None]):
        self.on_component_drag = on_component_drag
        self.search_value = ""
        self.categories = self._load_categories()
        
        super().__init__(
            bgcolor="white",
            border=ft.border.only(right=ft.BorderSide(1, "#E5E7EB")),
            padding=24,
            content=self._build_content()
        )
    
    def _load_categories(self) -> List[ComponentCategory]:
        """Load component categories from config"""
        return [
            ComponentCategory(
                name=cat["name"],
                icon=cat["icon"],
                components=cat["components"]
            )
            for cat in COMPONENT_CATEGORIES
        ]
    
    def _build_content(self) -> ft.Control:
        """Build the panel content"""
        return ft.Column([
            # Header
            ft.Row([
                ft.Text(
                    "Components",
                    size=18,
                    weight=ft.FontWeight.W_600
                ),
                ft.IconButton(
                    icon=ft.Icons.ADD,
                    icon_color="#5E6AD2",
                    tooltip="Add custom component"
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # Search box
            ft.TextField(
                hint_text="Search components...",
                border_radius=8,
                prefix_icon=ft.Icons.SEARCH,
                on_change=self._on_search,
                height=40,
                text_size=14,
                border_color="#E5E7EB",
                focused_border_color="#5E6AD2"
            ),
            
            # Categories
            ft.Column(
                controls=self._build_categories(),
                spacing=24,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
        ], spacing=16, expand=True)
    
    def _build_categories(self) -> List[ft.Control]:
        """Build category sections"""
        categories = []
        
        for category in self.categories:
            # Filter components based on search
            filtered_components = [
                comp for comp in category.components
                if self._matches_search(comp)
            ]
            
            if filtered_components:
                categories.append(
                    ft.Column([
                        ft.Text(
                            category.name.upper(),
                            size=12,
                            weight=ft.FontWeight.W_600,
                            color="#6B7280"  # Gray-600
                        ),
                        ft.Column([
                            ComponentItem(comp, self.on_component_drag).draggable
                            for comp in filtered_components
                        ], spacing=8)
                    ], spacing=12)
                )
        
        return categories
    
    def _matches_search(self, component: Dict[str, str]) -> bool:
        """Check if component matches search query"""
        if not self.search_value:
            return True
        
        search_lower = self.search_value.lower()
        return (search_lower in component["name"].lower() or 
                search_lower in component["description"].lower())
    
    def _on_search(self, e: ft.ControlEvent):
        """Handle search input"""
        self.search_value = e.control.value
        # Rebuild categories with filtered results
        categories_column = self.content.controls[2]
        categories_column.controls = self._build_categories()
        self.update()