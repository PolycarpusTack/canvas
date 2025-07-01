"""
HTML/CSS/JS Generator

CLAUDE.md Implementation:
- #9.1: Semantic, accessible HTML
- #7.2: Output encoding safety
- #3.4: Follow HTML5 best practices
- #1.5: Performance optimization
"""

import logging
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import html
import json
from datetime import datetime

from ..export_context import ExportContext
from ..export_config import ExportConfig, OptimizationSettings
from .base_generator import BaseGenerator
from ...models.component_enhanced import Component

logger = logging.getLogger(__name__)


class HTMLGenerator(BaseGenerator):
    """
    Generate semantic HTML5 with modern CSS and JavaScript
    
    CLAUDE.md Implementation:
    - #9.1: Semantic, accessible HTML
    - #7.2: Output encoding safety
    """
    
    def __init__(self):
        super().__init__()
        self.component_counter = 0
        self.generated_ids: Set[str] = set()
    
    async def generate(self, context: ExportContext) -> Dict[str, str]:
        """Generate complete HTML project"""
        files = {}
        config = context.config
        
        # Generate main HTML file
        html_content = await self._generate_html_document(context)
        files["index.html"] = html_content
        
        # Generate CSS
        css_content = await self._generate_styles(context)
        if config.options.inline_styles:
            # CSS will be inlined in HTML (already done)
            pass
        else:
            files["assets/css/styles.css"] = css_content
        
        # Generate JavaScript
        js_content = await self._generate_javascript(context)
        if config.options.inline_scripts:
            # JS will be inlined in HTML (already done)
            pass
        else:
            files["assets/js/main.js"] = js_content
        
        # Generate additional pages
        for page_name, page_data in context.routes.items():
            if page_name != "index":
                page_html = await self._generate_page(page_name, page_data, context)
                files[f"{page_name}.html"] = page_html
        
        # Generate manifest.json for PWA (default to True for modern apps)
        if getattr(config.options, 'generate_manifest', True):
            manifest = self._generate_manifest(context)
            files["manifest.json"] = json.dumps(manifest, indent=2)
        
        # Generate service worker (default to False to avoid complexity)
        if getattr(config.options, 'generate_service_worker', False):
            sw_content = self._generate_service_worker(context)
            files["sw.js"] = sw_content
        
        # Generate sitemap
        if config.options.generate_sitemap:
            sitemap = self._generate_sitemap(context)
            files["sitemap.xml"] = sitemap
        
        # Generate robots.txt
        if config.options.generate_robots_txt:
            robots = self._generate_robots_txt(context)
            files["robots.txt"] = robots
        
        return files
    
    async def _generate_html_document(
        self,
        context: ExportContext
    ) -> str:
        """
        Generate complete HTML5 document
        
        CLAUDE.md #3.4: Follow HTML5 best practices
        """
        config = context.config
        options = config.options
        
        # Build HTML structure
        html_parts = []
        
        # DOCTYPE
        html_parts.append('<!DOCTYPE html>')
        
        # HTML element with language
        html_parts.append(f'<html lang="{options.language}">')
        
        # Head section
        head_content = await self._build_head_section(context)
        html_parts.append(head_content)
        
        # Body section
        body_content = await self._build_body_section(context)
        html_parts.append(body_content)
        
        # Close HTML
        html_parts.append('</html>')
        
        # Join all parts
        html_content = '\n'.join(html_parts)
        
        # Format based on minification settings
        if config.optimization.minify_html:
            return self._minify_html(html_content)
        else:
            return self._format_html(html_content)
    
    async def _build_head_section(self, context: ExportContext) -> str:
        """Build HTML head section with all meta tags"""
        options = context.config.options
        optimization = context.config.optimization
        
        head_parts = ['<head>']
        
        # Charset (first thing in head)
        head_parts.append(f'  <meta charset="{options.charset}">')
        
        # Viewport for responsive design
        if options.viewport_meta:
            head_parts.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        
        # Title
        title = html.escape(options.title or "Canvas Export")
        head_parts.append(f'  <title>{title}</title>')
        
        # Meta description
        if options.meta_description:
            desc = html.escape(options.meta_description)
            head_parts.append(f'  <meta name="description" content="{desc}">')
        
        # Meta keywords
        if options.meta_keywords:
            keywords = html.escape(", ".join(options.meta_keywords))
            head_parts.append(f'  <meta name="keywords" content="{keywords}">')
        
        # Open Graph tags
        if options.og_tags:
            head_parts.extend(self._generate_og_tags(context))
        
        # Twitter Card tags
        if options.twitter_cards:
            head_parts.extend(self._generate_twitter_tags(context))
        
        # Favicon
        if options.favicon:
            head_parts.append(f'  <link rel="icon" href="{options.favicon}">')
        
        # Preconnect to external domains
        if options.use_cdn:
            cdn_domain = self._get_cdn_domain(options.cdn_provider)
            head_parts.append(f'  <link rel="preconnect" href="{cdn_domain}">')
        
        # CSS
        if options.inline_styles:
            css_content = await self._generate_styles(context)
            if optimization.inline_critical_css:
                # Split critical and non-critical CSS
                critical_css = self._extract_critical_css(css_content, context)
                head_parts.append(f'  <style>{critical_css}</style>')
                # Rest loaded async
                head_parts.append(f'  <style media="print" onload="this.media=\'all\'">{css_content}</style>')
            else:
                head_parts.append(f'  <style>{css_content}</style>')
        else:
            # External CSS
            css_path = "assets/css/styles.css"
            if optimization.inline_critical_css:
                # Inline critical CSS
                critical_css = self._extract_critical_css("", context)
                head_parts.append(f'  <style>{critical_css}</style>')
                # Preload full CSS
                head_parts.append(f'  <link rel="preload" href="{css_path}" as="style">')
                head_parts.append(f'  <link rel="stylesheet" href="{css_path}" media="print" onload="this.media=\'all\'">')
                # Fallback
                head_parts.append(f'  <noscript><link rel="stylesheet" href="{css_path}"></noscript>')
            else:
                head_parts.append(f'  <link rel="stylesheet" href="{css_path}">')
        
        # Preload fonts
        if optimization.preload_fonts:
            for font in self._get_used_fonts(context):
                head_parts.append(f'  <link rel="preload" href="{font.url}" as="font" type="font/{font.format}" crossorigin>')
        
        # PWA manifest
        if getattr(context.config.options, 'generate_manifest', True):
            head_parts.append('  <link rel="manifest" href="manifest.json">')
        
        # Theme color
        head_parts.append('  <meta name="theme-color" content="#5E6AD2">')
        
        head_parts.append('</head>')
        
        return '\n'.join(head_parts)
    
    async def _build_body_section(self, context: ExportContext) -> str:
        """Build HTML body with components"""
        body_parts = ['<body>']
        
        # Skip to content link for accessibility
        if getattr(context.config.options, 'include_skip_links', True):
            body_parts.append('  <a href="#main" class="skip-link">Skip to main content</a>')
        
        # Convert components to HTML
        root_components = self._get_root_components(context)
        for component in root_components:
            html_element = await self._component_to_html(component, context)
            body_parts.append(self._indent_html(html_element, 1))
        
        # JavaScript
        if context.config.options.inline_scripts:
            js_content = await self._generate_javascript(context)
            body_parts.append(f'  <script>{js_content}</script>')
        else:
            # External JavaScript
            js_path = "assets/js/main.js"
            if context.config.optimization.bundle_js:
                body_parts.append(f'  <script src="{js_path}" defer></script>')
            else:
                # Multiple script files
                body_parts.append(f'  <script src="{js_path}" defer></script>')
        
        # Service Worker registration
        if getattr(context.config.options, 'generate_service_worker', False):
            body_parts.append(self._generate_sw_registration())
        
        body_parts.append('</body>')
        
        return '\n'.join(body_parts)
    
    async def _component_to_html(
        self,
        component: Component,
        context: ExportContext,
        indent: int = 0
    ) -> str:
        """
        Convert Canvas component to semantic HTML
        
        CLAUDE.md #9.1: Use semantic elements
        CLAUDE.md #7.2: Escape user content
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
            "search": "search",  # HTML5.3
            "heading": self._get_heading_element(component),
            "paragraph": "p",
            "list": self._get_list_element(component),
            "button": "button",
            "link": "a",
            "image": "img",
            "video": "video",
            "audio": "audio"
        }
        
        # Determine element type
        element_type = semantic_map.get(component.type)
        if not element_type:
            element_type = semantic_map.get(component.semantic_role, "div")
        
        # Build attributes
        attributes = self._build_attributes(component, context)
        
        # Special handling for void elements
        void_elements = {"img", "br", "hr", "input", "meta", "link"}
        is_void = element_type in void_elements
        
        # Build opening tag
        attr_string = self._attributes_to_string(attributes)
        opening_tag = f"<{element_type}{attr_string}>"
        
        if is_void:
            return opening_tag
        
        # Handle content and children
        content_parts = []
        
        # Add text content
        if component.content:
            if component.content_type == "html":
                # Sanitized HTML content
                content_parts.append(self._sanitize_html(component.content))
            else:
                # Escaped text content
                content_parts.append(html.escape(str(component.content)))
        
        # Add children recursively
        for child in component.children:
            child_html = await self._component_to_html(child, context, indent + 1)
            content_parts.append(child_html)
        
        # Join content
        if content_parts:
            content = '\n'.join(content_parts)
            # Add indentation for multiline content
            if '\n' in content:
                content = '\n' + self._indent_html(content, indent + 1) + '\n' + ('  ' * indent)
        else:
            content = ''
        
        # Build complete element
        return f"{opening_tag}{content}</{element_type}>"
    
    def _build_attributes(self, component: Component, context: ExportContext) -> Dict[str, str]:
        """Build HTML attributes for component"""
        attributes = {}
        
        # ID attribute
        if component.id:
            comp_id = self._sanitize_id(component.id)
            # Ensure unique IDs
            if comp_id in self.generated_ids:
                comp_id = f"{comp_id}_{self.component_counter}"
                self.component_counter += 1
            self.generated_ids.add(comp_id)
            attributes["id"] = comp_id
        
        # Class attribute
        classes = []
        if component.class_name:
            classes.extend(component.class_name.split())
        
        # Add responsive classes
        if hasattr(component, "responsive_classes") and component.responsive_classes:
            classes.extend(component.responsive_classes)
        
        # Add component type class
        classes.append(f"canvas-{component.type}")
        
        if classes:
            attributes["class"] = " ".join(classes)
        
        # Style attribute
        if component.styles:
            style_string = self._styles_to_string(component.styles)
            if style_string:
                attributes["style"] = style_string
        
        # ARIA attributes
        aria_attrs = self._generate_aria_attributes(component)
        attributes.update(aria_attrs)
        
        # Data attributes
        if hasattr(component, "data_attributes"):
            for key, value in component.data_attributes.items():
                attributes[f"data-{key}"] = str(value)
        
        # Component-specific attributes
        if component.type == "link":
            attributes["href"] = component.properties.get("href", "#")
            if component.properties.get("target") == "_blank":
                attributes["target"] = "_blank"
                attributes["rel"] = "noopener noreferrer"
        
        elif component.type == "image":
            attributes["src"] = component.properties.get("src", "")
            attributes["alt"] = component.properties.get("alt", "")
            if context.config.optimization.lazy_load_images:
                attributes["loading"] = "lazy"
            attributes["decoding"] = "async"
            
            # Responsive images
            if hasattr(component, "srcset"):
                attributes["srcset"] = component.srcset
                attributes["sizes"] = component.sizes or "100vw"
        
        elif component.type == "input":
            attributes["type"] = component.properties.get("type", "text")
            attributes["name"] = component.properties.get("name", "")
            if component.properties.get("required"):
                attributes["required"] = ""
            if component.properties.get("placeholder"):
                attributes["placeholder"] = component.properties["placeholder"]
        
        elif component.type == "form":
            attributes["method"] = component.properties.get("method", "POST")
            attributes["action"] = component.properties.get("action", "#")
            if component.properties.get("novalidate"):
                attributes["novalidate"] = ""
        
        return attributes
    
    def _generate_aria_attributes(self, component: Component) -> Dict[str, str]:
        """
        Generate ARIA attributes for accessibility
        
        CLAUDE.md #9.1: WCAG compliance
        """
        aria = {}
        
        # Role attribute
        if hasattr(component, "role") and component.role:
            aria["role"] = component.role
        
        # Label
        if hasattr(component, "aria_label") and component.aria_label:
            aria["aria-label"] = component.aria_label
        elif component.type in ["button", "link"] and component.content:
            # Use content as label if no explicit label
            pass
        elif component.type in ["input", "textarea", "select"]:
            # Form elements need labels
            if not component.properties.get("aria-label"):
                logger.warning(f"Form element {component.id} missing label")
        
        # Describedby
        if hasattr(component, "aria_describedby"):
            aria["aria-describedby"] = component.aria_describedby
        
        # Live regions
        if hasattr(component, "aria_live"):
            aria["aria-live"] = component.aria_live
            if hasattr(component, "aria_atomic"):
                aria["aria-atomic"] = str(component.aria_atomic).lower()
        
        # States
        if hasattr(component, "aria_expanded"):
            aria["aria-expanded"] = str(component.aria_expanded).lower()
        if hasattr(component, "aria_selected"):
            aria["aria-selected"] = str(component.aria_selected).lower()
        if hasattr(component, "aria_checked"):
            aria["aria-checked"] = str(component.aria_checked).lower()
        
        return aria
    
    async def _generate_styles(self, context: ExportContext) -> str:
        """Generate CSS stylesheet"""
        css_parts = []
        
        # Reset/Normalize CSS
        css_parts.append(self._generate_css_reset())
        
        # CSS Variables
        css_parts.append(self._generate_css_variables(context))
        
        # Utility classes
        css_parts.append(self._generate_utility_classes(context))
        
        # Component styles
        css_parts.append(self._generate_component_styles(context))
        
        # Responsive styles
        css_parts.append(self._generate_responsive_styles(context))
        
        # Animations
        css_parts.append(self._generate_animations(context))
        
        # Print styles
        css_parts.append(self._generate_print_styles())
        
        return '\n\n'.join(css_parts)
    
    async def _generate_javascript(self, context: ExportContext) -> str:
        """Generate JavaScript code"""
        js_parts = []
        
        # Polyfills if needed
        if getattr(context.config.options, 'focus_visible_polyfill', True):
            js_parts.append(self._get_focus_visible_polyfill())
        
        # Component initialization
        js_parts.append(self._generate_component_init(context))
        
        # Event handlers
        js_parts.append(self._generate_event_handlers(context))
        
        # Accessibility enhancements
        js_parts.append(self._generate_a11y_enhancements(context))
        
        # Lazy loading
        if context.config.optimization.lazy_load_images:
            js_parts.append(self._generate_lazy_loading())
        
        return '\n\n'.join(js_parts)
    
    def _sanitize_id(self, id_value: str) -> str:
        """Sanitize ID for HTML compliance"""
        # Replace invalid characters
        sanitized = id_value.replace(" ", "-").replace(".", "-")
        # Ensure starts with letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = f"id-{sanitized}"
        return sanitized
    
    def _sanitize_html(self, html_content: str) -> str:
        """
        Sanitize HTML content for safety
        
        CLAUDE.md #7.2: Prevent XSS
        """
        # This is a simplified version - in production use bleach or similar
        # For now, just escape everything
        return html.escape(html_content)
    
    def _attributes_to_string(self, attributes: Dict[str, str]) -> str:
        """Convert attributes dictionary to HTML string"""
        if not attributes:
            return ""
        
        parts = []
        for key, value in attributes.items():
            if value == "":
                # Boolean attribute
                parts.append(key)
            else:
                # Regular attribute
                escaped_value = html.escape(value, quote=True)
                parts.append(f'{key}="{escaped_value}"')
        
        return " " + " ".join(parts) if parts else ""
    
    def _styles_to_string(self, styles: Dict[str, Any]) -> str:
        """Convert styles dictionary to CSS string"""
        if not styles:
            return ""
        
        style_parts = []
        for prop, value in styles.items():
            # Convert camelCase to kebab-case
            css_prop = self._camel_to_kebab(prop)
            style_parts.append(f"{css_prop}: {value}")
        
        return "; ".join(style_parts)
    
    def _camel_to_kebab(self, name: str) -> str:
        """Convert camelCase to kebab-case"""
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append('-')
            result.append(char.lower())
        return ''.join(result)
    
    def _get_heading_element(self, component: Component) -> str:
        """Get appropriate heading element"""
        level = component.properties.get("level", 2)
        level = max(1, min(6, level))  # Clamp between 1-6
        return f"h{level}"
    
    def _get_list_element(self, component: Component) -> str:
        """Get appropriate list element"""
        list_type = component.properties.get("type", "unordered")
        return "ol" if list_type == "ordered" else "ul"
    
    def _get_root_components(self, context: ExportContext) -> List[Component]:
        """Get root level components"""
        return [comp for comp in context.project.components if not comp.parent_id]
    
    def _indent_html(self, html_string: str, level: int) -> str:
        """Indent HTML string"""
        indent = "  " * level
        lines = html_string.split('\n')
        return '\n'.join(indent + line if line.strip() else line for line in lines)
    
    def _minify_html(self, html_content: str) -> str:
        """Basic HTML minification"""
        # Remove comments
        import re
        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        # Remove unnecessary whitespace
        html_content = re.sub(r'\s+', ' ', html_content)
        html_content = re.sub(r'>\s+<', '><', html_content)
        return html_content.strip()
    
    def _format_html(self, html_content: str) -> str:
        """Format HTML with proper indentation"""
        # This is a simplified formatter
        # In production, use a proper HTML formatter
        return html_content
    
    async def _generate_page(
        self,
        page_name: str,
        page_data: Any,
        context: ExportContext
    ) -> str:
        """
        Generate HTML for a specific page
        
        CLAUDE.md #9.1: Semantic HTML generation
        """
        try:
            # Create a copy of context for this page
            page_context = ExportContext(
                project=context.project,
                config=context.config,
                timestamp=context.timestamp
            )
            
            # Set page-specific data
            if hasattr(page_data, 'components'):
                page_context.components = page_data.components
            elif hasattr(page_data, 'root_component_id'):
                # Find root component for this page
                root_comp = context.project.get_component_by_id(page_data.root_component_id)
                if root_comp:
                    page_context.components = [root_comp]
            
            # Generate page HTML
            return await self._generate_html_document(page_context)
            
        except Exception as e:
            self.logger.error(f"Failed to generate page {page_name}: {e}")
            return f"<!-- Error generating page {page_name}: {e} -->"
    
    def _generate_manifest(self, context: ExportContext) -> str:
        """
        Generate web app manifest
        
        CLAUDE.md #3.4: Progressive web app features
        """
        import json
        
        manifest = {
            "name": context.project.name,
            "short_name": context.project.name[:12],
            "description": context.project.description or f"Generated by Canvas",
            "start_url": "/",
            "display": "standalone",
            "theme_color": "#000000",
            "background_color": "#ffffff",
            "icons": []
        }
        
        # Add icons if available
        for asset in context.project.assets:
            if (asset.metadata.asset_type == "image" and 
                "icon" in asset.metadata.name.lower()):
                
                manifest["icons"].append({
                    "src": asset.get_export_url(),
                    "sizes": f"{asset.metadata.get('width', 192)}x{asset.metadata.get('height', 192)}",
                    "type": asset.metadata.mime_type
                })
        
        # Add default icon if none provided
        if not manifest["icons"]:
            manifest["icons"] = [
                {
                    "src": "/assets/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "/assets/icon-512.png", 
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ]
        
        return json.dumps(manifest, indent=2)
    
    def _generate_service_worker(self, context: ExportContext) -> str:
        """
        Generate service worker for PWA
        
        CLAUDE.md #3.4: Progressive web app features
        """
        sw_content = """
// Service Worker for Canvas Generated App
const CACHE_NAME = 'canvas-app-v1';
const urlsToCache = [
  '/',
  '/assets/css/styles.css',
  '/assets/js/main.js'
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});
"""
        return sw_content.strip()
    
    def _generate_sitemap(self, context: ExportContext) -> str:
        """Generate XML sitemap"""
        urls = []
        base_url = context.config.metadata.get('base_url', 'https://example.com')
        
        # Add pages
        if hasattr(context.project, 'pages'):
            for page in context.project.pages:
                urls.append(f"{base_url}{page.path}")
        else:
            urls.append(base_url)
        
        sitemap_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
'''
        
        for url in urls:
            sitemap_xml += f'''  <url>
    <loc>{url}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
'''
        
        sitemap_xml += '</urlset>'
        return sitemap_xml
    
    def _generate_robots_txt(self, context: ExportContext) -> str:
        """Generate robots.txt"""
        base_url = context.config.metadata.get('base_url', 'https://example.com')
        
        robots_content = f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml
"""
        return robots_content.strip()
    
    async def _build_head_section(self, context: ExportContext) -> str:
        """Build HTML head section"""
        head_parts = []
        
        # Basic meta tags
        head_parts.append('<meta charset="UTF-8">')
        head_parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
        
        # Title
        title = context.project.metadata.get('title', context.project.name)
        head_parts.append(f'<title>{html.escape(title)}</title>')
        
        # Meta description
        if context.project.description:
            head_parts.append(f'<meta name="description" content="{html.escape(context.project.description)}">')
        
        # CSS
        head_parts.append('<link rel="stylesheet" href="assets/css/styles.css">')
        
        return '\n    '.join(head_parts)
    
    async def _build_body_section(self, context: ExportContext) -> str:
        """Build HTML body content"""
        body_parts = []
        
        # Skip to main content link
        body_parts.append('<a href="#main" class="skip-link">Skip to main content</a>')
        
        # Main content
        if context.project.components:
            for component in context.project.components:
                component_html = await self._component_to_html(component, context)
                body_parts.append(component_html)
        
        # Scripts
        body_parts.append('<script src="assets/js/main.js"></script>')
        
        return '\n    '.join(body_parts)
    
    def _get_cdn_domain(self, provider: str) -> str:
        """Get CDN domain for provider"""
        cdn_domains = {
            'cloudflare': 'cdnjs.cloudflare.com',
            'jsdelivr': 'cdn.jsdelivr.net',
            'unpkg': 'unpkg.com'
        }
        return cdn_domains.get(provider, 'cdnjs.cloudflare.com')
    
    def _get_used_fonts(self, context: ExportContext) -> List[str]:
        """Get list of fonts used in the project"""
        fonts = set()
        
        # Collect fonts from component styles
        for component in context.project.components:
            styles = component.get_all_styles()
            font_family = styles.get('fontFamily') or styles.get('font-family')
            if font_family:
                fonts.add(font_family)
        
        return list(fonts)
    
    def _get_root_components(self, context: ExportContext) -> List[Any]:
        """Get root-level components"""
        if not context.project.components:
            return []
        
        return [comp for comp in context.project.components if not comp.parent_id]
    
    def _generate_css_reset(self) -> str:
        """Generate CSS reset/normalize"""
        return """
/* CSS Reset */
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html, body {
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #333;
}

img {
    max-width: 100%;
    height: auto;
}

button {
    cursor: pointer;
    border: none;
    background: none;
    font: inherit;
}

a {
    text-decoration: none;
    color: inherit;
}

ul, ol {
    list-style: none;
}
"""
    
    def _generate_css_variables(self, context: ExportContext) -> str:
        """Generate CSS custom properties"""
        return """
:root {
    --primary-color: #007bff;
    --secondary-color: #6c757d;
    --success-color: #28a745;
    --danger-color: #dc3545;
    --warning-color: #ffc107;
    --info-color: #17a2b8;
    --light-color: #f8f9fa;
    --dark-color: #343a40;
    
    --font-size-xs: 0.75rem;
    --font-size-sm: 0.875rem;
    --font-size-base: 1rem;
    --font-size-lg: 1.25rem;
    --font-size-xl: 1.5rem;
    
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 3rem;
    
    --border-radius: 0.25rem;
    --border-radius-lg: 0.5rem;
    
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
}
"""
    
    def _generate_utility_classes(self, context: ExportContext) -> str:
        """Generate utility CSS classes"""
        return """
/* Utility Classes */
.text-center { text-align: center; }
.text-left { text-align: left; }
.text-right { text-align: right; }

.d-none { display: none; }
.d-block { display: block; }
.d-flex { display: flex; }
.d-grid { display: grid; }

.justify-content-center { justify-content: center; }
.justify-content-between { justify-content: space-between; }
.align-items-center { align-items: center; }

.m-0 { margin: 0; }
.m-1 { margin: var(--spacing-xs); }
.m-2 { margin: var(--spacing-sm); }
.m-3 { margin: var(--spacing-md); }
.m-4 { margin: var(--spacing-lg); }

.p-0 { padding: 0; }
.p-1 { padding: var(--spacing-xs); }
.p-2 { padding: var(--spacing-sm); }
.p-3 { padding: var(--spacing-md); }
.p-4 { padding: var(--spacing-lg); }

.w-100 { width: 100%; }
.h-100 { height: 100%; }

.btn {
    display: inline-block;
    padding: 0.375rem 0.75rem;
    margin-bottom: 0;
    font-size: 1rem;
    font-weight: 400;
    line-height: 1.5;
    text-align: center;
    text-decoration: none;
    vertical-align: middle;
    cursor: pointer;
    border: 1px solid transparent;
    border-radius: var(--border-radius);
    transition: all 0.15s ease-in-out;
}

.btn-primary {
    color: #fff;
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}

.btn-primary:hover {
    background-color: #0056b3;
    border-color: #004085;
}
"""
    
    def _generate_component_styles(self, context: ExportContext) -> str:
        """Generate component-specific styles"""
        css_parts = []
        
        for component in context.project.components:
            if hasattr(component, 'styles') and component.styles:
                # Generate styles for this component
                component_class = f".canvas-{component.type}"
                if component.id:
                    component_id = f"#{self._sanitize_id(component.id)}"
                    css_parts.append(f"{component_id} {{")
                else:
                    css_parts.append(f"{component_class} {{")
                
                for prop, value in component.styles.items():
                    css_prop = self._camel_to_kebab(prop)
                    css_parts.append(f"  {css_prop}: {value};")
                
                css_parts.append("}")
        
        return '\n'.join(css_parts)
    
    def _generate_responsive_styles(self, context: ExportContext) -> str:
        """Generate responsive media queries"""
        return """
/* Responsive Styles */
@media (max-width: 768px) {
    .container {
        padding: 1rem;
    }
    
    .btn {
        width: 100%;
        margin-bottom: 0.5rem;
    }
}

@media (max-width: 576px) {
    html {
        font-size: 14px;
    }
    
    .container {
        padding: 0.5rem;
    }
}
"""
    
    def _generate_animations(self, context: ExportContext) -> str:
        """Generate CSS animations"""
        return """
/* Animations */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideIn {
    from { transform: translateY(-10px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

.fade-in {
    animation: fadeIn 0.3s ease-in-out;
}

.slide-in {
    animation: slideIn 0.3s ease-in-out;
}
"""
    
    def _generate_print_styles(self) -> str:
        """Generate print-specific styles"""
        return """
/* Print Styles */
@media print {
    .no-print {
        display: none !important;
    }
    
    body {
        font-size: 12pt;
        line-height: 1.4;
    }
    
    h1, h2, h3, h4, h5, h6 {
        page-break-after: avoid;
    }
    
    img {
        max-width: 100% !important;
    }
    
    @page {
        margin: 0.5in;
    }
}
"""
    
    def _generate_component_init(self, context: ExportContext) -> str:
        """Generate component initialization JavaScript"""
        return """
// Component Initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize interactive components
    initializeButtons();
    initializeForms();
    initializeModals();
});

function initializeButtons() {
    const buttons = document.querySelectorAll('button[data-action]');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const action = this.getAttribute('data-action');
            if (window[action] && typeof window[action] === 'function') {
                window[action](e, this);
            }
        });
    });
}

function initializeForms() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

function initializeModals() {
    const modalTriggers = document.querySelectorAll('[data-modal-target]');
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const targetId = this.getAttribute('data-modal-target');
            const modal = document.getElementById(targetId);
            if (modal) {
                showModal(modal);
            }
        });
    });
}
"""
    
    def _generate_event_handlers(self, context: ExportContext) -> str:
        """Generate event handler JavaScript"""
        return """
// Event Handlers
function handleClick(event, element) {
    console.log('Button clicked:', element);
}

function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    return isValid;
}

function showFieldError(field, message) {
    field.classList.add('error');
    const errorElement = field.parentNode.querySelector('.error-message');
    if (errorElement) {
        errorElement.textContent = message;
    }
}

function clearFieldError(field) {
    field.classList.remove('error');
    const errorElement = field.parentNode.querySelector('.error-message');
    if (errorElement) {
        errorElement.textContent = '';
    }
}

function showModal(modal) {
    modal.style.display = 'block';
    modal.classList.add('active');
    document.body.classList.add('modal-open');
}

function hideModal(modal) {
    modal.style.display = 'none';
    modal.classList.remove('active');
    document.body.classList.remove('modal-open');
}
"""
    
    def _generate_a11y_enhancements(self, context: ExportContext) -> str:
        """Generate accessibility enhancement JavaScript"""
        return """
// Accessibility Enhancements
function enhanceAccessibility() {
    // Focus management
    const focusableElements = document.querySelectorAll(
        'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select'
    );
    
    // Skip links functionality
    const skipLinks = document.querySelectorAll('.skip-link');
    skipLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.focus();
            }
        });
    });
    
    // ARIA live region updates
    function announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }
    
    // Keyboard navigation for custom components
    function handleKeyboardNavigation(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            if (e.target.getAttribute('role') === 'button') {
                e.preventDefault();
                e.target.click();
            }
        }
    }
    
    document.addEventListener('keydown', handleKeyboardNavigation);
}

// Initialize accessibility enhancements
document.addEventListener('DOMContentLoaded', enhanceAccessibility);
"""
    
    def _generate_lazy_loading(self) -> str:
        """Generate lazy loading JavaScript"""
        return """
// Lazy Loading
function initializeLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        const images = document.querySelectorAll('img[data-src]');
        images.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for browsers without IntersectionObserver
        const images = document.querySelectorAll('img[data-src]');
        images.forEach(img => {
            img.src = img.dataset.src;
            img.classList.remove('lazy');
        });
    }
}

document.addEventListener('DOMContentLoaded', initializeLazyLoading);
"""
    
    def _get_focus_visible_polyfill(self) -> str:
        """Get focus-visible polyfill"""
        return """
// Focus-visible polyfill
(function() {
    var hadKeyboardEvent = true;
    var keyboardThrottleTimeout;
    
    function onPointerDown() {
        hadKeyboardEvent = false;
    }
    
    function onKeyDown(e) {
        if (e.metaKey || e.altKey || e.ctrlKey) {
            return;
        }
        hadKeyboardEvent = true;
    }
    
    function onFocus(e) {
        if (hadKeyboardEvent || e.target.matches(':focus-visible')) {
            e.target.classList.add('focus-visible');
        }
    }
    
    function onBlur(e) {
        e.target.classList.remove('focus-visible');
    }
    
    document.addEventListener('keydown', onKeyDown, true);
    document.addEventListener('mousedown', onPointerDown, true);
    document.addEventListener('pointerdown', onPointerDown, true);
    document.addEventListener('touchstart', onPointerDown, true);
    document.addEventListener('focus', onFocus, true);
    document.addEventListener('blur', onBlur, true);
})();
"""
    
    def _generate_sw_registration(self) -> str:
        """Generate service worker registration script"""
        return """
<script>
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed');
            });
    });
}
</script>"""