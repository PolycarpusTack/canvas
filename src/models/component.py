"""Component-related data models"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from uuid import uuid4


@dataclass
class ComponentStyle:
    """Component styling properties"""
    # Layout
    width: Optional[str] = None
    height: Optional[str] = None
    margin: Optional[str] = None
    padding: Optional[str] = None
    
    # Position
    position: str = "relative"
    top: Optional[str] = None
    right: Optional[str] = None
    bottom: Optional[str] = None
    left: Optional[str] = None
    
    # Display
    display: str = "block"
    flex_direction: Optional[str] = None
    justify_content: Optional[str] = None
    align_items: Optional[str] = None
    gap: Optional[str] = None
    grid_template_columns: Optional[str] = None
    grid_template_rows: Optional[str] = None
    
    # Appearance
    background_color: Optional[str] = None
    color: Optional[str] = None
    border: Optional[str] = None
    border_radius: Optional[str] = None
    box_shadow: Optional[str] = None
    opacity: float = 1.0
    
    # Typography
    font_family: Optional[str] = None
    font_size: Optional[str] = None
    font_weight: Optional[str] = None
    line_height: Optional[str] = None
    text_align: Optional[str] = None
    
    def to_css(self) -> str:
        """Convert to CSS string"""
        css_rules = []
        for key, value in asdict(self).items():
            if value is not None:
                css_key = key.replace('_', '-')
                css_rules.append(f"{css_key}: {value}")
        return "; ".join(css_rules)


@dataclass
class Component:
    """Base component model"""
    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = "div"
    name: str = "Component"
    content: Optional[str] = None
    children: List['Component'] = field(default_factory=list)
    style: ComponentStyle = field(default_factory=ComponentStyle)
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: Dict[str, str] = field(default_factory=dict)
    
    # Editor metadata
    locked: bool = False
    visible: bool = True
    selected: bool = False
    expanded: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "content": self.content,
            "children": [child.to_dict() for child in self.children],
            "style": asdict(self.style),
            "attributes": self.attributes,
            "events": self.events,
            "locked": self.locked,
            "visible": self.visible
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Component':
        """Create from dictionary"""
        style_data = data.pop('style', {})
        children_data = data.pop('children', [])
        
        component = cls(**data)
        component.style = ComponentStyle(**style_data)
        component.children = [cls.from_dict(child) for child in children_data]
        
        return component
    
    def to_html(self) -> str:
        """Convert to HTML string"""
        # Build attributes
        attrs = []
        if self.id:
            attrs.append(f'id="{self.id}"')
        
        if self.style:
            style_str = self.style.to_css()
            if style_str:
                attrs.append(f'style="{style_str}"')
        
        for key, value in self.attributes.items():
            attrs.append(f'{key}="{value}"')
        
        attrs_str = " ".join(attrs)
        
        # Build content
        if self.children:
            children_html = "\n".join(child.to_html() for child in self.children)
            return f"<{self.type} {attrs_str}>\n{children_html}\n</{self.type}>"
        elif self.content:
            return f"<{self.type} {attrs_str}>{self.content}</{self.type}>"
        else:
            return f"<{self.type} {attrs_str}></{self.type}>"


@dataclass
class ComponentCategory:
    """Component category for the component panel"""
    name: str
    icon: str
    components: List[Dict[str, str]]
    expanded: bool = True


@dataclass
class ComponentTemplate:
    """Predefined component template"""
    id: str
    name: str
    description: str
    thumbnail: Optional[str] = None
    category: str = "Custom"
    component: Optional[Component] = None
    
    def create_instance(self) -> Component:
        """Create a new instance of this template"""
        if self.component:
            # Deep copy the component
            return Component.from_dict(self.component.to_dict())
        return Component(name=self.name)