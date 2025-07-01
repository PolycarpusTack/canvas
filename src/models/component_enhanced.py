"""
Enhanced Component Model for Export System Compatibility

CLAUDE.md Implementation:
- #4.1: Strong typing and validation
- #2.1.1: Comprehensive validation
- #7.2: Content sanitization
"""

import html
import re
from dataclasses import dataclass, field, asdict, fields
from typing import Optional, List, Dict, Any, Union
from uuid import uuid4

from .component import Component as BaseComponent, ComponentStyle


@dataclass 
class ExportCompatibleComponent:
    """
    Enhanced Component model compatible with export system
    
    CLAUDE.md #4.1: Explicit types and validation
    """
    
    # Core properties
    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = "div" 
    name: Optional[str] = None
    content: Optional[str] = None
    content_type: str = "text"  # "text", "html", "markdown"
    
    # Hierarchy
    children: List['ExportCompatibleComponent'] = field(default_factory=list)
    parent_id: Optional[str] = None
    
    # Properties and styling
    properties: Dict[str, Any] = field(default_factory=dict)  # Export system expects this
    attributes: Dict[str, Any] = field(default_factory=dict)  # Canvas system uses this
    styles: Dict[str, Any] = field(default_factory=dict)     # Export system expects this
    style: Optional[ComponentStyle] = None                    # Canvas system uses this
    
    # Semantic and accessibility
    semantic_role: Optional[str] = None
    class_name: Optional[str] = None
    aria_attributes: Dict[str, str] = field(default_factory=dict)
    
    # Events and interactions
    events: Dict[str, str] = field(default_factory=dict)
    
    # Responsive and state
    responsive_styles: Dict[int, Dict[str, Any]] = field(default_factory=dict)  # breakpoint -> styles
    responsive_classes: List[str] = field(default_factory=list)
    data_attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Editor metadata
    locked: bool = False
    visible: bool = True
    selected: bool = False
    expanded: bool = True
    
    # Asset references
    asset_id: Optional[str] = None
    
    def __post_init__(self):
        """Initialize and validate component after creation"""
        self._sync_properties()
        self._validate_component()
        self._set_defaults()
    
    def _sync_properties(self):
        """
        Synchronize between properties/attributes and styles/style
        for compatibility with both systems
        """
        # Sync attributes <-> properties
        if self.attributes and not self.properties:
            self.properties = self.attributes.copy()
        elif self.properties and not self.attributes:
            self.attributes = self.properties.copy()
        
        # Sync style <-> styles
        if self.style and not self.styles:
            self.styles = asdict(self.style)
        elif self.styles and not self.style:
            # Only sync compatible properties that exist in ComponentStyle
            compatible_styles = self._filter_compatible_styles(self.styles)
            if compatible_styles:
                self.style = ComponentStyle(**compatible_styles)
        
        # Set class_name from properties if available
        if not self.class_name:
            self.class_name = self.properties.get("class") or self.properties.get("className")
    
    def _filter_compatible_styles(self, styles: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter styles to only include properties compatible with ComponentStyle
        """
        # Get field names from ComponentStyle
        style_fields = {f.name for f in fields(ComponentStyle)}
        
        compatible = {}
        for key, value in styles.items():
            # Convert camelCase to snake_case to match ComponentStyle fields
            snake_key = self._camel_to_snake(key)
            if snake_key in style_fields:
                compatible[snake_key] = value
        
        return compatible
    
    def _camel_to_snake(self, name: str) -> str:
        """Convert camelCase to snake_case"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _validate_component(self):
        """
        Validate component data
        
        CLAUDE.md #2.1.1: Comprehensive validation
        """
        # Validate ID
        if not self.id or not isinstance(self.id, str):
            raise ValueError("Component ID must be a non-empty string")
        
        # Validate type
        if not self.type or not isinstance(self.type, str):
            raise ValueError("Component type must be a non-empty string")
        
        # Validate content type
        valid_content_types = {"text", "html", "markdown"}
        if self.content_type not in valid_content_types:
            raise ValueError(f"Content type must be one of {valid_content_types}")
        
        # Validate parent_id if set
        if self.parent_id is not None and not isinstance(self.parent_id, str):
            raise ValueError("Parent ID must be a string")
    
    def _set_defaults(self):
        """Set intelligent defaults based on component type"""
        
        # Set semantic role based on type if not specified
        if not self.semantic_role:
            semantic_mapping = {
                "heading": "heading",
                "button": "button", 
                "link": "link",
                "image": "img",
                "input": "textbox",
                "form": "form",
                "nav": "navigation",
                "navbar": "navigation",
                "header": "banner",
                "footer": "contentinfo",
                "sidebar": "complementary",
                "content": "main",
                "section": "region",
                "article": "article"
            }
            self.semantic_role = semantic_mapping.get(self.type)
        
        # Set name if not specified
        if not self.name:
            self.name = f"{self.type.title()}_{self.id[:8]}"
        
        # Add default ARIA attributes for accessibility
        self._add_default_aria_attributes()
    
    def _add_default_aria_attributes(self):
        """
        Add default ARIA attributes for accessibility
        
        CLAUDE.md #9.1: Accessibility compliance
        """
        if self.type == "button" and "aria-label" not in self.aria_attributes:
            if self.content:
                self.aria_attributes["aria-label"] = self.content
            elif self.name:
                self.aria_attributes["aria-label"] = self.name
        
        if self.type == "heading" and "aria-level" not in self.aria_attributes:
            level = self.properties.get("level", 2)
            self.aria_attributes["aria-level"] = str(level)
        
        if self.type == "image" and "alt" not in self.properties:
            # Warn about missing alt text
            import logging
            logging.warning(f"Image component {self.id} missing alt text")
    
    def sanitize_content(self) -> str:
        """
        Sanitize content for safe output
        
        CLAUDE.md #7.2: Content sanitization
        """
        if not self.content:
            return ""
        
        if self.content_type == "html":
            # For HTML content, perform XSS prevention
            return self._sanitize_html(self.content)
        else:
            # For text content, escape HTML entities
            return html.escape(str(self.content))
    
    def _sanitize_html(self, html_content: str) -> str:
        """
        Sanitize HTML content to prevent XSS
        
        CLAUDE.md #7.2: XSS prevention
        """
        if not html_content:
            return ""
        
        # Remove dangerous elements and attributes
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
            r'<form[^>]*>.*?</form>',
            r'on\w+\s*=\s*["\'][^"\']*["\']',  # Event handlers
            r'javascript:',
            r'data:text/html',
            r'vbscript:'
        ]
        
        sanitized = html_content
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        return sanitized
    
    def get_all_properties(self) -> Dict[str, Any]:
        """Get merged properties including ARIA attributes"""
        all_props = self.properties.copy()
        all_props.update(self.attributes)
        
        # Add ARIA attributes
        for key, value in self.aria_attributes.items():
            all_props[key] = value
        
        # Add data attributes
        for key, value in self.data_attributes.items():
            all_props[f"data-{key}"] = value
        
        return all_props
    
    def get_all_styles(self) -> Dict[str, Any]:
        """Get merged styles from both sources"""
        all_styles = {}
        
        if self.style:
            all_styles.update(asdict(self.style))
        
        all_styles.update(self.styles)
        
        return {k: v for k, v in all_styles.items() if v is not None}
    
    def get_css_classes(self) -> List[str]:
        """Get all CSS classes for this component"""
        classes = []
        
        if self.class_name:
            classes.extend(self.class_name.split())
        
        # Add responsive classes
        classes.extend(self.responsive_classes)
        
        # Add type-based class
        classes.append(f"canvas-{self.type}")
        
        return list(set(classes))  # Remove duplicates
    
    def has_children(self) -> bool:
        """Check if component has child components"""
        return len(self.children) > 0
    
    def get_descendant_count(self) -> int:
        """Get total number of descendant components"""
        count = len(self.children)
        for child in self.children:
            count += child.get_descendant_count()
        return count
    
    def find_child_by_id(self, child_id: str) -> Optional['ExportCompatibleComponent']:
        """Find a child component by ID (recursive)"""
        for child in self.children:
            if child.id == child_id:
                return child
            found = child.find_child_by_id(child_id)
            if found:
                return found
        return None
    
    def find_children_by_type(self, component_type: str) -> List['ExportCompatibleComponent']:
        """Find all child components of a specific type (recursive)"""
        matches = []
        for child in self.children:
            if child.type == component_type:
                matches.append(child)
            matches.extend(child.find_children_by_type(component_type))
        return matches
    
    def add_child(self, child: 'ExportCompatibleComponent', index: Optional[int] = None):
        """Add a child component"""
        child.parent_id = self.id
        if index is None:
            self.children.append(child)
        else:
            self.children.insert(index, child)
    
    def remove_child(self, child_id: str) -> bool:
        """Remove a child component by ID"""
        for i, child in enumerate(self.children):
            if child.id == child_id:
                child.parent_id = None
                self.children.pop(i)
                return True
        return False
    
    def move_child(self, child_id: str, new_index: int) -> bool:
        """Move a child to a new position"""
        child = None
        old_index = None
        
        for i, c in enumerate(self.children):
            if c.id == child_id:
                child = c
                old_index = i
                break
        
        if child and old_index is not None:
            self.children.pop(old_index)
            self.children.insert(new_index, child)
            return True
        
        return False
    
    def clone(self, deep: bool = True) -> 'ExportCompatibleComponent':
        """Create a copy of this component"""
        if deep:
            # Deep clone with new IDs
            data = self.to_dict()
            return self._clone_with_new_ids(data)
        else:
            # Shallow clone - same structure but new top-level ID
            new_comp = ExportCompatibleComponent.from_dict(self.to_dict())
            new_comp.id = str(uuid4())
            return new_comp
    
    def _clone_with_new_ids(self, data: Dict[str, Any]) -> 'ExportCompatibleComponent':
        """Recursively clone component tree with new IDs"""
        # Generate new ID
        data['id'] = str(uuid4())
        
        # Clone children recursively
        if 'children' in data:
            data['children'] = [
                self._clone_with_new_ids(child_data) 
                for child_data in data['children']
            ]
        
        return ExportCompatibleComponent.from_dict(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'content': self.content,
            'content_type': self.content_type,
            'children': [child.to_dict() for child in self.children],
            'parent_id': self.parent_id,
            'properties': self.properties,
            'attributes': self.attributes,
            'styles': self.styles,
            'style': asdict(self.style) if self.style else None,
            'semantic_role': self.semantic_role,
            'class_name': self.class_name,
            'aria_attributes': self.aria_attributes,
            'events': self.events,
            'responsive_styles': self.responsive_styles,
            'responsive_classes': self.responsive_classes,
            'data_attributes': self.data_attributes,
            'locked': self.locked,
            'visible': self.visible,
            'selected': self.selected,
            'expanded': self.expanded,
            'asset_id': self.asset_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExportCompatibleComponent':
        """Create component from dictionary"""
        # Handle children
        children_data = data.pop('children', [])
        style_data = data.pop('style', None)
        
        # Create component
        component = cls(**data)
        
        # Restore style if present
        if style_data:
            component.style = ComponentStyle(**style_data)
        
        # Restore children
        component.children = [cls.from_dict(child_data) for child_data in children_data]
        
        return component
    
    @classmethod
    def from_base_component(cls, base_component: BaseComponent) -> 'ExportCompatibleComponent':
        """Convert from base Canvas component"""
        return cls(
            id=base_component.id,
            type=base_component.type,
            name=base_component.name,
            content=base_component.content,
            children=[cls.from_base_component(child) for child in base_component.children],
            style=base_component.style,
            attributes=base_component.attributes,
            events=base_component.events,
            locked=base_component.locked,
            visible=base_component.visible,
            selected=base_component.selected,
            expanded=base_component.expanded
        )
    
    def to_base_component(self) -> BaseComponent:
        """Convert to base Canvas component"""
        return BaseComponent(
            id=self.id,
            type=self.type,
            name=self.name or "",
            content=self.content,
            children=[child.to_base_component() for child in self.children],
            style=self.style or ComponentStyle(),
            attributes=self.attributes,
            events=self.events,
            locked=self.locked,
            visible=self.visible,
            selected=self.selected,
            expanded=self.expanded
        )


# Type alias for backward compatibility
Component = ExportCompatibleComponent