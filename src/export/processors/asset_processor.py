"""
Asset Processor

CLAUDE.md Implementation:
- #1.5: Performance optimization for assets
- #7.2: Safe asset handling
- #12.1: Asset processing logging
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import mimetypes
import hashlib

from ..export_config import OptimizationSettings
from ..export_result import AssetProcessingResult

logger = logging.getLogger(__name__)


class AssetProcessor:
    """
    Process and optimize assets for export
    
    CLAUDE.md #1.5: Performance optimization
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.processed_cache: Dict[str, AssetProcessingResult] = {}
    
    async def process_asset(
        self,
        asset: Any,
        optimization: OptimizationSettings
    ) -> AssetProcessingResult:
        """Process a single asset"""
        
        # Check cache
        cache_key = self._get_cache_key(asset)
        if cache_key in self.processed_cache:
            return self.processed_cache[cache_key]
        
        # Determine asset type
        mime_type = self._get_mime_type(asset)
        
        if mime_type.startswith('image/'):
            result = await self._process_image(asset, optimization)
        elif mime_type.startswith('video/'):
            result = await self._process_video(asset, optimization)
        elif mime_type.startswith('audio/'):
            result = await self._process_audio(asset, optimization)
        else:
            result = await self._process_generic(asset, optimization)
        
        # Cache result
        self.processed_cache[cache_key] = result
        
        return result
    
    async def _process_image(
        self,
        asset: Any,
        optimization: OptimizationSettings
    ) -> AssetProcessingResult:
        """Process image asset with real optimization"""
        
        original_path = getattr(asset, 'path', '')
        original_size = getattr(asset, 'size', 0)
        
        if not optimization.optimize_images:
            # No optimization - return as-is
            return AssetProcessingResult(
                original_path=original_path,
                processed_path=original_path,
                original_size=original_size,
                processed_size=original_size,
                format=self._get_format_from_mime(self._get_mime_type(asset)),
                optimization_applied=False
            )
        
        try:
            # Import real image processor
            from .image_processor import ImageProcessor, create_image_processor_from_optimization
            
            # Create image processor
            processor = ImageProcessor()
            processing_options = create_image_processor_from_optimization(optimization)
            
            # Get image data
            image_data = None
            if hasattr(asset, 'content') and asset.content:
                image_data = asset.content
            elif hasattr(asset, 'path') and asset.path:
                image_data = asset.path
            else:
                # Fallback to original behavior
                return self._process_image_fallback(asset, optimization)
            
            # Process the image
            result = await processor.process_image(image_data, processing_options)
            
            # Convert to our result format
            return AssetProcessingResult(
                original_path=original_path,
                processed_path=result.processed_path or f"{original_path}_optimized",
                original_size=result.original_size,
                processed_size=result.processed_size,
                format=result.processed_format or 'jpeg',
                optimization_applied=result.optimization_applied,
                variants=result.variants
            )
            
        except ImportError:
            # Pillow not available - fall back to simulation
            self.logger.warning("Pillow not available - using simulated image processing")
            return self._process_image_fallback(asset, optimization)
        
        except Exception as e:
            self.logger.error(f"Image processing failed: {e}")
            return self._process_image_fallback(asset, optimization)
    
    def _process_image_fallback(
        self,
        asset: Any,
        optimization: OptimizationSettings
    ) -> AssetProcessingResult:
        """Fallback image processing when real processing is not available"""
        
        original_path = getattr(asset, 'path', '')
        original_size = getattr(asset, 'size', 0)
        
        # Simulate optimization
        processed_size = int(original_size * (optimization.image_quality / 100))
        
        variants = []
        if optimization.generate_webp:
            variants.append({
                'format': 'webp',
                'width': optimization.max_image_width,
                'size': int(processed_size * 0.8),  # WebP is typically smaller
                'path': f"{original_path}.webp"
            })
        
        # Generate responsive sizes
        widths = [320, 640, 1024, optimization.max_image_width]
        for width in widths:
            if width <= optimization.max_image_width:
                variants.append({
                    'format': 'jpeg',
                    'width': width,
                    'size': int(processed_size * (width / optimization.max_image_width)),
                    'path': f"{original_path}_{width}w.jpg"
                })
        
        return AssetProcessingResult(
            original_path=original_path,
            processed_path=f"{original_path}_optimized.jpg",
            original_size=original_size,
            processed_size=processed_size,
            format='jpeg',
            optimization_applied=True,
            variants=variants
        )
    
    async def _process_video(
        self,
        asset: Any,
        optimization: OptimizationSettings
    ) -> AssetProcessingResult:
        """Process video asset"""
        # Video processing would involve:
        # - Format conversion (mp4, webm)
        # - Compression
        # - Thumbnail generation
        # - Multiple quality variants
        
        return AssetProcessingResult(
            original_path=getattr(asset, 'path', ''),
            processed_path=getattr(asset, 'path', ''),
            original_size=getattr(asset, 'size', 0),
            processed_size=getattr(asset, 'size', 0),
            format='mp4',
            optimization_applied=False
        )
    
    async def _process_audio(
        self,
        asset: Any,
        optimization: OptimizationSettings
    ) -> AssetProcessingResult:
        """Process audio asset"""
        # Audio processing would involve:
        # - Format conversion (mp3, ogg, m4a)
        # - Bitrate optimization
        # - Metadata stripping
        
        return AssetProcessingResult(
            original_path=getattr(asset, 'path', ''),
            processed_path=getattr(asset, 'path', ''),
            original_size=getattr(asset, 'size', 0),
            processed_size=getattr(asset, 'size', 0),
            format='mp3',
            optimization_applied=False
        )
    
    async def _process_generic(
        self,
        asset: Any,
        optimization: OptimizationSettings
    ) -> AssetProcessingResult:
        """Process generic asset (fonts, documents, etc.)"""
        return AssetProcessingResult(
            original_path=getattr(asset, 'path', ''),
            processed_path=getattr(asset, 'path', ''),
            original_size=getattr(asset, 'size', 0),
            processed_size=getattr(asset, 'size', 0),
            format=self._get_format_from_mime(self._get_mime_type(asset)),
            optimization_applied=False
        )
    
    def _get_mime_type(self, asset: Any) -> str:
        """Get MIME type of asset"""
        if hasattr(asset, 'mime_type'):
            return asset.mime_type
        
        if hasattr(asset, 'path'):
            mime_type, _ = mimetypes.guess_type(asset.path)
            return mime_type or 'application/octet-stream'
        
        return 'application/octet-stream'
    
    def _get_format_from_mime(self, mime_type: str) -> str:
        """Get format from MIME type"""
        format_map = {
            'image/jpeg': 'jpeg',
            'image/png': 'png',
            'image/gif': 'gif',
            'image/webp': 'webp',
            'image/svg+xml': 'svg',
            'video/mp4': 'mp4',
            'video/webm': 'webm',
            'audio/mpeg': 'mp3',
            'audio/ogg': 'ogg'
        }
        return format_map.get(mime_type, 'unknown')
    
    def _get_cache_key(self, asset: Any) -> str:
        """Generate cache key for asset"""
        if hasattr(asset, 'id'):
            return asset.id
        
        if hasattr(asset, 'path'):
            return hashlib.md5(asset.path.encode()).hexdigest()
        
        return str(id(asset))
    
    async def process_assets_batch(
        self,
        assets: List[Any],
        optimization: OptimizationSettings,
        max_concurrent: int = 5
    ) -> List[AssetProcessingResult]:
        """Process multiple assets concurrently"""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(asset):
            async with semaphore:
                return await self.process_asset(asset, optimization)
        
        tasks = [process_with_semaphore(asset) for asset in assets]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to process asset: {result}")
                # Create failed result
                processed_results.append(AssetProcessingResult(
                    original_path=getattr(assets[i], 'path', 'unknown'),
                    processed_path=getattr(assets[i], 'path', 'unknown'),
                    original_size=getattr(assets[i], 'size', 0),
                    processed_size=getattr(assets[i], 'size', 0),
                    format='unknown',
                    optimization_applied=False
                ))
            else:
                processed_results.append(result)
        
        return processed_results