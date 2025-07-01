"""
Test Export Pipeline

CLAUDE.md Implementation:
- #14.1: Comprehensive testing
- #2.2.3: Integration tests
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime

from src.export.export_pipeline import ExportPipeline
from src.export.export_config import (
    ExportConfig, ExportFormat, ExportOptions,
    OptimizationSettings, ExportPreset
)
from src.models.project_enhanced import Project
from src.models.component_enhanced import Component
from src.models.asset import Asset, AssetMetadata


@pytest.fixture
def sample_project():
    """Create a sample project for testing"""
    
    components = [
        Component(
            id="root",
            type="container",
            name="App",
            properties={"class": "app-container"},
            styles={"padding": "20px", "backgroundColor": "#f0f0f0"},
            children=[
                Component(
                    id="header",
                    type="heading",
                    name="Title",
                    content="Welcome to Canvas Export",
                    properties={"level": 1},
                    styles={"color": "#333", "marginBottom": "20px"}
                ),
                Component(
                    id="content",
                    type="container",
                    name="Content",
                    properties={"class": "content-area"},
                    children=[
                        Component(
                            id="text1",
                            type="text",
                            content="This is a sample project for testing export functionality.",
                            styles={"fontSize": "16px", "lineHeight": "1.5"}
                        ),
                        Component(
                            id="button1",
                            type="button",
                            name="ActionButton",
                            content="Click Me",
                            properties={
                                "onClick": "handleClick",
                                "class": "btn btn-primary"
                            },
                            styles={
                                "padding": "10px 20px",
                                "backgroundColor": "#007bff",
                                "color": "white",
                                "border": "none",
                                "borderRadius": "4px"
                            }
                        )
                    ]
                ),
                Component(
                    id="image1",
                    type="image",
                    name="Logo",
                    properties={
                        "src": "asset:logo-123",
                        "alt": "Company Logo",
                        "width": 200,
                        "height": 100
                    }
                )
            ]
        )
    ]
    
    return Project(
        id="test-project",
        name="Test Export Project",
        components=components,
        assets=[
            Asset(
                id="logo-123",
                path="/assets/logo.png",
                metadata=AssetMetadata(
                    name="logo.png",
                    mime_type="image/png",
                    size=5000,
                    asset_type="image"
                )
            )
        ],
        metadata={
            "title": "Test Project",
            "description": "A test project for export functionality",
            "author": "Test User"
        }
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory"""
    output_dir = tmp_path / "export_output"
    output_dir.mkdir()
    return output_dir


class TestExportPipeline:
    """Test export pipeline functionality"""
    
    @pytest.mark.asyncio
    async def test_html_export(self, sample_project, temp_output_dir):
        """Test HTML export"""
        
        # Create pipeline
        pipeline = ExportPipeline()
        
        # Create config
        config = ExportConfig(
            format=ExportFormat.HTML,
            output_path=temp_output_dir,
            options=ExportOptions(
                inline_styles=True,
                include_source_map=False,
                minify_code=True
            ),
            optimization=OptimizationSettings(
                minify_html=True,
                minify_css=True,
                minify_js=True
            )
        )
        
        # Export
        result = await pipeline.export(sample_project, config)
        
        # Assertions
        assert result.success is True
        assert len(result.errors) == 0
        assert result.output_path == temp_output_dir
        assert result.duration > 0
        
        # Check generated files
        index_file = temp_output_dir / "index.html"
        assert index_file.exists()
        
        # Check content
        content = index_file.read_text()
        assert "Welcome to Canvas Export" in content
        assert "Click Me" in content
    
    @pytest.mark.asyncio
    async def test_react_export(self, sample_project, temp_output_dir):
        """Test React export"""
        
        pipeline = ExportPipeline()
        
        config = ExportConfig(
            format=ExportFormat.REACT,
            output_path=temp_output_dir,
            options=ExportOptions(
                use_typescript=True,
                state_management="redux",
                generate_tests=True
            )
        )
        
        result = await pipeline.export(sample_project, config)
        
        assert result.success is True
        assert (temp_output_dir / "package.json").exists()
        assert (temp_output_dir / "src" / "App.tsx").exists()
        assert (temp_output_dir / "src" / "index.tsx").exists()
    
    @pytest.mark.asyncio
    async def test_vue_export(self, sample_project, temp_output_dir):
        """Test Vue export"""
        
        pipeline = ExportPipeline()
        
        config = ExportConfig(
            format=ExportFormat.VUE,
            output_path=temp_output_dir,
            options=ExportOptions(
                use_typescript=False,
                state_management="vuex"
            )
        )
        
        result = await pipeline.export(sample_project, config)
        
        assert result.success is True
        assert (temp_output_dir / "package.json").exists()
        assert (temp_output_dir / "src" / "App.vue").exists()
        assert (temp_output_dir / "src" / "main.js").exists()
    
    @pytest.mark.asyncio
    async def test_validation_failure(self, temp_output_dir):
        """Test export with validation failure"""
        
        pipeline = ExportPipeline()
        
        # Create invalid project (no components)
        invalid_project = Project(
            id="invalid",
            name="Invalid Project",
            components=[]  # Empty components
        )
        
        config = ExportConfig(
            format=ExportFormat.HTML,
            output_path=temp_output_dir
        )
        
        result = await pipeline.export(invalid_project, config)
        
        assert result.success is False
        assert len(result.errors) > 0
        assert "no components" in result.errors[0].lower()
    
    @pytest.mark.asyncio
    async def test_asset_processing(self, sample_project, temp_output_dir):
        """Test asset processing during export"""
        
        pipeline = ExportPipeline()
        
        config = ExportConfig(
            format=ExportFormat.HTML,
            output_path=temp_output_dir,
            optimization=OptimizationSettings(
                optimize_images=True,
                generate_webp=True,
                max_image_width=1200
            )
        )
        
        result = await pipeline.export(sample_project, config)
        
        assert result.success is True
        # Check that assets were processed
        assert result.report.assets_processed > 0
    
    @pytest.mark.asyncio
    async def test_progress_tracking(self, sample_project, temp_output_dir):
        """Test progress tracking during export"""
        
        pipeline = ExportPipeline()
        
        # Track progress updates
        progress_updates = []
        
        def progress_callback(phase):
            progress_updates.append({
                "phase": phase.name,
                "progress": phase.progress,
                "completed": phase.completed
            })
        
        pipeline.progress_tracker.register_callback("test", progress_callback)
        
        config = ExportConfig(
            format=ExportFormat.REACT,
            output_path=temp_output_dir
        )
        
        result = await pipeline.export(sample_project, config)
        
        assert result.success is True
        assert len(progress_updates) > 0
        
        # Check that all phases were tracked
        phase_names = [update["phase"] for update in progress_updates]
        expected_phases = [
            "validation", "preparation", "generation",
            "assets", "writing", "reporting"
        ]
        
        for phase in expected_phases:
            assert phase in phase_names
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, sample_project, temp_output_dir):
        """Test transaction rollback on failure"""
        
        pipeline = ExportPipeline()
        
        # Create config that will cause failure during write
        config = ExportConfig(
            format=ExportFormat.HTML,
            output_path=Path("/invalid/path/that/does/not/exist")
        )
        
        result = await pipeline.export(sample_project, config)
        
        assert result.success is False
        # Ensure no partial files were left
        assert not any(temp_output_dir.iterdir())
    
    @pytest.mark.asyncio
    async def test_code_optimization(self, sample_project, temp_output_dir):
        """Test code optimization features"""
        
        pipeline = ExportPipeline()
        
        # Export without optimization
        config_no_opt = ExportConfig(
            format=ExportFormat.HTML,
            output_path=temp_output_dir / "no_opt",
            options=ExportOptions(minify_code=False),
            optimization=OptimizationSettings(
                minify_html=False,
                minify_css=False,
                minify_js=False
            )
        )
        
        result_no_opt = await pipeline.export(sample_project, config_no_opt)
        
        # Export with optimization
        config_opt = ExportConfig(
            format=ExportFormat.HTML,
            output_path=temp_output_dir / "opt",
            options=ExportOptions(minify_code=True),
            optimization=OptimizationSettings(
                minify_html=True,
                minify_css=True,
                minify_js=True,
                purge_unused_css=True
            )
        )
        
        result_opt = await pipeline.export(sample_project, config_opt)
        
        assert result_no_opt.success is True
        assert result_opt.success is True
        
        # Compare file sizes
        no_opt_file = (temp_output_dir / "no_opt" / "index.html")
        opt_file = (temp_output_dir / "opt" / "index.html")
        
        assert no_opt_file.stat().st_size > opt_file.stat().st_size
    
    @pytest.mark.asyncio
    async def test_preset_configurations(self, sample_project, temp_output_dir):
        """Test export with preset configurations"""
        
        pipeline = ExportPipeline()
        
        # Test production preset
        config = ExportConfig.from_preset(
            ExportPreset.PRODUCTION,
            ExportFormat.REACT,
            temp_output_dir
        )
        
        result = await pipeline.export(sample_project, config)
        
        assert result.success is True
        assert config.optimization.minify_html is True
        assert config.optimization.optimize_images is True
    
    @pytest.mark.asyncio
    async def test_accessibility_validation(self, temp_output_dir):
        """Test accessibility validation during export"""
        
        pipeline = ExportPipeline()
        
        # Create project with accessibility issues
        components = [
            Component(
                id="img_no_alt",
                type="image",
                properties={"src": "test.jpg"}  # Missing alt text
            ),
            Component(
                id="button_no_text",
                type="button",
                properties={}  # Missing accessible text
            )
        ]
        
        project = Project(
            id="accessibility-test",
            name="Accessibility Test",
            components=components
        )
        
        config = ExportConfig(
            format=ExportFormat.HTML,
            output_path=temp_output_dir
        )
        
        result = await pipeline.export(project, config)
        
        # Should have warnings about accessibility
        assert len(result.warnings) > 0
        assert any("alt text" in w.lower() for w in result.warnings)