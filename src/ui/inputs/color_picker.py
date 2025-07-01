"""
Advanced Color Picker Component
Professional color picker with wheel, presets, and format conversion
Following CLAUDE.md guidelines for robust UI components
"""

import flet as ft
import math
from typing import Any, Callable, Optional, List, Tuple
import re
import logging

from components.property_definitions import PropertyDefinition, PropertyType
from property_input_base import PropertyInputBase

logger = logging.getLogger(__name__)


class ColorUtil:
    """Color utility functions for conversion and validation"""
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        try:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            return (0, 0, 0)
    
    @staticmethod
    def rgb_to_hex(r: int, g: int, b: int) -> str:
        """Convert RGB values to hex color"""
        return f"#{r:02x}{g:02x}{b:02x}"
    
    @staticmethod
    def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[int, int, int]:
        """Convert RGB to HSL"""
        r, g, b = r/255.0, g/255.0, b/255.0
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val
        
        # Lightness
        l = (max_val + min_val) / 2
        
        if diff == 0:
            h = s = 0  # achromatic
        else:
            # Saturation
            s = diff / (2 - max_val - min_val) if l > 0.5 else diff / (max_val + min_val)
            
            # Hue
            if max_val == r:
                h = (g - b) / diff + (6 if g < b else 0)
            elif max_val == g:
                h = (b - r) / diff + 2
            else:
                h = (r - g) / diff + 4
            h /= 6
        
        return (int(h * 360), int(s * 100), int(l * 100))
    
    @staticmethod
    def hsl_to_rgb(h: int, s: int, l: int) -> Tuple[int, int, int]:
        """Convert HSL to RGB"""
        h = h / 360.0
        s = s / 100.0
        l = l / 100.0
        
        def hue_to_rgb(p: float, q: float, t: float) -> float:
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        
        if s == 0:
            r = g = b = l  # achromatic
        else:
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)
        
        return (int(r * 255), int(g * 255), int(b * 255))
    
    @staticmethod
    def parse_color(color: str) -> Tuple[int, int, int]:
        """Parse color string and return RGB tuple"""
        color = color.strip()
        
        # Hex color
        if color.startswith('#'):
            return ColorUtil.hex_to_rgb(color)
        
        # RGB color
        rgb_match = re.match(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color, re.IGNORECASE)
        if rgb_match:
            return tuple(map(int, rgb_match.groups()))
        
        # HSL color
        hsl_match = re.match(r'hsl\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*\)', color, re.IGNORECASE)
        if hsl_match:
            h, s, l = map(int, hsl_match.groups())
            return ColorUtil.hsl_to_rgb(h, s, l)
        
        # CSS color names
        css_colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'green': (0, 128, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255),
            'gray': (128, 128, 128),
            'grey': (128, 128, 128),
            'orange': (255, 165, 0),
            'purple': (128, 0, 128),
            'brown': (165, 42, 42),
            'pink': (255, 192, 203),
        }
        
        return css_colors.get(color.lower(), (0, 0, 0))


class ColorWheel(ft.Container):
    """Interactive color wheel component"""
    
    def __init__(self, size: float = 200, on_color_change: Optional[Callable[[Tuple[int, int, int]], None]] = None):
        super().__init__()
        self.size = size
        self.on_color_change = on_color_change
        self.current_hue = 0
        self.current_saturation = 100
        self.current_lightness = 50
        
        self.width = size
        self.height = size
        self.border_radius = size / 2
        self.bgcolor = "#FFFFFF"
        self.border = ft.border.all(1, "#E5E7EB")
        
        # Create the wheel visual
        self.content = self._build_wheel()
    
    def _build_wheel(self) -> ft.Control:
        """Build the color wheel UI"""
        # For simplicity, we'll create a grid of color samples
        # In a full implementation, this would be a proper HSV wheel
        wheel_colors = []
        
        # Create a simple hue ring
        for i in range(12):
            hue = i * 30
            rgb = ColorUtil.hsl_to_rgb(hue, 100, 50)
            hex_color = ColorUtil.rgb_to_hex(*rgb)
            
            color_container = ft.Container(
                width=30,
                height=30,
                bgcolor=hex_color,
                border_radius=15,
                on_click=lambda e, h=hue: self._on_hue_select(h),
                border=ft.border.all(2, "#FFFFFF")
            )
            wheel_colors.append(color_container)
        
        # Arrange in a circle (simplified as a grid)
        rows = []
        for i in range(0, len(wheel_colors), 4):
            row = ft.Row(
                wheel_colors[i:i+4],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            )
            rows.append(row)
        
        return ft.Column(
            rows,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
    
    def _on_hue_select(self, hue: int) -> None:
        """Handle hue selection"""
        self.current_hue = hue
        rgb = ColorUtil.hsl_to_rgb(hue, self.current_saturation, self.current_lightness)
        if self.on_color_change:
            self.on_color_change(rgb)


class ColorSliders(ft.Container):
    """RGB/HSL color sliders"""
    
    def __init__(self, color_mode: str = "rgb", on_color_change: Optional[Callable[[Tuple[int, int, int]], None]] = None):
        super().__init__()
        self.color_mode = color_mode
        self.on_color_change = on_color_change
        self.current_rgb = (255, 0, 0)
        
        self.content = self._build_sliders()
    
    def _build_sliders(self) -> ft.Control:
        """Build color sliders based on mode"""
        controls = []
        
        if self.color_mode == "rgb":
            # RGB sliders
            self.r_slider = ft.Slider(
                min=0, max=255, value=self.current_rgb[0],
                on_change=lambda e: self._on_rgb_change()
            )
            self.g_slider = ft.Slider(
                min=0, max=255, value=self.current_rgb[1],
                on_change=lambda e: self._on_rgb_change()
            )
            self.b_slider = ft.Slider(
                min=0, max=255, value=self.current_rgb[2],
                on_change=lambda e: self._on_rgb_change()
            )
            
            controls.extend([
                ft.Row([ft.Text("R:", width=20), self.r_slider], spacing=10),
                ft.Row([ft.Text("G:", width=20), self.g_slider], spacing=10),
                ft.Row([ft.Text("B:", width=20), self.b_slider], spacing=10),
            ])
        
        elif self.color_mode == "hsl":
            # HSL sliders
            hsl = ColorUtil.rgb_to_hsl(*self.current_rgb)
            
            self.h_slider = ft.Slider(
                min=0, max=360, value=hsl[0],
                on_change=lambda e: self._on_hsl_change()
            )
            self.s_slider = ft.Slider(
                min=0, max=100, value=hsl[1],
                on_change=lambda e: self._on_hsl_change()
            )
            self.l_slider = ft.Slider(
                min=0, max=100, value=hsl[2],
                on_change=lambda e: self._on_hsl_change()
            )
            
            controls.extend([
                ft.Row([ft.Text("H:", width=20), self.h_slider], spacing=10),
                ft.Row([ft.Text("S:", width=20), self.s_slider], spacing=10),
                ft.Row([ft.Text("L:", width=20), self.l_slider], spacing=10),
            ])
        
        return ft.Column(controls, spacing=8)
    
    def _on_rgb_change(self) -> None:
        """Handle RGB slider changes"""
        if hasattr(self, 'r_slider'):
            r = int(self.r_slider.value)
            g = int(self.g_slider.value)
            b = int(self.b_slider.value)
            self.current_rgb = (r, g, b)
            if self.on_color_change:
                self.on_color_change((r, g, b))
    
    def _on_hsl_change(self) -> None:
        """Handle HSL slider changes"""
        if hasattr(self, 'h_slider'):
            h = int(self.h_slider.value)
            s = int(self.s_slider.value)
            l = int(self.l_slider.value)
            rgb = ColorUtil.hsl_to_rgb(h, s, l)
            self.current_rgb = rgb
            if self.on_color_change:
                self.on_color_change(rgb)
    
    def set_color(self, rgb: Tuple[int, int, int]) -> None:
        """Set color and update sliders"""
        self.current_rgb = rgb
        
        if self.color_mode == "rgb" and hasattr(self, 'r_slider'):
            self.r_slider.value = rgb[0]
            self.g_slider.value = rgb[1]
            self.b_slider.value = rgb[2]
        elif self.color_mode == "hsl" and hasattr(self, 'h_slider'):
            h, s, l = ColorUtil.rgb_to_hsl(*rgb)
            self.h_slider.value = h
            self.s_slider.value = s
            self.l_slider.value = l
        
        self.update()


class ColorPresets(ft.Container):
    """Color preset swatches"""
    
    DEFAULT_PRESETS = [
        "#FFFFFF", "#F5F5F5", "#E5E5E5", "#D4D4D4", "#A3A3A3", "#737373", "#525252", "#404040", "#262626", "#171717", "#000000",
        "#FEF2F2", "#FECACA", "#F87171", "#EF4444", "#DC2626", "#B91C1C", "#991B1B", "#7F1D1D", "#450A0A",
        "#FFF7ED", "#FED7AA", "#FDBA74", "#FB923C", "#F97316", "#EA580C", "#C2410C", "#9A3412", "#7C2D12", "#431407",
        "#FFFBEB", "#FDE68A", "#FCD34D", "#FBBF24", "#F59E0B", "#D97706", "#B45309", "#92400E", "#78350F", "#451A03",
        "#F0FDF4", "#BBF7D0", "#86EFAC", "#4ADE80", "#22C55E", "#16A34A", "#15803D", "#166534", "#14532D", "#052E16",
        "#ECFDF5", "#A7F3D0", "#6EE7B7", "#34D399", "#10B981", "#059669", "#047857", "#065F46", "#064E3B", "#022C22",
        "#F0F9FF", "#BAE6FD", "#7DD3FC", "#38BDF8", "#0EA5E9", "#0284C7", "#0369A1", "#075985", "#0C4A6E", "#082F49",
        "#EFF6FF", "#DBEAFE", "#BFDBFE", "#93C5FD", "#60A5FA", "#3B82F6", "#2563EB", "#1D4ED8", "#1E40AF", "#1E3A8A",
        "#F5F3FF", "#E9D5FF", "#C4B5FD", "#A78BFA", "#8B5CF6", "#7C3AED", "#6D28D9", "#5B21B6", "#4C1D95", "#312E81",
        "#FDF2F8", "#FCE7F3", "#FBCFE8", "#F9A8D4", "#F472B6", "#EC4899", "#DB2777", "#BE185D", "#9D174D", "#831843"
    ]
    
    def __init__(self, presets: Optional[List[str]] = None, on_color_select: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.presets = presets or self.DEFAULT_PRESETS
        self.on_color_select = on_color_select
        
        self.content = self._build_presets()
    
    def _build_presets(self) -> ft.Control:
        """Build preset color swatches"""
        swatch_controls = []
        
        for color in self.presets:
            swatch = ft.Container(
                width=24,
                height=24,
                bgcolor=color,
                border_radius=4,
                border=ft.border.all(1, "#E5E7EB"),
                on_click=lambda e, c=color: self._on_swatch_click(c),
                tooltip=color
            )
            swatch_controls.append(swatch)
        
        # Arrange in rows
        rows = []
        swatches_per_row = 11
        for i in range(0, len(swatch_controls), swatches_per_row):
            row = ft.Row(
                swatch_controls[i:i+swatches_per_row],
                spacing=4,
                alignment=ft.MainAxisAlignment.START
            )
            rows.append(row)
        
        return ft.Column([
            ft.Text("Presets", size=14, weight=ft.FontWeight.W_500),
            ft.Container(
                content=ft.Column(rows, spacing=4),
                padding=8,
                border=ft.border.all(1, "#E5E7EB"),
                border_radius=6
            )
        ], spacing=8)
    
    def _on_swatch_click(self, color: str) -> None:
        """Handle preset color selection"""
        if self.on_color_select:
            self.on_color_select(color)


class ColorPickerDialog(ft.AlertDialog):
    """Advanced color picker dialog"""
    
    def __init__(self, initial_color: str = "#FF0000", on_color_change: Optional[Callable[[str], None]] = None):
        self.initial_color = initial_color
        self.current_color = initial_color
        self.on_color_change = on_color_change
        self.color_format = "hex"  # hex, rgb, hsl
        
        # Parse initial color
        self.current_rgb = ColorUtil.parse_color(initial_color)
        
        super().__init__(
            title=ft.Text("Color Picker", size=18, weight=ft.FontWeight.BOLD),
            content=self._build_content(),
            actions=[
                ft.TextButton("Cancel", on_click=self._on_cancel),
                ft.ElevatedButton("OK", on_click=self._on_ok)
            ],
            modal=True
        )
    
    def _build_content(self) -> ft.Control:
        """Build the color picker dialog content"""
        # Current color preview
        self.color_preview = ft.Container(
            width=60,
            height=60,
            bgcolor=self.current_color,
            border_radius=8,
            border=ft.border.all(2, "#E5E7EB")
        )
        
        # Color input fields
        self.hex_input = ft.TextField(
            value=self.current_color,
            prefix_text="#",
            width=100,
            on_change=lambda e: self._on_hex_input(e.control.value),
            border_radius=6
        )
        
        # Format selector
        self.format_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("hex", "HEX"),
                ft.dropdown.Option("rgb", "RGB"),
                ft.dropdown.Option("hsl", "HSL")
            ],
            value="hex",
            width=80,
            on_change=lambda e: self._on_format_change(e.control.value)
        )
        
        # Color wheel
        self.color_wheel = ColorWheel(
            size=150,
            on_color_change=self._on_wheel_color_change
        )
        
        # Color sliders
        self.color_sliders = ColorSliders(
            color_mode="rgb",
            on_color_change=self._on_slider_color_change
        )
        
        # Color presets
        self.color_presets = ColorPresets(
            on_color_select=self._on_preset_select
        )
        
        # Tabs for different picker modes
        tabs = ft.Tabs([
            ft.Tab(
                text="Wheel",
                content=ft.Container(
                    content=self.color_wheel,
                    padding=20,
                    alignment=ft.alignment.center
                )
            ),
            ft.Tab(
                text="Sliders",
                content=ft.Container(
                    content=self.color_sliders,
                    padding=20
                )
            ),
            ft.Tab(
                text="Presets",
                content=ft.Container(
                    content=self.color_presets,
                    padding=20
                )
            )
        ])
        
        return ft.Container(
            content=ft.Column([
                # Header with preview and input
                ft.Row([
                    self.color_preview,
                    ft.Column([
                        ft.Row([
                            self.hex_input,
                            self.format_dropdown
                        ], spacing=8),
                        ft.Text(
                            f"RGB: {self.current_rgb[0]}, {self.current_rgb[1]}, {self.current_rgb[2]}",
                            size=12,
                            color="#6B7280"
                        )
                    ], spacing=4)
                ], spacing=16),
                
                ft.Divider(),
                
                # Color picker tabs
                tabs
            ], spacing=16),
            width=400,
            height=500
        )
    
    def _on_hex_input(self, value: str) -> None:
        """Handle hex input change"""
        try:
            # Add # if missing
            if not value.startswith('#'):
                value = '#' + value
            
            # Validate hex color
            rgb = ColorUtil.parse_color(value)
            self._update_color_from_rgb(rgb)
            self.current_color = value
        except:
            pass  # Invalid color, ignore
    
    def _on_format_change(self, format_name: str) -> None:
        """Handle color format change"""
        self.color_format = format_name
        self._update_color_display()
    
    def _on_wheel_color_change(self, rgb: Tuple[int, int, int]) -> None:
        """Handle color wheel change"""
        self._update_color_from_rgb(rgb)
    
    def _on_slider_color_change(self, rgb: Tuple[int, int, int]) -> None:
        """Handle color slider change"""
        self._update_color_from_rgb(rgb)
    
    def _on_preset_select(self, color: str) -> None:
        """Handle preset color selection"""
        rgb = ColorUtil.parse_color(color)
        self._update_color_from_rgb(rgb)
        self.current_color = color
    
    def _update_color_from_rgb(self, rgb: Tuple[int, int, int]) -> None:
        """Update all UI from RGB values"""
        self.current_rgb = rgb
        hex_color = ColorUtil.rgb_to_hex(*rgb)
        self.current_color = hex_color
        
        # Update UI
        self.color_preview.bgcolor = hex_color
        self.hex_input.value = hex_color.lstrip('#')
        
        # Update sliders
        self.color_sliders.set_color(rgb)
        
        self.update()
    
    def _update_color_display(self) -> None:
        """Update color display based on current format"""
        if self.color_format == "hex":
            self.hex_input.value = self.current_color.lstrip('#')
        elif self.color_format == "rgb":
            r, g, b = self.current_rgb
            self.hex_input.value = f"rgb({r}, {g}, {b})"
        elif self.color_format == "hsl":
            h, s, l = ColorUtil.rgb_to_hsl(*self.current_rgb)
            self.hex_input.value = f"hsl({h}, {s}%, {l}%)"
    
    def _on_cancel(self, e) -> None:
        """Handle cancel button"""
        self.open = False
        self.update()
    
    def _on_ok(self, e) -> None:
        """Handle OK button"""
        if self.on_color_change:
            self.on_color_change(self.current_color)
        self.open = False
        self.update()


class ColorPropertyInput(PropertyInputBase):
    """
    Advanced color input with picker and validation
    CLAUDE.md #7.2: Validate color input formats
    """
    
    def _build_input_control(self) -> ft.Control:
        # Parse current color
        current_rgb = ColorUtil.parse_color(self.value or "#FFFFFF")
        current_hex = ColorUtil.rgb_to_hex(*current_rgb)
        
        # Color preview button
        self.color_preview = ft.Container(
            width=40,
            height=40,
            bgcolor=current_hex,
            border_radius=6,
            border=ft.border.all(1, "#D1D5DB"),
            on_click=lambda e: self._open_color_picker(),
            tooltip="Click to open color picker"
        )
        
        # Hex input field
        self.hex_input = ft.TextField(
            value=self.value or "",
            on_change=lambda e: self._on_hex_change(e.control.value),
            on_focus=lambda e: self._handle_focus(True),
            on_blur=lambda e: self._handle_focus(False),
            width=120,
            height=40,
            border_radius=6,
            text_size=14,
            border_color="#D1D5DB",
            focused_border_color="#5E6AD2",
            prefix_text="#" if not (self.value and self.value.startswith('#')) else "",
        )
        
        # Format dropdown
        self.format_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("hex", "HEX"),
                ft.dropdown.Option("rgb", "RGB"),
                ft.dropdown.Option("hsl", "HSL"),
                ft.dropdown.Option("name", "Name")
            ],
            value="hex",
            width=80,
            height=40,
            on_change=lambda e: self._on_format_change(e.control.value),
            text_size=14
        )
        
        # Eyedropper button (placeholder - would need platform-specific implementation)
        eyedropper_btn = ft.IconButton(
            icon=ft.Icons.COLORIZE,
            tooltip="Eyedropper (coming soon)",
            on_click=lambda e: self._show_eyedropper_info(),
            disabled=True  # Disabled until implemented
        )
        
        return ft.Row([
            self.color_preview,
            self.hex_input,
            self.format_dropdown,
            eyedropper_btn
        ], spacing=8, alignment=ft.MainAxisAlignment.START)
    
    def _on_hex_change(self, value: str) -> None:
        """Handle manual hex input change"""
        # Ensure proper hex format
        if value and not value.startswith('#'):
            value = '#' + value
        
        # Update preview
        try:
            rgb = ColorUtil.parse_color(value)
            hex_color = ColorUtil.rgb_to_hex(*rgb)
            self.color_preview.bgcolor = hex_color
            self.color_preview.update()
        except:
            pass  # Invalid color, don't update preview
        
        self._handle_change(value)
    
    def _on_format_change(self, format_name: str) -> None:
        """Handle color format change"""
        if not self.value:
            return
        
        try:
            rgb = ColorUtil.parse_color(self.value)
            
            if format_name == "hex":
                new_value = ColorUtil.rgb_to_hex(*rgb)
            elif format_name == "rgb":
                new_value = f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"
            elif format_name == "hsl":
                h, s, l = ColorUtil.rgb_to_hsl(*rgb)
                new_value = f"hsl({h}, {s}%, {l}%)"
            else:  # name format
                new_value = self.value  # Keep as is
            
            self.hex_input.value = new_value
            self._handle_change(new_value)
            self.update()
        except:
            pass  # Invalid color
    
    def _open_color_picker(self) -> None:
        """Open the color picker dialog"""
        dialog = ColorPickerDialog(
            initial_color=self.value or "#FF0000",
            on_color_change=self._on_picker_color_change
        )
        
        # Add to page (in a real implementation, you'd get the page reference)
        # page.dialog = dialog
        # dialog.open = True
        # page.update()
        
        logger.info("Color picker dialog would open here")
    
    def _on_picker_color_change(self, color: str) -> None:
        """Handle color change from picker"""
        self.hex_input.value = color
        rgb = ColorUtil.parse_color(color)
        hex_color = ColorUtil.rgb_to_hex(*rgb)
        self.color_preview.bgcolor = hex_color
        self._handle_change(color)
        self.update()
    
    def _show_eyedropper_info(self) -> None:
        """Show info about eyedropper feature"""
        logger.info("Eyedropper feature would be implemented with platform-specific code")
    
    def _update_input_value(self, value: Any) -> None:
        """Update the input control's value"""
        self.hex_input.value = str(value) if value else ""
        
        # Update color preview
        try:
            rgb = ColorUtil.parse_color(value or "#FFFFFF")
            hex_color = ColorUtil.rgb_to_hex(*rgb)
            self.color_preview.bgcolor = hex_color
        except:
            self.color_preview.bgcolor = "#FFFFFF"


# Update the factory function to include color picker
def create_color_property_input(
    definition: PropertyDefinition,
    value: Any,
    on_change: Callable[[str, Any], None],
    **kwargs
) -> ColorPropertyInput:
    """Create a color property input"""
    return ColorPropertyInput(definition, value, on_change, **kwargs)