"""
React Generator

CLAUDE.md Implementation:
- #3.4: Modern React best practices
- #1.2: DRY component generation
- #4.1: Strong typing with TypeScript
- #7.2: XSS prevention in JSX
"""

import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
import json
import re

from ..export_context import ExportContext
from ..export_config import ExportConfig, ComponentStyle
from .base_generator import BaseGenerator
from ...models.component_enhanced import Component

logger = logging.getLogger(__name__)


@dataclass
class PropInfo:
    """Information about a component prop"""
    name: str
    type: str
    optional: bool = True
    default: Optional[Any] = None


@dataclass 
class ComponentInfo:
    """Information about a component for generation"""
    component: Component
    name: str
    path: str
    props: List[PropInfo] = field(default_factory=list)
    state_vars: List[Dict[str, Any]] = field(default_factory=list)
    has_state: bool = False
    has_effects: bool = False
    has_context: bool = False
    children: List['ComponentInfo'] = field(default_factory=list)


class ReactGenerator(BaseGenerator):
    """
    Generate modern React application with hooks and TypeScript support
    
    CLAUDE.md Implementation:
    - #3.4: Modern React best practices
    - #1.2: DRY component generation
    """
    
    def __init__(self):
        super().__init__()
        self.component_imports: Set[str] = set()
        self.generated_components: Dict[str, str] = {}
        self.component_registry: Dict[str, ComponentInfo] = {}
    
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
        
        # Generate prettier config
        if config.include_prettier:
            files[".prettierrc"] = self._generate_prettier_config()
        
        # Generate app structure
        ext = "tsx" if config.use_typescript else "jsx"
        
        # Entry point
        files[f"src/index.{ext}"] = self._generate_index(context)
        
        # Main App component
        files[f"src/App.{ext}"] = await self._generate_app_component(context)
        
        # Extract and generate reusable components
        components = self._extract_components(context)
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
        
        # Generate services/API layer
        if self._needs_api_layer(context):
            api_files = await self._generate_api_layer(context)
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
        
        # Generate build configuration
        if config.build_tool == "webpack":
            files["webpack.config.js"] = self._generate_webpack_config(context)
        elif config.build_tool == "vite":
            files["vite.config.js"] = self._generate_vite_config(context)
        
        return files
    
    def _generate_package_json(self, context: ExportContext) -> str:
        """Generate package.json with dependencies"""
        config = context.config.options
        
        package_data = {
            "name": context.project.name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "description": f"React app exported from Canvas Editor",
            "private": True,
            "scripts": {
                "start": "vite" if config.build_tool == "vite" else "webpack serve --mode development",
                "build": "vite build" if config.build_tool == "vite" else "webpack --mode production",
                "test": "jest",
                "lint": "eslint src --ext .js,.jsx,.ts,.tsx",
                "format": "prettier --write src/**/*.{js,jsx,ts,tsx,css,md}"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            },
            "devDependencies": {}
        }
        
        # Add TypeScript dependencies
        if config.use_typescript:
            package_data["devDependencies"].update({
                "typescript": "^5.0.0",
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0"
            })
        
        # Add routing
        if config.routing_library == "react-router":
            package_data["dependencies"]["react-router-dom"] = "^6.10.0"
        
        # Add state management
        if config.state_management == "redux":
            package_data["dependencies"].update({
                "redux": "^4.2.0",
                "@reduxjs/toolkit": "^1.9.0",
                "react-redux": "^8.0.0"
            })
        elif config.state_management == "mobx":
            package_data["dependencies"].update({
                "mobx": "^6.8.0",
                "mobx-react-lite": "^3.4.0"
            })
        
        # Add build tools
        if config.build_tool == "vite":
            package_data["devDependencies"].update({
                "vite": "^4.3.0",
                "@vitejs/plugin-react": "^4.0.0"
            })
        else:  # webpack
            package_data["devDependencies"].update({
                "webpack": "^5.80.0",
                "webpack-cli": "^5.0.0",
                "webpack-dev-server": "^4.13.0",
                "babel-loader": "^9.1.0",
                "@babel/core": "^7.21.0",
                "@babel/preset-env": "^7.21.0",
                "@babel/preset-react": "^7.18.0",
                "css-loader": "^6.7.0",
                "style-loader": "^3.3.0"
            })
        
        # Add testing
        if config.generate_tests:
            package_data["devDependencies"].update({
                "jest": "^29.5.0",
                "@testing-library/react": "^14.0.0",
                "@testing-library/jest-dom": "^5.16.0",
                "@testing-library/user-event": "^14.4.0"
            })
        
        # Add linting
        if config.include_eslint:
            package_data["devDependencies"].update({
                "eslint": "^8.40.0",
                "eslint-plugin-react": "^7.32.0",
                "eslint-plugin-react-hooks": "^4.6.0"
            })
        
        # Add prettier
        if config.include_prettier:
            package_data["devDependencies"]["prettier"] = "^2.8.0"
        
        return json.dumps(package_data, indent=2)
    
    def _generate_index(self, context: ExportContext) -> str:
        """Generate index.tsx/jsx entry point"""
        config = context.config.options
        
        imports = [
            "import React from 'react';",
            "import ReactDOM from 'react-dom/client';",
            "import './index.css';",
            "import App from './App';"
        ]
        
        # Add provider imports
        if config.state_management == "redux":
            imports.append("import { Provider } from 'react-redux';")
            imports.append("import { store } from './store';")
        elif config.state_management == "mobx":
            imports.append("import { StoreProvider } from './stores';")
        
        # Add router import
        if config.routing_library == "react-router":
            imports.append("import { BrowserRouter } from 'react-router-dom';")
        
        # Build render tree
        app_element = "App"
        
        # Wrap with router
        if config.routing_library == "react-router":
            app_element = f"BrowserRouter>\n    <{app_element} />\n  </BrowserRouter"
        
        # Wrap with state provider
        if config.state_management == "redux":
            app_element = f"Provider store={{store}}>\n    <{app_element} />\n  </Provider"
        elif config.state_management == "mobx":
            app_element = f"StoreProvider>\n    <{app_element} />\n  </StoreProvider"
        
        return f"""{chr(10).join(imports)}

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <{app_element} />
  </React.StrictMode>
);"""
    
    async def _generate_app_component(self, context: ExportContext) -> str:
        """Generate main App component"""
        config = context.config.options
        
        # Analyze component tree to determine structure
        root_components = self._get_root_components(context)
        
        # Build imports
        imports = self._collect_imports(root_components, config)
        
        # Generate component
        if config.component_style == ComponentStyle.FUNCTIONAL:
            component = await self._generate_functional_app(root_components, context)
        else:
            component = await self._generate_class_app(root_components, context)
        
        # Build complete file
        type_imports = ""
        if config.use_typescript:
            type_imports = "import type { FC } from 'react';\n"
        
        return f"""{type_imports}{chr(10).join(imports)}
import './App.css';

{component}

export default App;"""
    
    async def _generate_functional_app(
        self,
        root_components: List[Component],
        context: ExportContext
    ) -> str:
        """Generate functional App component"""
        config = context.config.options
        
        # Determine hooks needed
        hooks = []
        
        # Generate JSX
        jsx_content = await self._components_to_jsx(root_components, context, indent=2)
        
        # Build component
        type_annotation = ": FC" if config.use_typescript else ""
        
        return f"""const App{type_annotation} = () => {{
{self._indent(hooks, 1)}
  return (
    <div className="app">
{jsx_content}
    </div>
  );
}};"""
    
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
        imports = self._collect_component_imports(comp_info, config)
        
        # Generate types if TypeScript
        types = ""
        if config.use_typescript:
            types = self._generate_types(comp_info)
        
        # Generate component
        if config.component_style == ComponentStyle.FUNCTIONAL:
            component = await self._generate_functional_component(comp_info, config)
        else:
            component = await self._generate_class_component(comp_info, config)
        
        # Generate styles
        styles = self._generate_component_styles(comp_info)
        
        # Build complete file
        return f"""{chr(10).join(imports)}

{types}

{component}

{styles}

export default {comp_info.name};"""
    
    async def _generate_functional_component(
        self,
        comp_info: ComponentInfo,
        config: ExportConfig
    ) -> str:
        """Generate modern functional component with hooks"""
        # Determine needed hooks
        hooks = []
        
        if comp_info.has_state:
            hooks.extend(self._generate_state_hooks(comp_info))
        
        if comp_info.has_effects:
            hooks.extend(self._generate_effect_hooks(comp_info))
        
        if comp_info.has_context:
            hooks.extend(self._generate_context_hooks(comp_info))
        
        # Generate props interface for TypeScript
        props_type = ""
        if config.use_typescript:
            props_type = f": {comp_info.name}Props"
        
        # Generate JSX
        jsx_content = await self._component_to_jsx(comp_info.component, indent=2)
        
        # Build component
        props_destructure = self._generate_props_destructuring(comp_info)
        
        return f"""export const {comp_info.name} = ({{{props_destructure}}}{props_type}) => {{
{self._indent(hooks, 1)}

{self._generate_component_logic(comp_info, indent=1)}

  return (
{jsx_content}
  );
}};"""
    
    async def _component_to_jsx(
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
            if component.content_type == "html":
                # Dangerous HTML - needs sanitization
                jsx_lines.append(f"{indent_str}  {{/* dangerouslySetInnerHTML={{__html: sanitize(`{component.content}`)}} */}}")
                jsx_lines.append(f"{indent_str}  {self._escape_jsx_text(component.content)}")
            else:
                jsx_lines.append(f"{indent_str}  {self._escape_jsx_text(component.content)}")
        
        # Add children
        for child in component.children:
            child_jsx = await self._component_to_jsx(child, indent + 1)
            jsx_lines.append(child_jsx)
        
        jsx_lines.append(f"{indent_str}</{element}>")
        
        return "\n".join(jsx_lines)
    
    def _map_to_react_element(self, component_type: str) -> str:
        """Map component type to React element"""
        # Check if it's a custom component
        if component_type in self.generated_components:
            return self.generated_components[component_type]
        
        # Map to HTML elements
        element_map = {
            "container": "div",
            "text": "span",
            "heading": "h2",  # Default to h2
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
    
    def _build_jsx_props(self, component: Component) -> str:
        """Build JSX props string"""
        props = {}
        
        # Class name
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
            props["href"] = component.properties.get("href", "#")
            if component.properties.get("target") == "_blank":
                props["target"] = "_blank"
                props["rel"] = "noopener noreferrer"
        
        elif component.type == "image":
            props["src"] = component.properties.get("src", "")
            props["alt"] = component.properties.get("alt", "")
            if component.properties.get("loading") == "lazy":
                props["loading"] = "lazy"
        
        elif component.type == "input":
            props["type"] = component.properties.get("type", "text")
            props["name"] = component.properties.get("name", "")
            props["value"] = f"{{formData.{component.properties.get('name', '')}}}"
            props["onChange"] = f"{{handleInputChange}}"
            
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
                    # JavaScript expression
                    prop_strings.append(f"{key}={value}")
                else:
                    # String literal
                    prop_strings.append(f'{key}="{self._escape_jsx_attribute(value)}"')
            else:
                # Object or other
                prop_strings.append(f"{key}={{{json.dumps(value)}}}")
        
        return " " + " ".join(prop_strings) if prop_strings else ""
    
    def _escape_jsx_text(self, text: str) -> str:
        """
        Escape text for JSX
        
        CLAUDE.md #7.2: Prevent XSS
        """
        if not text:
            return ""
        
        # Escape special JSX characters
        text = str(text)
        text = text.replace("{", "&#123;")
        text = text.replace("}", "&#125;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        
        return text
    
    def _escape_jsx_attribute(self, value: str) -> str:
        """Escape attribute value for JSX"""
        # Escape quotes
        value = value.replace('"', '&quot;')
        value = value.replace("'", '&#39;')
        return value
    
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
            type_str = self._ts_type(prop.type)
            props_fields.append(f"  {prop.name}{optional}: {type_str};")
        
        if props_fields:
            types.append(f"""export interface {comp_info.name}Props {{
{chr(10).join(props_fields)}
}}""")
        
        # State interface if needed
        if comp_info.has_state:
            state_fields = []
            for state in comp_info.state_vars:
                state_fields.append(f"  {state.name}: {self._ts_type(state.type)};")
            
            types.append(f"""interface {comp_info.name}State {{
{chr(10).join(state_fields)}
}}""")
        
        return "\n\n".join(types)
    
    def _ts_type(self, prop_type: str) -> str:
        """Convert property type to TypeScript type"""
        type_map = {
            "string": "string",
            "number": "number",
            "boolean": "boolean",
            "array": "any[]",
            "object": "Record<string, any>",
            "function": "(...args: any[]) => void",
            "element": "React.ReactNode",
            "node": "React.ReactNode"
        }
        
        return type_map.get(prop_type, "any")
    
    def _collect_imports(self, components: List[Component], config: Any) -> List[str]:
        """Collect all necessary imports"""
        imports = ["import React from 'react';"]
        
        # Collect hooks
        hooks_needed = set()
        for comp in components:
            if hasattr(comp, "uses_state") and comp.uses_state:
                hooks_needed.add("useState")
            if hasattr(comp, "uses_effect") and comp.uses_effect:
                hooks_needed.add("useEffect")
        
        if hooks_needed:
            hooks_str = ", ".join(sorted(hooks_needed))
            imports[0] = f"import React, {{ {hooks_str} }} from 'react';"
        
        # Component imports
        for comp in self.generated_components.values():
            imports.append(f"import {comp} from './components/{comp}';")
        
        return imports
    
    def _extract_components(self, context: ExportContext) -> List[ComponentInfo]:
        """Extract reusable components from project"""
        components = []
        
        # Group components by type and properties
        component_groups = {}
        for comp in context.project.components:
            # Create signature for grouping
            signature = (comp.type, tuple(sorted(comp.properties.items())))
            if signature not in component_groups:
                component_groups[signature] = []
            component_groups[signature].append(comp)
        
        # Extract components used multiple times
        for signature, group in component_groups.items():
            if len(group) >= 3:  # Used 3+ times
                # Create component info
                comp_info = ComponentInfo(
                    name=self._generate_component_name(group[0]),
                    component=group[0],
                    props=self._extract_props(group),
                    instances=group
                )
                components.append(comp_info)
                
                # Register component
                self.generated_components[group[0].type] = comp_info.name
        
        return components
    
    def _generate_component_name(self, component: Component) -> str:
        """Generate React component name"""
        # Convert to PascalCase
        name = component.type.replace("_", " ").replace("-", " ")
        name = "".join(word.capitalize() for word in name.split())
        
        # Ensure valid component name
        if not name[0].isupper():
            name = "Component" + name
        
        return name
    
    def _extract_props(self, component_group: List[Component]) -> List[PropInfo]:
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
            if len(values) > 1:  # Property varies
                props.append(PropInfo(
                    name=key,
                    type=self._infer_prop_type(values),
                    optional=False,
                    default_value=None
                ))
        
        return props
    
    def _infer_prop_type(self, values: Set[str]) -> str:
        """Infer TypeScript type from values"""
        # Try to parse as numbers
        try:
            numbers = [float(v) for v in values]
            return "number"
        except ValueError:
            pass
        
        # Check for booleans
        if all(v.lower() in ["true", "false"] for v in values):
            return "boolean"
        
        # Default to string
        return "string"
    
    def _get_component_path(self, comp_info: ComponentInfo, config: Any) -> str:
        """Get file path for component"""
        ext = "tsx" if config.use_typescript else "jsx"
        return f"src/components/{comp_info.name}.{ext}"
    
    def _needs_custom_hooks(self, context: ExportContext) -> bool:
        """Check if custom hooks are needed"""
        # Check for complex state logic, API calls, etc.
        return any(
            comp.properties.get("uses_api", False)
            for comp in context.project.components
        )
    
    def _needs_api_layer(self, context: ExportContext) -> bool:
        """Check if API layer is needed"""
        # Check for forms, data fetching, etc.
        return any(
            comp.type in ["form", "data-table", "api-consumer"]
            for comp in context.project.components
        )
    
    def _get_root_components(self, context: ExportContext) -> List[Component]:
        """Get root level components"""
        return [comp for comp in context.project.components if not comp.parent_id]
    
    def _indent(self, lines: List[str], level: int) -> str:
        """Indent lines of code"""
        if not lines:
            return ""
        indent = "  " * level
        return "\n".join(indent + line for line in lines)
    
    def _generate_state_hooks(self, comp_info: ComponentInfo) -> List[str]:
        """Generate useState hooks"""
        hooks = []
        for state in comp_info.state_vars:
            default = json.dumps(state.default_value)
            hooks.append(f"const [{state.name}, set{state.name.capitalize()}] = useState({default});")
        return hooks
    
    def _generate_effect_hooks(self, comp_info: ComponentInfo) -> List[str]:
        """Generate useEffect hooks"""
        return ["// Add useEffect hooks as needed"]
    
    def _generate_context_hooks(self, comp_info: ComponentInfo) -> List[str]:
        """Generate useContext hooks"""
        return ["// Add useContext hooks as needed"]
    
    def _generate_props_destructuring(self, comp_info: ComponentInfo) -> str:
        """Generate props destructuring"""
        if not comp_info.props:
            return ""
        prop_names = [prop.name for prop in comp_info.props]
        return ", ".join(prop_names)
    
    def _generate_component_logic(self, comp_info: ComponentInfo, indent: int) -> str:
        """Generate component logic (handlers, etc.)"""
        logic = []
        
        # Add event handlers
        if comp_info.has_form:
            logic.append("const handleSubmit = (e) => {")
            logic.append("  e.preventDefault();")
            logic.append("  // Handle form submission")
            logic.append("};")
        
        if not logic:
            return ""
        
        indent_str = "  " * indent
        return "\n".join(indent_str + line for line in logic)
    
    async def _components_to_jsx(
        self,
        components: List[Component],
        context: ExportContext,
        indent: int
    ) -> str:
        """Convert multiple components to JSX"""
        jsx_parts = []
        for comp in components:
            jsx = await self._component_to_jsx(comp, indent)
            jsx_parts.append(jsx)
        return "\n".join(jsx_parts)
    
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
            "blur": "onBlur",
            "keydown": "onKeyDown",
            "keyup": "onKeyUp",
            "mouseenter": "onMouseEnter",
            "mouseleave": "onMouseLeave"
        }
        return event_map.get(event, f"on{event.capitalize()}")
    
    def _collect_component_imports(self, comp_info: ComponentInfo, config: Any) -> List[str]:
        """Collect imports for a component"""
        imports = ["import React from 'react';"]
        
        # Add hooks if needed
        if comp_info.has_state:
            imports[0] = "import React, { useState } from 'react';"
        
        # Add style import
        imports.append(f"import './{comp_info.name}.css';")
        
        return imports
    
    def _generate_component_styles(self, comp_info: ComponentInfo) -> str:
        """Generate component-specific styles"""
        return f"// Styles for {comp_info.name} component"
    
    async def _generate_styles(self, context: ExportContext) -> Dict[str, str]:
        """Generate style files"""
        files = {}
        
        # Global styles
        files["src/index.css"] = self._generate_global_styles(context)
        files["src/App.css"] = self._generate_app_styles(context)
        
        # Component styles
        for comp_name in self.generated_components.values():
            files[f"src/components/{comp_name}.css"] = self._generate_component_css(comp_name, context)
        
        return files
    
    def _generate_global_styles(self, context: ExportContext) -> str:
        """Generate global CSS"""
        return """/* Global styles */
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}"""
    
    def _generate_app_styles(self, context: ExportContext) -> str:
        """Generate App component styles"""
        return """.app {
  text-align: center;
  min-height: 100vh;
}"""
    
    def _generate_component_css(self, comp_name: str, context: ExportContext) -> str:
        """Generate component CSS"""
        return f"""/* Styles for {comp_name} component */
.{comp_name.lower()} {{
  /* Component styles */
}}"""
    
    async def _generate_hooks(self, context: ExportContext) -> Dict[str, str]:
        """Generate custom hooks"""
        return {
            "src/hooks/useApi.js": self._generate_use_api_hook(),
            "src/hooks/useLocalStorage.js": self._generate_use_local_storage_hook()
        }
    
    def _generate_use_api_hook(self) -> str:
        """Generate useApi custom hook"""
        return """import { useState, useEffect } from 'react';

export const useApi = (url, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch(url, options);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        setData(data);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [url]);

  return { data, loading, error };
};"""
    
    def _generate_use_local_storage_hook(self) -> str:
        """Generate useLocalStorage hook"""
        return """import { useState } from 'react';

export const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(error);
      return initialValue;
    }
  });

  const setValue = (value) => {
    try {
      setStoredValue(value);
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(error);
    }
  };

  return [storedValue, setValue];
};"""
    
    async def _generate_api_layer(self, context: ExportContext) -> Dict[str, str]:
        """Generate API/service layer"""
        return {
            "src/services/api.js": self._generate_api_service()
        }
    
    def _generate_api_service(self) -> str:
        """Generate API service"""
        return """const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001';

class ApiService {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    const response = await fetch(url, config);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'API request failed');
    }

    return data;
  }

  get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

export default new ApiService();"""
    
    async def _generate_tests(self, components: List[ComponentInfo], context: ExportContext) -> Dict[str, str]:
        """Generate test files"""
        files = {}
        
        # App test
        files["src/App.test.js"] = self._generate_app_test()
        
        # Component tests
        for comp_info in components:
            test_path = f"src/components/{comp_info.name}.test.js"
            files[test_path] = self._generate_component_test(comp_info)
        
        # Setup file
        files["src/setupTests.js"] = "import '@testing-library/jest-dom';"
        
        return files
    
    def _generate_app_test(self) -> str:
        """Generate App component test"""
        return """import { render, screen } from '@testing-library/react';
import App from './App';

test('renders app', () => {
  render(<App />);
  const appElement = screen.getByText(/canvas export/i);
  expect(appElement).toBeInTheDocument();
});"""
    
    def _generate_component_test(self, comp_info: ComponentInfo) -> str:
        """Generate component test"""
        return f"""import {{ render, screen }} from '@testing-library/react';
import {comp_info.name} from './{comp_info.name}';

describe('{comp_info.name}', () => {{
  test('renders without crashing', () => {{
    render(<{comp_info.name} />);
  }});
}});"""
    
    def _generate_readme(self, context: ExportContext) -> str:
        """Generate README.md"""
        return f"""# {context.project.name}

This project was exported from Canvas Editor.

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in development mode.
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

### `npm test`

Launches the test runner in interactive watch mode.

### `npm run build`

Builds the app for production to the `build` folder.

## Learn More

To learn React, check out the [React documentation](https://reactjs.org/).
"""
    
    def _generate_gitignore(self) -> str:
        """Generate .gitignore"""
        return """# Dependencies
/node_modules
/.pnp
.pnp.js

# Testing
/coverage

# Production
/build
/dist

# Misc
.DS_Store
.env.local
.env.development.local
.env.test.local
.env.production.local

npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.idea
.vscode
*.swp
*.swo"""
    
    def _generate_tsconfig(self) -> str:
        """Generate tsconfig.json"""
        return """{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}"""
    
    def _generate_eslint_config(self) -> str:
        """Generate .eslintrc.json"""
        return """{
  "extends": [
    "react-app",
    "react-app/jest"
  ],
  "rules": {
    "no-console": "warn",
    "no-unused-vars": "warn"
  }
}"""
    
    def _generate_prettier_config(self) -> str:
        """Generate .prettierrc"""
        return """{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}"""
    
    def _generate_vite_config(self, context: ExportContext) -> str:
        """Generate vite.config.js"""
        return """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000
  }
})"""
    
    def _generate_webpack_config(self, context: ExportContext) -> str:
        """Generate webpack.config.js"""
        return """const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  entry: './src/index.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js'
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: ['babel-loader']
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ]
  },
  resolve: {
    extensions: ['.js', '.jsx']
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './public/index.html'
    })
  ],
  devServer: {
    static: './dist',
    port: 3000
  }
};"""
    
    async def _generate_class_component(self, comp_info: ComponentInfo, config: Any) -> str:
        """Generate class-based component"""
        # Class components are less common in modern React
        return f"""export class {comp_info.name} extends React.Component {{
  render() {{
    return <div>Class component</div>;
  }}
}}"""
    
    async def _generate_class_app(self, root_components: List[Component], context: ExportContext) -> str:
        """Generate class-based App component"""
        return """class App extends React.Component {
  render() {
    return <div className="app">App</div>;
  }
}"""


# Helper classes
class ComponentInfo:
    """Information about a reusable component"""
    def __init__(self, name: str, component: Component, props: List['PropInfo'], instances: List[Component]):
        self.name = name
        self.component = component
        self.props = props
        self.instances = instances
        self.has_state = False
        self.has_effects = False
        self.has_context = False
        self.has_form = component.type == "form"
        self.state_vars = []


class PropInfo:
    """Information about a component prop"""
    def __init__(self, name: str, type: str, optional: bool, default_value: Any):
        self.name = name
        self.type = type
        self.optional = optional
        self.default_value = default_value