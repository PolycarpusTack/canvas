"""
Export Result and Report Classes

CLAUDE.md Implementation:
- #4.1: Explicit types for all fields
- #1.2: DRY with shared result structures
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .export_config import ExportFormat


@dataclass
class ExportResult:
    """
    Result of an export operation
    
    CLAUDE.md #4.1: Explicit typing
    """
    success: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Success data
    report: Optional['ExportReport'] = None
    output_path: Optional[Path] = None
    files_generated: List[str] = field(default_factory=list)
    
    # Timing
    duration: float = 0.0  # seconds
    
    # Debug info
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, error: str):
        """Add error message"""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str):
        """Add warning message"""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'success': self.success,
            'errors': self.errors,
            'warnings': self.warnings,
            'output_path': str(self.output_path) if self.output_path else None,
            'files_generated': self.files_generated,
            'duration': self.duration,
            'metadata': self.metadata
        }


@dataclass
class ExportReport:
    """
    Detailed export report
    
    CLAUDE.md #12.3: Comprehensive reporting
    """
    success: bool
    format: ExportFormat
    output_path: Path
    
    # File statistics
    files_generated: int
    assets_processed: int
    total_size_bytes: int
    
    # Issues
    warnings: List[str] = field(default_factory=list)
    
    # Optimization results
    optimization_applied: Dict[str, bool] = field(default_factory=dict)
    size_reduction_percentage: float = 0.0
    
    # File breakdown
    file_breakdown: Dict[str, int] = field(default_factory=dict)  # extension -> count
    
    # Performance
    performance_hints: List[str] = field(default_factory=list)
    lighthouse_estimates: Dict[str, int] = field(default_factory=dict)
    
    # Timing breakdown
    phase_timings: Dict[str, float] = field(default_factory=dict)
    
    # Generated at
    generated_at: datetime = field(default_factory=datetime.now)
    
    def get_formatted_size(self) -> str:
        """Get human-readable file size"""
        size = self.total_size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def get_summary(self) -> str:
        """Get text summary of report"""
        lines = [
            f"Export Report - {self.format.display_name}",
            f"Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"Output Path: {self.output_path}",
            f"Files Generated: {self.files_generated}",
            f"Assets Processed: {self.assets_processed}",
            f"Total Size: {self.get_formatted_size()}",
            ""
        ]
        
        if self.optimization_applied:
            lines.append("Optimizations Applied:")
            for opt, applied in self.optimization_applied.items():
                status = "✓" if applied else "✗"
                lines.append(f"  {status} {opt}")
            if self.size_reduction_percentage > 0:
                lines.append(f"  Size reduced by {self.size_reduction_percentage:.1f}%")
            lines.append("")
        
        if self.file_breakdown:
            lines.append("File Breakdown:")
            for ext, count in sorted(self.file_breakdown.items()):
                lines.append(f"  {ext}: {count} files")
            lines.append("")
        
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for warning in self.warnings[:5]:  # Show first 5
                lines.append(f"  - {warning}")
            if len(self.warnings) > 5:
                lines.append(f"  ... and {len(self.warnings) - 5} more")
            lines.append("")
        
        if self.performance_hints:
            lines.append("Performance Recommendations:")
            for hint in self.performance_hints:
                lines.append(f"  • {hint}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'success': self.success,
            'format': self.format.value,
            'output_path': str(self.output_path),
            'files_generated': self.files_generated,
            'assets_processed': self.assets_processed,
            'total_size': self.get_formatted_size(),
            'total_size_bytes': self.total_size_bytes,
            'warnings': self.warnings,
            'optimization_applied': self.optimization_applied,
            'size_reduction_percentage': self.size_reduction_percentage,
            'file_breakdown': self.file_breakdown,
            'performance_hints': self.performance_hints,
            'lighthouse_estimates': self.lighthouse_estimates,
            'generated_at': self.generated_at.isoformat()
        }
    
    def save_to_file(self, path: Path):
        """Save report to file"""
        import json
        
        report_data = self.to_dict()
        report_data['summary'] = self.get_summary()
        
        with open(path, 'w') as f:
            json.dumps(report_data, indent=2)


@dataclass
class FileGenerationResult:
    """Result of generating a single file"""
    path: str
    content: str
    size: int
    encoding: str = "utf-8"
    binary: bool = False
    
    def __post_init__(self):
        """Calculate size if not provided"""
        if not self.size:
            if self.binary:
                self.size = len(self.content) if isinstance(self.content, bytes) else 0
            else:
                self.size = len(self.content.encode(self.encoding))


@dataclass 
class AssetProcessingResult:
    """Result of processing an asset"""
    original_path: str
    processed_path: str
    original_size: int
    processed_size: int
    format: str
    optimization_applied: bool = False
    variants: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def size_reduction(self) -> float:
        """Calculate size reduction percentage"""
        if self.original_size == 0:
            return 0.0
        return ((self.original_size - self.processed_size) / self.original_size) * 100