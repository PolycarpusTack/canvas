"""
Angular Generator

CLAUDE.md Implementation:
- #3.4: Modern Angular best practices with standalone components
- #1.2: DRY component generation  
- #4.1: Strong typing with TypeScript
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
class AngularComponentInfo:
    """Information about an Angular component"""
    component: Component
    name: str
    selector: str
    path: str
    inputs: List[Dict[str, str]] = field(default_factory=list)
    outputs: List[Dict[str, str]] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    has_forms: bool = False
    has_router: bool = False
    children: List['AngularComponentInfo'] = field(default_factory=list)


class AngularGenerator(BaseGenerator):
    """
    Generate modern Angular application with standalone components
    
    CLAUDE.md Implementation:
    - #3.4: Modern Angular patterns (standalone components, signals)
    - #1.2: DRY component generation
    """
    
    def __init__(self):
        super().__init__()
        self.component_registry: Dict[str, AngularComponentInfo] = {}
        self.generated_services: Set[str] = set()
        
    async def generate(self, context: ExportContext) -> Dict[str, str]:
        """Generate complete Angular application"""
        files = {}
        config = context.config.options
        
        # Generate package.json
        files["package.json"] = self._generate_package_json(context)
        
        # Generate Angular config files
        files["angular.json"] = self._generate_angular_json(context)
        files["tsconfig.json"] = self._generate_tsconfig()
        files["tsconfig.app.json"] = self._generate_app_tsconfig()
        files["tsconfig.spec.json"] = self._generate_spec_tsconfig()
        
        # Generate main files
        files["src/main.ts"] = self._generate_main_ts(context)
        files["src/index.html"] = self._generate_index_html(context)
        files["src/styles.scss"] = self._generate_global_styles(context)
        
        # Generate app component
        files["src/app/app.component.ts"] = await self._generate_app_component(context)
        files["src/app/app.component.html"] = await self._generate_app_template(context)
        files["src/app/app.component.scss"] = self._generate_app_styles(context)
        
        # Generate routing if needed
        if self._needs_routing(context):
            files["src/app/app.routes.ts"] = self._generate_routes(context)
            
        # Extract and generate components
        components = self._extract_components(context)
        for comp_info in components:
            component_files = await self._generate_component_files(comp_info, context)
            files.update(component_files)
            
        # Generate services
        service_files = await self._generate_services(context)
        files.update(service_files)
        
        # Generate guards if needed
        if self._needs_guards(context):
            guard_files = self._generate_guards(context)
            files.update(guard_files)
            
        # Generate pipes if needed
        pipe_files = self._generate_pipes(context)
        files.update(pipe_files)
        
        # Generate environment files
        files["src/environments/environment.ts"] = self._generate_environment()
        files["src/environments/environment.prod.ts"] = self._generate_prod_environment()
        
        # Generate tests if requested
        if config.generate_tests:
            test_files = await self._generate_tests(components, context)
            files.update(test_files)
            
        # Generate README
        if config.generate_readme:
            files["README.md"] = self._generate_readme(context)
            
        # Generate .gitignore
        files[".gitignore"] = self._generate_gitignore()
        
        return files
    
    def _generate_package_json(self, context: ExportContext) -> str:
        """Generate package.json with Angular dependencies"""
        config = context.config.options
        
        package_data = {
            "name": context.project.name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "description": "Angular app exported from Canvas Editor",
            "scripts": {
                "ng": "ng",
                "start": "ng serve",
                "build": "ng build",
                "watch": "ng build --watch --configuration development",
                "test": "ng test",
                "e2e": "ng e2e",
                "lint": "ng lint"
            },
            "private": True,
            "dependencies": {
                "@angular/animations": "^17.0.0",
                "@angular/common": "^17.0.0",
                "@angular/compiler": "^17.0.0",
                "@angular/core": "^17.0.0",
                "@angular/forms": "^17.0.0",
                "@angular/platform-browser": "^17.0.0",
                "@angular/platform-browser-dynamic": "^17.0.0",
                "@angular/router": "^17.0.0",
                "rxjs": "~7.8.0",
                "tslib": "^2.3.0",
                "zone.js": "~0.14.0"
            },
            "devDependencies": {
                "@angular-devkit/build-angular": "^17.0.0",
                "@angular/cli": "^17.0.0",
                "@angular/compiler-cli": "^17.0.0",
                "@types/jasmine": "~5.1.0",
                "jasmine-core": "~5.1.0",
                "karma": "~6.4.0",
                "karma-chrome-launcher": "~3.2.0",
                "karma-coverage": "~2.2.0",
                "karma-jasmine": "~5.1.0",
                "karma-jasmine-html-reporter": "~2.1.0",
                "typescript": "~5.2.0"
            }
        }
        
        # Add state management if needed
        if config.state_management == "ngrx":
            package_data["dependencies"]["@ngrx/store"] = "^17.0.0"
            package_data["dependencies"]["@ngrx/effects"] = "^17.0.0"
            package_data["dependencies"]["@ngrx/store-devtools"] = "^17.0.0"
        
        # Add UI library
        if config.ui_library == "angular-material":
            package_data["dependencies"]["@angular/material"] = "^17.0.0"
            package_data["dependencies"]["@angular/cdk"] = "^17.0.0"
        elif config.ui_library == "ng-bootstrap":
            package_data["dependencies"]["@ng-bootstrap/ng-bootstrap"] = "^16.0.0"
            package_data["dependencies"]["bootstrap"] = "^5.3.0"
            
        # Add testing if requested
        if config.generate_tests:
            package_data["devDependencies"]["@angular/testing"] = "^17.0.0"
            
        return json.dumps(package_data, indent=2)
    
    def _generate_angular_json(self, context: ExportContext) -> str:
        """Generate angular.json configuration"""
        project_name = context.project.name.lower().replace(" ", "-")
        
        angular_config = {
            "$schema": "./node_modules/@angular/cli/lib/config/schema.json",
            "version": 1,
            "newProjectRoot": "projects",
            "projects": {
                project_name: {
                    "projectType": "application",
                    "schematics": {
                        "@schematics/angular:component": {
                            "style": "scss",
                            "standalone": True,
                            "changeDetection": "OnPush"
                        },
                        "@schematics/angular:application": {
                            "strict": True
                        }
                    },
                    "root": "",
                    "sourceRoot": "src",
                    "prefix": "app",
                    "architect": {
                        "build": {
                            "builder": "@angular-devkit/build-angular:browser",
                            "options": {
                                "outputPath": "dist",
                                "index": "src/index.html",
                                "main": "src/main.ts",
                                "polyfills": [],
                                "tsConfig": "tsconfig.app.json",
                                "inlineStyleLanguage": "scss",
                                "assets": ["src/favicon.ico", "src/assets"],
                                "styles": ["src/styles.scss"],
                                "scripts": []
                            },
                            "configurations": {
                                "production": {
                                    "budgets": [
                                        {
                                            "type": "initial",
                                            "maximumWarning": "500kb",
                                            "maximumError": "1mb"
                                        },
                                        {
                                            "type": "anyComponentStyle",
                                            "maximumWarning": "2kb",
                                            "maximumError": "4kb"
                                        }
                                    ],
                                    "outputHashing": "all"
                                },
                                "development": {
                                    "buildOptimizer": False,
                                    "optimization": False,
                                    "vendorChunk": True,
                                    "extractLicenses": False,
                                    "sourceMap": True,
                                    "namedChunks": True
                                }
                            },
                            "defaultConfiguration": "production"
                        },
                        "serve": {
                            "builder": "@angular-devkit/build-angular:dev-server",
                            "configurations": {
                                "production": {
                                    "buildTarget": f"{project_name}:build:production"
                                },
                                "development": {
                                    "buildTarget": f"{project_name}:build:development"
                                }
                            },
                            "defaultConfiguration": "development"
                        },
                        "test": {
                            "builder": "@angular-devkit/build-angular:karma",
                            "options": {
                                "polyfills": [],
                                "tsConfig": "tsconfig.spec.json",
                                "inlineStyleLanguage": "scss",
                                "assets": ["src/favicon.ico", "src/assets"],
                                "styles": ["src/styles.scss"],
                                "scripts": []
                            }
                        }
                    }
                }
            }
        }
        
        return json.dumps(angular_config, indent=2)
    
    def _generate_main_ts(self, context: ExportContext) -> str:
        """Generate main.ts bootstrap file"""
        return """import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient } from '@angular/common/http';

import { AppComponent } from './app/app.component';
import { routes } from './app/app.routes';

bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes),
    provideAnimations(),
    provideHttpClient(),
    // Add other providers here
  ]
}).catch(err => console.error(err));
"""
    
    def _generate_index_html(self, context: ExportContext) -> str:
        """Generate index.html"""
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{context.project.name}</title>
  <base href="/">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{context.project.description or 'Generated by Canvas Editor'}">
  <link rel="icon" type="image/x-icon" href="favicon.ico">
  <link rel="preconnect" href="https://fonts.gstatic.com">
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
</head>
<body class="mat-typography">
  <app-root></app-root>
</body>
</html>
"""
    
    async def _generate_app_component(self, context: ExportContext) -> str:
        """Generate main App component"""
        return """import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title = 'Canvas Export';
}
"""
    
    async def _generate_app_template(self, context: ExportContext) -> str:
        """Generate App component template"""
        # Convert root components to Angular template
        root_components = self._get_root_components(context)
        template_content = await self._components_to_template(root_components, context)
        
        return f"""<div class="app-container">
  <header class="app-header">
    <h1>{{{{ title }}}}</h1>
  </header>
  
  <main class="app-main">
{template_content}
  </main>
  
  <router-outlet></router-outlet>
</div>
"""
    
    async def _components_to_template(
        self, 
        components: List[Component], 
        context: ExportContext,
        indent: int = 2
    ) -> str:
        """Convert components to Angular template"""
        template_parts = []
        indent_str = " " * indent
        
        for component in components:
            template = await self._component_to_template(component, context, indent)
            template_parts.append(template)
            
        return "\n".join(template_parts)
    
    async def _component_to_template(
        self,
        component: Component,
        context: ExportContext,
        indent: int = 0
    ) -> str:
        """
        Convert single component to Angular template
        
        CLAUDE.md #7.2: Escape user content
        """
        indent_str = " " * indent
        
        # Handle text nodes
        if component.type == "text":
            # Escape content to prevent XSS
            content = self._escape_template_text(component.content)
            return f"{indent_str}{content}"
        
        # Map to Angular element or component
        element = self._map_to_angular_element(component.type)
        
        # Build attributes
        attrs = self._build_template_attributes(component)
        
        # Handle self-closing elements
        if not component.children and not component.content:
            return f"{indent_str}<{element}{attrs}></{element}>"
        
        # Handle elements with children
        template_lines = [f"{indent_str}<{element}{attrs}>"]
        
        # Add content
        if component.content:
            escaped_content = self._escape_template_text(component.content)
            template_lines.append(f"{indent_str}  {escaped_content}")
        
        # Add children
        for child in component.children:
            child_template = await self._component_to_template(child, context, indent + 2)
            template_lines.append(child_template)
        
        template_lines.append(f"{indent_str}</{element}>")
        
        return "\n".join(template_lines)
    
    def _map_to_angular_element(self, component_type: str) -> str:
        """Map component type to Angular element or component"""
        # Check if it's a custom component
        if component_type in self.component_registry:
            return self.component_registry[component_type].selector
        
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
    
    def _build_template_attributes(self, component: Component) -> str:
        """Build Angular template attributes"""
        attrs = {}
        
        # Class binding
        if component.class_name:
            attrs["class"] = component.class_name
        
        # Style binding
        if component.styles:
            style_obj = self._styles_to_angular_object(component.styles)
            if style_obj:
                attrs["[ngStyle]"] = f"{{{style_obj}}}"
        
        # Event bindings
        if hasattr(component, "events"):
            for event, handler in component.events.items():
                angular_event = self._map_event_name(event)
                attrs[f"({angular_event})"] = f"{handler}($event)"
        
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
            
            # Angular form binding
            if component.properties.get("name"):
                attrs["[(ngModel)]"] = f"formData.{component.properties['name']}"
            
            if component.properties.get("placeholder"):
                attrs["placeholder"] = component.properties["placeholder"]
            if component.properties.get("required"):
                attrs["required"] = "true"
        
        # Build attributes string
        if not attrs:
            return ""
        
        attr_strings = []
        for key, value in attrs.items():
            if key.startswith("[") or key.startswith("("):
                # Angular binding
                attr_strings.append(f'{key}="{value}"')
            elif value == "true":
                # Boolean attribute
                attr_strings.append(key)
            else:
                # String attribute
                attr_strings.append(f'{key}="{self._escape_attribute(value)}"')
        
        return " " + " ".join(attr_strings) if attr_strings else ""
    
    def _escape_template_text(self, text: str) -> str:
        """
        Escape text for Angular template
        
        CLAUDE.md #7.2: Prevent XSS
        """
        if not text:
            return ""
        
        # Angular automatically escapes text interpolation
        # But we still escape for safety
        text = str(text)
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace("&", "&amp;")
        
        return text
    
    def _escape_attribute(self, value: str) -> str:
        """Escape attribute value"""
        value = value.replace('"', '&quot;')
        value = value.replace("'", '&#39;')
        return value
    
    def _extract_components(self, context: ExportContext) -> List[AngularComponentInfo]:
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
                comp_info = AngularComponentInfo(
                    component=group[0],
                    name=self._generate_component_name(group[0]),
                    selector=self._generate_selector(group[0]),
                    path=f"src/app/components/{self._to_kebab_case(group[0].type)}",
                    inputs=self._extract_inputs(group),
                    has_forms=self._component_has_forms(group[0])
                )
                components.append(comp_info)
                
                # Register component
                self.component_registry[group[0].type] = comp_info
        
        return components
    
    def _generate_component_name(self, component: Component) -> str:
        """Generate Angular component name (PascalCase)"""
        name = component.type.replace("_", " ").replace("-", " ")
        name = "".join(word.capitalize() for word in name.split())
        
        if not name[0].isupper():
            name = "Custom" + name
        
        return name + "Component"
    
    def _generate_selector(self, component: Component) -> str:
        """Generate Angular component selector"""
        name = self._to_kebab_case(component.type)
        return f"app-{name}"
    
    def _to_kebab_case(self, text: str) -> str:
        """Convert to kebab-case"""
        import re
        text = re.sub('([a-z0-9])([A-Z])', r'\1-\2', text)
        return text.lower().replace('_', '-').replace(' ', '-')
    
    async def _generate_component_files(
        self,
        comp_info: AngularComponentInfo,
        context: ExportContext
    ) -> Dict[str, str]:
        """Generate all files for a component"""
        files = {}
        
        # Component TypeScript file
        files[f"{comp_info.path}.component.ts"] = await self._generate_component_ts(comp_info, context)
        
        # Component template
        files[f"{comp_info.path}.component.html"] = await self._generate_component_template(comp_info, context)
        
        # Component styles
        files[f"{comp_info.path}.component.scss"] = self._generate_component_styles(comp_info)
        
        # Component spec file
        files[f"{comp_info.path}.component.spec.ts"] = self._generate_component_spec(comp_info)
        
        return files
    
    async def _generate_component_ts(
        self,
        comp_info: AngularComponentInfo,
        context: ExportContext
    ) -> str:
        """Generate component TypeScript file"""
        imports = ["import { Component, Input, Output, EventEmitter } from '@angular/core';"]
        imports.append("import { CommonModule } from '@angular/common';")
        
        # Add form imports if needed
        if comp_info.has_forms:
            imports.append("import { FormsModule, ReactiveFormsModule } from '@angular/forms';")
        
        # Build inputs interface
        inputs_interface = ""
        if comp_info.inputs:
            input_props = []
            for input_info in comp_info.inputs:
                prop_type = input_info.get("type", "any")
                input_props.append(f"  {input_info['name']}: {prop_type};")
            
            inputs_interface = f"""
export interface {comp_info.name}Props {{
{chr(10).join(input_props)}
}}

"""
        
        # Build component inputs
        input_decorators = []
        for input_info in comp_info.inputs:
            input_decorators.append(f"  @Input() {input_info['name']}: {input_info.get('type', 'any')};")
        
        # Build component outputs
        output_decorators = []
        for output_info in comp_info.outputs:
            output_decorators.append(f"  @Output() {output_info['name']} = new EventEmitter<{output_info.get('type', 'any')}>();")
        
        # Build imports array
        component_imports = ["CommonModule"]
        if comp_info.has_forms:
            component_imports.extend(["FormsModule", "ReactiveFormsModule"])
        
        return f"""{chr(10).join(imports)}

{inputs_interface}@Component({{
  selector: '{comp_info.selector}',
  standalone: true,
  imports: [{', '.join(component_imports)}],
  templateUrl: './{self._to_kebab_case(comp_info.name.replace("Component", ""))}.component.html',
  styleUrl: './{self._to_kebab_case(comp_info.name.replace("Component", ""))}.component.scss'
}})
export class {comp_info.name} {{
{chr(10).join(input_decorators)}

{chr(10).join(output_decorators)}

  // Component logic here
  
}}
"""
    
    async def _generate_component_template(
        self,
        comp_info: AngularComponentInfo,
        context: ExportContext
    ) -> str:
        """Generate component template"""
        template = await self._component_to_template(comp_info.component, context)
        
        return f"""<div class="{self._to_kebab_case(comp_info.name.replace('Component', ''))}">
{template}
</div>
"""
    
    def _generate_component_styles(self, comp_info: AngularComponentInfo) -> str:
        """Generate component SCSS styles"""
        class_name = self._to_kebab_case(comp_info.name.replace("Component", ""))
        
        return f"""/* Styles for {comp_info.name} */
.{class_name} {{
  display: block;
  
  // Component-specific styles
}}
"""
    
    def _generate_component_spec(self, comp_info: AngularComponentInfo) -> str:
        """Generate component test spec"""
        return f"""import {{ ComponentFixture, TestBed }} from '@angular/core/testing';

import {{ {comp_info.name} }} from './{self._to_kebab_case(comp_info.name.replace("Component", ""))}.component';

describe('{comp_info.name}', () => {{
  let component: {comp_info.name};
  let fixture: ComponentFixture<{comp_info.name}>;

  beforeEach(async () => {{
    await TestBed.configureTestingModule({{
      imports: [{comp_info.name}]
    }})
    .compileComponents();
    
    fixture = TestBed.createComponent({comp_info.name});
    component = fixture.componentInstance;
    fixture.detectChanges();
  }});

  it('should create', () => {{
    expect(component).toBeTruthy();
  }});
}});
"""
    
    def _generate_global_styles(self, context: ExportContext) -> str:
        """Generate global SCSS styles"""
        return """/* Global styles */
* {
  box-sizing: border-box;
}

html, body {
  height: 100%;
  margin: 0;
  font-family: Roboto, "Helvetica Neue", sans-serif;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: #1976d2;
  color: white;
  padding: 1rem;
  text-align: center;
}

.app-main {
  flex: 1;
  padding: 2rem;
}
"""
    
    def _generate_app_styles(self, context: ExportContext) -> str:
        """Generate App component styles"""
        return """:host {
  display: block;
}

.app-container {
  min-height: 100vh;
}
"""
    
    def _generate_routes(self, context: ExportContext) -> str:
        """Generate app routes"""
        return """import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: '/home', pathMatch: 'full' },
  { path: 'home', loadComponent: () => import('./components/home/home.component').then(m => m.HomeComponent) },
  // Add more routes here
];
"""
    
    async def _generate_services(self, context: ExportContext) -> Dict[str, str]:
        """Generate Angular services"""
        files = {}
        
        # Data service
        files["src/app/services/data.service.ts"] = self._generate_data_service()
        files["src/app/services/data.service.spec.ts"] = self._generate_data_service_spec()
        
        return files
    
    def _generate_data_service(self) -> str:
        """Generate data service"""
        return """import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DataService {
  private apiUrl = 'http://localhost:3000/api';

  constructor(private http: HttpClient) { }

  getData(): Observable<any> {
    return this.http.get(`${this.apiUrl}/data`);
  }

  postData(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/data`, data);
  }
}
"""
    
    def _generate_data_service_spec(self) -> str:
        """Generate data service test"""
        return """import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { DataService } from './data.service';

describe('DataService', () => {
  let service: DataService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(DataService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
"""
    
    def _generate_tsconfig(self) -> str:
        """Generate TypeScript configuration"""
        return """{
  "compileOnSave": false,
  "compilerOptions": {
    "baseUrl": "./",
    "outDir": "./dist/out-tsc",
    "forceConsistentCasingInFileNames": true,
    "strict": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "sourceMap": true,
    "declaration": false,
    "downlevelIteration": true,
    "experimentalDecorators": true,
    "moduleResolution": "node",
    "importHelpers": true,
    "target": "ES2022",
    "module": "ES2022",
    "useDefineForClassFields": false,
    "lib": [
      "ES2022",
      "dom"
    ]
  },
  "angularCompilerOptions": {
    "enableI18nLegacyMessageIdFormat": false,
    "strictInjectionParameters": true,
    "strictInputAccessModifiers": true,
    "strictTemplates": true
  }
}
"""
    
    def _generate_app_tsconfig(self) -> str:
        """Generate app-specific TypeScript config"""
        return """{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "outDir": "./out-tsc/app",
    "types": []
  },
  "files": [
    "src/main.ts"
  ],
  "include": [
    "src/**/*.d.ts"
  ]
}
"""
    
    def _generate_spec_tsconfig(self) -> str:
        """Generate test TypeScript config"""
        return """{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "outDir": "./out-tsc/spec",
    "types": [
      "jasmine"
    ]
  },
  "include": [
    "src/**/*.spec.ts",
    "src/**/*.d.ts"
  ]
}
"""
    
    def _generate_environment(self) -> str:
        """Generate environment configuration"""
        return """export const environment = {
  production: false,
  apiUrl: 'http://localhost:3000/api'
};
"""
    
    def _generate_prod_environment(self) -> str:
        """Generate production environment"""
        return """export const environment = {
  production: true,
  apiUrl: '/api'
};
"""
    
    def _generate_readme(self, context: ExportContext) -> str:
        """Generate README.md"""
        return f"""# {context.project.name}

This project was exported from Canvas Editor and built with Angular 17.

## Development server

Run `ng serve` for a dev server. Navigate to `http://localhost:4200/`. The application will automatically reload if you change any of the source files.

## Code scaffolding

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.

## Build

Run `ng build` to build the project. The build artifacts will be stored in the `dist/` directory.

## Running unit tests

Run `ng test` to execute the unit tests via [Karma](https://karma-runner.github.io).

## Further help

To get more help on the Angular CLI use `ng help` or go check out the [Angular CLI Overview and Command Reference](https://angular.io/cli) page.
"""
    
    def _generate_gitignore(self) -> str:
        """Generate .gitignore"""
        return """# Compiled output
/dist
/tmp
/out-tsc
/bazel-out

# Node
/node_modules
npm-debug.log
yarn-error.log

# IDEs and editors
.idea/
.project
.classpath
.c9/
*.launch
.settings/
*.sublime-workspace

# Visual Studio Code
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json
.history/*

# Miscellaneous
/.angular/cache
.sass-cache/
/connect.lock
/coverage
/libpeerconnection.log
testem.log
/typings

# System files
.DS_Store
Thumbs.db
"""
    
    # Helper methods
    def _needs_routing(self, context: ExportContext) -> bool:
        """Check if routing is needed"""
        return len([c for c in context.project.components if not c.parent_id]) > 1
    
    def _needs_guards(self, context: ExportContext) -> bool:
        """Check if route guards are needed"""
        return any(c.properties.get("requires_auth") for c in context.project.components)
    
    def _component_has_forms(self, component: Component) -> bool:
        """Check if component has forms"""
        return component.type in ["form", "input", "textarea", "select"]
    
    def _get_root_components(self, context: ExportContext) -> List[Component]:
        """Get root components"""
        return [comp for comp in context.project.components if not comp.parent_id]
    
    def _extract_inputs(self, component_group: List[Component]) -> List[Dict[str, str]]:
        """Extract varying properties as inputs"""
        inputs = []
        
        # Find properties that vary across instances
        all_props = {}
        for comp in component_group:
            for key, value in comp.properties.items():
                if key not in all_props:
                    all_props[key] = set()
                all_props[key].add(str(value))
        
        # Create input info for varying properties
        for key, values in all_props.items():
            if len(values) > 1:
                inputs.append({
                    "name": key,
                    "type": self._infer_typescript_type(values)
                })
        
        return inputs
    
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
    
    def _styles_to_angular_object(self, styles: Dict[str, Any]) -> str:
        """Convert styles to Angular style binding"""
        style_pairs = []
        for key, value in styles.items():
            angular_key = self._to_camel_case(key)
            style_pairs.append(f"'{angular_key}': '{value}'")
        return "{" + ", ".join(style_pairs) + "}"
    
    def _to_camel_case(self, text: str) -> str:
        """Convert to camelCase"""
        parts = text.split("-")
        return parts[0] + "".join(part.capitalize() for part in parts[1:])
    
    def _map_event_name(self, event: str) -> str:
        """Map event name to Angular convention"""
        return event  # Angular uses standard DOM events
    
    def _generate_guards(self, context: ExportContext) -> Dict[str, str]:
        """Generate route guards"""
        return {
            "src/app/guards/auth.guard.ts": """import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

export const authGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);
  
  // Add authentication logic here
  const isAuthenticated = false; // Replace with actual auth check
  
  if (!isAuthenticated) {
    router.navigate(['/login']);
    return false;
  }
  
  return true;
};
"""
        }
    
    def _generate_pipes(self, context: ExportContext) -> Dict[str, str]:
        """Generate custom pipes"""
        return {}
    
    async def _generate_tests(self, components: List[AngularComponentInfo], context: ExportContext) -> Dict[str, str]:
        """Generate additional test files"""
        files = {}
        
        # App component test
        files["src/app/app.component.spec.ts"] = """import { TestBed } from '@angular/core/testing';
import { AppComponent } from './app.component';

describe('AppComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AppComponent],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should have the correct title', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app.title).toEqual('Canvas Export');
  });
});
"""
        
        return files