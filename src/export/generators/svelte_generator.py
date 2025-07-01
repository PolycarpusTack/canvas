"""
Svelte Generator

CLAUDE.md Implementation:
- #1.4: Modern Svelte patterns with SvelteKit
- #1.2: DRY component generation
- #4.1: TypeScript support
- #7.2: XSS prevention in templates
"""

import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
import json
import re

from ..export_context import ExportContext
from ..export_config import ExportConfig
from .base_generator import BaseGenerator
from ...models.component_enhanced import Component

logger = logging.getLogger(__name__)


@dataclass
class SvelteComponentInfo:
    """Information about a Svelte component"""
    component: Component
    name: str
    path: str
    props: List[Dict[str, str]] = field(default_factory=list)
    stores: Set[str] = field(default_factory=set)
    has_reactive: bool = False
    has_lifecycle: bool = False
    children: List['SvelteComponentInfo'] = field(default_factory=list)


class SvelteGenerator(BaseGenerator):
    """
    Generate modern Svelte application with SvelteKit
    
    CLAUDE.md Implementation:
    - #1.4: Modern Svelte patterns (stores, reactive statements)
    - #1.2: DRY component generation
    """
    
    def __init__(self):
        super().__init__()
        self.component_registry: Dict[str, SvelteComponentInfo] = {}
        self.generated_stores: Set[str] = set()
        
    async def generate(self, context: ExportContext) -> Dict[str, str]:
        """Generate complete SvelteKit application"""
        files = {}
        config = context.config.options
        
        # Generate package.json
        files["package.json"] = self._generate_package_json(context)
        
        # Generate SvelteKit config files
        files["svelte.config.js"] = self._generate_svelte_config(context)
        files["vite.config.js"] = self._generate_vite_config(context)
        
        # Generate TypeScript config if enabled
        if config.use_typescript:
            files["tsconfig.json"] = self._generate_tsconfig()
            files["app.d.ts"] = self._generate_app_types()
        
        # Generate app structure
        files["src/app.html"] = self._generate_app_html(context)
        files["src/app.css"] = self._generate_global_styles(context)
        
        # Generate routes
        route_files = await self._generate_routes(context)
        files.update(route_files)
        
        # Extract and generate components
        components = self._extract_components(context)
        for comp_info in components:
            component_files = await self._generate_component_files(comp_info, context)
            files.update(component_files)
            
        # Generate stores
        if self._needs_stores(context):
            store_files = self._generate_stores(context)
            files.update(store_files)
            
        # Generate utilities
        if config.include_utilities:
            utility_files = self._generate_utilities(context)
            files.update(utility_files)
            
        # Generate API routes if needed
        if self._needs_api_routes(context):
            api_files = self._generate_api_routes(context)
            files.update(api_files)
            
        # Generate tests if requested
        if config.generate_tests:
            test_files = await self._generate_tests(components, context)
            files.update(test_files)
            
        # Generate README
        if config.generate_readme:
            files["README.md"] = self._generate_readme(context)
            
        # Generate .gitignore
        files[".gitignore"] = self._generate_gitignore()
        
        # Generate Playwright config for testing
        if config.generate_tests:
            files["playwright.config.js"] = self._generate_playwright_config()
        
        return files
    
    def _generate_package_json(self, context: ExportContext) -> str:
        """Generate package.json with SvelteKit dependencies"""
        config = context.config.options
        
        package_data = {
            "name": context.project.name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "description": "SvelteKit app exported from Canvas Editor",
            "private": True,
            "scripts": {
                "build": "vite build",
                "dev": "vite dev",
                "preview": "vite preview",
                "test": "npm run test:integration && npm run test:unit",
                "check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json",
                "check:watch": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json --watch",
                "test:integration": "playwright test",
                "test:unit": "vitest"
            },
            "devDependencies": {
                "@sveltejs/adapter-auto": "^2.0.0",
                "@sveltejs/kit": "^1.20.4",
                "svelte": "^4.0.5",
                "vite": "^4.4.2"
            },
            "type": "module",
            "dependencies": {}
        }
        
        # Add TypeScript support
        if config.use_typescript:
            package_data["devDependencies"].update({
                "typescript": "^5.0.0",
                "svelte-check": "^3.4.3",
                "@sveltejs/adapter-auto": "^2.0.0"
            })
        
        # Add testing dependencies
        if config.generate_tests:
            package_data["devDependencies"].update({
                "@playwright/test": "^1.28.0",
                "vitest": "^0.34.0",
                "@testing-library/svelte": "^4.0.3"
            })
        
        # Add CSS framework
        if config.css_framework == "tailwind":
            package_data["devDependencies"].update({
                "tailwindcss": "^3.3.0",
                "postcss": "^8.4.24",
                "autoprefixer": "^10.4.14",
                "@tailwindcss/forms": "^0.5.2"
            })
        elif config.css_framework == "bootstrap":
            package_data["dependencies"]["bootstrap"] = "^5.3.0"
        
        # Add state management
        if config.state_management == "svelte-stores":
            # Built into Svelte, no additional dependencies
            pass
        
        # Add UI library
        if config.ui_library == "carbon":
            package_data["dependencies"]["carbon-components-svelte"] = "^0.82.0"
        elif config.ui_library == "smelte":
            package_data["dependencies"]["smelte"] = "^3.2.0"
            
        return json.dumps(package_data, indent=2)
    
    def _generate_svelte_config(self, context: ExportContext) -> str:
        """Generate svelte.config.js"""
        config = context.config.options
        
        preprocessors = []
        if config.use_typescript:
            preprocessors.append("vitePreprocess()")
        
        return f"""import adapter from '@sveltejs/adapter-auto';
{("import { vitePreprocess } from '@sveltejs/kit/vite';" if config.use_typescript else "")}

/** @type {{import('@sveltejs/kit').Config}} */
const config = {{
  // Consult https://kit.svelte.dev/docs/integrations#preprocessors
  // for more information about preprocessors
  preprocess: [{', '.join(preprocessors) if preprocessors else ''}],

  kit: {{
    // adapter-auto only supports some environments, see https://kit.svelte.dev/docs/adapter-auto
    adapter: adapter()
  }}
}};

export default config;
"""
    
    def _generate_vite_config(self, context: ExportContext) -> str:
        """Generate vite.config.js"""
        return """import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  test: {
    include: ['src/**/*.{test,spec}.{js,ts}']
  }
});
"""
    
    def _generate_app_html(self, context: ExportContext) -> str:
        """Generate app.html template"""
        return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%sveltekit.assets%/favicon.png" />
    <meta name="viewport" content="width=device-width" />
    <title>{context.project.name}</title>
    <meta name="description" content="{context.project.description or 'Generated by Canvas Editor'}" />
    %sveltekit.head%
  </head>
  <body data-sveltekit-preload-data="hover">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
"""
    
    def _generate_global_styles(self, context: ExportContext) -> str:
        """Generate global CSS styles"""
        return """/* Global styles */
:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;

  color-scheme: light dark;
  color: rgba(255, 255, 255, 0.87);
  background-color: #242424;

  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  -webkit-text-size-adjust: 100%;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  display: flex;
  place-items: center;
  min-width: 320px;
  min-height: 100vh;
}

h1, h2, h3, h4, h5, h6 {
  color: #213547;
}

@media (prefers-color-scheme: light) {
  :root {
    color: #213547;
    background-color: #ffffff;
  }
  
  h1, h2, h3, h4, h5, h6 {
    color: #213547;
  }
}

/* Component styles */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.page {
  padding: 2rem 0;
}
"""
    
    async def _generate_routes(self, context: ExportContext) -> Dict[str, str]:
        """Generate SvelteKit routes"""
        files = {}
        
        # Generate main layout
        files["src/routes/+layout.svelte"] = self._generate_layout(context)
        
        # Generate main page
        files["src/routes/+page.svelte"] = await self._generate_main_page(context)
        
        # Generate additional pages if needed
        if self._needs_multiple_pages(context):
            page_files = await self._generate_additional_pages(context)
            files.update(page_files)
        
        return files
    
    def _generate_layout(self, context: ExportContext) -> str:
        """Generate main layout"""
        return """<script>
  import '../app.css';
</script>

<div class="app">
  <header>
    <nav>
      <a href="/">Home</a>
      <!-- Add more navigation links -->
    </nav>
  </header>

  <main>
    <slot />
  </main>

  <footer>
    <p>&copy; 2024 Canvas Export</p>
  </footer>
</div>

<style>
  .app {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  header {
    background: #1976d2;
    color: white;
    padding: 1rem;
  }

  nav a {
    color: white;
    text-decoration: none;
    margin-right: 1rem;
  }

  nav a:hover {
    text-decoration: underline;
  }

  main {
    flex: 1;
    padding: 2rem;
  }

  footer {
    background: #f5f5f5;
    padding: 1rem;
    text-align: center;
  }
</style>
"""
    
    async def _generate_main_page(self, context: ExportContext) -> str:
        """Generate main page"""
        # Convert root components to Svelte
        root_components = self._get_root_components(context)
        component_markup = await self._components_to_svelte(root_components, context)
        
        return f"""<script>
  // Page logic here
  let title = '{context.project.name}';
</script>

<svelte:head>
  <title>{{title}}</title>
  <meta name="description" content="Generated by Canvas Editor" />
</svelte:head>

<div class="page-container">
  <h1>{{title}}</h1>
  
{component_markup}
</div>

<style>
  .page-container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }}
  
  h1 {{
    text-align: center;
    margin-bottom: 2rem;
  }}
</style>
"""
    
    async def _components_to_svelte(
        self,
        components: List[Component],
        context: ExportContext,
        indent: int = 2
    ) -> str:
        """Convert components to Svelte markup"""
        markup_parts = []
        
        for component in components:
            markup = await self._component_to_svelte(component, context, indent)
            markup_parts.append(markup)
            
        return "\n".join(markup_parts)
    
    async def _component_to_svelte(
        self,
        component: Component,
        context: ExportContext,
        indent: int = 0
    ) -> str:
        """
        Convert single component to Svelte markup
        
        CLAUDE.md #7.2: Escape user content
        """
        indent_str = " " * indent
        
        # Handle text nodes
        if component.type == "text":
            # Escape content to prevent XSS
            content = self._escape_svelte_text(component.content)
            return f"{indent_str}{content}"
        
        # Map to Svelte element or component
        element = self._map_to_svelte_element(component.type)
        
        # Build attributes and bindings
        attrs = self._build_svelte_attributes(component)
        
        # Handle self-closing elements
        if not component.children and not component.content:
            return f"{indent_str}<{element}{attrs} />"
        
        # Handle elements with children
        markup_lines = [f"{indent_str}<{element}{attrs}>"]
        
        # Add content
        if component.content:
            escaped_content = self._escape_svelte_text(component.content)
            markup_lines.append(f"{indent_str}  {escaped_content}")
        
        # Add children
        for child in component.children:
            child_markup = await self._component_to_svelte(child, context, indent + 2)
            markup_lines.append(child_markup)
        
        markup_lines.append(f"{indent_str}</{element}>")
        
        return "\n".join(markup_lines)
    
    def _map_to_svelte_element(self, component_type: str) -> str:
        """Map component type to Svelte element or component"""
        # Check if it's a custom component
        if component_type in self.component_registry:
            return self.component_registry[component_type].name
        
        # Map to HTML elements
        element_map = {
            "container": "div",
            "text": "span",
            "heading": "h2",
            "paragraph": "p", 
            "link": "a",
            "button": "button",
            "image": "img",
            "list": "ul",
            "listitem": "li",
            "form": "form",
            "input": "input",
            "textarea": "textarea",
            "select": "select"
        }
        
        return element_map.get(component_type, "div")
    
    def _build_svelte_attributes(self, component: Component) -> str:
        """Build Svelte attributes and bindings"""
        attrs = {}
        
        # Class binding
        if component.class_name:
            attrs["class"] = component.class_name
        
        # Style binding
        if component.styles:
            style_string = self._styles_to_css_string(component.styles)
            if style_string:
                attrs["style"] = style_string
        
        # Event handlers
        if hasattr(component, "events"):
            for event, handler in component.events.items():
                attrs[f"on:{event}"] = f"{{{handler}}}"
        
        # Component-specific attributes
        if component.type == "link":
            attrs["href"] = component.properties.get("href", "#")
            if component.properties.get("target") == "_blank":
                attrs["target"] = "_blank"
                attrs["rel"] = "noopener noreferrer"
        
        elif component.type == "image":
            attrs["src"] = component.properties.get("src", "")
            attrs["alt"] = component.properties.get("alt", "")
            if component.properties.get("loading") == "lazy":
                attrs["loading"] = "lazy"
        
        elif component.type == "input":
            input_type = component.properties.get("type", "text")
            attrs["type"] = input_type
            attrs["name"] = component.properties.get("name", "")
            
            # Svelte two-way binding
            if component.properties.get("name"):
                attrs["bind:value"] = f"formData.{component.properties['name']}"
            
            if component.properties.get("placeholder"):
                attrs["placeholder"] = component.properties["placeholder"]
            if component.properties.get("required"):
                attrs["required"] = True
        
        # Build attributes string
        if not attrs:
            return ""
        
        attr_strings = []
        for key, value in attrs.items():
            if key.startswith("on:") or key.startswith("bind:"):
                # Svelte directive
                attr_strings.append(f'{key}={value}')
            elif isinstance(value, bool):
                if value:
                    attr_strings.append(key)
            elif key == "style":
                attr_strings.append(f'style="{value}"')
            else:
                # Regular attribute
                attr_strings.append(f'{key}="{self._escape_attribute(value)}"')
        
        return " " + " ".join(attr_strings) if attr_strings else ""
    
    def _escape_svelte_text(self, text: str) -> str:
        """
        Escape text for Svelte
        
        CLAUDE.md #7.2: Prevent XSS
        """
        if not text:
            return ""
        
        # Svelte automatically escapes text content
        # But we still escape for safety
        text = str(text)
        text = text.replace("{", "&#123;")
        text = text.replace("}", "&#125;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        
        return text
    
    def _escape_attribute(self, value: str) -> str:
        """Escape attribute value"""
        value = str(value)
        value = value.replace('"', '&quot;')
        value = value.replace("'", '&#39;')
        return value
    
    def _extract_components(self, context: ExportContext) -> List[SvelteComponentInfo]:
        """Extract reusable components"""
        components = []
        
        # Group components by type and properties
        component_groups = {}
        for comp in context.project.components:
            signature = (comp.type, tuple(sorted(comp.properties.items())))
            if signature not in component_groups:
                component_groups[signature] = []
            component_groups[signature].append(comp)
        
        # Extract components used multiple times
        for signature, group in component_groups.items():
            if len(group) >= 2:  # Used 2+ times
                comp_info = SvelteComponentInfo(
                    component=group[0],
                    name=self._generate_component_name(group[0]),
                    path=f"src/lib/components/{self._to_kebab_case(group[0].type)}",
                    props=self._extract_props(group),
                    has_reactive=self._component_has_reactive(group[0])
                )
                components.append(comp_info)
                
                # Register component
                self.component_registry[group[0].type] = comp_info
        
        return components
    
    def _generate_component_name(self, component: Component) -> str:
        """Generate Svelte component name (PascalCase)"""
        name = component.type.replace("_", " ").replace("-", " ")
        name = "".join(word.capitalize() for word in name.split())
        
        if not name[0].isupper():
            name = "Custom" + name
        
        return name
    
    def _to_kebab_case(self, text: str) -> str:
        """Convert to kebab-case"""
        import re
        text = re.sub('([a-z0-9])([A-Z])', r'\1-\2', text)
        return text.lower().replace('_', '-').replace(' ', '-')
    
    async def _generate_component_files(
        self,
        comp_info: SvelteComponentInfo,
        context: ExportContext
    ) -> Dict[str, str]:
        """Generate Svelte component file"""
        files = {}
        
        # Component Svelte file
        files[f"{comp_info.path}.svelte"] = await self._generate_component_svelte(comp_info, context)
        
        # Component test if needed
        if context.config.options.generate_tests:
            files[f"{comp_info.path}.test.js"] = self._generate_component_test(comp_info)
        
        return files
    
    async def _generate_component_svelte(
        self,
        comp_info: SvelteComponentInfo,
        context: ExportContext
    ) -> str:
        """Generate Svelte component file"""
        config = context.config.options
        
        # Build script section
        script_lang = "ts" if config.use_typescript else ""
        script_content = self._generate_component_script(comp_info, config)
        
        # Build markup section
        markup_content = await self._component_to_svelte(comp_info.component, context, 0)
        
        # Build style section
        style_content = self._generate_component_styles(comp_info)
        
        return f"""<script{(' lang="' + script_lang + '"' if script_lang else '')}>
{script_content}
</script>

{markup_content}

<style>
{style_content}
</style>
"""
    
    def _generate_component_script(self, comp_info: SvelteComponentInfo, config: Any) -> str:
        """Generate component script section"""
        script_lines = []
        
        # Import statements
        if comp_info.stores:
            script_lines.append("  import { writable } from 'svelte/store';")
        
        # Export props
        if comp_info.props:
            for prop in comp_info.props:
                prop_type = f": {prop['type']}" if config.use_typescript else ""
                default_value = prop.get('default', '""' if prop['type'] == 'string' else 'null')
                script_lines.append(f"  export let {prop['name']}{prop_type} = {default_value};")
        
        # Reactive statements
        if comp_info.has_reactive:
            script_lines.append("")
            script_lines.append("  // Reactive statements")
            script_lines.append("  $: processedData = processData(data);")
        
        # Component logic
        script_lines.append("")
        script_lines.append("  // Component logic")
        script_lines.append("  function handleClick() {")
        script_lines.append("    // Handle click event")
        script_lines.append("  }")
        
        return "\n".join(script_lines)
    
    def _generate_component_styles(self, comp_info: SvelteComponentInfo) -> str:
        """Generate component styles"""
        return f"""  /* Styles for {comp_info.name} */
  :global(.{self._to_kebab_case(comp_info.name)}) {{
    display: block;
  }}
  
  /* Component-specific styles */
"""
    
    def _generate_component_test(self, comp_info: SvelteComponentInfo) -> str:
        """Generate component test"""
        return f"""import {{ render, screen }} from '@testing-library/svelte';
import {{ expect, test }} from 'vitest';
import {comp_info.name} from './{self._to_kebab_case(comp_info.name)}.svelte';

test('renders {comp_info.name}', () => {{
  render({comp_info.name});
  // Add test assertions here
}});
"""
    
    def _generate_stores(self, context: ExportContext) -> Dict[str, str]:
        """Generate Svelte stores"""
        files = {}
        
        # Global store
        files["src/lib/stores/index.js"] = """import { writable } from 'svelte/store';

// Global application state
export const appState = writable({
  user: null,
  theme: 'light',
  notifications: []
});

// Project data store
export const projectData = writable({
  components: [],
  selectedComponent: null,
  isLoading: false
});

// Utility functions
export function updateProjectData(newData) {
  projectData.update(data => ({ ...data, ...newData }));
}

export function selectComponent(componentId) {
  projectData.update(data => ({ 
    ...data, 
    selectedComponent: componentId 
  }));
}
"""
        
        return files
    
    def _generate_utilities(self, context: ExportContext) -> Dict[str, str]:
        """Generate utility functions"""
        files = {}
        
        files["src/lib/utils/index.js"] = """// Utility functions

export function formatDate(date) {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }).format(new Date(date));
}

export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

export function generateId() {
  return Math.random().toString(36).substr(2, 9);
}
"""
        
        return files
    
    def _generate_api_routes(self, context: ExportContext) -> Dict[str, str]:
        """Generate SvelteKit API routes"""
        files = {}
        
        # API endpoint example
        files["src/routes/api/data/+server.js"] = """import { json } from '@sveltejs/kit';

/** @type {import('./$types').RequestHandler} */
export async function GET() {
  // Fetch data from database or external API
  const data = {
    message: 'Hello from SvelteKit API',
    timestamp: new Date().toISOString()
  };
  
  return json(data);
}

/** @type {import('./$types').RequestHandler} */
export async function POST({ request }) {
  const body = await request.json();
  
  // Process the data
  const result = {
    success: true,
    data: body
  };
  
  return json(result);
}
"""
        
        return files
    
    def _generate_tsconfig(self) -> str:
        """Generate TypeScript configuration"""
        return """{
  "extends": "./.svelte-kit/tsconfig.json",
  "compilerOptions": {
    "allowJs": true,
    "checkJs": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "sourceMap": true,
    "strict": true
  }
}
"""
    
    def _generate_app_types(self) -> str:
        """Generate app type definitions"""
        return """// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
  namespace App {
    // interface Error {}
    // interface Locals {}
    // interface PageData {}
    // interface Platform {}
  }
}

export {};
"""
    
    def _generate_playwright_config(self) -> str:
        """Generate Playwright test configuration"""
        return """import { defineConfig, devices } from '@playwright/test';

/**
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: 'html',
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:4173',

    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry'
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] }
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] }
    }
  ],

  /* Run your local dev server before starting the tests */
  webServer: {
    command: 'npm run build && npm run preview',
    port: 4173
  }
});
"""
    
    def _generate_readme(self, context: ExportContext) -> str:
        """Generate README.md"""
        return f"""# {context.project.name}

This project was exported from Canvas Editor and built with SvelteKit.

## Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```bash
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building

To create a production version of your app:

```bash
npm run build
```

You can preview the production build with `npm run preview`.

## Testing

Run the unit tests:

```bash
npm run test:unit
```

Run the integration tests:

```bash
npm run test:integration
```

## Deploying

To deploy your app, you may need to install an [adapter](https://kit.svelte.dev/docs/adapters) for your target environment.
"""
    
    def _generate_gitignore(self) -> str:
        """Generate .gitignore"""
        return """.DS_Store
node_modules
/build
/.svelte-kit
/package
.env
.env.*
!.env.example
vite.config.js.timestamp-*
vite.config.ts.timestamp-*
"""
    
    async def _generate_additional_pages(self, context: ExportContext) -> Dict[str, str]:
        """Generate additional pages"""
        files = {}
        
        # About page example
        files["src/routes/about/+page.svelte"] = """<svelte:head>
  <title>About</title>
  <meta name="description" content="About this app" />
</svelte:head>

<div class="text-column">
  <h1>About this app</h1>
  
  <p>
    This is a SvelteKit app generated from Canvas Editor.
  </p>
  
  <p>
    Visit <a href="https://kit.svelte.dev">kit.svelte.dev</a> to read the documentation
  </p>
</div>

<style>
  .text-column {
    max-width: 48rem;
    margin: 0 auto;
    padding: 2rem;
  }
</style>
"""
        
        return files
    
    async def _generate_tests(self, components: List[SvelteComponentInfo], context: ExportContext) -> Dict[str, str]:
        """Generate test files"""
        files = {}
        
        # Example integration test
        files["tests/test.js"] = """import { expect, test } from '@playwright/test';

test('index page has expected h1', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toBeVisible();
});
"""
        
        # Vitest setup
        files["src/lib/utils/test-utils.js"] = """import { render } from '@testing-library/svelte';

// Custom render function with common providers
export function renderComponent(component, options = {}) {
  return render(component, {
    ...options
  });
}
"""
        
        return files
    
    # Helper methods
    def _needs_stores(self, context: ExportContext) -> bool:
        """Check if stores are needed"""
        return any(c.properties.get("uses_state") for c in context.project.components)
    
    def _needs_api_routes(self, context: ExportContext) -> bool:
        """Check if API routes are needed"""
        return any(c.type in ["form", "api-consumer"] for c in context.project.components)
    
    def _needs_multiple_pages(self, context: ExportContext) -> bool:
        """Check if multiple pages are needed"""
        return len([c for c in context.project.components if not c.parent_id]) > 1
    
    def _component_has_reactive(self, component: Component) -> bool:
        """Check if component needs reactive statements"""
        return component.properties.get("reactive", False)
    
    def _get_root_components(self, context: ExportContext) -> List[Component]:
        """Get root components"""
        return [comp for comp in context.project.components if not comp.parent_id]
    
    def _extract_props(self, component_group: List[Component]) -> List[Dict[str, str]]:
        """Extract varying properties as props"""
        props = []
        
        # Find properties that vary across instances
        all_props = {}
        for comp in component_group:
            for key, value in comp.properties.items():
                if key not in all_props:
                    all_props[key] = set()
                all_props[key].add(str(value))
        
        # Create prop info for varying properties
        for key, values in all_props.items():
            if len(values) > 1:
                props.append({
                    "name": key,
                    "type": self._infer_type(values),
                    "default": list(values)[0]
                })
        
        return props
    
    def _infer_type(self, values: Set[str]) -> str:
        """Infer type from values"""
        try:
            numbers = [float(v) for v in values]
            return "number"
        except ValueError:
            pass
        
        if all(v.lower() in ["true", "false"] for v in values):
            return "boolean"
        
        return "string"
    
    def _styles_to_css_string(self, styles: Dict[str, Any]) -> str:
        """Convert styles dictionary to CSS string"""
        css_parts = []
        for key, value in styles.items():
            css_key = self._to_kebab_case(key)
            css_parts.append(f"{css_key}: {value}")
        return "; ".join(css_parts)