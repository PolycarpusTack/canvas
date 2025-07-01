"""Service for exporting projects to various formats"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import zipfile
from datetime import datetime

from models.component import Component
from models.project import ProjectMetadata


class ExportService:
    """Service for exporting Canvas projects"""
    
    def __init__(self):
        self.export_formats = ["html", "react", "vue", "zip"]
    
    def export_to_html(self, components: List[Component], 
                       project: ProjectMetadata,
                       output_path: Path) -> bool:
        """Export project as static HTML/CSS/JS"""
        try:
            # Create output directory
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate HTML
            html_content = self._generate_html(components, project)
            with open(output_path / "index.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Generate CSS
            css_content = self._generate_css(components)
            css_dir = output_path / "css"
            css_dir.mkdir(exist_ok=True)
            with open(css_dir / "styles.css", "w", encoding="utf-8") as f:
                f.write(css_content)
            
            # Generate JS
            js_content = self._generate_javascript(components)
            js_dir = output_path / "js"
            js_dir.mkdir(exist_ok=True)
            with open(js_dir / "script.js", "w", encoding="utf-8") as f:
                f.write(js_content)
            
            # Copy assets
            self._copy_assets(project, output_path)
            
            return True
            
        except Exception as e:
            print(f"Error exporting to HTML: {e}")
            return False
    
    def _generate_html(self, components: List[Component], 
                       project: ProjectMetadata) -> str:
        """Generate HTML document"""
        # Build component tree HTML
        body_content = "\n".join(comp.to_html() for comp in components)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project.name}</title>
    <meta name="description" content="{project.description}">
    <link rel="stylesheet" href="css/styles.css">
</head>
<body>
    {body_content}
    <script src="js/script.js"></script>
</body>
</html>"""
        
        return html
    
    def _generate_css(self, components: List[Component]) -> str:
        """Generate CSS from component styles"""
        css_rules = ["""/* Canvas Editor Generated Styles */
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
"""]
        
        # Extract component styles
        def extract_styles(component: Component, rules: List[str]):
            if component.id and component.style:
                css = component.style.to_css()
                if css:
                    rules.append(f"#{component.id} {{\n    {css}\n}}")
            
            for child in component.children:
                extract_styles(child, rules)
        
        for component in components:
            extract_styles(component, css_rules)
        
        return "\n\n".join(css_rules)
    
    def _generate_javascript(self, components: List[Component]) -> str:
        """Generate JavaScript for interactions"""
        js_code = """// Canvas Editor Generated JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Canvas Editor project loaded');
    
    // Component event handlers
"""
        
        # Extract event handlers
        def extract_events(component: Component, handlers: List[str]):
            if component.events:
                for event, handler in component.events.items():
                    handlers.append(f"""
    // {component.name} - {event}
    document.getElementById('{component.id}')?.addEventListener('{event}', function(e) {{
        {handler}
    }});""")
            
            for child in component.children:
                extract_events(child, handlers)
        
        handlers = []
        for component in components:
            extract_events(component, handlers)
        
        js_code += "\n".join(handlers)
        js_code += "\n});"
        
        return js_code
    
    def _copy_assets(self, project: ProjectMetadata, output_path: Path):
        """Copy project assets to output"""
        if project.path:
            project_path = Path(project.path)
            assets_dir = project_path / "assets"
            
            if assets_dir.exists():
                output_assets = output_path / "assets"
                output_assets.mkdir(exist_ok=True)
                
                # Copy all asset files
                for asset_file in assets_dir.rglob("*"):
                    if asset_file.is_file():
                        relative = asset_file.relative_to(assets_dir)
                        output_file = output_assets / relative
                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        output_file.write_bytes(asset_file.read_bytes())
    
    def export_to_react(self, components: List[Component], 
                        project: ProjectMetadata,
                        output_path: Path) -> bool:
        """Export project as React components"""
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate React component files
            components_dir = output_path / "src" / "components"
            components_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate App.js
            app_content = self._generate_react_app(components, project)
            with open(output_path / "src" / "App.js", "w", encoding="utf-8") as f:
                f.write(app_content)
            
            # Generate package.json
            package_json = self._generate_react_package_json(project)
            with open(output_path / "package.json", "w", encoding="utf-8") as f:
                json.dump(package_json, f, indent=2)
            
            # Generate index.js
            index_content = """import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);"""
            
            with open(output_path / "src" / "index.js", "w", encoding="utf-8") as f:
                f.write(index_content)
            
            return True
            
        except Exception as e:
            print(f"Error exporting to React: {e}")
            return False
    
    def _generate_react_app(self, components: List[Component], 
                            project: ProjectMetadata) -> str:
        """Generate React App component"""
        # Convert components to JSX
        jsx_content = self._components_to_jsx(components)
        
        return f"""import React from 'react';
import './App.css';

function App() {{
  return (
    <div className="App">
      {jsx_content}
    </div>
  );
}}

export default App;"""
    
    def _components_to_jsx(self, components: List[Component], indent: int = 6) -> str:
        """Convert components to JSX"""
        jsx_lines = []
        indent_str = " " * indent
        
        for component in components:
            # Convert component to JSX element
            tag = component.type if component.type != "div" else "div"
            attrs = []
            
            if component.id:
                attrs.append(f'id="{component.id}"')
            
            if component.attributes.get("class"):
                attrs.append(f'className="{component.attributes["class"]}"')
            
            if component.style:
                style_obj = {}
                # Convert CSS to React style object
                if component.style.width:
                    style_obj["width"] = component.style.width
                if component.style.height:
                    style_obj["height"] = component.style.height
                # Add more style conversions...
                
                if style_obj:
                    style_str = json.dumps(style_obj)
                    attrs.append(f"style={{{style_str}}}")
            
            attrs_str = " ".join(attrs)
            
            if component.children:
                jsx_lines.append(f"{indent_str}<{tag} {attrs_str}>")
                jsx_lines.append(self._components_to_jsx(component.children, indent + 2))
                jsx_lines.append(f"{indent_str}</{tag}>")
            elif component.content:
                jsx_lines.append(f"{indent_str}<{tag} {attrs_str}>{component.content}</{tag}>")
            else:
                jsx_lines.append(f"{indent_str}<{tag} {attrs_str} />")
        
        return "\n".join(jsx_lines)
    
    def _generate_react_package_json(self, project: ProjectMetadata) -> Dict[str, Any]:
        """Generate package.json for React export"""
        return {
            "name": project.name.lower().replace(" ", "-"),
            "version": "0.1.0",
            "private": True,
            "dependencies": {
                "@testing-library/jest-dom": "^5.16.5",
                "@testing-library/react": "^13.4.0",
                "@testing-library/user-event": "^13.5.0",
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1",
                "web-vitals": "^2.1.4"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "eslintConfig": {
                "extends": ["react-app", "react-app/jest"]
            },
            "browserslist": {
                "production": [">0.2%", "not dead", "not op_mini all"],
                "development": [
                    "last 1 chrome version",
                    "last 1 firefox version",
                    "last 1 safari version"
                ]
            }
        }
    
    def export_to_zip(self, components: List[Component],
                      project: ProjectMetadata,
                      output_file: Path) -> bool:
        """Export project as ZIP archive"""
        try:
            # First export to HTML in temp directory
            temp_dir = output_file.parent / f"temp_{datetime.now().timestamp()}"
            self.export_to_html(components, project, temp_dir)
            
            # Create ZIP file
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_dir)
                        zipf.write(file_path, arcname)
            
            # Clean up temp directory
            import shutil
            shutil.rmtree(temp_dir)
            
            return True
            
        except Exception as e:
            print(f"Error creating ZIP: {e}")
            return False