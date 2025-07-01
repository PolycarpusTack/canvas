"""
Component Preview System
Generates live previews, property variations, responsive views, and code snippets.
"""

from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
import base64
import hashlib

from component_types import ComponentDefinition, PropertyDefinition, PropertyType, ValidationResult
from component_registry import ComponentRegistry, get_component_registry
from component_factory import ComponentFactory, get_component_factory
from models.component import Component


logger = logging.getLogger(__name__)


class PreviewFormat(Enum):
    """Supported preview formats"""
    PNG = "png"
    SVG = "svg"
    HTML = "html"
    WEBP = "webp"
    PDF = "pdf"


class PreviewSize(Enum):
    """Standard preview sizes"""
    THUMBNAIL = (120, 90)
    SMALL = (240, 180)
    MEDIUM = (480, 360)
    LARGE = (960, 720)
    FULL = (1920, 1080)
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height


class ResponsiveBreakpoint(Enum):
    """Responsive design breakpoints"""
    MOBILE = (375, 667)    # iPhone 8
    TABLET = (768, 1024)   # iPad
    DESKTOP = (1440, 900)  # Desktop
    LARGE = (1920, 1080)   # Large desktop
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height


class CodeFramework(Enum):
    """Supported code generation frameworks"""
    HTML = "html"
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    CSS = "css"
    TAILWIND = "tailwind"


@dataclass
class PreviewVariation:
    """A property variation for component preview"""
    name: str
    description: str
    properties: Dict[str, Any]
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    
    def get_display_name(self) -> str:
        """Get a user-friendly display name"""
        return self.name.replace('_', ' ').title()


@dataclass
class PreviewImage:
    """Generated preview image data"""
    format: PreviewFormat
    size: PreviewSize
    data: bytes
    generated_at: datetime
    cache_key: str
    file_size: int
    
    def to_data_url(self) -> str:
        """Convert to data URL for web display"""
        mime_type = f"image/{self.format.value}"
        encoded_data = base64.b64encode(self.data).decode('utf-8')
        return f"data:{mime_type};base64,{encoded_data}"
    
    def save_to_file(self, file_path: Path) -> bool:
        """Save preview to file"""
        try:
            with open(file_path, 'wb') as f:
                f.write(self.data)
            return True
        except Exception as e:
            logger.error(f"Failed to save preview to {file_path}: {e}")
            return False


@dataclass
class ComponentPreview:
    """Complete component preview with all variations"""
    component_id: str
    component_name: str
    primary_preview: PreviewImage
    variations: List[Tuple[PreviewVariation, PreviewImage]] = field(default_factory=list)
    responsive_previews: Dict[ResponsiveBreakpoint, PreviewImage] = field(default_factory=dict)
    code_snippets: Dict[CodeFramework, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    cache_duration: timedelta = field(default_factory=lambda: timedelta(hours=24))
    
    def is_cache_valid(self) -> bool:
        """Check if the preview cache is still valid"""
        return datetime.now() - self.generated_at < self.cache_duration
    
    def get_variation_by_name(self, name: str) -> Optional[Tuple[PreviewVariation, PreviewImage]]:
        """Get a variation by name"""
        return next(
            ((var, img) for var, img in self.variations if var.name == name),
            None
        )


@dataclass
class PreviewRenderConfig:
    """Configuration for preview rendering"""
    background_color: str = "#ffffff"
    show_guides: bool = False
    show_rulers: bool = False
    padding: int = 20
    quality: int = 90  # For JPEG/WebP
    scale: float = 1.0
    theme: str = "light"  # "light", "dark", "auto"
    include_shadows: bool = True
    include_animations: bool = False


class ComponentPreviewManager:
    """
    Manages component preview generation with caching and optimization.
    Provides live previews, variations, responsive views, and code generation.
    """
    
    def __init__(
        self,
        registry: Optional[ComponentRegistry] = None,
        factory: Optional[ComponentFactory] = None,
        cache_path: Optional[Path] = None
    ):
        """Initialize the preview manager"""
        self.registry = registry or get_component_registry()
        self.factory = factory or get_component_factory()
        self.cache_path = cache_path or Path("user_data/preview_cache")
        
        # Ensure cache directory exists
        self.cache_path.mkdir(parents=True, exist_ok=True)
        
        # Preview cache
        self.preview_cache: Dict[str, ComponentPreview] = {}
        self.variation_cache: Dict[str, List[PreviewVariation]] = {}
        self.code_cache: Dict[str, Dict[CodeFramework, str]] = {}
        
        # Configuration
        self.default_config = PreviewRenderConfig()
        self.max_cache_size = 1000  # Maximum cached previews
        self.max_cache_age = timedelta(days=7)
        
        # Load cached previews
        self._load_preview_cache()
        
        # Built-in variations
        self._initialize_built_in_variations()
        
        logger.info("Component preview manager initialized")
    
    def generate_preview(
        self,
        component_id: str,
        size: PreviewSize = PreviewSize.MEDIUM,
        format: PreviewFormat = PreviewFormat.PNG,
        config: Optional[PreviewRenderConfig] = None,
        force_regenerate: bool = False
    ) -> Optional[ComponentPreview]:
        """
        Generate a complete preview for a component.
        
        Args:
            component_id: Component to preview
            size: Preview size
            format: Preview format
            config: Render configuration
            force_regenerate: Force regeneration even if cached
            
        Returns:
            ComponentPreview object or None if failed
        """
        # Check cache first
        cache_key = self._generate_cache_key(component_id, size, format, config)
        
        if not force_regenerate and cache_key in self.preview_cache:
            cached_preview = self.preview_cache[cache_key]
            if cached_preview.is_cache_valid():
                logger.debug(f"Using cached preview for {component_id}")
                return cached_preview
        
        # Get component definition
        definition = self.registry.get(component_id)
        if not definition:
            logger.error(f"Component definition not found: {component_id}")
            return None
        
        render_config = config or self.default_config
        
        try:
            # Generate primary preview
            component = self.factory.create_component(component_id)
            primary_preview = self._render_component_preview(
                component, definition, size, format, render_config
            )
            
            if not primary_preview:
                return None
            
            # Create preview object
            preview = ComponentPreview(
                component_id=component_id,
                component_name=definition.name,
                primary_preview=primary_preview,
                metadata={
                    "component_type": definition.id,
                    "category": definition.category.name,
                    "render_config": {
                        "size": f"{size.width}x{size.height}",
                        "format": format.value,
                        "background": render_config.background_color,
                        "theme": render_config.theme
                    }
                }
            )
            
            # Generate variations
            variations = self.get_preview_variations(component_id)
            for variation in variations[:10]:  # Limit to first 10 variations
                try:
                    var_component = self.factory.create_component(
                        component_id, variation.properties
                    )
                    var_preview = self._render_component_preview(
                        var_component, definition, size, format, render_config
                    )
                    
                    if var_preview:
                        preview.variations.append((variation, var_preview))
                        
                except Exception as e:
                    logger.warning(f"Failed to generate variation '{variation.name}': {e}")
            
            # Generate responsive previews
            for breakpoint in ResponsiveBreakpoint:
                try:
                    responsive_size = PreviewSize((breakpoint.width, breakpoint.height))
                    responsive_preview = self._render_component_preview(
                        component, definition, responsive_size, format, render_config
                    )
                    
                    if responsive_preview:
                        preview.responsive_previews[breakpoint] = responsive_preview
                        
                except Exception as e:
                    logger.warning(f"Failed to generate responsive preview for {breakpoint.name}: {e}")
            
            # Generate code snippets
            preview.code_snippets = self.generate_code_snippets(component_id)
            
            # Cache the preview
            self.preview_cache[cache_key] = preview
            self._save_preview_cache(cache_key, preview)
            
            # Cleanup old cache entries
            self._cleanup_cache()
            
            logger.info(f"Generated preview for {component_id}")
            return preview
            
        except Exception as e:
            logger.error(f"Failed to generate preview for {component_id}: {e}")
            return None
    
    def get_preview_variations(self, component_id: str) -> List[PreviewVariation]:
        """Get all available variations for a component"""
        # Check cache first
        if component_id in self.variation_cache:
            return self.variation_cache[component_id]
        
        definition = self.registry.get(component_id)
        if not definition:
            return []
        
        variations = []
        
        # Generate variations based on component properties
        for prop in definition.properties:
            prop_variations = self._generate_property_variations(prop, definition)
            variations.extend(prop_variations)
        
        # Add component-specific variations
        component_variations = self._get_component_specific_variations(component_id)
        variations.extend(component_variations)
        
        # Cache the variations
        self.variation_cache[component_id] = variations
        
        return variations
    
    def generate_batch_previews(
        self,
        component_ids: List[str],
        size: PreviewSize = PreviewSize.SMALL,
        format: PreviewFormat = PreviewFormat.PNG,
        max_concurrent: int = 5
    ) -> Dict[str, ComponentPreview]:
        """Generate previews for multiple components efficiently"""
        results = {}
        
        # Process in batches to avoid overwhelming the system
        for i in range(0, len(component_ids), max_concurrent):
            batch = component_ids[i:i + max_concurrent]
            
            for component_id in batch:
                try:
                    preview = self.generate_preview(component_id, size, format)
                    if preview:
                        results[component_id] = preview
                except Exception as e:
                    logger.error(f"Failed to generate batch preview for {component_id}: {e}")
        
        logger.info(f"Generated batch previews for {len(results)}/{len(component_ids)} components")
        return results
    
    def generate_style_variations(
        self,
        component_id: str,
        style_properties: List[str],
        size: PreviewSize = PreviewSize.SMALL
    ) -> List[PreviewVariation]:
        """Generate variations for specific style properties"""
        definition = self.registry.get(component_id)
        if not definition:
            return []
        
        variations = []
        
        for prop_name in style_properties:
            prop = definition.get_property(prop_name)
            if not prop:
                continue
            
            prop_variations = self._generate_property_variations(prop, definition)
            variations.extend(prop_variations)
        
        return variations
    
    def generate_code_snippets(self, component_id: str) -> Dict[CodeFramework, str]:
        """Generate code snippets for different frameworks"""
        # Check cache first
        if component_id in self.code_cache:
            return self.code_cache[component_id]
        
        definition = self.registry.get(component_id)
        if not definition:
            return {}
        
        try:
            component = self.factory.create_component(component_id)
            snippets = {}
            
            # Generate HTML snippet
            snippets[CodeFramework.HTML] = self._generate_html_snippet(component, definition)
            
            # Generate React snippet
            snippets[CodeFramework.REACT] = self._generate_react_snippet(component, definition)
            
            # Generate Vue snippet
            snippets[CodeFramework.VUE] = self._generate_vue_snippet(component, definition)
            
            # Generate CSS snippet
            snippets[CodeFramework.CSS] = self._generate_css_snippet(component, definition)
            
            # Generate Tailwind snippet
            snippets[CodeFramework.TAILWIND] = self._generate_tailwind_snippet(component, definition)
            
            # Cache the snippets
            self.code_cache[component_id] = snippets
            
            return snippets
            
        except Exception as e:
            logger.error(f"Failed to generate code snippets for {component_id}: {e}")
            return {}
    
    def get_interactive_demo(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Generate interactive demo configuration"""
        definition = self.registry.get(component_id)
        if not definition:
            return None
        
        demo_config = {
            "component_id": component_id,
            "name": definition.name,
            "description": definition.description,
            "properties": [],
            "interactions": [],
            "examples": []
        }
        
        # Add editable properties
        for prop in definition.properties:
            if prop.editable:
                prop_config = {
                    "name": prop.name,
                    "type": prop.type.value,
                    "default": prop.default_value,
                    "description": prop.description,
                    "group": prop.group
                }
                
                # Add control configuration
                if prop.type == PropertyType.SELECT and prop.options:
                    prop_config["options"] = [
                        {"value": opt.value, "label": opt.label}
                        for opt in prop.options
                    ]
                elif prop.type == PropertyType.NUMBER and prop.validation:
                    prop_config["min"] = prop.validation.min_value
                    prop_config["max"] = prop.validation.max_value
                elif prop.type == PropertyType.COLOR:
                    prop_config["format"] = "hex"
                
                demo_config["properties"].append(prop_config)
        
        # Add common interactions
        demo_config["interactions"] = [
            {"type": "click", "description": "Click to interact"},
            {"type": "hover", "description": "Hover for effects"},
        ]
        
        # Add usage examples
        variations = self.get_preview_variations(component_id)
        demo_config["examples"] = [
            {
                "name": var.name,
                "description": var.description,
                "properties": var.properties
            }
            for var in variations[:5]  # Limit to 5 examples
        ]
        
        return demo_config
    
    def get_accessibility_info(self, component_id: str) -> Dict[str, Any]:
        """Get accessibility information for a component"""
        definition = self.registry.get(component_id)
        if not definition:
            return {}
        
        accessibility_info = {
            "component_id": component_id,
            "aria_support": [],
            "keyboard_navigation": [],
            "screen_reader_support": [],
            "color_contrast": {},
            "recommendations": []
        }
        
        # Analyze ARIA support based on component type
        if definition.id in ["button", "link"]:
            accessibility_info["aria_support"] = [
                "aria-label", "aria-describedby", "aria-disabled"
            ]
            accessibility_info["keyboard_navigation"] = [
                "Enter key activation", "Space key activation", "Tab navigation"
            ]
        elif definition.id in ["input", "textarea"]:
            accessibility_info["aria_support"] = [
                "aria-label", "aria-describedby", "aria-required", "aria-invalid"
            ]
            accessibility_info["keyboard_navigation"] = [
                "Tab navigation", "Arrow key navigation (if applicable)"
            ]
        elif definition.id == "modal":
            accessibility_info["aria_support"] = [
                "aria-modal", "aria-labelledby", "aria-describedby", "role=dialog"
            ]
            accessibility_info["keyboard_navigation"] = [
                "Escape key to close", "Tab trapping", "Focus management"
            ]
        
        # General recommendations
        accessibility_info["recommendations"] = [
            "Ensure sufficient color contrast (4.5:1 for normal text)",
            "Provide meaningful alt text for images",
            "Use semantic HTML elements",
            "Test with keyboard navigation",
            "Test with screen readers"
        ]
        
        return accessibility_info
    
    def clear_cache(self, component_id: Optional[str] = None):
        """Clear preview cache"""
        if component_id:
            # Clear cache for specific component
            keys_to_remove = [key for key in self.preview_cache.keys() if component_id in key]
            for key in keys_to_remove:
                del self.preview_cache[key]
            
            self.variation_cache.pop(component_id, None)
            self.code_cache.pop(component_id, None)
            
            logger.info(f"Cleared cache for component: {component_id}")
        else:
            # Clear all cache
            self.preview_cache.clear()
            self.variation_cache.clear()
            self.code_cache.clear()
            
            logger.info("Cleared all preview cache")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache usage statistics"""
        total_size = 0
        valid_count = 0
        
        for preview in self.preview_cache.values():
            total_size += preview.primary_preview.file_size
            for _, var_preview in preview.variations:
                total_size += var_preview.file_size
            for resp_preview in preview.responsive_previews.values():
                total_size += resp_preview.file_size
            
            if preview.is_cache_valid():
                valid_count += 1
        
        return {
            "total_cached_previews": len(self.preview_cache),
            "valid_cached_previews": valid_count,
            "total_cache_size_bytes": total_size,
            "total_cache_size_mb": round(total_size / (1024 * 1024), 2),
            "cached_variations": len(self.variation_cache),
            "cached_code_snippets": len(self.code_cache),
            "cache_hit_ratio": valid_count / len(self.preview_cache) if self.preview_cache else 0
        }
    
    # Private Methods
    
    def _render_component_preview(
        self,
        component: Component,
        definition: ComponentDefinition,
        size: PreviewSize,
        format: PreviewFormat,
        config: PreviewRenderConfig
    ) -> Optional[PreviewImage]:
        """Render a component to an image preview"""
        try:
            # This is a mock implementation
            # In a real system, this would use a headless browser or rendering engine
            
            # Generate mock image data
            mock_image_data = self._generate_mock_image(
                component, definition, size, format, config
            )
            
            cache_key = self._generate_cache_key(
                definition.id, size, format, config
            )
            
            preview_image = PreviewImage(
                format=format,
                size=size,
                data=mock_image_data,
                generated_at=datetime.now(),
                cache_key=cache_key,
                file_size=len(mock_image_data)
            )
            
            return preview_image
            
        except Exception as e:
            logger.error(f"Failed to render component preview: {e}")
            return None
    
    def _generate_mock_image(
        self,
        component: Component,
        definition: ComponentDefinition,
        size: PreviewSize,
        format: PreviewFormat,
        config: PreviewRenderConfig
    ) -> bytes:
        """Generate mock image data (placeholder implementation)"""
        # This is a placeholder implementation
        # In a real system, this would use a proper rendering engine
        
        # Create a simple mock image representation
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    margin: 0;
                    padding: {config.padding}px;
                    background-color: {config.background_color};
                    font-family: Arial, sans-serif;
                    width: {size.width}px;
                    height: {size.height}px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .component {{
                    border: 2px solid #ccc;
                    border-radius: 8px;
                    padding: 16px;
                    background: white;
                    text-align: center;
                    min-width: 120px;
                    min-height: 60px;
                }}
                .component-name {{
                    font-weight: bold;
                    margin-bottom: 8px;
                }}
                .component-type {{
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="component">
                <div class="component-name">{definition.name}</div>
                <div class="component-type">{definition.id}</div>
            </div>
        </body>
        </html>
        """
        
        # In a real implementation, this would convert HTML to image
        # For now, return the HTML content as bytes
        return html_content.encode('utf-8')
    
    def _generate_property_variations(
        self,
        prop: PropertyDefinition,
        definition: ComponentDefinition
    ) -> List[PreviewVariation]:
        """Generate variations for a single property"""
        variations = []
        
        if prop.type == PropertyType.SELECT and prop.options:
            # Create variations for each option
            for option in prop.options:
                variation = PreviewVariation(
                    name=f"{prop.name}_{option.value}",
                    description=f"{prop.name.title()}: {option.label}",
                    properties={prop.name: option.value},
                    tags=[prop.group, prop.type.value],
                    category=prop.group
                )
                variations.append(variation)
        
        elif prop.type == PropertyType.BOOLEAN:
            # Create true/false variations
            for value, label in [(True, "Enabled"), (False, "Disabled")]:
                variation = PreviewVariation(
                    name=f"{prop.name}_{str(value).lower()}",
                    description=f"{prop.name.title()}: {label}",
                    properties={prop.name: value},
                    tags=[prop.group, "boolean"],
                    category=prop.group
                )
                variations.append(variation)
        
        elif prop.type == PropertyType.COLOR:
            # Create color variations
            colors = [
                ("#007bff", "Primary Blue"),
                ("#28a745", "Success Green"),
                ("#dc3545", "Danger Red"),
                ("#ffc107", "Warning Yellow"),
                ("#6c757d", "Secondary Gray")
            ]
            
            for color, label in colors:
                variation = PreviewVariation(
                    name=f"{prop.name}_{color.replace('#', '')}",
                    description=f"{prop.name.title()}: {label}",
                    properties={prop.name: color},
                    tags=[prop.group, "color"],
                    category=prop.group
                )
                variations.append(variation)
        
        elif prop.type == PropertyType.SIZE:
            # Create size variations
            sizes = [
                ("sm", "Small"),
                ("md", "Medium"),
                ("lg", "Large"),
                ("xl", "Extra Large")
            ]
            
            for size, label in sizes:
                variation = PreviewVariation(
                    name=f"{prop.name}_{size}",
                    description=f"{prop.name.title()}: {label}",
                    properties={prop.name: size},
                    tags=[prop.group, "size"],
                    category=prop.group
                )
                variations.append(variation)
        
        return variations
    
    def _get_component_specific_variations(self, component_id: str) -> List[PreviewVariation]:
        """Get variations specific to a component type"""
        variations = []
        
        # Button variations
        if component_id == "button":
            button_variations = [
                PreviewVariation(
                    name="button_primary",
                    description="Primary button style",
                    properties={"variant": "primary", "text": "Primary Button"},
                    tags=["style", "primary"],
                    category="appearance"
                ),
                PreviewVariation(
                    name="button_secondary",
                    description="Secondary button style",
                    properties={"variant": "secondary", "text": "Secondary Button"},
                    tags=["style", "secondary"],
                    category="appearance"
                ),
                PreviewVariation(
                    name="button_disabled",
                    description="Disabled button state",
                    properties={"disabled": True, "text": "Disabled Button"},
                    tags=["state", "disabled"],
                    category="state"
                ),
                PreviewVariation(
                    name="button_loading",
                    description="Loading button state",
                    properties={"loading": True, "text": "Loading..."},
                    tags=["state", "loading"],
                    category="state"
                )
            ]
            variations.extend(button_variations)
        
        # Input variations
        elif component_id == "input":
            input_variations = [
                PreviewVariation(
                    name="input_text",
                    description="Text input",
                    properties={"type": "text", "placeholder": "Enter text..."},
                    tags=["type", "text"],
                    category="type"
                ),
                PreviewVariation(
                    name="input_email",
                    description="Email input",
                    properties={"type": "email", "placeholder": "Enter email..."},
                    tags=["type", "email"],
                    category="type"
                ),
                PreviewVariation(
                    name="input_password",
                    description="Password input",
                    properties={"type": "password", "placeholder": "Enter password..."},
                    tags=["type", "password"],
                    category="type"
                ),
                PreviewVariation(
                    name="input_error",
                    description="Input with error state",
                    properties={"error": True, "placeholder": "Invalid input"},
                    tags=["state", "error"],
                    category="state"
                )
            ]
            variations.extend(input_variations)
        
        # Card variations
        elif component_id == "card":
            card_variations = [
                PreviewVariation(
                    name="card_basic",
                    description="Basic card layout",
                    properties={"title": "Card Title", "content": "Card content goes here..."},
                    tags=["layout", "basic"],
                    category="layout"
                ),
                PreviewVariation(
                    name="card_image",
                    description="Card with image",
                    properties={
                        "title": "Image Card", 
                        "content": "Card with image header",
                        "image": "https://via.placeholder.com/300x150"
                    },
                    tags=["layout", "image"],
                    category="layout"
                ),
                PreviewVariation(
                    name="card_actions",
                    description="Card with action buttons",
                    properties={
                        "title": "Action Card",
                        "content": "Card with action buttons",
                        "actions": ["Edit", "Delete"]
                    },
                    tags=["layout", "actions"],
                    category="layout"
                )
            ]
            variations.extend(card_variations)
        
        return variations
    
    def _generate_html_snippet(self, component: Component, definition: ComponentDefinition) -> str:
        """Generate HTML code snippet"""
        return component.to_html()
    
    def _generate_react_snippet(self, component: Component, definition: ComponentDefinition) -> str:
        """Generate React code snippet"""
        component_name = definition.name.replace(' ', '')
        
        # Generate props
        props = []
        for key, value in component.attributes.items():
            if isinstance(value, str):
                props.append(f'{key}="{value}"')
            elif isinstance(value, bool):
                if value:
                    props.append(key)
                else:
                    props.append(f'{key}={{{str(value).lower()}}}')
            else:
                props.append(f'{key}={{{repr(value)}}}')
        
        props_str = ' '.join(props)
        
        if component.children or component.content:
            content = component.content or "Children components here"
            return f"""<{component_name} {props_str}>
  {content}
</{component_name}>"""
        else:
            return f"<{component_name} {props_str} />"
    
    def _generate_vue_snippet(self, component: Component, definition: ComponentDefinition) -> str:
        """Generate Vue code snippet"""
        component_name = definition.name.lower().replace(' ', '-')
        
        # Generate props
        props = []
        for key, value in component.attributes.items():
            if isinstance(value, str):
                props.append(f'{key}="{value}"')
            elif isinstance(value, bool):
                props.append(f':{key}="{str(value).lower()}"')
            else:
                props.append(f':{key}="{repr(value)}"')
        
        props_str = ' '.join(props)
        
        if component.children or component.content:
            content = component.content or "<!-- Children components here -->"
            return f"""<{component_name} {props_str}>
  {content}
</{component_name}>"""
        else:
            return f"<{component_name} {props_str} />"
    
    def _generate_css_snippet(self, component: Component, definition: ComponentDefinition) -> str:
        """Generate CSS code snippet"""
        css_class = f".{definition.id}"
        
        css_rules = []
        if component.style:
            style_dict = component.style.__dict__
            for key, value in style_dict.items():
                if value is not None:
                    css_key = key.replace('_', '-')
                    css_rules.append(f"  {css_key}: {value};")
        
        if css_rules:
            return f"""{css_class} {{
{chr(10).join(css_rules)}
}}"""
        else:
            return f"""{css_class} {{
  /* Add your styles here */
}}"""
    
    def _generate_tailwind_snippet(self, component: Component, definition: ComponentDefinition) -> str:
        """Generate Tailwind CSS classes"""
        classes = []
        
        if component.style:
            # Map CSS properties to Tailwind classes
            style_dict = component.style.__dict__
            
            # Display
            if style_dict.get('display') == 'flex':
                classes.append('flex')
            elif style_dict.get('display') == 'grid':
                classes.append('grid')
            elif style_dict.get('display') == 'block':
                classes.append('block')
            
            # Flex properties
            if style_dict.get('justify_content') == 'center':
                classes.append('justify-center')
            elif style_dict.get('justify_content') == 'space-between':
                classes.append('justify-between')
            
            if style_dict.get('align_items') == 'center':
                classes.append('items-center')
            
            # Spacing
            if style_dict.get('padding'):
                classes.append('p-4')  # Default padding
            if style_dict.get('margin'):
                classes.append('m-4')  # Default margin
            
            # Colors
            if style_dict.get('background_color'):
                if 'blue' in str(style_dict['background_color']).lower():
                    classes.append('bg-blue-500')
                elif 'red' in str(style_dict['background_color']).lower():
                    classes.append('bg-red-500')
                elif 'green' in str(style_dict['background_color']).lower():
                    classes.append('bg-green-500')
                else:
                    classes.append('bg-gray-100')
            
            # Border radius
            if style_dict.get('border_radius'):
                classes.append('rounded-lg')
        
        # Default classes based on component type
        if definition.id == 'button':
            classes.extend(['px-4', 'py-2', 'rounded', 'font-medium'])
        elif definition.id == 'card':
            classes.extend(['bg-white', 'shadow-md', 'rounded-lg', 'p-6'])
        elif definition.id == 'input':
            classes.extend(['border', 'border-gray-300', 'rounded', 'px-3', 'py-2'])
        
        return ' '.join(classes) if classes else 'your-tailwind-classes'
    
    def _generate_cache_key(
        self,
        component_id: str,
        size: PreviewSize,
        format: PreviewFormat,
        config: Optional[PreviewRenderConfig]
    ) -> str:
        """Generate cache key for preview"""
        config_str = ""
        if config:
            config_str = f"{config.background_color}_{config.theme}_{config.scale}"
        
        key_string = f"{component_id}_{size.width}x{size.height}_{format.value}_{config_str}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _initialize_built_in_variations(self):
        """Initialize built-in component variations"""
        # This would contain pre-defined variations for common components
        # For now, variations are generated dynamically
        pass
    
    def _load_preview_cache(self):
        """Load preview cache from storage"""
        try:
            cache_file = self.cache_path / "preview_cache.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Note: In a real implementation, this would deserialize
                # the full preview objects from storage
                logger.info(f"Loaded {len(cache_data)} cached previews")
                
        except Exception as e:
            logger.error(f"Failed to load preview cache: {e}")
    
    def _save_preview_cache(self, cache_key: str, preview: ComponentPreview):
        """Save preview to cache storage"""
        try:
            # In a real implementation, this would serialize and save
            # the preview data to persistent storage
            cache_file = self.cache_path / f"{cache_key}.json"
            
            cache_data = {
                "component_id": preview.component_id,
                "generated_at": preview.generated_at.isoformat(),
                "metadata": preview.metadata
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save preview cache: {e}")
    
    def _cleanup_cache(self):
        """Clean up old cache entries"""
        if len(self.preview_cache) <= self.max_cache_size:
            return
        
        # Remove oldest entries
        sorted_previews = sorted(
            self.preview_cache.items(),
            key=lambda x: x[1].generated_at
        )
        
        to_remove = len(self.preview_cache) - self.max_cache_size
        for i in range(to_remove):
            cache_key, _ = sorted_previews[i]
            del self.preview_cache[cache_key]
        
        logger.info(f"Cleaned up {to_remove} old cache entries")


# Global preview manager instance
_preview_manager_instance: Optional[ComponentPreviewManager] = None


def get_component_preview_manager() -> ComponentPreviewManager:
    """Get the global component preview manager instance"""
    global _preview_manager_instance
    if _preview_manager_instance is None:
        _preview_manager_instance = ComponentPreviewManager()
    return _preview_manager_instance