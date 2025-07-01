"""
Virtual Property List Component
High-performance virtual scrolling for property lists with conditional visibility
Following CLAUDE.md guidelines for performance optimization
"""

import flet as ft
from typing import List, Dict, Any, Callable, Optional, Set
import math
import logging

from ...components.property_definitions import PropertyDefinition, PropertyCategory
from ..inputs.property_input_base import create_property_input

logger = logging.getLogger(__name__)


class VirtualPropertyList(ft.Container):
    """
    Virtual scrolling list for property inputs with conditional visibility
    CLAUDE.md #12.5: Performance with many properties
    """
    
    def __init__(
        self,
        properties: List[PropertyDefinition],
        property_values: Dict[str, Any],
        on_property_change: Callable[[str, Any], None],
        item_height: int = 80,
        visible_items: int = 10,
        component_id: Optional[str] = None
    ):
        super().__init__()
        
        # Core data
        self.all_properties = properties
        self.property_values = property_values
        self.on_property_change = on_property_change
        self.component_id = component_id
        
        # Virtual scrolling parameters
        self.item_height = item_height
        self.visible_items = visible_items
        self.container_height = visible_items * item_height
        
        # State
        self.scroll_offset = 0
        self.filtered_properties: List[PropertyDefinition] = []
        self.visible_properties: List[PropertyDefinition] = []
        self.rendered_inputs: Dict[str, Any] = {}
        
        # Dependency tracking
        self.dependency_map: Dict[str, Set[str]] = {}  # property -> dependents
        self.visibility_state: Dict[str, bool] = {}
        
        # Initialize
        self._update_filtered_properties()
        self._build_dependency_map()
        self._update_visibility_state()
        
        # Set container properties
        self.height = self.container_height
        self.content = self._build_content()
    
    def _build_content(self) -> ft.Control:
        """Build the virtual scrolling container"""
        # Create scrollable container
        self.scroll_container = ft.Column(
            controls=[],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            on_scroll=self._on_scroll,
            height=self.container_height
        )
        
        # Update visible items
        self._update_visible_items()
        
        return self.scroll_container
    
    def _build_dependency_map(self) -> None:
        """Build map of property dependencies for efficient updates"""
        self.dependency_map.clear()
        
        for prop in self.all_properties:
            if prop.dependencies:
                for dep in prop.dependencies:
                    parent_prop = dep.property_name
                    if parent_prop not in self.dependency_map:
                        self.dependency_map[parent_prop] = set()
                    self.dependency_map[parent_prop].add(prop.name)
    
    def _update_visibility_state(self) -> None:
        """Update visibility state for all properties based on dependencies"""
        self.visibility_state.clear()
        
        for prop in self.all_properties:
            is_visible = self._evaluate_property_visibility(prop)
            self.visibility_state[prop.name] = is_visible
    
    def _evaluate_property_visibility(self, prop: PropertyDefinition) -> bool:
        """Evaluate if a property should be visible based on dependencies"""
        if not prop.visible:
            return False
        
        if not prop.dependencies:
            return True
        
        # Evaluate all dependencies
        for dependency in prop.dependencies:
            if not dependency.evaluate(self.property_values):
                if dependency.action in ["hide", "disable"]:
                    return False
        
        return True
    
    def _update_filtered_properties(self) -> None:
        """Update the filtered properties list based on visibility"""
        self.filtered_properties = [
            prop for prop in self.all_properties
            if self.visibility_state.get(prop.name, True)
        ]
    
    def _update_visible_items(self) -> None:
        """Update visible items based on scroll position"""
        if not self.filtered_properties:
            self.scroll_container.controls = []
            return
        
        # Calculate visible range
        start_index = max(0, int(self.scroll_offset // self.item_height))
        end_index = min(
            len(self.filtered_properties),
            start_index + self.visible_items + 2  # Buffer for smooth scrolling
        )
        
        # Create spacer for items above visible area
        top_spacer_height = start_index * self.item_height
        top_spacer = ft.Container(height=top_spacer_height) if top_spacer_height > 0 else None
        
        # Create visible property inputs
        visible_controls = []
        if top_spacer:
            visible_controls.append(top_spacer)
        
        for i in range(start_index, end_index):
            prop = self.filtered_properties[i]
            
            # Create or reuse property input
            if prop.name not in self.rendered_inputs:
                input_control = self._create_property_input(prop)
                if input_control:
                    self.rendered_inputs[prop.name] = input_control
            
            if prop.name in self.rendered_inputs:
                # Wrap in container with fixed height
                item_container = ft.Container(
                    content=self.rendered_inputs[prop.name],
                    height=self.item_height,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4)
                )
                visible_controls.append(item_container)
        
        # Create spacer for items below visible area
        bottom_items = len(self.filtered_properties) - end_index
        bottom_spacer_height = bottom_items * self.item_height
        bottom_spacer = ft.Container(height=bottom_spacer_height) if bottom_spacer_height > 0 else None
        if bottom_spacer:
            visible_controls.append(bottom_spacer)
        
        # Update scroll container
        self.scroll_container.controls = visible_controls
        self.update()
    
    def _create_property_input(self, prop: PropertyDefinition) -> Optional[ft.Control]:
        """Create property input for a property"""
        try:
            current_value = self.property_values.get(prop.name, prop.default_value)
            
            input_control = create_property_input(
                prop, current_value, self._on_input_change, component_id=self.component_id
            )
            
            return input_control
        except Exception as e:
            logger.error(f"Failed to create input for property {prop.name}: {e}")
            return None
    
    def _on_scroll(self, e) -> None:
        """Handle scroll events"""
        if hasattr(e, 'scroll_delta_y'):
            # Update scroll offset
            self.scroll_offset += e.scroll_delta_y
            self.scroll_offset = max(0, self.scroll_offset)
            
            # Update visible items
            self._update_visible_items()
    
    def _on_input_change(self, property_name: str, value: Any) -> None:
        """Handle property input changes"""
        # Update property values
        self.property_values[property_name] = value
        
        # Check for dependent properties
        if property_name in self.dependency_map:
            dependents = self.dependency_map[property_name]
            visibility_changed = False
            
            for dependent_prop_name in dependents:
                # Find the property definition
                dependent_prop = next(
                    (p for p in self.all_properties if p.name == dependent_prop_name),
                    None
                )
                
                if dependent_prop:
                    old_visibility = self.visibility_state.get(dependent_prop_name, True)
                    new_visibility = self._evaluate_property_visibility(dependent_prop)
                    
                    if old_visibility != new_visibility:
                        self.visibility_state[dependent_prop_name] = new_visibility
                        visibility_changed = True
                        
                        # Remove from rendered inputs if hidden
                        if not new_visibility and dependent_prop_name in self.rendered_inputs:
                            del self.rendered_inputs[dependent_prop_name]
            
            # Update filtered properties if visibility changed
            if visibility_changed:
                self._update_filtered_properties()
                self._update_visible_items()
        
        # Notify parent
        self.on_property_change(property_name, value)
        
        logger.debug(f"Virtual list: Property {property_name} changed to {value}")
    
    def update_properties(self, new_properties: List[PropertyDefinition]) -> None:
        """Update the properties list"""
        self.all_properties = new_properties
        self._build_dependency_map()
        self._update_visibility_state()
        self._update_filtered_properties()
        
        # Clear rendered inputs to force recreation
        self.rendered_inputs.clear()
        self._update_visible_items()
    
    def update_property_values(self, new_values: Dict[str, Any]) -> None:
        """Update property values"""
        self.property_values.update(new_values)
        self._update_visibility_state()
        self._update_filtered_properties()
        
        # Update existing inputs
        for prop_name, input_control in self.rendered_inputs.items():
            if prop_name in new_values:
                if hasattr(input_control, 'set_value'):
                    input_control.set_value(new_values[prop_name], validate=False)
        
        self._update_visible_items()
    
    def scroll_to_property(self, property_name: str) -> None:
        """Scroll to make a specific property visible"""
        # Find property index in filtered list
        prop_index = None
        for i, prop in enumerate(self.filtered_properties):
            if prop.name == property_name:
                prop_index = i
                break
        
        if prop_index is not None:
            # Calculate scroll position
            target_offset = prop_index * self.item_height
            
            # Adjust to center in visible area
            center_offset = (self.visible_items // 2) * self.item_height
            self.scroll_offset = max(0, target_offset - center_offset)
            
            self._update_visible_items()
    
    def get_visible_property_count(self) -> int:
        """Get number of visible properties"""
        return len(self.filtered_properties)
    
    def get_total_property_count(self) -> int:
        """Get total number of properties"""
        return len(self.all_properties)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "total_properties": len(self.all_properties),
            "visible_properties": len(self.filtered_properties),
            "rendered_inputs": len(self.rendered_inputs),
            "item_height": self.item_height,
            "container_height": self.container_height,
            "scroll_offset": self.scroll_offset
        }


class DependencyAwarePropertyGroup(ft.Container):
    """
    Property group with dependency-aware visibility
    Shows/hides properties based on conditional logic
    """
    
    def __init__(
        self,
        category: PropertyCategory,
        properties: List[PropertyDefinition],
        property_values: Dict[str, Any],
        on_property_change: Callable[[str, Any], None],
        component_id: Optional[str] = None,
        use_virtual_scrolling: bool = True
    ):
        super().__init__()
        
        self.category = category
        self.properties = properties
        self.property_values = property_values
        self.on_property_change = on_property_change
        self.component_id = component_id
        self.use_virtual_scrolling = use_virtual_scrolling
        
        # State
        self.collapsed = False
        self.property_list: Optional[VirtualPropertyList] = None
        self.dependency_warnings: List[str] = []
        
        self.content = self._build_content()
    
    def _build_content(self) -> ft.Control:
        """Build the property group content"""
        # Header
        header = self._build_header()
        
        # Property list
        if self.use_virtual_scrolling and len(self.properties) > 10:
            # Use virtual scrolling for large property lists
            self.property_list = VirtualPropertyList(
                properties=self.properties,
                property_values=self.property_values,
                on_property_change=self._on_property_change,
                component_id=self.component_id
            )
            properties_container = self.property_list
        else:
            # Use regular list for smaller property lists
            properties_container = self._build_regular_property_list()
        
        # Dependency warnings
        warnings_container = self._build_warnings() if self.dependency_warnings else ft.Container()
        
        return ft.Column([
            header,
            ft.Container(
                content=ft.Column([
                    warnings_container,
                    properties_container
                ], spacing=8),
                visible=not self.collapsed,
                padding=ft.padding.only(left=8, right=8, bottom=8)
            )
        ], spacing=0)
    
    def _build_header(self) -> ft.Control:
        """Build category header"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(self.category.icon, size=16, color="#5E6AD2"),
                ft.Text(
                    self.category.display_name,
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color="#374151"
                ),
                ft.Container(expand=True),
                ft.Text(
                    f"{self._get_visible_count()}/{len(self.properties)}",
                    size=12,
                    color="#6B7280"
                ),
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
    
    def _build_regular_property_list(self) -> ft.Control:
        """Build regular (non-virtual) property list"""
        controls = []
        
        for prop in self.properties:
            if self._should_show_property(prop):
                input_control = self._create_property_input(prop)
                if input_control:
                    controls.append(input_control)
        
        return ft.Column(controls, spacing=12, scroll=ft.ScrollMode.AUTO)
    
    def _build_warnings(self) -> ft.Control:
        """Build dependency warnings display"""
        if not self.dependency_warnings:
            return ft.Container()
        
        warning_controls = []
        for warning in self.dependency_warnings:
            warning_controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.WARNING_AMBER, size=16, color="#F59E0B"),
                        ft.Text(warning, size=12, color="#F59E0B")
                    ], spacing=8),
                    bgcolor="#FFFBEB",
                    border=ft.border.all(1, "#FDE68A"),
                    border_radius=4,
                    padding=8
                )
            )
        
        return ft.Column(warning_controls, spacing=4)
    
    def _should_show_property(self, prop: PropertyDefinition) -> bool:
        """Check if property should be shown"""
        if not prop.visible:
            return False
        
        if not prop.dependencies:
            return True
        
        # Evaluate dependencies
        for dependency in prop.dependencies:
            if not dependency.evaluate(self.property_values):
                if dependency.action in ["hide"]:
                    return False
        
        return True
    
    def _create_property_input(self, prop: PropertyDefinition) -> Optional[ft.Control]:
        """Create property input"""
        try:
            current_value = self.property_values.get(prop.name, prop.default_value)
            return create_property_input(
                prop, current_value, self._on_property_change, component_id=self.component_id
            )
        except Exception as e:
            logger.error(f"Failed to create input for property {prop.name}: {e}")
            return None
    
    def _get_visible_count(self) -> int:
        """Get count of visible properties"""
        return sum(1 for prop in self.properties if self._should_show_property(prop))
    
    def _toggle_collapsed(self) -> None:
        """Toggle collapsed state"""
        self.collapsed = not self.collapsed
        self.content = self._build_content()
        self.update()
    
    def _on_property_change(self, property_name: str, value: Any) -> None:
        """Handle property change"""
        # Update values
        self.property_values[property_name] = value
        
        # Check for dependency changes
        self._check_dependency_changes(property_name)
        
        # Notify parent
        self.on_property_change(property_name, value)
    
    def _check_dependency_changes(self, changed_property: str) -> None:
        """Check if property change affects dependencies"""
        should_rebuild = False
        
        for prop in self.properties:
            if prop.dependencies:
                for dep in prop.dependencies:
                    if dep.property_name == changed_property:
                        should_rebuild = True
                        break
        
        if should_rebuild:
            # Rebuild to update visibility
            if self.property_list:
                self.property_list.update_property_values(self.property_values)
            else:
                self.content = self._build_content()
                self.update()
    
    def update_property_values(self, new_values: Dict[str, Any]) -> None:
        """Update property values"""
        self.property_values.update(new_values)
        
        if self.property_list:
            self.property_list.update_property_values(new_values)
        else:
            self.content = self._build_content()
            self.update()