"""
Test Export Generators

CLAUDE.md Implementation:
- #14.1: Unit tests for generators
"""

import pytest
from pathlib import Path

from src.export.generators.html_generator import HTMLGenerator
from src.export.generators.react_generator import ReactGenerator
from src.export.generators.vue_generator import VueGenerator
from src.export.export_context import ExportContext
from src.export.export_config import (
    ExportConfig, ExportFormat, ExportOptions
)
from src.models.project_enhanced import Project
from src.models.component_enhanced import Component


@pytest.fixture
def export_context():
    """Create export context for testing"""
    
    project = Project(
        id="test",
        name="Test Project",
        components=[
            Component(
                id="root",
                type="container",
                properties={"class": "container"},
                children=[
                    Component(
                        id="heading",
                        type="heading",
                        content="Test Heading",
                        properties={"level": 1}
                    ),
                    Component(
                        id="button",
                        type="button",
                        content="Click Me",
                        properties={
                            "onClick": "handleClick",
                            "class": "btn primary"
                        }
                    )
                ]
            )
        ],
        metadata={
            "title": "Test Project",
            "description": "Test"
        }
    )
    
    config = ExportConfig(
        format=ExportFormat.HTML,
        output_path=Path("/tmp"),
        options=ExportOptions()
    )
    
    context = ExportContext(project=project, config=config)
    return context


class TestHTMLGenerator:
    """Test HTML generator"""
    
    @pytest.mark.asyncio
    async def test_basic_html_generation(self, export_context):
        """Test basic HTML generation"""
        
        generator = HTMLGenerator()
        files = await generator.generate(
            export_context,
            export_context.config.options
        )
        
        assert "index.html" in files
        assert "styles.css" in files
        assert "script.js" in files
        
        # Check HTML content
        html = files["index.html"]
        assert "<!DOCTYPE html>" in html
        assert "<h1>Test Heading</h1>" in html
        assert '<button' in html
        assert 'Click Me</button>' in html
    
    @pytest.mark.asyncio
    async def test_single_file_mode(self, export_context):
        """Test single file HTML generation"""
        
        export_context.config.options.single_file = True
        
        generator = HTMLGenerator()
        files = await generator.generate(
            export_context,
            export_context.config.options
        )
        
        assert len(files) == 1
        assert "index.html" in files
        
        # Should have inline styles and scripts
        html = files["index.html"]
        assert "<style>" in html
        assert "<script>" in html
    
    @pytest.mark.asyncio
    async def test_accessibility_features(self, export_context):
        """Test accessibility features in HTML"""
        
        generator = HTMLGenerator()
        files = await generator.generate(
            export_context,
            export_context.config.options
        )
        
        html = files["index.html"]
        
        # Check for accessibility features
        assert 'lang="en"' in html
        assert '<meta charset="UTF-8">' in html
        assert 'role="main"' in html or 'main' in html
        assert 'Skip to main content' in html  # Skip link


class TestReactGenerator:
    """Test React generator"""
    
    @pytest.mark.asyncio
    async def test_react_generation(self, export_context):
        """Test React component generation"""
        
        export_context.config.format = ExportFormat.REACT
        
        generator = ReactGenerator()
        files = await generator.generate(
            export_context,
            export_context.config.options
        )
        
        assert "package.json" in files
        assert "src/App.jsx" in files
        assert "src/index.jsx" in files
        
        # Check App component
        app_content = files["src/App.jsx"]
        assert "import React" in app_content
        assert "function App()" in app_content
        assert "export default App" in app_content
    
    @pytest.mark.asyncio
    async def test_react_typescript(self, export_context):
        """Test React with TypeScript"""
        
        export_context.config.format = ExportFormat.REACT
        export_context.config.options.typescript = True
        
        generator = ReactGenerator()
        files = await generator.generate(
            export_context,
            export_context.config.options
        )
        
        assert "src/App.tsx" in files
        assert "src/index.tsx" in files
        assert "tsconfig.json" in files
        
        # Check TypeScript content
        app_content = files["src/App.tsx"]
        assert ": React.FC" in app_content or ": FC" in app_content
    
    @pytest.mark.asyncio
    async def test_react_component_extraction(self, export_context):
        """Test React component extraction"""
        
        # Add a reusable component
        button_component = Component(
            id="custom_button",
            type="button",
            name="CustomButton",
            content="Reusable Button",
            properties={"variant": "primary"}
        )
        
        export_context.project.components[0].children.append(button_component)
        export_context.config.format = ExportFormat.REACT
        
        generator = ReactGenerator()
        files = await generator.generate(
            export_context,
            export_context.config.options
        )
        
        # Should extract custom component
        assert "src/components/CustomButton.jsx" in files
        
        # Check component content
        button_content = files["src/components/CustomButton.jsx"]
        assert "function CustomButton" in button_content
        assert "export default CustomButton" in button_content


class TestVueGenerator:
    """Test Vue generator"""
    
    @pytest.mark.asyncio
    async def test_vue_generation(self, export_context):
        """Test Vue component generation"""
        
        export_context.config.format = ExportFormat.VUE
        
        generator = VueGenerator()
        files = await generator.generate(
            export_context,
            export_context.config.options
        )
        
        assert "package.json" in files
        assert "src/App.vue" in files
        assert "src/main.js" in files
        
        # Check App component
        app_content = files["src/App.vue"]
        assert "<template>" in app_content
        assert "<script setup>" in app_content
        assert "<style scoped>" in app_content
    
    @pytest.mark.asyncio
    async def test_vue_composition_api(self, export_context):
        """Test Vue with Composition API"""
        
        export_context.config.format = ExportFormat.VUE
        
        generator = VueGenerator()
        files = await generator.generate(
            export_context,
            export_context.config.options
        )
        
        app_content = files["src/App.vue"]
        
        # Should use Composition API
        assert "<script setup>" in app_content
        assert "ref" in files["src/main.js"] or "createApp" in files["src/main.js"]
    
    @pytest.mark.asyncio
    async def test_vue_router_generation(self, export_context):
        """Test Vue Router generation"""
        
        # Add multiple top-level containers (pages)
        export_context.project.components.append(
            Component(
                id="about",
                type="container",
                name="About",
                children=[
                    Component(
                        id="about_text",
                        type="text",
                        content="About page"
                    )
                ]
            )
        )
        
        export_context.config.format = ExportFormat.VUE
        
        generator = VueGenerator()
        files = await generator.generate(
            export_context,
            export_context.config.options
        )
        
        assert "src/router/index.js" in files
        
        router_content = files["src/router/index.js"]
        assert "createRouter" in router_content
        assert "createWebHistory" in router_content


class TestGeneratorCommon:
    """Test common generator functionality"""
    
    @pytest.mark.asyncio
    async def test_style_generation(self, export_context):
        """Test CSS generation from component styles"""
        
        # Add component with styles
        export_context.project.components[0].styles = {
            "backgroundColor": "#f0f0f0",
            "padding": "20px",
            "borderRadius": "8px"
        }
        
        generator = HTMLGenerator()
        files = await generator.generate(
            export_context,
            export_context.config.options
        )
        
        css_content = files["styles.css"]
        
        # Check CSS generation
        assert "background-color: #f0f0f0" in css_content
        assert "padding: 20px" in css_content
        assert "border-radius: 8px" in css_content
    
    @pytest.mark.asyncio
    async def test_responsive_styles(self, export_context):
        """Test responsive CSS generation"""
        
        # Add responsive styles
        export_context.project.components[0].responsive_styles = {
            768: {"padding": "10px"},
            1024: {"padding": "30px"}
        }
        
        generator = HTMLGenerator()
        files = await generator.generate(
            export_context,
            export_context.config.options
        )
        
        css_content = files["styles.css"]
        
        # Check media queries
        assert "@media" in css_content
        assert "max-width: 768px" in css_content or "min-width: 768px" in css_content
    
    @pytest.mark.asyncio
    async def test_asset_references(self, export_context):
        """Test asset reference handling"""
        
        # Add image with asset reference
        export_context.project.components[0].children.append(
            Component(
                id="logo",
                type="image",
                properties={
                    "src": "asset:logo-123",
                    "alt": "Logo"
                }
            )
        )
        
        export_context.asset_map = {
            "logo-123": {
                "path": "/assets/logo.png",
                "url": "logo.png"
            }
        }
        
        generator = HTMLGenerator()
        files = await generator.generate(
            export_context,
            export_context.config.options
        )
        
        html_content = files["index.html"]
        
        # Should resolve asset reference
        assert 'src="assets/logo.png"' in html_content or 'src="logo.png"' in html_content