"""
Advanced Spacing Property Input
4-value spacing input (margin/padding) with linked values and visual preview
Following CLAUDE.md guidelines for robust UI components
"""

import flet as ft
from typing import Any, Callable, Optional, Dict, List, Tuple
import re
import logging

from components.property_definitions import PropertyDefinition, PropertyType
from property_input_base import PropertyInputBase

logger = logging.getLogger(__name__)


class SpacingValue:
    """Represents a spacing value with individual sides"""
    
    def __init__(self, value: str = "0"):
        self.top = "0"
        self.right = "0"
        self.bottom = "0"
        self.left = "0"
        self.unit = "px"
        self.linked = True
        
        self._parse_value(value)
    
    def _parse_value(self, value: str) -> None:
        """Parse CSS spacing shorthand into individual values"""
        if not value or value.strip() == "":
            return
        
        # Remove extra whitespace and split
        parts = value.strip().split()
        
        # Extract unit from first value
        if parts:
            unit_match = re.search(r'([a-zA-Z%]+)$', parts[0])
            if unit_match:
                self.unit = unit_match.group(1)
        
        # Remove units from all parts for easier processing
        numeric_parts = []
        for part in parts:
            numeric_part = re.sub(r'[a-zA-Z%]+$', '', part)
            numeric_parts.append(numeric_part)
        
        # Parse according to CSS shorthand rules
        if len(numeric_parts) == 1:
            # All sides same
            self.top = self.right = self.bottom = self.left = numeric_parts[0]
            self.linked = True
        elif len(numeric_parts) == 2:
            # Vertical | Horizontal
            self.top = self.bottom = numeric_parts[0]
            self.right = self.left = numeric_parts[1]
            self.linked = False
        elif len(numeric_parts) == 3:
            # Top | Horizontal | Bottom
            self.top = numeric_parts[0]
            self.right = self.left = numeric_parts[1]
            self.bottom = numeric_parts[2]
            self.linked = False
        elif len(numeric_parts) == 4:
            # Top | Right | Bottom | Left
            self.top = numeric_parts[0]
            self.right = numeric_parts[1]
            self.bottom = numeric_parts[2]
            self.left = numeric_parts[3]
            self.linked = False
    
    def to_css(self) -> str:
        """Convert to CSS shorthand"""
        values = [self.top, self.right, self.bottom, self.left]
        
        # Add units
        values_with_units = [f"{v}{self.unit}" for v in values]
        
        # Optimize shorthand
        if all(v == values[0] for v in values):
            # All same
            return values_with_units[0]
        elif values[0] == values[2] and values[1] == values[3]:
            # Vertical/Horizontal pattern
            return f"{values_with_units[0]} {values_with_units[1]}"
        elif values[1] == values[3]:
            # Top/Bottom different, Left/Right same
            return f"{values_with_units[0]} {values_with_units[1]} {values_with_units[2]}"
        else:
            # All different
            return " ".join(values_with_units)
    
    def get_numeric_values(self) -> Tuple[float, float, float, float]:
        """Get numeric values as floats"""
        try:
            return (
                float(self.top) if self.top else 0,
                float(self.right) if self.right else 0,
                float(self.bottom) if self.bottom else 0,
                float(self.left) if self.left else 0
            )
        except ValueError:
            return (0, 0, 0, 0)


class SpacingPreview(ft.Container):
    """Visual preview of spacing values"""
    
    def __init__(self, spacing_value: SpacingValue, size: int = 100):
        super().__init__()
        self.spacing_value = spacing_value
        self.size = size
        
        self.width = size + 40
        self.height = size + 40
        self.content = self._build_preview()
    
    def _build_preview(self) -> ft.Control:
        """Build the visual spacing preview"""
        # Get numeric values for visualization
        top, right, bottom, left = self.spacing_value.get_numeric_values()
        
        # Scale values for display (max 20px for preview)
        scale_factor = 20 / max(max(top, right, bottom, left), 1)
        scaled_top = min(top * scale_factor, 20)
        scaled_right = min(right * scale_factor, 20)
        scaled_bottom = min(bottom * scale_factor, 20)
        scaled_left = min(left * scale_factor, 20)
        
        # Central element
        center_element = ft.Container(
            width=self.size - scaled_left - scaled_right,
            height=self.size - scaled_top - scaled_bottom,
            bgcolor="#5E6AD2",
            border_radius=4
        )
        
        # Container with spacing visualization
        preview_container = ft.Container(
            content=center_element,
            padding=ft.padding.only(
                top=scaled_top,
                right=scaled_right,
                bottom=scaled_bottom,
                left=scaled_left
            ),
            bgcolor="#E5E7EB",
            border_radius=8,
            border=ft.border.all(1, "#D1D5DB")
        )
        
        # Labels for values
        labels = ft.Column([
            ft.Text(f"T: {top}{self.spacing_value.unit}", size=10, text_align=ft.TextAlign.CENTER),
            ft.Row([
                ft.Text(f"L: {left}{self.spacing_value.unit}", size=10),
                ft.Text(f"R: {right}{self.spacing_value.unit}", size=10),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Text(f"B: {bottom}{self.spacing_value.unit}", size=10, text_align=ft.TextAlign.CENTER),
        ], spacing=2, alignment=ft.MainAxisAlignment.CENTER)
        
        return ft.Column([
            preview_container,
            ft.Divider(height=10),
            labels
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    def update_spacing(self, spacing_value: SpacingValue) -> None:
        """Update the preview with new spacing values"""
        self.spacing_value = spacing_value
        self.content = self._build_preview()
        self.update()


class SpacingPropertyInput(PropertyInputBase):
    """
    Advanced spacing input with 4-value support and linking
    CLAUDE.md #1.4: Extensible for future units
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spacing_value = SpacingValue(str(self.value) if self.value else "0")
        
    def _build_input_control(self) -> ft.Control:
        """Build the spacing input interface"""
        # Link toggle button
        self.link_button = ft.IconButton(
            icon=ft.Icons.LINK if self.spacing_value.linked else ft.Icons.LINK_OFF,
            tooltip="Link all values" if not self.spacing_value.linked else "Unlink values",
            on_click=lambda e: self._toggle_link(),
            icon_color="#5E6AD2" if self.spacing_value.linked else "#9CA3AF"
        )
        
        # Individual side inputs
        self.top_input = self._create_side_input("top", "T", self.spacing_value.top)
        self.right_input = self._create_side_input("right", "R", self.spacing_value.right)
        self.bottom_input = self._create_side_input("bottom", "B", self.spacing_value.bottom)
        self.left_input = self._create_side_input("left", "L", self.spacing_value.left)
        
        # Unit selector
        self.unit_selector = ft.Dropdown(
            options=[
                ft.dropdown.Option("px", "px"),
                ft.dropdown.Option("em", "em"),
                ft.dropdown.Option("rem", "rem"),
                ft.dropdown.Option("%", "%"),
                ft.dropdown.Option("vh", "vh"),
                ft.dropdown.Option("vw", "vw"),
                ft.dropdown.Option("auto", "auto")
            ],
            value=self.spacing_value.unit,
            width=70,
            height=36,
            text_size=12,
            on_change=lambda e: self._on_unit_change(e.control.value)
        )
        
        # Quick preset buttons
        preset_buttons = self._create_preset_buttons()
        
        # Spacing preview
        self.spacing_preview = SpacingPreview(self.spacing_value)
        
        # Layout modes
        layout_tabs = ft.Tabs([
            ft.Tab(
                text="Grid",
                content=self._build_grid_layout()
            ),
            ft.Tab(
                text="Linear",
                content=self._build_linear_layout()
            ),
            ft.Tab(
                text="Preview",
                content=ft.Container(
                    content=self.spacing_preview,
                    alignment=ft.alignment.center,
                    padding=10
                )
            )
        ], height=200)
        
        return ft.Column([
            # Header with link toggle and unit
            ft.Row([
                self.link_button,
                ft.Text("Spacing", size=14, weight=ft.FontWeight.W_500),
                ft.Container(expand=True),
                self.unit_selector
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # Quick presets
            preset_buttons,
            
            # Main input area
            layout_tabs
        ], spacing=12)
    
    def _create_side_input(self, side: str, label: str, value: str) -> ft.TextField:
        """Create input field for a specific side"""
        return ft.TextField(
            value=value,
            label=label,
            width=50,
            height=36,
            text_size=12,
            text_align=ft.TextAlign.CENTER,
            border_radius=4,
            on_change=lambda e, s=side: self._on_side_change(s, e.control.value),
            on_focus=lambda e: self._handle_focus(True),
            on_blur=lambda e: self._handle_focus(False)
        )
    
    def _create_preset_buttons(self) -> ft.Control:
        """Create quick preset buttons"""
        presets = [
            ("0", "None"),
            ("4px", "XS"),
            ("8px", "SM"),
            ("16px", "MD"),
            ("24px", "LG"),
            ("32px", "XL")
        ]
        
        buttons = []
        for value, label in presets:
            btn = ft.ElevatedButton(
                text=label,
                width=50,
                height=32,
                style=ft.ButtonStyle(
                    text_style=ft.TextStyle(size=10),
                    padding=ft.padding.all(4)
                ),
                on_click=lambda e, v=value: self._apply_preset(v)
            )
            buttons.append(btn)
        
        return ft.Row(buttons, spacing=4, scroll=ft.ScrollMode.AUTO)
    
    def _build_grid_layout(self) -> ft.Control:
        """Build grid layout for spacing inputs"""
        return ft.Container(
            content=ft.Column([
                # Top
                ft.Row([
                    ft.Container(expand=True),
                    self.top_input,
                    ft.Container(expand=True)
                ]),
                # Middle row with left and right
                ft.Row([
                    self.left_input,
                    ft.Container(
                        content=ft.Icon(ft.Icons.CROP_SQUARE, size=40, color="#E5E7EB"),
                        expand=True,
                        alignment=ft.alignment.center
                    ),
                    self.right_input
                ]),
                # Bottom
                ft.Row([
                    ft.Container(expand=True),
                    self.bottom_input,
                    ft.Container(expand=True)
                ])
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            padding=16
        )
    
    def _build_linear_layout(self) -> ft.Control:
        """Build linear layout for spacing inputs"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Top:", size=12, width=40),
                    self.top_input
                ], spacing=8),
                ft.Row([
                    ft.Text("Right:", size=12, width=40),
                    self.right_input
                ], spacing=8),
                ft.Row([
                    ft.Text("Bottom:", size=12, width=40),
                    self.bottom_input
                ], spacing=8),
                ft.Row([
                    ft.Text("Left:", size=12, width=40),
                    self.left_input
                ], spacing=8)
            ], spacing=8),
            padding=16
        )
    
    def _toggle_link(self) -> None:
        """Toggle linking of values"""
        self.spacing_value.linked = not self.spacing_value.linked
        
        # Update button icon
        self.link_button.icon = ft.Icons.LINK if self.spacing_value.linked else ft.Icons.LINK_OFF
        self.link_button.icon_color = "#5E6AD2" if self.spacing_value.linked else "#9CA3AF"
        
        # If linking, set all values to top value
        if self.spacing_value.linked:
            top_value = self.spacing_value.top
            self.spacing_value.right = top_value
            self.spacing_value.bottom = top_value
            self.spacing_value.left = top_value
            
            # Update input fields
            self.right_input.value = top_value
            self.bottom_input.value = top_value
            self.left_input.value = top_value
        
        self._update_value()
        self.update()
    
    def _on_side_change(self, side: str, value: str) -> None:
        """Handle change in individual side value"""
        # Update the specific side
        setattr(self.spacing_value, side, value)
        
        # If linked, update all sides
        if self.spacing_value.linked:
            self.spacing_value.top = value
            self.spacing_value.right = value
            self.spacing_value.bottom = value
            self.spacing_value.left = value
            
            # Update all input fields
            for input_field in [self.top_input, self.right_input, self.bottom_input, self.left_input]:
                input_field.value = value
        
        self._update_value()
        self.update()
    
    def _on_unit_change(self, unit: str) -> None:
        """Handle unit change"""
        self.spacing_value.unit = unit
        self._update_value()
    
    def _apply_preset(self, value: str) -> None:
        """Apply a preset value to all sides"""
        # Parse the numeric part
        numeric_part = re.sub(r'[a-zA-Z%]+$', '', value)
        
        # Apply to all sides
        self.spacing_value.top = numeric_part
        self.spacing_value.right = numeric_part
        self.spacing_value.bottom = numeric_part
        self.spacing_value.left = numeric_part
        self.spacing_value.linked = True
        
        # Extract unit if present
        unit_match = re.search(r'([a-zA-Z%]+)$', value)
        if unit_match:
            self.spacing_value.unit = unit_match.group(1)
            self.unit_selector.value = unit_match.group(1)
        
        # Update all inputs
        self.top_input.value = numeric_part
        self.right_input.value = numeric_part
        self.bottom_input.value = numeric_part
        self.left_input.value = numeric_part
        
        # Update link button
        self.link_button.icon = ft.Icons.LINK
        self.link_button.icon_color = "#5E6AD2"
        
        self._update_value()
        self.update()
    
    def _update_value(self) -> None:
        """Update the component value and notify parent"""
        css_value = self.spacing_value.to_css()
        self.value = css_value
        
        # Update preview
        self.spacing_preview.update_spacing(self.spacing_value)
        
        # Notify parent of change
        self._handle_change(css_value)
    
    def _update_input_value(self, value: Any) -> None:
        """Update input fields from external value change"""
        self.spacing_value = SpacingValue(str(value) if value else "0")
        
        # Update all input fields
        self.top_input.value = self.spacing_value.top
        self.right_input.value = self.spacing_value.right
        self.bottom_input.value = self.spacing_value.bottom
        self.left_input.value = self.spacing_value.left
        
        # Update unit selector
        self.unit_selector.value = self.spacing_value.unit
        
        # Update link button
        self.link_button.icon = ft.Icons.LINK if self.spacing_value.linked else ft.Icons.LINK_OFF
        self.link_button.icon_color = "#5E6AD2" if self.spacing_value.linked else "#9CA3AF"
        
        # Update preview
        self.spacing_preview.update_spacing(self.spacing_value)


class BorderPropertyInput(PropertyInputBase):
    """Border input with width, style, and color"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.border_width = "1"
        self.border_style = "solid"
        self.border_color = "#000000"
        self._parse_border_value(str(self.value) if self.value else "")
    
    def _parse_border_value(self, value: str) -> None:
        """Parse CSS border shorthand"""
        if not value:
            return
        
        parts = value.split()
        for part in parts:
            if re.match(r'^\d+(\.\d+)?(px|em|rem|%)$', part):
                self.border_width = re.sub(r'[a-zA-Z%]+$', '', part)
            elif part in ['solid', 'dashed', 'dotted', 'double', 'groove', 'ridge', 'inset', 'outset', 'none']:
                self.border_style = part
            elif re.match(r'^#[0-9A-Fa-f]{3,6}$', part) or part in ['red', 'blue', 'green', 'black', 'white']:
                self.border_color = part
    
    def _build_input_control(self) -> ft.Control:
        """Build border input controls"""
        # Width input
        width_input = ft.TextField(
            label="Width",
            value=self.border_width,
            width=80,
            height=36,
            text_size=12,
            suffix_text="px",
            on_change=lambda e: self._on_border_change()
        )
        
        # Style dropdown
        style_dropdown = ft.Dropdown(
            label="Style",
            options=[
                ft.dropdown.Option("solid", "Solid"),
                ft.dropdown.Option("dashed", "Dashed"),
                ft.dropdown.Option("dotted", "Dotted"),
                ft.dropdown.Option("double", "Double"),
                ft.dropdown.Option("none", "None")
            ],
            value=self.border_style,
            width=100,
            height=36,
            text_size=12,
            on_change=lambda e: self._on_border_change()
        )
        
        # Color input (simplified)
        color_input = ft.TextField(
            label="Color",
            value=self.border_color,
            width=100,
            height=36,
            text_size=12,
            on_change=lambda e: self._on_border_change()
        )
        
        # Store references
        self.width_input = width_input
        self.style_dropdown = style_dropdown
        self.color_input = color_input
        
        return ft.Row([
            width_input,
            style_dropdown,
            color_input
        ], spacing=8)
    
    def _on_border_change(self) -> None:
        """Handle border property changes"""
        self.border_width = self.width_input.value
        self.border_style = self.style_dropdown.value
        self.border_color = self.color_input.value
        
        # Construct CSS border value
        if self.border_style == "none":
            border_value = "none"
        else:
            border_value = f"{self.border_width}px {self.border_style} {self.border_color}"
        
        self._handle_change(border_value)
    
    def _update_input_value(self, value: Any) -> None:
        """Update input fields from external value change"""
        self._parse_border_value(str(value) if value else "")
        
        if hasattr(self, 'width_input'):
            self.width_input.value = self.border_width
            self.style_dropdown.value = self.border_style
            self.color_input.value = self.border_color


# Factory functions
def create_spacing_property_input(
    definition: PropertyDefinition,
    value: Any,
    on_change: Callable[[str, Any], None],
    **kwargs
) -> SpacingPropertyInput:
    """Create a spacing property input"""
    return SpacingPropertyInput(definition, value, on_change, **kwargs)


def create_border_property_input(
    definition: PropertyDefinition,
    value: Any,
    on_change: Callable[[str, Any], None],
    **kwargs
) -> BorderPropertyInput:
    """Create a border property input"""
    return BorderPropertyInput(definition, value, on_change, **kwargs)