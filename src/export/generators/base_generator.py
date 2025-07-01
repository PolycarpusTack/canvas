"""
Base Generator Class

CLAUDE.md Implementation:
- #1.4: Extensible base for all generators
- #2.1.1: Common validation methods
- #12.1: Structured logging
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging

from ..export_context import ExportContext

logger = logging.getLogger(__name__)


class BaseGenerator(ABC):
    """
    Abstract base class for all code generators
    
    CLAUDE.md #1.4: Extensible architecture
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def generate(self, context: ExportContext) -> Dict[str, str]:
        """
        Generate files for the target format
        
        Args:
            context: Export context with project data
            
        Returns:
            Dictionary mapping file paths to file contents
        """
        pass
    
    def validate_context(self, context: ExportContext) -> bool:
        """
        Validate export context before generation
        
        CLAUDE.md #2.1.1: Common validation
        """
        if not context.project:
            self.logger.error("No project in export context")
            return False
        
        if not context.project.components:
            self.logger.warning("No components to export")
        
        return True
    
    def get_file_extension(self, file_type: str, context: ExportContext) -> str:
        """Get file extension based on configuration"""
        extensions = {
            "javascript": ".tsx" if context.config.options.use_typescript else ".jsx",
            "style": ".scss" if context.config.options.use_sass else ".css",
            "config": ".json"
        }
        return extensions.get(file_type, "")
    
    def log_generation_start(self, format_name: str):
        """Log generation start"""
        self.logger.info(f"Starting {format_name} generation")
    
    def log_generation_complete(self, file_count: int):
        """Log generation completion"""
        self.logger.info(f"Generation complete: {file_count} files created")