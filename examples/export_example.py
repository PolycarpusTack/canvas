"""
Export System Example

Demonstrates how to use the Canvas export system to generate
HTML, React, and Vue applications from a Canvas project.
"""

import asyncio
from pathlib import Path
from datetime import datetime

from src.export import (
    ExportPipeline,
    ExportConfig,
    ExportFormat,
    ExportOptions,
    OptimizationSettings,
    ExportPreset
)
from src.models.project import Project
from src.models.component import Component


def create_sample_project() -> Project:
    """Create a sample Canvas project"""
    
    # Create a simple landing page structure
    components = [
        Component(
            id="root",
            type="container",
            name="LandingPage",
            properties={"class": "landing-page"},
            styles={
                "minHeight": "100vh",
                "fontFamily": "Arial, sans-serif"
            },
            children=[
                # Header
                Component(
                    id="header",
                    type="container",
                    name="Header",
                    properties={"class": "header"},
                    styles={
                        "backgroundColor": "#333",
                        "color": "white",
                        "padding": "20px"
                    },
                    children=[
                        Component(
                            id="logo",
                            type="heading",
                            content="Canvas Export Demo",
                            properties={"level": 1},
                            styles={"margin": "0"}
                        ),
                        Component(
                            id="nav",
                            type="container",
                            properties={"class": "nav"},
                            styles={
                                "display": "flex",
                                "gap": "20px",
                                "marginTop": "10px"
                            },
                            children=[
                                Component(
                                    id="nav1",
                                    type="link",
                                    content="Home",
                                    properties={"href": "#home"}
                                ),
                                Component(
                                    id="nav2",
                                    type="link",
                                    content="Features",
                                    properties={"href": "#features"}
                                ),
                                Component(
                                    id="nav3",
                                    type="link",
                                    content="Contact",
                                    properties={"href": "#contact"}
                                )
                            ]
                        )
                    ]
                ),
                
                # Hero Section
                Component(
                    id="hero",
                    type="container",
                    name="HeroSection",
                    properties={"class": "hero"},
                    styles={
                        "textAlign": "center",
                        "padding": "100px 20px",
                        "backgroundColor": "#f8f9fa"
                    },
                    children=[
                        Component(
                            id="hero_title",
                            type="heading",
                            content="Build Amazing Web Apps",
                            properties={"level": 2},
                            styles={
                                "fontSize": "48px",
                                "marginBottom": "20px"
                            }
                        ),
                        Component(
                            id="hero_text",
                            type="text",
                            content="Export your Canvas designs to production-ready code",
                            styles={
                                "fontSize": "20px",
                                "color": "#666",
                                "marginBottom": "30px"
                            }
                        ),
                        Component(
                            id="cta_button",
                            type="button",
                            name="CTAButton",
                            content="Get Started",
                            properties={
                                "onClick": "handleGetStarted",
                                "class": "cta-button"
                            },
                            styles={
                                "fontSize": "18px",
                                "padding": "15px 30px",
                                "backgroundColor": "#007bff",
                                "color": "white",
                                "border": "none",
                                "borderRadius": "5px",
                                "cursor": "pointer"
                            }
                        )
                    ]
                ),
                
                # Features Section
                Component(
                    id="features",
                    type="container",
                    name="FeaturesSection",
                    properties={"class": "features"},
                    styles={
                        "padding": "80px 20px",
                        "maxWidth": "1200px",
                        "margin": "0 auto"
                    },
                    children=[
                        Component(
                            id="features_title",
                            type="heading",
                            content="Features",
                            properties={"level": 2},
                            styles={
                                "textAlign": "center",
                                "marginBottom": "50px"
                            }
                        ),
                        Component(
                            id="features_grid",
                            type="container",
                            properties={"class": "features-grid"},
                            styles={
                                "display": "grid",
                                "gridTemplateColumns": "repeat(auto-fit, minmax(300px, 1fr))",
                                "gap": "30px"
                            },
                            children=[
                                # Feature 1
                                Component(
                                    id="feature1",
                                    type="container",
                                    name="FeatureCard",
                                    properties={"class": "feature-card"},
                                    styles={
                                        "padding": "30px",
                                        "backgroundColor": "#f8f9fa",
                                        "borderRadius": "8px"
                                    },
                                    children=[
                                        Component(
                                            id="feature1_title",
                                            type="heading",
                                            content="Multiple Formats",
                                            properties={"level": 3}
                                        ),
                                        Component(
                                            id="feature1_text",
                                            type="text",
                                            content="Export to HTML, React, Vue, Angular, and more."
                                        )
                                    ]
                                ),
                                # Feature 2
                                Component(
                                    id="feature2",
                                    type="container",
                                    name="FeatureCard",
                                    properties={"class": "feature-card"},
                                    styles={
                                        "padding": "30px",
                                        "backgroundColor": "#f8f9fa",
                                        "borderRadius": "8px"
                                    },
                                    children=[
                                        Component(
                                            id="feature2_title",
                                            type="heading",
                                            content="Optimized Output",
                                            properties={"level": 3}
                                        ),
                                        Component(
                                            id="feature2_text",
                                            type="text",
                                            content="Minified, tree-shaken, production-ready code."
                                        )
                                    ]
                                ),
                                # Feature 3
                                Component(
                                    id="feature3",
                                    type="container",
                                    name="FeatureCard",
                                    properties={"class": "feature-card"},
                                    styles={
                                        "padding": "30px",
                                        "backgroundColor": "#f8f9fa",
                                        "borderRadius": "8px"
                                    },
                                    children=[
                                        Component(
                                            id="feature3_title",
                                            type="heading",
                                            content="Accessibility",
                                            properties={"level": 3}
                                        ),
                                        Component(
                                            id="feature3_text",
                                            type="text",
                                            content="WCAG compliant with semantic HTML and ARIA."
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    ]
    
    return Project(
        id="landing-page-demo",
        name="Landing Page Demo",
        components=components,
        assets=[],
        metadata={
            "title": "Canvas Export Demo",
            "description": "A demonstration of Canvas export capabilities",
            "author": "Canvas Team"
        }
    )


async def export_html_example():
    """Export to HTML format"""
    
    print("\n=== HTML Export Example ===")
    
    # Create project
    project = create_sample_project()
    
    # Create export pipeline
    pipeline = ExportPipeline()
    
    # Configure HTML export
    config = ExportConfig(
        format=ExportFormat.HTML,
        output_path=Path("./exports/html"),
        options=ExportOptions(
            single_file=False,
            include_source_maps=False,
            minify_code=True,
            include_readme=True
        ),
        optimization=OptimizationSettings(
            minify_html=True,
            minify_css=True,
            minify_js=True,
            optimize_images=True,
            purge_unused_css=True
        )
    )
    
    # Export
    print(f"Exporting to {config.output_path}...")
    result = await pipeline.export(project, config)
    
    if result.success:
        print(f"✓ Export successful!")
        print(f"  Files generated: {result.report.files_generated}")
        print(f"  Total size: {result.report.total_size_bytes / 1024:.1f} KB")
        print(f"  Duration: {result.duration:.2f}s")
    else:
        print(f"✗ Export failed!")
        for error in result.errors:
            print(f"  - {error}")


async def export_react_example():
    """Export to React format"""
    
    print("\n=== React Export Example ===")
    
    project = create_sample_project()
    pipeline = ExportPipeline()
    
    # Use production preset for React
    config = ExportConfig.from_preset(
        ExportPreset.PRODUCTION,
        ExportFormat.REACT,
        Path("./exports/react")
    )
    
    # Customize options
    config.options.typescript = True
    config.options.state_management = True
    config.options.include_tests = True
    
    print(f"Exporting to {config.output_path}...")
    result = await pipeline.export(project, config)
    
    if result.success:
        print(f"✓ Export successful!")
        print(f"  TypeScript: {config.options.typescript}")
        print(f"  State Management: {config.options.state_management}")
        print(f"  Tests Included: {config.options.include_tests}")
        
        # Show file breakdown
        print("\n  File types generated:")
        for ext, count in result.report.file_breakdown.items():
            print(f"    {ext}: {count} files")
    else:
        print(f"✗ Export failed!")
        for error in result.errors:
            print(f"  - {error}")


async def export_vue_example():
    """Export to Vue format"""
    
    print("\n=== Vue Export Example ===")
    
    project = create_sample_project()
    pipeline = ExportPipeline()
    
    # Configure Vue export
    config = ExportConfig(
        format=ExportFormat.VUE,
        output_path=Path("./exports/vue"),
        options=ExportOptions(
            typescript=False,
            state_management=True,
            include_package_json=True,
            include_readme=True
        )
    )
    
    # Track progress
    def progress_callback(phase):
        print(f"  Progress: {phase.description} ({phase.progress * 100:.0f}%)")
    
    pipeline.progress_tracker.register_callback("example", progress_callback)
    
    print(f"Exporting to {config.output_path}...")
    result = await pipeline.export(project, config)
    
    if result.success:
        print(f"✓ Export successful!")
        
        # Show warnings if any
        if result.warnings:
            print("\n  Warnings:")
            for warning in result.warnings:
                print(f"    ⚠ {warning}")
        
        # Show performance hints
        if result.report.performance_hints:
            print("\n  Performance hints:")
            for hint in result.report.performance_hints:
                print(f"    💡 {hint}")
    else:
        print(f"✗ Export failed!")
        for error in result.errors:
            print(f"  - {error}")


async def main():
    """Run all export examples"""
    
    print("Canvas Export System Examples")
    print("============================")
    
    # Run examples
    await export_html_example()
    await export_react_example()
    await export_vue_example()
    
    print("\n✨ All examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())