"""
Property Canvas Integration Layer
Complete integration between property editor and canvas editor
Following CLAUDE.md guidelines for robust integration patterns
"""

import flet as ft
from typing import Any, Dict, Optional, Callable, List, Set
import logging
from datetime import datetime

from components.property_definitions import PropertyDefinition, PropertyType, ValidationResult
from components.property_registry import get_registry
from components.default_component_properties import register_default_components
from models.component import Component, ComponentStyle
from ui.panels.complete_property_panel import PropertyPanel
from services.component_service import ComponentService

logger = logging.getLogger(__name__)


class PropertyCanvasIntegrator:
    """
    Main integration class that connects property editor to canvas
    CLAUDE.md #1.1: Enterprise-grade integration patterns
    CLAUDE.md #2.3: Defensive programming with error handling
    """
    
    def __init__(
        self,
        canvas_update_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        validation_callback: Optional[Callable[[str, ValidationResult], None]] = None
    ):
        """
        Initialize the property-canvas integrator
        
        Args:
            canvas_update_callback: Called when component properties change
            validation_callback: Called when validation state changes
        """
        self.canvas_update_callback = canvas_update_callback
        self.validation_callback = validation_callback
        
        # Core services
        self.registry = get_registry()
        self.component_service = ComponentService()
        
        # State tracking
        self.current_component_id: Optional[str] = None
        self.selected_components: Set[str] = set()
        self.property_change_queue: List[Dict[str, Any]] = []
        self.validation_state: Dict[str, ValidationResult] = {}
        
        # Performance optimization
        self.batch_update_timer: Optional[Any] = None
        self.batch_update_delay = 0.1  # 100ms batching
        
        # Initialize default components
        register_default_components()
        
        logger.info("PropertyCanvasIntegrator initialized")
    
    def create_property_panel(self) -> PropertyPanel:
        """Create a property panel connected to this integrator"""
        return PropertyPanel(on_property_change=self._on_property_change)
    
    def set_selected_component(self, component_id: Optional[str], component_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Set the currently selected component for property editing
        
        Args:
            component_id: ID of the component to edit
            component_data: Optional component data (will fetch if not provided)
        """
        self.current_component_id = component_id
        
        if component_id:
            # Get component data if not provided
            if component_data is None:
                component_data = self.component_service.get_component(component_id)
            
            if component_data:
                # Create Component object for property panel
                component = self._create_component_from_data(component_data)
                
                # Validate current properties
                self._validate_component_properties(component)
                
                logger.info(f"Selected component for editing: {component_id} ({component.type})")
            else:
                logger.warning(f"Component data not found for ID: {component_id}")
        else:
            logger.info("Cleared component selection")
    
    def set_multi_selection(self, component_ids: List[str]) -> None:
        """
        Set multiple components for bulk property editing
        
        Args:
            component_ids: List of component IDs to edit
        """
        self.selected_components = set(component_ids)
        
        if len(component_ids) == 1:
            # Single selection - show full property editor
            self.set_selected_component(component_ids[0])
        elif len(component_ids) > 1:
            # Multi-selection - show common properties only
            self._handle_multi_selection(component_ids)
        else:
            # No selection
            self.set_selected_component(None)
    
    def _handle_multi_selection(self, component_ids: List[str]) -> None:
        """Handle multi-component selection"""
        # Find common properties across all selected components
        common_properties = self._find_common_properties(component_ids)
        
        # Create a virtual component representing the selection
        virtual_component = Component(
            id="multi_selection",
            type="multi",
            name=f"{len(component_ids)} components selected"
        )
        
        # Set common property values
        virtual_component.properties = self._get_common_property_values(component_ids, common_properties)
        
        logger.info(f"Multi-selection: {len(component_ids)} components, {len(common_properties)} common properties")
    
    def _find_common_properties(self, component_ids: List[str]) -> List[PropertyDefinition]:
        """Find properties common to all selected components"""
        if not component_ids:
            return []
        
        # Get component types
        component_types = []
        for comp_id in component_ids:
            comp_data = self.component_service.get_component(comp_id)
            if comp_data:
                component_types.append(comp_data.get('type', ''))
        
        if not component_types:
            return []
        
        # Find properties common to all types
        all_property_sets = []
        for comp_type in component_types:
            properties = self.registry.get_component_properties(comp_type)
            property_names = {prop.name for prop in properties}
            all_property_sets.append(property_names)
        
        # Intersection of all property sets
        common_property_names = set.intersection(*all_property_sets) if all_property_sets else set()
        
        # Get property definitions for common properties
        if component_types:
            first_type_properties = self.registry.get_component_properties(component_types[0])
            return [prop for prop in first_type_properties if prop.name in common_property_names]
        
        return []
    
    def _get_common_property_values(self, component_ids: List[str], properties: List[PropertyDefinition]) -> Dict[str, Any]:
        """Get property values that are common across all selected components"""
        common_values = {}
        
        for prop_def in properties:
            values = []
            
            # Collect values from all components
            for comp_id in component_ids:
                comp_data = self.component_service.get_component(comp_id)
                if comp_data and 'properties' in comp_data:
                    value = comp_data['properties'].get(prop_def.name, prop_def.default_value)
                    values.append(value)
            
            # Use common value if all are the same, otherwise use a placeholder
            if values and all(v == values[0] for v in values):
                common_values[prop_def.name] = values[0]
            else:
                common_values[prop_def.name] = None  # Mixed values
        
        return common_values
    
    def _on_property_change(self, component_id: str, property_name: str, value: Any) -> None:
        """
        Handle property change from property panel
        CLAUDE.md #12.5: Performance - batch updates for responsiveness
        """
        # Add to batch queue
        change_event = {
            "component_id": component_id,
            "property_name": property_name,
            "value": value,
            "timestamp": datetime.now()
        }
        
        self.property_change_queue.append(change_event)
        
        # Handle multi-selection
        if len(self.selected_components) > 1 and component_id == "multi_selection":
            # Apply to all selected components
            for comp_id in self.selected_components:
                self._apply_property_change(comp_id, property_name, value)
        else:
            # Single component
            self._apply_property_change(component_id, property_name, value)
        
        # Schedule batch update
        self._schedule_batch_update()
        
        logger.debug(f"Property change queued: {component_id}.{property_name} = {value}")
    
    def _apply_property_change(self, component_id: str, property_name: str, value: Any) -> None:
        """Apply property change to a specific component"""
        try:
            # Get current component data
            component_data = self.component_service.get_component(component_id)
            if not component_data:
                logger.error(f"Component not found: {component_id}")
                return
            
            # Update component properties
            if 'properties' not in component_data:
                component_data['properties'] = {}
            
            # Handle special property paths (e.g., style.color)
            if '.' in property_name:
                self._apply_nested_property_change(component_data, property_name, value)
            else:
                component_data['properties'][property_name] = value
            
            # Update component in service
            self.component_service.update_component(component_id, component_data)
            
            # Validate the change
            self._validate_property_change(component_id, property_name, value)
            
        except Exception as e:
            logger.error(f"Failed to apply property change: {e}")
            if self.validation_callback:
                self.validation_callback(component_id, ValidationResult(
                    is_valid=False,
                    errors=[f"Failed to apply property change: {str(e)}"]
                ))
    
    def _apply_nested_property_change(self, component_data: Dict[str, Any], property_path: str, value: Any) -> None:
        """Apply change to nested property (e.g., style.color)"""
        path_parts = property_path.split('.')
        
        if path_parts[0] == 'style':
            # Update style properties
            if 'style' not in component_data:
                component_data['style'] = {}
            
            style_property = path_parts[1]
            component_data['style'][style_property] = value
            
        elif path_parts[0] == 'content':
            # Update content properties
            if 'content' not in component_data:
                component_data['content'] = {}
            
            content_property = path_parts[1]
            component_data['content'][content_property] = value
        
        else:
            # Regular nested property
            current = component_data
            for part in path_parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            current[path_parts[-1]] = value
    
    def _validate_property_change(self, component_id: str, property_name: str, value: Any) -> None:
        """Validate a property change"""
        try:
            component_data = self.component_service.get_component(component_id)
            if not component_data:
                return
            
            component_type = component_data.get('type', '')
            
            # Validate individual property
            result = self.registry.validate_property_value(component_type, property_name, value)
            
            # Store validation result
            validation_key = f"{component_id}.{property_name}"
            self.validation_state[validation_key] = result
            
            # Notify validation callback
            if self.validation_callback:
                self.validation_callback(component_id, result)
            
            if not result.is_valid:
                logger.warning(f"Property validation failed for {validation_key}: {result.errors}")
            
        except Exception as e:
            logger.error(f"Property validation error: {e}")
    
    def _schedule_batch_update(self) -> None:
        """Schedule batched update to canvas"""
        # Cancel previous timer if exists
        if self.batch_update_timer:
            # In real implementation, would cancel the timer
            pass
        
        # Schedule new update
        # In real implementation, would use actual timer
        self._process_batch_update()
    
    def _process_batch_update(self) -> None:
        """Process queued property changes in batch"""
        if not self.property_change_queue:
            return
        
        # Group changes by component
        changes_by_component = {}
        for change in self.property_change_queue:
            comp_id = change["component_id"]
            if comp_id not in changes_by_component:
                changes_by_component[comp_id] = []
            changes_by_component[comp_id].append(change)
        
        # Send batch updates to canvas
        for component_id, changes in changes_by_component.items():
            if self.canvas_update_callback:
                # Prepare update data
                update_data = {
                    "component_id": component_id,
                    "changes": changes,
                    "timestamp": datetime.now(),
                    "batch_size": len(changes)
                }
                
                try:
                    self.canvas_update_callback(component_id, update_data)
                except Exception as e:
                    logger.error(f"Canvas update callback failed: {e}")
        
        # Clear the queue
        self.property_change_queue.clear()
        self.batch_update_timer = None
        
        logger.debug(f"Processed batch update for {len(changes_by_component)} components")
    
    def _create_component_from_data(self, component_data: Dict[str, Any]) -> Component:
        """Create Component object from raw data"""
        # Extract style data
        style_data = component_data.get('style', {})
        style = ComponentStyle(**style_data)
        
        # Create component
        component = Component(
            id=component_data.get('id', ''),
            type=component_data.get('type', ''),
            name=component_data.get('name', ''),
            content=component_data.get('content'),
            style=style,
            attributes=component_data.get('attributes', {}),
            events=component_data.get('events', {})
        )
        
        # Set properties
        if 'properties' in component_data:
            component.properties = component_data['properties']
        
        return component
    
    def _validate_component_properties(self, component: Component) -> None:
        """Validate all properties of a component"""
        if not hasattr(component, 'properties'):
            return
        
        result = self.registry.validate_all_properties(component.type, component.properties)
        self.validation_state[component.id] = result
        
        if self.validation_callback:
            self.validation_callback(component.id, result)
        
        if not result.is_valid:
            logger.warning(f"Component {component.id} has validation errors: {result.errors}")
    
    # Public API methods
    
    def get_component_properties(self, component_type: str) -> List[PropertyDefinition]:
        """Get all available properties for a component type"""
        return self.registry.get_component_properties(component_type)
    
    def get_property_value(self, component_id: str, property_name: str) -> Any:
        """Get current value of a component property"""
        component_data = self.component_service.get_component(component_id)
        if component_data and 'properties' in component_data:
            return component_data['properties'].get(property_name)
        return None
    
    def set_property_value(self, component_id: str, property_name: str, value: Any) -> bool:
        """Set a component property value programmatically"""
        try:
            self._apply_property_change(component_id, property_name, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set property value: {e}")
            return False
    
    def reset_component_properties(self, component_id: str) -> bool:
        """Reset all component properties to defaults"""
        try:
            component_data = self.component_service.get_component(component_id)
            if not component_data:
                return False
            
            component_type = component_data.get('type', '')
            properties = self.registry.get_component_properties(component_type)
            
            # Reset to defaults
            default_properties = {}
            for prop_def in properties:
                default_properties[prop_def.name] = prop_def.default_value
            
            component_data['properties'] = default_properties
            self.component_service.update_component(component_id, component_data)
            
            return True
        except Exception as e:
            logger.error(f"Failed to reset component properties: {e}")
            return False
    
    def get_validation_state(self, component_id: Optional[str] = None) -> Dict[str, ValidationResult]:
        """Get validation state for component(s)"""
        if component_id:
            return {k: v for k, v in self.validation_state.items() if k.startswith(component_id)}
        return self.validation_state.copy()
    
    def export_component_properties(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Export component properties for saving/sharing"""
        component_data = self.component_service.get_component(component_id)
        if component_data and 'properties' in component_data:
            return {
                "component_id": component_id,
                "component_type": component_data.get('type', ''),
                "properties": component_data['properties'].copy(),
                "exported_at": datetime.now().isoformat()
            }
        return None
    
    def import_component_properties(self, component_id: str, properties_data: Dict[str, Any]) -> bool:
        """Import component properties from saved data"""
        try:
            properties = properties_data.get('properties', {})
            
            for prop_name, value in properties.items():
                self._apply_property_change(component_id, prop_name, value)
            
            return True
        except Exception as e:
            logger.error(f"Failed to import component properties: {e}")
            return False
    
    def search_properties(self, query: str, component_type: Optional[str] = None) -> List[PropertyDefinition]:
        """Search for properties across components"""
        return self.registry.search_properties(query, component_type)
    
    def get_property_history(self, component_id: str, property_name: str) -> List[Dict[str, Any]]:
        """Get change history for a property (from queue)"""
        history = []
        for change in self.property_change_queue:
            if (change["component_id"] == component_id and 
                change["property_name"] == property_name):
                history.append(change)
        
        return sorted(history, key=lambda x: x["timestamp"], reverse=True)
    
    def clear_validation_state(self, component_id: Optional[str] = None) -> None:
        """Clear validation state"""
        if component_id:
            keys_to_remove = [k for k in self.validation_state.keys() if k.startswith(component_id)]
            for key in keys_to_remove:
                del self.validation_state[key]
        else:
            self.validation_state.clear()
    
    def shutdown(self) -> None:
        """Clean shutdown of the integrator"""
        # Process any remaining changes
        if self.property_change_queue:
            self._process_batch_update()
        
        # Cancel timers
        if self.batch_update_timer:
            # Cancel timer in real implementation
            pass
        
        # Clear state
        self.validation_state.clear()
        self.property_change_queue.clear()
        self.selected_components.clear()
        
        logger.info("PropertyCanvasIntegrator shutdown complete")


class PropertyEditorManager:
    """
    High-level manager for the complete property editing system
    Coordinates property panel, integration, and canvas updates
    """
    
    def __init__(self, canvas_container: ft.Container):
        """
        Initialize the property editor manager
        
        Args:
            canvas_container: The main canvas container
        """
        self.canvas_container = canvas_container
        self.property_panel: Optional[PropertyPanel] = None
        self.integrator: Optional[PropertyCanvasIntegrator] = None
        
        # Initialize integration
        self._setup_integration()
    
    def _setup_integration(self) -> None:
        """Set up the integration between property editor and canvas"""
        # Create integrator with callbacks
        self.integrator = PropertyCanvasIntegrator(
            canvas_update_callback=self._on_canvas_update,
            validation_callback=self._on_validation_update
        )
        
        # Create property panel
        self.property_panel = self.integrator.create_property_panel()
    
    def _on_canvas_update(self, component_id: str, update_data: Dict[str, Any]) -> None:
        """Handle canvas updates from property changes"""
        logger.info(f"Canvas update for component {component_id}: {len(update_data.get('changes', []))} changes")
        
        # In real implementation, would trigger canvas re-rendering
        # This is where the visual updates would be applied
    
    def _on_validation_update(self, component_id: str, validation_result: ValidationResult) -> None:
        """Handle validation state updates"""
        if not validation_result.is_valid:
            logger.warning(f"Validation errors for {component_id}: {validation_result.errors}")
    
    def get_property_panel(self) -> PropertyPanel:
        """Get the property panel for UI integration"""
        if not self.property_panel:
            raise RuntimeError("Property panel not initialized")
        return self.property_panel
    
    def select_component(self, component_id: str, component_data: Optional[Dict[str, Any]] = None) -> None:
        """Select a component for property editing"""
        if self.integrator:
            self.integrator.set_selected_component(component_id, component_data)
            
            # Update property panel
            if self.property_panel and component_data:
                component = self.integrator._create_component_from_data(component_data)
                self.property_panel.set_component(component)
    
    def clear_selection(self) -> None:
        """Clear component selection"""
        if self.integrator:
            self.integrator.set_selected_component(None)
        if self.property_panel:
            self.property_panel.set_component(None)
    
    def set_multi_selection(self, component_ids: List[str]) -> None:
        """Set multiple components for editing"""
        if self.integrator:
            self.integrator.set_multi_selection(component_ids)
    
    def get_integrator(self) -> PropertyCanvasIntegrator:
        """Get the property-canvas integrator"""
        if not self.integrator:
            raise RuntimeError("Integrator not initialized")
        return self.integrator