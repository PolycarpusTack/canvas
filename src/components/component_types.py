"""
Enhanced Component Type System with Comprehensive Validation
Implements the component definition system from the design.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class ComponentCategory(Enum):
    """
    Component categories for organization.
    Each category has display name, icon, and order.
    """
    # Basic
    LAYOUT = ("Layout", "dashboard", 1)
    CONTENT = ("Content", "article", 2)
    FORMS = ("Forms", "edit_note", 3)
    MEDIA = ("Media", "image", 4)
    
    # Advanced
    NAVIGATION = ("Navigation", "menu", 5)
    DATA_DISPLAY = ("Data Display", "table_chart", 6)
    FEEDBACK = ("Feedback", "info", 7)
    
    # Special
    CUSTOM = ("Custom", "widgets", 8)
    TEMPLATES = ("Templates", "dashboard_customize", 9)
    
    def __init__(self, display_name: str, icon: str, order: int):
        self.display_name = display_name
        self.icon = icon
        self.order = order


class PropertyType(Enum):
    """Types of component properties"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    COLOR = "color"
    SELECT = "select"
    SPACING = "spacing"
    SIZE = "size"
    URL = "url"
    ICON = "icon"
    DATE = "date"
    FILE = "file"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ValidationResult:
    """Result of validation operations"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ComponentSlot:
    """
    Defines a slot for child components.
    Validates slot configuration and accepted components.
    """
    name: str
    description: str
    accepts: List[str] = field(default_factory=list)  # Component types, "*" for any
    min_items: int = 0
    max_items: Optional[int] = None
    required: bool = False
    
    def __post_init__(self):
        """Validate slot configuration"""
        if not self.name:
            raise ValueError("Slot name is required")
        
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', self.name):
            raise ValueError(f"Invalid slot name: {self.name}")
        
        if self.min_items < 0:
            raise ValueError("min_items cannot be negative")
        
        if self.max_items is not None and self.max_items < self.min_items:
            raise ValueError("max_items must be >= min_items")
    
    def accepts_component(self, component_type: str) -> bool:
        """Check if slot accepts component type"""
        if "*" in self.accepts:
            return True
        return component_type in self.accepts
    
    def validate_count(self, count: int) -> ValidationResult:
        """Validate number of components in slot"""
        errors = []
        
        if count < self.min_items:
            errors.append(f"Slot '{self.name}' requires at least {self.min_items} items")
        
        if self.max_items is not None and count > self.max_items:
            errors.append(f"Slot '{self.name}' allows maximum {self.max_items} items")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )


@dataclass
class ComponentConstraints:
    """
    Comprehensive constraint validation for components.
    Enforces size, hierarchy, and instance constraints.
    """
    # Size constraints
    min_width: Optional[float] = None
    max_width: Optional[float] = None
    min_height: Optional[float] = None
    max_height: Optional[float] = None
    aspect_ratio: Optional[float] = None
    
    # Hierarchy constraints
    allowed_parents: Optional[List[str]] = None
    forbidden_parents: Optional[List[str]] = None
    allowed_children: Optional[List[str]] = None
    forbidden_children: Optional[List[str]] = None
    max_depth: int = 10
    
    # Instance constraints
    max_instances: Optional[int] = None
    max_instances_per_parent: Optional[int] = None
    singleton: bool = False
    
    # Property constraints
    required_props: List[str] = field(default_factory=list)
    immutable_props: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate constraints"""
        if self.min_width and self.max_width and self.min_width > self.max_width:
            raise ValueError("min_width cannot be greater than max_width")
        
        if self.min_height and self.max_height and self.min_height > self.max_height:
            raise ValueError("min_height cannot be greater than max_height")
        
        if self.aspect_ratio and self.aspect_ratio <= 0:
            raise ValueError("aspect_ratio must be positive")
    
    def validate_parent(self, parent_type: Optional[str]) -> ValidationResult:
        """Validate parent relationship"""
        errors = []
        
        if parent_type is None:
            # Check if component requires a parent
            if self.allowed_parents and "*" not in self.allowed_parents:
                errors.append("Component requires a parent")
        else:
            if self.allowed_parents and parent_type not in self.allowed_parents and "*" not in self.allowed_parents:
                errors.append(f"Parent type '{parent_type}' not allowed")
            
            if self.forbidden_parents and parent_type in self.forbidden_parents:
                errors.append(f"Parent type '{parent_type}' is forbidden")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def validate_child(self, child_type: str) -> ValidationResult:
        """Validate child relationship"""
        errors = []
        
        if self.allowed_children:
            if child_type not in self.allowed_children and "*" not in self.allowed_children:
                errors.append(f"Child type '{child_type}' not allowed")
        
        if self.forbidden_children and child_type in self.forbidden_children:
            errors.append(f"Child type '{child_type}' is forbidden")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def validate_size(self, width: Optional[float], height: Optional[float]) -> ValidationResult:
        """Validate component size"""
        errors = []
        
        if width is not None:
            if self.min_width and width < self.min_width:
                errors.append(f"Width {width} is less than minimum {self.min_width}")
            if self.max_width and width > self.max_width:
                errors.append(f"Width {width} exceeds maximum {self.max_width}")
        
        if height is not None:
            if self.min_height and height < self.min_height:
                errors.append(f"Height {height} is less than minimum {self.min_height}")
            if self.max_height and height > self.max_height:
                errors.append(f"Height {height} exceeds maximum {self.max_height}")
        
        if self.aspect_ratio and width and height:
            actual_ratio = width / height
            if abs(actual_ratio - self.aspect_ratio) > 0.01:
                errors.append(f"Aspect ratio {actual_ratio:.2f} doesn't match required {self.aspect_ratio:.2f}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )


@dataclass
class PropertyOption:
    """Option for select/radio properties"""
    value: Any
    label: str
    icon: Optional[str] = None
    description: Optional[str] = None


@dataclass
class PropertyValidation:
    """Validation rules for a property"""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    custom_validator: Optional[str] = None  # Function name
    
    def validate(self, value: Any) -> ValidationResult:
        """Validate property value"""
        errors = []
        
        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                errors.append(f"Value {value} is less than minimum {self.min_value}")
            if self.max_value is not None and value > self.max_value:
                errors.append(f"Value {value} exceeds maximum {self.max_value}")
        
        if isinstance(value, str):
            if self.min_length is not None and len(value) < self.min_length:
                errors.append(f"Length {len(value)} is less than minimum {self.min_length}")
            if self.max_length is not None and len(value) > self.max_length:
                errors.append(f"Length {len(value)} exceeds maximum {self.max_length}")
            
            if self.pattern:
                if not re.match(self.pattern, value):
                    errors.append(f"Value doesn't match pattern {self.pattern}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )


@dataclass
class PropertyDefinition:
    """Define a component property with full metadata"""
    name: str
    type: PropertyType
    default_value: Any
    description: str = ""
    required: bool = False
    visible: bool = True
    editable: bool = True
    validation: Optional[PropertyValidation] = None
    options: Optional[List[PropertyOption]] = None  # For select/radio
    depends_on: Optional[Dict[str, Any]] = None  # Conditional visibility
    group: str = "General"  # Property grouping
    
    def __post_init__(self):
        """Validate property definition"""
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', self.name):
            raise ValueError(f"Invalid property name: {self.name}")
        
        # Validate options for select types
        if self.type == PropertyType.SELECT and not self.options:
            raise ValueError(f"Property '{self.name}' of type SELECT requires options")


@dataclass
class ComponentDefinition:
    """
    Complete component definition with all metadata.
    This is the core type that defines a component in the library.
    """
    # Identity
    id: str
    name: str
    category: ComponentCategory
    
    # Visual
    icon: str
    preview_image: Optional[str] = None
    
    # Documentation
    description: str = ""
    tags: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)
    
    # Properties
    properties: List[PropertyDefinition] = field(default_factory=list)
    default_values: Dict[str, Any] = field(default_factory=dict)
    
    # Structure
    slots: List[ComponentSlot] = field(default_factory=list)
    constraints: ComponentConstraints = field(default_factory=ComponentConstraints)
    
    # Behavior
    accepts_children: bool = False
    draggable: bool = True
    droppable: bool = True
    resizable: bool = True
    rotatable: bool = False
    selectable: bool = True
    
    # Metadata
    version: str = "1.0.0"
    author: str = "Canvas Editor"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Advanced
    custom_renderer: Optional[str] = None  # Custom rendering function
    event_handlers: Dict[str, str] = field(default_factory=dict)
    inherit_from: Optional[str] = None  # Base component to inherit from
    
    def __post_init__(self):
        """Validate definition on creation"""
        # Validate ID format
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', self.id):
            raise ValueError(f"Invalid component ID: {self.id}")
        
        # Validate required properties have defaults
        for prop in self.properties:
            if prop.required and prop.name not in self.default_values:
                raise ValueError(f"Required property '{prop.name}' needs default value")
        
        # Set timestamps
        if not self.created_at:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # Validate slots if accepts_children is False
        if not self.accepts_children and self.slots:
            raise ValueError("Component doesn't accept children but has slots defined")
    
    def get_property(self, name: str) -> Optional[PropertyDefinition]:
        """Get property definition by name"""
        return next((p for p in self.properties if p.name == name), None)
    
    def get_slot(self, name: str) -> Optional[ComponentSlot]:
        """Get slot definition by name"""
        return next((s for s in self.slots if s.name == name), None)
    
    def validate_properties(self, props: Dict[str, Any]) -> ValidationResult:
        """Validate a set of properties against this definition"""
        errors = []
        warnings = []
        
        # Check required properties
        for prop_def in self.properties:
            if prop_def.required and prop_def.name not in props:
                errors.append(f"Required property '{prop_def.name}' is missing")
        
        # Validate provided properties
        for key, value in props.items():
            prop_def = self.get_property(key)
            if not prop_def:
                warnings.append(f"Unknown property '{key}'")
                continue
            
            # Validate value if validation rules exist
            if prop_def.validation:
                result = prop_def.validation.validate(value)
                errors.extend(result.errors)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.name,
            'icon': self.icon,
            'description': self.description,
            'tags': self.tags,
            'properties': [
                {
                    'name': p.name,
                    'type': p.type.value,
                    'default': p.default_value,
                    'required': p.required,
                    'group': p.group
                }
                for p in self.properties
            ],
            'default_values': self.default_values,
            'slots': [
                {
                    'name': s.name,
                    'accepts': s.accepts,
                    'required': s.required
                }
                for s in self.slots
            ],
            'constraints': {
                'min_width': self.constraints.min_width,
                'max_width': self.constraints.max_width,
                'allowed_parents': self.constraints.allowed_parents,
                'allowed_children': self.constraints.allowed_children,
            },
            'accepts_children': self.accepts_children,
            'draggable': self.draggable,
            'resizable': self.resizable,
            'version': self.version,
            'author': self.author
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ComponentDefinition:
        """Create from dictionary"""
        # Convert category
        category = ComponentCategory[data['category']]
        
        # Convert properties
        properties = []
        for prop_data in data.get('properties', []):
            properties.append(PropertyDefinition(
                name=prop_data['name'],
                type=PropertyType(prop_data['type']),
                default_value=prop_data.get('default'),
                required=prop_data.get('required', False),
                group=prop_data.get('group', 'General')
            ))
        
        # Convert slots
        slots = []
        for slot_data in data.get('slots', []):
            slots.append(ComponentSlot(
                name=slot_data['name'],
                description=slot_data.get('description', ''),
                accepts=slot_data.get('accepts', ['*']),
                required=slot_data.get('required', False)
            ))
        
        # Convert constraints
        constraint_data = data.get('constraints', {})
        constraints = ComponentConstraints(
            min_width=constraint_data.get('min_width'),
            max_width=constraint_data.get('max_width'),
            allowed_parents=constraint_data.get('allowed_parents'),
            allowed_children=constraint_data.get('allowed_children')
        )
        
        return cls(
            id=data['id'],
            name=data['name'],
            category=category,
            icon=data.get('icon', 'widgets'),
            description=data.get('description', ''),
            tags=data.get('tags', []),
            properties=properties,
            default_values=data.get('default_values', {}),
            slots=slots,
            constraints=constraints,
            accepts_children=data.get('accepts_children', False),
            draggable=data.get('draggable', True),
            resizable=data.get('resizable', True),
            version=data.get('version', '1.0.0'),
            author=data.get('author', 'Canvas Editor')
        )


@dataclass
class CustomComponent:
    """
    User-created custom component.
    Wraps a component definition with additional metadata.
    """
    definition: ComponentDefinition
    template: Any  # Component instance used as template
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0
    shared: bool = False
    share_url: Optional[str] = None
    
    def increment_usage(self):
        """Track component usage"""
        self.usage_count += 1
        self.updated_at = datetime.now()


# Type aliases for clarity
ComponentMap = Dict[str, ComponentDefinition]
ComponentList = List[ComponentDefinition]