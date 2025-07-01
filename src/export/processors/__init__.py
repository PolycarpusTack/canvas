"""
Export Processors Module

Contains asset processors and code optimizers.
"""

from .asset_processor import AssetProcessor
from .code_optimizer import CodeOptimizer

# Image processor is optional (requires Pillow)
try:
    from .image_processor import ImageProcessor, ImageProcessingOptions, ImageFormatConverter
    IMAGE_PROCESSING_AVAILABLE = True
    __all__ = [
        'AssetProcessor',
        'CodeOptimizer',
        'ImageProcessor',
        'ImageProcessingOptions', 
        'ImageFormatConverter'
    ]
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False
    __all__ = [
        'AssetProcessor',
        'CodeOptimizer'
    ]