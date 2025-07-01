"""
Enhanced Property Definition System
Implements advanced property features including dependencies, responsive design, and animations
Following CLAUDE.md guidelines for enterprise-grade code
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Callable, Union, Set
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PropertyCategory(Enum):
    """Property categories for organization with priority ordering"""
    CONTENT = ("Content", "article", 1)
    STYLE = ("Style", "palette", 2) 
    LAYOUT = ("Layout", "dashboard", 3)
    SPACING = ("Spacing", "space_bar", 4)
    TYPOGRAPHY = ("Typography", "text_fields", 5)
    EFFECTS = ("Effects", "auto_awesome", 6)
    INTERACTIONS = ("Interactions", "touch_app", 7)
    RESPONSIVE = ("Responsive", "devices", 8)
    ADVANCED = ("Advanced", "settings", 9)
    
    def __init__(self, display_name: str, icon: str, priority: int):
        self.display_name = display_name
        self.icon = icon
        self.priority = priority


class PropertyType(Enum):
    """Extended property types for advanced editing"""
    # Basic types
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"
    RADIO = "radio"
    
    # Advanced types
    COLOR = "color"
    GRADIENT = "gradient"
    SHADOW = "shadow"
    SPACING = "spacing"  # 4-value input
    SIZE = "size"  # with unit selector
    BORDER = "border"  # composite border editor
    URL = "url"
    FILE = "file"
    ICON = "icon"
    DATE = "date"
    RANGE = "range"  # slider
    
    # Special types
    FONT_FAMILY = "font_family"
    ANIMATION = "animation"
    TRANSFORM = "transform"
    FILTER = "filter"
    CODE = "code"  # code editor
    JSON = "json"  # JSON editor


@dataclass
class PropertyDependency:
    """
    Define conditional property visibility/availability
    CLAUDE.md #1.4: Extensibility - design for future enhancements
    """
    property_name: str  # Property this depends on
    operator: str  # "equals", "not_equals", "contains", "in", "greater_than", etc.
    value: Any  # Value to compare against
    action: str = "show"  # "show", "hide", "enable", "disable"
    
    def evaluate(self, property_values: Dict[str, Any]) -> bool:
        """Evaluate if dependency condition is met"""
        if self.property_name not in property_values:
            return False
            
        actual_value = property_values[self.property_name]
        
        if self.operator == "equals":
            return actual_value == self.value
        elif self.operator == "not_equals":
            return actual_value != self.value
        elif self.operator == "contains" and isinstance(actual_value, str):
            return self.value in actual_value
        elif self.operator == "in" and isinstance(self.value, list):
            return actual_value in self.value
        elif self.operator == "greater_than" and isinstance(actual_value, (int, float)):
            return actual_value > self.value
        elif self.operator == "less_than" and isinstance(actual_value, (int, float)):
            return actual_value < self.value
        elif self.operator == "truthy":
            return bool(actual_value)
        elif self.operator == "falsy":
            return not bool(actual_value)
        
        return False


@dataclass
class PropertyValidation:
    """
    Comprehensive validation rules
    CLAUDE.md #2.1: Robust error handling with meaningful messages
    """
    # Pattern validation
    pattern: Optional[str] = None
    pattern_flags: int = 0  # re flags
    
    # Length validation
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    
    # Value validation
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    
    # Custom validation
    custom_validator: Optional[str] = None  # Function name in validator registry
    
    # Options validation
    allowed_values: Optional[List[Any]] = None
    forbidden_values: Optional[List[Any]] = None
    
    # File validation
    allowed_extensions: Optional[List[str]] = None
    max_file_size: Optional[int] = None  # in bytes
    
    # Error messages
    error_messages: Dict[str, str] = field(default_factory=dict)
    
    def validate(self, value: Any) -> ValidationResult:
        """
        CLAUDE.md #2.1.2: Meaningful error messages
        """
        errors = []
        warnings = []
        
        # Null/empty validation
        if value is None or value == "":
            return ValidationResult(is_valid=True)
        
        # Pattern validation
        if self.pattern and isinstance(value, str):
            if not re.match(self.pattern, value, self.pattern_flags):
                errors.append(
                    self.error_messages.get("pattern", f"Value must match pattern: {self.pattern}")
                )
        
        # Length validation
        if isinstance(value, str):
            if self.min_length is not None and len(value) < self.min_length:
                errors.append(
                    self.error_messages.get("min_length", f"Minimum length is {self.min_length}")
                )
            if self.max_length is not None and len(value) > self.max_length:
                errors.append(
                    self.error_messages.get("max_length", f"Maximum length is {self.max_length}")
                )
        
        # Numeric validation
        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                errors.append(
                    self.error_messages.get("min_value", f"Minimum value is {self.min_value}")
                )
            if self.max_value is not None and value > self.max_value:
                errors.append(
                    self.error_messages.get("max_value", f"Maximum value is {self.max_value}")
                )
        
        # Allowed/forbidden values
        if self.allowed_values and value not in self.allowed_values:
            errors.append(
                self.error_messages.get("allowed_values", f"Value must be one of: {', '.join(map(str, self.allowed_values))}")
            )
        if self.forbidden_values and value in self.forbidden_values:
            errors.append(
                self.error_messages.get("forbidden_values", f"Value cannot be: {value}")
            )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


@dataclass
class ValidationResult:
    """Result of validation with detailed feedback"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass 
class PropertyOption:
    """Option for select/radio properties with rich metadata"""
    value: Any
    label: str
    icon: Optional[str] = None
    description: Optional[str] = None
    disabled: bool = False
    group: Optional[str] = None  # For grouped options


@dataclass
class PropertyOptionGroup:
    """Group of related options"""
    label: str
    options: List[PropertyOption]
    collapsible: bool = True
    collapsed: bool = False


@dataclass
class ResponsiveValue:
    """
    Value that changes based on breakpoints
    CLAUDE.md #1.4: Extensibility for responsive design
    """
    base: Any  # Default value
    breakpoints: Dict[str, Any] = field(default_factory=dict)  # {"sm": value, "md": value, ...}
    
    def get_value(self, breakpoint: str = "base") -> Any:
        """Get value for specific breakpoint"""
        if breakpoint in self.breakpoints:
            return self.breakpoints[breakpoint]
        return self.base


@dataclass
class AnimationConfig:
    """Configuration for animatable properties"""
    duration: float = 0.3  # seconds
    easing: str = "ease-out"  # CSS easing function
    delay: float = 0.0
    property_name: str = ""  # CSS property to animate


@dataclass
class PropertyDefinition:
    """
    Enhanced property definition with advanced features
    CLAUDE.md #1.4: Extensibility - design for future enhancements
    CLAUDE.md #4.1: Explicit types for all fields
    """
    # Basic info
    name: str
    label: str
    category: PropertyCategory
    type: PropertyType
    default_value: Any
    
    # Description and help
    description: str = ""
    help_text: Optional[str] = None
    help_url: Optional[str] = None
    
    # Validation
    validation: Optional[PropertyValidation] = None
    required: bool = False
    
    # Type-specific options
    options: Optional[Union[List[PropertyOption], List[PropertyOptionGroup]]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    step: Optional[Union[int, float]] = None
    units: Optional[List[str]] = None  # Available units (px, %, em, etc.)
    default_unit: Optional[str] = None
    
    # UI hints
    placeholder: Optional[str] = None
    icon: Optional[str] = None
    input_width: Optional[str] = None  # "small", "medium", "large", "full"
    show_preview: bool = False  # Show live preview
    
    # Advanced features
    dependencies: List[PropertyDependency] = field(default_factory=list)
    responsive: bool = False  # Can have different values per breakpoint
    animatable: bool = False  # Can be animated
    animation_config: Optional[AnimationConfig] = None
    
    # Behavior
    visible: bool = True
    editable: bool = True
    advanced: bool = False  # Show in advanced tab
    experimental: bool = False  # Mark as experimental feature
    
    # Search and filtering
    tags: List[str] = field(default_factory=list)
    search_keywords: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """
        CLAUDE.md #2.1.1: Validate all inputs
        """
        # Validate property name
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', self.name):
            raise ValueError(f"Invalid property name: {self.name}. Must start with letter and contain only letters, numbers, and underscores.")
        
        # Validate select/radio options
        if self.type in [PropertyType.SELECT, PropertyType.RADIO] and not self.options:
            raise ValueError(f"Property '{self.name}' of type {self.type.value} requires options")
        
        # Validate numeric constraints
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(f"min_value ({self.min_value}) cannot be greater than max_value ({self.max_value})")
        
        # Add search keywords
        if not self.search_keywords:
            self.search_keywords = [
                self.name.lower(),
                self.label.lower(),
                self.type.value.lower(),
                self.category.display_name.lower()
            ]
            self.search_keywords.extend(self.tags)
    
    def evaluate_dependencies(self, property_values: Dict[str, Any]) -> Dict[str, bool]:
        """
        Evaluate all dependencies and return visibility/availability states
        Returns: {"visible": bool, "enabled": bool}
        """
        visible = True
        enabled = True
        
        for dep in self.dependencies:
            if dep.evaluate(property_values):
                if dep.action == "hide":
                    visible = False
                elif dep.action == "show":
                    visible = True
                elif dep.action == "disable":
                    enabled = False
                elif dep.action == "enable":
                    enabled = True
        
        return {"visible": visible, "enabled": enabled}
    
    def validate_value(self, value: Any) -> ValidationResult:
        """Validate a value against this property's rules"""
        if self.validation:
            return self.validation.validate(value)
        
        # Basic type validation
        errors = []
        if self.type == PropertyType.NUMBER and value is not None:
            try:
                float(value)
            except (ValueError, TypeError):
                errors.append(f"Value must be a number")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def get_responsive_value(self, value: Any, breakpoint: str = "base") -> Any:
        """Get value for specific breakpoint if responsive"""
        if self.responsive and isinstance(value, ResponsiveValue):
            return value.get_value(breakpoint)
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage/transmission"""
        return {
            "name": self.name,
            "label": self.label,
            "category": self.category.name,
            "type": self.type.value,
            "default_value": self.default_value,
            "description": self.description,
            "required": self.required,
            "responsive": self.responsive,
            "animatable": self.animatable,
            "tags": self.tags
        }


# Common property definitions for reuse
COMMON_PROPERTIES = {
    "id": PropertyDefinition(
        name="id",
        label="Component ID",
        category=PropertyCategory.ADVANCED,
        type=PropertyType.TEXT,
        default_value="",
        description="Unique identifier for the component",
        validation=PropertyValidation(
            pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$",
            error_messages={
                "pattern": "ID must start with a letter and contain only letters, numbers, hyphens, and underscores"
            }
        ),
        placeholder="my-component-id",
        icon="fingerprint",
        tags=["identifier", "id", "name"]
    ),
    
    "className": PropertyDefinition(
        name="className",
        label="CSS Classes",
        category=PropertyCategory.STYLE,
        type=PropertyType.TEXT,
        default_value="",
        description="Space-separated CSS class names",
        placeholder="class1 class2",
        icon="css",
        tags=["class", "css", "style"]
    ),
    
    "visible": PropertyDefinition(
        name="visible",
        label="Visible",
        category=PropertyCategory.ADVANCED,
        type=PropertyType.BOOLEAN,
        default_value=True,
        description="Whether the component is visible",
        icon="visibility",
        tags=["visibility", "show", "hide"]
    )
}