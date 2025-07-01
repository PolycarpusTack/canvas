"""
Export System Module

Provides functionality to export Canvas projects to various formats:
- HTML/CSS/JS
- React
- Vue
- Angular
- And more...

CLAUDE.md Implementation:
- Complete export pipeline with validation
- Asset processing and optimization
- Multiple output formats
- Progress tracking
"""

from .export_config import (
    ExportConfig,
    ExportFormat,
    ExportOptions,
    OptimizationSettings,
    ComponentStyle,
    ImageFormat,
    ExportPreset,
    ValidationResult
)

from .export_pipeline import ExportPipeline
from .export_context import ExportContext
from .export_result import ExportResult, ExportReport
from .export_transaction import ExportTransaction, TransactionManager
from .export_validator import ExportValidator
from .progress_tracker import ProgressTracker

# Generators
from .generators.base_generator import BaseGenerator
from .generators.html_generator import HTMLGenerator
from .generators.react_generator import ReactGenerator
from .generators.vue_generator import VueGenerator

__all__ = [
    # Config
    'ExportConfig',
    'ExportFormat', 
    'ExportOptions',
    'OptimizationSettings',
    'ComponentStyle',
    'ImageFormat',
    'ExportPreset',
    'ValidationResult',
    
    # Core
    'ExportPipeline',
    'ExportContext',
    'ExportResult',
    'ExportReport',
    'ExportTransaction',
    'TransactionManager',
    'ExportValidator',
    'ProgressTracker',
    
    # Generators
    'BaseGenerator',
    'HTMLGenerator',
    'ReactGenerator',
    'VueGenerator'
]

# Version
__version__ = "1.0.0"