"""
Enhanced Property Input Base Classes
Provides accessibility-first, enterprise-grade property input components
Following CLAUDE.md guidelines for robust UI components
"""

import flet as ft
from typing import Any, Callable, Optional, Dict, List, Union
from abc import ABC, abstractmethod
import logging
from datetime import datetime

from components.property_definitions import (
    PropertyDefinition, PropertyType, ValidationResult
)
from components.property_registry import get_registry

logger = logging.getLogger(__name__)


class PropertyInputBase(ft.Container, ABC):
    """
    Base class for all property input controls
    CLAUDE.md #1.2: DRY - Base class for all inputs
    CLAUDE.md #9.1: Accessibility built-in
    """
    
    def __init__(
        self,
        definition: PropertyDefinition,
        value: Any,
        on_change: Callable[[str, Any], None],
        on_validate: Optional[Callable[[Any], ValidationResult]] = None,
        component_id: Optional[str] = None,
        responsive_breakpoint: str = "base",
        **kwargs
    ):
        super().__init__(**kwargs)
        
        # Core properties
        self.definition = definition
        self.value = value
        self.component_id = component_id
        self.responsive_breakpoint = responsive_breakpoint
        
        # Callbacks
        self.on_change_handler = on_change
        self.on_validate_handler = on_validate or self._default_validate
        
        # State
        self.validation_result: Optional[ValidationResult] = None
        self.is_focused = False
        self.is_dirty = False
        self.last_validated_value = value
        
        # Registry reference
        self.registry = get_registry()
        
        # Accessibility properties
        self.accessible = True
        self.aria_label = definition.label
        self.aria_describedby = f"help-{definition.name}"
        
        # Set container properties
        self.padding = ft.padding.symmetric(vertical=8, horizontal=0)
        self.content = self._build_content()
        
        # Validate initial value
        self._validate_value(value, silent=True)
    
    def _default_validate(self, value: Any) -> ValidationResult:
        """Use definition's validation rules and registry validators"""
        if self.component_id:
            return self.registry.validate_property_value(
                self.component_id, self.definition.name, value
            )
        else:
            return self.definition.validate_value(value)
    
    def _validate_value(self, value: Any, silent: bool = False) -> ValidationResult:
        """
        Validate a value and update UI accordingly
        CLAUDE.md #2.1.2: Validate before propagating
        """
        try:
            result = self.on_validate_handler(value)
            self.validation_result = result
            self.last_validated_value = value
            
            if not silent:
                self._update_validation_ui()
            
            return result
            
        except Exception as e:
            logger.error(f"Validation error for property '{self.definition.name}': {e}")
            error_result = ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"]
            )
            self.validation_result = error_result
            return error_result
    
    def _handle_change(self, value: Any) -> None:
        """
        Handle value change with validation and callbacks
        CLAUDE.md #2.1.2: Validate before propagating
        """
        # Mark as dirty
        self.is_dirty = True
        
        # Validate new value
        validation = self._validate_value(value)
        
        # Always update the UI to show current value
        self.value = value
        
        # Only propagate if valid or if we want to show validation errors
        if validation.is_valid:
            try:
                self.on_change_handler(self.definition.name, value)
                logger.debug(f"Property '{self.definition.name}' changed to: {value}")
            except Exception as e:
                logger.error(f"Error handling property change: {e}")
        
        # Update UI
        self._update_validation_ui()
        self.update()
    
    def _handle_focus(self, is_focused: bool) -> None:
        """Handle focus changes for accessibility"""
        self.is_focused = is_focused
        if not is_focused and self.is_dirty:
            # Re-validate on blur
            self._validate_value(self.value)
    
    def _update_validation_ui(self) -> None:
        """Update UI to reflect validation state"""
        if hasattr(self, '_error_text') and self._error_text:
            if self.validation_result and not self.validation_result.is_valid:
                self._error_text.value = self.validation_result.errors[0] if self.validation_result.errors else ""
                self._error_text.visible = True
            else:
                self._error_text.visible = False
    
    @abstractmethod
    def _build_input_control(self) -> ft.Control:
        """Build the main input control - implemented by subclasses"""
        pass
    
    def _build_content(self) -> ft.Control:
        """
        Build the complete property input with label, input, and help
        CLAUDE.md #9.3: Full keyboard access
        CLAUDE.md #9.4: Proper ARIA labels
        """
        controls = []
        
        # Label with required indicator
        label_text = self.definition.label
        if self.definition.required:
            label_text += " *"
        
        # Icon + Label row
        label_row = [
            ft.Text(
                label_text,
                size=14,
                weight=ft.FontWeight.W_500,
                color="#374151"
            )
        ]
        
        if self.definition.icon:
            label_row.insert(0, ft.Icon(
                name=self.definition.icon,
                size=16,
                color="#6B7280"
            ))
        
        # Add responsive indicator if applicable
        if self.definition.responsive and self.responsive_breakpoint != "base":
            label_row.append(
                ft.Container(
                    content=ft.Text(
                        self.responsive_breakpoint.upper(),
                        size=10,
                        color="#FFFFFF"
                    ),
                    bgcolor="#5E6AD2",
                    padding=ft.padding.symmetric(horizontal=4, vertical=2),
                    border_radius=2
                )
            )
        
        controls.append(
            ft.Row(label_row, spacing=6, alignment=ft.MainAxisAlignment.START)
        )
        
        # Main input control
        input_control = self._build_input_control()
        controls.append(input_control)
        
        # Error message
        self._error_text = ft.Text(
            "",
            size=12,
            color="#EF4444",
            visible=False
        )
        controls.append(self._error_text)
        
        # Help text
        if self.definition.help_text:
            help_text = ft.Text(
                self.definition.help_text,
                size=12,
                color="#6B7280",
                text_align=ft.TextAlign.LEFT
            )
            
            # Add help URL if available
            if self.definition.help_url:
                help_row = ft.Row([
                    help_text,
                    ft.IconButton(
                        icon=ft.Icons.HELP_OUTLINE,
                        icon_size=14,
                        tooltip="More help",
                        on_click=lambda e: self._open_help_url()
                    )
                ], spacing=4)
                controls.append(help_row)
            else:
                controls.append(help_text)
        
        # Validation warnings (non-blocking)
        if self.validation_result and self.validation_result.warnings:
            warnings_text = ft.Text(
                f"⚠️ {self.validation_result.warnings[0]}",
                size=12,
                color="#F59E0B"
            )
            controls.append(warnings_text)
        
        return ft.Column(
            controls=controls,
            spacing=6,
            tight=True
        )
    
    def _open_help_url(self) -> None:
        """Open help URL in browser"""
        if self.definition.help_url:
            # In a real Flet app, you'd use ft.page.launch_url
            logger.info(f"Opening help URL: {self.definition.help_url}")
    
    def set_value(self, value: Any, validate: bool = True) -> None:
        """Programmatically set the value"""
        self.value = value
        if validate:
            self._validate_value(value)
        self._update_input_value(value)
        self.update()
    
    def get_value(self) -> Any:
        """Get the current value"""
        return self.value
    
    def is_valid(self) -> bool:
        """Check if current value is valid"""
        if not self.validation_result:
            self._validate_value(self.value, silent=True)
        return self.validation_result.is_valid if self.validation_result else False
    
    def get_validation_errors(self) -> List[str]:
        """Get current validation errors"""
        if self.validation_result:
            return self.validation_result.errors
        return []
    
    def reset(self) -> None:
        """Reset to default value"""
        self.set_value(self.definition.default_value)
        self.is_dirty = False
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable/disable the input"""
        # Override in subclasses to disable specific controls
        pass
    
    def set_visible(self, visible: bool) -> None:
        """Show/hide the input"""
        self.visible = visible
        self.update()
    
    @abstractmethod
    def _update_input_value(self, value: Any) -> None:
        """Update the input control's value - implemented by subclasses"""
        pass


class TextPropertyInput(PropertyInputBase):
    """Text input for string properties"""
    
    def _build_input_control(self) -> ft.Control:
        multiline = self.definition.type == PropertyType.TEXTAREA
        
        self._text_field = ft.TextField(
            value=str(self.value) if self.value is not None else "",
            placeholder=self.definition.placeholder,
            multiline=multiline,
            min_lines=3 if multiline else 1,
            max_lines=8 if multiline else 1,
            on_change=lambda e: self._handle_change(e.control.value),
            on_focus=lambda e: self._handle_focus(True),
            on_blur=lambda e: self._handle_focus(False),
            border_radius=6,
            text_size=14,
            border_color="#D1D5DB",
            focused_border_color="#5E6AD2",
            # Accessibility
            label=self.definition.label,
            helper_text="",  # We handle this in the base class
        )
        
        return self._text_field
    
    def _update_input_value(self, value: Any) -> None:
        self._text_field.value = str(value) if value is not None else ""


class NumberPropertyInput(PropertyInputBase):
    """Number input with optional unit selector"""
    
    def _build_input_control(self) -> ft.Control:
        # Extract numeric value and unit
        numeric_value, unit = self._parse_value(self.value)
        
        controls = []
        
        # Number input
        self._number_field = ft.TextField(
            value=str(numeric_value) if numeric_value is not None else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: self._handle_numeric_change(e.control.value),
            on_focus=lambda e: self._handle_focus(True),
            on_blur=lambda e: self._handle_focus(False),
            width=120,
            border_radius=6,
            text_size=14,
            border_color="#D1D5DB",
            focused_border_color="#5E6AD2",
            label=self.definition.label,
        )
        controls.append(self._number_field)
        
        # Unit selector if applicable
        if self.definition.units:
            self._unit_dropdown = ft.Dropdown(
                options=[ft.dropdown.Option(unit) for unit in self.definition.units],
                value=unit or self.definition.default_unit or self.definition.units[0],
                on_change=lambda e: self._handle_unit_change(e.control.value),
                width=80,
                text_size=14,
                border_color="#D1D5DB",
                focused_border_color="#5E6AD2"
            )
            controls.append(self._unit_dropdown)
        
        # Step controls if step is defined
        if self.definition.step:
            step_controls = ft.Column([
                ft.IconButton(
                    icon=ft.Icons.KEYBOARD_ARROW_UP,
                    icon_size=16,
                    on_click=lambda e: self._step_value(self.definition.step),
                    tooltip="Increase"
                ),
                ft.IconButton(
                    icon=ft.Icons.KEYBOARD_ARROW_DOWN,
                    icon_size=16,
                    on_click=lambda e: self._step_value(-self.definition.step),
                    tooltip="Decrease"
                )
            ], spacing=0, tight=True)
            controls.append(step_controls)
        
        return ft.Row(controls, spacing=8, alignment=ft.MainAxisAlignment.START)
    
    def _parse_value(self, value: Any) -> tuple[Optional[float], Optional[str]]:
        """Parse value into numeric part and unit"""
        if value is None or value == "":
            return None, None
        
        value_str = str(value).strip()
        
        # Try to extract number and unit
        import re
        match = re.match(r'^(-?\d*\.?\d+)\s*([a-zA-Z%]*)$', value_str)
        if match:
            try:
                numeric = float(match.group(1))
                unit = match.group(2) if match.group(2) else None
                return numeric, unit
            except ValueError:
                pass
        
        # Try just number
        try:
            return float(value_str), None
        except ValueError:
            return None, None
    
    def _handle_numeric_change(self, value: str) -> None:
        """Handle change in numeric value"""
        try:
            numeric_value = float(value) if value else 0
            unit = getattr(self, '_current_unit', None)
            
            if unit:
                full_value = f"{numeric_value}{unit}"
            else:
                full_value = numeric_value
            
            self._handle_change(full_value)
        except ValueError:
            # Invalid number, let validation handle it
            self._handle_change(value)
    
    def _handle_unit_change(self, unit: str) -> None:
        """Handle change in unit"""
        self._current_unit = unit
        try:
            numeric_value = float(self._number_field.value) if self._number_field.value else 0
            full_value = f"{numeric_value}{unit}"
            self._handle_change(full_value)
        except ValueError:
            pass
    
    def _step_value(self, step: float) -> None:
        """Step the value up or down"""
        try:
            current = float(self._number_field.value) if self._number_field.value else 0
            new_value = current + step
            
            # Respect min/max bounds
            if self.definition.min_value is not None:
                new_value = max(new_value, self.definition.min_value)
            if self.definition.max_value is not None:
                new_value = min(new_value, self.definition.max_value)
            
            self._number_field.value = str(new_value)
            self._handle_numeric_change(str(new_value))
            self.update()
        except ValueError:
            pass
    
    def _update_input_value(self, value: Any) -> None:
        numeric_value, unit = self._parse_value(value)
        self._number_field.value = str(numeric_value) if numeric_value is not None else ""
        if hasattr(self, '_unit_dropdown') and unit:
            self._unit_dropdown.value = unit


class BooleanPropertyInput(PropertyInputBase):
    """Boolean input as checkbox or switch"""
    
    def _build_input_control(self) -> ft.Control:
        self._checkbox = ft.Checkbox(
            value=bool(self.value) if self.value is not None else False,
            on_change=lambda e: self._handle_change(e.control.value),
            label="",  # Label is handled by base class
        )
        
        return self._checkbox
    
    def _update_input_value(self, value: Any) -> None:
        self._checkbox.value = bool(value) if value is not None else False


class SelectPropertyInput(PropertyInputBase):
    """Select/dropdown input"""
    
    def _build_input_control(self) -> ft.Control:
        # Build options from property definition
        options = []
        
        if self.definition.options:
            for option in self.definition.options:
                if hasattr(option, 'value'):  # PropertyOption
                    options.append(ft.dropdown.Option(
                        key=str(option.value),
                        text=option.label
                    ))
                else:  # Simple string option
                    options.append(ft.dropdown.Option(
                        key=str(option),
                        text=str(option)
                    ))
        
        self._dropdown = ft.Dropdown(
            options=options,
            value=str(self.value) if self.value is not None else None,
            on_change=lambda e: self._handle_change(e.control.value),
            border_radius=6,
            text_size=14,
            border_color="#D1D5DB",
            focused_border_color="#5E6AD2",
            # Enable search for long lists
            enable_search=len(options) > 10 if options else False
        )
        
        return self._dropdown
    
    def _update_input_value(self, value: Any) -> None:
        self._dropdown.value = str(value) if value is not None else None


# Factory function for creating property inputs
def create_property_input(
    definition: PropertyDefinition,
    value: Any,
    on_change: Callable[[str, Any], None],
    **kwargs
) -> PropertyInputBase:
    """
    Factory function to create appropriate property input based on type
    CLAUDE.md #1.4: Extensibility - easy to add new types
    """
    # Import advanced inputs to avoid circular imports
    try:
        from advanced_inputs import create_advanced_property_input
        from color_picker import create_color_property_input
        from spacing_input import create_spacing_property_input, create_border_property_input
        
        # Check for advanced input types first
        if definition.type in [PropertyType.FILE, PropertyType.ICON, PropertyType.DATE, PropertyType.RANGE]:
            return create_advanced_property_input(definition, value, on_change, **kwargs)
        elif definition.type == PropertyType.COLOR:
            return create_color_property_input(definition, value, on_change, **kwargs)
        elif definition.type == PropertyType.SPACING:
            return create_spacing_property_input(definition, value, on_change, **kwargs)
        elif definition.type == PropertyType.BORDER:
            return create_border_property_input(definition, value, on_change, **kwargs)
    except ImportError:
        logger.warning("Advanced input types not available")
    
    # Basic input types
    input_classes = {
        PropertyType.TEXT: TextPropertyInput,
        PropertyType.TEXTAREA: TextPropertyInput,
        PropertyType.NUMBER: NumberPropertyInput,
        PropertyType.SIZE: NumberPropertyInput,
        PropertyType.BOOLEAN: BooleanPropertyInput,
        PropertyType.SELECT: SelectPropertyInput,
        PropertyType.RADIO: SelectPropertyInput,
    }
    
    input_class = input_classes.get(definition.type)
    if input_class:
        return input_class(definition, value, on_change, **kwargs)
    else:
        # Fallback to text input with warning
        logger.warning(f"No specific input for type {definition.type}, using text input")
        return TextPropertyInput(definition, value, on_change, **kwargs)