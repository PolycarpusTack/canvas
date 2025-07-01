"""
Export Pipeline Core Implementation

CLAUDE.md Implementation:
- #2.1.4: Resource management with transactions
- #12.1: Structured logging throughout
- #1.2: DRY principle for generators
- #2.1.3: Retry logic for resilience
"""

import asyncio
import traceback
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import tempfile
import json

from ..models.project_enhanced import Project
from ..models.component_enhanced import Component
from .export_config import (
    ExportConfig, ExportFormat, ValidationResult,
    OptimizationSettings
)
from .export_context import ExportContext
from .export_result import ExportResult, ExportReport
from .export_transaction import ExportTransaction
from .export_validator import ExportValidator
from .progress_tracker import ProgressTracker

# Import generators
from .generators.html_generator import HTMLGenerator
from .generators.react_generator import ReactGenerator
from .generators.vue_generator import VueGenerator
from .generators.base_generator import BaseGenerator

# Import processors
from .processors.asset_processor import AssetProcessor
from .processors.code_optimizer import CodeOptimizer

logger = logging.getLogger(__name__)


class ExportPipeline:
    """
    Main export pipeline with transaction support
    
    CLAUDE.md Implementation:
    - #2.1.4: Resource management with transactions
    - #12.1: Structured logging
    - #1.2: DRY principle for generators
    """
    
    def __init__(self):
        # Initialize logger
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize generators
        self.generators: Dict[ExportFormat, BaseGenerator] = {
            ExportFormat.HTML: HTMLGenerator(),
            ExportFormat.REACT: ReactGenerator(),
            ExportFormat.VUE: VueGenerator(),
            # More generators can be added here
        }
        
        # Initialize processors
        self.asset_processor = AssetProcessor()
        self.code_optimizer = CodeOptimizer()
        self.validator = ExportValidator()
        self.progress_tracker = ProgressTracker()
        
        # Configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
    
    async def export(
        self, 
        project: Project, 
        config: ExportConfig
    ) -> ExportResult:
        """
        Main export method with transaction support
        
        CLAUDE.md #2.1.3: Implement retry logic
        """
        start_time = datetime.now()
        
        # Initialize progress tracking
        self.progress_tracker.reset()
        self.progress_tracker.set_total_phases(7)
        
        # Create transaction context
        transaction = ExportTransaction(config.output_path)
        
        try:
            # Phase 1: Validation
            self.progress_tracker.start_phase("validation", "Validating project...")
            validation = await self._validate_project(project, config)
            if not validation.is_valid:
                return ExportResult(
                    success=False,
                    errors=validation.errors,
                    warnings=validation.warnings,
                    duration=(datetime.now() - start_time).total_seconds()
                )
            
            # Phase 2: Preparation
            self.progress_tracker.start_phase("preparation", "Preparing export context...")
            context = await self._prepare_export_context(project, config)
            
            # Phase 3: Code Generation
            self.progress_tracker.start_phase("generation", "Generating code...")
            generator = self.generators.get(config.format)
            if not generator:
                raise ValueError(f"Unsupported format: {config.format}")
            
            files = await self._generate_with_retry(generator, context)
            
            # Phase 4: Asset Processing
            self.progress_tracker.start_phase("assets", "Processing assets...")
            assets = await self._process_assets_parallel(
                project.assets,
                config.optimization
            )
            
            # Phase 5: Optimization
            if config.options.minify_code or config.optimization.minify_html:
                self.progress_tracker.start_phase("optimization", "Optimizing code...")
                files = await self._optimize_code(files, config)
            
            # Phase 6: Write Output
            self.progress_tracker.start_phase("writing", "Writing files...")
            await self._write_output_transactional(
                transaction,
                files,
                assets,
                config
            )
            
            # Phase 7: Generate Report
            self.progress_tracker.start_phase("reporting", "Generating report...")
            report = self._generate_export_report(
                files,
                assets,
                config,
                context,
                validation.warnings
            )
            
            # Commit transaction
            await transaction.commit()
            
            # Calculate final metrics
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Export completed successfully",
                extra={
                    "format": config.format.value,
                    "duration": duration,
                    "files_count": len(files),
                    "assets_count": len(assets),
                    "output_path": str(config.output_path)
                }
            )
            
            return ExportResult(
                success=True,
                report=report,
                output_path=config.output_path,
                duration=duration,
                files_generated=list(files.keys()),
                metadata={
                    "format": config.format.value,
                    "timestamp": datetime.now().isoformat(),
                    "project_name": project.name
                }
            )
            
        except Exception as e:
            # Rollback on any error
            await transaction.rollback()
            
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            
            logger.error(
                f"Export failed: {error_msg}",
                exc_info=True,
                extra={
                    "format": config.format.value,
                    "output_path": str(config.output_path)
                }
            )
            
            return ExportResult(
                success=False,
                errors=[error_msg],
                stack_trace=stack_trace,
                duration=(datetime.now() - start_time).total_seconds()
            )
            
        finally:
            # Cleanup
            await transaction.cleanup()
            self.progress_tracker.complete()
    
    async def _validate_project(
        self,
        project: Project,
        config: ExportConfig
    ) -> ValidationResult:
        """Validate project before export"""
        # Config validation
        config_result = config.validate()
        if not config_result.is_valid:
            return config_result
        
        # Project validation
        project_result = await self.validator.validate_project(project, config)
        
        # Merge results
        config_result.merge(project_result)
        
        return config_result
    
    async def _prepare_export_context(
        self,
        project: Project,
        config: ExportConfig
    ) -> ExportContext:
        """Prepare export context with all necessary data"""
        context = ExportContext(
            project=project,
            config=config,
            timestamp=datetime.now()
        )
        
        # Analyze component tree
        context.component_tree = self._build_component_tree(project.components)
        
        # Extract reusable components
        context.reusable_components = self._extract_reusable_components(
            project.components
        )
        
        # Prepare asset mappings
        context.asset_map = self._build_asset_map(project.assets)
        
        # Calculate responsive breakpoints
        context.breakpoints = self._extract_breakpoints(project.components)
        
        # Prepare route information
        if project.pages:
            context.routes = self._build_route_map(project.pages)
        
        return context
    
    async def _generate_with_retry(
        self,
        generator: BaseGenerator,
        context: ExportContext
    ) -> Dict[str, str]:
        """
        Generate code with retry logic
        
        CLAUDE.md #2.1.3: Exponential backoff retry
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return await generator.generate(context)
                
            except Exception as e:
                last_error = e
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Generation failed, retrying in {delay}s",
                        extra={
                            "attempt": attempt + 1,
                            "error": str(e)
                        }
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error("Generation failed after all retries")
        
        raise last_error
    
    async def _process_assets_parallel(
        self,
        assets: List[Any],
        optimization: OptimizationSettings
    ) -> Dict[str, Any]:
        """
        Process assets in parallel
        
        CLAUDE.md #1.5: Performance optimization
        """
        if not assets:
            return {}
        
        # Create tasks for parallel processing
        tasks = []
        for asset in assets:
            task = self.asset_processor.process_asset(asset, optimization)
            tasks.append(task)
        
        # Process in batches to avoid overwhelming system
        batch_size = 10
        processed_assets = {}
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            results = await asyncio.gather(*batch, return_exceptions=True)
            
            for asset, result in zip(assets[i:i + batch_size], results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to process asset {asset.name}: {result}")
                else:
                    processed_assets[asset.id] = result
            
            # Update progress
            self.progress_tracker.update_progress(
                (i + len(batch)) / len(tasks)
            )
        
        return processed_assets
    
    async def _optimize_code(
        self,
        files: Dict[str, str],
        config: ExportConfig
    ) -> Dict[str, str]:
        """Optimize generated code"""
        optimized = {}
        
        for path, content in files.items():
            try:
                # Determine file type
                if path.endswith('.html'):
                    optimized[path] = await self.code_optimizer.optimize_html(
                        content,
                        config.optimization
                    )
                elif path.endswith('.css'):
                    optimized[path] = await self.code_optimizer.optimize_css(
                        content,
                        config.optimization
                    )
                elif path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    optimized[path] = await self.code_optimizer.optimize_js(
                        content,
                        config.optimization
                    )
                else:
                    # No optimization for other files
                    optimized[path] = content
                    
            except Exception as e:
                logger.warning(f"Failed to optimize {path}: {e}")
                optimized[path] = content  # Use original on failure
        
        return optimized
    
    async def _write_output_transactional(
        self,
        transaction: ExportTransaction,
        files: Dict[str, str],
        assets: Dict[str, Any],
        config: ExportConfig
    ) -> None:
        """
        Write output files transactionally
        
        CLAUDE.md #2.1.4: Atomic file operations
        """
        # Write code files
        for path, content in files.items():
            await transaction.write_file(path, content)
            self.progress_tracker.increment_files_written()
        
        # Write processed assets
        for asset_id, asset_data in assets.items():
            if isinstance(asset_data, dict) and "path" in asset_data:
                await transaction.write_file(
                    asset_data["path"],
                    asset_data["content"]
                )
                self.progress_tracker.increment_files_written()
        
        # Write metadata
        metadata = {
            "export_config": config.to_dict(),
            "export_date": datetime.now().isoformat(),
            "generator_version": "1.0.0",
            "files": list(files.keys()),
            "assets": list(assets.keys())
        }
        
        await transaction.write_file(
            ".canvas-export.json",
            json.dumps(metadata, indent=2)
        )
    
    def _generate_export_report(
        self,
        files: Dict[str, str],
        assets: Dict[str, Any],
        config: ExportConfig,
        context: ExportContext,
        warnings: List[str]
    ) -> ExportReport:
        """Generate detailed export report"""
        # Calculate sizes
        total_size = sum(len(content) for content in files.values())
        
        # Count file types
        file_types = {}
        for path in files:
            ext = Path(path).suffix or "no extension"
            file_types[ext] = file_types.get(ext, 0) + 1
        
        return ExportReport(
            success=True,
            format=config.format,
            output_path=config.output_path,
            files_generated=len(files),
            assets_processed=len(assets),
            total_size_bytes=total_size,
            warnings=warnings,
            optimization_applied={
                "html_minified": config.optimization.minify_html,
                "css_minified": config.optimization.minify_css,
                "js_minified": config.optimization.minify_js,
                "images_optimized": config.optimization.optimize_images
            },
            file_breakdown=file_types,
            performance_hints=self._generate_performance_hints(context, config)
        )
    
    def _build_component_tree(self, components: List[Component]) -> Dict[str, Any]:
        """Build hierarchical component tree"""
        tree = {}
        component_map = {comp.id: comp for comp in components}
        
        # Build tree structure
        for component in components:
            if not component.parent_id:
                # Root component
                tree[component.id] = self._build_subtree(
                    component,
                    component_map
                )
        
        return tree
    
    def _build_subtree(
        self,
        component: Component,
        component_map: Dict[str, Component]
    ) -> Dict[str, Any]:
        """Recursively build component subtree"""
        node = {
            "component": component,
            "children": []
        }
        
        # Find children
        for comp in component_map.values():
            if comp.parent_id == component.id:
                child_node = self._build_subtree(comp, component_map)
                node["children"].append(child_node)
        
        return node
    
    def _extract_reusable_components(
        self,
        components: List[Component]
    ) -> List[Component]:
        """Identify components that should be extracted as reusable"""
        reusable = []
        
        # Count component usage
        type_counts = {}
        for comp in components:
            key = (comp.type, tuple(sorted(comp.properties.items())))
            type_counts[key] = type_counts.get(key, 0) + 1
        
        # Extract components used multiple times
        seen = set()
        for comp in components:
            key = (comp.type, tuple(sorted(comp.properties.items())))
            if type_counts[key] > 2 and key not in seen:
                reusable.append(comp)
                seen.add(key)
        
        return reusable
    
    def _build_asset_map(self, assets: List[Any]) -> Dict[str, Any]:
        """Build asset ID to asset mapping"""
        return {asset.id: asset for asset in assets}
    
    def _extract_breakpoints(self, components: List[Component]) -> List[int]:
        """Extract unique responsive breakpoints"""
        breakpoints = set()
        
        for comp in components:
            # Extract from responsive properties
            if hasattr(comp, "responsive_styles"):
                for bp in comp.responsive_styles:
                    breakpoints.add(bp)
        
        # Add default breakpoints if none found
        if not breakpoints:
            breakpoints = {576, 768, 992, 1200}  # Bootstrap defaults
        
        return sorted(breakpoints)
    
    def _build_route_map(self, pages: List[Any]) -> Dict[str, Any]:
        """Build routing information"""
        routes = {}
        
        for page in pages:
            routes[page.path] = {
                "name": page.name,
                "component": page.root_component_id,
                "title": page.title,
                "meta": page.meta_tags
            }
        
        return routes
    
    def _generate_performance_hints(
        self,
        context: ExportContext,
        config: ExportConfig
    ) -> List[str]:
        """Generate performance improvement hints"""
        hints = []
        
        # Check image optimization
        if not config.optimization.optimize_images:
            hints.append("Enable image optimization to reduce file sizes")
        
        # Check code splitting
        if len(context.project.components) > 100:
            hints.append("Consider code splitting for better performance")
        
        # Check CSS optimization
        if not config.optimization.purge_unused_css:
            hints.append("Enable CSS purging to remove unused styles")
        
        return hints
    
    async def _optimize_code(
        self,
        files: Dict[str, str],
        config: ExportConfig
    ) -> Dict[str, str]:
        """
        Optimize generated code
        
        CLAUDE.md #1.5: Performance optimization
        """
        try:
            # Use the code optimizer
            optimized_files, report = await self.code_optimizer.optimize_bundle(
                files,
                config.optimization
            )
            
            self.logger.info(
                f"Code optimization complete",
                extra={
                    "original_size": report["original_size"],
                    "optimized_size": report["optimized_size"],
                    "savings_percentage": report["savings_percentage"],
                    "techniques": report["techniques_applied"]
                }
            )
            
            return optimized_files
            
        except Exception as e:
            self.logger.error(f"Code optimization failed: {e}")
            # Return original files if optimization fails
            return files