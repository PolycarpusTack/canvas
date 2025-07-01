"""
Export Validator

CLAUDE.md Implementation:
- #2.1.1: Comprehensive validation
- #9.1: Accessibility validation
- #5.4: Security validation
"""

import asyncio
import logging
from typing import List, Optional, Any, Dict
from pathlib import Path

from ..models.project_enhanced import Project
from ..models.component_enhanced import Component
from .export_config import ExportConfig, ValidationResult

logger = logging.getLogger(__name__)


class ExportValidator:
    """
    Comprehensive pre-export validation
    
    CLAUDE.md Implementation:
    - #2.1.1: Validate everything
    - #9.1: Accessibility validation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def validate_project(
        self,
        project: Project,
        config: ExportConfig
    ) -> ValidationResult:
        """Comprehensive validation before export"""
        
        errors = []
        warnings = []
        
        # Run all validators in parallel
        validators = [
            self._validate_structure(project),
            self._validate_assets(project),
            self._validate_accessibility(project),
            self._validate_seo(project),
            self._validate_performance(project, config),
            self._validate_security(project),
            self._validate_compatibility(project, config)
        ]
        
        results = await asyncio.gather(*validators, return_exceptions=True)
        
        # Aggregate results
        for result in results:
            if isinstance(result, Exception):
                errors.append(f"Validation error: {result}")
            else:
                errors.extend(result.errors)
                warnings.extend(result.warnings)
        
        # Create final result
        final_result = ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
        # Add metadata
        final_result.metadata.update({
            "component_count": len(project.components),
            "asset_count": len(getattr(project, 'assets', [])),
            "validation_timestamp": "now"
        })
        
        return final_result
    
    async def _validate_structure(self, project: Project) -> ValidationResult:
        """Validate project structure"""
        result = ValidationResult()
        
        # Check for empty project
        if not project.components:
            result.add_error("Project has no components to export")
            return result
        
        # Check for orphaned components
        component_ids = {comp.id for comp in project.components}
        for comp in project.components:
            if comp.parent_id and comp.parent_id not in component_ids:
                result.add_warning(f"Component '{comp.id}' references non-existent parent '{comp.parent_id}'")
        
        # Check for circular dependencies
        if self._has_circular_dependencies(project.components):
            result.add_error("Circular component dependencies detected")
        
        # Check component depth
        max_depth = self._calculate_max_depth(project.components)
        if max_depth > 20:
            result.add_warning(f"Component nesting depth ({max_depth}) may cause performance issues")
        
        return result
    
    async def _validate_assets(self, project: Project) -> ValidationResult:
        """Validate project assets"""
        result = ValidationResult()
        
        assets = getattr(project, 'assets', [])
        
        # Check asset references
        referenced_assets = self._get_referenced_assets(project.components)
        for asset_ref in referenced_assets:
            if not any(asset.id == asset_ref for asset in assets):
                result.add_error(f"Component references missing asset: {asset_ref}")
        
        # Check asset sizes
        total_size = 0
        for asset in assets:
            if hasattr(asset, 'size'):
                total_size += asset.size
                if asset.size > 10 * 1024 * 1024:  # 10MB
                    result.add_warning(f"Large asset detected: {asset.name} ({asset.size / 1024 / 1024:.1f}MB)")
        
        if total_size > 50 * 1024 * 1024:  # 50MB total
            result.add_warning(f"Total asset size ({total_size / 1024 / 1024:.1f}MB) may impact performance")
        
        # Check asset formats
        for asset in assets:
            if hasattr(asset, 'mime_type'):
                if asset.mime_type not in self._get_supported_mime_types():
                    result.add_warning(f"Unsupported asset type: {asset.mime_type}")
        
        return result
    
    async def _validate_accessibility(self, project: Project) -> ValidationResult:
        """
        Validate accessibility requirements
        
        CLAUDE.md #9.1: WCAG compliance checks
        """
        result = ValidationResult()
        
        for component in project.components:
            # Images need alt text
            if component.type == "image":
                if not component.properties.get("alt"):
                    result.add_error(
                        f"Image '{component.name or component.id}' missing alt text (WCAG 1.1.1)"
                    )
            
            # Form inputs need labels
            elif component.type in ["input", "textarea", "select"]:
                has_label = (
                    component.properties.get("aria-label") or
                    component.properties.get("aria-labelledby") or
                    self._has_associated_label(component, project.components)
                )
                if not has_label:
                    result.add_warning(
                        f"Form input '{component.name or component.id}' should have a label (WCAG 3.3.2)"
                    )
            
            # Buttons need accessible text
            elif component.type == "button":
                if not component.content and not component.properties.get("aria-label"):
                    result.add_error(
                        f"Button '{component.name or component.id}' missing accessible text (WCAG 4.1.2)"
                    )
            
            # Check heading hierarchy
            if component.type == "heading":
                level = component.properties.get("level", 2)
                if level < 1 or level > 6:
                    result.add_error(f"Invalid heading level: {level}")
            
            # Check color contrast
            if self._has_low_contrast(component):
                result.add_warning(
                    f"Low color contrast in '{component.name or component.id}' (WCAG 1.4.3)"
                )
        
        # Check for skip links
        has_skip_link = any(
            comp.properties.get("href", "").startswith("#") and
            "skip" in comp.properties.get("class", "").lower()
            for comp in project.components
            if comp.type == "link"
        )
        if not has_skip_link:
            result.add_warning("Consider adding skip navigation links for accessibility")
        
        return result
    
    async def _validate_seo(self, project: Project) -> ValidationResult:
        """Validate SEO requirements"""
        result = ValidationResult()
        
        # Check for meta information
        if not project.metadata.get("title"):
            result.add_warning("Project missing title for SEO")
        
        if not project.metadata.get("description"):
            result.add_warning("Project missing description for SEO")
        
        # Check heading structure
        h1_count = sum(
            1 for comp in project.components
            if comp.type == "heading" and comp.properties.get("level") == 1
        )
        
        if h1_count == 0:
            result.add_warning("No H1 heading found (important for SEO)")
        elif h1_count > 1:
            result.add_warning(f"Multiple H1 headings found ({h1_count}) - use only one per page")
        
        # Check image alt texts for SEO
        images_without_alt = [
            comp for comp in project.components
            if comp.type == "image" and not comp.properties.get("alt")
        ]
        if images_without_alt:
            result.add_warning(f"{len(images_without_alt)} images missing alt text (impacts SEO)")
        
        return result
    
    async def _validate_performance(self, project: Project, config: ExportConfig) -> ValidationResult:
        """Validate performance considerations"""
        result = ValidationResult()
        
        # Component count
        if len(project.components) > 1000:
            result.add_warning(f"High component count ({len(project.components)}) may impact performance")
        
        # DOM depth
        max_depth = self._calculate_max_depth(project.components)
        if max_depth > 15:
            result.add_warning(f"Deep DOM nesting ({max_depth} levels) may impact performance")
        
        # Image optimization
        if not config.optimization.optimize_images:
            unoptimized_images = [
                comp for comp in project.components
                if comp.type == "image"
            ]
            if unoptimized_images:
                result.add_warning(f"{len(unoptimized_images)} images will not be optimized")
        
        # Large inline styles
        components_with_large_styles = [
            comp for comp in project.components
            if hasattr(comp, 'styles') and len(str(comp.styles)) > 1000
        ]
        if components_with_large_styles:
            result.add_warning(
                f"{len(components_with_large_styles)} components have large inline styles"
            )
        
        return result
    
    async def _validate_security(self, project: Project) -> ValidationResult:
        """
        Validate security concerns
        
        CLAUDE.md #5.4: Security validation
        """
        result = ValidationResult()
        
        for component in project.components:
            # Check for unsafe content
            if component.content_type == "html":
                if self._contains_unsafe_html(component.content):
                    result.add_error(
                        f"Component '{component.name or component.id}' contains potentially unsafe HTML"
                    )
            
            # Check for javascript: URLs
            if component.type == "link":
                href = component.properties.get("href", "")
                if href.startswith("javascript:"):
                    result.add_error(
                        f"Component '{component.name or component.id}' uses unsafe javascript: URL"
                    )
            
            # Check for external resources
            for prop, value in component.properties.items():
                if isinstance(value, str) and value.startswith("http"):
                    if not value.startswith("https"):
                        result.add_warning(
                            f"Component '{component.name or component.id}' uses insecure HTTP resource"
                        )
        
        return result
    
    async def _validate_compatibility(self, project: Project, config: ExportConfig) -> ValidationResult:
        """Validate format-specific compatibility"""
        result = ValidationResult()
        
        # React-specific validation
        if config.format.value == "react":
            # Check for reserved prop names
            for comp in project.components:
                if "key" in comp.properties and not comp.properties.get("key").startswith("$"):
                    result.add_warning(
                        f"Component uses 'key' prop which is reserved in React"
                    )
        
        # Check for CSS Grid/Flexbox usage
        components_with_modern_layout = [
            comp for comp in project.components
            if hasattr(comp, 'styles') and (
                comp.styles.get('display') in ['grid', 'flex'] or
                any(prop.startswith('grid') for prop in comp.styles)
            )
        ]
        
        if components_with_modern_layout:
            result.add_warning(
                f"{len(components_with_modern_layout)} components use modern CSS features - ensure browser compatibility"
            )
        
        return result
    
    def _has_circular_dependencies(self, components: List[Component]) -> bool:
        """Check for circular parent-child relationships"""
        visited = set()
        rec_stack = set()
        
        def has_cycle(comp_id: str) -> bool:
            visited.add(comp_id)
            rec_stack.add(comp_id)
            
            # Find children
            children = [c for c in components if c.parent_id == comp_id]
            for child in children:
                if child.id not in visited:
                    if has_cycle(child.id):
                        return True
                elif child.id in rec_stack:
                    return True
            
            rec_stack.remove(comp_id)
            return False
        
        # Check all components
        for comp in components:
            if comp.id not in visited:
                if has_cycle(comp.id):
                    return True
        
        return False
    
    def _calculate_max_depth(self, components: List[Component]) -> int:
        """Calculate maximum component nesting depth"""
        def get_depth(comp_id: str, depth: int = 0) -> int:
            children = [c for c in components if c.parent_id == comp_id]
            if not children:
                return depth
            return max(get_depth(child.id, depth + 1) for child in children)
        
        root_components = [c for c in components if not c.parent_id]
        if not root_components:
            return 0
        
        return max(get_depth(root.id, 1) for root in root_components)
    
    def _get_referenced_assets(self, components: List[Component]) -> List[str]:
        """Get all asset IDs referenced by components"""
        asset_refs = []
        
        for comp in components:
            # Check common asset properties
            for prop in ['src', 'backgroundImage', 'icon', 'logo']:
                if prop in comp.properties:
                    value = comp.properties[prop]
                    if isinstance(value, str) and value.startswith('asset:'):
                        asset_refs.append(value.replace('asset:', ''))
        
        return asset_refs
    
    def _get_supported_mime_types(self) -> List[str]:
        """Get list of supported MIME types"""
        return [
            'image/jpeg', 'image/png', 'image/gif', 'image/svg+xml', 'image/webp',
            'video/mp4', 'video/webm', 'video/ogg',
            'audio/mpeg', 'audio/ogg', 'audio/wav',
            'application/pdf', 'text/plain', 'text/csv'
        ]
    
    def _has_associated_label(self, input_component: Component, all_components: List[Component]) -> bool:
        """Check if input has an associated label"""
        input_id = input_component.id
        
        # Look for label with 'for' attribute
        for comp in all_components:
            if comp.type == "label" and comp.properties.get("for") == input_id:
                return True
        
        # Check if input is wrapped in label
        for comp in all_components:
            if comp.type == "label" and any(
                child.id == input_id for child in getattr(comp, 'children', [])
            ):
                return True
        
        return False
    
    def _has_low_contrast(self, component: Component) -> bool:
        """Check if component has low color contrast"""
        if not hasattr(component, 'styles'):
            return False
        
        fg_color = component.styles.get('color')
        bg_color = component.styles.get('backgroundColor')
        
        if fg_color and bg_color:
            # Simplified contrast check - in production use proper WCAG calculation
            return False  # TODO: Implement proper contrast ratio calculation
        
        return False
    
    def _contains_unsafe_html(self, html_content: str) -> bool:
        """Check for potentially unsafe HTML content"""
        if not html_content:
            return False
        
        # Check for script tags
        if '<script' in html_content.lower():
            return True
        
        # Check for event handlers
        import re
        if re.search(r'on\w+\s*=', html_content, re.IGNORECASE):
            return True
        
        # Check for iframes
        if '<iframe' in html_content.lower():
            return True
        
        return False