"""
Component Renderer for Canvas
Converts component models to visual representations with accurate style mapping
Following CLAUDE.md guidelines for extensible rendering system
"""

import flet as ft
from typing import Optional, Dict, Any, List, Tuple, Union
import logging
import re

from models.component import Component, ComponentStyle
from .render_cache import RenderCache
from .canvas_renderer import RenderContext

logger = logging.getLogger(__name__)


class ComponentRenderer:
    """
    Handles component-to-visual conversion
    CLAUDE.md #3.4: Follow established patterns
    CLAUDE.md #7.2: Output encoding for safety
    CLAUDE.md #1.2: DRY - Reusable rendering logic
    """
    
    def __init__(self, render_cache: Optional[RenderCache] = None):
        """Initialize component renderer"""
        self.render_cache = render_cache
        
        # CSS unit parsers
        self._unit_parsers = {
            'px': self._parse_px,
            '%': self._parse_percent,
            'rem': self._parse_rem,
            'em': self._parse_em,
            'vw': self._parse_vw,
            'vh': self._parse_vh,
            'auto': lambda v, c: None
        }
        
        # Component type renderers
        self._type_renderers = {
            'text': self._render_text_component,
            'heading': self._render_heading_component,
            'paragraph': self._render_paragraph_component,
            'button': self._render_button_component,
            'image': self._render_image_component,
            'input': self._render_input_component,
            'container': self._render_container_component,
            'div': self._render_container_component,
            'row': self._render_row_component,
            'column': self._render_column_component,
            'form': self._render_form_component
        }
        
        logger.info("ComponentRenderer initialized")
    
    def render_component(
        self,
        component: Component,
        context: RenderContext
    ) -> ft.Control:
        """
        Main entry point for rendering a component
        Uses cache if available
        """
        # Try cache first
        if self.render_cache:
            control, was_cached = self.render_cache.get_or_render(
                component,
                lambda c: self._do_render_component(c, context)
            )
            if was_cached:
                # Apply context-specific modifications (selection, hover)
                control = self._apply_context_state(control, context)
            return control
        
        # Direct render without cache
        return self._do_render_component(component, context)
    
    def _do_render_component(
        self,
        component: Component,
        context: RenderContext
    ) -> ft.Control:
        """Actual rendering logic"""
        # Get type-specific renderer
        renderer = self._type_renderers.get(
            component.type,
            self._render_generic_component
        )
        
        # Render component
        control = renderer(component, context)
        
        # Apply common properties
        control = self._apply_common_properties(control, component, context)
        
        # Apply visual effects
        control = self._apply_visual_effects(control, component)
        
        # Apply interaction handlers
        control = self._apply_interactions(control, component, context)
        
        return control
    
    def _render_text_component(
        self, 
        component: Component, 
        context: RenderContext
    ) -> ft.Control:
        """Render text component"""
        text_content = component.properties.get('text', '')
        
        return ft.Text(
            value=self._sanitize_text(text_content),
            size=self._parse_font_size(component.style.font_size, context),
            weight=self._parse_font_weight(component.style.font_weight),
            color=component.style.color or "#374151",
            font_family=component.style.font_family,
            text_align=self._parse_text_align(component.style.text_align),
            max_lines=component.properties.get('maxLines'),
            overflow=ft.TextOverflow.ELLIPSIS if component.properties.get('ellipsis') else None
        )
    
    def _render_heading_component(
        self, 
        component: Component, 
        context: RenderContext
    ) -> ft.Control:
        """Render heading component (h1-h6)"""
        level = component.properties.get('level', 1)
        text_content = component.properties.get('text', '')
        
        # Default heading sizes
        heading_sizes = {
            1: 32, 2: 28, 3: 24, 4: 20, 5: 18, 6: 16
        }
        
        default_size = heading_sizes.get(level, 20)
        
        return ft.Text(
            value=self._sanitize_text(text_content),
            size=self._parse_font_size(component.style.font_size, context) or default_size,
            weight=ft.FontWeight.BOLD,
            color=component.style.color or "#1F2937",
            font_family=component.style.font_family
        )
    
    def _render_paragraph_component(
        self, 
        component: Component, 
        context: RenderContext
    ) -> ft.Control:
        """Render paragraph component"""
        text_content = component.properties.get('text', '')
        
        return ft.Text(
            value=self._sanitize_text(text_content),
            size=self._parse_font_size(component.style.font_size, context) or 14,
            color=component.style.color or "#4B5563",
            font_family=component.style.font_family,
            text_align=self._parse_text_align(component.style.text_align)
        )
    
    def _render_button_component(
        self, 
        component: Component, 
        context: RenderContext
    ) -> ft.Control:
        """Render button component"""
        text = component.properties.get('text', 'Button')
        variant = component.properties.get('variant', 'primary')
        
        # Button styling based on variant
        if variant == 'primary':
            button = ft.ElevatedButton(
                text=self._sanitize_text(text),
                bgcolor=component.style.background_color or "#5E6AD2",
                color=component.style.color or "white"
            )
        elif variant == 'secondary':
            button = ft.OutlinedButton(
                text=self._sanitize_text(text),
                style=ft.ButtonStyle(
                    color=component.style.color or "#5E6AD2",
                    side=ft.BorderSide(1, component.style.border_color or "#5E6AD2")
                )
            )
        else:  # text variant
            button = ft.TextButton(
                text=self._sanitize_text(text),
                style=ft.ButtonStyle(
                    color=component.style.color or "#5E6AD2"
                )
            )
        
        # Apply icon if present
        icon_name = component.properties.get('icon')
        if icon_name:
            button.icon = self._get_icon(icon_name)
        
        return button
    
    def _render_image_component(
        self, 
        component: Component, 
        context: RenderContext
    ) -> ft.Control:
        """Render image component"""
        src = component.properties.get('src', '')
        alt = component.properties.get('alt', '')
        
        # Create image with error handling
        image = ft.Image(
            src=src,
            width=self._parse_dimension(component.style.width, context),
            height=self._parse_dimension(component.style.height, context),
            fit=self._parse_image_fit(component.properties.get('objectFit', 'contain')),
            error_content=ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.BROKEN_IMAGE, size=32, color="#9CA3AF"),
                    ft.Text(alt or "Image failed to load", size=12, color="#6B7280")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                alignment=ft.alignment.center,
                bgcolor="#F3F4F6"
            )
        )
        
        return image
    
    def _render_input_component(
        self, 
        component: Component, 
        context: RenderContext
    ) -> ft.Control:
        """Render input component"""
        input_type = component.properties.get('type', 'text')
        placeholder = component.properties.get('placeholder', '')
        value = component.properties.get('value', '')
        
        # Create appropriate input based on type
        if input_type == 'textarea':
            input_control = ft.TextField(
                value=value,
                hint_text=placeholder,
                multiline=True,
                min_lines=3,
                max_lines=10
            )
        elif input_type == 'password':
            input_control = ft.TextField(
                value=value,
                hint_text=placeholder,
                password=True,
                can_reveal_password=True
            )
        elif input_type == 'number':
            input_control = ft.TextField(
                value=value,
                hint_text=placeholder,
                keyboard_type=ft.KeyboardType.NUMBER
            )
        else:
            input_control = ft.TextField(
                value=value,
                hint_text=placeholder
            )
        
        # Apply styling
        input_control.border_color = component.style.border_color or "#E5E7EB"
        input_control.focused_border_color = "#5E6AD2"
        input_control.text_size = self._parse_font_size(component.style.font_size, context) or 14
        
        return input_control
    
    def _render_container_component(
        self, 
        component: Component, 
        context: RenderContext
    ) -> ft.Control:
        """Render generic container (div)"""
        # Render children if any
        content = None
        if component.children:
            child_controls = []
            for child in component.children:
                child_context = RenderContext(
                    component=child,
                    parent=context,
                    depth=context.depth + 1,
                    zoom_level=context.zoom_level,
                    viewport_offset=context.viewport_offset
                )
                child_control = self.render_component(child, child_context)
                if child_control:
                    child_controls.append(child_control)
            
            # Apply layout
            if component.style.display == "flex":
                content = self._create_flex_layout(component, child_controls)
            elif component.style.display == "grid":
                content = self._create_grid_layout(component, child_controls)
            else:
                content = ft.Column(controls=child_controls, spacing=0)
        
        return ft.Container(content=content)
    
    def _render_row_component(
        self, 
        component: Component, 
        context: RenderContext
    ) -> ft.Control:
        """Render row component"""
        child_controls = self._render_children(component, context)
        
        return ft.Row(
            controls=child_controls,
            alignment=self._parse_main_axis_alignment(
                component.style.justify_content or "start"
            ),
            vertical_alignment=self._parse_cross_axis_alignment(
                component.style.align_items or "start"
            ),
            spacing=self._parse_dimension(component.style.gap, context) or 0,
            wrap=component.style.flex_wrap == "wrap"
        )
    
    def _render_column_component(
        self, 
        component: Component, 
        context: RenderContext
    ) -> ft.Control:
        """Render column component"""
        child_controls = self._render_children(component, context)
        
        return ft.Column(
            controls=child_controls,
            alignment=self._parse_main_axis_alignment(
                component.style.justify_content or "start"
            ),
            horizontal_alignment=self._parse_cross_axis_alignment(
                component.style.align_items or "start"
            ),
            spacing=self._parse_dimension(component.style.gap, context) or 0
        )
    
    def _render_form_component(
        self, 
        component: Component, 
        context: RenderContext
    ) -> ft.Control:
        """Render form component"""
        # Forms are rendered as columns with special handling
        return self._render_column_component(component, context)
    
    def _render_generic_component(
        self, 
        component: Component, 
        context: RenderContext
    ) -> ft.Control:
        """Fallback renderer for unknown component types"""
        logger.warning(f"Unknown component type: {component.type}")
        
        return ft.Container(
            content=ft.Text(
                f"[{component.type}]",
                size=12,
                color="#9CA3AF"
            ),
            border=ft.border.all(1, "#E5E7EB"),
            padding=4
        )
    
    def _render_children(
        self, 
        component: Component, 
        context: RenderContext
    ) -> List[ft.Control]:
        """Render component children"""
        child_controls = []
        
        for child in component.children:
            child_context = RenderContext(
                component=child,
                parent=context,
                depth=context.depth + 1,
                zoom_level=context.zoom_level,
                viewport_offset=context.viewport_offset,
                parent_width=self._parse_dimension(component.style.width, context),
                parent_height=self._parse_dimension(component.style.height, context)
            )
            
            child_control = self.render_component(child, child_context)
            if child_control:
                child_controls.append(child_control)
        
        return child_controls
    
    def _apply_common_properties(
        self,
        control: ft.Control,
        component: Component,
        context: RenderContext
    ) -> ft.Control:
        """Apply common properties to any control"""
        # Wrap in container to apply positioning and styling
        container = ft.Container(
            content=control,
            key=component.id,  # For efficient updates
            
            # Dimensions
            width=self._parse_dimension(component.style.width, context),
            height=self._parse_dimension(component.style.height, context),
            
            # Positioning
            left=self._parse_dimension(component.style.left, context) if component.style.position == "absolute" else None,
            top=self._parse_dimension(component.style.top, context) if component.style.position == "absolute" else None,
            right=self._parse_dimension(component.style.right, context) if component.style.position == "absolute" else None,
            bottom=self._parse_dimension(component.style.bottom, context) if component.style.position == "absolute" else None,
            
            # Spacing
            padding=self._parse_padding(component.style.padding, context),
            margin=self._parse_margin(component.style.margin, context),
            
            # Appearance
            bgcolor=component.style.background_color,
            border_radius=self._parse_border_radius(component.style.border_radius, context),
            border=self._parse_border(component.style, context),
            
            # Effects
            opacity=component.style.opacity,
            shadow=self._parse_box_shadow(component.style.box_shadow) if component.style.box_shadow else None,
            
            # Behavior
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS if component.style.overflow == "hidden" else None,
            animate=self._should_animate(component)
        )
        
        return container
    
    def _apply_context_state(
        self,
        control: ft.Control,
        context: RenderContext
    ) -> ft.Control:
        """Apply context-specific state (selection, hover)"""
        if not isinstance(control, ft.Container):
            control = ft.Container(content=control)
        
        if context.is_selected:
            # Add selection border
            control.border = ft.border.all(2, "#5E6AD2")
        
        if context.is_hovered:
            # Add hover effect
            control.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color="#0000001A",
                offset=ft.Offset(0, 2)
            )
        
        return control
    
    def _apply_visual_effects(
        self,
        control: ft.Control,
        component: Component
    ) -> ft.Control:
        """Apply visual effects like transforms, filters"""
        # Future: Add transform support (rotate, scale, skew)
        # Future: Add filter support (blur, brightness, etc)
        return control
    
    def _apply_interactions(
        self,
        control: ft.Control,
        component: Component,
        context: RenderContext
    ) -> ft.Control:
        """Apply interaction handlers"""
        # These will be connected to the interaction system
        # For now, just mark the component as interactive
        if not isinstance(control, ft.Container):
            control = ft.Container(content=control)
        
        # Make interactive if not locked
        if not component.editor_locked:
            control.on_click = lambda e: self._handle_click(component, context)
            control.on_hover = lambda e: self._handle_hover(component, context, e)
        
        return control
    
    # CSS Parsing Methods
    
    def _parse_dimension(
        self, 
        value: Optional[Union[str, int, float]], 
        context: RenderContext
    ) -> Optional[float]:
        """Parse CSS dimension value"""
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Extract unit
            match = re.match(r'^([\d.]+)(\w+)?$', value.strip())
            if match:
                number = float(match.group(1))
                unit = match.group(2) or 'px'
                
                parser = self._unit_parsers.get(unit, self._parse_px)
                return parser(number, context)
        
        return None
    
    def _parse_px(self, value: float, context: RenderContext) -> float:
        """Parse pixel value"""
        return value
    
    def _parse_percent(self, value: float, context: RenderContext) -> Optional[float]:
        """Parse percentage value"""
        if context.parent_width is not None:
            return (value / 100) * context.parent_width
        return None
    
    def _parse_rem(self, value: float, context: RenderContext) -> float:
        """Parse rem value (root em)"""
        return value * 16  # Base font size
    
    def _parse_em(self, value: float, context: RenderContext) -> float:
        """Parse em value"""
        parent_font_size = 16  # Default
        if context.parent and hasattr(context.parent.component.style, 'font_size'):
            parent_font_size = self._parse_font_size(
                context.parent.component.style.font_size, 
                context.parent
            ) or 16
        return value * parent_font_size
    
    def _parse_vw(self, value: float, context: RenderContext) -> float:
        """Parse viewport width value"""
        # Future: Get actual viewport width
        return value * 12  # Approximate for now
    
    def _parse_vh(self, value: float, context: RenderContext) -> float:
        """Parse viewport height value"""
        # Future: Get actual viewport height
        return value * 8  # Approximate for now
    
    def _parse_padding(
        self, 
        padding: Optional[str], 
        context: RenderContext
    ) -> Optional[ft.Padding]:
        """Parse CSS padding"""
        if not padding:
            return None
        
        values = padding.strip().split()
        parsed = [self._parse_dimension(v, context) or 0 for v in values]
        
        if len(parsed) == 1:
            return ft.padding.all(parsed[0])
        elif len(parsed) == 2:
            return ft.padding.symmetric(vertical=parsed[0], horizontal=parsed[1])
        elif len(parsed) == 4:
            return ft.padding.only(
                top=parsed[0], 
                right=parsed[1], 
                bottom=parsed[2], 
                left=parsed[3]
            )
        
        return None
    
    def _parse_margin(
        self, 
        margin: Optional[str], 
        context: RenderContext
    ) -> Optional[ft.Margin]:
        """Parse CSS margin"""
        # Similar to padding
        return self._parse_padding(margin, context)
    
    def _parse_border_radius(
        self, 
        radius: Optional[str], 
        context: RenderContext
    ) -> Optional[ft.BorderRadius]:
        """Parse CSS border radius"""
        if not radius:
            return None
        
        value = self._parse_dimension(radius, context)
        if value is not None:
            return ft.border_radius.all(value)
        
        return None
    
    def _parse_border(
        self, 
        style: ComponentStyle, 
        context: RenderContext
    ) -> Optional[ft.Border]:
        """Parse CSS border"""
        if not style.border:
            return None
        
        # Simple border parsing for now
        width = 1
        color = style.border_color or "#E5E7EB"
        
        return ft.border.all(width, color)
    
    def _parse_box_shadow(self, shadow: str) -> Optional[ft.BoxShadow]:
        """Parse CSS box shadow"""
        # Simple shadow parsing
        return ft.BoxShadow(
            spread_radius=0,
            blur_radius=4,
            color="#0000001A",
            offset=ft.Offset(0, 2)
        )
    
    def _parse_font_size(
        self, 
        size: Optional[str], 
        context: RenderContext
    ) -> Optional[float]:
        """Parse font size"""
        return self._parse_dimension(size, context)
    
    def _parse_font_weight(self, weight: Optional[str]) -> Optional[ft.FontWeight]:
        """Parse font weight"""
        if not weight:
            return None
        
        weight_map = {
            "normal": ft.FontWeight.NORMAL,
            "bold": ft.FontWeight.BOLD,
            "100": ft.FontWeight.W_100,
            "200": ft.FontWeight.W_200,
            "300": ft.FontWeight.W_300,
            "400": ft.FontWeight.W_400,
            "500": ft.FontWeight.W_500,
            "600": ft.FontWeight.W_600,
            "700": ft.FontWeight.W_700,
            "800": ft.FontWeight.W_800,
            "900": ft.FontWeight.W_900
        }
        
        return weight_map.get(str(weight).lower())
    
    def _parse_text_align(self, align: Optional[str]) -> Optional[ft.TextAlign]:
        """Parse text alignment"""
        if not align:
            return None
        
        align_map = {
            "left": ft.TextAlign.LEFT,
            "center": ft.TextAlign.CENTER,
            "right": ft.TextAlign.RIGHT,
            "justify": ft.TextAlign.JUSTIFY
        }
        
        return align_map.get(align)
    
    def _parse_main_axis_alignment(self, value: str) -> ft.MainAxisAlignment:
        """Parse flex main axis alignment"""
        align_map = {
            "start": ft.MainAxisAlignment.START,
            "end": ft.MainAxisAlignment.END,
            "center": ft.MainAxisAlignment.CENTER,
            "space-between": ft.MainAxisAlignment.SPACE_BETWEEN,
            "space-around": ft.MainAxisAlignment.SPACE_AROUND,
            "space-evenly": ft.MainAxisAlignment.SPACE_EVENLY
        }
        
        return align_map.get(value, ft.MainAxisAlignment.START)
    
    def _parse_cross_axis_alignment(self, value: str) -> ft.CrossAxisAlignment:
        """Parse flex cross axis alignment"""
        align_map = {
            "start": ft.CrossAxisAlignment.START,
            "end": ft.CrossAxisAlignment.END,
            "center": ft.CrossAxisAlignment.CENTER,
            "stretch": ft.CrossAxisAlignment.STRETCH
        }
        
        return align_map.get(value, ft.CrossAxisAlignment.START)
    
    def _parse_image_fit(self, fit: str) -> ft.ImageFit:
        """Parse image object-fit"""
        fit_map = {
            "contain": ft.ImageFit.CONTAIN,
            "cover": ft.ImageFit.COVER,
            "fill": ft.ImageFit.FILL,
            "none": ft.ImageFit.NONE,
            "scale-down": ft.ImageFit.SCALE_DOWN
        }
        
        return fit_map.get(fit, ft.ImageFit.CONTAIN)
    
    def _create_flex_layout(
        self, 
        component: Component, 
        children: List[ft.Control]
    ) -> ft.Control:
        """Create flex layout"""
        if component.style.flex_direction in ["row", "row-reverse"]:
            return ft.Row(
                controls=children,
                alignment=self._parse_main_axis_alignment(
                    component.style.justify_content or "start"
                ),
                vertical_alignment=self._parse_cross_axis_alignment(
                    component.style.align_items or "start"
                ),
                spacing=self._parse_dimension(component.style.gap, None) or 0
            )
        else:
            return ft.Column(
                controls=children,
                alignment=self._parse_main_axis_alignment(
                    component.style.justify_content or "start"
                ),
                horizontal_alignment=self._parse_cross_axis_alignment(
                    component.style.align_items or "start"
                ),
                spacing=self._parse_dimension(component.style.gap, None) or 0
            )
    
    def _create_grid_layout(
        self, 
        component: Component, 
        children: List[ft.Control]
    ) -> ft.Control:
        """Create grid layout (simplified)"""
        # For now, wrap in a column
        # Future: Implement proper CSS Grid
        return ft.Column(controls=children, spacing=0)
    
    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text content for safe rendering
        CLAUDE.md #7.2: Output encoding
        """
        # Basic HTML entity encoding
        return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))
    
    def _get_icon(self, icon_name: str) -> Optional[str]:
        """Get icon from name"""
        # Map common icon names to Flet icons
        icon_map = {
            "home": ft.Icons.HOME,
            "settings": ft.Icons.SETTINGS,
            "search": ft.Icons.SEARCH,
            "menu": ft.Icons.MENU,
            "close": ft.Icons.CLOSE,
            "add": ft.Icons.ADD,
            "edit": ft.Icons.EDIT,
            "delete": ft.Icons.DELETE,
            "save": ft.Icons.SAVE,
            "download": ft.Icons.DOWNLOAD,
            "upload": ft.Icons.UPLOAD
        }
        
        return icon_map.get(icon_name.lower())
    
    def _should_animate(self, component: Component) -> Optional[int]:
        """Check if component should animate"""
        # Future: Parse animation properties
        return None
    
    # Event handlers (placeholders for interaction system)
    
    def _handle_click(self, component: Component, context: RenderContext) -> None:
        """Handle component click"""
        logger.debug(f"Component clicked: {component.id}")
    
    def _handle_hover(
        self, 
        component: Component, 
        context: RenderContext, 
        event: ft.HoverEvent
    ) -> None:
        """Handle component hover"""
        if event.data == "true":
            logger.debug(f"Component hover enter: {component.id}")
        else:
            logger.debug(f"Component hover exit: {component.id}")