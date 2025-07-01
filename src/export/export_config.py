"""
Export Configuration Models

CLAUDE.md Implementation:
- #2.1.1: Comprehensive validation for all configuration
- #4.1: Explicit types for all fields
- #7.1: Path traversal prevention
- #1.4: Extensible for future export formats
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import codecs
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """
    CLAUDE.md #4.1: Explicit enum for export formats
    """
    HTML = "html"
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    SVELTE = "svelte"
    WORDPRESS = "wordpress"
    STATIC_SITE = "static_site"
    NEXT_JS = "nextjs"
    GATSBY = "gatsby"
    ZIP = "zip"
    
    @property
    def display_name(self) -> str:
        """Get human-readable name"""
        return {
            self.HTML: "HTML/CSS/JS",
            self.REACT: "React",
            self.VUE: "Vue.js",
            self.ANGULAR: "Angular",
            self.SVELTE: "Svelte",
            self.WORDPRESS: "WordPress Theme",
            self.STATIC_SITE: "Static Site",
            self.NEXT_JS: "Next.js",
            self.GATSBY: "Gatsby",
            self.ZIP: "ZIP Archive"
        }.get(self, self.value)


class ComponentStyle(Enum):
    """Component generation style"""
    FUNCTIONAL = "functional"
    CLASS_BASED = "class"
    COMPOSITION_API = "composition"  # For Vue 3


class ImageFormat(Enum):
    """Output image formats"""
    ORIGINAL = "original"
    WEBP = "webp"
    AVIF = "avif"
    JPEG = "jpeg"
    PNG = "png"


class ValidationResult:
    """Validation result container"""
    def __init__(self, is_valid: bool = True, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata: Dict[str, Any] = {}
    
    def add_error(self, error: str):
        """Add error and mark invalid"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add warning without affecting validity"""
        self.warnings.append(warning)
    
    def merge(self, other: ValidationResult):
        """Merge another validation result"""
        self.is_valid = self.is_valid and other.is_valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.metadata.update(other.metadata)


@dataclass
class OptimizationSettings:
    """
    CLAUDE.md #1.5: Performance optimization settings
    """
    # Code optimization
    minify_html: bool = True
    minify_css: bool = True
    minify_js: bool = True
    remove_comments: bool = True
    tree_shake: bool = True
    
    # CSS optimization
    purge_unused_css: bool = True
    inline_critical_css: bool = True
    prefix_css: bool = True
    
    # JS optimization
    transpile_js: bool = True
    bundle_js: bool = True
    source_maps: bool = False
    
    # Image optimization
    optimize_images: bool = True
    image_quality: int = 85  # 1-100
    max_image_width: int = 2048
    generate_webp: bool = True
    generate_avif: bool = False
    lazy_load_images: bool = True
    
    # Performance
    enable_compression: bool = True
    enable_caching_headers: bool = True
    preload_fonts: bool = True
    prefetch_links: bool = True
    
    def validate(self) -> ValidationResult:
        """Validate optimization settings"""
        result = ValidationResult()
        
        if self.image_quality < 1 or self.image_quality > 100:
            result.add_error(f"Image quality must be between 1-100, got {self.image_quality}")
        
        if self.max_image_width < 100:
            result.add_warning(f"Max image width {self.max_image_width}px is very small")
        
        if self.source_maps and self.minify_js:
            result.add_warning("Source maps with minification increases file size")
        
        return result


@dataclass
class ExportOptions:
    """
    CLAUDE.md #1.4: Extensible export options
    """
    # General options
    minify_code: bool = True
    include_source_map: bool = False
    inline_styles: bool = False
    inline_scripts: bool = False
    preserve_comments: bool = False
    
    # Framework-specific
    use_typescript: bool = False
    use_sass: bool = False
    use_css_modules: bool = False
    component_style: ComponentStyle = ComponentStyle.FUNCTIONAL
    state_management: Optional[str] = None  # redux, mobx, vuex, etc.
    routing_library: Optional[str] = None  # react-router, vue-router, etc.
    
    # HTML options  
    doctype: str = "html5"
    viewport_meta: bool = True
    charset: str = "UTF-8"
    language: str = "en"
    title: str = "Canvas Export"
    favicon: Optional[str] = None
    
    # SEO options
    generate_sitemap: bool = True
    generate_robots_txt: bool = True
    meta_description: Optional[str] = None
    meta_keywords: Optional[List[str]] = None
    og_tags: bool = True
    twitter_cards: bool = True
    
    # Asset options
    optimize_images: bool = True
    image_format: ImageFormat = ImageFormat.WEBP
    embed_fonts: bool = True
    use_cdn: bool = False
    cdn_provider: Optional[str] = None  # cloudflare, unpkg, jsDelivr
    
    # Development options
    generate_readme: bool = True
    generate_tests: bool = False
    include_eslint: bool = True
    include_prettier: bool = True
    
    # Build options
    package_manager: str = "npm"  # npm, yarn, pnpm
    build_tool: Optional[str] = None  # webpack, vite, parcel
    
    # Accessibility
    include_skip_links: bool = True
    aria_live_regions: bool = True
    focus_visible_polyfill: bool = True
    
    def __post_init__(self):
        """Initialize with defaults"""
        if self.meta_keywords is None:
            self.meta_keywords = []
        
        # Auto-detect build tool based on framework
        if self.build_tool is None:
            if self.use_typescript:
                self.build_tool = "vite"
            else:
                self.build_tool = "webpack"
    
    def validate(self) -> ValidationResult:
        """
        CLAUDE.md #2.1.2: Comprehensive validation
        """
        result = ValidationResult()
        
        # Validate charset
        try:
            codecs.lookup(self.charset)
        except LookupError:
            result.add_error(f"Invalid charset: {self.charset}")
        
        # Validate component style compatibility
        if self.use_typescript and self.component_style == ComponentStyle.CLASS_BASED:
            if not self.state_management:
                result.add_warning("TypeScript class components work better with state management")
        
        # Validate package manager
        valid_managers = ["npm", "yarn", "pnpm"]
        if self.package_manager not in valid_managers:
            result.add_error(f"Invalid package manager: {self.package_manager}")
        
        # Validate CDN
        if self.use_cdn and not self.cdn_provider:
            result.add_error("CDN provider must be specified when use_cdn is True")
        
        return result


@dataclass
class ExportConfig:
    """
    Main export configuration
    CLAUDE.md #2.1.1: Validate all configuration
    CLAUDE.md #7.1: Path traversal prevention
    """
    format: ExportFormat
    output_path: Path
    options: ExportOptions = field(default_factory=ExportOptions)
    optimization: OptimizationSettings = field(default_factory=OptimizationSettings)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration on creation"""
        # Convert string path to Path object
        if isinstance(self.output_path, str):
            self.output_path = Path(self.output_path)
        
        self._validate_output_path()
        self._validate_format_compatibility()
        
        # Set default metadata
        if "created_at" not in self.metadata:
            self.metadata["created_at"] = datetime.now().isoformat()
        if "version" not in self.metadata:
            self.metadata["version"] = "1.0.0"
    
    def _validate_output_path(self) -> None:
        """
        CLAUDE.md #7.1: Path traversal prevention
        """
        # Resolve to absolute path
        try:
            abs_path = self.output_path.resolve()
        except Exception as e:
            raise ValueError(f"Invalid output path: {e}")
        
        # Check if path is safe
        if ".." in str(self.output_path):
            raise ValueError("Output path cannot contain parent references")
        
        # Check path components
        for part in self.output_path.parts:
            if part.startswith('.') and part != '.':
                raise ValueError(f"Hidden directories not allowed: {part}")
        
        # Ensure parent directory exists
        if not abs_path.parent.exists():
            raise ValueError(f"Parent directory does not exist: {abs_path.parent}")
        
        # Check write permissions
        if abs_path.exists():
            if not os.access(abs_path, os.W_OK):
                raise PermissionError(f"No write permission for: {abs_path}")
            if abs_path.is_file():
                raise ValueError(f"Output path is a file, not a directory: {abs_path}")
        else:
            # Check parent write permissions
            if not os.access(abs_path.parent, os.W_OK):
                raise PermissionError(f"No write permission for parent: {abs_path.parent}")
    
    def _validate_format_compatibility(self) -> None:
        """Validate format-specific options compatibility"""
        # React-specific validation
        if self.format == ExportFormat.REACT:
            if self.options.component_style == ComponentStyle.COMPOSITION_API:
                raise ValueError("Composition API is Vue-specific, not available for React")
        
        # Vue-specific validation
        elif self.format == ExportFormat.VUE:
            if self.options.component_style == ComponentStyle.CLASS_BASED:
                logger.warning("Class-based components are deprecated in Vue 3")
        
        # Static site validation
        elif self.format == ExportFormat.STATIC_SITE:
            if self.options.state_management:
                logger.warning("State management not applicable for static sites")
                self.options.state_management = None
    
    def validate(self) -> ValidationResult:
        """Comprehensive validation"""
        result = ValidationResult()
        
        # Validate options
        options_result = self.options.validate()
        result.merge(options_result)
        
        # Validate optimization
        optimization_result = self.optimization.validate()
        result.merge(optimization_result)
        
        # Cross-validation
        if self.options.inline_styles and self.optimization.inline_critical_css:
            result.add_warning("Both inline_styles and inline_critical_css enabled")
        
        # Add metadata
        result.metadata["format"] = self.format.value
        result.metadata["output_path"] = str(self.output_path)
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "format": self.format.value,
            "output_path": str(self.output_path),
            "options": {
                "minify_code": self.options.minify_code,
                "use_typescript": self.options.use_typescript,
                "component_style": self.options.component_style.value,
                "charset": self.options.charset,
                "language": self.options.language,
                # ... other options
            },
            "optimization": {
                "minify_html": self.optimization.minify_html,
                "optimize_images": self.optimization.optimize_images,
                "image_quality": self.optimization.image_quality,
                # ... other optimization settings
            },
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExportConfig:
        """Deserialize from dictionary"""
        options = ExportOptions(
            minify_code=data["options"].get("minify_code", True),
            use_typescript=data["options"].get("use_typescript", False),
            component_style=ComponentStyle(data["options"].get("component_style", "functional")),
            charset=data["options"].get("charset", "UTF-8"),
            language=data["options"].get("language", "en"),
        )
        
        optimization = OptimizationSettings(
            minify_html=data["optimization"].get("minify_html", True),
            optimize_images=data["optimization"].get("optimize_images", True),
            image_quality=data["optimization"].get("image_quality", 85),
        )
        
        return cls(
            format=ExportFormat(data["format"]),
            output_path=Path(data["output_path"]),
            options=options,
            optimization=optimization,
            metadata=data.get("metadata", {})
        )


@dataclass
class ExportPreset:
    """Predefined export configurations"""
    name: str
    description: str
    config: ExportConfig
    
    @staticmethod
    def get_presets() -> List[ExportPreset]:
        """Get all available presets"""
        return [
            ExportPreset(
                name="Modern React App",
                description="React with TypeScript, hooks, and modern tooling",
                config=ExportConfig(
                    format=ExportFormat.REACT,
                    output_path=Path("./export/react-app"),
                    options=ExportOptions(
                        use_typescript=True,
                        component_style=ComponentStyle.FUNCTIONAL,
                        build_tool="vite",
                        include_eslint=True,
                        include_prettier=True
                    )
                )
            ),
            ExportPreset(
                name="Vue 3 Composition",
                description="Vue 3 with Composition API and TypeScript",
                config=ExportConfig(
                    format=ExportFormat.VUE,
                    output_path=Path("./export/vue-app"),
                    options=ExportOptions(
                        use_typescript=True,
                        component_style=ComponentStyle.COMPOSITION_API,
                        build_tool="vite"
                    )
                )
            ),
            ExportPreset(
                name="Optimized Static Site",
                description="Static HTML/CSS/JS with maximum optimization",
                config=ExportConfig(
                    format=ExportFormat.HTML,
                    output_path=Path("./export/static-site"),
                    optimization=OptimizationSettings(
                        minify_html=True,
                        minify_css=True,
                        minify_js=True,
                        purge_unused_css=True,
                        inline_critical_css=True,
                        optimize_images=True,
                        generate_webp=True
                    )
                )
            )
        ]