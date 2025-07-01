"""Service for managing components and templates"""

from typing import List, Dict, Any, Optional
import uuid
from models.component import Component, ComponentTemplate, ComponentStyle


class ComponentService:
    """Service for creating and managing components"""
    
    def __init__(self):
        self.templates: Dict[str, ComponentTemplate] = self._load_default_templates()
        self.custom_templates: Dict[str, ComponentTemplate] = {}
    
    def _load_default_templates(self) -> Dict[str, ComponentTemplate]:
        """Load default component templates"""
        templates = {}
        
        # Section template
        section = Component(
            type="section",
            name="Section",
            style=ComponentStyle(
                padding="2rem",
                margin="1rem 0"
            )
        )
        templates["section"] = ComponentTemplate(
            id="section",
            name="Section",
            description="Container with padding",
            category="Layout",
            component=section
        )
        
        # Grid template
        grid = Component(
            type="div",
            name="Grid",
            style=ComponentStyle(
                display="grid",
                grid_template_columns="repeat(auto-fit, minmax(300px, 1fr))",
                gap="1rem"
            )
        )
        templates["grid"] = ComponentTemplate(
            id="grid",
            name="Grid",
            description="Responsive grid layout",
            category="Layout",
            component=grid
        )
        
        # Add more default templates...
        
        return templates
    
    def create_component_from_type(self, component_type: str, 
                                   drop_position: Optional[tuple] = None) -> Component:
        """Create a new component instance from type"""
        # Check if we have a template
        template = self.templates.get(component_type) or self.custom_templates.get(component_type)
        
        if template:
            component = template.create_instance()
        else:
            # Create basic component
            component = Component(
                type=component_type,
                name=component_type.title()
            )
        
        # Apply drop position if provided
        if drop_position:
            component.style.position = "absolute"
            component.style.left = f"{drop_position[0]}px"
            component.style.top = f"{drop_position[1]}px"
        
        return component
    
    def create_component_from_data(self, data: Dict[str, Any]) -> Component:
        """Create component from drag data"""
        component_type = data.get("type", "div")
        name = data.get("name", "Component")
        
        component = self.create_component_from_type(component_type)
        component.name = name
        
        # Apply any additional data
        if "content" in data:
            component.content = data["content"]
        
        return component
    
    def update_component_property(self, component: Component, 
                                  property_path: str, value: Any) -> bool:
        """Update a component property using dot notation path"""
        try:
            # Split the path (e.g., "style.width" -> ["style", "width"])
            parts = property_path.split(".")
            
            # Navigate to the target
            target = component
            for part in parts[:-1]:
                if part == "style":
                    target = component.style
                elif part == "attributes":
                    target = component.attributes
                elif part == "events":
                    target = component.events
                else:
                    target = getattr(target, part)
            
            # Set the value
            final_key = parts[-1]
            if isinstance(target, dict):
                target[final_key] = value
            else:
                setattr(target, final_key, value)
            
            return True
            
        except Exception as e:
            print(f"Error updating component property: {e}")
            return False
    
    def duplicate_component(self, component: Component) -> Component:
        """Create a duplicate of a component"""
        # Deep copy via serialization
        duplicate = Component.from_dict(component.to_dict())
        
        # Generate new ID
        duplicate.id = str(uuid.uuid4())
        
        # Offset position slightly
        if duplicate.style.position == "absolute":
            if duplicate.style.left:
                left_val = duplicate.style.left.replace("px", "")
                try:
                    duplicate.style.left = f"{int(left_val) + 20}px"
                except:
                    pass
            if duplicate.style.top:
                top_val = duplicate.style.top.replace("px", "")
                try:
                    duplicate.style.top = f"{int(top_val) + 20}px"
                except:
                    pass
        
        return duplicate
    
    def move_component(self, component: Component, direction: str) -> bool:
        """Move component up or down in its parent"""
        # This would be implemented by the parent container
        # Returns True if move was successful
        return True
    
    def delete_component(self, component: Component) -> bool:
        """Delete a component"""
        # This would be implemented by the parent container
        # Returns True if deletion was successful
        return True
    
    def save_as_template(self, component: Component, name: str, 
                         description: str = "") -> ComponentTemplate:
        """Save a component as a custom template"""
        template_id = str(uuid.uuid4())
        template = ComponentTemplate(
            id=template_id,
            name=name,
            description=description,
            category="Custom",
            component=component
        )
        
        self.custom_templates[template_id] = template
        return template
    
    def get_all_templates(self) -> List[ComponentTemplate]:
        """Get all available templates"""
        all_templates = list(self.templates.values())
        all_templates.extend(self.custom_templates.values())
        return all_templates