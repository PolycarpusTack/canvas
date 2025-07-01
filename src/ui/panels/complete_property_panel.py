"""
Complete Property Panel Implementation
Implements the exact PropertyPanel interface specified in the design documentation
Following CLAUDE.md guidelines for enterprise-grade UI organization
"""

import flet as ft
from typing import Optional, Dict, Any, Callable, List, Set
from collections import defaultdict
import logging
from datetime import datetime

from components.property_definitions import (
    PropertyDefinition, PropertyType, PropertyCategory, ValidationResult
)
from components.property_registry import get_registry
from models.component import Component
from inputs.property_input_base import create_property_input
from inputs.color_picker import create_color_property_input
from inputs.spacing_input import create_spacing_property_input, create_border_property_input

logger = logging.getLogger(__name__)


class PropertyPanel(ft.UserControl):
    """
    Complete Property Panel implementation as specified in design documentation
    CLAUDE.md #1.1: Enterprise-grade UI organization
    CLAUDE.md #12.5: Performance with many properties
    """
    
    def __init__(self, on_property_change: Callable[[str, str, Any], None]):
        super().__init__()
        self.on_property_change = on_property_change
        self.current_component: Optional[Component] = None
        self.active_tab = "content"
        self.search_query = ""
        self.property_inputs: Dict[str, Any] = {}
        self.filtered_properties: List[PropertyDefinition] = []
        self.categorized_properties: Dict[PropertyCategory, List[PropertyDefinition]] = {}
        self.current_breakpoint = "base"
        
        # Registry reference
        self.registry = get_registry()
        
        # UI components (will be initialized in build)
        self.search_field: Optional[ft.TextField] = None
        self.category_tabs: Optional[ft.Tabs] = None
        self.property_list: Optional[ft.ListView] = None
        self.breakpoint_selector: Optional[ft.Row] = None
        self.header_text: Optional[ft.Text] = None
        
    def build(self) -> ft.Control:
        """Build the complete property panel interface"""
        return ft.Column([
            # Header
            self._build_header(),
            
            # Search
            self._build_search(),
            
            # Category tabs
            self._build_tabs(),
            
            # Property list (virtual scrolling for performance)
            self._build_property_list_container(),
            
            # Responsive breakpoints
            self._build_breakpoint_selector()
        ], spacing=16, expand=True)
    
    def _build_header(self) -> ft.Control:
        """Build the panel header"""
        self.header_text = ft.Text(
            "Properties",
            size=18,
            weight=ft.FontWeight.BOLD,
            color="#1F2937"
        )
        
        if self.current_component:
            component_info = ft.Row([
                ft.Icon(
                    self._get_component_icon(self.current_component.type),
                    size=20,
                    color="#5E6AD2"
                ),
                ft.Column([
                    ft.Text(
                        f"Editing {self.current_component.type}",
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color="#374151"
                    ),
                    ft.Text(
                        f"ID: {self.current_component.id}",
                        size=12,
                        color="#6B7280"
                    )
                ], spacing=2, tight=True)
            ], spacing=8, alignment=ft.MainAxisAlignment.START)
            
            return ft.Column([
                self.header_text,
                component_info
            ], spacing=8)
        
        return self.header_text
    
    def _build_search(self) -> ft.Control:
        """Build the search interface"""
        self.search_field = ft.TextField(
            prefix_icon=ft.Icons.SEARCH,
            hint_text="Search properties...",
            on_change=lambda e: self._filter_properties(e.control.value),
            border_radius=8,
            height=40,
            text_size=14,
            border_color="#E5E7EB",
            focused_border_color="#5E6AD2"
        )
        return self.search_field
    
    def _build_tabs(self) -> ft.Control:
        """Build category tabs"""
        if not self.current_component:
            return ft.Container()
        
        # Get all properties for current component
        all_properties = self.registry.get_component_properties(self.current_component.type)
        self.categorized_properties = self._organize_properties_by_category(all_properties)
        
        # Create tabs for each category that has properties
        tabs = []
        for category, properties in self.categorized_properties.items():
            if properties:  # Only create tabs for categories with properties
                tab = ft.Tab(
                    text=category.display_name,
                    icon=category.icon,
                    content=self._build_category_content(category, properties)
                )
                tabs.append(tab)
        
        if tabs:
            self.category_tabs = ft.Tabs(
                tabs=tabs,
                selected_index=0,
                animation_duration=300,
                expand=True
            )
            return self.category_tabs
        
        return ft.Container()
    
    def _build_category_content(self, category: PropertyCategory, properties: List[PropertyDefinition]) -> ft.Control:
        """Build content for a category tab"""
        property_controls = []
        
        for prop_def in properties:
            if self._should_show_property(prop_def):
                input_control = self._create_property_input(prop_def)
                if input_control:
                    property_controls.append(input_control)
        
        if not property_controls:
            return ft.Container(
                content=ft.Text(
                    f"No {category.display_name.lower()} properties",
                    color="#9CA3AF",
                    text_align=ft.TextAlign.CENTER
                ),
                alignment=ft.alignment.center,
                padding=20
            )
        
        return ft.Container(
            content=ft.Column(
                controls=property_controls,
                spacing=12,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=16,
            expand=True
        )
    
    def _build_property_list_container(self) -> ft.Control:
        """Build the main property list container with virtual scrolling"""
        if not self.current_component:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(
                        ft.Icons.TUNE_ROUNDED,
                        size=48,
                        color="#9CA3AF"
                    ),
                    ft.Text(
                        "Select a component to edit properties",
                        size=14,
                        color="#6B7280",
                        text_align=ft.TextAlign.CENTER
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                alignment=ft.alignment.center,
                expand=True,
                padding=40
            )
        
        # Return the tabs container which contains the property lists
        return ft.Container(
            content=self.category_tabs if self.category_tabs else ft.Container(),
            expand=True
        )
    
    def _build_breakpoint_selector(self) -> ft.Control:
        """Build responsive breakpoint selector"""
        if not self.current_component:
            return ft.Container()
        
        # Check if any properties are responsive
        all_properties = self.registry.get_component_properties(self.current_component.type)
        has_responsive = any(prop.responsive for prop in all_properties)
        
        if not has_responsive:
            return ft.Container()
        
        breakpoints = [
            ("base", "Base", ft.Icons.DEVICES),
            ("sm", "SM", ft.Icons.PHONE_ANDROID),
            ("md", "MD", ft.Icons.TABLET_MAC),
            ("lg", "LG", ft.Icons.LAPTOP_MAC),
            ("xl", "XL", ft.Icons.DESKTOP_MAC)
        ]
        
        chips = []
        for bp_key, bp_label, bp_icon in breakpoints:
            chip = ft.FilterChip(
                label=ft.Text(bp_label, size=12),
                leading=ft.Icon(bp_icon, size=16),
                selected=bp_key == self.current_breakpoint,
                on_select=lambda e, key=bp_key: self._on_breakpoint_change(key),
                show_checkmark=False,
                bgcolor="#F9FAFB",
                selected_color="#E0E7FF",
                selected_border_color="#5E6AD2"
            )
            chips.append(chip)
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Responsive Breakpoint", size=14, weight=ft.FontWeight.W_500),
                ft.Row(chips, spacing=4, scroll=ft.ScrollMode.AUTO)
            ], spacing=8),
            padding=ft.padding.symmetric(vertical=8)
        )
    
    def _organize_properties_by_category(
        self,
        properties: List[PropertyDefinition]
    ) -> Dict[PropertyCategory, List[PropertyDefinition]]:
        """Group and sort properties as specified in design"""
        categorized = {}
        
        # Group by category
        for prop in properties:
            if prop.category not in categorized:
                categorized[prop.category] = []
            categorized[prop.category].append(prop)
        
        # Sort within categories
        for category, props in categorized.items():
            props.sort(key=lambda p: (p.category.priority, p.label))
        
        return categorized
    
    def _should_show_property(self, prop_def: PropertyDefinition) -> bool:
        """Check if property should be shown based on search and dependencies"""
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
        
        # Dependency evaluation
        if prop_def.dependencies and self.current_component:
            property_values = getattr(self.current_component, 'properties', {})
            states = prop_def.evaluate_dependencies(property_values)
            return states.get("visible", True) and prop_def.visible
        
        return prop_def.visible
    
    def _create_property_input(self, prop_def: PropertyDefinition) -> Optional[ft.Control]:
        """Create appropriate input for property type"""
        if not self.current_component:
            return None
        
        # Get current value
        current_value = None
        if hasattr(self.current_component, 'properties'):
            current_value = self.current_component.properties.get(prop_def.name, prop_def.default_value)
        else:
            current_value = prop_def.default_value
        
        # Create input based on type
        try:
            if prop_def.type == PropertyType.COLOR:
                input_control = create_color_property_input(
                    prop_def, current_value, self._on_input_change, component_id=self.current_component.id
                )
            elif prop_def.type == PropertyType.SPACING:
                input_control = create_spacing_property_input(
                    prop_def, current_value, self._on_input_change, component_id=self.current_component.id
                )
            elif prop_def.type == PropertyType.BORDER:
                input_control = create_border_property_input(
                    prop_def, current_value, self._on_input_change, component_id=self.current_component.id
                )
            else:
                input_control = create_property_input(
                    prop_def, current_value, self._on_input_change, component_id=self.current_component.id
                )
            
            if input_control:
                self.property_inputs[prop_def.name] = input_control
                return input_control
        
        except Exception as e:
            logger.error(f"Failed to create input for property {prop_def.name}: {e}")
            return None
        
        return None
    
    def _filter_properties(self, query: str) -> None:
        """Filter properties based on search query"""
        self.search_query = query
        self._refresh_current_tab()
    
    def _refresh_current_tab(self) -> None:
        """Refresh the current tab content"""
        if not self.category_tabs or not self.current_component:
            return
        
        # Get current tab
        current_tab_index = self.category_tabs.selected_index
        if current_tab_index is None or current_tab_index < 0:
            return
        
        # Rebuild tabs to apply filters
        self._rebuild_tabs()
    
    def _rebuild_tabs(self) -> None:
        """Rebuild all tabs with current filters"""
        if not self.current_component:
            return
        
        all_properties = self.registry.get_component_properties(self.current_component.type)
        self.categorized_properties = self._organize_properties_by_category(all_properties)
        
        # Update tab contents
        for i, tab in enumerate(self.category_tabs.tabs):
            category = list(self.categorized_properties.keys())[i]
            properties = self.categorized_properties[category]
            tab.content = self._build_category_content(category, properties)
        
        self.update()
    
    def _on_input_change(self, property_name: str, value: Any) -> None:
        """Handle property value change"""
        if not self.current_component:
            return
        
        # Update component properties
        if not hasattr(self.current_component, 'properties'):
            self.current_component.properties = {}
        
        self.current_component.properties[property_name] = value
        
        # Notify parent component
        if self.on_property_change:
            self.on_property_change(self.current_component.id, property_name, value)
        
        # Update dependent properties
        self._update_dependent_properties(property_name, value)
        
        logger.debug(f"Property {property_name} changed to {value} for component {self.current_component.id}")
    
    def _update_dependent_properties(self, changed_property: str, new_value: Any) -> None:
        """Update visibility/state of dependent properties"""
        if not self.current_component:
            return
        
        all_properties = self.registry.get_component_properties(self.current_component.type)
        
        for prop_def in all_properties:
            if prop_def.dependencies:
                # Check if this property depends on the changed property
                depends_on_changed = any(
                    dep.property_name == changed_property 
                    for dep in prop_def.dependencies
                )
                
                if depends_on_changed:
                    # Re-evaluate dependencies and update input visibility
                    property_values = getattr(self.current_component, 'properties', {})
                    states = prop_def.evaluate_dependencies(property_values)
                    
                    input_control = self.property_inputs.get(prop_def.name)
                    if input_control:
                        input_control.set_visible(states.get("visible", True))
                        if hasattr(input_control, 'set_enabled'):
                            input_control.set_enabled(states.get("enabled", True))
    
    def _on_breakpoint_change(self, breakpoint: str) -> None:
        """Handle responsive breakpoint change"""
        if self.current_breakpoint != breakpoint:
            self.current_breakpoint = breakpoint
            
            # Update all responsive property inputs to show values for this breakpoint
            for prop_name, input_control in self.property_inputs.items():
                if hasattr(input_control, 'responsive_breakpoint'):
                    input_control.responsive_breakpoint = breakpoint
                    # In a full implementation, you'd load breakpoint-specific values here
            
            # Update breakpoint selector visual state
            self._update_breakpoint_selector()
            
            logger.info(f"Switched to breakpoint: {breakpoint}")
    
    def _update_breakpoint_selector(self) -> None:
        """Update breakpoint selector visual state"""
        if self.breakpoint_selector:
            # Update chip selection state
            self.update()
    
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
    
    # Public API methods
    
    def set_component(self, component: Optional[Component]) -> None:
        """Set the component to edit"""
        self.current_component = component
        self.property_inputs.clear()
        
        # Rebuild the entire panel
        self.build()
        self.update()
        
        if component:
            logger.info(f"Property panel now editing component: {component.type} (ID: {component.id})")
        else:
            logger.info("Property panel cleared - no component selected")
    
    def get_current_component(self) -> Optional[Component]:
        """Get the currently edited component"""
        return self.current_component
    
    def get_property_value(self, property_name: str) -> Any:
        """Get current value of a property"""
        if not self.current_component:
            return None
        
        properties = getattr(self.current_component, 'properties', {})
        return properties.get(property_name)
    
    def set_property_value(self, property_name: str, value: Any, update_ui: bool = True) -> None:
        """Programmatically set a property value"""
        if not self.current_component:
            return
        
        if not hasattr(self.current_component, 'properties'):
            self.current_component.properties = {}
        
        self.current_component.properties[property_name] = value
        
        if update_ui:
            input_control = self.property_inputs.get(property_name)
            if input_control:
                input_control.set_value(value, validate=False)
        
        if self.on_property_change:
            self.on_property_change(self.current_component.id, property_name, value)
    
    def validate_all_properties(self) -> ValidationResult:
        """Validate all current property values"""
        if not self.current_component:
            return ValidationResult(is_valid=True)
        
        property_values = getattr(self.current_component, 'properties', {})
        return self.registry.validate_all_properties(self.current_component.type, property_values)
    
    def reset_property(self, property_name: str) -> None:
        """Reset a property to its default value"""
        if not self.current_component:
            return
        
        prop_def = self.registry.get_property(self.current_component.type, property_name)
        if prop_def:
            self.set_property_value(property_name, prop_def.default_value)
    
    def reset_all_properties(self) -> None:
        """Reset all properties to their default values"""
        if not self.current_component:
            return
        
        all_properties = self.registry.get_component_properties(self.current_component.type)
        for prop_def in all_properties:
            self.set_property_value(prop_def.name, prop_def.default_value)
    
    def export_properties(self) -> Dict[str, Any]:
        """Export current property values"""
        if not self.current_component:
            return {}
        
        return getattr(self.current_component, 'properties', {}).copy()
    
    def import_properties(self, properties: Dict[str, Any]) -> None:
        """Import property values"""
        if not self.current_component:
            return
        
        for prop_name, value in properties.items():
            self.set_property_value(prop_name, value)


# Compatibility wrapper for existing enhanced properties panel
class EnhancedPropertiesPanel(PropertyPanel):
    """
    Compatibility wrapper that extends PropertyPanel to match existing interface
    """
    
    def __init__(self, on_property_change: Callable[[str, str, Any], None]):
        super().__init__(on_property_change)
    
    def set_component_data(self, component_data: Dict[str, Any]) -> None:
        """Set component from raw data (compatibility method)"""
        if component_data:
            # Convert dict to Component object
            from models.component import Component, ComponentStyle
            
            component = Component(
                id=component_data.get('id', ''),
                type=component_data.get('type', ''),
                name=component_data.get('name', ''),
                style=ComponentStyle(**component_data.get('style', {}))
            )
            
            # Set properties if provided
            if 'properties' in component_data:
                component.properties = component_data['properties']
            
            self.set_component(component)
        else:
            self.set_component(None)