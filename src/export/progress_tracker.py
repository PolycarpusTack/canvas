"""
Progress Tracker for Export Operations

CLAUDE.md Implementation:
- #12.3: Progress monitoring
- #6.1: Clear progress state management
"""

import time
import logging
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PhaseProgress:
    """Progress information for a single phase"""
    name: str
    description: str
    start_time: float
    end_time: Optional[float] = None
    progress: float = 0.0  # 0.0 to 1.0
    completed: bool = False
    error: Optional[str] = None


class ProgressTracker:
    """
    Track export progress across multiple phases
    
    CLAUDE.md #12.3: Detailed progress monitoring
    """
    
    def __init__(self):
        self.phases: Dict[str, PhaseProgress] = {}
        self.current_phase: Optional[str] = None
        self.total_phases: int = 0
        self.start_time: float = time.time()
        self.callbacks: Dict[str, Callable[[PhaseProgress], None]] = {}
        
        # Metrics
        self.files_written: int = 0
        self.assets_processed: int = 0
        self.bytes_written: int = 0
    
    def reset(self):
        """Reset tracker for new export"""
        self.phases.clear()
        self.current_phase = None
        self.total_phases = 0
        self.start_time = time.time()
        self.files_written = 0
        self.assets_processed = 0
        self.bytes_written = 0
    
    def set_total_phases(self, count: int):
        """Set total number of phases"""
        self.total_phases = count
    
    def start_phase(self, phase_name: str, description: str = ""):
        """Start a new phase"""
        # Complete previous phase if any
        if self.current_phase:
            self.complete_phase(self.current_phase)
        
        # Start new phase
        self.phases[phase_name] = PhaseProgress(
            name=phase_name,
            description=description,
            start_time=time.time()
        )
        self.current_phase = phase_name
        
        logger.info(f"Started phase: {phase_name} - {description}")
        self._notify_callbacks(phase_name)
    
    def update_progress(self, progress: float):
        """Update progress for current phase (0.0 to 1.0)"""
        if self.current_phase and self.current_phase in self.phases:
            phase = self.phases[self.current_phase]
            phase.progress = max(0.0, min(1.0, progress))
            self._notify_callbacks(self.current_phase)
    
    def complete_phase(self, phase_name: Optional[str] = None):
        """Mark phase as completed"""
        phase_name = phase_name or self.current_phase
        if phase_name and phase_name in self.phases:
            phase = self.phases[phase_name]
            phase.end_time = time.time()
            phase.progress = 1.0
            phase.completed = True
            
            duration = phase.end_time - phase.start_time
            logger.info(f"Completed phase: {phase_name} in {duration:.2f}s")
            self._notify_callbacks(phase_name)
    
    def fail_phase(self, error: str, phase_name: Optional[str] = None):
        """Mark phase as failed"""
        phase_name = phase_name or self.current_phase
        if phase_name and phase_name in self.phases:
            phase = self.phases[phase_name]
            phase.end_time = time.time()
            phase.error = error
            phase.completed = False
            
            logger.error(f"Phase failed: {phase_name} - {error}")
            self._notify_callbacks(phase_name)
    
    def complete(self):
        """Complete all tracking"""
        if self.current_phase:
            self.complete_phase(self.current_phase)
        
        total_duration = time.time() - self.start_time
        logger.info(
            f"Export completed in {total_duration:.2f}s - "
            f"{self.files_written} files, {self.assets_processed} assets, "
            f"{self.bytes_written / 1024 / 1024:.2f}MB written"
        )
    
    def increment_files_written(self, bytes_written: int = 0):
        """Increment files written counter"""
        self.files_written += 1
        self.bytes_written += bytes_written
    
    def increment_assets_processed(self):
        """Increment assets processed counter"""
        self.assets_processed += 1
    
    def get_overall_progress(self) -> float:
        """Get overall progress (0.0 to 1.0)"""
        if self.total_phases == 0:
            return 0.0
        
        completed_phases = sum(
            1 for phase in self.phases.values()
            if phase.completed
        )
        
        current_phase_progress = 0.0
        if self.current_phase and self.current_phase in self.phases:
            current_phase_progress = self.phases[self.current_phase].progress
        
        return (completed_phases + current_phase_progress) / self.total_phases
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return time.time() - self.start_time
    
    def get_estimated_time_remaining(self) -> Optional[float]:
        """Estimate time remaining in seconds"""
        progress = self.get_overall_progress()
        if progress <= 0:
            return None
        
        elapsed = self.get_elapsed_time()
        total_estimated = elapsed / progress
        remaining = total_estimated - elapsed
        
        return max(0, remaining)
    
    def register_callback(self, name: str, callback: Callable[[PhaseProgress], None]):
        """Register progress callback"""
        self.callbacks[name] = callback
    
    def unregister_callback(self, name: str):
        """Unregister progress callback"""
        self.callbacks.pop(name, None)
    
    def _notify_callbacks(self, phase_name: str):
        """Notify all registered callbacks"""
        if phase_name in self.phases:
            phase = self.phases[phase_name]
            for callback in self.callbacks.values():
                try:
                    callback(phase)
                except Exception as e:
                    logger.error(f"Progress callback error: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get progress summary"""
        return {
            'overall_progress': self.get_overall_progress(),
            'elapsed_time': self.get_elapsed_time(),
            'estimated_remaining': self.get_estimated_time_remaining(),
            'current_phase': self.current_phase,
            'completed_phases': [
                name for name, phase in self.phases.items()
                if phase.completed
            ],
            'files_written': self.files_written,
            'assets_processed': self.assets_processed,
            'bytes_written': self.bytes_written,
            'phase_details': {
                name: {
                    'description': phase.description,
                    'progress': phase.progress,
                    'completed': phase.completed,
                    'duration': (phase.end_time - phase.start_time) if phase.end_time else None,
                    'error': phase.error
                }
                for name, phase in self.phases.items()
            }
        }
    
    def format_progress_bar(self, width: int = 50) -> str:
        """Format a text progress bar"""
        progress = self.get_overall_progress()
        filled = int(width * progress)
        empty = width - filled
        
        bar = f"[{'=' * filled}{' ' * empty}]"
        percentage = f"{progress * 100:.1f}%"
        
        return f"{bar} {percentage}"
    
    def format_status(self) -> str:
        """Format current status message"""
        if self.current_phase and self.current_phase in self.phases:
            phase = self.phases[self.current_phase]
            return f"{phase.description} ({phase.progress * 100:.0f}%)"
        
        return "Preparing..."