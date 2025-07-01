"""Properties panel for component editing - Fixed for Flet 0.28.3"""

import flet as ft
from typing import Optional, Dict, Any, Callable, List
from models.component import Component, ComponentStyle
from utils.flet_compat import CompatPropertyInput


class PropertiesPanel(ft.Container):
    """Properties panel for editing component properties"""
    
    def __init__(self, on_property_change: Callable[[str, str, Any], None]):
        super().__init__()
        self.on_property_change = on_property_change
        self.current_component: Optional[Component] = None
        
        # Set container properties
        self.bgcolor = "#FFFFFF"
        self.border = ft.border.only(left=ft.BorderSide(1, "#E5E7EB"))
        self.padding = 20
        self.expand = True
        
        # Build initial content
        self.content = self._build_empty_state()
    
    def _build_empty_state(self):
        """Build empty state UI"""
        return ft.Column([
            ft.Text(
                "Properties",
                size=18,
                weight=ft.FontWeight.BOLD,
                color="#1F2937"
            ),
            ft.Container(
                content=ft.Column([
                    ft.Icon(
                        ft.Icons.TUNE_ROUNDED,
                        size=48,
                        color="#9CA3AF"
                    ),
                    ft.Text(
                        "Select a component to edit",
                        size=14,
                        color="#6B7280",
                        text_align=ft.TextAlign.CENTER
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=ft.padding.symmetric(vertical=40),
                alignment=ft.alignment.center,
                expand=True
            )
        ], spacing=20, expand=True)
    
    def set_component(self, component: Optional[Component]):
        """Set the component to edit"""
        self.current_component = component
        if component:
            self.content = self._build_property_editor(component)
        else:
            self.content = self._build_empty_state()
        self.update()
    
    def set_component_data(self, component_data: Dict[str, Any]):
        """Set component from raw data (for state management integration)"""
        # Convert dict to Component-like object for compatibility
        class ComponentData:
            def __init__(self, data):
                self.id = data.get('id', '')
                self.type = data.get('type', '')
                self.name = data.get('name', '')
                self.content = data.get('content', {})
                self.style = ComponentStyle(**data.get('style', {}))
                self.props = data.get('props', {})
        
        component = ComponentData(component_data)
        self.set_component(component)
    
    def _build_property_editor(self, component: Component):
        """Build property editor for a component"""
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Content",
                    icon=ft.Icons.EDIT_ROUNDED,
                    content=self._build_content_tab(component)
                ),
                ft.Tab(
                    text="Style", 
                    icon=ft.Icons.PALETTE_ROUNDED,
                    content=self._build_style_tab(component)
                ),
                ft.Tab(
                    text="Advanced",
                    icon=ft.Icons.SETTINGS_ROUNDED,
                    content=self._build_advanced_tab(component)
                )
            ],
            expand=True
        )
        
        return ft.Column([
            # Header
            ft.Row([
                ft.Icon(
                    self._get_component_icon(component.type),
                    size=20,
                    color="#5E6AD2"
                ),
                ft.Text(
                    f"Editing {component.type}",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color="#1F2937"
                ),
                ft.Container(
                    content=ft.Text(
                        component.id,
                        size=12,
                        color="#6B7280"
                    ),
                    bgcolor="#F3F4F6",
                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    border_radius=4
                )
            ], alignment=ft.MainAxisAlignment.START, spacing=10),
            
            ft.Divider(height=20, color="#E5E7EB"),
            
            # Tabs
            tabs
        ], spacing=0, expand=True)
    
    def _build_content_tab(self, component: Component):
        """Build content properties tab"""
        controls = []
        
        # Component name
        controls.append(
            CompatPropertyInput(
                label="Name",
                value=component.name,
                on_change=lambda v: self._on_property_change(component.id, "name", v)
            )
        )
        
        # Type-specific content
        if component.type == "text":
            controls.append(
                CompatPropertyInput(
                    label="Text",
                    value=component.content.get("text", ""),
                    input_type="textarea",
                    on_change=lambda v: self._on_property_change(component.id, "content.text", v)
                )
            )
        elif component.type == "button":
            controls.append(
                CompatPropertyInput(
                    label="Label",
                    value=component.content.get("label", ""),
                    on_change=lambda v: self._on_property_change(component.id, "content.label", v)
                )
            )
        elif component.type == "image":
            controls.append(
                CompatPropertyInput(
                    label="Source URL",
                    value=component.content.get("src", ""),
                    on_change=lambda v: self._on_property_change(component.id, "content.src", v)
                )
            )
            controls.append(
                CompatPropertyInput(
                    label="Alt Text",
                    value=component.content.get("alt", ""),
                    on_change=lambda v: self._on_property_change(component.id, "content.alt", v)
                )
            )
        
        return ft.Container(
            content=ft.Column(controls, spacing=16, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def _build_style_tab(self, component: Component):
        """Build style properties tab"""
        controls = []
        
        # Position
        controls.append(ft.Text("Position", size=16, weight=ft.FontWeight.W_600))
        controls.append(
            ft.Row([
                CompatPropertyInput(
                    label="Left",
                    value=component.style.left,
                    on_change=lambda v: self._on_property_change(component.id, "style.left", v),
                    expand=True
                ),
                CompatPropertyInput(
                    label="Top",
                    value=component.style.top,
                    on_change=lambda v: self._on_property_change(component.id, "style.top", v),
                    expand=True
                )
            ], spacing=10)
        )
        
        # Size
        controls.append(ft.Text("Size", size=16, weight=ft.FontWeight.W_600))
        controls.append(
            ft.Row([
                CompatPropertyInput(
                    label="Width",
                    value=component.style.width,
                    on_change=lambda v: self._on_property_change(component.id, "style.width", v),
                    expand=True
                ),
                CompatPropertyInput(
                    label="Height",
                    value=component.style.height,
                    on_change=lambda v: self._on_property_change(component.id, "style.height", v),
                    expand=True
                )
            ], spacing=10)
        )
        
        # Colors
        controls.append(ft.Text("Colors", size=16, weight=ft.FontWeight.W_600))
        controls.append(
            CompatPropertyInput(
                label="Background",
                value=component.style.background_color,
                input_type="color",
                on_change=lambda v: self._on_property_change(component.id, "style.background_color", v)
            )
        )
        controls.append(
            CompatPropertyInput(
                label="Text Color",
                value=component.style.color,
                input_type="color",
                on_change=lambda v: self._on_property_change(component.id, "style.color", v)
            )
        )
        
        # Typography
        if component.type in ["text", "button", "heading"]:
            controls.append(ft.Text("Typography", size=16, weight=ft.FontWeight.W_600))
            controls.append(
                CompatPropertyInput(
                    label="Font Size",
                    value=component.style.font_size,
                    on_change=lambda v: self._on_property_change(component.id, "style.font_size", v)
                )
            )
            controls.append(
                CompatPropertyInput(
                    label="Font Weight",
                    value=component.style.font_weight,
                    input_type="dropdown",
                    options=["normal", "bold", "100", "200", "300", "400", "500", "600", "700", "800", "900"],
                    on_change=lambda v: self._on_property_change(component.id, "style.font_weight", v)
                )
            )
        
        return ft.Container(
            content=ft.Column(controls, spacing=16, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def _build_advanced_tab(self, component: Component):
        """Build advanced properties tab"""
        controls = []
        
        # CSS Classes
        controls.append(
            CompatPropertyInput(
                label="CSS Classes",
                value=component.props.get("className", ""),
                on_change=lambda v: self._on_property_change(component.id, "props.className", v)
            )
        )
        
        # Custom attributes
        controls.append(
            CompatPropertyInput(
                label="Custom Attributes",
                value="",
                input_type="textarea",
                on_change=lambda v: self._on_property_change(component.id, "props.attributes", v)
            )
        )
        
        # History
        controls.append(ft.Divider(height=30, color="#E5E7EB"))
        controls.append(ft.Text("History", size=16, weight=ft.FontWeight.W_600))
        controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("Recent changes:", size=14, color="#6B7280"),
                    ft.Text("• Component created", size=12, color="#9CA3AF"),
                    ft.Text("• Name changed", size=12, color="#9CA3AF"),
                    ft.Text("• Style updated", size=12, color="#9CA3AF")
                ], spacing=4),
                bgcolor="#F9FAFB",
                padding=10,
                border_radius=6
            )
        )
        
        return ft.Container(
            content=ft.Column(controls, spacing=16, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def _on_property_change(self, component_id: str, property_path: str, value: Any):
        """Handle property change"""
        if self.on_property_change:
            self.on_property_change(component_id, property_path, value)
    
    def _get_component_icon(self, component_type: str) -> str:
        """Get icon for component type"""
        icons = {
            "text": ft.Icons.TEXT_FIELDS,
            "button": ft.Icons.SMART_BUTTON,
            "image": ft.Icons.IMAGE,
            "container": ft.Icons.SQUARE_OUTLINED,
            "row": ft.Icons.VIEW_COLUMN,
            "column": ft.Icons.VIEW_STREAM,
            "form": ft.Icons.DYNAMIC_FORM
        }
        return icons.get(component_type, ft.Icons.WIDGETS)