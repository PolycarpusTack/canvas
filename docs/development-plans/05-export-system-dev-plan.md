# Export System - Development Plan

## Phase 1: Solution Design Analysis & Validation

### 1. Initial Understanding
- **Goal**: Convert Canvas projects to production-ready code in multiple formats
- **Stack**: Python, BeautifulSoup, cssutils, terser, image optimization libraries
- **Components**: ExportPipeline, CodeGenerators, AssetProcessor, CodeOptimizer
- **User Personas**: Developers exporting their designs to production code

### 2. Clarity Assessment
- **Export Formats**: High (3) - Well-defined list of target formats
- **Code Generation**: High (3) - Clear component-to-code mapping
- **Asset Processing**: Medium (2) - Image optimization specifics need refinement
- **Optimization Pipeline**: Medium (2) - Performance targets not specified
- **Framework Templates**: High (3) - Clear structure for each framework
- **Overall Clarity**: High (3)

### 3. Technical Feasibility
- **HTML Generation**: Low risk (1) - Straightforward template generation
- **React/Vue Generation**: Medium risk (2) - Complex state management mapping
- **Asset Optimization**: Medium risk (2) - Performance vs quality balance
- **Code Optimization**: High risk (3) - Tree shaking complexity
- **Large Projects**: High risk (3) - Memory usage with many components

### 4. Security Assessment
- **Path Traversal**: Validate all output paths
- **Code Injection**: Sanitize component content
- **Asset Validation**: Check file types and sizes
- **External Resources**: Validate CDN URLs

### 5. Performance Requirements
- **Export Time**: < 30s for 100 component project
- **Memory Usage**: < 1GB for large projects
- **Asset Processing**: Parallel optimization
- **Code Quality**: Lighthouse score > 90

**Recommendation**: PROCEEDING with backlog generation

---

## EPIC A: Core Export Pipeline

Implement the fundamental export system with HTML generation and basic optimization.

**Definition of Done:**
- ✓ Export pipeline architecture complete
- ✓ HTML/CSS/JS generation working
- ✓ Asset processing implemented
- ✓ Export validation and reporting

**Business Value:** Enables production deployment of Canvas projects

**Risk Assessment:**
- Memory usage with large projects (High/3) - Stream processing needed
- Code quality consistency (Medium/2) - Template standardization
- Cross-browser compatibility (Medium/2) - Testing matrix required

**Cross-Functional Requirements:**
- Performance: < 30s export for typical projects
- Security: Sanitize all user content
- Accessibility: Generate WCAG compliant code
- Observability: Progress tracking and error logging

---

### USER STORY A-1: Export Pipeline Architecture

**ID & Title:** A-1: Build Core Export Pipeline
**User Persona Narrative:** As a developer, I want a reliable export system so I can deploy my Canvas projects
**Business Value:** High (3)
**Priority Score:** 5
**Story Points:** L

**Acceptance Criteria:**
```gherkin
Given I have a Canvas project with components
When I initiate an export to HTML
Then I receive production-ready files
And all assets are properly processed
And I get a detailed export report

Given an export fails partway through
When I check the output directory
Then no partial files remain
And I receive clear error messages
```

**External Dependencies:** BeautifulSoup, cssutils, Pillow
**Technical Debt Considerations:** May need streaming for large exports
**Test Data Requirements:** Various project sizes and complexities

---

#### TASK A-1-T1: Create Export Configuration Models

**Goal:** Implement comprehensive export configuration system

**Token Budget:** 8,000 tokens

**Required Models:**
```python
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

class ExportFormat(Enum):
    """
    CLAUDE.md #4.1: Explicit enum for formats
    """
    HTML = "html"
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    SVELTE = "svelte"
    WORDPRESS = "wordpress"
    STATIC_SITE = "static_site"
    ZIP = "zip"

@dataclass
class ExportConfig:
    """
    CLAUDE.md #2.1.1: Validate all configuration
    CLAUDE.md #4.1: Explicit types for all fields
    """
    format: ExportFormat
    output_path: Path
    options: 'ExportOptions'
    optimization: 'OptimizationSettings'
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration on creation"""
        self._validate_output_path()
        self._validate_format_compatibility()
    
    def _validate_output_path(self) -> None:
        """
        CLAUDE.md #7.1: Path traversal prevention
        """
        # Resolve to absolute path
        abs_path = self.output_path.resolve()
        
        # Check if path is safe
        if ".." in str(self.output_path):
            raise ValueError("Output path cannot contain parent references")
        
        # Ensure parent directory exists
        if not abs_path.parent.exists():
            raise ValueError(f"Parent directory does not exist: {abs_path.parent}")
        
        # Check write permissions
        if abs_path.exists() and not os.access(abs_path, os.W_OK):
            raise PermissionError(f"No write permission for: {abs_path}")
```

**Validation System:**
```python
@dataclass
class ExportOptions:
    """
    CLAUDE.md #1.4: Extensible for future options
    """
    # General options
    minify_code: bool = True
    include_source_map: bool = False
    inline_styles: bool = False
    inline_scripts: bool = False
    preserve_comments: bool = False
    
    # Framework-specific
    use_typescript: bool = False
    use_sass: bool = False
    component_style: ComponentStyle = ComponentStyle.FUNCTIONAL
    state_management: Optional[str] = None
    routing_library: Optional[str] = None
    
    # HTML options  
    doctype: str = "html5"
    viewport_meta: bool = True
    charset: str = "UTF-8"
    language: str = "en"
    
    # Asset options
    optimize_images: bool = True
    image_format: ImageFormat = ImageFormat.WEBP
    embed_fonts: bool = True
    use_cdn: bool = False
    cdn_provider: Optional[str] = None
    
    def validate(self) -> ValidationResult:
        """
        CLAUDE.md #2.1.2: Comprehensive validation
        """
        errors = []
        
        # Validate charset
        try:
            codecs.lookup(self.charset)
        except LookupError:
            errors.append(f"Invalid charset: {self.charset}")
        
        # Validate component style compatibility
        if self.use_typescript and self.component_style == ComponentStyle.CLASS_BASED:
            # TypeScript class components need additional config
            if not self.metadata.get("tsconfig"):
                errors.append("TypeScript class components require tsconfig")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
```

**Deliverables:**
- Complete configuration models with validation
- Optimization settings dataclass
- Export metadata structure
- 100% test coverage

**Quality Gates:**
- ✓ All fields strongly typed
- ✓ Comprehensive validation
- ✓ Path security checks
- ✓ Extensible design

**Unblocks:** [A-1-T2, A-1-T3]
**Confidence Score:** High (3)

---

#### TASK A-1-T2: Implement Export Pipeline Core

**Goal:** Create main export pipeline with transaction support

**Token Budget:** 12,000 tokens

**Pipeline Implementation:**
```python
class ExportPipeline:
    """
    CLAUDE.md #2.1.4: Resource management
    CLAUDE.md #12.1: Structured logging
    CLAUDE.md #1.2: DRY principle for generators
    """
    
    def __init__(self):
        self.generators: Dict[ExportFormat, BaseGenerator] = {
            ExportFormat.HTML: HTMLGenerator(),
            ExportFormat.REACT: ReactGenerator(),
            ExportFormat.VUE: VueGenerator(),
            # ... other generators
        }
        self.asset_processor = AssetProcessor()
        self.code_optimizer = CodeOptimizer()
        self.progress_tracker = ProgressTracker()
        
    async def export(
        self, 
        project: Project, 
        config: ExportConfig
    ) -> ExportResult:
        """
        Main export method with transaction support
        CLAUDE.md #2.1.3: Implement retry logic
        """
        # Create transaction context
        transaction = ExportTransaction(config.output_path)
        
        try:
            # Phase 1: Validation
            self.progress_tracker.start_phase("validation")
            validation = await self._validate_project(project, config)
            if not validation.is_valid:
                return ExportResult(
                    success=False,
                    errors=validation.errors,
                    warnings=validation.warnings
                )
            
            # Phase 2: Preparation
            self.progress_tracker.start_phase("preparation")
            context = await self._prepare_export_context(project, config)
            
            # Phase 3: Code Generation
            self.progress_tracker.start_phase("generation")
            generator = self.generators.get(config.format)
            if not generator:
                raise ValueError(f"Unsupported format: {config.format}")
            
            files = await generator.generate(context)
            
            # Phase 4: Asset Processing
            self.progress_tracker.start_phase("assets")
            assets = await self._process_assets_parallel(
                project.assets,
                config.optimization
            )
            
            # Phase 5: Optimization
            if config.options.minify_code:
                self.progress_tracker.start_phase("optimization")
                files = await self._optimize_code(files, config)
            
            # Phase 6: Write Output
            self.progress_tracker.start_phase("writing")
            await self._write_output_transactional(
                transaction,
                files,
                assets,
                config
            )
            
            # Phase 7: Generate Report
            report = self._generate_export_report(
                files,
                assets,
                config,
                context
            )
            
            # Commit transaction
            await transaction.commit()
            
            return ExportResult(
                success=True,
                report=report,
                output_path=config.output_path
            )
            
        except Exception as e:
            # Rollback on any error
            await transaction.rollback()
            logger.error(f"Export failed: {e}", exc_info=True)
            
            return ExportResult(
                success=False,
                errors=[str(e)],
                stack_trace=traceback.format_exc()
            )
        finally:
            # Cleanup
            await transaction.cleanup()
            self.progress_tracker.complete()
```

**Transaction Support:**
```python
class ExportTransaction:
    """
    CLAUDE.md #2.1.4: Atomic file operations
    """
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.temp_path = output_path.parent / f".{output_path.name}_tmp"
        self.backup_path = output_path.parent / f".{output_path.name}_backup"
        self.written_files: List[Path] = []
        
    async def write_file(self, relative_path: str, content: Union[str, bytes]):
        """Write file to temporary location"""
        file_path = self.temp_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(content, str):
            await aiofiles.open(file_path, 'w').write(content)
        else:
            await aiofiles.open(file_path, 'wb').write(content)
        
        self.written_files.append(file_path)
    
    async def commit(self):
        """Atomically move temp files to final location"""
        # Backup existing if present
        if self.output_path.exists():
            shutil.move(self.output_path, self.backup_path)
        
        try:
            # Move temp to final
            shutil.move(self.temp_path, self.output_path)
            
            # Remove backup on success
            if self.backup_path.exists():
                shutil.rmtree(self.backup_path)
                
        except Exception:
            # Restore backup on failure
            if self.backup_path.exists():
                shutil.move(self.backup_path, self.output_path)
            raise
```

**Unblocks:** [A-2-T1]
**Confidence Score:** Medium (2) - Complex transaction handling

---

#### TASK A-1-T3: Implement Export Validation

**Goal:** Create comprehensive pre-export validation

**Token Budget:** 6,000 tokens

**Validation Implementation:**
```python
class ExportValidator:
    """
    CLAUDE.md #2.1.1: Validate everything
    CLAUDE.md #9.1: Accessibility validation
    """
    
    async def validate_project(
        self,
        project: Project,
        config: ExportConfig
    ) -> ValidationResult:
        """Comprehensive validation before export"""
        
        errors = []
        warnings = []
        
        # Run all validators in parallel
        validators = [
            self._validate_structure(project),
            self._validate_assets(project),
            self._validate_accessibility(project),
            self._validate_seo(project),
            self._validate_performance(project, config),
            self._validate_security(project)
        ]
        
        results = await asyncio.gather(*validators, return_exceptions=True)
        
        # Aggregate results
        for result in results:
            if isinstance(result, Exception):
                errors.append(f"Validation error: {result}")
            else:
                errors.extend(result.errors)
                warnings.extend(result.warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={
                "component_count": len(project.components),
                "asset_count": len(project.assets),
                "validation_time": datetime.now()
            }
        )
    
    async def _validate_accessibility(self, project: Project) -> ValidationResult:
        """
        CLAUDE.md #9.1: WCAG compliance checks
        """
        errors = []
        warnings = []
        
        for component in project.components:
            # Images need alt text
            if component.type == "image":
                if not component.attributes.get("alt"):
                    errors.append(
                        f"Image '{component.name}' missing alt text (WCAG 1.1.1)"
                    )
            
            # Form inputs need labels
            elif component.type == "input":
                if not component.attributes.get("aria-label") and \
                   not component.attributes.get("id"):
                    warnings.append(
                        f"Input '{component.name}' should have label (WCAG 3.3.2)"
                    )
            
            # Check color contrast
            if component.style.color and component.style.background_color:
                contrast = self._calculate_contrast(
                    component.style.color,
                    component.style.background_color
                )
                if contrast < 4.5:
                    warnings.append(
                        f"Low contrast in '{component.name}' ({contrast:.1f}:1)"
                    )
        
        return ValidationResult(
            is_valid=True,  # Accessibility issues are warnings
            errors=errors,
            warnings=warnings
        )
```

**Unblocks:** [A-2-T1]
**Confidence Score:** High (3)

---

### USER STORY A-2: HTML/CSS/JS Generation

**ID & Title:** A-2: Generate Static Web Files
**User Persona Narrative:** As a developer, I want clean HTML/CSS/JS output so I can deploy static sites
**Business Value:** High (3)
**Priority Score:** 5
**Story Points:** L

**Acceptance Criteria:**
```gherkin
Given I export a Canvas project to HTML
When I view the generated files
Then I see semantic HTML5 markup
And modern CSS with flexbox/grid
And optimized JavaScript
And all assets properly linked

Given I have responsive components
When I export to HTML
Then media queries are generated
And images have srcset attributes
And layout adapts to screen sizes
```

---

#### TASK A-2-T1: Implement HTML Generator

**Goal:** Create semantic HTML5 generator with accessibility

**Token Budget:** 10,000 tokens

**HTML Generation:**
```python
class HTMLGenerator(BaseGenerator):
    """
    CLAUDE.md #9.1: Semantic, accessible HTML
    CLAUDE.md #7.2: Output encoding safety
    """
    
    def __init__(self):
        self.component_mapper = ComponentToHTMLMapper()
        self.style_generator = StyleGenerator()
        self.script_generator = ScriptGenerator()
        
    async def generate(self, context: ExportContext) -> Dict[str, str]:
        """Generate complete HTML project"""
        
        files = {}
        
        # Generate main HTML file
        html = await self._generate_html_document(context)
        files["index.html"] = html
        
        # Generate CSS
        css = await self.style_generator.generate(context)
        if context.config.options.inline_styles:
            # CSS will be inlined in HTML
            pass
        else:
            files["assets/css/styles.css"] = css
        
        # Generate JavaScript
        js = await self.script_generator.generate(context)
        if context.config.options.inline_scripts:
            # JS will be inlined in HTML
            pass
        else:
            files["assets/js/main.js"] = js
        
        # Generate additional pages
        for page in context.project.pages:
            if page.name != "index":
                page_html = await self._generate_page(page, context)
                files[f"{page.name}.html"] = page_html
        
        return files
    
    async def _generate_html_document(
        self,
        context: ExportContext
    ) -> str:
        """
        Generate complete HTML5 document
        CLAUDE.md #3.4: Follow HTML5 best practices
        """
        doc = HTMLDocument()
        
        # Configure document
        doc.doctype = context.config.options.doctype
        doc.language = context.config.options.language
        
        # Build head section
        head = await self._build_head_section(context)
        doc.head = head
        
        # Build body content
        body = HTMLElement("body")
        
        # Add skip navigation link for accessibility
        skip_link = HTMLElement("a", {
            "href": "#main",
            "class": "skip-link"
        })
        skip_link.add_text("Skip to main content")
        body.add_child(skip_link)
        
        # Convert components to HTML
        for component in context.components:
            element = await self._component_to_html(component, context)
            body.add_child(element)
        
        doc.body = body
        
        # Render with formatting
        if context.config.options.minify_code:
            return doc.render(pretty=False, minify=True)
        else:
            return doc.render(pretty=True, minify=False)
```

**Component Mapping:**
```python
def _component_to_html(
    self,
    component: Component,
    context: ExportContext
) -> HTMLElement:
    """
    Convert Canvas component to semantic HTML
    CLAUDE.md #9.1: Use semantic elements
    """
    # Semantic element mapping
    semantic_map = {
        "navbar": "nav",
        "header": "header",
        "footer": "footer",
        "sidebar": "aside",
        "content": "main",
        "section": "section",
        "article": "article",
        "figure": "figure",
        "form": "form",
        "search": "search"  # HTML5.3
    }
    
    # Determine element type
    element_type = semantic_map.get(component.semantic_role)
    if not element_type:
        element_type = semantic_map.get(component.type, "div")
    
    # Create element
    element = HTMLElement(element_type)
    
    # Add attributes
    if component.id:
        element.set_attribute("id", self._sanitize_id(component.id))
    
    # Add CSS classes
    classes = []
    if component.class_name:
        classes.extend(component.class_name.split())
    if component.responsive_classes:
        classes.extend(self._generate_responsive_classes(component))
    
    if classes:
        element.set_attribute("class", " ".join(classes))
    
    # Add ARIA attributes
    aria_attrs = self._generate_aria_attributes(component)
    for attr, value in aria_attrs.items():
        element.set_attribute(attr, value)
    
    # Add data attributes
    if component.data_attributes:
        for key, value in component.data_attributes.items():
            element.set_attribute(f"data-{key}", str(value))
    
    # Handle specific component types
    if component.type == "image":
        element = self._create_picture_element(component, context)
    elif component.type == "text" and component.rich_text:
        element.inner_html = self._sanitize_rich_text(component.content)
    else:
        # Add content
        if component.content:
            element.add_text(component.content)
    
    # Add children recursively
    for child in component.children:
        child_element = self._component_to_html(child, context)
        element.add_child(child_element)
    
    return element
```

**Responsive Image Generation:**
```python
def _create_picture_element(
    self,
    component: Component,
    context: ExportContext
) -> HTMLElement:
    """
    Generate responsive picture element
    CLAUDE.md #1.5: Optimize for performance
    """
    picture = HTMLElement("picture")
    
    # Get processed image assets
    image_assets = context.get_image_assets(component.asset_id)
    
    # Add WebP sources
    if context.config.optimization.image_format == "webp":
        webp_sources = [a for a in image_assets if a.format == "webp"]
        if webp_sources:
            source = HTMLElement("source", {
                "type": "image/webp",
                "srcset": self._build_srcset(webp_sources)
            })
            picture.add_child(source)
    
    # Add fallback img element
    img = HTMLElement("img", {
        "src": image_assets[0].url,
        "alt": component.attributes.get("alt", ""),
        "loading": "lazy" if context.config.optimization.lazy_load_images else None,
        "decoding": "async"
    })
    
    # Add srcset for responsive images
    img.set_attribute("srcset", self._build_srcset(image_assets))
    img.set_attribute("sizes", self._calculate_sizes(component))
    
    picture.add_child(img)
    return picture
```

**Unblocks:** [A-2-T2, A-3-T1]
**Confidence Score:** High (3)

---

### USER STORY A-3: React/Vue Export

**ID & Title:** A-3: Generate Modern Framework Code
**User Persona Narrative:** As a developer, I want to export to React/Vue so I can integrate with existing projects
**Business Value:** High (3)
**Priority Score:** 4
**Story Points:** XL

---

#### TASK A-3-T1: Implement React Generator

**Goal:** Create React component generator with hooks and TypeScript support

**Token Budget:** 15,000 tokens

**React Generation:**
```python
class ReactGenerator(BaseGenerator):
    """
    CLAUDE.md #3.4: Modern React best practices
    CLAUDE.md #1.2: DRY component generation
    """
    
    async def generate(self, context: ExportContext) -> Dict[str, str]:
        """Generate complete React application"""
        
        files = {}
        config = context.config.options
        
        # Generate package.json
        files["package.json"] = self._generate_package_json(context)
        
        # Generate TypeScript config if needed
        if config.use_typescript:
            files["tsconfig.json"] = self._generate_tsconfig()
            files[".eslintrc.json"] = self._generate_eslint_config()
        
        # Generate app structure
        files["src/index.tsx" if config.use_typescript else "src/index.jsx"] = \
            self._generate_index(context)
        
        files["src/App.tsx" if config.use_typescript else "src/App.jsx"] = \
            await self._generate_app_component(context)
        
        # Extract and generate reusable components
        components = self._extract_components(context.components)
        for comp_info in components:
            file_path = self._get_component_path(comp_info, config)
            files[file_path] = await self._generate_component(comp_info, context)
        
        # Generate styles
        style_files = await self._generate_styles(context)
        files.update(style_files)
        
        # Generate utilities and hooks
        if self._needs_custom_hooks(context):
            hook_files = await self._generate_hooks(context)
            files.update(hook_files)
        
        # Generate tests if requested
        if context.config.options.generate_tests:
            test_files = await self._generate_tests(components, context)
            files.update(test_files)
        
        return files
```

**Component Generation:**
```python
async def _generate_component(
    self,
    comp_info: ComponentInfo,
    context: ExportContext
) -> str:
    """
    Generate individual React component
    CLAUDE.md #4.1: Strong typing with TypeScript
    """
    config = context.config.options
    
    # Build imports
    imports = self._collect_imports(comp_info, config)
    
    # Generate component
    if config.component_style == ComponentStyle.FUNCTIONAL:
        component = self._generate_functional_component(comp_info, config)
    else:
        component = self._generate_class_component(comp_info, config)
    
    # Build complete file
    template = self._get_component_template(config.use_typescript)
    
    return template.format(
        imports="\n".join(imports),
        types=self._generate_types(comp_info) if config.use_typescript else "",
        component=component,
        exports=self._generate_exports(comp_info)
    )

def _generate_functional_component(
    self,
    comp_info: ComponentInfo,
    config: ExportOptions
) -> str:
    """
    Generate modern functional component with hooks
    """
    # Determine needed hooks
    hooks = []
    
    if comp_info.has_state:
        hooks.append(self._generate_state_hooks(comp_info))
    
    if comp_info.has_effects:
        hooks.append(self._generate_effect_hooks(comp_info))
    
    if comp_info.has_context:
        hooks.append(self._generate_context_hooks(comp_info))
    
    # Generate props interface for TypeScript
    props_type = ""
    if config.use_typescript:
        props_type = f": {comp_info.name}Props"
    
    # Build component
    return f"""
export const {comp_info.name} = ({{{self._generate_props_destructuring(comp_info)}}}{props_type}) => {{
{self._indent(hooks, 1)}

{self._generate_component_logic(comp_info, indent=1)}

  return (
{self._component_to_jsx(comp_info.component, indent=2)}
  );
}};"""

def _component_to_jsx(
    self,
    component: Component,
    indent: int = 0
) -> str:
    """
    Convert component tree to JSX
    CLAUDE.md #7.2: Escape user content
    """
    indent_str = "  " * indent
    
    # Handle text nodes
    if component.type == "text":
        # Escape content to prevent XSS
        content = self._escape_jsx_text(component.content)
        return f"{indent_str}{content}"
    
    # Map to React element
    element = self._map_to_react_element(component.type)
    
    # Build props
    props = self._build_jsx_props(component)
    
    # Handle self-closing elements
    if not component.children and not component.content:
        return f"{indent_str}<{element}{props} />"
    
    # Handle elements with children
    jsx_lines = [f"{indent_str}<{element}{props}>"]
    
    # Add content
    if component.content:
        jsx_lines.append(f"{indent_str}  {self._escape_jsx_text(component.content)}")
    
    # Add children
    for child in component.children:
        jsx_lines.append(self._component_to_jsx(child, indent + 1))
    
    jsx_lines.append(f"{indent_str}</{element}>")
    
    return "\n".join(jsx_lines)
```

**TypeScript Support:**
```python
def _generate_types(self, comp_info: ComponentInfo) -> str:
    """
    Generate TypeScript interfaces
    CLAUDE.md #4.1: Explicit types
    """
    types = []
    
    # Props interface
    props_fields = []
    for prop in comp_info.props:
        optional = "?" if prop.optional else ""
        props_fields.append(
            f"  {prop.name}{optional}: {self._ts_type(prop.type)};"
        )
    
    if props_fields:
        types.append(f"""
export interface {comp_info.name}Props {{
{chr(10).join(props_fields)}
}}""")
    
    # State interface if needed
    if comp_info.has_state:
        state_fields = []
        for state in comp_info.state_vars:
            state_fields.append(
                f"  {state.name}: {self._ts_type(state.type)};"
            )
        
        types.append(f"""
interface {comp_info.name}State {{
{chr(10).join(state_fields)}
}}""")
    
    return "\n".join(types)
```

**Unblocks:** [A-3-T2]
**Confidence Score:** Medium (2) - Complex framework mapping

---

## EPIC B: Advanced Export Features

Implement asset optimization, code optimization, and specialized exports.

**Definition of Done:**
- ✓ Image optimization with responsive variants
- ✓ CSS/JS minification and tree shaking
- ✓ Framework-specific optimizations
- ✓ Performance metrics in export report

**Business Value:** Production-ready, optimized output

---

### Technical Debt Management

```yaml
# Export System Debt Tracking
export_debt:
  items:
    - id: ES-001
      description: "Streaming export for large projects"
      impact: "Memory usage with 1000+ components"
      effort: "L"
      priority: 1
      
    - id: ES-002
      description: "Worker threads for asset processing"
      impact: "Faster parallel image optimization"
      effort: "M"
      priority: 2
      
    - id: ES-003
      description: "Incremental export capability"
      impact: "Faster re-exports of changed files only"
      effort: "XL"
      priority: 3
```

---

## Testing Strategy

### Unit Tests
```python
@pytest.mark.parametrize("component,expected_html", [
    (
        Component(type="header", semantic_role="header"),
        '<header></header>'
    ),
    (
        Component(type="nav", attributes={"aria-label": "Main"}),
        '<nav aria-label="Main"></nav>'
    )
])
def test_component_to_html_semantic_mapping(component, expected_html):
    """CLAUDE.md #6.2: Test semantic HTML generation"""
    generator = HTMLGenerator()
    result = generator._component_to_html(component, ExportContext())
    assert result.render() == expected_html
```

### Integration Tests
```python
@pytest.mark.integration
async def test_complete_react_export():
    """Test full React app generation"""
    project = create_test_project()
    config = ExportConfig(
        format=ExportFormat.REACT,
        output_path=Path("./test-export"),
        options=ExportOptions(use_typescript=True)
    )
    
    exporter = ExportPipeline()
    result = await exporter.export(project, config)
    
    assert result.success
    assert Path("./test-export/package.json").exists()
    assert Path("./test-export/src/App.tsx").exists()
```

---

## Performance Optimization

```python
class ExportPerformanceOptimizer:
    """CLAUDE.md #1.5: Performance optimization"""
    
    async def process_assets_parallel(
        self,
        assets: List[Asset],
        config: OptimizationSettings
    ) -> List[ProcessedAsset]:
        """Process assets in parallel with worker pool"""
        
        # Group assets by type for batch processing
        grouped = defaultdict(list)
        for asset in assets:
            grouped[asset.type].append(asset)
        
        # Process each type in parallel
        tasks = []
        for asset_type, group in grouped.items():
            processor = self._get_processor(asset_type)
            task = self._process_group(processor, group, config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return [asset for group in results for asset in group]
```

---

## Security Checklist

- [ ] Sanitize all component content for XSS
- [ ] Validate output paths to prevent traversal
- [ ] Check asset file types and sizes
- [ ] Escape special characters in generated code
- [ ] Validate CDN URLs if used
- [ ] Implement CSP headers in HTML output

---

## Export Workflow Summary

1. **Validate** project and configuration
2. **Prepare** export context with all data
3. **Generate** code for target format
4. **Process** and optimize assets
5. **Optimize** generated code
6. **Write** files transactionally
7. **Report** results and metrics

Each step includes comprehensive error handling, progress tracking, and rollback capability.