# Component Library - Solution Design Document

## Overview
The Component Library system manages the collection of draggable components, custom component creation, component templates, and the component marketplace.

## Functional Requirements

### 1. Built-in Components
- Basic HTML elements
- Layout components
- Form elements
- Media components
- Navigation components
- Data display components

### 2. Custom Components
- Create from existing components
- Save as reusable templates
- Export/import components
- Version management
- Component documentation

### 3. Component Search
- Search by name
- Filter by category
- Filter by properties
- Recently used
- Favorites

### 4. Component Preview
- Live preview
- Property variations
- Responsive preview
- Code preview

## Technical Specifications

### Component Registry

```python
@dataclass
class ComponentDefinition:
    """Defines a component type in the library"""
    id: str
    name: str
    category: ComponentCategory
    icon: str
    description: str
    tags: List[str]
    
    # Component creation
    default_properties: Dict[str, Any]
    constraints: ComponentConstraints
    slots: List[ComponentSlot]
    
    # Behavior
    accepts_children: bool
    draggable: bool
    resizable: bool
    
    # Metadata
    version: str
    author: str
    documentation_url: Optional[str]
    preview_image: Optional[str]

@dataclass
class ComponentConstraints:
    """Constraints for component usage"""
    min_width: Optional[float] = None
    max_width: Optional[float] = None
    min_height: Optional[float] = None
    max_height: Optional[float] = None
    allowed_parents: Optional[List[str]] = None
    allowed_children: Optional[List[str]] = None
    max_instances: Optional[int] = None
    required_props: List[str] = field(default_factory=list)

@dataclass
class ComponentSlot:
    """Defines a slot for child components"""
    name: str
    description: str
    accepts: List[str]  # Component types
    min_items: int = 0
    max_items: Optional[int] = None
```

### Built-in Component Library

```python
class BuiltInComponents:
    """Registry of built-in components"""
    
    COMPONENTS = {
        # Layout Components
        "section": ComponentDefinition(
            id="section",
            name="Section",
            category=ComponentCategory.LAYOUT,
            icon="dashboard",
            description="A container section with padding",
            tags=["layout", "container", "wrapper"],
            default_properties={
                "padding": "2rem",
                "margin": "0 auto",
                "max-width": "1200px"
            },
            constraints=ComponentConstraints(),
            slots=[ComponentSlot(name="content", description="Section content", accepts=["*"])],
            accepts_children=True,
            draggable=True,
            resizable=True,
            version="1.0.0",
            author="Canvas Editor"
        ),
        
        "grid": ComponentDefinition(
            id="grid",
            name="Grid",
            category=ComponentCategory.LAYOUT,
            icon="grid_view",
            description="Responsive grid container",
            tags=["layout", "grid", "responsive"],
            default_properties={
                "display": "grid",
                "grid-template-columns": "repeat(auto-fit, minmax(300px, 1fr))",
                "gap": "1rem"
            },
            constraints=ComponentConstraints(min_width=200),
            slots=[ComponentSlot(name="items", description="Grid items", accepts=["*"])],
            accepts_children=True,
            draggable=True,
            resizable=True,
            version="1.0.0",
            author="Canvas Editor"
        ),
        
        # Form Components
        "form": ComponentDefinition(
            id="form",
            name="Form",
            category=ComponentCategory.FORMS,
            icon="edit_note",
            description="Form container",
            tags=["form", "input", "data"],
            default_properties={
                "method": "POST",
                "action": "#"
            },
            constraints=ComponentConstraints(
                allowed_children=["input", "textarea", "select", "button", "label", "fieldset"]
            ),
            slots=[
                ComponentSlot(
                    name="fields",
                    description="Form fields",
                    accepts=["input", "textarea", "select", "fieldset"]
                ),
                ComponentSlot(
                    name="actions",
                    description="Form actions",
                    accepts=["button"]
                )
            ],
            accepts_children=True,
            draggable=True,
            resizable=True,
            version="1.0.0",
            author="Canvas Editor"
        ),
        
        "input": ComponentDefinition(
            id="input",
            name="Input",
            category=ComponentCategory.FORMS,
            icon="input",
            description="Text input field",
            tags=["form", "input", "text"],
            default_properties={
                "type": "text",
                "placeholder": "Enter text...",
                "required": False
            },
            constraints=ComponentConstraints(
                allowed_parents=["form", "fieldset", "div", "section"],
                min_width=100
            ),
            slots=[],
            accepts_children=False,
            draggable=True,
            resizable=True,
            version="1.0.0",
            author="Canvas Editor"
        ),
        
        # Content Components
        "heading": ComponentDefinition(
            id="heading",
            name="Heading",
            category=ComponentCategory.CONTENT,
            icon="title",
            description="Heading text (h1-h6)",
            tags=["text", "heading", "title"],
            default_properties={
                "level": 2,
                "text": "Heading",
                "align": "left"
            },
            constraints=ComponentConstraints(),
            slots=[],
            accepts_children=False,
            draggable=True,
            resizable=True,
            version="1.0.0",
            author="Canvas Editor"
        ),
        
        # Add more components...
    }
```

### Component Factory

```python
class ComponentFactory:
    """Creates component instances from definitions"""
    
    def __init__(self, registry: ComponentRegistry):
        self.registry = registry
    
    def create_component(self, component_id: str, props: Optional[Dict] = None) -> Component:
        """Create a component instance"""
        
        definition = self.registry.get_definition(component_id)
        if not definition:
            raise ValueError(f"Unknown component: {component_id}")
        
        # Merge with default properties
        properties = {**definition.default_properties}
        if props:
            properties.update(props)
        
        # Create component
        component = Component(
            id=str(uuid.uuid4()),
            type=component_id,
            name=definition.name,
            properties=properties,
            constraints=definition.constraints,
            slots={slot.name: [] for slot in definition.slots}
        )
        
        # Apply component-specific initialization
        self._initialize_component(component, definition)
        
        return component
    
    def _initialize_component(self, component: Component, definition: ComponentDefinition):
        """Component-specific initialization"""
        
        if component.type == "form":
            # Add default form structure
            component.add_child(self.create_component("fieldset"))
            component.add_child(self.create_component("button", {"text": "Submit"}))
        
        elif component.type == "table":
            # Add default table structure
            component.add_child(self.create_component("thead"))
            component.add_child(self.create_component("tbody"))
        
        # Add more initializations...
```

### Custom Component System

```python
class CustomComponentManager:
    """Manages user-created custom components"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.custom_components: Dict[str, CustomComponent] = {}
        self._load_custom_components()
    
    def create_custom_component(self, name: str, base_component: Component,
                                metadata: Dict[str, Any]) -> CustomComponent:
        """Create a custom component from existing component"""
        
        # Generate unique ID
        component_id = f"custom_{slugify(name)}_{uuid.uuid4().hex[:8]}"
        
        # Create definition
        definition = ComponentDefinition(
            id=component_id,
            name=name,
            category=ComponentCategory.CUSTOM,
            icon=metadata.get("icon", "widgets"),
            description=metadata.get("description", ""),
            tags=metadata.get("tags", []),
            default_properties=self._extract_properties(base_component),
            constraints=ComponentConstraints(),
            slots=self._extract_slots(base_component),
            accepts_children=len(base_component.children) > 0,
            draggable=True,
            resizable=True,
            version="1.0.0",
            author=metadata.get("author", "User")
        )
        
        # Create custom component
        custom = CustomComponent(
            definition=definition,
            template=base_component,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            usage_count=0
        )
        
        # Save
        self.custom_components[component_id] = custom
        self._save_custom_component(custom)
        
        return custom
    
    def export_component(self, component_id: str) -> Dict[str, Any]:
        """Export component as shareable JSON"""
        
        custom = self.custom_components.get(component_id)
        if not custom:
            raise ValueError(f"Component not found: {component_id}")
        
        return {
            "version": "1.0",
            "component": {
                "definition": asdict(custom.definition),
                "template": custom.template.to_dict(),
                "metadata": {
                    "created_at": custom.created_at.isoformat(),
                    "updated_at": custom.updated_at.isoformat(),
                    "usage_count": custom.usage_count
                }
            }
        }
    
    def import_component(self, data: Dict[str, Any]) -> CustomComponent:
        """Import component from JSON"""
        
        # Validate version
        if data.get("version") != "1.0":
            raise ValueError("Unsupported component version")
        
        # Create definition
        def_data = data["component"]["definition"]
        definition = ComponentDefinition(**def_data)
        
        # Create template
        template = Component.from_dict(data["component"]["template"])
        
        # Create custom component
        custom = CustomComponent(
            definition=definition,
            template=template,
            created_at=datetime.fromisoformat(data["component"]["metadata"]["created_at"]),
            updated_at=datetime.now(),
            usage_count=0
        )
        
        # Check for conflicts
        if definition.id in self.custom_components:
            # Generate new ID
            definition.id = f"{definition.id}_{uuid.uuid4().hex[:8]}"
        
        # Save
        self.custom_components[definition.id] = custom
        self._save_custom_component(custom)
        
        return custom
```

### Component Search Engine

```python
class ComponentSearchEngine:
    """Search and filter components"""
    
    def __init__(self, components: Dict[str, ComponentDefinition]):
        self.components = components
        self._build_search_index()
    
    def _build_search_index(self):
        """Build search index for fast searching"""
        
        self.search_index = {}
        
        for comp_id, definition in self.components.items():
            # Index by name
            tokens = self._tokenize(definition.name)
            for token in tokens:
                if token not in self.search_index:
                    self.search_index[token] = []
                self.search_index[token].append(comp_id)
            
            # Index by tags
            for tag in definition.tags:
                if tag not in self.search_index:
                    self.search_index[tag] = []
                self.search_index[tag].append(comp_id)
    
    def search(self, query: str, filters: Optional[SearchFilters] = None) -> List[ComponentDefinition]:
        """Search components"""
        
        # Tokenize query
        tokens = self._tokenize(query.lower())
        
        # Find matching components
        matches = set()
        for token in tokens:
            if token in self.search_index:
                matches.update(self.search_index[token])
        
        # Convert to definitions
        results = [self.components[comp_id] for comp_id in matches]
        
        # Apply filters
        if filters:
            results = self._apply_filters(results, filters)
        
        # Sort by relevance
        results = self._sort_by_relevance(results, query)
        
        return results
    
    def _apply_filters(self, components: List[ComponentDefinition], 
                       filters: SearchFilters) -> List[ComponentDefinition]:
        """Apply search filters"""
        
        filtered = components
        
        if filters.categories:
            filtered = [c for c in filtered if c.category in filters.categories]
        
        if filters.tags:
            filtered = [c for c in filtered if any(tag in c.tags for tag in filters.tags)]
        
        if filters.accepts_children is not None:
            filtered = [c for c in filtered if c.accepts_children == filters.accepts_children]
        
        return filtered
```

### Component Preview System

```python
class ComponentPreview:
    """Generates component previews"""
    
    def __init__(self, renderer: ComponentRenderer):
        self.renderer = renderer
    
    def generate_preview(self, definition: ComponentDefinition, 
                         variations: Optional[List[Dict]] = None) -> PreviewData:
        """Generate component preview"""
        
        previews = []
        
        # Default preview
        default_component = ComponentFactory().create_component(definition.id)
        previews.append({
            "name": "Default",
            "component": default_component,
            "rendered": self.renderer.render_to_image(default_component)
        })
        
        # Variations
        if variations:
            for i, variation in enumerate(variations):
                component = ComponentFactory().create_component(
                    definition.id,
                    props=variation
                )
                previews.append({
                    "name": f"Variation {i+1}",
                    "component": component,
                    "rendered": self.renderer.render_to_image(component)
                })
        
        # Generate code snippets
        code_snippets = {
            "html": self._generate_html_snippet(default_component),
            "react": self._generate_react_snippet(default_component),
            "vue": self._generate_vue_snippet(default_component)
        }
        
        return PreviewData(
            component_id=definition.id,
            previews=previews,
            code_snippets=code_snippets,
            responsive_preview=self._generate_responsive_preview(default_component)
        )
```

### Component Categories

```python
class ComponentCategory(Enum):
    """Component categories for organization"""
    
    # Basic
    LAYOUT = ("Layout", "dashboard", ["section", "grid", "flex", "stack"])
    CONTENT = ("Content", "article", ["heading", "paragraph", "list", "quote"])
    FORMS = ("Forms", "edit_note", ["form", "input", "select", "checkbox"])
    MEDIA = ("Media", "image", ["image", "video", "audio", "canvas"])
    
    # Advanced
    NAVIGATION = ("Navigation", "menu", ["navbar", "sidebar", "breadcrumb", "tabs"])
    DATA = ("Data Display", "table_chart", ["table", "chart", "stat", "timeline"])
    FEEDBACK = ("Feedback", "info", ["alert", "toast", "modal", "tooltip"])
    
    # Special
    CUSTOM = ("Custom", "widgets", [])
    TEMPLATES = ("Templates", "dashboard_customize", [])
    
    def __init__(self, display_name: str, icon: str, components: List[str]):
        self.display_name = display_name
        self.icon = icon
        self.components = components
```

## Component Panel UI

```python
class ComponentLibraryPanel:
    """UI panel for component library"""
    
    def __init__(self, search_engine: ComponentSearchEngine,
                 factory: ComponentFactory):
        self.search_engine = search_engine
        self.factory = factory
        self.selected_category = None
        self.search_query = ""
        self.favorites = self._load_favorites()
    
    def build_ui(self) -> ft.Control:
        return ft.Column([
            # Header
            self._build_header(),
            
            # Search
            self._build_search_bar(),
            
            # Quick filters
            self._build_quick_filters(),
            
            # Component grid
            self._build_component_grid(),
            
            # Custom components section
            self._build_custom_section()
        ])
    
    def _build_component_grid(self) -> ft.Control:
        """Build the grid of components"""
        
        # Get components to display
        if self.search_query:
            components = self.search_engine.search(self.search_query)
        elif self.selected_category:
            components = self._get_category_components(self.selected_category)
        else:
            components = self._get_recent_components()
        
        # Build grid
        return ft.GridView(
            runs_count=2,
            max_extent=140,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
            controls=[
                self._build_component_card(comp) for comp in components
            ]
        )
    
    def _build_component_card(self, definition: ComponentDefinition) -> ft.Control:
        """Build a draggable component card"""
        
        return ft.Draggable(
            data=json.dumps({
                "component_id": definition.id,
                "type": "library_component"
            }),
            content=ft.Container(
                bgcolor="#F5F5F5",
                border_radius=8,
                padding=10,
                on_hover=lambda e: self._show_preview(definition) if e.data == "true" else None,
                content=ft.Column([
                    # Icon
                    ft.Icon(definition.icon, size=32, color="#5E6AD2"),
                    
                    # Name
                    ft.Text(
                        definition.name,
                        size=12,
                        weight=ft.FontWeight.W_500,
                        text_align=ft.TextAlign.CENTER
                    ),
                    
                    # Favorite button
                    ft.IconButton(
                        icon=ft.icons.STAR if definition.id in self.favorites else ft.icons.STAR_OUTLINE,
                        icon_size=16,
                        on_click=lambda e: self._toggle_favorite(definition.id)
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        )
```

## Usage Analytics

```python
class ComponentAnalytics:
    """Track component usage for insights"""
    
    def __init__(self):
        self.usage_data: Dict[str, ComponentUsage] = {}
    
    def track_usage(self, component_id: str, action: UsageAction):
        """Track component usage"""
        
        if component_id not in self.usage_data:
            self.usage_data[component_id] = ComponentUsage(
                component_id=component_id,
                drag_count=0,
                drop_count=0,
                preview_count=0,
                last_used=None
            )
        
        usage = self.usage_data[component_id]
        
        if action == UsageAction.DRAG:
            usage.drag_count += 1
        elif action == UsageAction.DROP:
            usage.drop_count += 1
        elif action == UsageAction.PREVIEW:
            usage.preview_count += 1
        
        usage.last_used = datetime.now()
    
    def get_popular_components(self, limit: int = 10) -> List[str]:
        """Get most used components"""
        
        sorted_usage = sorted(
            self.usage_data.items(),
            key=lambda x: x[1].drop_count,
            reverse=True
        )
        
        return [comp_id for comp_id, _ in sorted_usage[:limit]]
```

## Testing Requirements

### Unit Tests
- Component creation
- Custom component save/load
- Search functionality
- Filter logic

### Integration Tests
- Drag and drop flow
- Component preview generation
- Import/export cycle
- Analytics tracking

## Future Enhancements

1. **Component Marketplace**: Share/sell custom components
2. **AI Component Generation**: Generate components from description
3. **Component Variations**: Multiple style variations
4. **Smart Suggestions**: Recommend components based on context
5. **Component Bundles**: Group related components
6. **Version Control**: Component version management
7. **Documentation Generator**: Auto-generate component docs
8. **Accessibility Checker**: Validate component accessibility

## Example Usage

```python
# Initialize component library
registry = ComponentRegistry()
registry.register_built_in_components()

factory = ComponentFactory(registry)
search_engine = ComponentSearchEngine(registry.get_all_definitions())

# Search for form components
form_components = search_engine.search("form input")

# Create a component
button = factory.create_component("button", {
    "text": "Click me",
    "variant": "primary"
})

# Create custom component
custom_manager = CustomComponentManager(Path("./custom-components"))
custom_card = custom_manager.create_custom_component(
    name="Product Card",
    base_component=card_template,
    metadata={
        "description": "E-commerce product card",
        "tags": ["ecommerce", "product", "card"],
        "author": "John Doe"
    }
)

# Export custom component
export_data = custom_manager.export_component(custom_card.definition.id)
```