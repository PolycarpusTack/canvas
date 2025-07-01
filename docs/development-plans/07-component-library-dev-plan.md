# Component Library - Development Plan

## Phase 1: Solution Design Analysis & Validation

### 1. Initial Understanding
- **Goal**: Build comprehensive component library with search, custom components, and previews
- **Stack**: Python/Flet, JSON storage, component registry pattern
- **Components**: ComponentRegistry, ComponentFactory, SearchEngine, CustomComponentManager
- **User Personas**: Designers browsing and using components to build interfaces

### 2. Clarity Assessment
- **Built-in Components**: High (3) - Well-defined component definitions
- **Custom Components**: High (3) - Clear creation and management flow
- **Search System**: High (3) - Comprehensive search with filters
- **Preview System**: Medium (2) - Preview generation complexity
- **Component Constraints**: High (3) - Clear parent/child rules
- **Overall Clarity**: High (3)

### 3. Technical Feasibility
- **Component Registry**: Low risk (1) - Standard registry pattern
- **Search Implementation**: Low risk (1) - Basic text search
- **Custom Components**: Medium risk (2) - Serialization complexity
- **Preview Generation**: High risk (3) - Real-time rendering challenges
- **Import/Export**: Medium risk (2) - Version compatibility

### 4. Security Assessment
- **Component Validation**: Prevent malicious component definitions
- **Import Security**: Validate imported components
- **Path Traversal**: Secure custom component storage
- **Content Sanitization**: Prevent XSS in component content

### 5. Performance Requirements
- **Search Response**: < 100ms for 1000 components
- **Preview Generation**: < 500ms per component
- **Component Creation**: < 50ms
- **Library Load Time**: < 1s for full library

**Recommendation**: PROCEEDING with backlog generation

---

## EPIC A: Core Component System

Implement the foundation of the component library with registry, factory, and built-in components.

**Definition of Done:**
- ✓ Component registry with all built-in components
- ✓ Component factory creating instances
- ✓ Component constraints enforced
- ✓ Drag and drop integration ready

**Business Value:** Essential building blocks for Canvas Editor

**Risk Assessment:**
- Component compatibility (Medium/2) - Careful constraint design
- Performance with many components (Medium/2) - Efficient data structures
- Extensibility for future components (Low/1) - Flexible architecture

**Cross-Functional Requirements:**
- Performance: Instant component creation
- Security: Validate all component properties
- Accessibility: Component metadata for screen readers
- Observability: Component usage tracking

---

### USER STORY A-1: Component Registry and Models

**ID & Title:** A-1: Build Component Registry System
**User Persona Narrative:** As a developer, I want a well-organized component library so I can easily find and use components
**Business Value:** High (3)
**Priority Score:** 5
**Story Points:** L

**Acceptance Criteria:**
```gherkin
Given I have a component registry
When I request a component definition
Then I receive complete component metadata
And the component has proper constraints
And all required properties are defined

Given I register a new component
When the component has invalid configuration
Then registration fails with clear error
And the registry remains unchanged
```

**External Dependencies:** None
**Technical Debt Considerations:** Consider plugin architecture for future
**Test Data Requirements:** Full set of component definitions

---

#### TASK A-1-T1: Create Component Definition Models

**Goal:** Implement comprehensive component definition system

**Token Budget:** 10,000 tokens

**Component Models:**
```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set
import re

class ComponentCategory(Enum):
    """
    CLAUDE.md #4.1: Explicit component categories
    """
    # Basic
    LAYOUT = ("Layout", "dashboard", 1)
    CONTENT = ("Content", "article", 2)
    FORMS = ("Forms", "edit_note", 3)
    MEDIA = ("Media", "image", 4)
    
    # Advanced
    NAVIGATION = ("Navigation", "menu", 5)
    DATA_DISPLAY = ("Data Display", "table_chart", 6)
    FEEDBACK = ("Feedback", "info", 7)
    
    # Special
    CUSTOM = ("Custom", "widgets", 8)
    TEMPLATES = ("Templates", "dashboard_customize", 9)
    
    def __init__(self, display_name: str, icon: str, order: int):
        self.display_name = display_name
        self.icon = icon
        self.order = order

@dataclass
class ComponentSlot:
    """
    Defines a slot for child components
    CLAUDE.md #2.1.1: Validate slot configuration
    """
    name: str
    description: str
    accepts: List[str] = field(default_factory=list)  # Component types, "*" for any
    min_items: int = 0
    max_items: Optional[int] = None
    required: bool = False
    
    def __post_init__(self):
        """Validate slot configuration"""
        if not self.name:
            raise ValueError("Slot name is required")
        
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', self.name):
            raise ValueError(f"Invalid slot name: {self.name}")
        
        if self.min_items < 0:
            raise ValueError("min_items cannot be negative")
        
        if self.max_items is not None and self.max_items < self.min_items:
            raise ValueError("max_items must be >= min_items")
    
    def accepts_component(self, component_type: str) -> bool:
        """Check if slot accepts component type"""
        if "*" in self.accepts:
            return True
        return component_type in self.accepts

@dataclass
class ComponentConstraints:
    """
    CLAUDE.md #2.1.1: Comprehensive constraint validation
    """
    # Size constraints
    min_width: Optional[float] = None
    max_width: Optional[float] = None
    min_height: Optional[float] = None
    max_height: Optional[float] = None
    aspect_ratio: Optional[float] = None
    
    # Hierarchy constraints
    allowed_parents: Optional[List[str]] = None
    forbidden_parents: Optional[List[str]] = None
    allowed_children: Optional[List[str]] = None
    forbidden_children: Optional[List[str]] = None
    max_depth: int = 10
    
    # Instance constraints
    max_instances: Optional[int] = None
    max_instances_per_parent: Optional[int] = None
    singleton: bool = False
    
    # Property constraints
    required_props: List[str] = field(default_factory=list)
    immutable_props: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate constraints"""
        if self.min_width and self.max_width and self.min_width > self.max_width:
            raise ValueError("min_width cannot be greater than max_width")
        
        if self.min_height and self.max_height and self.min_height > self.max_height:
            raise ValueError("min_height cannot be greater than max_height")
        
        if self.aspect_ratio and self.aspect_ratio <= 0:
            raise ValueError("aspect_ratio must be positive")
    
    def validate_parent(self, parent_type: Optional[str]) -> ValidationResult:
        """Validate parent relationship"""
        errors = []
        
        if self.allowed_parents and parent_type not in self.allowed_parents:
            errors.append(f"Parent type '{parent_type}' not allowed")
        
        if self.forbidden_parents and parent_type in self.forbidden_parents:
            errors.append(f"Parent type '{parent_type}' is forbidden")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

@dataclass
class PropertyDefinition:
    """Define a component property"""
    name: str
    type: PropertyType
    default_value: Any
    description: str = ""
    required: bool = False
    visible: bool = True
    editable: bool = True
    validation: Optional[PropertyValidation] = None
    options: Optional[List[PropertyOption]] = None  # For select/radio
    depends_on: Optional[Dict[str, Any]] = None  # Conditional visibility

@dataclass
class ComponentDefinition:
    """
    Complete component definition
    CLAUDE.md #1.4: Extensible for future properties
    """
    # Identity
    id: str
    name: str
    category: ComponentCategory
    
    # Visual
    icon: str
    preview_image: Optional[str] = None
    
    # Documentation
    description: str = ""
    tags: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)
    
    # Properties
    properties: List[PropertyDefinition] = field(default_factory=list)
    default_values: Dict[str, Any] = field(default_factory=dict)
    
    # Structure
    slots: List[ComponentSlot] = field(default_factory=list)
    constraints: ComponentConstraints = field(default_factory=ComponentConstraints)
    
    # Behavior
    accepts_children: bool = False
    draggable: bool = True
    droppable: bool = True
    resizable: bool = True
    rotatable: bool = False
    
    # Metadata
    version: str = "1.0.0"
    author: str = "Canvas Editor"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Advanced
    custom_renderer: Optional[str] = None  # Custom rendering function
    event_handlers: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """
        CLAUDE.md #2.1.1: Validate definition on creation
        """
        # Validate ID format
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', self.id):
            raise ValueError(f"Invalid component ID: {self.id}")
        
        # Validate required properties have defaults
        for prop in self.properties:
            if prop.required and prop.name not in self.default_values:
                raise ValueError(f"Required property '{prop.name}' needs default value")
        
        # Set timestamps
        if not self.created_at:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.name,
            'icon': self.icon,
            'description': self.description,
            'tags': self.tags,
            'properties': [prop.__dict__ for prop in self.properties],
            'default_values': self.default_values,
            'slots': [slot.__dict__ for slot in self.slots],
            'constraints': self.constraints.__dict__,
            'accepts_children': self.accepts_children,
            'draggable': self.draggable,
            'droppable': self.droppable,
            'resizable': self.resizable,
            'version': self.version,
            'author': self.author
        }
```

**Built-in Component Definitions:**
```python
class BuiltInComponents:
    """
    CLAUDE.md #1.2: DRY - Reusable component definitions
    """
    
    @staticmethod
    def get_all_definitions() -> Dict[str, ComponentDefinition]:
        """Get all built-in component definitions"""
        return {
            # Layout Components
            "section": BuiltInComponents._create_section(),
            "container": BuiltInComponents._create_container(),
            "grid": BuiltInComponents._create_grid(),
            "flex": BuiltInComponents._create_flex(),
            "stack": BuiltInComponents._create_stack(),
            
            # Content Components
            "heading": BuiltInComponents._create_heading(),
            "paragraph": BuiltInComponents._create_paragraph(),
            "text": BuiltInComponents._create_text(),
            "image": BuiltInComponents._create_image(),
            "video": BuiltInComponents._create_video(),
            
            # Form Components
            "form": BuiltInComponents._create_form(),
            "input": BuiltInComponents._create_input(),
            "textarea": BuiltInComponents._create_textarea(),
            "select": BuiltInComponents._create_select(),
            "checkbox": BuiltInComponents._create_checkbox(),
            "radio": BuiltInComponents._create_radio(),
            "button": BuiltInComponents._create_button(),
            
            # Navigation Components
            "navbar": BuiltInComponents._create_navbar(),
            "sidebar": BuiltInComponents._create_sidebar(),
            "tabs": BuiltInComponents._create_tabs(),
            "breadcrumb": BuiltInComponents._create_breadcrumb(),
            
            # Data Display
            "table": BuiltInComponents._create_table(),
            "list": BuiltInComponents._create_list(),
            "card": BuiltInComponents._create_card(),
            
            # Feedback
            "alert": BuiltInComponents._create_alert(),
            "modal": BuiltInComponents._create_modal(),
            "tooltip": BuiltInComponents._create_tooltip(),
        }
    
    @staticmethod
    def _create_section() -> ComponentDefinition:
        """Create section component definition"""
        return ComponentDefinition(
            id="section",
            name="Section",
            category=ComponentCategory.LAYOUT,
            icon="dashboard",
            description="A semantic section container",
            tags=["layout", "container", "semantic", "html5"],
            
            properties=[
                PropertyDefinition(
                    name="padding",
                    type=PropertyType.SPACING,
                    default_value="2rem",
                    description="Internal spacing"
                ),
                PropertyDefinition(
                    name="background",
                    type=PropertyType.COLOR,
                    default_value="transparent",
                    description="Background color"
                ),
                PropertyDefinition(
                    name="fullWidth",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Expand to full viewport width"
                ),
            ],
            
            default_values={
                "padding": "2rem",
                "margin": "0 auto",
                "maxWidth": "1200px",
                "background": "transparent",
                "fullWidth": False
            },
            
            slots=[
                ComponentSlot(
                    name="content",
                    description="Section content",
                    accepts=["*"],  # Accept any component
                    min_items=0,
                    max_items=None
                )
            ],
            
            constraints=ComponentConstraints(
                min_width=200,
                allowed_children=["*"],  # Accept any
                forbidden_children=["html", "head", "body"],  # No document elements
            ),
            
            accepts_children=True,
            draggable=True,
            droppable=True,
            resizable=True
        )
```

**Deliverables:**
- Complete component definition models
- Built-in component library
- Validation system
- Serialization methods

**Quality Gates:**
- ✓ All fields strongly typed
- ✓ Comprehensive validation
- ✓ 100% test coverage
- ✓ Performance benchmarks met

**Unblocks:** [A-1-T2, A-1-T3]
**Confidence Score:** High (3)

---

#### TASK A-1-T2: Implement Component Registry

**Goal:** Create registry for managing component definitions

**Token Budget:** 8,000 tokens

**Registry Implementation:**
```python
class ComponentRegistry:
    """
    CLAUDE.md #6.1: Clear component ownership
    CLAUDE.md #12.1: Structured logging
    """
    
    def __init__(self):
        self._definitions: Dict[str, ComponentDefinition] = {}
        self._categories: Dict[ComponentCategory, List[str]] = defaultdict(list)
        self._tags: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.RLock()
        self._initialized = False
        
    def initialize(self) -> None:
        """
        Initialize with built-in components
        CLAUDE.md #2.1.4: Idempotent initialization
        """
        with self._lock:
            if self._initialized:
                return
            
            # Register all built-in components
            definitions = BuiltInComponents.get_all_definitions()
            for comp_id, definition in definitions.items():
                self.register(definition)
            
            self._initialized = True
            logger.info(f"Registry initialized with {len(self._definitions)} components")
    
    def register(self, definition: ComponentDefinition) -> None:
        """
        Register a component definition
        CLAUDE.md #2.1.1: Validate before registration
        """
        with self._lock:
            # Validate definition
            validation = self._validate_definition(definition)
            if not validation.is_valid:
                raise RegistrationError(f"Invalid definition: {validation.errors}")
            
            # Check for duplicates
            if definition.id in self._definitions:
                raise RegistrationError(f"Component '{definition.id}' already registered")
            
            # Store definition
            self._definitions[definition.id] = definition
            
            # Update indices
            self._categories[definition.category].append(definition.id)
            for tag in definition.tags:
                self._tags[tag].add(definition.id)
            
            logger.info(
                f"Registered component",
                extra={
                    "component_id": definition.id,
                    "name": definition.name,
                    "category": definition.category.name
                }
            )
    
    def _validate_definition(self, definition: ComponentDefinition) -> ValidationResult:
        """
        Comprehensive definition validation
        CLAUDE.md #2.1.2: Detailed error messages
        """
        errors = []
        
        # Check for circular slot dependencies
        if definition.slots:
            for slot in definition.slots:
                if definition.id in slot.accepts:
                    errors.append(f"Circular dependency: component cannot accept itself in slot '{slot.name}'")
        
        # Validate constraint consistency
        if definition.constraints.allowed_children and definition.constraints.forbidden_children:
            overlap = set(definition.constraints.allowed_children) & set(definition.constraints.forbidden_children)
            if overlap:
                errors.append(f"Conflicting constraints: {overlap} both allowed and forbidden")
        
        # Validate property names are unique
        prop_names = [prop.name for prop in definition.properties]
        if len(prop_names) != len(set(prop_names)):
            errors.append("Duplicate property names found")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def get(self, component_id: str) -> Optional[ComponentDefinition]:
        """Get component definition by ID"""
        return self._definitions.get(component_id)
    
    def get_by_category(self, category: ComponentCategory) -> List[ComponentDefinition]:
        """Get all components in a category"""
        component_ids = self._categories.get(category, [])
        return [self._definitions[comp_id] for comp_id in component_ids]
    
    def get_by_tag(self, tag: str) -> List[ComponentDefinition]:
        """Get all components with a specific tag"""
        component_ids = self._tags.get(tag, set())
        return [self._definitions[comp_id] for comp_id in component_ids]
    
    def search(self, query: str) -> List[ComponentDefinition]:
        """
        Simple search implementation
        CLAUDE.md #1.5: Optimize for common searches
        """
        query_lower = query.lower()
        results = []
        
        for definition in self._definitions.values():
            # Search in name
            if query_lower in definition.name.lower():
                results.append(definition)
                continue
            
            # Search in tags
            if any(query_lower in tag.lower() for tag in definition.tags):
                results.append(definition)
                continue
            
            # Search in description
            if query_lower in definition.description.lower():
                results.append(definition)
        
        return results
    
    def validate_relationship(
        self,
        parent_type: Optional[str],
        child_type: str
    ) -> ValidationResult:
        """
        Validate parent-child relationship
        CLAUDE.md #5.4: Security - prevent invalid hierarchies
        """
        errors = []
        
        child_def = self.get(child_type)
        if not child_def:
            errors.append(f"Unknown component type: {child_type}")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Validate against child constraints
        if parent_type:
            parent_validation = child_def.constraints.validate_parent(parent_type)
            errors.extend(parent_validation.errors)
            
            # Check parent's allowed children
            parent_def = self.get(parent_type)
            if parent_def:
                if parent_def.constraints.allowed_children:
                    if child_type not in parent_def.constraints.allowed_children and \
                       "*" not in parent_def.constraints.allowed_children:
                        errors.append(f"Parent '{parent_type}' does not accept '{child_type}' children")
                
                if parent_def.constraints.forbidden_children:
                    if child_type in parent_def.constraints.forbidden_children:
                        errors.append(f"Parent '{parent_type}' forbids '{child_type}' children")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
```

**Registry Persistence:**
```python
class RegistryPersistence:
    """
    CLAUDE.md #2.1.4: Reliable persistence
    """
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def save_registry(self, registry: ComponentRegistry) -> None:
        """Save registry to disk"""
        data = {
            'version': '1.0',
            'components': {
                comp_id: definition.to_dict()
                for comp_id, definition in registry._definitions.items()
            },
            'metadata': {
                'saved_at': datetime.now().isoformat(),
                'component_count': len(registry._definitions)
            }
        }
        
        file_path = self.storage_path / "component_registry.json"
        temp_path = file_path.with_suffix('.tmp')
        
        # Write to temp file
        async with aiofiles.open(temp_path, 'w') as f:
            await f.write(json.dumps(data, indent=2))
        
        # Atomic replace
        temp_path.replace(file_path)
        
        logger.info(f"Saved registry with {len(registry._definitions)} components")
```

**Unblocks:** [A-1-T3, A-2-T1]
**Confidence Score:** High (3)

---

#### TASK A-1-T3: Implement Component Factory

**Goal:** Create factory for instantiating components

**Token Budget:** 10,000 tokens

**Factory Implementation:**
```python
class ComponentFactory:
    """
    CLAUDE.md #3.3: Factory pattern for component creation
    CLAUDE.md #2.1.1: Validate all inputs
    """
    
    def __init__(self, registry: ComponentRegistry):
        self.registry = registry
        self._creation_strategies: Dict[str, CreationStrategy] = {}
        self._initialize_strategies()
        
    def create_component(
        self,
        component_type: str,
        props: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None
    ) -> Component:
        """
        Create a component instance
        CLAUDE.md #2.1.2: Comprehensive error handling
        """
        # Get definition
        definition = self.registry.get(component_type)
        if not definition:
            raise ComponentCreationError(f"Unknown component type: {component_type}")
        
        # Validate parent relationship
        if parent_id:
            parent_type = self._get_parent_type(parent_id)
            validation = self.registry.validate_relationship(parent_type, component_type)
            if not validation.is_valid:
                raise ComponentCreationError(
                    f"Cannot add {component_type} to {parent_type}: {validation.errors}"
                )
        
        # Merge properties with defaults
        component_props = self._merge_properties(definition, props)
        
        # Validate properties
        prop_validation = self._validate_properties(definition, component_props)
        if not prop_validation.is_valid:
            raise ComponentCreationError(f"Invalid properties: {prop_validation.errors}")
        
        # Create component ID
        component_id = self._generate_component_id(component_type)
        
        # Create base component
        component = Component(
            id=component_id,
            type=component_type,
            name=definition.name,
            properties=component_props,
            children=[],
            parent_id=parent_id,
            metadata={
                'created_at': datetime.now().isoformat(),
                'version': definition.version,
                'category': definition.category.name
            }
        )
        
        # Apply creation strategy
        strategy = self._creation_strategies.get(component_type)
        if strategy:
            component = strategy.create(component, definition)
        
        # Initialize slots
        if definition.slots:
            component.slots = {slot.name: [] for slot in definition.slots}
        
        logger.debug(
            f"Created component",
            extra={
                'component_id': component.id,
                'type': component_type,
                'parent_id': parent_id
            }
        )
        
        return component
    
    def _merge_properties(
        self,
        definition: ComponentDefinition,
        props: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge user properties with defaults
        CLAUDE.md #1.4: Extensible property handling
        """
        # Start with defaults
        merged = definition.default_values.copy()
        
        # Apply user properties
        if props:
            for key, value in props.items():
                # Check if property exists
                prop_def = next(
                    (p for p in definition.properties if p.name == key),
                    None
                )
                
                if prop_def:
                    # Validate type
                    if self._validate_property_type(value, prop_def.type):
                        merged[key] = value
                    else:
                        logger.warning(
                            f"Invalid type for property '{key}': expected {prop_def.type}"
                        )
                else:
                    # Allow custom properties with warning
                    logger.warning(f"Unknown property '{key}' for component {definition.id}")
                    merged[key] = value
        
        return merged
    
    def _validate_properties(
        self,
        definition: ComponentDefinition,
        props: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate component properties
        CLAUDE.md #2.1.1: Thorough validation
        """
        errors = []
        
        for prop_def in definition.properties:
            value = props.get(prop_def.name)
            
            # Check required properties
            if prop_def.required and value is None:
                errors.append(f"Required property '{prop_def.name}' is missing")
                continue
            
            # Skip if not provided and not required
            if value is None:
                continue
            
            # Validate using property validation
            if prop_def.validation:
                validation = prop_def.validation.validate(value)
                if not validation.is_valid:
                    errors.extend(validation.errors)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
```

**Component Creation Strategies:**
```python
class CreationStrategy(ABC):
    """Base class for component creation strategies"""
    
    @abstractmethod
    def create(self, component: Component, definition: ComponentDefinition) -> Component:
        """Apply creation strategy"""
        pass

class FormCreationStrategy(CreationStrategy):
    """
    Special handling for form components
    CLAUDE.md #3.4: Follow form best practices
    """
    
    def create(self, component: Component, definition: ComponentDefinition) -> Component:
        """Initialize form with structure"""
        
        # Add form ID if not present
        if 'id' not in component.properties:
            component.properties['id'] = f"form_{component.id}"
        
        # Add CSRF token placeholder
        component.properties['csrf_token'] = "{{ csrf_token }}"
        
        # Add default action
        if 'action' not in component.properties:
            component.properties['action'] = "#"
        
        # Add default method
        if 'method' not in component.properties:
            component.properties['method'] = "POST"
        
        # Add novalidate for custom validation
        component.properties['novalidate'] = True
        
        # Add accessibility attributes
        component.properties['role'] = "form"
        component.properties['aria-label'] = component.properties.get('name', 'Form')
        
        return component

class GridCreationStrategy(CreationStrategy):
    """
    Grid layout initialization
    CLAUDE.md #1.5: Performance-optimized defaults
    """
    
    def create(self, component: Component, definition: ComponentDefinition) -> Component:
        """Initialize grid with responsive defaults"""
        
        # Set responsive grid template
        if 'gridTemplateColumns' not in component.properties:
            component.properties['gridTemplateColumns'] = 'repeat(auto-fit, minmax(250px, 1fr))'
        
        # Add gap
        if 'gap' not in component.properties:
            component.properties['gap'] = '1rem'
        
        # Add responsive behavior
        component.properties['responsive'] = True
        
        return component

class ComponentFactoryConfig:
    """
    Factory configuration
    CLAUDE.md #12.3: Monitor component creation
    """
    
    def __init__(self):
        self.metrics = ComponentCreationMetrics()
        self.id_generator = ComponentIDGenerator()
        
    def track_creation(self, component_type: str, duration: float):
        """Track component creation metrics"""
        self.metrics.record_creation(component_type, duration)
```

**Unblocks:** [A-2-T1]
**Confidence Score:** High (3)

---

### USER STORY A-2: Component Search and Discovery

**ID & Title:** A-2: Implement Component Search Engine
**User Persona Narrative:** As a designer, I want to quickly find components so I can build efficiently
**Business Value:** High (3)
**Priority Score:** 4
**Story Points:** M

**Acceptance Criteria:**
```gherkin
Given I search for "button"
When the search completes
Then I see all button-related components
And results are ranked by relevance
And search completes in < 100ms

Given I filter by category "Forms"
When I apply the filter
Then I only see form components
And the filter persists across searches
```

---

#### TASK A-2-T1: Implement Search Engine

**Goal:** Create fast, flexible component search

**Token Budget:** 10,000 tokens

**Search Implementation:**
```python
class ComponentSearchEngine:
    """
    CLAUDE.md #1.5: Optimized search performance
    CLAUDE.md #9.1: Accessible search results
    """
    
    def __init__(self, registry: ComponentRegistry):
        self.registry = registry
        self.index = SearchIndex()
        self._build_index()
        
    def _build_index(self) -> None:
        """
        Build search index for fast searching
        CLAUDE.md #1.5: Pre-compute for performance
        """
        start_time = time.perf_counter()
        
        for comp_id, definition in self.registry._definitions.items():
            # Index component name
            self.index.add_document(
                doc_id=comp_id,
                fields={
                    'name': definition.name,
                    'description': definition.description,
                    'tags': ' '.join(definition.tags),
                    'category': definition.category.display_name
                },
                metadata={
                    'category': definition.category,
                    'accepts_children': definition.accepts_children,
                    'author': definition.author
                }
            )
        
        duration = time.perf_counter() - start_time
        logger.info(f"Built search index in {duration:.2f}s")
    
    def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        limit: int = 50
    ) -> SearchResults:
        """
        Search components with optional filters
        CLAUDE.md #2.1.2: Handle empty queries
        """
        if not query and not filters:
            # Return popular components
            return self._get_popular_components(limit)
        
        # Search in index
        raw_results = self.index.search(
            query=query or "*",
            filters=self._build_index_filters(filters),
            limit=limit * 2  # Get extra for post-filtering
        )
        
        # Convert to component definitions
        components = []
        for result in raw_results:
            definition = self.registry.get(result.doc_id)
            if definition:
                components.append(SearchResult(
                    component=definition,
                    score=result.score,
                    highlights=result.highlights
                ))
        
        # Apply additional filters
        if filters:
            components = self._apply_filters(components, filters)
        
        # Sort by relevance
        components.sort(key=lambda x: x.score, reverse=True)
        
        # Limit results
        components = components[:limit]
        
        return SearchResults(
            query=query,
            results=components,
            total_count=len(components),
            filters_applied=filters,
            search_time_ms=0  # Will be set by timing decorator
        )
    
    def _apply_filters(
        self,
        results: List[SearchResult],
        filters: SearchFilters
    ) -> List[SearchResult]:
        """Apply additional filters not in index"""
        
        filtered = results
        
        # Filter by component properties
        if filters.properties:
            filtered = [
                r for r in filtered
                if all(
                    prop in [p.name for p in r.component.properties]
                    for prop in filters.properties
                )
            ]
        
        # Filter by constraints
        if filters.accepts_children is not None:
            filtered = [
                r for r in filtered
                if r.component.accepts_children == filters.accepts_children
            ]
        
        if filters.resizable is not None:
            filtered = [
                r for r in filtered
                if r.component.resizable == filters.resizable
            ]
        
        return filtered

class SearchIndex:
    """
    Simple inverted index for fast searching
    CLAUDE.md #1.5: Memory-efficient index
    """
    
    def __init__(self):
        self.documents: Dict[str, Document] = {}
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)
        self.metadata_index: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
    
    def add_document(
        self,
        doc_id: str,
        fields: Dict[str, str],
        metadata: Dict[str, Any]
    ) -> None:
        """Add document to index"""
        
        # Store document
        self.documents[doc_id] = Document(
            id=doc_id,
            fields=fields,
            metadata=metadata
        )
        
        # Build inverted index
        for field_name, field_value in fields.items():
            tokens = self._tokenize(field_value)
            for token in tokens:
                self.inverted_index[token].add(doc_id)
        
        # Build metadata index
        for key, value in metadata.items():
            if isinstance(value, (str, int, bool, Enum)):
                self.metadata_index[key][str(value)].add(doc_id)
    
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50
    ) -> List[SearchHit]:
        """Search documents"""
        
        # Get matching documents
        if query == "*":
            # Match all
            doc_ids = set(self.documents.keys())
        else:
            # Search by tokens
            tokens = self._tokenize(query)
            doc_ids = set()
            
            for token in tokens:
                if token in self.inverted_index:
                    if not doc_ids:
                        doc_ids = self.inverted_index[token].copy()
                    else:
                        doc_ids &= self.inverted_index[token]
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if key in self.metadata_index:
                    filter_docs = self.metadata_index[key].get(str(value), set())
                    doc_ids &= filter_docs
        
        # Score and rank
        results = []
        for doc_id in doc_ids:
            doc = self.documents[doc_id]
            score = self._calculate_score(doc, query)
            highlights = self._generate_highlights(doc, query)
            
            results.append(SearchHit(
                doc_id=doc_id,
                score=score,
                highlights=highlights
            ))
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:limit]
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for indexing"""
        # Simple tokenization - can be improved
        tokens = re.findall(r'\w+', text.lower())
        return tokens
    
    def _calculate_score(self, doc: Document, query: str) -> float:
        """Calculate relevance score"""
        score = 0.0
        query_lower = query.lower()
        
        # Exact match in name
        if query_lower == doc.fields['name'].lower():
            score += 10.0
        
        # Partial match in name
        elif query_lower in doc.fields['name'].lower():
            score += 5.0
        
        # Match in tags
        if query_lower in doc.fields.get('tags', '').lower():
            score += 3.0
        
        # Match in description
        if query_lower in doc.fields.get('description', '').lower():
            score += 1.0
        
        return score
```

**Unblocks:** [B-1-T1]
**Confidence Score:** High (3)

---

## EPIC B: Custom Components and Preview

Implement custom component creation, management, and preview generation.

**Definition of Done:**
- ✓ Custom components can be created and saved
- ✓ Import/export working
- ✓ Preview generation functional
- ✓ Component versioning

**Business Value:** Enable component reusability and sharing

---

### Technical Debt Management

```yaml
# Component Library Debt Tracking
component_debt:
  items:
    - id: CL-001
      description: "Implement fuzzy search algorithm"
      impact: "Better search results"
      effort: "M"
      priority: 2
      
    - id: CL-002
      description: "Add component usage analytics"
      impact: "Understand popular components"
      effort: "S"
      priority: 3
      
    - id: CL-003
      description: "Create component marketplace API"
      impact: "Enable component sharing"
      effort: "L"
      priority: 1
```

---

## Testing Strategy

### Unit Tests
```python
@pytest.mark.parametrize("component_type,parent_type,expected", [
    ("input", "form", True),
    ("input", "table", False),
    ("button", "form", True),
    ("form", "form", False),  # Forms can't nest
])
def test_component_relationship_validation(
    component_type, parent_type, expected
):
    """CLAUDE.md #6.2: Test component constraints"""
    registry = ComponentRegistry()
    registry.initialize()
    
    result = registry.validate_relationship(parent_type, component_type)
    assert result.is_valid == expected

def test_component_factory_creation():
    """Test component creation with properties"""
    registry = ComponentRegistry()
    registry.initialize()
    factory = ComponentFactory(registry)
    
    button = factory.create_component(
        "button",
        props={
            "text": "Click me",
            "variant": "primary",
            "size": "large"
        }
    )
    
    assert button.type == "button"
    assert button.properties["text"] == "Click me"
    assert button.properties["variant"] == "primary"
```

### Integration Tests
```python
@pytest.mark.integration
async def test_search_performance():
    """Test search completes within performance budget"""
    registry = ComponentRegistry()
    registry.initialize()
    
    # Add 1000 custom components
    for i in range(1000):
        registry.register(ComponentDefinition(
            id=f"custom_{i}",
            name=f"Custom Component {i}",
            category=ComponentCategory.CUSTOM,
            icon="widgets",
            tags=[f"tag{i % 10}", "custom"]
        ))
    
    engine = ComponentSearchEngine(registry)
    
    # Test search performance
    start = time.perf_counter()
    results = engine.search("custom", limit=50)
    duration = time.perf_counter() - start
    
    assert duration < 0.1  # 100ms budget
    assert len(results.results) == 50
```

---

## Performance Optimization

```python
class ComponentOptimizations:
    """CLAUDE.md #1.5: Performance optimizations"""
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def validate_cached_relationship(
        parent_type: str,
        child_type: str,
        constraints_hash: int
    ) -> bool:
        """Cache relationship validation results"""
        # Validation logic here
        pass
    
    @staticmethod
    def batch_create_components(
        factory: ComponentFactory,
        requests: List[ComponentRequest]
    ) -> List[Component]:
        """Batch component creation for efficiency"""
        components = []
        
        # Pre-validate all relationships
        validations = [
            factory.registry.validate_relationship(
                req.parent_type,
                req.component_type
            )
            for req in requests
        ]
        
        # Create valid components
        for req, validation in zip(requests, validations):
            if validation.is_valid:
                component = factory.create_component(
                    req.component_type,
                    req.props,
                    req.parent_id
                )
                components.append(component)
        
        return components
```

---

## Security Checklist

- [ ] Validate all component definitions
- [ ] Sanitize imported components
- [ ] Prevent prototype pollution
- [ ] Validate file paths for custom components
- [ ] Check component property values
- [ ] Limit custom component complexity

---

## Component Library Architecture Summary

1. **Registry**: Central repository of component definitions
2. **Factory**: Creates component instances with validation
3. **Search**: Fast, flexible component discovery
4. **Custom**: User-created reusable components
5. **Preview**: Visual component previews
6. **Export/Import**: Component sharing capabilities