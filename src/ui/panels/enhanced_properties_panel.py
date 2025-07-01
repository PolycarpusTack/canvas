"""
Enhanced Properties Panel
Professional property editor with search, filtering, and advanced inputs
Following CLAUDE.md guidelines for enterprise-grade UI components
"""

import flet as ft
from typing import Optional, Dict, Any, Callable, List, Set
from collections import defaultdict
import logging

from components.property_definitions import (
    PropertyDefinition, PropertyType, PropertyCategory, ValidationResult
)
from components.property_registry import get_registry
from models.component import Component
from inputs.property_input_base import create_property_input
from inputs.color_picker import create_color_property_input
from inputs.spacing_input import create_spacing_property_input, create_border_property_input

logger = logging.getLogger(__name__)


class PropertySearchFilter(ft.Container):
    """Search and filter controls for properties"""
    
    def __init__(self, on_search: Callable[[str], None], on_filter: Callable[[List[str]], None]):
        super().__init__()
        self.on_search = on_search
        self.on_filter = on_filter
        self.selected_categories: Set[str] = set()
        
        self.content = self._build_content()
    
    def _build_content(self) -> ft.Control:
        """Build search and filter UI"""
        # Search field
        self.search_field = ft.TextField(
            hint_text="Search properties...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=lambda e: self.on_search(e.control.value),
            border_radius=8,
            height=40,
            text_size=14,
            border_color="#E5E7EB",
            focused_border_color="#5E6AD2"
        )
        
        # Category filter chips
        category_chips = []
        for category in PropertyCategory:
            chip = ft.FilterChip(
                label=ft.Text(category.display_name, size=12),
                leading=ft.Icon(category.icon, size=16),
                selected=False,
                on_select=lambda e, cat=category.name: self._on_category_filter(cat, e.control.selected),
                show_checkmark=False,
                bgcolor="#F9FAFB",
                selected_color="#E0E7FF",
                selected_border_color="#5E6AD2"
            )
            category_chips.append(chip)
        
        # Filter row with chips
        filter_row = ft.Row(
            controls=category_chips,
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            height=40
        )
        
        return ft.Column([
            self.search_field,
            ft.Container(
                content=filter_row,
                padding=ft.padding.symmetric(vertical=8)
            )
        ], spacing=8)
    
    def _on_category_filter(self, category: str, selected: bool) -> None:
        """Handle category filter selection"""
        if selected:
            self.selected_categories.add(category)
        else:
            self.selected_categories.discard(category)
        
        self.on_filter(list(self.selected_categories))


class PropertyGroup(ft.Container):
    """Group of related properties with collapsible header"""
    
    def __init__(
        self,
        category: PropertyCategory,
        properties: List[PropertyDefinition],
        property_values: Dict[str, Any],
        on_property_change: Callable[[str, Any], None],
        component_id: Optional[str] = None,
        collapsed: bool = False
    ):
        super().__init__()
        self.category = category
        self.properties = properties
        self.property_values = property_values
        self.on_property_change = on_property_change
        self.component_id = component_id
        self.collapsed = collapsed
        self.property_inputs: Dict[str, Any] = {}
        
        self.content = self._build_content()
    
    def _build_content(self) -> ft.Control:
        """Build the property group UI"""
        if not self.properties:
            return ft.Container()
        
        # Group header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(
                    self.category.icon,
                    size=16,
                    color="#5E6AD2"
                ),
                ft.Text(
                    self.category.display_name,
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color="#374151"
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.EXPAND_LESS if not self.collapsed else ft.Icons.EXPAND_MORE,
                    icon_size=16,
                    on_click=lambda e: self._toggle_collapsed(),
                    tooltip="Collapse/Expand"
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor="#F9FAFB",
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border=ft.border.all(1, "#E5E7EB"),
            on_click=lambda e: self._toggle_collapsed()
        )
        
        # Property inputs
        property_controls = []
        if not self.collapsed:
            for prop_def in self.properties:
                if self._should_show_property(prop_def):
                    input_control = self._create_property_input(prop_def)
                    if input_control:
                        property_controls.append(input_control)
        
        properties_container = ft.Column(
            controls=property_controls,
            spacing=12,
            visible=not self.collapsed
        )
        
        return ft.Column([
            header,
            ft.Container(
                content=properties_container,
                padding=ft.padding.only(left=12, right=12, bottom=12, top=4)
            )
        ], spacing=0)
    
    def _should_show_property(self, prop_def: PropertyDefinition) -> bool:
        """Check if property should be shown based on dependencies"""
        if not prop_def.dependencies:
            return prop_def.visible
        
        states = prop_def.evaluate_dependencies(self.property_values)
        return states.get("visible", True) and prop_def.visible
    
    def _create_property_input(self, prop_def: PropertyDefinition) -> Optional[ft.Control]:
        """Create appropriate input for property type"""
        current_value = self.property_values.get(prop_def.name, prop_def.default_value)
        
        # Factory function mapping
        if prop_def.type == PropertyType.COLOR:
            input_control = create_color_property_input(
                prop_def, current_value, self._on_input_change, component_id=self.component_id
            )
        elif prop_def.type == PropertyType.SPACING:
            input_control = create_spacing_property_input(
                prop_def, current_value, self._on_input_change, component_id=self.component_id
            )
        elif prop_def.type == PropertyType.BORDER:
            input_control = create_border_property_input(
                prop_def, current_value, self._on_input_change, component_id=self.component_id
            )
        else:
            input_control = create_property_input(
                prop_def, current_value, self._on_input_change, component_id=self.component_id
            )
        
        if input_control:
            self.property_inputs[prop_def.name] = input_control
            return input_control
        
        return None
    
    def _on_input_change(self, property_name: str, value: Any) -> None:
        """Handle property value change"""
        self.property_values[property_name] = value
        self.on_property_change(property_name, value)
        
        # Update visibility of other properties based on dependencies
        self._update_property_visibility()
    
    def _update_property_visibility(self) -> None:
        """Update property visibility based on current values"""
        for prop_def in self.properties:
            if prop_def.dependencies:
                states = prop_def.evaluate_dependencies(self.property_values)
                input_control = self.property_inputs.get(prop_def.name)
                if input_control:
                    input_control.set_visible(states.get("visible", True))
                    input_control.set_enabled(states.get("enabled", True))
    
    def _toggle_collapsed(self) -> None:
        """Toggle collapsed state"""
        self.collapsed = not self.collapsed
        self.content = self._build_content()
        self.update()
    
    def update_property_values(self, property_values: Dict[str, Any]) -> None:
        """Update property values from external source"""
        self.property_values = property_values
        
        # Update individual inputs
        for prop_name, input_control in self.property_inputs.items():
            new_value = property_values.get(prop_name)
            if new_value is not None:
                input_control.set_value(new_value, validate=False)


class ResponsiveBreakpointSelector(ft.Container):
    """Selector for responsive breakpoints"""
    
    BREAKPOINTS = [
        ("base", "Base", ft.Icons.DEVICES),
        ("sm", "SM", ft.Icons.PHONE_ANDROID),
        ("md", "MD", ft.Icons.TABLET_MAC),
        ("lg", "LG", ft.Icons.LAPTOP_MAC),
        ("xl", "XL", ft.Icons.DESKTOP_MAC)
    ]
    
    def __init__(self, current_breakpoint: str = "base", on_breakpoint_change: Callable[[str], None] = None):
        super().__init__()
        self.current_breakpoint = current_breakpoint
        self.on_breakpoint_change = on_breakpoint_change
        
        self.content = self._build_content()
    
    def _build_content(self) -> ft.Control:
        """Build breakpoint selector"""
        chips = []
        for bp_key, bp_label, bp_icon in self.BREAKPOINTS:
            chip = ft.FilterChip(
                label=ft.Text(bp_label, size=12),
                leading=ft.Icon(bp_icon, size=16),
                selected=bp_key == self.current_breakpoint,
                on_select=lambda e, key=bp_key: self._on_breakpoint_select(key),
                show_checkmark=False,
                bgcolor="#F9FAFB",
                selected_color="#E0E7FF",
                selected_border_color="#5E6AD2"
            )
            chips.append(chip)
        
        return ft.Column([
            ft.Text("Responsive Breakpoint", size=14, weight=ft.FontWeight.W_500),
            ft.Row(chips, spacing=4, scroll=ft.ScrollMode.AUTO)
        ], spacing=8)
    
    def _on_breakpoint_select(self, breakpoint: str) -> None:
        """Handle breakpoint selection"""
        if self.current_breakpoint != breakpoint:
            self.current_breakpoint = breakpoint
            if self.on_breakpoint_change:
                self.on_breakpoint_change(breakpoint)
            self._update_selection()
    
    def _update_selection(self) -> None:
        """Update chip selection state"""
        # In a full implementation, you'd update the chip states
        self.update()


class EnhancedPropertiesPanel(ft.Container):
    """
    Professional properties panel with advanced features
    CLAUDE.md #1.1: Enterprise-grade UI organization
    CLAUDE.md #12.5: Performance with many properties
    """
    
    def __init__(self, on_property_change: Callable[[str, str, Any], None]):
        super().__init__()
        self.on_property_change = on_property_change
        self.current_component: Optional[Component] = None
        self.current_component_id: Optional[str] = None
        self.current_breakpoint = "base"
        self.property_groups: Dict[PropertyCategory, PropertyGroup] = {}
        self.filtered_properties: List[PropertyDefinition] = []
        self.search_query = ""
        self.selected_categories: Set[str] = set()
        
        # Registry reference
        self.registry = get_registry()
        
        # Set container properties
        self.bgcolor = "#FFFFFF"
        self.border = ft.border.only(left=ft.BorderSide(1, "#E5E7EB"))
        self.padding = 20
        self.expand = True
        
        # Build initial content
        self.content = self._build_empty_state()
    
    def _build_empty_state(self) -> ft.Control:
        """Build empty state when no component is selected"""
        return ft.Column([
            ft.Text(
                "Properties",
                size=20,
                weight=ft.FontWeight.BOLD,
                color="#1F2937"
            ),
            ft.Container(
                content=ft.Column([
                    ft.Icon(
                        ft.Icons.TUNE_ROUNDED,
                        size=64,
                        color="#9CA3AF"
                    ),
                    ft.Text(
                        "Select a component to edit properties",
                        size=16,
                        color="#6B7280",
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        "Advanced property editor with search, validation, and responsive support",
                        size=14,
                        color="#9CA3AF",
                        text_align=ft.TextAlign.CENTER
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                padding=ft.padding.symmetric(vertical=60),
                alignment=ft.alignment.center,
                expand=True
            )
        ], spacing=24, expand=True)
    
    def set_component(self, component: Optional[Component]) -> None:
        """Set the component to edit"""
        if component:
            self.current_component = component
            self.current_component_id = component.id
            self.content = self._build_property_editor(component)
        else:
            self.current_component = None
            self.current_component_id = None
            self.content = self._build_empty_state()
        self.update()
    
    def set_component_data(self, component_data: Dict[str, Any]) -> None:
        """Set component from raw data"""
        if component_data:
            # Create a component-like object
            class ComponentData:
                def __init__(self, data):
                    self.id = data.get('id', '')
                    self.type = data.get('type', '')
                    self.name = data.get('name', '')
                    self.properties = data.get('properties', {})
            
            component = ComponentData(component_data)
            self.current_component = component
            self.current_component_id = component.id
            self.content = self._build_property_editor(component)
        else:
            self.current_component = None
            self.current_component_id = None
            self.content = self._build_empty_state()
        self.update()
    
    def _build_property_editor(self, component) -> ft.Control:
        """Build the property editor interface"""
        # Get properties for component type
        properties = self.registry.get_component_properties(component.type)
        
        if not properties:
            return self._build_no_properties_state(component)
        
        # Component header
        header = self._build_component_header(component)
        
        # Search and filter
        search_filter = PropertySearchFilter(
            on_search=self._on_search,
            on_filter=self._on_filter
        )
        
        # Responsive breakpoint selector
        breakpoint_selector = ResponsiveBreakpointSelector(
            current_breakpoint=self.current_breakpoint,
            on_breakpoint_change=self._on_breakpoint_change
        )
        
        # Property groups
        self._build_property_groups(properties, component)
        
        # Properties list with virtual scrolling for performance
        properties_list = ft.ListView(
            controls=list(self.property_groups.values()),
            spacing=16,
            expand=True,
            auto_scroll=False
        )
        
        # Validation summary
        validation_summary = self._build_validation_summary()
        
        return ft.Column([
            header,
            ft.Divider(height=1, color="#E5E7EB"),
            search_filter,
            ft.Divider(height=1, color="#E5E7EB"),
            breakpoint_selector,
            ft.Divider(height=1, color="#E5E7EB"),
            properties_list,
            validation_summary
        ], spacing=0, expand=True)
    
    def _build_component_header(self, component) -> ft.Control:
        """Build component header with info"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    self._get_component_icon(component.type),
                    size=24,
                    color="#5E6AD2"
                ),
                ft.Column([
                    ft.Text(
                        f"{component.name or component.type}",
                        size=18,
                        weight=ft.FontWeight.W_600,
                        color="#1F2937"
                    ),
                    ft.Text(
                        f"Type: {component.type} • ID: {component.id}",
                        size=12,
                        color="#6B7280"
                    )
                ], spacing=2, alignment=ft.MainAxisAlignment.START),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Reset all properties",
                    on_click=lambda e: self._reset_all_properties()
                )
            ], alignment=ft.MainAxisAlignment.START),
            padding=ft.padding.symmetric(vertical=12)
        )
    
    def _build_no_properties_state(self, component) -> ft.Control:
        """Build state when component has no editable properties"""
        return ft.Column([
            self._build_component_header(component),
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.SETTINGS_OUTLINED, size=48, color="#9CA3AF"),
                    ft.Text(
                        "No editable properties",
                        size=16,
                        color="#6B7280",
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        f"The {component.type} component doesn't have configurable properties.",
                        size=14,
                        color="#9CA3AF",
                        text_align=ft.TextAlign.CENTER
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                padding=ft.padding.symmetric(vertical=40),
                alignment=ft.alignment.center,
                expand=True
            )
        ], spacing=16, expand=True)
    
    def _build_property_groups(self, properties: List[PropertyDefinition], component) -> None:
        """Build property groups organized by category"""
        # Group properties by category
        grouped_properties = defaultdict(list)
        for prop in properties:
            if self._matches_search_and_filter(prop):
                grouped_properties[prop.category].append(prop)
        
        # Get current property values
        property_values = getattr(component, 'properties', {})
        
        # Create property group components
        self.property_groups.clear()
        for category, props in grouped_properties.items():
            if props:  # Only create groups with properties
                group = PropertyGroup(
                    category=category,
                    properties=props,
                    property_values=property_values,
                    on_property_change=self._on_property_change,
                    component_id=component.id,
                    collapsed=category in [PropertyCategory.ADVANCED]  # Collapse advanced by default
                )
                self.property_groups[category] = group
    
    def _build_validation_summary(self) -> ft.Control:
        """Build validation summary"""
        if not self.current_component:
            return ft.Container()
        
        # Get validation results for all properties
        validation_results = []
        if hasattr(self.current_component, 'properties'):
            result = self.registry.validate_all_properties(
                self.current_component.type,
                self.current_component.properties
            )
            
            if not result.is_valid:
                error_summary = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=16, color="#EF4444"),
                        ft.Text(
                            f"{len(result.errors)} validation error(s)",
                            size=12,
                            color="#EF4444"
                        )
                    ], spacing=4),
                    bgcolor="#FEF2F2",
                    border=ft.border.all(1, "#FECACA"),
                    border_radius=4,
                    padding=8
                )
                return error_summary
        
        return ft.Container()
    
    def _matches_search_and_filter(self, prop_def: PropertyDefinition) -> bool:
        """Check if property matches current search and filter criteria"""
        # Search filter
        if self.search_query:
            query_lower = self.search_query.lower()
            if not any([
                query_lower in prop_def.name.lower(),
                query_lower in prop_def.label.lower(),
                query_lower in prop_def.description.lower(),
                any(query_lower in tag.lower() for tag in prop_def.tags),
                any(query_lower in kw.lower() for kw in prop_def.search_keywords)
            ]):
                return False
        
        # Category filter
        if self.selected_categories and prop_def.category.name not in self.selected_categories:
            return False
        
        return True
    
    def _on_search(self, query: str) -> None:
        """Handle search query change"""
        self.search_query = query
        self._refresh_properties()
    
    def _on_filter(self, categories: List[str]) -> None:
        """Handle category filter change"""
        self.selected_categories = set(categories)
        self._refresh_properties()
    
    def _on_breakpoint_change(self, breakpoint: str) -> None:
        """Handle responsive breakpoint change"""
        self.current_breakpoint = breakpoint
        # In a full implementation, you'd update property values for the new breakpoint
        logger.info(f"Breakpoint changed to: {breakpoint}")
    
    def _on_property_change(self, property_name: str, value: Any) -> None:
        """Handle property value change"""
        if self.current_component and self.on_property_change:
            # Update component properties
            if not hasattr(self.current_component, 'properties'):
                self.current_component.properties = {}
            self.current_component.properties[property_name] = value
            
            # Notify parent
            self.on_property_change(self.current_component_id, property_name, value)
    
    def _refresh_properties(self) -> None:
        """Refresh property display based on current filters"""
        if self.current_component:
            properties = self.registry.get_component_properties(self.current_component.type)
            self._build_property_groups(properties, self.current_component)
            
            # Update properties list
            if hasattr(self, 'content') and self.content:
                # In a full implementation, you'd update the ListView controls
                pass
    
    def _reset_all_properties(self) -> None:
        """Reset all properties to default values"""
        if not self.current_component:
            return
        
        properties = self.registry.get_component_properties(self.current_component.type)
        for prop_def in properties:
            if hasattr(self.current_component, 'properties'):
                self.current_component.properties[prop_def.name] = prop_def.default_value
                self._on_property_change(prop_def.name, prop_def.default_value)
        
        # Update all property groups
        for group in self.property_groups.values():
            group.update_property_values(self.current_component.properties)
    
    def _get_component_icon(self, component_type: str) -> str:
        """Get icon for component type"""
        icons = {
            "text": ft.Icons.TEXT_FIELDS,
            "button": ft.Icons.SMART_BUTTON,
            "image": ft.Icons.IMAGE,
            "container": ft.Icons.SQUARE_OUTLINED,
            "div": ft.Icons.CROP_SQUARE,
            "row": ft.Icons.VIEW_COLUMN,
            "column": ft.Icons.VIEW_STREAM,
            "form": ft.Icons.DYNAMIC_FORM,
            "input": ft.Icons.INPUT,
            "heading": ft.Icons.TITLE,
            "paragraph": ft.Icons.NOTES
        }
        return icons.get(component_type, ft.Icons.WIDGETS)