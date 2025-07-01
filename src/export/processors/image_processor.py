"""
Real Image Processing Implementation

CLAUDE.md Implementation:
- #1.5: Performance optimization
- #7.2: Safe image handling
- #2.1.1: Comprehensive validation
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
import io
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

# Image processing will be available if Pillow is installed
try:
    from PIL import Image, ImageOpt, ImageFile
    from PIL.ExifTags import TAGS
    PILLOW_AVAILABLE = True
    
    # Enable loading of truncated images
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    
except ImportError:
    PILLOW_AVAILABLE = False
    Image = None

from ..export_config import OptimizationSettings
from ...models.asset import AssetProcessingResult

logger = logging.getLogger(__name__)


@dataclass
class ImageProcessingOptions:
    """Options for image processing operations"""
    
    # Quality settings
    jpeg_quality: int = 85
    webp_quality: int = 80
    avif_quality: int = 75
    
    # Resize settings
    max_width: int = 1920
    max_height: int = 1080
    maintain_aspect_ratio: bool = True
    
    # Format settings
    output_format: str = "webp"  # webp, jpeg, png, avif
    generate_fallback: bool = True
    progressive_jpeg: bool = True
    
    # Responsive settings
    generate_responsive: bool = True
    responsive_breakpoints: List[int] = None
    
    # Optimization settings
    strip_metadata: bool = True
    optimize: bool = True
    
    def __post_init__(self):
        if self.responsive_breakpoints is None:
            self.responsive_breakpoints = [320, 640, 1024, 1920]


class ImageProcessor:
    """
    Real image processing with Pillow
    
    CLAUDE.md #1.5: Optimized image processing
    """
    
    def __init__(self, max_workers: int = 4):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        if not PILLOW_AVAILABLE:
            self.logger.warning("Pillow not available - image processing will be limited")
    
    async def process_image(
        self,
        image_data: Union[bytes, str, Path],
        options: ImageProcessingOptions,
        output_path: Optional[Path] = None
    ) -> AssetProcessingResult:
        """
        Process a single image with optimization
        
        CLAUDE.md #7.2: Safe image processing
        """
        result = AssetProcessingResult()
        
        try:
            # Load image
            image, original_format, original_size = await self._load_image(image_data)
            if not image:
                result.error = "Failed to load image"
                return result
            
            result.original_format = original_format
            result.original_size = original_size
            
            # Validate image
            if not self._validate_image(image):
                result.error = "Image validation failed"
                return result
            
            # Process image
            processed_variants = await self._process_image_variants(image, options)
            
            # Generate primary output
            primary_variant = processed_variants[0] if processed_variants else None
            if primary_variant:
                result.processed_path = str(primary_variant['path'])
                result.processed_size = primary_variant['size']
                result.processed_format = primary_variant['format']
                result.optimization_applied = True
                result.variants = processed_variants
                result.success = True
            
            # Calculate compression ratio
            if result.original_size > 0:
                savings = result.original_size - result.processed_size
                result.compression_ratio = savings / result.original_size
            
            self.logger.info(
                f"Image processed: {result.original_size} -> {result.processed_size} bytes "
                f"({result.compression_ratio:.1%} reduction)"
            )
            
        except Exception as e:
            result.error = f"Image processing failed: {e}"
            self.logger.error(result.error, exc_info=True)
        
        return result
    
    async def _load_image(
        self, 
        image_data: Union[bytes, str, Path]
    ) -> Tuple[Optional[Any], str, int]:
        """
        Load image from various sources
        
        CLAUDE.md #7.2: Safe image loading
        """
        if not PILLOW_AVAILABLE:
            return None, "", 0
        
        try:
            image = None
            original_size = 0
            
            if isinstance(image_data, bytes):
                # Load from bytes
                image = await asyncio.get_event_loop().run_in_executor(
                    self.executor, Image.open, io.BytesIO(image_data)
                )
                original_size = len(image_data)
                
            elif isinstance(image_data, (str, Path)):
                # Load from file
                path = Path(image_data)
                if not path.exists():
                    self.logger.error(f"Image file not found: {path}")
                    return None, "", 0
                
                # Security check
                if not self._is_safe_image_path(path):
                    self.logger.error(f"Unsafe image path: {path}")
                    return None, "", 0
                
                original_size = path.stat().st_size
                image = await asyncio.get_event_loop().run_in_executor(
                    self.executor, Image.open, str(path)
                )
            
            if image:
                # Convert to RGB if necessary
                if image.mode in ('RGBA', 'LA', 'P'):
                    # For transparency, use white background
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    
                    if image.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', image.size, (255, 255, 255))
                        if image.mode == 'RGBA':
                            background.paste(image, mask=image.split()[-1])
                        else:
                            background.paste(image, mask=image.split()[-1])
                        image = background
                
                original_format = image.format or 'UNKNOWN'
                return image, original_format, original_size
            
        except Exception as e:
            self.logger.error(f"Failed to load image: {e}")
        
        return None, "", 0
    
    def _is_safe_image_path(self, path: Path) -> bool:
        """
        Validate image path for security
        
        CLAUDE.md #7.1: Path traversal prevention
        """
        # Check for path traversal
        if '..' in str(path):
            return False
        
        # Check file extension
        safe_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        if path.suffix.lower() not in safe_extensions:
            return False
        
        # Check file size (max 50MB)
        try:
            if path.stat().st_size > 50 * 1024 * 1024:
                return False
        except OSError:
            return False
        
        return True
    
    def _validate_image(self, image: Any) -> bool:
        """
        Validate loaded image
        
        CLAUDE.md #2.1.1: Image validation
        """
        if not image:
            return False
        
        # Check dimensions
        width, height = image.size
        if width <= 0 or height <= 0:
            return False
        
        # Check maximum dimensions (prevent memory issues)
        max_dimension = 10000
        if width > max_dimension or height > max_dimension:
            self.logger.warning(f"Image too large: {width}x{height}")
            return False
        
        # Check total pixels (prevent memory bombs)
        total_pixels = width * height
        max_pixels = 100_000_000  # 100 megapixels
        if total_pixels > max_pixels:
            self.logger.warning(f"Image has too many pixels: {total_pixels}")
            return False
        
        return True
    
    async def _process_image_variants(
        self,
        image: Any,
        options: ImageProcessingOptions
    ) -> List[Dict[str, Any]]:
        """Process image into multiple variants"""
        variants = []
        
        try:
            # Generate responsive variants
            if options.generate_responsive:
                for width in options.responsive_breakpoints:
                    variant = await self._create_responsive_variant(image, width, options)
                    if variant:
                        variants.append(variant)
            else:
                # Generate single optimized variant
                variant = await self._create_single_variant(image, options)
                if variant:
                    variants.append(variant)
            
        except Exception as e:
            self.logger.error(f"Failed to process image variants: {e}")
        
        return variants
    
    async def _create_responsive_variant(
        self,
        image: Any,
        target_width: int,
        options: ImageProcessingOptions
    ) -> Optional[Dict[str, Any]]:
        """Create a responsive variant at specific width"""
        try:
            # Calculate new dimensions
            original_width, original_height = image.size
            
            if target_width >= original_width:
                # Don't upscale
                new_width = original_width
                new_height = original_height
            else:
                # Calculate proportional height
                ratio = target_width / original_width
                new_width = target_width
                new_height = int(original_height * ratio)
            
            # Resize image
            resized_image = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            )
            
            # Save in requested format
            output_data = await self._save_image(resized_image, options)
            
            if output_data:
                return {
                    'width': new_width,
                    'height': new_height,
                    'format': options.output_format,
                    'size': len(output_data),
                    'data': output_data,
                    'path': f"image_{new_width}w.{options.output_format}",
                    'responsive': True
                }
            
        except Exception as e:
            self.logger.error(f"Failed to create responsive variant: {e}")
        
        return None
    
    async def _create_single_variant(
        self,
        image: Any,
        options: ImageProcessingOptions
    ) -> Optional[Dict[str, Any]]:
        """Create single optimized variant"""
        try:
            # Resize if needed
            processed_image = image
            original_width, original_height = image.size
            
            if (original_width > options.max_width or 
                original_height > options.max_height):
                
                # Calculate new dimensions maintaining aspect ratio
                ratio = min(
                    options.max_width / original_width,
                    options.max_height / original_height
                )
                
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                
                processed_image = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                )
            
            # Save optimized version
            output_data = await self._save_image(processed_image, options)
            
            if output_data:
                width, height = processed_image.size
                return {
                    'width': width,
                    'height': height,
                    'format': options.output_format,
                    'size': len(output_data),
                    'data': output_data,
                    'path': f"image.{options.output_format}",
                    'responsive': False
                }
            
        except Exception as e:
            self.logger.error(f"Failed to create single variant: {e}")
        
        return None
    
    async def _save_image(
        self,
        image: Any,
        options: ImageProcessingOptions
    ) -> Optional[bytes]:
        """Save image with optimization settings"""
        try:
            output_buffer = io.BytesIO()
            
            # Determine save parameters
            save_kwargs = {
                'format': options.output_format.upper(),
                'optimize': options.optimize
            }
            
            # Format-specific options
            if options.output_format.lower() == 'jpeg':
                save_kwargs.update({
                    'quality': options.jpeg_quality,
                    'progressive': options.progressive_jpeg
                })
            elif options.output_format.lower() == 'webp':
                save_kwargs.update({
                    'quality': options.webp_quality,
                    'method': 6  # Better compression
                })
            elif options.output_format.lower() == 'png':
                save_kwargs.update({
                    'compress_level': 9  # Maximum compression
                })
            
            # Strip metadata if requested
            if options.strip_metadata:
                # Create new image without EXIF data
                data = list(image.getdata())
                clean_image = Image.new(image.mode, image.size)
                clean_image.putdata(data)
                image = clean_image
            
            # Save image
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: image.save(output_buffer, **save_kwargs)
            )
            
            return output_buffer.getvalue()
            
        except Exception as e:
            self.logger.error(f"Failed to save image: {e}")
            return None
    
    async def get_image_info(self, image_data: Union[bytes, str, Path]) -> Dict[str, Any]:
        """Get information about an image without processing"""
        try:
            image, original_format, original_size = await self._load_image(image_data)
            
            if not image:
                return {}
            
            width, height = image.size
            
            info = {
                'width': width,
                'height': height,
                'format': original_format,
                'mode': image.mode,
                'size': original_size,
                'has_transparency': image.mode in ('RGBA', 'LA', 'P'),
                'animated': getattr(image, 'is_animated', False)
            }
            
            # Extract EXIF data if available
            if hasattr(image, '_getexif') and image._getexif():
                exif_data = {}
                for tag_id, value in image._getexif().items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = str(value)[:100]  # Limit value length
                info['exif'] = exif_data
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get image info: {e}")
            return {}
    
    def close(self):
        """Clean up resources"""
        if self.executor:
            self.executor.shutdown(wait=True)


class ImageFormatConverter:
    """Convert images between different formats"""
    
    @staticmethod
    async def convert_to_webp(
        image_data: bytes,
        quality: int = 80
    ) -> Optional[bytes]:
        """Convert image to WebP format"""
        if not PILLOW_AVAILABLE:
            return None
        
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            output_buffer = io.BytesIO()
            image.save(
                output_buffer,
                format='WEBP',
                quality=quality,
                method=6
            )
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"WebP conversion failed: {e}")
            return None
    
    @staticmethod
    async def create_srcset(
        image_data: bytes,
        breakpoints: List[int] = None
    ) -> List[Dict[str, Any]]:
        """Create responsive image srcset"""
        if breakpoints is None:
            breakpoints = [320, 640, 1024, 1920]
        
        if not PILLOW_AVAILABLE:
            return []
        
        srcset_images = []
        
        try:
            image = Image.open(io.BytesIO(image_data))
            original_width, original_height = image.size
            
            for width in breakpoints:
                if width <= original_width:
                    # Calculate proportional height
                    ratio = width / original_width
                    height = int(original_height * ratio)
                    
                    # Resize image
                    resized = image.resize((width, height), Image.Resampling.LANCZOS)
                    
                    # Save as WebP
                    output_buffer = io.BytesIO()
                    resized.save(
                        output_buffer,
                        format='WEBP',
                        quality=80,
                        method=6
                    )
                    
                    srcset_images.append({
                        'width': width,
                        'height': height,
                        'data': output_buffer.getvalue(),
                        'size': len(output_buffer.getvalue()),
                        'descriptor': f"{width}w"
                    })
            
        except Exception as e:
            logger.error(f"Srcset creation failed: {e}")
        
        return srcset_images


def create_image_processor_from_optimization(
    optimization: OptimizationSettings
) -> ImageProcessingOptions:
    """Create ImageProcessingOptions from export OptimizationSettings"""
    
    return ImageProcessingOptions(
        jpeg_quality=optimization.image_quality,
        webp_quality=max(optimization.image_quality - 5, 70),  # WebP can be lower quality
        max_width=optimization.max_image_width,
        max_height=optimization.max_image_width,  # Keep square aspect limit
        output_format="webp" if optimization.generate_webp else "jpeg",
        generate_fallback=True,
        generate_responsive=True,
        responsive_breakpoints=[320, 640, 1024, optimization.max_image_width],
        strip_metadata=True,
        optimize=optimization.optimize_images
    )