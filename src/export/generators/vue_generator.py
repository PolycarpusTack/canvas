"""
Vue Generator

CLAUDE.md Implementation:
- #1.4: Efficient Vue code generation
- #2.1.3: TypeScript support
- #9.1: Accessibility features
"""

import json
from typing import Dict, List, Optional, Any, Set
from pathlib import Path

from .base_generator import BaseGenerator
from ..export_context import ExportContext
from ..export_config import ExportOptions
from ...models.component_enhanced import Component


class VueGenerator(BaseGenerator):
    """
    Generate Vue 3 applications with Composition API
    
    CLAUDE.md #1.4: Modern Vue patterns
    """
    
    def __init__(self):
        super().__init__()
        self.component_registry: Dict[str, str] = {}
        self.imported_components: Set[str] = set()
    
    async def generate(
        self,
        context: ExportContext,
        options: ExportOptions
    ) -> Dict[str, str]:
        """Generate Vue application"""
        
        files = {}
        
        # Generate project structure
        if options.include_package_json:
            files["package.json"] = self._generate_package_json(
                context.project,
                options
            )
        
        # Generate main files
        files["src/main.js"] = self._generate_main_file(options)
        files["src/App.vue"] = self._generate_app_component(
            context.project,
            options
        )
        
        # Generate router if needed
        if self._needs_router(context.project):
            files["src/router/index.js"] = self._generate_router(
                context.project,
                options
            )
        
        # Generate components
        component_files = await self._generate_components(
            context.project.components,
            options
        )
        files.update(component_files)
        
        # Generate stores (Pinia)
        if options.state_management:
            store_files = self._generate_stores(context.project, options)
            files.update(store_files)
        
        # Generate styles
        files["src/assets/main.css"] = self._generate_styles(
            context.get_all_styles()
        )
        
        # Generate utilities
        if options.include_utilities:
            files["src/utils/index.js"] = self._generate_utilities()
        
        # Generate TypeScript files if enabled
        if options.typescript:
            files.update(self._generate_typescript_files(options))
        
        # Generate config files
        files["vite.config.js"] = self._generate_vite_config(options)
        files[".gitignore"] = self._generate_gitignore()
        
        if options.include_readme:
            files["README.md"] = self._generate_readme(
                context.project,
                options
            )
        
        return files
    
    def _generate_package_json(
        self,
        project: Any,
        options: ExportOptions
    ) -> str:
        """Generate package.json"""
        
        dependencies = {
            "vue": "^3.4.0",
            "vue-router": "^4.2.0",
        }
        
        if options.state_management:
            dependencies["pinia"] = "^2.1.0"
        
        dev_dependencies = {
            "@vitejs/plugin-vue": "^4.5.0",
            "vite": "^5.0.0"
        }
        
        if options.typescript:
            dev_dependencies.update({
                "typescript": "^5.3.0",
                "vue-tsc": "^1.8.0",
                "@vue/tsconfig": "^0.5.0"
            })
        
        if options.include_tests:
            dev_dependencies.update({
                "@vue/test-utils": "^2.4.0",
                "vitest": "^1.0.0",
                "jsdom": "^23.0.0"
            })
        
        package_json = {
            "name": project.name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "private": True,
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview"
            },
            "dependencies": dependencies,
            "devDependencies": dev_dependencies
        }
        
        if options.typescript:
            package_json["scripts"]["build"] = "vue-tsc && vite build"
        
        if options.include_tests:
            package_json["scripts"]["test"] = "vitest"
            package_json["scripts"]["test:ui"] = "vitest --ui"
        
        return json.dumps(package_json, indent=2)
    
    def _generate_main_file(self, options: ExportOptions) -> str:
        """Generate main.js entry point"""
        
        imports = [
            "import { createApp } from 'vue'",
            "import App from './App.vue'",
            "import './assets/main.css'"
        ]
        
        if self._needs_router:
            imports.append("import router from './router'")
        
        if options.state_management:
            imports.append("import { createPinia } from 'pinia'")
        
        setup = ["const app = createApp(App)"]
        
        if options.state_management:
            setup.append("const pinia = createPinia()")
            setup.append("app.use(pinia)")
        
        if self._needs_router:
            setup.append("app.use(router)")
        
        setup.append("app.mount('#app')")
        
        return "\n".join(imports) + "\n\n" + "\n".join(setup)
    
    def _generate_app_component(
        self,
        project: Any,
        options: ExportOptions
    ) -> str:
        """Generate App.vue component"""
        
        # Find root components
        root_components = [
            comp for comp in project.components
            if not comp.parent_id
        ]
        
        template_content = self._generate_component_template(
            root_components,
            options
        )
        
        script_setup = []
        
        if options.typescript:
            script_setup.append('<script setup lang="ts">')
        else:
            script_setup.append('<script setup>')
        
        # Import child components
        for comp in self._get_custom_components(root_components):
            comp_name = self._to_pascal_case(comp.name or comp.type)
            script_setup.append(
                f"import {comp_name} from './components/{comp_name}.vue'"
            )
        
        script_setup.append('</script>')
        
        style_content = """
<style scoped>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
}
</style>
"""
        
        return f"""<template>
  <div id="app">
{template_content}
  </div>
</template>

{chr(10).join(script_setup)}

{style_content}"""
    
    def _generate_component_template(
        self,
        components: List[Component],
        options: ExportOptions,
        indent: int = 2
    ) -> str:
        """Generate Vue template for components"""
        
        lines = []
        indent_str = "  " * indent
        
        for comp in components:
            lines.append(self._render_vue_component(comp, options, indent))
        
        return "\n".join(lines)
    
    def _render_vue_component(
        self,
        component: Component,
        options: ExportOptions,
        indent: int = 2
    ) -> str:
        """Render a single Vue component"""
        
        indent_str = "  " * indent
        
        # Map Canvas component types to Vue elements
        tag_map = {
            "container": "div",
            "text": "p",
            "heading": f"h{component.properties.get('level', 2)}",
            "button": "button",
            "input": "input",
            "image": "img",
            "link": "router-link" if self._needs_router else "a",
            "list": "ul",
            "listItem": "li",
            "form": "form",
            "label": "label",
            "textarea": "textarea",
            "select": "select"
        }
        
        # Check if it's a custom component
        if self._is_custom_component(component):
            tag = self._to_kebab_case(component.name or component.type)
            props = self._generate_vue_props(component.properties)
            
            if component.children:
                children_html = self._generate_component_template(
                    component.children,
                    options,
                    indent + 1
                )
                return f"""{indent_str}<{tag}{props}>
{children_html}
{indent_str}</{tag}>"""
            else:
                return f"{indent_str}<{tag}{props} />"
        
        # Regular HTML element
        tag = tag_map.get(component.type, "div")
        
        # Generate attributes
        attrs = []
        
        # Add Vue directives
        if component.properties.get("v-if"):
            attrs.append(f'v-if="{component.properties["v-if"]}"')
        
        if component.properties.get("v-for"):
            attrs.append(f'v-for="{component.properties["v-for"]}"')
            attrs.append(f':key="{component.properties.get("key", "index")}"')
        
        if component.properties.get("v-model"):
            attrs.append(f'v-model="{component.properties["v-model"]}"')
        
        # Add event handlers
        for prop, value in component.properties.items():
            if prop.startswith("on"):
                event = prop[2:].lower()
                attrs.append(f'@{event}="{value}"')
            elif prop.startswith("v-on:"):
                attrs.append(f'{prop}="{value}"')
        
        # Add regular attributes
        for prop, value in component.properties.items():
            if prop in ["id", "class", "title", "placeholder", "name", "type"]:
                attrs.append(f'{prop}="{value}"')
            elif prop == "href" and tag == "router-link":
                attrs.append(f':to="{value}"')
            elif prop == "src" and tag == "img":
                # Handle asset references
                if value.startswith("asset:"):
                    attrs.append(f':src="getAssetUrl(\'{value}\')"')
                else:
                    attrs.append(f'src="{value}"')
        
        # Add styles
        if hasattr(component, 'styles') and component.styles:
            style_str = self._styles_to_string(component.styles)
            attrs.append(f':style="{{{style_str}}}"')
        
        # Add accessibility attributes
        if component.type == "image" and component.properties.get("alt"):
            attrs.append(f'alt="{component.properties["alt"]}"')
        
        attrs_str = " " + " ".join(attrs) if attrs else ""
        
        # Self-closing tags
        if tag in ["img", "input", "br", "hr"]:
            return f"{indent_str}<{tag}{attrs_str} />"
        
        # Handle content and children
        if component.children:
            children_html = self._generate_component_template(
                component.children,
                options,
                indent + 1
            )
            return f"""{indent_str}<{tag}{attrs_str}>
{children_html}
{indent_str}</{tag}>"""
        elif component.content:
            # Handle Vue interpolation
            if "{{" in component.content:
                return f"{indent_str}<{tag}{attrs_str}>{component.content}</{tag}>"
            else:
                return f"{indent_str}<{tag}{attrs_str}>{self._escape_html(component.content)}</{tag}>"
        else:
            return f"{indent_str}<{tag}{attrs_str}></{tag}>"
    
    async def _generate_components(
        self,
        components: List[Component],
        options: ExportOptions
    ) -> Dict[str, str]:
        """Generate Vue component files"""
        
        files = {}
        generated_components = set()
        
        for comp in components:
            if self._should_extract_component(comp) and comp.name not in generated_components:
                comp_name = self._to_pascal_case(comp.name)
                file_path = f"src/components/{comp_name}.vue"
                files[file_path] = await self._generate_component_file(
                    comp,
                    options
                )
                generated_components.add(comp.name)
        
        return files
    
    async def _generate_component_file(
        self,
        component: Component,
        options: ExportOptions
    ) -> str:
        """Generate a single Vue component file"""
        
        template_content = self._render_vue_component(
            component,
            options,
            indent=1
        )
        
        # Generate script section
        script_lines = []
        
        if options.typescript:
            script_lines.append('<script setup lang="ts">')
        else:
            script_lines.append('<script setup>')
        
        # Add imports
        child_components = self._get_custom_components(component.children or [])
        for child in child_components:
            child_name = self._to_pascal_case(child.name or child.type)
            script_lines.append(
                f"import {child_name} from './{child_name}.vue'"
            )
        
        # Add props definition
        if component.properties:
            if options.typescript:
                script_lines.append("\ninterface Props {")
                for prop, value in component.properties.items():
                    if not prop.startswith("on") and not prop.startswith("v-"):
                        prop_type = self._get_typescript_type(value)
                        script_lines.append(f"  {prop}?: {prop_type}")
                script_lines.append("}")
                script_lines.append("\nconst props = defineProps<Props>()")
            else:
                props_def = []
                for prop in component.properties:
                    if not prop.startswith("on") and not prop.startswith("v-"):
                        props_def.append(f"'{prop}'")
                if props_def:
                    script_lines.append(f"\nconst props = defineProps([{', '.join(props_def)}])")
        
        # Add emits if needed
        emits = [
            prop[2:].lower() for prop in component.properties
            if prop.startswith("on")
        ]
        if emits:
            emit_list = ', '.join(f"'{e}'" for e in emits)
            script_lines.append(f"\nconst emit = defineEmits([{emit_list}])")
        
        # Add any component logic
        if options.state_management and self._needs_store_access(component):
            script_lines.append("\nimport { useMainStore } from '../stores/main'")
            script_lines.append("const store = useMainStore()")
        
        script_lines.append('</script>')
        
        # Generate style section
        style_lines = ['<style scoped>']
        
        # Extract component-specific styles
        if hasattr(component, 'styles') and component.styles:
            selector = f".{self._to_kebab_case(component.name or component.type)}"
            style_lines.append(f"{selector} {{")
            for prop, value in component.styles.items():
                css_prop = self._to_kebab_case(prop)
                style_lines.append(f"  {css_prop}: {value};")
            style_lines.append("}")
        
        style_lines.append('</style>')
        
        return f"""<template>
{template_content}
</template>

{chr(10).join(script_lines)}

{chr(10).join(style_lines)}"""
    
    def _generate_stores(
        self,
        project: Any,
        options: ExportOptions
    ) -> Dict[str, str]:
        """Generate Pinia stores"""
        
        files = {}
        
        # Main store
        store_content = """import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useMainStore = defineStore('main', () => {
  // State
  const projectData = ref({})
  const selectedComponent = ref(null)
  const isLoading = ref(false)
  
  // Getters
  const componentCount = computed(() => {
    return Object.keys(projectData.value.components || {}).length
  })
  
  // Actions
  function setProjectData(data) {
    projectData.value = data
  }
  
  function selectComponent(componentId) {
    selectedComponent.value = componentId
  }
  
  function setLoading(loading) {
    isLoading.value = loading
  }
  
  return {
    projectData,
    selectedComponent,
    isLoading,
    componentCount,
    setProjectData,
    selectComponent,
    setLoading
  }
})"""
        
        if options.typescript:
            # Add TypeScript version
            files["src/stores/main.ts"] = self._add_typescript_to_store(
                store_content
            )
        else:
            files["src/stores/main.js"] = store_content
        
        return files
    
    def _generate_router(
        self,
        project: Any,
        options: ExportOptions
    ) -> str:
        """Generate Vue Router configuration"""
        
        imports = [
            "import { createRouter, createWebHistory } from 'vue-router'"
        ]
        
        # Find pages/routes
        pages = self._extract_pages(project)
        
        for page in pages:
            page_name = self._to_pascal_case(page.name or "Page")
            imports.append(
                f"import {page_name} from '../views/{page_name}.vue'"
            )
        
        routes = []
        for i, page in enumerate(pages):
            page_name = self._to_pascal_case(page.name or "Page")
            path = "/" if i == 0 else f"/{self._to_kebab_case(page.name)}"
            routes.append(f"""  {{
    path: '{path}',
    name: '{page_name}',
    component: {page_name}
  }}""")
        
        imports_str = '\n'.join(imports)
        routes_str = ',\n'.join(routes)
        
        return f"""{imports_str}

const routes = [
{routes_str}
]

const router = createRouter({{
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
}})

export default router"""
    
    def _generate_vite_config(self, options: ExportOptions) -> str:
        """Generate Vite configuration"""
        
        plugins = ["vue()"]
        
        return f"""import {{ defineConfig }} from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({{
  plugins: [{', '.join(plugins)}],
  resolve: {{
    alias: {{
      '@': '/src'
    }}
  }}
}})"""
    
    def _generate_typescript_files(
        self,
        options: ExportOptions
    ) -> Dict[str, str]:
        """Generate TypeScript configuration files"""
        
        files = {}
        
        # tsconfig.json
        files["tsconfig.json"] = """{
  "extends": "@vue/tsconfig/tsconfig.web.json",
  "include": ["env.d.ts", "src/**/*", "src/**/*.vue"],
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}"""
        
        # env.d.ts
        files["env.d.ts"] = """/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}"""
        
        return files
    
    def _generate_vue_props(self, properties: Dict[str, Any]) -> str:
        """Generate Vue prop bindings"""
        props = []
        
        for key, value in properties.items():
            if key.startswith("v-") or key.startswith("on"):
                continue
            
            if isinstance(value, bool):
                if value:
                    props.append(f":{key}=\"true\"")
                else:
                    props.append(f":{key}=\"false\"")
            elif isinstance(value, (int, float)):
                props.append(f":{key}=\"{value}\"")
            elif isinstance(value, str) and "{{" in value:
                props.append(f":{key}=\"{value}\"")
            else:
                props.append(f'{key}="{value}"')
        
        return " " + " ".join(props) if props else ""
    
    def _is_custom_component(self, component: Component) -> bool:
        """Check if component should be extracted as custom component"""
        return (
            component.name and
            component.type not in ["text", "heading", "button", "input", "image", "link"]
        )
    
    def _should_extract_component(self, component: Component) -> bool:
        """Determine if component should be extracted to separate file"""
        return (
            self._is_custom_component(component) and
            len(component.children or []) > 2
        )
    
    def _get_custom_components(
        self,
        components: List[Component]
    ) -> List[Component]:
        """Get all custom components from a list"""
        custom = []
        
        for comp in components:
            if self._is_custom_component(comp):
                custom.append(comp)
            if comp.children:
                custom.extend(self._get_custom_components(comp.children))
        
        return custom
    
    def _needs_router(self, project: Any) -> bool:
        """Check if project needs Vue Router"""
        # Simple heuristic: multiple top-level containers might be pages
        root_containers = [
            comp for comp in project.components
            if not comp.parent_id and comp.type == "container"
        ]
        return len(root_containers) > 1
    
    def _needs_store_access(self, component: Component) -> bool:
        """Check if component needs store access"""
        # Check for state bindings in properties
        for value in component.properties.values():
            if isinstance(value, str) and "store." in value:
                return True
        return False
    
    def _extract_pages(self, project: Any) -> List[Component]:
        """Extract page components for routing"""
        # Find top-level containers that could be pages
        pages = [
            comp for comp in project.components
            if not comp.parent_id and comp.type == "container"
        ]
        
        # If no clear pages, create a single home page
        if not pages:
            pages = [Component(
                id="home",
                type="container",
                name="Home",
                children=project.components
            )]
        
        return pages
    
    def _add_typescript_to_store(self, js_content: str) -> str:
        """Convert JavaScript store to TypeScript"""
        # This is a simplified conversion
        ts_content = js_content.replace(
            "import { ref, computed } from 'vue'",
            "import { ref, computed, Ref, ComputedRef } from 'vue'"
        )
        
        # Add type annotations
        ts_content = ts_content.replace(
            "const projectData = ref({})",
            "const projectData: Ref<Record<string, any>> = ref({})"
        )
        
        ts_content = ts_content.replace(
            "const selectedComponent = ref(null)",
            "const selectedComponent: Ref<string | null> = ref(null)"
        )
        
        ts_content = ts_content.replace(
            "const isLoading = ref(false)",
            "const isLoading: Ref<boolean> = ref(false)"
        )
        
        return ts_content
    
    def _get_typescript_type(self, value: Any) -> str:
        """Get TypeScript type from value"""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "number"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "any[]"
        elif isinstance(value, dict):
            return "Record<string, any>"
        else:
            return "any"
    
    def _to_kebab_case(self, text: str) -> str:
        """Convert to kebab-case"""
        # Handle camelCase and PascalCase
        import re
        text = re.sub('([a-z0-9])([A-Z])', r'\1-\2', text)
        text = re.sub('([A-Z])([A-Z][a-z])', r'\1-\2', text)
        return text.lower().replace(' ', '-').replace('_', '-')
    
    def _to_pascal_case(self, text: str) -> str:
        """Convert to PascalCase"""
        words = text.replace('-', ' ').replace('_', ' ').split()
        return ''.join(word.capitalize() for word in words)
    
    def _styles_to_string(self, styles: Dict[str, Any]) -> str:
        """Convert styles dict to Vue style binding string"""
        style_parts = []
        
        for prop, value in styles.items():
            # Convert camelCase to kebab-case for CSS
            css_prop = self._to_kebab_case(prop)
            
            if isinstance(value, (int, float)):
                # Add 'px' to numeric values for certain properties
                if prop in ['width', 'height', 'fontSize', 'padding', 'margin']:
                    style_parts.append(f"'{css_prop}': '{value}px'")
                else:
                    style_parts.append(f"'{css_prop}': {value}")
            else:
                style_parts.append(f"'{css_prop}': '{value}'")
        
        return ", ".join(style_parts)