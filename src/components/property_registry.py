"""
Property Registry System
Thread-safe registration and management of component properties
Following CLAUDE.md guidelines for enterprise-grade code
"""

from __future__ import annotations
import threading
from typing import Dict, List, Optional, Any, Callable, Set
from collections import defaultdict
import logging
import json
from pathlib import Path
from datetime import datetime

from property_definitions import (
    PropertyDefinition, PropertyType, PropertyValidation,
    ValidationResult, COMMON_PROPERTIES
)
from component_types import ComponentDefinition

logger = logging.getLogger(__name__)


class PropertyValidator:
    """Base class for custom property validators"""
    
    def validate(self, value: Any, property_def: PropertyDefinition) -> ValidationResult:
        """Validate a property value"""
        raise NotImplementedError("Subclasses must implement validate()")


class PropertyRegistry:
    """
    Thread-safe registry for component property definitions
    CLAUDE.md #1.3: Singleton pattern for consistency
    CLAUDE.md #12.1: Structured logging
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._definitions: Dict[str, List[PropertyDefinition]] = {}
        self._validators: Dict[PropertyType, PropertyValidator] = {}
        self._custom_validators: Dict[str, Callable] = {}
        self._property_groups: Dict[str, List[str]] = defaultdict(list)
        self._lock = threading.RLock()
        
        # Cache for frequently accessed data
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Initialize default validators
        self._init_default_validators()
        
        # Register common properties
        self._register_common_properties()
        
        logger.info("PropertyRegistry initialized")
    
    def _init_default_validators(self):
        """Initialize built-in validators for each property type"""
        # Color validator
        self.register_validator(PropertyType.COLOR, ColorValidator())
        
        # URL validator
        self.register_validator(PropertyType.URL, URLValidator())
        
        # Number validator
        self.register_validator(PropertyType.NUMBER, NumberValidator())
        
        # Spacing validator
        self.register_validator(PropertyType.SPACING, SpacingValidator())
    
    def _register_common_properties(self):
        """Register common properties that all components can use"""
        for prop_name, prop_def in COMMON_PROPERTIES.items():
            self.register_common_property(prop_def)
    
    def register_component_properties(
        self,
        component_type: str,
        properties: List[PropertyDefinition],
        replace: bool = False
    ) -> None:
        """
        Register properties for a component type
        CLAUDE.md #2.1.4: Thread-safe registration
        """
        with self._lock:
            # Validate component type
            if not component_type:
                raise ValueError("Component type cannot be empty")
            
            # Check if already exists
            if component_type in self._definitions and not replace:
                raise ValueError(f"Properties for component '{component_type}' already registered. Use replace=True to override.")
            
            # Validate no duplicate property names
            property_names = [p.name for p in properties]
            if len(property_names) != len(set(property_names)):
                duplicates = [name for name in property_names if property_names.count(name) > 1]
                raise ValueError(f"Duplicate property names found: {', '.join(set(duplicates))}")
            
            # Validate each property
            for prop in properties:
                self._validate_property_definition(prop)
            
            # Store properties
            self._definitions[component_type] = properties
            
            # Update property groups
            for prop in properties:
                self._property_groups[prop.category.name].append(f"{component_type}.{prop.name}")
            
            # Clear cache
            self._clear_cache()
            
            logger.info(f"Registered {len(properties)} properties for component '{component_type}'")
    
    def register_common_property(self, property_def: PropertyDefinition) -> None:
        """Register a property that's available to all components"""
        with self._lock:
            if "_common" not in self._definitions:
                self._definitions["_common"] = []
            
            # Check for duplicates
            existing_names = [p.name for p in self._definitions["_common"]]
            if property_def.name in existing_names:
                logger.warning(f"Common property '{property_def.name}' already registered, skipping")
                return
            
            self._definitions["_common"].append(property_def)
            logger.info(f"Registered common property '{property_def.name}'")
    
    def register_validator(self, property_type: PropertyType, validator: PropertyValidator) -> None:
        """Register a validator for a property type"""
        with self._lock:
            self._validators[property_type] = validator
            logger.info(f"Registered validator for property type '{property_type.value}'")
    
    def register_custom_validator(self, name: str, validator_func: Callable) -> None:
        """Register a custom validator function"""
        with self._lock:
            self._custom_validators[name] = validator_func
            logger.info(f"Registered custom validator '{name}'")
    
    def get_component_properties(
        self,
        component_type: str,
        include_common: bool = True
    ) -> List[PropertyDefinition]:
        """
        Get all properties for a component type
        CLAUDE.md #2.3: Defensive programming
        """
        with self._lock:
            # Check cache first
            cache_key = f"props_{component_type}_{include_common}"
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached
            
            properties = []
            
            # Get component-specific properties
            if component_type in self._definitions:
                properties.extend(self._definitions[component_type])
            
            # Add common properties if requested
            if include_common and "_common" in self._definitions:
                common_props = self._definitions["_common"]
                # Don't add duplicates
                existing_names = {p.name for p in properties}
                for prop in common_props:
                    if prop.name not in existing_names:
                        properties.append(prop)
            
            # Cache result
            self._set_cached(cache_key, properties)
            
            return properties
    
    def get_property(self, component_type: str, property_name: str) -> Optional[PropertyDefinition]:
        """Get a specific property definition"""
        properties = self.get_component_properties(component_type)
        return next((p for p in properties if p.name == property_name), None)
    
    def validate_property_value(
        self,
        component_type: str,
        property_name: str,
        value: Any
    ) -> ValidationResult:
        """
        Validate a property value
        CLAUDE.md #2.1.2: Meaningful error messages
        """
        # Get property definition
        prop_def = self.get_property(component_type, property_name)
        if not prop_def:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unknown property '{property_name}' for component '{component_type}'"]
            )
        
        # Use property's own validation first
        result = prop_def.validate_value(value)
        if not result.is_valid:
            return result
        
        # Use type-specific validator if available
        if prop_def.type in self._validators:
            validator = self._validators[prop_def.type]
            result = validator.validate(value, prop_def)
            if not result.is_valid:
                return result
        
        # Use custom validator if specified
        if prop_def.validation and prop_def.validation.custom_validator:
            validator_name = prop_def.validation.custom_validator
            if validator_name in self._custom_validators:
                validator_func = self._custom_validators[validator_name]
                try:
                    is_valid = validator_func(value, prop_def)
                    if not is_valid:
                        return ValidationResult(
                            is_valid=False,
                            errors=[f"Custom validation failed for '{property_name}'"]
                        )
                except Exception as e:
                    logger.error(f"Custom validator '{validator_name}' failed: {e}")
                    return ValidationResult(
                        is_valid=False,
                        errors=[f"Validation error: {str(e)}"]
                    )
        
        return ValidationResult(is_valid=True)
    
    def validate_all_properties(
        self,
        component_type: str,
        property_values: Dict[str, Any]
    ) -> ValidationResult:
        """Validate all properties for a component"""
        errors = []
        warnings = []
        
        properties = self.get_component_properties(component_type)
        
        # Check required properties
        for prop in properties:
            if prop.required and prop.name not in property_values:
                errors.append(f"Required property '{prop.name}' is missing")
        
        # Validate provided properties
        for prop_name, value in property_values.items():
            result = self.validate_property_value(component_type, prop_name, value)
            errors.extend(result.errors)
            warnings.extend(result.warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def search_properties(
        self,
        query: str,
        component_type: Optional[str] = None,
        categories: Optional[List[str]] = None
    ) -> List[PropertyDefinition]:
        """
        Search for properties by query
        CLAUDE.md #1.5: Performance optimization with caching
        """
        with self._lock:
            # Normalize query
            query_lower = query.lower()
            
            # Get all properties to search
            if component_type:
                properties = self.get_component_properties(component_type)
            else:
                # Search all properties
                properties = []
                for comp_type, props in self._definitions.items():
                    properties.extend(props)
            
            # Filter by categories if specified
            if categories:
                properties = [
                    p for p in properties
                    if p.category.name in categories
                ]
            
            # Search properties
            results = []
            for prop in properties:
                # Search in various fields
                if any([
                    query_lower in prop.name.lower(),
                    query_lower in prop.label.lower(),
                    query_lower in prop.description.lower(),
                    any(query_lower in tag.lower() for tag in prop.tags),
                    any(query_lower in kw.lower() for kw in prop.search_keywords)
                ]):
                    results.append(prop)
            
            return results
    
    def export_schema(self, component_type: Optional[str] = None) -> Dict[str, Any]:
        """Export property schema for documentation or tooling"""
        with self._lock:
            if component_type:
                properties = self.get_component_properties(component_type)
                return {
                    "component_type": component_type,
                    "properties": [prop.to_dict() for prop in properties]
                }
            else:
                # Export all schemas
                schemas = {}
                for comp_type in self._definitions:
                    if comp_type != "_common":
                        properties = self.get_component_properties(comp_type)
                        schemas[comp_type] = [prop.to_dict() for prop in properties]
                return schemas
    
    def _validate_property_definition(self, prop_def: PropertyDefinition) -> None:
        """Validate a property definition before registration"""
        # Check for circular dependencies
        if prop_def.dependencies:
            self._check_circular_dependencies(prop_def)
        
        # Validate property type specific requirements
        if prop_def.type in [PropertyType.SELECT, PropertyType.RADIO]:
            if not prop_def.options:
                raise ValueError(f"Property '{prop_def.name}' requires options")
            if len(prop_def.options) == 0:
                raise ValueError(f"Property '{prop_def.name}' must have at least one option")
    
    def _check_circular_dependencies(self, prop_def: PropertyDefinition) -> None:
        """Check for circular dependencies"""
        visited = set()
        
        def check_deps(prop_name: str, deps: List[PropertyDependency], path: List[str]):
            if prop_name in path:
                raise ValueError(f"Circular dependency detected: {' -> '.join(path + [prop_name])}")
            
            for dep in deps:
                check_deps(dep.property_name, [], path + [prop_name])
        
        check_deps(prop_def.name, prop_def.dependencies, [])
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self._cache:
            timestamp = self._cache_timestamps.get(key)
            if timestamp and (datetime.now() - timestamp).seconds < self._cache_ttl:
                return self._cache[key]
        return None
    
    def _set_cached(self, key: str, value: Any) -> None:
        """Set cached value with timestamp"""
        self._cache[key] = value
        self._cache_timestamps[key] = datetime.now()
    
    def _clear_cache(self) -> None:
        """Clear all cached data"""
        self._cache.clear()
        self._cache_timestamps.clear()


# Built-in validators
class ColorValidator(PropertyValidator):
    """Validator for color properties"""
    
    def validate(self, value: Any, property_def: PropertyDefinition) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                errors=["Color value must be a string"]
            )
        
        # Check various color formats
        import re
        patterns = {
            'hex': r'^#?[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?$',
            'rgb': r'^rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)$',
            'rgba': r'^rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*[01]?\.?\d*\s*\)$',
            'hsl': r'^hsl\(\s*\d{1,3}\s*,\s*\d{1,3}%\s*,\s*\d{1,3}%\s*\)$',
            'hsla': r'^hsla\(\s*\d{1,3}\s*,\s*\d{1,3}%\s*,\s*\d{1,3}%\s*,\s*[01]?\.?\d*\s*\)$'
        }
        
        # Check if value matches any pattern
        for format_name, pattern in patterns.items():
            if re.match(pattern, value, re.IGNORECASE):
                return ValidationResult(is_valid=True)
        
        # Check for CSS color names
        css_colors = {
            'black', 'white', 'red', 'green', 'blue', 'yellow', 'cyan', 'magenta',
            'gray', 'grey', 'orange', 'purple', 'brown', 'pink', 'transparent'
        }
        if value.lower() in css_colors:
            return ValidationResult(is_valid=True)
        
        return ValidationResult(
            is_valid=False,
            errors=["Invalid color format. Use HEX (#RRGGBB), RGB(r,g,b), HSL(h,s%,l%), or CSS color names"],
            suggestions=["#FF0000", "rgb(255, 0, 0)", "hsl(0, 100%, 50%)", "red"]
        )


class URLValidator(PropertyValidator):
    """Validator for URL properties"""
    
    def validate(self, value: Any, property_def: PropertyDefinition) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                errors=["URL must be a string"]
            )
        
        import re
        # Basic URL pattern
        url_pattern = r'^(https?://)?[\w\-]+(\.[\w\-]+)+([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?$'
        
        if re.match(url_pattern, value, re.IGNORECASE):
            return ValidationResult(is_valid=True)
        
        # Check for relative URLs
        if value.startswith('/') or value.startswith('./') or value.startswith('../'):
            return ValidationResult(is_valid=True)
        
        return ValidationResult(
            is_valid=False,
            errors=["Invalid URL format"],
            suggestions=["https://example.com", "/path/to/resource", "./relative/path"]
        )


class NumberValidator(PropertyValidator):
    """Validator for number properties"""
    
    def validate(self, value: Any, property_def: PropertyDefinition) -> ValidationResult:
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                errors=["Value must be a valid number"]
            )
        
        errors = []
        
        # Check min/max constraints
        if property_def.min_value is not None and num_value < property_def.min_value:
            errors.append(f"Value must be at least {property_def.min_value}")
        
        if property_def.max_value is not None and num_value > property_def.max_value:
            errors.append(f"Value must be at most {property_def.max_value}")
        
        # Check step constraint
        if property_def.step is not None:
            # Check if value is a multiple of step
            remainder = (num_value - (property_def.min_value or 0)) % property_def.step
            if remainder > 0.0001:  # Small epsilon for floating point comparison
                errors.append(f"Value must be a multiple of {property_def.step}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )


class SpacingValidator(PropertyValidator):
    """Validator for spacing properties (margin, padding)"""
    
    def validate(self, value: Any, property_def: PropertyDefinition) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                errors=["Spacing value must be a string"]
            )
        
        # Parse spacing value
        import re
        # Pattern for valid spacing value with unit
        value_pattern = r'^-?\d+(\.\d+)?(px|em|rem|%|vh|vw|auto)$'
        
        # Split by spaces
        parts = value.strip().split()
        
        if len(parts) == 0 or len(parts) > 4:
            return ValidationResult(
                is_valid=False,
                errors=["Spacing must have 1-4 values"],
                suggestions=["10px", "10px 20px", "10px 20px 30px", "10px 20px 30px 40px"]
            )
        
        # Validate each part
        for part in parts:
            if part != "auto" and not re.match(value_pattern, part, re.IGNORECASE):
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Invalid spacing value: {part}"],
                    suggestions=["10px", "1em", "50%", "auto"]
                )
        
        return ValidationResult(is_valid=True)


# Singleton instance
_registry = PropertyRegistry()

# Public API
def get_registry() -> PropertyRegistry:
    """Get the singleton PropertyRegistry instance"""
    return _registry