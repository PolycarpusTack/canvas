"""
Next.js Generator

CLAUDE.md Implementation:
- #3.4: Modern Next.js patterns with App Router
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
class NextJSComponentInfo:
    """Information about a Next.js component"""
    component: Component
    name: str
    path: str
    props: List[Dict[str, str]] = field(default_factory=list)
    is_page: bool = False
    is_server_component: bool = True
    has_client_features: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List['NextJSComponentInfo'] = field(default_factory=list)


class NextJSGenerator(BaseGenerator):
    """
    Generate modern Next.js application with App Router
    
    CLAUDE.md Implementation:
    - #3.4: Modern Next.js patterns (App Router, Server Components)
    - #1.2: DRY component generation
    """
    
    def __init__(self):
        super().__init__()
        self.component_registry: Dict[str, NextJSComponentInfo] = {}
        self.generated_pages: Set[str] = set()
        
    async def generate(self, context: ExportContext) -> Dict[str, str]:
        """Generate complete Next.js application"""
        files = {}
        config = context.config.options
        
        # Generate package.json
        files["package.json"] = self._generate_package_json(context)
        
        # Generate Next.js config files
        files["next.config.js"] = self._generate_next_config(context)
        
        # Generate TypeScript config if enabled
        if config.use_typescript:
            files["tsconfig.json"] = self._generate_tsconfig()
        
        # Generate Tailwind config if enabled
        if config.css_framework == "tailwind":
            files["tailwind.config.js"] = self._generate_tailwind_config()
            files["postcss.config.js"] = self._generate_postcss_config()
        
        # Generate app directory structure
        app_files = await self._generate_app_structure(context)
        files.update(app_files)
        
        # Generate pages from components
        page_files = await self._generate_pages(context)
        files.update(page_files)
        
        # Extract and generate reusable components
        components = self._extract_components(context)
        for comp_info in components:
            component_files = await self._generate_component_files(comp_info, context)
            files.update(component_files)
            
        # Generate API routes if needed
        if self._needs_api_routes(context):
            api_files = self._generate_api_routes(context)
            files.update(api_files)
            
        # Generate middleware if needed
        if self._needs_middleware(context):
            files["middleware.ts" if config.use_typescript else "middleware.js"] = self._generate_middleware(context)
            
        # Generate utilities and hooks
        utility_files = self._generate_utilities(context)
        files.update(utility_files)
        
        # Generate styles
        style_files = self._generate_styles(context)
        files.update(style_files)
        
        # Generate tests if requested
        if config.generate_tests:
            test_files = await self._generate_tests(components, context)
            files.update(test_files)
            
        # Generate README
        if config.generate_readme:
            files["README.md"] = self._generate_readme(context)
            
        # Generate .gitignore
        files[".gitignore"] = self._generate_gitignore()
        
        # Generate environment files
        files[".env.local"] = self._generate_env_file()
        files[".env.example"] = self._generate_env_example()
        
        return files
    
    def _generate_package_json(self, context: ExportContext) -> str:
        """Generate package.json with Next.js dependencies"""
        config = context.config.options
        
        package_data = {
            "name": context.project.name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "description": "Next.js app exported from Canvas Editor",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint",
                "type-check": "tsc --noEmit",
                "test": "jest",
                "test:watch": "jest --watch",
                "test:e2e": "playwright test"
            },
            "dependencies": {
                "next": "^14.0.0",
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            },
            "devDependencies": {
                "eslint": "^8.0.0",
                "eslint-config-next": "^14.0.0"
            }
        }
        
        # Add TypeScript support
        if config.use_typescript:
            package_data["devDependencies"].update({
                "typescript": "^5.0.0",
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0",
                "@types/node": "^20.0.0"
            })
        
        # Add Tailwind CSS
        if config.css_framework == "tailwind":
            package_data["devDependencies"].update({
                "tailwindcss": "^3.3.0",
                "postcss": "^8.4.24",
                "autoprefixer": "^10.4.14",
                "@tailwindcss/forms": "^0.5.2",
                "@tailwindcss/typography": "^0.5.7"
            })
        
        # Add state management
        if config.state_management == "zustand":
            package_data["dependencies"]["zustand"] = "^4.4.0"
        elif config.state_management == "redux":
            package_data["dependencies"].update({
                "@reduxjs/toolkit": "^1.9.0",
                "react-redux": "^8.1.0"
            })
        
        # Add UI library
        if config.ui_library == "shadcn":
            package_data["dependencies"].update({
                "@radix-ui/react-slot": "^1.0.2",
                "class-variance-authority": "^0.7.0",
                "clsx": "^2.0.0",
                "lucide-react": "^0.263.1",
                "tailwind-merge": "^1.14.0"
            })
        elif config.ui_library == "chakra":
            package_data["dependencies"].update({
                "@chakra-ui/react": "^2.8.0",
                "@emotion/react": "^11.11.0",
                "@emotion/styled": "^11.11.0",
                "framer-motion": "^10.16.0"
            })
        
        # Add testing dependencies
        if config.generate_tests:
            package_data["devDependencies"].update({
                "jest": "^29.5.0",
                "jest-environment-jsdom": "^29.5.0",
                "@testing-library/react": "^14.0.0",
                "@testing-library/jest-dom": "^5.16.0",
                "@testing-library/user-event": "^14.4.0",
                "@playwright/test": "^1.36.0"
            })
        
        # Add additional tools
        package_data["devDependencies"].update({
            "prettier": "^3.0.0",
            "@next/bundle-analyzer": "^14.0.0"
        })
        
        return json.dumps(package_data, indent=2)
    
    def _generate_next_config(self, context: ExportContext) -> str:
        """Generate next.config.js"""
        config = context.config.options
        
        config_options = []
        
        # Enable experimental features
        experimental = []
        if config.experimental_features:
            experimental.append("serverActions: true")
            experimental.append("serverComponentsExternalPackages: []")
        
        if experimental:
            config_options.append(f"experimental: {{ {', '.join(experimental)} }}")
        
        # Add image domains if needed
        config_options.append("images: { domains: ['localhost', 'example.com'] }")
        
        # Add bundle analyzer
        config_options.append("webpack: (config, { isServer }) => { return config; }")
        
        return f"""/** @type {{import('next').NextConfig}} */
const nextConfig = {{
  {',\n  '.join(config_options)}
}};

module.exports = nextConfig;
"""
    
    async def _generate_app_structure(self, context: ExportContext) -> Dict[str, str]:
        """Generate app directory structure"""
        files = {}
        config = context.config.options
        ext = "tsx" if config.use_typescript else "jsx"
        
        # Root layout
        files[f"app/layout.{ext}"] = self._generate_root_layout(context)
        
        # Root page
        files[f"app/page.{ext}"] = await self._generate_root_page(context)
        
        # Global styles
        files["app/globals.css"] = self._generate_global_css(context)
        
        # Loading UI
        files[f"app/loading.{ext}"] = self._generate_loading_ui()
        
        # Error UI
        files[f"app/error.{ext}"] = self._generate_error_ui()
        
        # Not Found UI
        files[f"app/not-found.{ext}"] = self._generate_not_found_ui()
        
        return files
    
    def _generate_root_layout(self, context: ExportContext) -> str:
        """Generate root layout component"""
        config = context.config.options
        
        imports = ["import './globals.css'"]
        
        if config.ui_library == "chakra":
            imports.append("import { ChakraProvider } from '@chakra-ui/react'")
        
        metadata_fields = [
            f"title: '{context.project.name}',",
            f"description: '{context.project.description or 'Generated by Canvas Editor'}'"
        ]
        
        children_wrapper = "children"
        if config.ui_library == "chakra":
            children_wrapper = "<ChakraProvider>{children}</ChakraProvider>"
        
        type_annotation = ""
        if config.use_typescript:
            type_annotation = ": { children: React.ReactNode }"
        
        return f"""{chr(10).join(imports)}

export const metadata = {{
  {chr(10).join(metadata_fields)}
}};

export default function RootLayout({{
  children,
}}{type_annotation}) {{
  return (
    <html lang="en">
      <body>
        {children_wrapper}
      </body>
    </html>
  );
}}
"""
    
    async def _generate_root_page(self, context: ExportContext) -> str:
        """Generate root page component"""
        config = context.config.options
        
        # Convert root components to Next.js JSX
        root_components = self._get_root_components(context)
        jsx_content = await self._components_to_jsx(root_components, context, 2)
        
        imports = []
        if self._needs_client_features(root_components):
            imports.append("'use client';")
        
        return f"""{chr(10).join(imports)}

export default function Home() {{
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-8">
          {context.project.name}
        </h1>
{jsx_content}
      </div>
    </main>
  );
}}
"""
    
    async def _components_to_jsx(
        self,
        components: List[Component],
        context: ExportContext,
        indent: int = 0
    ) -> str:
        """Convert components to Next.js JSX"""
        jsx_parts = []
        
        for component in components:
            jsx = await self._component_to_jsx(component, context, indent)
            jsx_parts.append(jsx)
            
        return "\n".join(jsx_parts)
    
    async def _component_to_jsx(
        self,
        component: Component,
        context: ExportContext,
        indent: int = 0
    ) -> str:
        """
        Convert single component to Next.js JSX
        
        CLAUDE.md #7.2: Escape user content
        """
        indent_str = "  " * indent
        
        # Handle text nodes
        if component.type == "text":
            content = self._escape_jsx_text(component.content)
            return f"{indent_str}{content}"
        
        # Map to Next.js element or component
        element = self._map_to_nextjs_element(component.type)
        
        # Build props
        props = self._build_jsx_props(component)
        
        # Handle self-closing elements
        if not component.children and not component.content:
            return f"{indent_str}<{element}{props} />"
        
        # Handle elements with children
        jsx_lines = [f"{indent_str}<{element}{props}>"]
        
        # Add content
        if component.content:
            escaped_content = self._escape_jsx_text(component.content)
            jsx_lines.append(f"{indent_str}  {escaped_content}")
        
        # Add children
        for child in component.children:
            child_jsx = await self._component_to_jsx(child, context, indent + 1)
            jsx_lines.append(child_jsx)
        
        jsx_lines.append(f"{indent_str}</{element}>")
        
        return "\n".join(jsx_lines)
    
    def _map_to_nextjs_element(self, component_type: str) -> str:
        """Map component type to Next.js element or component"""
        # Check if it's a custom component
        if component_type in self.component_registry:
            return self.component_registry[component_type].name
        
        # Map to HTML elements or Next.js components
        element_map = {
            "container": "div",
            "text": "span",
            "heading": "h2",
            "paragraph": "p",
            "link": "Link",  # Next.js Link component
            "button": "button",
            "image": "Image",  # Next.js Image component
            "list": "ul",
            "listitem": "li",
            "form": "form",
            "input": "input",
            "textarea": "textarea",
            "select": "select"
        }
        
        return element_map.get(component_type, "div")
    
    def _build_jsx_props(self, component: Component) -> str:
        """Build JSX props string for Next.js"""
        props = {}
        
        # Tailwind classes
        if component.class_name:
            props["className"] = component.class_name
        
        # Style
        if component.styles:
            style_obj = self._styles_to_jsx_object(component.styles)
            if style_obj:
                props["style"] = style_obj
        
        # Event handlers
        if hasattr(component, "events"):
            for event, handler in component.events.items():
                react_event = self._map_event_name(event)
                props[react_event] = f"{{{handler}}}"
        
        # Component-specific props
        if component.type == "link":
            props["href"] = component.properties.get("href", "/")
            if component.properties.get("target") == "_blank":
                props["target"] = "_blank"
                props["rel"] = "noopener noreferrer"
        
        elif component.type == "image":
            props["src"] = component.properties.get("src", "")
            props["alt"] = component.properties.get("alt", "")
            props["width"] = component.properties.get("width", 500)
            props["height"] = component.properties.get("height", 300)
            if component.properties.get("priority"):
                props["priority"] = True
        
        elif component.type == "input":
            props["type"] = component.properties.get("type", "text")
            props["name"] = component.properties.get("name", "")
            
            if component.properties.get("placeholder"):
                props["placeholder"] = component.properties["placeholder"]
            if component.properties.get("required"):
                props["required"] = True
        
        # Build props string
        if not props:
            return ""
        
        prop_strings = []
        for key, value in props.items():
            if isinstance(value, bool):
                if value:
                    prop_strings.append(key)
            elif isinstance(value, str):
                if value.startswith("{") and value.endswith("}"):
                    prop_strings.append(f"{key}={value}")
                else:
                    prop_strings.append(f'{key}="{self._escape_jsx_attribute(value)}"')
            else:
                prop_strings.append(f"{key}={{{json.dumps(value)}}}")
        
        return " " + " ".join(prop_strings) if prop_strings else ""
    
    def _escape_jsx_text(self, text: str) -> str:
        """
        Escape text for JSX
        
        CLAUDE.md #7.2: Prevent XSS
        """
        if not text:
            return ""
        
        text = str(text)
        text = text.replace("{", "&#123;")
        text = text.replace("}", "&#125;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        
        return text
    
    def _escape_jsx_attribute(self, value: str) -> str:
        """Escape attribute value for JSX"""
        value = value.replace('"', '&quot;')
        value = value.replace("'", '&#39;')
        return value
    
    async def _generate_pages(self, context: ExportContext) -> Dict[str, str]:
        """Generate additional pages"""
        files = {}
        config = context.config.options
        ext = "tsx" if config.use_typescript else "jsx"
        
        # Generate pages for top-level containers
        page_components = self._identify_page_components(context)
        
        for page_comp in page_components:
            page_path = self._generate_page_path(page_comp)
            files[f"app/{page_path}/page.{ext}"] = await self._generate_page_component(page_comp, context)
            
            # Generate metadata
            if self._needs_metadata(page_comp):
                files[f"app/{page_path}/layout.{ext}"] = self._generate_page_layout(page_comp, context)
        
        return files
    
    def _extract_components(self, context: ExportContext) -> List[NextJSComponentInfo]:
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
                comp_info = NextJSComponentInfo(
                    component=group[0],
                    name=self._generate_component_name(group[0]),
                    path=f"components/{self._to_kebab_case(group[0].type)}",
                    props=self._extract_props(group),
                    has_client_features=self._component_needs_client(group[0])
                )
                components.append(comp_info)
                
                # Register component
                self.component_registry[group[0].type] = comp_info
        
        return components
    
    def _generate_component_name(self, component: Component) -> str:
        """Generate Next.js component name (PascalCase)"""
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
        comp_info: NextJSComponentInfo,
        context: ExportContext
    ) -> Dict[str, str]:
        """Generate component files"""
        files = {}
        config = context.config.options
        ext = "tsx" if config.use_typescript else "jsx"
        
        # Component file
        files[f"{comp_info.path}.{ext}"] = await self._generate_component_tsx(comp_info, context)
        
        # Component test
        if config.generate_tests:
            files[f"{comp_info.path}.test.{ext}"] = self._generate_component_test(comp_info)
        
        # Component stories (Storybook)
        if config.include_storybook:
            files[f"{comp_info.path}.stories.{ext}"] = self._generate_component_story(comp_info)
        
        return files
    
    async def _generate_component_tsx(
        self,
        comp_info: NextJSComponentInfo,
        context: ExportContext
    ) -> str:
        """Generate Next.js component"""
        config = context.config.options
        
        # Build imports
        imports = []
        if comp_info.has_client_features:
            imports.append("'use client';")
        
        imports.extend([
            "import React from 'react';",
        ])
        
        # Add Next.js imports if needed
        if self._component_uses_image(comp_info.component):
            imports.append("import Image from 'next/image';")
        if self._component_uses_link(comp_info.component):
            imports.append("import Link from 'next/link';")
        
        # Generate types
        types = ""
        if config.use_typescript:
            types = self._generate_component_types(comp_info)
        
        # Generate component
        jsx_content = await self._component_to_jsx(comp_info.component, context, 1)
        
        props_type = f": {comp_info.name}Props" if config.use_typescript else ""
        
        return f"""{chr(10).join(imports)}

{types}

export default function {comp_info.name}({self._generate_props_destructuring(comp_info)}{props_type}) {{
  return (
{jsx_content}
  );
}}
"""
    
    def _generate_component_types(self, comp_info: NextJSComponentInfo) -> str:
        """Generate TypeScript types for component"""
        if not comp_info.props:
            return f"interface {comp_info.name}Props {{}}"
        
        prop_types = []
        for prop in comp_info.props:
            optional = "?" if prop.get("optional", True) else ""
            prop_types.append(f"  {prop['name']}{optional}: {prop['type']};")
        
        return f"""interface {comp_info.name}Props {{
{chr(10).join(prop_types)}
}}
"""
    
    def _generate_component_test(self, comp_info: NextJSComponentInfo) -> str:
        """Generate component test"""
        return f"""import {{ render, screen }} from '@testing-library/react';
import {comp_info.name} from './{self._to_kebab_case(comp_info.name)}';

describe('{comp_info.name}', () => {{
  it('renders without crashing', () => {{
    render(<{comp_info.name} />);
  }});
  
  it('displays content correctly', () => {{
    render(<{comp_info.name} />);
    // Add specific test assertions here
  }});
}});
"""
    
    def _generate_api_routes(self, context: ExportContext) -> Dict[str, str]:
        """Generate Next.js API routes"""
        files = {}
        config = context.config.options
        ext = "ts" if config.use_typescript else "js"
        
        # Example API route
        files[f"app/api/data/route.{ext}"] = self._generate_api_route()
        
        return files
    
    def _generate_api_route(self) -> str:
        """Generate API route handler"""
        return """import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Fetch data from database or external API
    const data = {
      message: 'Hello from Next.js API',
      timestamp: new Date().toISOString()
    };
    
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Process the data
    const result = {
      success: true,
      data: body
    };
    
    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json(
      { error: 'Bad Request' },
      { status: 400 }
    );
  }
}
"""
    
    def _generate_middleware(self, context: ExportContext) -> str:
        """Generate Next.js middleware"""
        return """import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Add authentication, logging, or other middleware logic here
  
  // Example: Add security headers
  const response = NextResponse.next();
  
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'origin-when-cross-origin');
  
  return response;
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
"""
    
    def _generate_utilities(self, context: ExportContext) -> Dict[str, str]:
        """Generate utility functions and hooks"""
        files = {}
        config = context.config.options
        ext = "ts" if config.use_typescript else "js"
        
        # Utility functions
        files[f"lib/utils.{ext}"] = """import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }).format(date);
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}
"""
        
        # Custom hooks
        files[f"hooks/use-local-storage.{ext}"] = """'use client';

import { useState, useEffect } from 'react';

export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T) => void] {
  const [storedValue, setStoredValue] = useState<T>(initialValue);

  useEffect(() => {
    try {
      const item = window.localStorage.getItem(key);
      if (item) {
        setStoredValue(JSON.parse(item));
      }
    } catch (error) {
      console.error(error);
    }
  }, [key]);

  const setValue = (value: T) => {
    try {
      setStoredValue(value);
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(error);
    }
  };

  return [storedValue, setValue];
}
"""
        
        return files
    
    def _generate_styles(self, context: ExportContext) -> Dict[str, str]:
        """Generate style files"""
        files = {}
        
        # Global CSS with Tailwind
        files["app/globals.css"] = self._generate_global_css(context)
        
        return files
    
    def _generate_global_css(self, context: ExportContext) -> str:
        """Generate global CSS"""
        config = context.config.options
        
        if config.css_framework == "tailwind":
            return """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96%;
    --secondary-foreground: 222.2 84% 4.9%;
    --muted: 210 40% 96%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96%;
    --accent-foreground: 222.2 84% 4.9%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
"""
        else:
            return """/* Global styles */
* {
  box-sizing: border-box;
  padding: 0;
  margin: 0;
}

html,
body {
  max-width: 100vw;
  overflow-x: hidden;
}

body {
  color: rgb(var(--foreground-rgb));
  background: linear-gradient(
      to bottom,
      transparent,
      rgb(var(--background-end-rgb))
    )
    rgb(var(--background-start-rgb));
}

a {
  color: inherit;
  text-decoration: none;
}

@media (prefers-color-scheme: dark) {
  html {
    color-scheme: dark;
  }
}
"""
    
    def _generate_tailwind_config(self) -> str:
        """Generate Tailwind configuration"""
        return """/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
"""
    
    def _generate_postcss_config(self) -> str:
        """Generate PostCSS configuration"""
        return """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"""
    
    def _generate_tsconfig(self) -> str:
        """Generate TypeScript configuration"""
        return """{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
"""
    
    def _generate_loading_ui(self) -> str:
        """Generate loading UI component"""
        return """export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
    </div>
  );
}
"""
    
    def _generate_error_ui(self) -> str:
        """Generate error UI component"""
        return """'use client';

import { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h2 className="text-2xl font-bold mb-4">Something went wrong!</h2>
      <button
        onClick={reset}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Try again
      </button>
    </div>
  );
}
"""
    
    def _generate_not_found_ui(self) -> str:
        """Generate not found UI component"""
        return """import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h2 className="text-2xl font-bold mb-4">Not Found</h2>
      <p className="mb-4">Could not find requested resource</p>
      <Link 
        href="/"
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Return Home
      </Link>
    </div>
  );
}
"""
    
    def _generate_readme(self, context: ExportContext) -> str:
        """Generate README.md"""
        return f"""# {context.project.name}

This is a [Next.js](https://nextjs.org/) project exported from Canvas Editor.

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Features

- ⚡️ Next.js 14 with App Router
- 🎨 Tailwind CSS for styling
- 📱 Responsive design
- 🔧 TypeScript support
- 🧪 Testing with Jest and Playwright
- 📝 ESLint and Prettier for code quality

## Project Structure

```
├── app/                   # App router pages and layouts
├── components/            # Reusable components
├── lib/                   # Utility functions
├── hooks/                 # Custom React hooks
├── public/                # Static assets
└── types/                 # TypeScript type definitions
```

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/deployment) for more details.
"""
    
    def _generate_gitignore(self) -> str:
        """Generate .gitignore"""
        return """# See https://help.github.com/articles/ignoring-files/ for more about ignoring files.

# dependencies
/node_modules
/.pnp
.pnp.js
.yarn/install-state.gz

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# local env files
.env*.local

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts
"""
    
    def _generate_env_file(self) -> str:
        """Generate .env.local"""
        return """# Local environment variables
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:3000/api

# Database (if using)
# DATABASE_URL=""

# Auth (if using)
# NEXTAUTH_SECRET=""
# NEXTAUTH_URL=""
"""
    
    def _generate_env_example(self) -> str:
        """Generate .env.example"""
        return """# Environment variables example
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:3000/api

# Add your environment variables here
"""
    
    # Helper methods
    def _needs_api_routes(self, context: ExportContext) -> bool:
        """Check if API routes are needed"""
        return any(c.type in ["form", "api-consumer"] for c in context.project.components)
    
    def _needs_middleware(self, context: ExportContext) -> bool:
        """Check if middleware is needed"""
        return any(c.properties.get("requires_auth") for c in context.project.components)
    
    def _needs_client_features(self, components: List[Component]) -> bool:
        """Check if components need client-side features"""
        return any(self._component_needs_client(comp) for comp in components)
    
    def _component_needs_client(self, component: Component) -> bool:
        """Check if component needs 'use client' directive"""
        client_types = ["input", "button", "form"]
        return component.type in client_types or bool(getattr(component, "events", None))
    
    def _component_uses_image(self, component: Component) -> bool:
        """Check if component uses Next.js Image"""
        return component.type == "image"
    
    def _component_uses_link(self, component: Component) -> bool:
        """Check if component uses Next.js Link"""
        return component.type == "link"
    
    def _get_root_components(self, context: ExportContext) -> List[Component]:
        """Get root components"""
        return [comp for comp in context.project.components if not comp.parent_id]
    
    def _identify_page_components(self, context: ExportContext) -> List[Component]:
        """Identify components that should become pages"""
        # Logic to identify page-worthy components
        return [comp for comp in context.project.components 
                if not comp.parent_id and comp.type == "container"]
    
    def _generate_page_path(self, component: Component) -> str:
        """Generate page path from component"""
        return self._to_kebab_case(component.name or component.type)
    
    async def _generate_page_component(self, component: Component, context: ExportContext) -> str:
        """Generate a page component"""
        jsx_content = await self._component_to_jsx(component, context, 1)
        
        return f"""export default function {self._generate_component_name(component)}() {{
  return (
{jsx_content}
  );
}}
"""
    
    def _generate_page_layout(self, component: Component, context: ExportContext) -> str:
        """Generate page layout with metadata"""
        return f"""export const metadata = {{
  title: '{component.name or component.type}',
  description: 'Generated by Canvas Editor'
}};

export default function Layout({{ children }}: {{ children: React.ReactNode }}) {{
  return children;
}}
"""
    
    def _needs_metadata(self, component: Component) -> bool:
        """Check if component needs custom metadata"""
        return bool(component.name)
    
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
                    "type": self._infer_typescript_type(values),
                    "optional": True
                })
        
        return props
    
    def _infer_typescript_type(self, values: Set[str]) -> str:
        """Infer TypeScript type from values"""
        try:
            numbers = [float(v) for v in values]
            return "number"
        except ValueError:
            pass
        
        if all(v.lower() in ["true", "false"] for v in values):
            return "boolean"
        
        return "string"
    
    def _generate_props_destructuring(self, comp_info: NextJSComponentInfo) -> str:
        """Generate props destructuring"""
        if not comp_info.props:
            return ""
        prop_names = [prop["name"] for prop in comp_info.props]
        return "{ " + ", ".join(prop_names) + " }"
    
    def _styles_to_jsx_object(self, styles: Dict[str, Any]) -> Dict[str, Any]:
        """Convert styles to JSX style object"""
        jsx_styles = {}
        for key, value in styles.items():
            # Convert kebab-case to camelCase
            camel_key = self._kebab_to_camel(key)
            jsx_styles[camel_key] = value
        return jsx_styles
    
    def _kebab_to_camel(self, name: str) -> str:
        """Convert kebab-case to camelCase"""
        parts = name.split("-")
        return parts[0] + "".join(part.capitalize() for part in parts[1:])
    
    def _map_event_name(self, event: str) -> str:
        """Map event name to React convention"""
        event_map = {
            "click": "onClick",
            "change": "onChange",
            "submit": "onSubmit",
            "focus": "onFocus",
            "blur": "onBlur"
        }
        return event_map.get(event, f"on{event.capitalize()}")
    
    def _generate_component_story(self, comp_info: NextJSComponentInfo) -> str:
        """Generate Storybook story"""
        return f"""import type {{ Meta, StoryObj }} from '@storybook/react';
import {comp_info.name} from './{self._to_kebab_case(comp_info.name)}';

const meta: Meta<typeof {comp_info.name}> = {{
  title: 'Components/{comp_info.name}',
  component: {comp_info.name},
  parameters: {{
    layout: 'centered',
  }},
  tags: ['autodocs'],
}};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {{
  args: {{
    // Add default props here
  }},
}};
"""
    
    async def _generate_tests(self, components: List[NextJSComponentInfo], context: ExportContext) -> Dict[str, str]:
        """Generate test files"""
        files = {}
        
        # Jest configuration
        files["jest.config.js"] = """const nextJest = require('next/jest');

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: './',
});

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jsdom',
};

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig);
"""
        
        # Jest setup
        files["jest.setup.js"] = """import '@testing-library/jest-dom';"""
        
        # Playwright configuration
        files["playwright.config.ts"] = """import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    port: 3000,
  },
});
"""
        
        # Example E2E test
        files["e2e/example.spec.ts"] = """import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/Canvas Export/);
});

test('navigation works', async ({ page }) => {
  await page.goto('/');
  // Add more test assertions here
});
"""
        
        return files