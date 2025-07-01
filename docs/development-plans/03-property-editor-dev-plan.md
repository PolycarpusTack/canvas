# Property Editor - Development Plan

## Phase 1: Solution Design Analysis & Validation

### 1. Initial Understanding
- **Goal**: Build comprehensive property editing system with various input types
- **Stack**: Flet UI components, Python property system
- **Components**: PropertyEditor, PropertyInput types, Validation system
- **User Personas**: Designers editing component properties

### 2. Clarity Assessment
- **Property Schema**: High (3) - Well-defined PropertyDefinition structure
- **Input Types**: High (3) - Clear mapping of types to UI controls
- **Validation Rules**: Medium (2) - Need specific validation patterns
- **Conditional Properties**: Medium (2) - Dependency logic needs examples
- **Overall Clarity**: High (3)

### 3. Technical Feasibility
- **Basic Inputs**: Low risk (1) - Standard form controls
- **Custom Editors**: Medium risk (2) - Gradient/shadow editors complex
- **Real-time Updates**: Medium risk (2) - Performance with many properties
- **Responsive Properties**: High risk (3) - Breakpoint management complex

### 4. Security Assessment
- **Input Sanitization**: Prevent XSS in property values
- **File Upload**: Validate file types and sizes
- **Color Values**: Validate color formats

### 5. Compliance
- **Accessibility**: WCAG 2.1 AA for all inputs
- **Internationalization**: Support for RTL layouts

**Recommendation**: PROCEEDING with backlog generation

---

## EPIC A: Core Property System

Implement property definitions, basic input types, and real-time updates.

**Definition of Done:**
- ✓ All standard input types functional
- ✓ Real-time property updates < 16ms
- ✓ Comprehensive validation system

**Business Value:** Essential for visual editing experience

**Risk Assessment:**
- Performance with many properties (Medium/2) - Virtual scrolling needed
- Complex property dependencies (Medium/2) - Clear state management
- Custom input types (Medium/2) - Extensible architecture

**Cross-Functional Requirements:**
- Accessibility: All inputs keyboard navigable with labels
- Performance: Updates complete in < 16ms
- Security: Input validation prevents injection
- Observability: Log all property changes

---

### USER STORY A-1: Property Definition System

**ID & Title:** A-1: Create Property Schema and Registry
**User Persona Narrative:** As a developer, I want to define component properties so designers can edit them
**Business Value:** High (3)
**Priority Score:** 5
**Story Points:** M

**Acceptance Criteria:**
```gherkin
Given I define a button component
When I specify its properties
Then I can define text, color, size, and behavior properties
And each property has appropriate validation rules

Given a property has dependencies
When the parent property changes
Then dependent properties update accordingly
And invalid combinations are prevented
```

**External Dependencies:** None
**Technical Debt Considerations:** Schema versioning for future updates
**Test Data Requirements:** Sample component definitions

---

#### TASK A-1-T1: Implement Property Definition Models

**Goal:** Create comprehensive property definition system

**Token Budget:** 8,000 tokens

**Required Interfaces:**
```python
@dataclass
class PropertyDefinition:
    """
    CLAUDE.md #1.4: Extensibility - design for future enhancements
    CLAUDE.md #4.1: Explicit types for all fields
    """
    name: str                          # Internal property name
    label: str                         # Display label
    category: PropertyCategory         # Grouping category
    type: PropertyType                # Input type
    default_value: Any                # Default value
    
    # Validation
    validation: Optional[PropertyValidation] = None
    required: bool = False
    
    # Type-specific options
    options: Optional[List[PropertyOption]] = None  # For select/radio
    min_value: Optional[Union[int, float]] = None   # For numeric
    max_value: Optional[Union[int, float]] = None   # For numeric
    step: Optional[Union[int, float]] = None        # For numeric
    units: Optional[List[str]] = None               # Available units
    
    # UI hints
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    icon: Optional[str] = None
    
    # Advanced features
    depends_on: Optional[PropertyDependency] = None
    responsive: bool = False
    animatable: bool = False
    
    def __post_init__(self):
        """CLAUDE.md #2.1.1: Validate all inputs"""
        self._validate_definition()
```

**Validation System:**
```python
@dataclass
class PropertyValidation:
    """Comprehensive validation rules"""
    pattern: Optional[str] = None          # Regex pattern
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    custom_validator: Optional[Callable] = None
    error_message: Optional[str] = None
    
    def validate(self, value: Any) -> ValidationResult:
        """CLAUDE.md #2.1.2: Meaningful error messages"""
        errors = []
        
        if self.pattern and isinstance(value, str):
            if not re.match(self.pattern, value):
                errors.append(self.error_message or f"Value must match pattern: {self.pattern}")
        
        # Additional validation...
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
```

**Deliverables:**
- Complete property definition models
- Validation system with common validators
- Property categories and organization
- 100% test coverage

**Quality Gates:**
- ✓ All fields strongly typed
- ✓ Validation prevents invalid definitions
- ✓ Serializable for storage
- ✓ Documentation with examples

**Unblocks:** [A-1-T2, A-2-T1]
**Confidence Score:** High (3)

---

#### TASK A-1-T2: Create Property Registry

**Goal:** Implement registry for component property definitions

**Token Budget:** 6,000 tokens

**Implementation:**
```python
class PropertyRegistry:
    """
    CLAUDE.md #1.3: Singleton pattern for consistency
    CLAUDE.md #12.1: Structured logging
    """
    _instance = None
    
    def __init__(self):
        self._definitions: Dict[str, List[PropertyDefinition]] = {}
        self._validators: Dict[PropertyType, PropertyValidator] = {}
        self._lock = threading.RLock()
        self._init_default_validators()
    
    def register_component_properties(
        self,
        component_type: str,
        properties: List[PropertyDefinition]
    ) -> None:
        """
        CLAUDE.md #2.1.4: Thread-safe registration
        """
        with self._lock:
            # Validate no duplicate names
            names = [p.name for p in properties]
            if len(names) != len(set(names)):
                raise ValueError("Duplicate property names")
            
            # Validate all properties
            for prop in properties:
                self._validate_property_definition(prop)
            
            self._definitions[component_type] = properties
            logger.info(f"Registered {len(properties)} properties for {component_type}")
```

**Built-in Properties:**
```python
# Common properties for all components
COMMON_PROPERTIES = [
    PropertyDefinition(
        name="id",
        label="Component ID",
        category=PropertyCategory.ADVANCED,
        type=PropertyType.TEXT,
        validation=PropertyValidation(
            pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$",
            error_message="ID must start with letter, contain only letters, numbers, dash, underscore"
        )
    ),
    PropertyDefinition(
        name="className",
        label="CSS Classes",
        category=PropertyCategory.STYLE,
        type=PropertyType.TEXT,
        placeholder="Enter space-separated class names"
    )
]
```

**Unblocks:** [A-2-T1]
**Confidence Score:** High (3)

---

### USER STORY A-2: Property Input Components

**ID & Title:** A-2: Implement Property Input Types
**User Persona Narrative:** As a designer, I want appropriate input controls for each property type
**Business Value:** High (3)
**Priority Score:** 5
**Story Points:** L

**Acceptance Criteria:**
```gherkin
Given I select a component with color property
When I click the color input
Then I see a color picker
And I can enter hex values manually
And changes update in real-time

Given I edit a spacing property
When I adjust the values
Then I see separate inputs for top/right/bottom/left
And I can link values for uniform spacing
And units are clearly shown
```

---

#### TASK A-2-T1: Implement Base Property Input

**Goal:** Create base class for all property inputs

**Token Budget:** 5,000 tokens

**Base Implementation:**
```python
class PropertyInput(ft.UserControl):
    """
    CLAUDE.md #1.2: DRY - Base class for all inputs
    CLAUDE.md #9.1: Accessibility built-in
    """
    def __init__(
        self,
        definition: PropertyDefinition,
        value: Any,
        on_change: Callable[[str, Any], None],
        on_validate: Optional[Callable[[Any], ValidationResult]] = None
    ):
        super().__init__()
        self.definition = definition
        self.value = value
        self.on_change = on_change
        self.on_validate = on_validate or self._default_validate
        self.error_message: Optional[str] = None
        
    def _default_validate(self, value: Any) -> ValidationResult:
        """Use definition's validation rules"""
        if self.definition.validation:
            return self.definition.validation.validate(value)
        return ValidationResult(is_valid=True)
    
    def _handle_change(self, value: Any) -> None:
        """
        CLAUDE.md #2.1.2: Validate before propagating
        """
        validation = self.on_validate(value)
        
        if validation.is_valid:
            self.error_message = None
            self.on_change(self.definition.name, value)
        else:
            self.error_message = validation.errors[0] if validation.errors else "Invalid value"
        
        self.update()
    
    def build(self) -> ft.Control:
        """Override in subclasses"""
        raise NotImplementedError
```

**Accessibility Requirements:**
```python
def _build_accessible_container(self, input_control: ft.Control) -> ft.Control:
    """
    CLAUDE.md #9.3: Full keyboard access
    CLAUDE.md #9.4: Proper ARIA labels
    """
    return ft.Column([
        ft.Text(
            self.definition.label,
            size=14,
            weight=ft.FontWeight.W_500,
            color="#374151"
        ),
        input_control,
        ft.Text(
            self.error_message or "",
            size=12,
            color="#EF4444",
            visible=bool(self.error_message)
        ) if self.error_message else ft.Container(),
        ft.Text(
            self.definition.help_text or "",
            size=12,
            color="#6B7280",
            visible=bool(self.definition.help_text)
        )
    ], spacing=4)
```

**Unblocks:** [A-2-T2, A-2-T3, A-2-T4]
**Confidence Score:** High (3)

---

#### TASK A-2-T2: Implement Text and Number Inputs

**Goal:** Create text, textarea, and number input types

**Token Budget:** 7,000 tokens

**Implementations:**
```python
class TextPropertyInput(PropertyInput):
    """Text input with validation"""
    
    def build(self) -> ft.Control:
        text_field = ft.TextField(
            value=str(self.value) if self.value is not None else "",
            placeholder=self.definition.placeholder,
            password=self.definition.type == PropertyType.PASSWORD,
            multiline=self.definition.type == PropertyType.TEXTAREA,
            min_lines=3 if self.definition.type == PropertyType.TEXTAREA else 1,
            max_lines=10 if self.definition.type == PropertyType.TEXTAREA else 1,
            on_change=lambda e: self._handle_change(e.control.value),
            error_text=self.error_message,
            helper_text=self.definition.help_text,
            # Accessibility
            label=self.definition.label,
            autofocus=False
        )
        
        return self._build_accessible_container(text_field)


class NumberPropertyInput(PropertyInput):
    """
    CLAUDE.md #2.1.1: Validate numeric ranges
    """
    def build(self) -> ft.Control:
        # Create input with optional unit selector
        controls = [
            ft.TextField(
                value=str(self.value) if self.value is not None else "",
                keyboard_type=ft.KeyboardType.NUMBER,
                on_change=lambda e: self._handle_numeric_change(e.control.value),
                width=150,
                error_text=self.error_message
            )
        ]
        
        # Add unit selector if applicable
        if self.definition.units:
            controls.append(
                ft.Dropdown(
                    options=[ft.dropdown.Option(unit) for unit in self.definition.units],
                    value=self._extract_unit(self.value),
                    on_change=lambda e: self._handle_unit_change(e.control.value),
                    width=80
                )
            )
        
        return self._build_accessible_container(
            ft.Row(controls, spacing=8)
        )
```

**Unblocks:** [A-2-T3]
**Confidence Score:** High (3)

---

#### TASK A-2-T3: Implement Color Picker Input

**Goal:** Create color input with picker and validation

**Token Budget:** 8,000 tokens

**Implementation:**
```python
class ColorPropertyInput(PropertyInput):
    """
    CLAUDE.md #7.2: Validate color input formats
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.picker_open = False
        
    def build(self) -> ft.Control:
        return self._build_accessible_container(
            ft.Row([
                # Color preview
                ft.Container(
                    width=36,
                    height=36,
                    bgcolor=self.value or "#FFFFFF",
                    border_radius=6,
                    border=ft.border.all(1, "#D1D5DB"),
                    on_click=lambda e: self._toggle_picker()
                ),
                # Hex input
                ft.TextField(
                    value=self.value or "",
                    prefix_text="#",
                    max_length=6,
                    on_change=lambda e: self._handle_hex_input(e.control.value),
                    width=100,
                    error_text=self.error_message
                ),
                # Format selector
                ft.Dropdown(
                    options=[
                        ft.dropdown.Option("HEX"),
                        ft.dropdown.Option("RGB"),
                        ft.dropdown.Option("HSL")
                    ],
                    value="HEX",
                    width=80,
                    on_change=lambda e: self._change_format(e.control.value)
                )
            ], spacing=8)
        )
    
    def _validate_color(self, value: str) -> ValidationResult:
        """
        CLAUDE.md #2.1.1: Comprehensive validation
        """
        patterns = {
            'hex': r'^#?[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?$',
            'rgb': r'^rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)$',
            'rgba': r'^rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*[01]?\.?\d*\s*\)$',
            'hsl': r'^hsl\(\s*\d{1,3}\s*,\s*\d{1,3}%\s*,\s*\d{1,3}%\s*\)$'
        }
        
        for format_name, pattern in patterns.items():
            if re.match(pattern, value, re.IGNORECASE):
                return ValidationResult(is_valid=True)
        
        return ValidationResult(
            is_valid=False,
            errors=["Invalid color format. Use HEX (#RRGGBB), RGB, or HSL"]
        )
```

**Color Picker Dialog:**
```python
def _show_color_picker(self):
    """Show advanced color picker dialog"""
    # Implementation of color picker with:
    # - Color wheel
    # - RGB/HSL sliders
    # - Preset colors
    # - Recent colors
    # - Eyedropper tool (if supported)
```

**Unblocks:** [A-2-T4]
**Confidence Score:** Medium (2) - Complex UI component

---

#### TASK A-2-T4: Implement Complex Input Types

**Goal:** Create spacing, select, and file inputs

**Token Budget:** 10,000 tokens

**Spacing Input (4-value):**
```python
class SpacingPropertyInput(PropertyInput):
    """
    Margin/Padding input with linked values
    CLAUDE.md #1.4: Extensible for future units
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.linked = True
        self.values = self._parse_spacing(self.value)
        
    def _parse_spacing(self, value: str) -> Dict[str, str]:
        """Parse CSS spacing shorthand"""
        if not value:
            return {"top": "0", "right": "0", "bottom": "0", "left": "0"}
        
        parts = value.split()
        if len(parts) == 1:
            return {k: parts[0] for k in ["top", "right", "bottom", "left"]}
        elif len(parts) == 2:
            return {"top": parts[0], "right": parts[1], "bottom": parts[0], "left": parts[1]}
        elif len(parts) == 3:
            return {"top": parts[0], "right": parts[1], "bottom": parts[2], "left": parts[1]}
        else:
            return {"top": parts[0], "right": parts[1], "bottom": parts[2], "left": parts[3]}
    
    def build(self) -> ft.Control:
        # Link toggle button
        link_button = ft.IconButton(
            icon=ft.icons.LINK if self.linked else ft.icons.LINK_OFF,
            on_click=lambda e: self._toggle_link(),
            tooltip="Link all values"
        )
        
        # Individual inputs
        inputs = {}
        for side in ["top", "right", "bottom", "left"]:
            inputs[side] = ft.TextField(
                value=self.values[side],
                width=60,
                on_change=lambda e, s=side: self._handle_value_change(s, e.control.value),
                label=side.capitalize()[0],  # T, R, B, L
                text_align=ft.TextAlign.CENTER
            )
        
        return self._build_accessible_container(
            ft.Column([
                ft.Row([link_button, ft.Text("Link values")]),
                ft.Row([
                    inputs["top"],
                    inputs["right"],
                    inputs["bottom"],
                    inputs["left"]
                ], spacing=8)
            ], spacing=8)
        )
```

**Select/Dropdown Input:**
```python
class SelectPropertyInput(PropertyInput):
    """Dropdown with search and groups"""
    
    def build(self) -> ft.Control:
        # Support grouped options
        options = []
        for opt in self.definition.options:
            if isinstance(opt, PropertyOptionGroup):
                # Add group header
                options.append(ft.dropdown.Option(
                    key=f"group_{opt.label}",
                    text=opt.label,
                    disabled=True
                ))
                # Add group items
                for item in opt.options:
                    options.append(ft.dropdown.Option(
                        key=item.value,
                        text=f"  {item.label}"  # Indent
                    ))
            else:
                options.append(ft.dropdown.Option(
                    key=opt.value,
                    text=opt.label
                ))
        
        return self._build_accessible_container(
            ft.Dropdown(
                options=options,
                value=self.value,
                on_change=lambda e: self._handle_change(e.control.value),
                # Enable search for long lists
                enable_search=len(options) > 10
            )
        )
```

**Unblocks:** [A-3-T1]
**Confidence Score:** High (3)

---

### USER STORY A-3: Property Categories and Organization

**ID & Title:** A-3: Organize Properties by Category
**User Persona Narrative:** As a designer, I want properties organized logically so I can find them quickly
**Business Value:** Medium (2)
**Priority Score:** 3
**Story Points:** S

---

#### TASK A-3-T1: Implement Property Panel Layout

**Goal:** Create organized property panel with categories

**Token Budget:** 8,000 tokens

**Implementation:**
```python
class PropertyPanel(ft.UserControl):
    """
    CLAUDE.md #1.1: Enterprise-grade UI organization
    CLAUDE.md #12.5: Performance with many properties
    """
    def __init__(self, on_property_change: Callable[[str, str, Any], None]):
        super().__init__()
        self.on_property_change = on_property_change
        self.current_component: Optional[Component] = None
        self.active_tab = "content"
        self.search_query = ""
        self.property_inputs: Dict[str, PropertyInput] = {}
        
    def build(self) -> ft.Control:
        return ft.Column([
            # Header
            self._build_header(),
            
            # Search
            ft.TextField(
                prefix_icon=ft.icons.SEARCH,
                hint_text="Search properties...",
                on_change=lambda e: self._filter_properties(e.control.value),
                border_radius=8,
                height=40
            ),
            
            # Category tabs
            self._build_tabs(),
            
            # Property list (virtual scrolling for performance)
            ft.ListView(
                controls=self._build_property_list(),
                height=400,
                spacing=10,
                # Virtual scrolling for many properties
                item_extent=80  # Estimated item height
            ),
            
            # Responsive breakpoints
            self._build_breakpoint_selector()
        ], spacing=16, expand=True)
```

**Category Organization:**
```python
def _organize_properties_by_category(
    self,
    properties: List[PropertyDefinition]
) -> Dict[PropertyCategory, List[PropertyDefinition]]:
    """Group and sort properties"""
    categorized = {}
    
    # Group by category
    for prop in properties:
        if prop.category not in categorized:
            categorized[prop.category] = []
        categorized[prop.category].append(prop)
    
    # Sort within categories
    for category, props in categorized.items():
        props.sort(key=lambda p: (p.category.priority, p.label))
    
    return categorized
```

**Unblocks:** [B-1-T1]
**Confidence Score:** High (3)

---

## EPIC B: Advanced Property Features

Implement conditional properties, validation feedback, and responsive design support.

**Definition of Done:**
- ✓ Conditional properties show/hide correctly
- ✓ Validation provides helpful feedback
- ✓ Responsive breakpoints functional

**Business Value:** Advanced editing capabilities

---

### Technical Debt Prevention

```python
# Property Editor Debt Prevention Rules
class PropertyEditorRules:
    """CLAUDE.md Technical Debt Management"""
    
    MAX_PROPERTIES_PER_COMPONENT = 50
    MAX_CUSTOM_VALIDATORS = 10
    MAX_DEPENDENCY_DEPTH = 3
    
    @staticmethod
    def check_property_complexity(definition: PropertyDefinition) -> List[str]:
        """Identify potential debt"""
        issues = []
        
        if definition.depends_on and definition.depends_on.depth > 3:
            issues.append("Deep dependency chain - consider flattening")
        
        if definition.validation and len(definition.validation.rules) > 5:
            issues.append("Complex validation - consider simplifying")
        
        return issues
```

---

## Testing Strategy

### Property Input Testing
```python
@pytest.mark.parametrize("input_type,test_value,expected", [
    (PropertyType.COLOR, "#FF0000", True),
    (PropertyType.COLOR, "red", False),
    (PropertyType.NUMBER, "42", True),
    (PropertyType.NUMBER, "abc", False),
    (PropertyType.SPACING, "10px 20px", True),
])
def test_property_validation(input_type, test_value, expected):
    """CLAUDE.md #6.2: Comprehensive validation testing"""
    definition = PropertyDefinition(
        name="test",
        type=input_type,
        # ... setup
    )
    
    input_component = PropertyInputFactory.create(definition)
    result = input_component.validate(test_value)
    
    assert result.is_valid == expected
```

### Accessibility Testing
```python
def test_property_inputs_accessible():
    """CLAUDE.md #9: WCAG compliance"""
    for input_type in PropertyType:
        input_component = PropertyInputFactory.create(
            PropertyDefinition(name="test", type=input_type)
        )
        
        # Check for labels
        assert input_component.has_label()
        
        # Check keyboard navigation
        assert input_component.is_keyboard_accessible()
        
        # Check ARIA attributes
        assert input_component.has_aria_describedby()
```

---

## Performance Optimization

```python
class PropertyPanelOptimizations:
    """CLAUDE.md #1.5: Performance optimizations"""
    
    def implement_virtual_scrolling(self):
        """Only render visible properties"""
        
    def implement_debounced_updates(self):
        """Batch property changes"""
        
    def implement_property_caching(self):
        """Cache computed property values"""
```

---

## Security Checklist

- [ ] Sanitize all property values before display
- [ ] Validate file uploads (type, size, content)
- [ ] Prevent script injection in text properties
- [ ] Validate URLs in link properties
- [ ] Rate limit property updates