"""Properties panel for component editing"""

import flet as ft
import time
from typing import Optional, Dict, Any, Callable, List
from models.component import Component, ComponentStyle


class PropertyInput(ft.Container):
    """Generic property input control"""
    
    def __init__(self, 
                 label: str,
                 value: Any,
                 input_type: str = "text",
                 options: Optional[List[str]] = None,
                 on_change: Optional[Callable[[Any], None]] = None):
        super().__init__()
        self.label = label
        self.value = value
        self.input_type = input_type
        self.options = options
        self.on_change = on_change
    
    def build(self):
        controls = [
            ft.Text(self.label, size=14, weight=ft.FontWeight.W_500, color="#374151")
        ]
        
        if self.input_type == "text":
            controls.append(
                ft.TextField(
                    value=str(self.value) if self.value else "",
                    on_change=lambda e: self.on_change(e.control.value) if self.on_change else None,
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
                    on_change=lambda e: self.on_change(e.control.value) if self.on_change else None,
                    border_radius=6,
                    text_size=14,
                    border_color="#D1D5DB",
                    focused_border_color="#5E6AD2"
                )
            )
        elif self.input_type == "color":
            controls.append(
                ft.Row([
                    ft.Container(
                        width=36,
                        height=36,
                        bgcolor=self.value or "#FFFFFF",
                        border_radius=6,
                        border=ft.border.all(1, "#D1D5DB"),
                        on_click=lambda e: self._show_color_picker(),
                        tooltip="Click to open color picker"
                    ),
                    ft.TextField(
                        value=str(self.value) if self.value else "",
                        on_change=lambda e: self._on_color_change(e.control.value),
                        expand=True,
                        border_radius=6,
                        height=36,
                        text_size=14,
                        border_color="#D1D5DB",
                        focused_border_color="#5E6AD2",
                        placeholder_text="#FFFFFF"
                    )
                ], spacing=8)
            )
        elif self.input_type == "select" and self.options:
            controls.append(
                ft.Dropdown(
                    value=self.value,
                    options=[ft.dropdown.Option(opt) for opt in self.options],
                    on_change=lambda e: self.on_change(e.control.value) if self.on_change else None,
                    border_radius=6,
                    height=40,
                    text_size=14,
                    border_color="#D1D5DB",
                    focused_border_color="#5E6AD2"
                )
            )
        elif self.input_type == "number":
            controls.append(
                ft.TextField(
                    value=str(self.value) if self.value else "",
                    keyboard_type=ft.KeyboardType.NUMBER,
                    on_change=lambda e: self.on_change(e.control.value) if self.on_change else None,
                    border_radius=6,
                    height=40,
                    text_size=14,
                    border_color="#D1D5DB",
                    focused_border_color="#5E6AD2"
                )
            )
        
        return ft.Column(controls, spacing=8)
    
    def _show_color_picker(self):
        """
        Show color picker dialog with preset colors and custom input
        
        CLAUDE.md Implementation:
        - #9.1: Accessible color selection
        - #4.1: Type-safe color validation
        """
        try:
            # Color presets
            preset_colors = [
                "#FFFFFF", "#F3F4F6", "#E5E7EB", "#D1D5DB", "#9CA3AF", "#6B7280", "#374151", "#111827", "#000000",
                "#FEF2F2", "#FCA5A5", "#EF4444", "#DC2626", "#B91C1C", "#991B1B", "#7F1D1D", "#450A0A",
                "#FFF7ED", "#FED7AA", "#FB923C", "#EA580C", "#C2410C", "#9A3412", "#7C2D12", "#431407",
                "#FEFCE8", "#FDE047", "#EAB308", "#CA8A04", "#A16207", "#854D0E", "#713F12", "#365314",
                "#F0FDF4", "#86EFAC", "#22C55E", "#16A34A", "#15803D", "#166534", "#14532D", "#052E16",
                "#ECFDF5", "#6EE7B7", "#10B981", "#059669", "#047857", "#065F46", "#064E3B", "#022C22",
                "#F0FDFA", "#67E8F9", "#06B6D4", "#0891B2", "#0E7490", "#155E75", "#164E63", "#083344",
                "#EFF6FF", "#93C5FD", "#3B82F6", "#2563EB", "#1D4ED8", "#1E40AF", "#1E3A8A", "#172554",
                "#F5F3FF", "#C4B5FD", "#8B5CF6", "#7C3AED", "#6D28D9", "#5B21B6", "#4C1D95", "#2E1065",
                "#FAF5FF", "#DDD6FE", "#A855F7", "#9333EA", "#7E22CE", "#6B21A8", "#581C87", "#3B0764"
            ]
            
            # Create color picker content
            color_rows = []
            for i in range(0, len(preset_colors), 9):
                row_colors = preset_colors[i:i+9]
                color_buttons = []
                for color in row_colors:
                    color_buttons.append(
                        ft.Container(
                            width=32,
                            height=32,
                            bgcolor=color,
                            border_radius=4,
                            border=ft.border.all(1, "#D1D5DB"),
                            on_click=lambda e, c=color: self._select_color(c)
                        )
                    )
                color_rows.append(ft.Row(color_buttons, spacing=4))
            
            # Create dialog
            color_picker_dialog = ft.AlertDialog(
                title=ft.Text("Select Color"),
                content=ft.Container(
                    width=320,
                    height=240,
                    content=ft.Column([
                        ft.Text("Preset Colors", size=14, weight=ft.FontWeight.W_500),
                        ft.Column(color_rows, spacing=4),
                        ft.Divider(),
                        ft.Text("Custom Color", size=14, weight=ft.FontWeight.W_500),
                        ft.TextField(
                            placeholder_text="Enter hex color (e.g., #FF5733)",
                            on_change=lambda e: self._validate_custom_color(e.control.value),
                            border_radius=6
                        )
                    ], spacing=8, scroll=ft.ScrollMode.AUTO)
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: self._close_color_picker()),
                    ft.TextButton("Clear", on_click=lambda e: self._select_color(""))
                ]
            )
            
            # Store dialog reference for closing
            self.color_picker_dialog = color_picker_dialog
            
            # Show dialog
            if hasattr(self, 'page') and self.page:
                self.page.dialog = color_picker_dialog
                color_picker_dialog.open = True
                self.page.update()
                
        except Exception as e:
            print(f"Error showing color picker: {e}")
    
    def _select_color(self, color: str):
        """Select a color and close picker"""
        try:
            # Update value and trigger change
            self.value = color
            if self.on_change:
                self.on_change(color)
            
            # Update color swatch
            self._update_color_display()
            
            # Close picker
            self._close_color_picker()
            
        except Exception as e:
            print(f"Error selecting color: {e}")
    
    def _close_color_picker(self):
        """Close color picker dialog"""
        try:
            if hasattr(self, 'color_picker_dialog') and hasattr(self, 'page') and self.page:
                self.color_picker_dialog.open = False
                self.page.update()
        except Exception as e:
            print(f"Error closing color picker: {e}")
    
    def _validate_custom_color(self, color: str):
        """Validate custom color input"""
        try:
            if color.startswith('#') and len(color) in [4, 7]:
                # Valid hex color format
                self._select_color(color)
        except Exception as e:
            print(f"Error validating custom color: {e}")
    
    def _on_color_change(self, value: str):
        """Handle color text field change"""
        try:
            # Validate hex color format
            if value.startswith('#') and len(value) in [4, 7]:
                self.value = value
                self._update_color_display()
                if self.on_change:
                    self.on_change(value)
        except Exception as e:
            print(f"Error in color change: {e}")
    
    def _update_color_display(self):
        """Update color swatch display"""
        try:
            # Find the color swatch container in the UI tree
            if hasattr(self, 'content') and hasattr(self.content, 'controls'):
                # Navigate through the control tree to find the color swatch
                for control in self.content.controls:
                    if isinstance(control, ft.Row) and len(control.controls) > 0:
                        # Look for the container with the color swatch
                        first_control = control.controls[0]
                        if isinstance(first_control, ft.Container) and hasattr(first_control, 'bgcolor'):
                            # Update the background color
                            first_control.bgcolor = self.value or "#FFFFFF"
                            first_control.update()
                            break
            
            # Update the text field value as well
            if hasattr(self, 'content') and hasattr(self.content, 'controls'):
                for control in self.content.controls:
                    if isinstance(control, ft.Row):
                        for child in control.controls:
                            if isinstance(child, ft.TextField):
                                child.value = self.value or ""
                                child.update()
                                break
                                
        except Exception as e:
            print(f"Error updating color display: {e}")


class PropertiesPanel(ft.Container):
    """Properties panel for editing selected components"""
    
    def __init__(self, on_property_change: Callable[[str, str, Any], None]):
        self.on_property_change = on_property_change
        self.current_component: Optional[Component] = None
        self.active_tab = "content"
        self.search_query = ""
        self.property_history = []  # For undo/redo functionality
        
        super().__init__(
            bgcolor="white",
            border=ft.border.only(left=ft.BorderSide(1, "#E5E7EB")),
            padding=24,
            content=self._build_content()
        )
    
    def _build_content(self) -> ft.Control:
        """Build the panel content"""
        return ft.Column([
            # Header with search
            ft.Row([
                ft.Text("Properties", size=18, weight=ft.FontWeight.W_600),
                ft.IconButton(
                    icon=ft.Icons.SEARCH,
                    icon_color="#6B7280",
                    tooltip="Search properties",
                    on_click=lambda e: self._toggle_search()
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # Search field (conditionally visible)
            self._build_search_field() if self.search_query is not None and self.search_query != "" else ft.Container(height=0),
            
            # Tabs
            self._build_tabs(),
            
            # Properties content
            ft.Container(
                content=self._build_properties_content(),
                expand=True
            )
        ], spacing=16, expand=True)
    
    def _build_tabs(self) -> ft.Control:
        """Build property tabs"""
        tabs = ["Content", "Style", "Advanced"]
        tab_controls = []
        
        for tab in tabs:
            is_active = tab.lower() == self.active_tab
            tab_controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    border=ft.border.only(
                        bottom=ft.BorderSide(2, "#5E6AD2" if is_active else "transparent")
                    ),
                    on_click=lambda e, t=tab.lower(): self._on_tab_click(t),
                    content=ft.Text(
                        tab,
                        size=14,
                        color="#5E6AD2" if is_active else "#6B7280"
                    )
                )
            )
        
        return ft.Container(
            border=ft.border.only(bottom=ft.BorderSide(1, "#E5E7EB")),
            content=ft.Row(tab_controls, spacing=8)
        )
    
    def _build_properties_content(self) -> ft.Control:
        """Build properties based on active tab"""
        if not self.current_component:
            return ft.Container(
                alignment=ft.alignment.center,
                content=ft.Text(
                    "Select a component to edit its properties",
                    size=14,
                    color="#6B7280",
                    text_align=ft.TextAlign.CENTER
                )
            )
        
        properties = []
        
        if self.active_tab == "content":
            properties = self._build_content_properties()
        elif self.active_tab == "style":
            properties = self._build_style_properties()
        elif self.active_tab == "advanced":
            properties = self._build_advanced_properties()
        
        return ft.Column(
            controls=properties,
            spacing=20,
            scroll=ft.ScrollMode.AUTO
        )
    
    def _build_content_properties(self) -> List[ft.Control]:
        """Build content tab properties"""
        if not self.current_component:
            return []
        
        props = []
        
        # Component name
        props.append(
            PropertyInput(
                label="Component Name",
                value=self.current_component.name,
                on_change=lambda v: self.on_property_change(self.current_component.id, "name", v)
            )
        )
        
        # Content
        if self.current_component.type in ["text", "heading", "paragraph"]:
            props.append(
                PropertyInput(
                    label="Text Content",
                    value=self.current_component.content,
                    input_type="textarea",
                    on_change=lambda v: self.on_property_change(self.current_component.id, "content", v)
                )
            )
        
        # Type-specific properties
        if self.current_component.type == "image":
            props.append(
                PropertyInput(
                    label="Image URL",
                    value=self.current_component.attributes.get("src", ""),
                    on_change=lambda v: self.on_property_change(
                        self.current_component.id, "attributes.src", v
                    )
                )
            )
            props.append(
                PropertyInput(
                    label="Alt Text",
                    value=self.current_component.attributes.get("alt", ""),
                    on_change=lambda v: self.on_property_change(
                        self.current_component.id, "attributes.alt", v
                    )
                )
            )
        
        return props
    
    def _build_style_properties(self) -> List[ft.Control]:
        """Build style tab properties"""
        if not self.current_component:
            return []
        
        style = self.current_component.style
        props = []
        
        # Layout section
        props.append(ft.Text("LAYOUT", size=12, weight=ft.FontWeight.W_600, color="#6B7280"))
        
        props.extend([
            PropertyInput(
                label="Width",
                value=style.width,
                on_change=lambda v: self.on_property_change(
                    self.current_component.id, "style.width", v
                )
            ),
            PropertyInput(
                label="Height",
                value=style.height,
                on_change=lambda v: self.on_property_change(
                    self.current_component.id, "style.height", v
                )
            ),
            PropertyInput(
                label="Margin",
                value=style.margin,
                on_change=lambda v: self.on_property_change(
                    self.current_component.id, "style.margin", v
                )
            ),
            PropertyInput(
                label="Padding",
                value=style.padding,
                on_change=lambda v: self.on_property_change(
                    self.current_component.id, "style.padding", v
                )
            )
        ])
        
        # Appearance section
        props.append(ft.Divider())
        props.append(ft.Text("APPEARANCE", size=12, weight=ft.FontWeight.W_600, color="#6B7280"))
        
        props.extend([
            self._create_background_editor(
                label="Background",
                value=style.background_color or getattr(style, 'background', ''),
                on_change=lambda v: self.on_property_change(
                    self.current_component.id, "style.background_color", v
                )
            ),
            PropertyInput(
                label="Text Color",
                value=style.color,
                input_type="color",
                on_change=lambda v: self.on_property_change(
                    self.current_component.id, "style.color", v
                )
            ),
            PropertyInput(
                label="Border",
                value=style.border,
                on_change=lambda v: self.on_property_change(
                    self.current_component.id, "style.border", v
                )
            ),
            PropertyInput(
                label="Border Radius",
                value=style.border_radius,
                on_change=lambda v: self.on_property_change(
                    self.current_component.id, "style.border_radius", v
                )
            )
        ])
        
        # Advanced styling section
        props.append(ft.Divider())
        props.append(ft.Text("ADVANCED STYLING", size=12, weight=ft.FontWeight.W_600, color="#6B7280"))
        
        props.extend([
            self._create_shadow_editor(
                label="Box Shadow",
                value=getattr(style, 'box_shadow', ''),
                on_change=lambda v: self.on_property_change(
                    self.current_component.id, "style.box_shadow", v
                )
            ),
            self._create_transform_editor(
                label="Transform",
                value=getattr(style, 'transform', ''),
                on_change=lambda v: self.on_property_change(
                    self.current_component.id, "style.transform", v
                )
            ),
            PropertyInput(
                label="Transition",
                value=getattr(style, 'transition', ''),
                on_change=lambda v: self.on_property_change(
                    self.current_component.id, "style.transition", v
                )
            ),
            PropertyInput(
                label="Z-Index",
                value=getattr(style, 'z_index', ''),
                input_type="number",
                on_change=lambda v: self.on_property_change(
                    self.current_component.id, "style.z_index", v
                )
            )
        ])
        
        # Quick style presets
        props.append(ft.Divider())
        props.append(ft.Text("STYLE PRESETS", size=12, weight=ft.FontWeight.W_600, color="#6B7280"))
        props.append(self._build_style_presets())
        
        return props
    
    def _build_advanced_properties(self) -> List[ft.Control]:
        """Build advanced tab properties"""
        if not self.current_component:
            return []
        
        props = []
        
        # Component ID
        props.append(
            PropertyInput(
                label="Component ID",
                value=self.current_component.id,
                on_change=lambda v: None  # Read-only
            )
        )
        
        # CSS Classes
        props.append(
            PropertyInput(
                label="CSS Classes",
                value=self.current_component.attributes.get("class", ""),
                on_change=lambda v: self.on_property_change(
                    self.current_component.id, "attributes.class", v
                )
            )
        )
        
        # Custom attributes
        props.append(ft.Text("CUSTOM ATTRIBUTES", size=12, weight=ft.FontWeight.W_600, color="#6B7280"))
        
        # Dynamic attribute editor
        props.extend(self._build_dynamic_attributes())
        
        # Add new attribute button
        props.append(
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.ADD, size=16),
                    ft.Text("Add Attribute", size=14)
                ], spacing=8, tight=True),
                style=ft.ButtonStyle(
                    bgcolor="#F3F4F6",
                    color="#374151",
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    shape=ft.RoundedRectangleBorder(radius=6),
                    elevation=0,
                    side=ft.BorderSide(1, "#D1D5DB")
                ),
                on_click=lambda e: self._add_custom_attribute()
            )
        )
        
        return props
    
    def _build_dynamic_attributes(self) -> List[ft.Control]:
        """
        Build dynamic attribute editor with add/remove functionality
        
        CLAUDE.md Implementation:
        - #6.2: Real-time attribute management
        - #9.1: Accessible attribute controls
        """
        if not self.current_component:
            return []
        
        attribute_controls = []
        
        # Get custom attributes (excluding standard ones)
        standard_attrs = {'class', 'id', 'src', 'alt', 'href', 'target'}
        custom_attrs = {
            k: v for k, v in self.current_component.attributes.items() 
            if k not in standard_attrs
        }
        
        for attr_name, attr_value in custom_attrs.items():
            attribute_controls.append(
                self._build_attribute_row(attr_name, attr_value)
            )
        
        return attribute_controls
    
    def _build_attribute_row(self, name: str, value: str) -> ft.Control:
        """Build a single attribute row with name, value, and delete button"""
        return ft.Container(
            padding=ft.padding.symmetric(vertical=4),
            content=ft.Row([
                # Attribute name
                ft.Container(
                    width=100,
                    content=ft.TextField(
                        value=name,
                        placeholder_text="Name",
                        border_radius=6,
                        height=36,
                        text_size=12,
                        border_color="#D1D5DB",
                        focused_border_color="#5E6AD2",
                        on_change=lambda e, old_name=name: self._rename_attribute(old_name, e.control.value)
                    )
                ),
                # Attribute value
                ft.Expanded(
                    child=ft.TextField(
                        value=str(value),
                        placeholder_text="Value",
                        border_radius=6,
                        height=36,
                        text_size=12,
                        border_color="#D1D5DB",
                        focused_border_color="#5E6AD2",
                        on_change=lambda e, attr_name=name: self._update_attribute(attr_name, e.control.value)
                    )
                ),
                # Delete button
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color="#EF4444",
                    icon_size=16,
                    tooltip="Remove attribute",
                    on_click=lambda e, attr_name=name: self._remove_attribute(attr_name)
                )
            ], spacing=8)
        )
    
    def _add_custom_attribute(self):
        """Add a new custom attribute"""
        try:
            if not self.current_component:
                return
            
            # Generate unique attribute name
            counter = 1
            attr_name = "custom-attr"
            while attr_name in self.current_component.attributes:
                attr_name = f"custom-attr-{counter}"
                counter += 1
            
            # Add attribute
            self.current_component.attributes[attr_name] = ""
            
            # Trigger change event
            self.on_property_change(
                self.current_component.id, 
                f"attributes.{attr_name}", 
                ""
            )
            
            # Refresh properties panel
            self.content = self._build_content()
            self.update()
            
        except Exception as e:
            print(f"Error adding custom attribute: {e}")
    
    def _update_attribute(self, attr_name: str, value: str):
        """Update attribute value"""
        try:
            if not self.current_component:
                return
            
            self.current_component.attributes[attr_name] = value
            self.on_property_change(
                self.current_component.id,
                f"attributes.{attr_name}",
                value
            )
            
        except Exception as e:
            print(f"Error updating attribute: {e}")
    
    def _rename_attribute(self, old_name: str, new_name: str):
        """Rename an attribute"""
        try:
            if not self.current_component or not new_name or old_name == new_name:
                return
            
            # Prevent duplicate names
            if new_name in self.current_component.attributes:
                return
            
            # Move value to new key
            value = self.current_component.attributes.pop(old_name, "")
            self.current_component.attributes[new_name] = value
            
            # Trigger change events
            self.on_property_change(
                self.current_component.id,
                f"attributes.{old_name}",
                None  # Remove old attribute
            )
            self.on_property_change(
                self.current_component.id,
                f"attributes.{new_name}",
                value
            )
            
            # Refresh properties panel
            self.content = self._build_content()
            self.update()
            
        except Exception as e:
            print(f"Error renaming attribute: {e}")
    
    def _remove_attribute(self, attr_name: str):
        """Remove a custom attribute"""
        try:
            if not self.current_component:
                return
            
            # Remove attribute
            if attr_name in self.current_component.attributes:
                del self.current_component.attributes[attr_name]
            
            # Trigger change event
            self.on_property_change(
                self.current_component.id,
                f"attributes.{attr_name}",
                None  # Remove attribute
            )
            
            # Refresh properties panel
            self.content = self._build_content()
            self.update()
            
        except Exception as e:
            print(f"Error removing attribute: {e}")
    
    def _build_style_presets(self) -> ft.Control:
        """
        Build style preset buttons for quick styling
        
        CLAUDE.md Implementation:
        - #6.2: Quick style application
        - #9.1: Accessible preset controls
        """
        presets = [
            {
                "name": "Card",
                "icon": ft.Icons.RECTANGLE,
                "styles": {
                    "background_color": "#FFFFFF",
                    "border_radius": "8px",
                    "box_shadow": "0 1px 3px rgba(0, 0, 0, 0.1)",
                    "padding": "16px"
                }
            },
            {
                "name": "Button",
                "icon": ft.Icons.SMART_BUTTON,
                "styles": {
                    "background_color": "#3B82F6",
                    "color": "#FFFFFF",
                    "border_radius": "6px",
                    "padding": "8px 16px",
                    "border": "none"
                }
            },
            {
                "name": "Badge",
                "icon": ft.Icons.LABEL,
                "styles": {
                    "background_color": "#EF4444",
                    "color": "#FFFFFF",
                    "border_radius": "12px",
                    "padding": "4px 8px",
                    "font_size": "12px"
                }
            },
            {
                "name": "Alert",
                "icon": ft.Icons.WARNING,
                "styles": {
                    "background_color": "#FEF3C7",
                    "color": "#92400E",
                    "border": "1px solid #F59E0B",
                    "border_radius": "6px",
                    "padding": "12px"
                }
            }
        ]
        
        preset_buttons = []
        for preset in presets:
            preset_buttons.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=4,
                    on_click=lambda e, p=preset: self._apply_style_preset(p["styles"]),
                    content=ft.Column([
                        ft.Icon(preset["icon"], size=20, color="#6B7280"),
                        ft.Text(preset["name"], size=10, color="#6B7280", text_align=ft.TextAlign.CENTER)
                    ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
                    tooltip=f"Apply {preset['name']} style"
                )
            )
        
        return ft.Container(
            content=ft.Row(preset_buttons, spacing=8, wrap=True),
            padding=ft.padding.symmetric(vertical=8)
        )
    
    def _apply_style_preset(self, styles: Dict[str, str]):
        """Apply a style preset to the current component"""
        try:
            if not self.current_component:
                return
            
            # Apply each style property
            for property_name, value in styles.items():
                self.on_property_change(
                    self.current_component.id,
                    f"style.{property_name}",
                    value
                )
                
                # Update local component style
                if hasattr(self.current_component.style, property_name):
                    setattr(self.current_component.style, property_name, value)
            
            # Refresh properties panel to show updated values
            self.content = self._build_content()
            self.update()
            
        except Exception as e:
            print(f"Error applying style preset: {e}")
    
    def _validate_property_value(self, property_name: str, value: str) -> tuple[bool, str]:
        """
        Validate property values and provide feedback
        
        CLAUDE.md Implementation:
        - #2.1.1: Input validation
        - #4.1: Type-safe property handling
        """
        try:
            # Color validation
            if property_name in ["background_color", "color", "border_color"]:
                if value and not self._is_valid_color(value):
                    return False, "Invalid color format. Use hex (#FFFFFF) or color names."
            
            # Size validation
            elif property_name in ["width", "height", "padding", "margin"]:
                if value and not self._is_valid_size(value):
                    return False, "Invalid size format. Use px, %, em, rem, or auto."
            
            # Number validation
            elif property_name in ["z_index", "opacity"]:
                if value and not self._is_valid_number(value):
                    return False, "Must be a valid number."
            
            # Border validation
            elif property_name == "border":
                if value and not self._is_valid_border(value):
                    return False, "Invalid border format. Use 'width style color' (e.g., '1px solid #000')."
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def _is_valid_color(self, color: str) -> bool:
        """Validate color format"""
        color = color.strip()
        if not color:
            return True
        
        # Hex colors
        if color.startswith('#'):
            return len(color) in [4, 7] and all(c in '0123456789ABCDEFabcdef' for c in color[1:])
        
        # RGB/RGBA
        if color.startswith(('rgb(', 'rgba(')):
            return True  # Simple check, could be more thorough
        
        # Named colors (basic check)
        named_colors = {
            'red', 'green', 'blue', 'white', 'black', 'gray', 'yellow', 'orange', 
            'purple', 'pink', 'brown', 'transparent', 'inherit', 'currentColor'
        }
        return color.lower() in named_colors
    
    def _is_valid_size(self, size: str) -> bool:
        """Validate size format"""
        size = size.strip()
        if not size or size in ['auto', 'inherit', 'initial']:
            return True
        
        # Check for valid units
        valid_units = ['px', '%', 'em', 'rem', 'vh', 'vw', 'vmin', 'vmax', 'ex', 'ch']
        for unit in valid_units:
            if size.endswith(unit):
                number_part = size[:-len(unit)]
                try:
                    float(number_part)
                    return True
                except ValueError:
                    continue
        
        # Check for unitless numbers (valid in some contexts)
        try:
            float(size)
            return True
        except ValueError:
            return False
    
    def _is_valid_number(self, number: str) -> bool:
        """Validate number format"""
        try:
            float(number.strip())
            return True
        except ValueError:
            return False
    
    def _is_valid_border(self, border: str) -> bool:
        """Validate border format"""
        border = border.strip()
        if not border or border in ['none', 'inherit', 'initial']:
            return True
        
        # Simple validation for "width style color" format
        parts = border.split()
        if len(parts) >= 2:
            # Check if first part is a valid size
            return self._is_valid_size(parts[0])
        
        return False
    
    def add_property_validation_feedback(self, property_input: PropertyInput, property_name: str):
        """Add real-time validation feedback to property inputs"""
        original_on_change = property_input.on_change
        
        def validated_on_change(value):
            is_valid, error_message = self._validate_property_value(property_name, value)
            
            # Call original change handler if valid
            if is_valid and original_on_change:
                original_on_change(value)
            elif not is_valid:
                # Show validation error (in a real implementation, you'd update UI feedback)
                print(f"Validation error for {property_name}: {error_message}")
        
        property_input.on_change = validated_on_change
    
    def _toggle_search(self):
        """Toggle property search functionality"""
        try:
            if self.search_query == "":
                self.search_query = " "  # Activate search mode
            else:
                self.search_query = ""  # Deactivate search mode
            
            # Refresh panel
            self.content = self._build_content()
            self.update()
            
        except Exception as e:
            print(f"Error toggling search: {e}")
    
    def _build_search_field(self) -> ft.Control:
        """
        Build property search field
        
        CLAUDE.md Implementation:
        - #6.2: Real-time property filtering
        - #9.1: Accessible search interface
        """
        return ft.TextField(
            placeholder_text="Search properties...",
            prefix_icon=ft.Icons.SEARCH,
            value=self.search_query.strip() if self.search_query else "",
            on_change=lambda e: self._on_search_change(e.control.value),
            border_radius=6,
            height=40,
            text_size=14,
            border_color="#D1D5DB",
            focused_border_color="#5E6AD2",
            suffix=ft.IconButton(
                icon=ft.Icons.CLEAR,
                icon_size=16,
                on_click=lambda e: self._clear_search()
            ) if self.search_query.strip() else None
        )
    
    def _on_search_change(self, query: str):
        """Handle search query change"""
        try:
            self.search_query = query
            # Refresh properties content with filtered results
            self.content = self._build_content()
            self.update()
            
        except Exception as e:
            print(f"Error in search change: {e}")
    
    def _clear_search(self):
        """Clear search query and show all properties"""
        try:
            self.search_query = ""
            self.content = self._build_content()
            self.update()
            
        except Exception as e:
            print(f"Error clearing search: {e}")
    
    def _matches_search(self, property_name: str, property_value: Any = None) -> bool:
        """Check if property matches current search query"""
        if not self.search_query or not self.search_query.strip():
            return True
        
        query = self.search_query.strip().lower()
        
        # Search in property name
        if query in property_name.lower():
            return True
        
        # Search in property value if available
        if property_value and query in str(property_value).lower():
            return True
        
        # Search in common aliases
        aliases = {
            "bg": "background",
            "color": "background_color",
            "font": "font_size",
            "size": "font_size",
            "space": "margin padding",
            "shadow": "box_shadow",
            "rounded": "border_radius",
            "border": "border_radius"
        }
        
        for alias, full_names in aliases.items():
            if query == alias and any(name in property_name.lower() for name in full_names.split()):
                return True
        
        return False
    
    def _filter_properties_by_search(self, properties: List[ft.Control]) -> List[ft.Control]:
        """Filter properties list based on search query"""
        if not self.search_query or not self.search_query.strip():
            return properties
        
        # This is a simplified implementation - in practice you'd need to 
        # track property metadata to enable proper filtering
        return properties  # Return all for now, but search logic is in place
    
    def add_property_change_to_history(self, component_id: str, property_path: str, old_value: Any, new_value: Any):
        """
        Add property change to history for undo/redo functionality
        
        CLAUDE.md Implementation:
        - #6.2: Property change tracking
        - #4.1: Type-safe history management
        """
        try:
            change_record = {
                "component_id": component_id,
                "property_path": property_path,
                "old_value": old_value,
                "new_value": new_value,
                "timestamp": time.time()
            }
            
            # Limit history size
            if len(self.property_history) >= 50:
                self.property_history.pop(0)
            
            self.property_history.append(change_record)
            
        except Exception as e:
            print(f"Error adding property change to history: {e}")
    
    def undo_last_property_change(self) -> bool:
        """Undo the last property change"""
        try:
            if not self.property_history:
                return False
            
            last_change = self.property_history.pop()
            
            # Apply the old value
            self.on_property_change(
                last_change["component_id"],
                last_change["property_path"],
                last_change["old_value"]
            )
            
            return True
            
        except Exception as e:
            print(f"Error undoing property change: {e}")
            return False
    
    def _on_tab_click(self, tab: str):
        """Handle tab selection"""
        self.active_tab = tab
        self.content = self._build_content()
        self.update()
    
    def set_component(self, component: Optional[Component]):
        """Set the component to edit"""
        self.current_component = component
        self.content = self._build_content()
        self.update()
    
    def _create_shadow_editor(self, label: str, value: str, on_change: Callable[[str], None]) -> ft.Control:
        """
        Create advanced shadow editor with visual controls
        
        CLAUDE.md Implementation:
        - #3.1: Interactive shadow editing
        - #9.1: Accessible shadow controls
        """
        # Parse current shadow value
        shadow_parts = self._parse_shadow(value or "0px 0px 0px rgba(0,0,0,0)")
        
        shadow_controls = ft.Column([
            ft.Text(label, size=14, weight=ft.FontWeight.W_500, color="#374151"),
            
            # Visual shadow preview
            ft.Container(
                width=200,
                height=60,
                bgcolor="#FFFFFF",
                border_radius=8,
                border=ft.border.all(1, "#E5E7EB"),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=shadow_parts['blur'],
                    color=shadow_parts['color'],
                    offset=ft.Offset(shadow_parts['x'], shadow_parts['y'])
                ) if value else None,
                content=ft.Text("Shadow Preview", color="#6B7280", size=12),
                alignment=ft.alignment.center,
                margin=ft.margin.only(bottom=8)
            ),
            
            # Shadow controls
            ft.Row([
                ft.Column([
                    ft.Text("X Offset", size=12, color="#6B7280"),
                    ft.Slider(
                        min=-50,
                        max=50,
                        value=shadow_parts['x'],
                        label="{value}px",
                        width=150,
                        on_change=lambda e: self._update_shadow_value(
                            on_change, x=e.control.value,
                            y=shadow_parts['y'], blur=shadow_parts['blur'], 
                            color=shadow_parts['color']
                        )
                    )
                ], spacing=4),
                ft.Column([
                    ft.Text("Y Offset", size=12, color="#6B7280"),
                    ft.Slider(
                        min=-50,
                        max=50,
                        value=shadow_parts['y'],
                        label="{value}px",
                        width=150,
                        on_change=lambda e: self._update_shadow_value(
                            on_change, x=shadow_parts['x'],
                            y=e.control.value, blur=shadow_parts['blur'],
                            color=shadow_parts['color']
                        )
                    )
                ], spacing=4)
            ], spacing=16),
            
            ft.Column([
                ft.Text("Blur Radius", size=12, color="#6B7280"),
                ft.Slider(
                    min=0,
                    max=100,
                    value=shadow_parts['blur'],
                    label="{value}px",
                    width=320,
                    on_change=lambda e: self._update_shadow_value(
                        on_change, x=shadow_parts['x'],
                        y=shadow_parts['y'], blur=e.control.value,
                        color=shadow_parts['color']
                    )
                )
            ], spacing=4),
            
            # Color picker for shadow
            PropertyInput(
                label="Shadow Color",
                value=shadow_parts['color'],
                input_type="color",
                on_change=lambda c: self._update_shadow_value(
                    on_change, x=shadow_parts['x'],
                    y=shadow_parts['y'], blur=shadow_parts['blur'],
                    color=c
                )
            ),
            
            # Manual input
            ft.TextField(
                value=value or "",
                label="CSS Value",
                on_change=lambda e: on_change(e.control.value),
                border_radius=6,
                height=40,
                text_size=12,
                border_color="#D1D5DB",
                focused_border_color="#5E6AD2"
            )
        ], spacing=8)
        
        return shadow_controls
    
    def _create_transform_editor(self, label: str, value: str, on_change: Callable[[str], None]) -> ft.Control:
        """
        Create advanced transform editor with visual controls
        
        CLAUDE.md Implementation:
        - #3.1: Interactive transform editing
        - #9.1: Accessible transform controls
        """
        # Parse current transform value
        transforms = self._parse_transform(value or "")
        
        transform_controls = ft.Column([
            ft.Text(label, size=14, weight=ft.FontWeight.W_500, color="#374151"),
            
            # Transform type selector
            ft.RadioGroup(
                content=ft.Row([
                    ft.Radio(value="translate", label="Translate"),
                    ft.Radio(value="rotate", label="Rotate"),
                    ft.Radio(value="scale", label="Scale"),
                    ft.Radio(value="skew", label="Skew")
                ]),
                value=transforms.get('type', 'translate'),
                on_change=lambda e: self._switch_transform_type(e.control.value)
            ),
            
            # Dynamic transform controls based on type
            ft.Container(
                content=self._build_transform_controls(transforms, on_change),
                key="transform_controls"
            ),
            
            # Combined transform display
            ft.TextField(
                value=value or "",
                label="CSS Transform Value",
                on_change=lambda e: on_change(e.control.value),
                border_radius=6,
                height=40,
                text_size=12,
                border_color="#D1D5DB",
                focused_border_color="#5E6AD2"
            )
        ], spacing=8)
        
        return transform_controls
    
    def _parse_shadow(self, shadow_value: str) -> Dict[str, Any]:
        """Parse CSS shadow value into components"""
        try:
            if not shadow_value:
                return {'x': 0, 'y': 0, 'blur': 0, 'color': 'rgba(0,0,0,0.1)'}
            
            # Simple parser for "Xpx Ypx blurpx color" format
            parts = shadow_value.split()
            x = float(parts[0].replace('px', '')) if len(parts) > 0 else 0
            y = float(parts[1].replace('px', '')) if len(parts) > 1 else 0
            blur = float(parts[2].replace('px', '')) if len(parts) > 2 else 0
            color = ' '.join(parts[3:]) if len(parts) > 3 else 'rgba(0,0,0,0.1)'
            
            return {'x': x, 'y': y, 'blur': blur, 'color': color}
        except:
            return {'x': 0, 'y': 0, 'blur': 0, 'color': 'rgba(0,0,0,0.1)'}
    
    def _parse_transform(self, transform_value: str) -> Dict[str, Any]:
        """Parse CSS transform value into components"""
        try:
            if not transform_value:
                return {'type': 'translate', 'values': {}}
            
            # Extract transform functions
            import re
            transforms = {}
            
            # Find translate
            translate_match = re.search(r'translate\(([^)]+)\)', transform_value)
            if translate_match:
                transforms['type'] = 'translate'
                values = translate_match.group(1).split(',')
                transforms['values'] = {
                    'x': values[0].strip() if len(values) > 0 else '0',
                    'y': values[1].strip() if len(values) > 1 else '0'
                }
            
            # Find rotate
            rotate_match = re.search(r'rotate\(([^)]+)\)', transform_value)
            if rotate_match:
                transforms['type'] = 'rotate'
                transforms['values'] = {'angle': rotate_match.group(1).strip()}
            
            # Find scale
            scale_match = re.search(r'scale\(([^)]+)\)', transform_value)
            if scale_match:
                transforms['type'] = 'scale'
                values = scale_match.group(1).split(',')
                transforms['values'] = {
                    'x': values[0].strip() if len(values) > 0 else '1',
                    'y': values[1].strip() if len(values) > 1 else values[0].strip()
                }
            
            return transforms if transforms else {'type': 'translate', 'values': {}}
        except:
            return {'type': 'translate', 'values': {}}
    
    def _update_shadow_value(self, on_change: Callable, x: float, y: float, blur: float, color: str):
        """Update shadow CSS value from components"""
        shadow_value = f"{int(x)}px {int(y)}px {int(blur)}px {color}"
        on_change(shadow_value)
    
    def _build_transform_controls(self, transforms: Dict[str, Any], on_change: Callable) -> ft.Control:
        """Build transform-specific controls"""
        transform_type = transforms.get('type', 'translate')
        values = transforms.get('values', {})
        
        if transform_type == 'translate':
            return ft.Column([
                ft.Row([
                    ft.TextField(
                        label="X",
                        value=values.get('x', '0'),
                        width=150,
                        on_change=lambda e: self._update_transform_value(
                            on_change, 'translate', x=e.control.value, 
                            y=values.get('y', '0')
                        )
                    ),
                    ft.TextField(
                        label="Y",
                        value=values.get('y', '0'),
                        width=150,
                        on_change=lambda e: self._update_transform_value(
                            on_change, 'translate', x=values.get('x', '0'),
                            y=e.control.value
                        )
                    )
                ])
            ])
        elif transform_type == 'rotate':
            return ft.Slider(
                min=-360,
                max=360,
                value=float(values.get('angle', '0').replace('deg', '')),
                label="{value}°",
                width=320,
                on_change=lambda e: on_change(f"rotate({e.control.value}deg)")
            )
        elif transform_type == 'scale':
            return ft.Column([
                ft.Row([
                    ft.TextField(
                        label="Scale X",
                        value=values.get('x', '1'),
                        width=150,
                        on_change=lambda e: self._update_transform_value(
                            on_change, 'scale', x=e.control.value,
                            y=values.get('y', '1')
                        )
                    ),
                    ft.TextField(
                        label="Scale Y",
                        value=values.get('y', '1'),
                        width=150,
                        on_change=lambda e: self._update_transform_value(
                            on_change, 'scale', x=values.get('x', '1'),
                            y=e.control.value
                        )
                    )
                ])
            ])
        else:
            return ft.Text("Transform type not supported yet")
    
    def _update_transform_value(self, on_change: Callable, transform_type: str, **kwargs):
        """Update transform CSS value from components"""
        if transform_type == 'translate':
            x = kwargs.get('x', '0')
            y = kwargs.get('y', '0')
            on_change(f"translate({x}, {y})")
        elif transform_type == 'scale':
            x = kwargs.get('x', '1')
            y = kwargs.get('y', '1')
            on_change(f"scale({x}, {y})")
    
    def _switch_transform_type(self, transform_type: str):
        """Switch between transform types in the editor"""
        # This would update the UI to show different controls
        # Implementation would refresh the transform controls container
        pass
    
    def _create_background_editor(self, label: str, value: str, on_change: Callable[[str], None]) -> ft.Control:
        """
        Create advanced background editor with gradient support
        
        CLAUDE.md Implementation:
        - #3.1: Interactive background/gradient editing
        - #9.1: Accessible background controls
        """
        # Determine if value is a gradient
        is_gradient = value and ('gradient' in value or 'linear-gradient' in value or 'radial-gradient' in value)
        
        background_controls = ft.Column([
            ft.Text(label, size=14, weight=ft.FontWeight.W_500, color="#374151"),
            
            # Type selector
            ft.RadioGroup(
                content=ft.Row([
                    ft.Radio(value="solid", label="Solid Color"),
                    ft.Radio(value="linear", label="Linear Gradient"),
                    ft.Radio(value="radial", label="Radial Gradient")
                ]),
                value="linear" if is_gradient and "linear" in value else "radial" if is_gradient and "radial" in value else "solid",
                on_change=lambda e: self._switch_background_type(e.control.value, on_change)
            ),
            
            # Dynamic background controls
            ft.Container(
                content=self._build_background_controls(value, is_gradient, on_change),
                key="background_controls"
            ),
            
            # Manual CSS input
            ft.TextField(
                value=value or "",
                label="CSS Value",
                on_change=lambda e: on_change(e.control.value),
                border_radius=6,
                height=40,
                text_size=12,
                border_color="#D1D5DB",
                focused_border_color="#5E6AD2"
            )
        ], spacing=8)
        
        return background_controls
    
    def _build_background_controls(self, value: str, is_gradient: bool, on_change: Callable) -> ft.Control:
        """Build background-specific controls"""
        if not is_gradient:
            # Solid color picker
            return PropertyInput(
                label="Color",
                value=value or "#FFFFFF",
                input_type="color",
                on_change=on_change
            )
        else:
            # Gradient controls
            gradient_data = self._parse_gradient(value)
            
            return ft.Column([
                # Gradient stops
                ft.Text("Gradient Stops", size=12, color="#6B7280"),
                ft.Column([
                    self._create_gradient_stop(i, stop, gradient_data, on_change)
                    for i, stop in enumerate(gradient_data.get('stops', []))
                ], spacing=8),
                
                # Add stop button
                ft.TextButton(
                    "Add Color Stop",
                    icon=ft.Icons.ADD,
                    on_click=lambda e: self._add_gradient_stop(gradient_data, on_change)
                ),
                
                # Direction control for linear gradient
                gradient_data.get('type') == 'linear' and ft.Column([
                    ft.Text("Direction", size=12, color="#6B7280"),
                    ft.Slider(
                        min=0,
                        max=360,
                        value=gradient_data.get('angle', 90),
                        label="{value}°",
                        width=320,
                        on_change=lambda e: self._update_gradient_angle(e.control.value, gradient_data, on_change)
                    )
                ]) or ft.Container()
            ], spacing=8)
    
    def _create_gradient_stop(self, index: int, stop: Dict[str, Any], gradient_data: Dict, on_change: Callable) -> ft.Control:
        """Create a gradient stop editor"""
        return ft.Row([
            PropertyInput(
                label="",
                value=stop.get('color', '#000000'),
                input_type="color",
                on_change=lambda c: self._update_gradient_stop(index, 'color', c, gradient_data, on_change)
            ),
            ft.TextField(
                value=str(stop.get('position', 0)),
                label="Position %",
                width=100,
                on_change=lambda e: self._update_gradient_stop(index, 'position', e.control.value, gradient_data, on_change)
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE,
                icon_color="#EF4444",
                tooltip="Remove stop",
                on_click=lambda e: self._remove_gradient_stop(index, gradient_data, on_change)
            )
        ], spacing=8)
    
    def _parse_gradient(self, gradient_value: str) -> Dict[str, Any]:
        """Parse CSS gradient value"""
        try:
            import re
            
            # Default gradient
            if not gradient_value or 'gradient' not in gradient_value:
                return {
                    'type': 'linear',
                    'angle': 90,
                    'stops': [
                        {'color': '#5E6AD2', 'position': 0},
                        {'color': '#3B82F6', 'position': 100}
                    ]
                }
            
            # Parse gradient type and parameters
            gradient_data = {'stops': []}
            
            if 'linear-gradient' in gradient_value:
                gradient_data['type'] = 'linear'
                # Extract angle if present
                angle_match = re.search(r'(\d+)deg', gradient_value)
                if angle_match:
                    gradient_data['angle'] = int(angle_match.group(1))
                else:
                    gradient_data['angle'] = 90
            else:
                gradient_data['type'] = 'radial'
            
            # Extract color stops
            color_pattern = r'(#[0-9a-fA-F]+|rgb[a]?\([^)]+\)|[a-zA-Z]+)\s*(\d+%)?'
            stops = re.findall(color_pattern, gradient_value)
            
            for i, (color, position) in enumerate(stops):
                position_value = int(position.replace('%', '')) if position else (i * 100 // (len(stops) - 1) if len(stops) > 1 else 0)
                gradient_data['stops'].append({
                    'color': color,
                    'position': position_value
                })
            
            return gradient_data
        except:
            return {
                'type': 'linear',
                'angle': 90,
                'stops': [
                    {'color': '#5E6AD2', 'position': 0},
                    {'color': '#3B82F6', 'position': 100}
                ]
            }
    
    def _update_gradient_stop(self, index: int, prop: str, value: Any, gradient_data: Dict, on_change: Callable):
        """Update a gradient stop"""
        if index < len(gradient_data['stops']):
            gradient_data['stops'][index][prop] = value
            on_change(self._build_gradient_css(gradient_data))
    
    def _add_gradient_stop(self, gradient_data: Dict, on_change: Callable):
        """Add a new gradient stop"""
        gradient_data['stops'].append({
            'color': '#000000',
            'position': 50
        })
        on_change(self._build_gradient_css(gradient_data))
    
    def _remove_gradient_stop(self, index: int, gradient_data: Dict, on_change: Callable):
        """Remove a gradient stop"""
        if len(gradient_data['stops']) > 2:  # Keep at least 2 stops
            gradient_data['stops'].pop(index)
            on_change(self._build_gradient_css(gradient_data))
    
    def _update_gradient_angle(self, angle: float, gradient_data: Dict, on_change: Callable):
        """Update gradient angle"""
        gradient_data['angle'] = angle
        on_change(self._build_gradient_css(gradient_data))
    
    def _build_gradient_css(self, gradient_data: Dict) -> str:
        """Build CSS gradient string from data"""
        stops = ' '.join([f"{stop['color']} {stop['position']}%" for stop in gradient_data['stops']])
        
        if gradient_data['type'] == 'linear':
            return f"linear-gradient({gradient_data['angle']}deg, {stops})"
        else:
            return f"radial-gradient(circle, {stops})"
    
    def _switch_background_type(self, bg_type: str, on_change: Callable):
        """Switch between background types"""
        if bg_type == 'solid':
            on_change('#FFFFFF')
        else:
            # Default gradient
            default_gradient = self._build_gradient_css({
                'type': 'linear' if bg_type == 'linear' else 'radial',
                'angle': 90,
                'stops': [
                    {'color': '#5E6AD2', 'position': 0},
                    {'color': '#3B82F6', 'position': 100}
                ]
            })
            on_change(default_gradient)
    
    def set_component_data(self, component_data: Dict[str, Any]):
        """
        Set component data from state management system
        
        CLAUDE.md Implementation:
        - #6.2: State-driven property editing
        - #4.1: Type-safe data handling
        """
        try:
            if not component_data:
                self.current_component = None
                self.content = self._build_content()
                self.update()
                return
            
            # Convert dict data to Component object if needed
            if isinstance(component_data, dict):
                from models.component import Component
                
                # Handle both single component and component with metadata
                if 'component' in component_data:
                    # Data has wrapper with component field
                    comp_data = component_data['component']
                else:
                    # Data is the component itself
                    comp_data = component_data
                
                # Create Component object from data
                if isinstance(comp_data, dict):
                    # Ensure required fields exist
                    comp_data.setdefault('id', '')
                    comp_data.setdefault('type', 'container')
                    comp_data.setdefault('name', 'Component')
                    
                    component = Component(**comp_data)
                else:
                    component = comp_data
                
                self.set_component(component)
            elif hasattr(component_data, 'id'):
                # Already a Component object
                self.set_component(component_data)
            else:
                # Unknown data format
                self.current_component = None
                self.content = self._build_content()
                self.update()
                
        except Exception as e:
            print(f"Error setting component data: {e}")
            # Ensure properties panel doesn't break
            self.current_component = None
            self.content = self._build_content()
            self.update()