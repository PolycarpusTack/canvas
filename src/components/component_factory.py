"""
Component Factory System
Creates component instances from definitions with proper initialization.
"""

from typing import Dict, Optional, Any, List
from uuid import uuid4
import logging
from datetime import datetime

from component_types import ComponentDefinition, ValidationResult
from component_registry import ComponentRegistry, get_component_registry
from models.component import Component, ComponentStyle


logger = logging.getLogger(__name__)


class ComponentFactory:
    """
    Factory for creating component instances from definitions.
    Handles proper initialization, validation, and default setup.
    """
    
    def __init__(self, registry: Optional[ComponentRegistry] = None):
        """Initialize the factory with a component registry"""
        self.registry = registry or get_component_registry()
        self._instance_counters: Dict[str, int] = {}
        self._singleton_instances: Dict[str, Component] = {}
    
    def create_component(
        self,
        component_id: str,
        properties: Optional[Dict[str, Any]] = None,
        validate: bool = True
    ) -> Component:
        """
        Create a component instance from a definition.
        
        Args:
            component_id: ID of the component definition
            properties: Optional properties to override defaults
            validate: Whether to validate the properties
            
        Returns:
            Component instance
            
        Raises:
            ValueError: If component definition not found or validation fails
        """
        # Get component definition
        definition = self.registry.get(component_id)
        if not definition:
            raise ValueError(f"Component definition not found: {component_id}")
        
        # Check singleton constraint
        if definition.constraints.singleton:
            if component_id in self._singleton_instances:
                logger.warning(f"Singleton component {component_id} already exists")
                return self._singleton_instances[component_id]
        
        # Merge properties with defaults
        final_properties = self._prepare_properties(definition, properties)
        
        # Validate properties if requested
        if validate:
            validation_result = definition.validate_properties(final_properties)
            if not validation_result.is_valid:
                raise ValueError(f"Invalid properties: {validation_result.errors}")
        
        # Generate unique instance ID
        instance_id = self._generate_instance_id(component_id)
        
        # Create base component
        component = Component(
            id=instance_id,
            type=component_id,
            name=self._generate_instance_name(definition),
            attributes=self._extract_attributes(final_properties),
            style=self._create_component_style(definition, final_properties)
        )
        
        # Apply component-specific initialization
        self._initialize_component(component, definition, final_properties)
        
        # Store singleton instance
        if definition.constraints.singleton:
            self._singleton_instances[component_id] = component
        
        # Track instance creation
        self._track_instance_creation(component_id)
        
        logger.debug(f"Created component instance: {component_id} -> {instance_id}")
        return component
    
    def create_component_tree(
        self,
        component_id: str,
        properties: Optional[Dict[str, Any]] = None,
        children: Optional[List[Dict[str, Any]]] = None
    ) -> Component:
        """
        Create a component with child components.
        
        Args:
            component_id: ID of the parent component definition
            properties: Optional properties for the parent
            children: List of child component configurations
            
        Returns:
            Component tree
        """
        # Create parent component
        parent = self.create_component(component_id, properties)
        
        # Add children if provided
        if children:
            for child_config in children:
                child_id = child_config.get("component_id")
                child_props = child_config.get("properties", {})
                child_children = child_config.get("children")
                
                if child_id:
                    # Validate parent-child relationship
                    validation = self.registry.validate_parent_child(component_id, child_id)
                    if not validation.is_valid:
                        logger.warning(f"Invalid parent-child relationship: {validation.errors}")
                        continue
                    
                    # Create child (recursive for nested children)
                    if child_children:
                        child = self.create_component_tree(child_id, child_props, child_children)
                    else:
                        child = self.create_component(child_id, child_props)
                    
                    parent.children.append(child)
        
        return parent
    
    def create_from_template(self, template: Component) -> Component:
        """
        Create a new component instance from an existing template.
        Performs a deep copy with new IDs.
        """
        # Create new instance from template's definition
        new_component = self.create_component(
            template.type,
            properties=template.attributes.copy()
        )
        
        # Copy styling
        new_component.style = ComponentStyle(**template.style.__dict__)
        
        # Recursively copy children
        for child in template.children:
            new_child = self.create_from_template(child)
            new_component.children.append(new_child)
        
        return new_component
    
    def validate_component_tree(self, component: Component) -> ValidationResult:
        """
        Validate an entire component tree for constraint compliance.
        """
        errors = []
        warnings = []
        
        # Validate the component itself
        definition = self.registry.get(component.type)
        if not definition:
            errors.append(f"Unknown component type: {component.type}")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Validate properties
        prop_result = definition.validate_properties(component.attributes)
        errors.extend(prop_result.errors)
        warnings.extend(prop_result.warnings)
        
        # Validate children
        for child in component.children:
            # Validate parent-child relationship
            relation_result = self.registry.validate_parent_child(component.type, child.type)
            if not relation_result.is_valid:
                errors.extend([f"Child {child.id}: {error}" for error in relation_result.errors])
            
            # Recursively validate child
            child_result = self.validate_component_tree(child)
            errors.extend([f"Child {child.id}: {error}" for error in child_result.errors])
            warnings.extend([f"Child {child.id}: {warning}" for warning in child_result.warnings])
        
        # Validate slot constraints
        if definition.slots:
            slot_errors = self._validate_slots(component, definition)
            errors.extend(slot_errors)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def get_instance_count(self, component_id: str) -> int:
        """Get the number of instances created for a component type"""
        return self._instance_counters.get(component_id, 0)
    
    def reset_singleton(self, component_id: str) -> bool:
        """Reset a singleton instance (for testing/development)"""
        if component_id in self._singleton_instances:
            del self._singleton_instances[component_id]
            return True
        return False
    
    # Private methods
    
    def _prepare_properties(
        self,
        definition: ComponentDefinition,
        properties: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Merge user properties with defaults"""
        final_properties = definition.default_values.copy()
        
        if properties:
            # Only include known properties
            for prop_name, value in properties.items():
                prop_def = definition.get_property(prop_name)
                if prop_def:
                    final_properties[prop_name] = value
                else:
                    logger.warning(f"Unknown property '{prop_name}' for component {definition.id}")
        
        return final_properties
    
    def _generate_instance_id(self, component_id: str) -> str:
        """Generate a unique instance ID"""
        return f"{component_id}_{uuid4().hex[:8]}"
    
    def _generate_instance_name(self, definition: ComponentDefinition) -> str:
        """Generate a human-readable instance name"""
        count = self._instance_counters.get(definition.id, 0) + 1
        if count == 1:
            return definition.name
        return f"{definition.name} {count}"
    
    def _extract_attributes(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Extract HTML attributes from properties"""
        attributes = {}
        
        # Common HTML attributes
        html_attrs = {
            'id', 'class', 'title', 'data-*', 'aria-*',
            'placeholder', 'value', 'href', 'src', 'alt',
            'type', 'name', 'required', 'disabled', 'readonly'
        }
        
        for key, value in properties.items():
            # Include direct HTML attributes
            if key in html_attrs or key.startswith(('data-', 'aria-')):
                attributes[key] = value
            # Convert some properties to attributes
            elif key in ['width', 'height', 'maxlength', 'min', 'max', 'step']:
                attributes[key] = value
        
        return attributes
    
    def _create_component_style(
        self,
        definition: ComponentDefinition,
        properties: Dict[str, Any]
    ) -> ComponentStyle:
        """Create component style from properties"""
        style = ComponentStyle()
        
        # Map properties to CSS styles
        style_mappings = {
            'width': 'width',
            'height': 'height',
            'margin': 'margin',
            'padding': 'padding',
            'background': 'background_color',
            'color': 'color',
            'border': 'border',
            'border_radius': 'border_radius',
            'font_size': 'font_size',
            'font_weight': 'font_weight',
            'text_align': 'text_align',
            'display': 'display',
            'position': 'position',
            'flex_direction': 'flex_direction',
            'justify_content': 'justify_content',
            'align_items': 'align_items',
            'gap': 'gap',
            'grid_template_columns': 'grid_template_columns',
            'grid_template_rows': 'grid_template_rows'
        }
        
        for prop_key, style_key in style_mappings.items():
            if prop_key in properties:
                setattr(style, style_key, properties[prop_key])
        
        return style
    
    def _initialize_component(
        self,
        component: Component,
        definition: ComponentDefinition,
        properties: Dict[str, Any]
    ):
        """Apply component-specific initialization"""
        
        # Set component content for text-based components
        text_components = {'heading', 'paragraph', 'text', 'button', 'label'}
        if definition.id in text_components and 'text' in properties:
            component.content = properties['text']
        
        # Initialize form elements
        if definition.id == 'form':
            component.attributes.update({
                'method': properties.get('method', 'POST'),
                'action': properties.get('action', '#')
            })
        
        elif definition.id == 'input':
            component.attributes.update({
                'type': properties.get('type', 'text'),
                'placeholder': properties.get('placeholder', ''),
                'name': properties.get('name', f'input_{uuid4().hex[:6]}')
            })
            if properties.get('required'):
                component.attributes['required'] = True
        
        elif definition.id == 'select':
            component.attributes['name'] = properties.get('name', f'select_{uuid4().hex[:6]}')
            # Add default option if options provided
            options = properties.get('options', [])
            if options:
                for option in options:
                    option_component = Component(
                        id=str(uuid4()),
                        type='option',
                        name='Option',
                        content=option.get('label', option.get('value', '')),
                        attributes={'value': option.get('value', '')}
                    )
                    component.children.append(option_component)
        
        elif definition.id == 'image':
            component.attributes.update({
                'src': properties.get('src', ''),
                'alt': properties.get('alt', '')
            })
        
        elif definition.id == 'link':
            component.attributes['href'] = properties.get('href', '#')
            component.content = properties.get('text', 'Link')
        
        # Set editor metadata
        component.locked = properties.get('locked', False)
        component.visible = properties.get('visible', True)
        
        # Apply behavior settings from definition
        if hasattr(component, 'draggable'):
            component.draggable = definition.draggable
        if hasattr(component, 'resizable'):
            component.resizable = definition.resizable
    
    def _validate_slots(self, component: Component, definition: ComponentDefinition) -> List[str]:
        """Validate component slots"""
        errors = []
        
        # Group children by slot (simplified - assumes single default slot)
        child_count = len(component.children)
        
        for slot in definition.slots:
            # Validate slot item count
            result = slot.validate_count(child_count)
            errors.extend(result.errors)
            
            # Validate child types in slot
            for child in component.children:
                if not slot.accepts_component(child.type):
                    errors.append(f"Component '{child.type}' not accepted in slot '{slot.name}'")
        
        return errors
    
    def _track_instance_creation(self, component_id: str):
        """Track instance creation for statistics"""
        if component_id not in self._instance_counters:
            self._instance_counters[component_id] = 0
        self._instance_counters[component_id] += 1


# Global factory instance
_factory_instance: Optional[ComponentFactory] = None


def get_component_factory() -> ComponentFactory:
    """Get the global component factory instance"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = ComponentFactory()
    return _factory_instance