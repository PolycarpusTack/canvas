# Enhanced Property Editor System

A professional-grade property editing system for the Canvas visual editor, built with enterprise-level code quality and following CLAUDE.md development guidelines.

## 🌟 Features

### Core Features ✅
- **Advanced Property Definitions** - Comprehensive property schema with validation, dependencies, and metadata
- **Thread-Safe Registry** - Centralized property management with caching and validation
- **Accessibility-First Inputs** - WCAG 2.1 AA compliant property input components
- **Advanced Color Picker** - Professional color picker with wheel, presets, and format conversion
- **Smart Spacing Input** - 4-value spacing input with linked values and visual preview
- **Comprehensive Validation** - Robust validation system with meaningful error messages
- **Search & Filtering** - Real-time property search and category filtering
- **Extensive Testing** - Comprehensive unit test coverage

### Advanced Features 🚧
- **Gradient Editor** - Visual gradient editor (pending implementation)
- **Shadow Editor** - Box shadow visual editor (pending implementation) 
- **Property Dependencies** - Conditional property visibility (partially implemented)
- **Responsive Breakpoints** - Breakpoint-specific property values (UI implemented)

## 📁 Architecture

```
src/components/
├── property_definitions.py      # Core property definition models
├── property_registry.py         # Thread-safe property registry
├── default_component_properties.py  # Default component definitions
└── component_types.py          # Legacy component types (enhanced)

src/ui/inputs/
├── property_input_base.py      # Base property input classes
├── color_picker.py             # Advanced color picker component
└── spacing_input.py            # Spacing and border input components

src/ui/panels/
├── enhanced_properties_panel.py  # Main property editor panel
└── properties_fixed.py          # Legacy properties panel (enhanced)

tests/
└── test_property_system.py     # Comprehensive test suite
```

## 🚀 Quick Start

### 1. Register Component Properties

```python
from src.components.property_registry import get_registry
from src.components.property_definitions import PropertyDefinition, PropertyType, PropertyCategory

# Get the singleton registry
registry = get_registry()

# Define button properties
button_properties = [
    PropertyDefinition(
        name="text",
        label="Button Text", 
        category=PropertyCategory.CONTENT,
        type=PropertyType.TEXT,
        default_value="Button",
        required=True,
        placeholder="Enter button text",
        icon="text_fields"
    ),
    PropertyDefinition(
        name="variant",
        label="Style Variant",
        category=PropertyCategory.STYLE,
        type=PropertyType.SELECT,
        default_value="primary",
        options=[
            PropertyOption("primary", "Primary"),
            PropertyOption("secondary", "Secondary"),
            PropertyOption("danger", "Danger")
        ]
    ),
    PropertyDefinition(
        name="background_color",
        label="Background Color",
        category=PropertyCategory.STYLE,
        type=PropertyType.COLOR,
        default_value="#5E6AD2",
        responsive=True,
        animatable=True
    )
]

# Register the component
registry.register_component_properties("button", button_properties)
```

### 2. Use the Enhanced Properties Panel

```python
import flet as ft
from src.ui.panels.enhanced_properties_panel import EnhancedPropertiesPanel

def on_property_change(component_id: str, property_name: str, value: Any):
    print(f"Component {component_id} property {property_name} changed to: {value}")

# Create the properties panel
properties_panel = EnhancedPropertiesPanel(on_property_change=on_property_change)

# Set a component to edit
component = Component(id="btn_1", type="button", name="My Button")
properties_panel.set_component(component)
```

### 3. Create Custom Property Inputs

```python
from src.ui.inputs.property_input_base import PropertyInputBase

class CustomPropertyInput(PropertyInputBase):
    """Custom property input example"""
    
    def _build_input_control(self) -> ft.Control:
        # Build your custom input UI
        return ft.TextField(
            value=str(self.value) if self.value else "",
            on_change=lambda e: self._handle_change(e.control.value)
        )
    
    def _update_input_value(self, value: Any) -> None:
        # Update the input when value changes externally
        pass
```

## 🎨 Property Types

The system supports a comprehensive set of property types:

### Basic Types
- `TEXT` - Single line text input
- `TEXTAREA` - Multi-line text input  
- `NUMBER` - Numeric input with validation
- `BOOLEAN` - Checkbox/toggle input
- `SELECT` - Dropdown selection
- `RADIO` - Radio button selection

### Advanced Types
- `COLOR` - Advanced color picker with formats
- `SPACING` - 4-value spacing input (margin/padding)
- `SIZE` - Size input with unit selector
- `BORDER` - Border editor (width, style, color)
- `URL` - URL input with validation
- `FILE` - File upload input
- `RANGE` - Slider input
- `DATE` - Date picker

### Special Types
- `GRADIENT` - Gradient editor (coming soon)
- `SHADOW` - Box shadow editor (coming soon)
- `ANIMATION` - Animation properties
- `TRANSFORM` - CSS transforms

## 🔧 Property Features

### Validation
```python
PropertyDefinition(
    name="font_size",
    validation=PropertyValidation(
        min_value=8,
        max_value=72,
        error_messages={
            "min_value": "Font size too small for readability",
            "max_value": "Font size too large"
        }
    )
)
```

### Dependencies
```python
PropertyDefinition(
    name="background_color",
    dependencies=[
        PropertyDependency("variant", "equals", "primary", "show")
    ]
)
```

### Responsive Design
```python
PropertyDefinition(
    name="font_size",
    responsive=True,  # Enables breakpoint-specific values
    default_value=ResponsiveValue(
        base="16px",
        breakpoints={
            "sm": "14px",
            "md": "18px", 
            "lg": "20px"
        }
    )
)
```

### Animation Support
```python
PropertyDefinition(
    name="background_color",
    animatable=True,
    animation_config=AnimationConfig(
        duration=0.3,
        easing="ease-out",
        property_name="background-color"
    )
)
```

## 🎯 Property Categories

Properties are organized into logical categories:

- **CONTENT** - Content and data properties
- **STYLE** - Visual styling properties  
- **LAYOUT** - Layout and positioning
- **SPACING** - Margin and padding
- **TYPOGRAPHY** - Text and font properties
- **EFFECTS** - Visual effects (shadows, filters)
- **INTERACTIONS** - Event handlers and behaviors
- **RESPONSIVE** - Responsive design properties
- **ADVANCED** - Advanced/developer properties

## 🔍 Search & Filtering

The enhanced properties panel includes:

- **Real-time search** - Search by name, label, description, or tags
- **Category filtering** - Filter by property categories
- **Keyboard shortcuts** - Efficient keyboard navigation
- **Property grouping** - Collapsible category groups

## ✅ Validation System

Comprehensive validation with:

- **Type validation** - Ensures correct data types
- **Range validation** - Min/max constraints
- **Pattern validation** - Regex pattern matching
- **Custom validators** - Extensible validation functions
- **Helpful error messages** - Clear, actionable feedback
- **Real-time validation** - Instant feedback as you type

## 🎨 Color System

Advanced color picker features:

- **Multiple formats** - HEX, RGB, HSL support
- **Color wheel** - Visual color selection
- **Preset swatches** - Common color palettes
- **Recent colors** - Color history
- **Format conversion** - Seamless format switching
- **Accessibility** - WCAG AA compliant

## 📏 Spacing System

Smart spacing input with:

- **4-value support** - Top, right, bottom, left
- **Linked values** - Link/unlink sides
- **Visual preview** - See spacing changes live
- **Unit support** - px, em, rem, %, auto
- **Quick presets** - Common spacing values
- **CSS shorthand** - Optimized CSS output

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/test_property_system.py -v

# Run specific test class
python -m pytest tests/test_property_system.py::TestPropertyDefinition -v

# Run with coverage
python -m pytest tests/test_property_system.py --cov=src/components --cov=src/ui/inputs
```

Test coverage includes:
- Property definition validation
- Registry thread safety
- Color utility functions
- Spacing value parsing
- Validation systems
- Integration tests

## 🔧 Configuration

### Registry Configuration
```python
# Custom validator registration
registry.register_custom_validator("email", validate_email_format)

# Built-in validator customization
registry.register_validator(PropertyType.COLOR, CustomColorValidator())
```

### Performance Tuning
```python
# Adjust cache TTL (default: 5 minutes)
registry._cache_ttl = 600  # 10 minutes

# Virtual scrolling for large property lists
properties_panel = EnhancedPropertiesPanel(
    virtual_scrolling=True,
    item_height=80
)
```

## 🚧 Roadmap

### Immediate (Next Sprint)
- [ ] Gradient editor implementation
- [ ] Shadow editor with visual preview
- [ ] Enhanced property dependencies
- [ ] Animation property inputs

### Short Term
- [ ] Custom property type system
- [ ] Property templates and presets
- [ ] Bulk property operations
- [ ] Property history/undo system

### Long Term
- [ ] Visual property binding
- [ ] Advanced responsive controls
- [ ] Property expressions/formulas
- [ ] Plugin system for custom inputs

## 🤝 Contributing

### Code Style
- Follow CLAUDE.md guidelines
- Use type hints for all functions
- Include comprehensive docstrings
- Add unit tests for new features

### Adding New Property Types
1. Define the property type in `PropertyType` enum
2. Create input component extending `PropertyInputBase`
3. Add validator if needed
4. Update factory function
5. Add comprehensive tests

### Adding New Validators
1. Extend `PropertyValidator` base class
2. Implement `validate()` method
3. Register with registry
4. Add unit tests

## 📚 API Reference

### Core Classes

#### PropertyDefinition
```python
class PropertyDefinition:
    name: str                    # Internal property name
    label: str                   # Display label
    category: PropertyCategory   # Organization category
    type: PropertyType          # Input type
    default_value: Any          # Default value
    validation: PropertyValidation  # Validation rules
    dependencies: List[PropertyDependency]  # Conditional logic
    responsive: bool = False    # Responsive support
    animatable: bool = False    # Animation support
```

#### PropertyRegistry
```python
class PropertyRegistry:
    def register_component_properties(component_type: str, properties: List[PropertyDefinition])
    def get_component_properties(component_type: str) -> List[PropertyDefinition]
    def validate_property_value(component_type: str, property_name: str, value: Any) -> ValidationResult
    def search_properties(query: str, component_type: str = None) -> List[PropertyDefinition]
```

#### PropertyInputBase
```python
class PropertyInputBase(ft.Container, ABC):
    def __init__(definition: PropertyDefinition, value: Any, on_change: Callable)
    def set_value(value: Any, validate: bool = True)
    def get_value() -> Any
    def is_valid() -> bool
    def reset() -> None
```

## 📄 License

This Property Editor System is part of the Canvas visual editor project and follows the same licensing terms.

---

**Built with ❤️ following CLAUDE.md enterprise development guidelines**