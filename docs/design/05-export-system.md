# Export System - Solution Design Document

## Overview
The Export System converts Canvas projects into production-ready code in various formats including static HTML/CSS/JS, React components, Vue components, and more.

## Functional Requirements

### 1. Export Formats
- Static HTML/CSS/JavaScript
- React application
- Vue.js application
- Angular application
- Svelte application
- WordPress theme
- Static site (Jekyll, Hugo)
- ZIP archive

### 2. Export Options
- Minification
- Code optimization
- Asset optimization
- Responsive images
- Component extraction
- Style preprocessing

### 3. Code Quality
- Clean, readable output
- Semantic HTML
- Modern CSS (Grid, Flexbox)
- Accessible markup
- SEO-friendly structure

### 4. Asset Handling
- Image optimization
- Font embedding
- Icon sprites
- External resources
- CDN integration

## Technical Specifications

### Export Configuration

```python
@dataclass
class ExportConfig:
    format: ExportFormat
    output_path: Path
    options: ExportOptions
    optimization: OptimizationSettings
    
@dataclass
class ExportOptions:
    # General options
    minify_code: bool = True
    include_source_map: bool = False
    inline_styles: bool = False
    inline_scripts: bool = False
    
    # Framework-specific
    use_typescript: bool = False
    use_sass: bool = False
    component_style: str = "functional"  # "functional" or "class-based"
    state_management: Optional[str] = None  # "redux", "vuex", etc.
    
    # HTML options
    doctype: str = "html5"
    viewport_meta: bool = True
    charset: str = "UTF-8"
    
    # Asset options
    optimize_images: bool = True
    image_format: str = "webp"  # with fallbacks
    embed_fonts: bool = True
    use_cdn: bool = False
    
@dataclass
class OptimizationSettings:
    remove_unused_css: bool = True
    tree_shake_js: bool = True
    compress_images: bool = True
    image_quality: int = 85
    lazy_load_images: bool = True
    preload_fonts: bool = True
    critical_css: bool = True
```

### Export Pipeline

```python
class ExportPipeline:
    def export(self, project: Project, config: ExportConfig) -> ExportResult:
        """Main export pipeline"""
        
        # 1. Validate project
        validation = self.validate_project(project)
        if not validation.is_valid:
            return ExportResult(success=False, errors=validation.errors)
        
        # 2. Prepare export
        context = self.prepare_context(project, config)
        
        # 3. Generate code
        if config.format == ExportFormat.HTML:
            files = self.generate_html(context)
        elif config.format == ExportFormat.REACT:
            files = self.generate_react(context)
        elif config.format == ExportFormat.VUE:
            files = self.generate_vue(context)
        # ... other formats
        
        # 4. Process assets
        assets = self.process_assets(project.assets, config.optimization)
        
        # 5. Optimize code
        if config.options.minify_code:
            files = self.optimize_code(files, config.optimization)
        
        # 6. Write output
        self.write_output(files, assets, config.output_path)
        
        # 7. Generate report
        report = self.generate_report(files, assets, config)
        
        return ExportResult(success=True, report=report)
```

### HTML/CSS/JS Generation

```python
class HTMLGenerator:
    def generate(self, components: List[Component], config: ExportConfig) -> Dict[str, str]:
        """Generate static HTML/CSS/JS files"""
        
        # Generate HTML
        html = self.generate_html(components, config)
        
        # Generate CSS
        css = self.generate_css(components, config)
        
        # Generate JavaScript
        js = self.generate_javascript(components, config)
        
        return {
            "index.html": html,
            "css/styles.css": css,
            "js/script.js": js
        }
    
    def generate_html(self, components: List[Component], config: ExportConfig) -> str:
        """Generate semantic HTML5"""
        
        # Build document structure
        doc = HTMLDocument()
        
        # Add head elements
        doc.head.add_meta(charset=config.options.charset)
        if config.options.viewport_meta:
            doc.head.add_meta(name="viewport", content="width=device-width, initial-scale=1.0")
        
        doc.head.add_title(config.project.name)
        doc.head.add_meta(name="description", content=config.project.description)
        
        # Add styles
        if config.options.inline_styles:
            doc.head.add_style(self.generate_css(components, config))
        else:
            doc.head.add_link(rel="stylesheet", href="css/styles.css")
        
        # Generate body content
        for component in components:
            doc.body.add(self.component_to_html(component))
        
        # Add scripts
        if config.options.inline_scripts:
            doc.body.add_script(self.generate_javascript(components, config))
        else:
            doc.body.add_script(src="js/script.js", defer=True)
        
        return doc.render(pretty=not config.options.minify_code)
    
    def component_to_html(self, component: Component) -> HTMLElement:
        """Convert component to semantic HTML"""
        
        # Map component types to semantic elements
        element_map = {
            "header": "header",
            "nav": "nav",
            "section": "section",
            "article": "article",
            "aside": "aside",
            "footer": "footer",
            "button": "button",
            "form": "form",
            "input": "input"
        }
        
        # Create element
        tag = element_map.get(component.type, "div")
        element = HTMLElement(tag)
        
        # Add attributes
        if component.id:
            element.set_attribute("id", self.sanitize_id(component.id))
        
        if component.attributes.get("class"):
            element.set_attribute("class", component.attributes["class"])
        
        # Add ARIA attributes for accessibility
        if component.attributes.get("aria-label"):
            element.set_attribute("aria-label", component.attributes["aria-label"])
        
        # Add content
        if component.content:
            element.add_text(component.content)
        
        # Add children
        for child in component.children:
            element.add_child(self.component_to_html(child))
        
        return element
```

### React Generation

```python
class ReactGenerator:
    def generate(self, components: List[Component], config: ExportConfig) -> Dict[str, str]:
        """Generate React application"""
        
        files = {}
        
        # Generate package.json
        files["package.json"] = self.generate_package_json(config)
        
        # Generate App component
        files["src/App.jsx"] = self.generate_app_component(components, config)
        
        # Generate individual components
        for component in self.extract_reusable_components(components):
            filename = f"src/components/{component.name}.jsx"
            files[filename] = self.generate_react_component(component, config)
        
        # Generate styles
        if config.options.use_sass:
            files["src/styles/main.scss"] = self.generate_sass(components)
        else:
            files["src/styles/main.css"] = self.generate_css(components)
        
        # Generate index files
        files["src/index.jsx"] = self.generate_index()
        files["public/index.html"] = self.generate_html_template()
        
        return files
    
    def generate_react_component(self, component: Component, config: ExportConfig) -> str:
        """Generate a React component"""
        
        if config.options.component_style == "functional":
            return self.generate_functional_component(component, config)
        else:
            return self.generate_class_component(component, config)
    
    def generate_functional_component(self, component: Component, config: ExportConfig) -> str:
        """Generate functional React component"""
        
        imports = self.collect_imports(component)
        props_interface = self.generate_props_interface(component) if config.options.use_typescript else ""
        
        template = f'''
{imports}

{props_interface}

export default function {component.name}({self.generate_props_destructuring(component)}) {{
  {self.generate_component_logic(component)}
  
  return (
    {self.component_to_jsx(component, indent=4)}
  );
}}
'''
        return template.strip()
    
    def component_to_jsx(self, component: Component, indent: int = 0) -> str:
        """Convert component to JSX"""
        
        indent_str = " " * indent
        
        # Handle special components
        if component.type == "text":
            return f'{indent_str}<span>{component.content}</span>'
        
        # Build JSX element
        tag = self.get_jsx_tag(component.type)
        props = self.build_jsx_props(component)
        
        if component.children:
            jsx = f'{indent_str}<{tag}{props}>\n'
            for child in component.children:
                jsx += self.component_to_jsx(child, indent + 2) + '\n'
            jsx += f'{indent_str}</{tag}>'
        elif component.content:
            jsx = f'{indent_str}<{tag}{props}>{component.content}</{tag}>'
        else:
            jsx = f'{indent_str}<{tag}{props} />'
        
        return jsx
```

### Style Generation

```python
class StyleGenerator:
    def generate_css(self, components: List[Component], config: ExportConfig) -> str:
        """Generate optimized CSS"""
        
        # Collect all styles
        styles = StyleCollector()
        for component in components:
            styles.add_component_styles(component)
        
        # Generate CSS rules
        css = CSSBuilder()
        
        # Add reset/normalize
        css.add_reset()
        
        # Add custom properties (CSS variables)
        css.add_rule(':root', styles.get_css_variables())
        
        # Add component styles
        for selector, rules in styles.get_rules():
            css.add_rule(selector, rules)
        
        # Add responsive styles
        for breakpoint, rules in styles.get_responsive_rules():
            css.add_media_query(breakpoint, rules)
        
        # Optimize
        if config.optimization.remove_unused_css:
            css = self.remove_unused_css(css, components)
        
        # Minify
        if config.options.minify_code:
            css = self.minify_css(css)
        
        return css.render()
    
    def generate_modern_css(self, component: Component) -> Dict[str, str]:
        """Generate modern CSS using Grid/Flexbox"""
        
        rules = {}
        
        # Layout
        if component.style.display == "flex":
            rules.update({
                "display": "flex",
                "flex-direction": component.style.flex_direction or "row",
                "justify-content": component.style.justify_content or "flex-start",
                "align-items": component.style.align_items or "stretch",
                "gap": component.style.gap or "0"
            })
        elif component.style.display == "grid":
            rules.update({
                "display": "grid",
                "grid-template-columns": component.style.grid_template_columns,
                "grid-template-rows": component.style.grid_template_rows,
                "gap": component.style.gap or "0"
            })
        
        # Spacing (using logical properties)
        if component.style.margin:
            rules["margin"] = component.style.margin
        if component.style.padding:
            rules["padding-block"] = component.style.padding
            rules["padding-inline"] = component.style.padding
        
        return rules
```

### Asset Processing

```python
class AssetProcessor:
    def process_assets(self, assets: List[Asset], config: OptimizationSettings) -> List[ProcessedAsset]:
        """Process and optimize assets"""
        
        processed = []
        
        for asset in assets:
            if asset.type == "image":
                processed.extend(self.process_image(asset, config))
            elif asset.type == "font":
                processed.append(self.process_font(asset, config))
            elif asset.type == "icon":
                processed.append(self.process_icon(asset, config))
        
        return processed
    
    def process_image(self, image: Asset, config: OptimizationSettings) -> List[ProcessedAsset]:
        """Generate responsive images"""
        
        processed = []
        
        # Generate WebP version
        if config.image_format == "webp":
            webp = self.convert_to_webp(image, config.image_quality)
            processed.append(webp)
        
        # Generate multiple sizes for srcset
        sizes = [320, 640, 1024, 1920]
        for size in sizes:
            resized = self.resize_image(image, size, config.image_quality)
            processed.append(resized)
        
        # Keep original as fallback
        processed.append(ProcessedAsset(
            source=image,
            path=f"images/{image.filename}",
            optimized=self.optimize_image(image, config)
        ))
        
        return processed
```

### Code Optimization

```python
class CodeOptimizer:
    def optimize_html(self, html: str) -> str:
        """Optimize HTML output"""
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove comments
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Remove empty attributes
        for tag in soup.find_all():
            for attr, value in list(tag.attrs.items()):
                if not value:
                    del tag.attrs[attr]
        
        # Minify
        return htmlmin.minify(
            str(soup),
            remove_empty_space=True,
            remove_comments=True,
            reduce_boolean_attributes=True
        )
    
    def optimize_css(self, css: str, used_selectors: Set[str]) -> str:
        """Remove unused CSS and optimize"""
        
        # Parse CSS
        stylesheet = cssutils.parseString(css)
        
        # Remove unused rules
        for rule in stylesheet:
            if isinstance(rule, cssutils.css.CSSStyleRule):
                if rule.selectorText not in used_selectors:
                    stylesheet.deleteRule(rule)
        
        # Optimize
        cssutils.ser.prefs.useMinified()
        
        return stylesheet.cssText.decode('utf-8')
    
    def optimize_javascript(self, js: str) -> str:
        """Optimize JavaScript with tree shaking"""
        
        # Use terser for minification
        result = subprocess.run(
            ['terser', '--compress', '--mangle'],
            input=js.encode('utf-8'),
            capture_output=True
        )
        
        return result.stdout.decode('utf-8')
```

## Export Workflow

### 1. Pre-export Validation
```python
def validate_project(project: Project) -> ValidationResult:
    errors = []
    warnings = []
    
    # Check for missing assets
    for component in project.components:
        if component.type == "image" and not component.attributes.get("src"):
            errors.append(f"Image component '{component.name}' missing source")
    
    # Check for accessibility
    for component in project.components:
        if component.type == "image" and not component.attributes.get("alt"):
            warnings.append(f"Image '{component.name}' missing alt text")
    
    # Check for SEO
    if not project.metadata.description:
        warnings.append("Project missing meta description")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )
```

### 2. Export Report
```python
@dataclass
class ExportReport:
    format: str
    timestamp: datetime
    files_generated: int
    total_size: int
    optimization_savings: int
    errors: List[str]
    warnings: List[str]
    performance_metrics: Dict[str, Any]
    
    def generate_summary(self) -> str:
        return f"""
Export Complete!

Format: {self.format}
Files: {self.files_generated}
Size: {self.format_bytes(self.total_size)}
Optimization: {self.optimization_savings}% saved

Performance Metrics:
- First Contentful Paint: {self.performance_metrics.get('fcp', 'N/A')}
- Total Blocking Time: {self.performance_metrics.get('tbt', 'N/A')}
- Cumulative Layout Shift: {self.performance_metrics.get('cls', 'N/A')}
"""
```

## Testing Requirements

### Unit Tests
- Component to HTML conversion
- JSX generation accuracy
- CSS rule generation
- Asset path resolution

### Integration Tests
- Full project export
- Framework-specific exports
- Asset processing pipeline
- Code optimization

### End-to-End Tests
- Exported code runs correctly
- React app builds and runs
- Images load properly
- Responsive behavior works

## Future Enhancements

1. **More Frameworks**: Solid, Astro, Qwik support
2. **Server-Side Rendering**: Next.js, Nuxt.js templates
3. **PWA Export**: Service worker, manifest
4. **CMS Integration**: WordPress, Drupal themes
5. **API Integration**: Generate API connections
6. **Test Generation**: Unit tests for components
7. **Documentation**: Auto-generate component docs
8. **CI/CD Integration**: GitHub Actions, Netlify config

## Example Usage

```python
# Configure export
config = ExportConfig(
    format=ExportFormat.REACT,
    output_path=Path("./exported-app"),
    options=ExportOptions(
        use_typescript=True,
        component_style="functional",
        optimize_images=True
    ),
    optimization=OptimizationSettings(
        remove_unused_css=True,
        compress_images=True,
        image_quality=85
    )
)

# Execute export
exporter = ExportPipeline()
result = exporter.export(project, config)

if result.success:
    print(result.report.generate_summary())
else:
    print("Export failed:", result.errors)
```