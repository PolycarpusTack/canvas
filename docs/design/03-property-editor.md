# Property Editor - Solution Design Document

## Overview
The Property Editor allows users to modify component properties through a user-friendly interface with different input types based on the property type.

## Functional Requirements

### 1. Property Display
- Show properties for selected component
- Group properties by category (Content, Style, Advanced)
- Display appropriate input controls
- Show current values

### 2. Property Editing
- Real-time updates as user types
- Validation with error messages
- Undo/redo support
- Reset to default values

### 3. Input Types
- Text fields (single/multi-line)
- Number inputs with units
- Color pickers
- Select dropdowns
- Toggle switches
- File uploads
- Custom editors (gradient, shadow)

### 4. Advanced Features
- Property search/filter
- Conditional properties
- Property inheritance
- Responsive breakpoints

## Technical Specifications

### Property Definition Schema

```python
@dataclass
class PropertyDefinition:
    name: str                   # Internal property name
    label: str                  # Display label
    category: str               # Category for grouping
    type: PropertyType          # Input type
    default_value: Any          # Default value
    options: Optional[List]     # For select/radio
    validation: Optional[Dict]  # Validation rules
    units: Optional[List[str]]  # Available units (px, %, em)
    min_value: Optional[float]  # For numeric inputs
    max_value: Optional[float]  # For numeric inputs
    step: Optional[float]       # For numeric inputs
    placeholder: Optional[str]  # Input placeholder
    help_text: Optional[str]    # Tooltip/help
    depends_on: Optional[Dict]  # Conditional display
    responsive: bool            # Supports breakpoints

class PropertyType(Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    COLOR = "color"
    SELECT = "select"
    TOGGLE = "toggle"
    RANGE = "range"
    FILE = "file"
    GRADIENT = "gradient"
    SHADOW = "shadow"
    SPACING = "spacing"      # Special 4-value input
    BORDER = "border"        # Composite border input
```

### Property Registry

```python
# Define properties for each component type
COMPONENT_PROPERTIES = {
    "button": [
        PropertyDefinition(
            name="text",
            label="Button Text",
            category="Content",
            type=PropertyType.TEXT,
            default_value="Button",
            placeholder="Enter button text"
        ),
        PropertyDefinition(
            name="variant",
            label="Variant",
            category="Style",
            type=PropertyType.SELECT,
            default_value="primary",
            options=["primary", "secondary", "outline", "ghost"]
        ),
        PropertyDefinition(
            name="size",
            label="Size",
            category="Style",
            type=PropertyType.SELECT,
            default_value="medium",
            options=["small", "medium", "large"]
        ),
        PropertyDefinition(
            name="width",
            label="Width",
            category="Layout",
            type=PropertyType.NUMBER,
            default_value="auto",
            units=["auto", "px", "%", "rem"],
            min_value=0
        )
    ],
    # More component definitions...
}
```

### Property Editor API

```python
class PropertyEditor:
    def set_component(component: Component) -> None
    def get_properties() -> List[PropertyDefinition]
    def update_property(name: str, value: Any) -> None
    def validate_property(name: str, value: Any) -> ValidationResult
    def reset_property(name: str) -> None
    def reset_all_properties() -> None
    def search_properties(query: str) -> List[PropertyDefinition]
    def get_property_categories() -> List[str]
    def set_breakpoint(breakpoint: str) -> None
```

### Input Components

```python
class PropertyInput:
    """Base class for property inputs"""
    def __init__(self, definition: PropertyDefinition, value: Any):
        self.definition = definition
        self.value = value
        self.on_change = None
        self.on_validate = None
    
    def render(self) -> ft.Control:
        raise NotImplementedError
    
    def validate(self) -> ValidationResult:
        return self.on_validate(self.value) if self.on_validate else ValidationResult(True)

class TextPropertyInput(PropertyInput):
    def render(self) -> ft.Control:
        return ft.TextField(
            label=self.definition.label,
            value=str(self.value) if self.value else "",
            placeholder=self.definition.placeholder,
            on_change=lambda e: self.on_change(e.control.value),
            error_text=None
        )

class ColorPropertyInput(PropertyInput):
    def render(self) -> ft.Control:
        return ft.Row([
            ft.Container(
                width=36,
                height=36,
                bgcolor=self.value or "#FFFFFF",
                border_radius=6,
                on_click=self._open_color_picker
            ),
            ft.TextField(
                value=self.value or "",
                expand=True,
                on_change=lambda e: self._update_color(e.control.value)
            )
        ])

class SpacingPropertyInput(PropertyInput):
    """4-value input for margin/padding"""
    def render(self) -> ft.Control:
        values = self._parse_spacing(self.value)
        return ft.Column([
            ft.Text(self.definition.label),
            ft.Row([
                self._create_input("Top", values[0]),
                self._create_input("Right", values[1]),
                self._create_input("Bottom", values[2]),
                self._create_input("Left", values[3])
            ])
        ])
```

## Implementation Guidelines

### 1. Property Panel Layout

```python
def build_property_panel():
    return ft.Column([
        # Header with component name
        ft.Row([
            ft.Icon(get_component_icon(component.type)),
            ft.Text(component.name, weight="bold"),
            ft.IconButton(icon="close", on_click=deselect_component)
        ]),
        
        # Search bar
        ft.TextField(
            prefix_icon="search",
            hint_text="Search properties...",
            on_change=filter_properties
        ),
        
        # Category tabs
        ft.Tabs([
            ft.Tab(text="Content", content=build_content_properties()),
            ft.Tab(text="Style", content=build_style_properties()),
            ft.Tab(text="Layout", content=build_layout_properties()),
            ft.Tab(text="Advanced", content=build_advanced_properties())
        ]),
        
        # Responsive breakpoint selector
        ft.SegmentedButton(
            segments=[
                ft.Segment(value="base", label="Base"),
                ft.Segment(value="sm", label="SM"),
                ft.Segment(value="md", label="MD"),
                ft.Segment(value="lg", label="LG"),
                ft.Segment(value="xl", label="XL")
            ],
            selected=["base"],
            on_change=change_breakpoint
        )
    ])
```

### 2. Property Updates

```python
def handle_property_change(property_name: str, new_value: Any):
    # 1. Validate value
    validation = validate_property(property_name, new_value)
    if not validation.is_valid:
        show_error(validation.message)
        return
    
    # 2. Update component
    old_value = component.get_property(property_name)
    component.set_property(property_name, new_value)
    
    # 3. Record for undo
    undo_manager.record({
        "type": "property_change",
        "component_id": component.id,
        "property": property_name,
        "old_value": old_value,
        "new_value": new_value
    })
    
    # 4. Update canvas
    canvas.update_component(component)
    
    # 5. Save state
    auto_save()
```

### 3. Conditional Properties

```python
def evaluate_conditions(component: Component) -> List[PropertyDefinition]:
    """Return properties that should be visible based on conditions"""
    visible_properties = []
    
    for prop in get_all_properties(component.type):
        if prop.depends_on:
            # Check condition
            condition_met = True
            for dep_prop, dep_value in prop.depends_on.items():
                actual_value = component.get_property(dep_prop)
                if isinstance(dep_value, list):
                    condition_met &= actual_value in dep_value
                else:
                    condition_met &= actual_value == dep_value
            
            if condition_met:
                visible_properties.append(prop)
        else:
            visible_properties.append(prop)
    
    return visible_properties
```

### 4. Property Validation

```python
class PropertyValidator:
    @staticmethod
    def validate_color(value: str) -> ValidationResult:
        # Check hex, rgb, rgba, hsl, hsla
        patterns = [
            r'^#[0-9A-Fa-f]{3}$',
            r'^#[0-9A-Fa-f]{6}$',
            r'^#[0-9A-Fa-f]{8}$',
            r'^rgb\(\d{1,3},\s*\d{1,3},\s*\d{1,3}\)$',
            r'^rgba\(\d{1,3},\s*\d{1,3},\s*\d{1,3},\s*[0-1]\.?\d*\)$'
        ]
        
        for pattern in patterns:
            if re.match(pattern, value):
                return ValidationResult(True)
        
        return ValidationResult(False, "Invalid color format")
    
    @staticmethod
    def validate_unit_value(value: str, allowed_units: List[str]) -> ValidationResult:
        # Parse number and unit
        match = re.match(r'^(-?\d+\.?\d*)\s*(\w+)?$', value)
        if not match:
            return ValidationResult(False, "Invalid format")
        
        number, unit = match.groups()
        if unit and unit not in allowed_units:
            return ValidationResult(False, f"Unit must be one of: {', '.join(allowed_units)}")
        
        return ValidationResult(True)
```

### 5. Custom Property Editors

```python
class GradientEditor(PropertyInput):
    """Custom editor for CSS gradients"""
    def render(self):
        return ft.Column([
            ft.Text(self.definition.label),
            ft.Row([
                ft.Dropdown(
                    options=["linear", "radial", "conic"],
                    value="linear",
                    width=100
                ),
                ft.TextField(
                    hint_text="45deg",
                    width=80
                )
            ]),
            # Color stops
            ft.Column([
                self._create_color_stop(0),
                self._create_color_stop(100),
                ft.TextButton("Add Stop", on_click=self._add_stop)
            ]),
            # Preview
            ft.Container(
                height=50,
                gradient=self._build_gradient(),
                border_radius=6
            )
        ])

class BoxShadowEditor(PropertyInput):
    """Custom editor for box shadows"""
    def render(self):
        return ft.Column([
            ft.Text(self.definition.label),
            ft.Row([
                ft.TextField(label="X", width=60),
                ft.TextField(label="Y", width=60),
                ft.TextField(label="Blur", width=60),
                ft.TextField(label="Spread", width=60)
            ]),
            ColorPropertyInput(
                PropertyDefinition(name="color", label="Color", type=PropertyType.COLOR),
                "#000000"
            ).render(),
            ft.Checkbox(label="Inset"),
            # Preview
            ft.Container(
                height=100,
                width=100,
                bgcolor="white",
                shadow=self._build_shadow()
            )
        ])
```

## Error Handling

- **Invalid values**: Show inline error messages
- **Type mismatches**: Coerce or reject with explanation
- **Out of range**: Clamp to valid range
- **Circular dependencies**: Detect and prevent

## Performance Optimization

- Debounce text input changes
- Batch property updates
- Memoize property definitions
- Virtual scrolling for many properties
- Lazy load custom editors

## Testing Requirements

### Unit Tests
- Property validation functions
- Value parsing and formatting
- Conditional property logic
- Unit conversions

### Integration Tests
- Property updates reflect in canvas
- Undo/redo functionality
- Breakpoint switching
- Search/filter functionality

## Accessibility

- Keyboard navigation between inputs
- Clear labels and help text
- Error messages for screen readers
- High contrast mode support

## Future Enhancements

1. **Property Presets**: Save and apply property combinations
2. **Global Variables**: Define and use CSS variables
3. **Animation Editor**: Timeline-based animation properties
4. **Data Binding**: Bind properties to data sources
5. **Computed Properties**: Properties based on calculations
6. **Property History**: Show property change history
7. **Bulk Edit**: Edit multiple components at once
8. **AI Suggestions**: Smart property recommendations

## Example Usage

```python
# Select a component
canvas.select_component(button_id)

# Property editor updates
property_editor.set_component(button)

# User changes a property
property_editor.on_property_change = lambda name, value: 
    update_component_property(button, name, value)

# Search for properties
results = property_editor.search_properties("color")

# Switch to responsive mode
property_editor.set_breakpoint("md")  # Medium screens
```