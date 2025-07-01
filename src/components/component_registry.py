"""
Component Registry System
Central registry for managing all component definitions.
"""

from typing import Dict, List, Optional, Set, Callable, Any
from datetime import datetime
import json
import logging
from pathlib import Path
from component_types import (
    ComponentDefinition, ComponentCategory, ValidationResult,
    ComponentMap, ComponentList, CustomComponent
)
from builtin_components import BuiltInComponents


logger = logging.getLogger(__name__)


class ComponentRegistry:
    """
    Central registry for all component definitions.
    Manages built-in components, custom components, and component validation.
    """
    
    def __init__(self):
        """Initialize the component registry"""
        self._components: ComponentMap = {}
        self._custom_components: Dict[str, CustomComponent] = {}
        self._categories: Dict[ComponentCategory, Set[str]] = {}
        self._tags: Dict[str, Set[str]] = {}
        self._recently_used: List[str] = []
        self._favorites: Set[str] = set()
        self._listeners: List[Callable[[str, str], None]] = []
        
        # Initialize with built-in components
        self._register_builtin_components()
    
    def _register_builtin_components(self):
        """Register all built-in components"""
        logger.info("Registering built-in components")
        
        definitions = BuiltInComponents.get_all_definitions()
        for component_id, definition in definitions.items():
            try:
                self.register(definition)
                logger.debug(f"Registered built-in component: {component_id}")
            except Exception as e:
                logger.error(f"Failed to register component {component_id}: {e}")
    
    def register(self, definition: ComponentDefinition) -> ValidationResult:
        """
        Register a component definition.
        Validates the definition and updates indexes.
        """
        # Validate the definition
        result = self._validate_definition(definition)
        if not result.is_valid:
            logger.warning(f"Invalid component definition {definition.id}: {result.errors}")
            return result
        
        # Check for conflicts
        if definition.id in self._components:
            return ValidationResult(
                is_valid=False,
                errors=[f"Component with ID '{definition.id}' already exists"]
            )
        
        # Register the component
        self._components[definition.id] = definition
        
        # Update indexes
        self._update_indexes(definition)
        
        # Notify listeners
        self._notify_listeners("registered", definition.id)
        
        logger.info(f"Successfully registered component: {definition.id}")
        return ValidationResult(is_valid=True)
    
    def unregister(self, component_id: str) -> bool:
        """
        Unregister a component definition.
        Returns True if successful, False if component not found.
        """
        if component_id not in self._components:
            logger.warning(f"Attempted to unregister unknown component: {component_id}")
            return False
        
        definition = self._components[component_id]
        
        # Remove from main registry
        del self._components[component_id]
        
        # Remove from indexes
        self._remove_from_indexes(definition)
        
        # Remove from favorites and recently used
        self._favorites.discard(component_id)
        self._recently_used = [id for id in self._recently_used if id != component_id]
        
        # Notify listeners
        self._notify_listeners("unregistered", component_id)
        
        logger.info(f"Successfully unregistered component: {component_id}")
        return True
    
    def get(self, component_id: str) -> Optional[ComponentDefinition]:
        """Get a component definition by ID"""
        definition = self._components.get(component_id)
        
        # Track usage
        if definition:
            self._track_usage(component_id)
        
        return definition
    
    def exists(self, component_id: str) -> bool:
        """Check if a component exists"""
        return component_id in self._components
    
    def get_all(self) -> ComponentMap:
        """Get all registered components"""
        return self._components.copy()
    
    def get_by_category(self, category: ComponentCategory) -> ComponentList:
        """Get all components in a category"""
        component_ids = self._categories.get(category, set())
        return [self._components[id] for id in component_ids if id in self._components]
    
    def get_by_tag(self, tag: str) -> ComponentList:
        """Get all components with a specific tag"""
        component_ids = self._tags.get(tag.lower(), set())
        return [self._components[id] for id in component_ids if id in self._components]
    
    def get_categories(self) -> List[ComponentCategory]:
        """Get all categories that have components"""
        return sorted(
            [cat for cat in self._categories if self._categories[cat]],
            key=lambda c: c.order
        )
    
    def get_tags(self) -> List[str]:
        """Get all unique tags"""
        return sorted(self._tags.keys())
    
    def get_recently_used(self, limit: int = 10) -> ComponentList:
        """Get recently used components"""
        # Remove duplicates while preserving order
        seen = set()
        unique_recent = []
        for id in reversed(self._recently_used):
            if id not in seen and id in self._components:
                seen.add(id)
                unique_recent.append(id)
                if len(unique_recent) >= limit:
                    break
        
        return [self._components[id] for id in unique_recent]
    
    def get_favorites(self) -> ComponentList:
        """Get favorite components"""
        return [self._components[id] for id in self._favorites if id in self._components]
    
    def add_favorite(self, component_id: str) -> bool:
        """Add a component to favorites"""
        if component_id in self._components:
            self._favorites.add(component_id)
            return True
        return False
    
    def remove_favorite(self, component_id: str) -> bool:
        """Remove a component from favorites"""
        if component_id in self._favorites:
            self._favorites.remove(component_id)
            return True
        return False
    
    def is_favorite(self, component_id: str) -> bool:
        """Check if a component is a favorite"""
        return component_id in self._favorites
    
    def validate_parent_child(self, parent_id: Optional[str], child_id: str) -> ValidationResult:
        """Validate if a child component can be added to a parent"""
        child_def = self._components.get(child_id)
        if not child_def:
            return ValidationResult(
                is_valid=False,
                errors=[f"Child component '{child_id}' not found"]
            )
        
        # If no parent, check if child can be root
        if parent_id is None:
            return child_def.constraints.validate_parent(None)
        
        # Get parent definition
        parent_def = self._components.get(parent_id)
        if not parent_def:
            return ValidationResult(
                is_valid=False,
                errors=[f"Parent component '{parent_id}' not found"]
            )
        
        # Check if parent accepts children
        if not parent_def.accepts_children:
            return ValidationResult(
                is_valid=False,
                errors=[f"Component '{parent_id}' does not accept children"]
            )
        
        # Validate constraints
        errors = []
        
        # Check child's parent constraints
        child_parent_result = child_def.constraints.validate_parent(parent_id)
        errors.extend(child_parent_result.errors)
        
        # Check parent's child constraints
        parent_child_result = parent_def.constraints.validate_child(child_id)
        errors.extend(parent_child_result.errors)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def register_custom_component(self, custom: CustomComponent) -> ValidationResult:
        """Register a custom component"""
        # Validate the definition
        result = self.register(custom.definition)
        if not result.is_valid:
            return result
        
        # Store custom component metadata
        self._custom_components[custom.definition.id] = custom
        
        return ValidationResult(is_valid=True)
    
    def get_custom_components(self) -> Dict[str, CustomComponent]:
        """Get all custom components"""
        return self._custom_components.copy()
    
    def export_registry(self, path: Path) -> bool:
        """Export registry to file"""
        try:
            data = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    id: def_.to_dict() for id, def_ in self._components.items()
                },
                "custom_components": {
                    id: {
                        "definition": custom.definition.to_dict(),
                        "created_at": custom.created_at.isoformat(),
                        "updated_at": custom.updated_at.isoformat(),
                        "usage_count": custom.usage_count,
                        "shared": custom.shared
                    }
                    for id, custom in self._custom_components.items()
                },
                "favorites": list(self._favorites),
                "recently_used": self._recently_used[-100:]  # Last 100
            }
            
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Exported registry to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export registry: {e}")
            return False
    
    def import_registry(self, path: Path, merge: bool = True) -> ValidationResult:
        """Import registry from file"""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            if data.get("version") != "1.0":
                return ValidationResult(
                    is_valid=False,
                    errors=["Unsupported registry version"]
                )
            
            errors = []
            imported_count = 0
            
            # Import components
            for id, comp_data in data.get("components", {}).items():
                if not merge and id in self._components:
                    continue
                
                try:
                    definition = ComponentDefinition.from_dict(comp_data)
                    result = self.register(definition)
                    if result.is_valid:
                        imported_count += 1
                    else:
                        errors.extend(result.errors)
                except Exception as e:
                    errors.append(f"Failed to import component {id}: {e}")
            
            # Import favorites
            if merge:
                self._favorites.update(data.get("favorites", []))
            
            logger.info(f"Imported {imported_count} components from {path}")
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=[f"Imported {imported_count} components"]
            )
            
        except Exception as e:
            logger.error(f"Failed to import registry: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Import failed: {e}"]
            )
    
    def add_listener(self, listener: Callable[[str, str], None]):
        """Add a registry change listener"""
        self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable[[str, str], None]):
        """Remove a registry change listener"""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    # Private methods
    
    def _validate_definition(self, definition: ComponentDefinition) -> ValidationResult:
        """Validate a component definition"""
        errors = []
        warnings = []
        
        # Check for required fields
        if not definition.id:
            errors.append("Component ID is required")
        
        if not definition.name:
            errors.append("Component name is required")
        
        if not definition.icon:
            warnings.append("Component icon is recommended")
        
        # Validate slots
        slot_names = set()
        for slot in definition.slots:
            if slot.name in slot_names:
                errors.append(f"Duplicate slot name: {slot.name}")
            slot_names.add(slot.name)
        
        # Validate properties
        prop_names = set()
        for prop in definition.properties:
            if prop.name in prop_names:
                errors.append(f"Duplicate property name: {prop.name}")
            prop_names.add(prop.name)
        
        # Validate default values
        for prop in definition.properties:
            if prop.required and prop.name not in definition.default_values:
                errors.append(f"Required property '{prop.name}' needs default value")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _update_indexes(self, definition: ComponentDefinition):
        """Update category and tag indexes"""
        # Update category index
        if definition.category not in self._categories:
            self._categories[definition.category] = set()
        self._categories[definition.category].add(definition.id)
        
        # Update tag index
        for tag in definition.tags:
            tag_lower = tag.lower()
            if tag_lower not in self._tags:
                self._tags[tag_lower] = set()
            self._tags[tag_lower].add(definition.id)
    
    def _remove_from_indexes(self, definition: ComponentDefinition):
        """Remove component from indexes"""
        # Remove from category index
        if definition.category in self._categories:
            self._categories[definition.category].discard(definition.id)
            if not self._categories[definition.category]:
                del self._categories[definition.category]
        
        # Remove from tag index
        for tag in definition.tags:
            tag_lower = tag.lower()
            if tag_lower in self._tags:
                self._tags[tag_lower].discard(definition.id)
                if not self._tags[tag_lower]:
                    del self._tags[tag_lower]
    
    def _track_usage(self, component_id: str):
        """Track component usage for recently used list"""
        # Add to recently used (most recent at end)
        self._recently_used.append(component_id)
        
        # Limit size
        if len(self._recently_used) > 1000:
            self._recently_used = self._recently_used[-500:]
    
    def _notify_listeners(self, event: str, component_id: str):
        """Notify all listeners of registry changes"""
        for listener in self._listeners:
            try:
                listener(event, component_id)
            except Exception as e:
                logger.error(f"Error notifying listener: {e}")


# Global registry instance
_registry_instance: Optional[ComponentRegistry] = None


def get_component_registry() -> ComponentRegistry:
    """Get the global component registry instance"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ComponentRegistry()
    return _registry_instance