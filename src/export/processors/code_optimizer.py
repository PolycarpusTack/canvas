"""
Code Optimizer

CLAUDE.md Implementation:
- #1.5: Performance optimization
- #7.3: CSS optimization
- #6.3: Tree shaking and dead code elimination
"""

import re
import json
import logging
from typing import Dict, Optional, Any, List, Set, Tuple
from pathlib import Path

from ..export_config import OptimizationSettings

logger = logging.getLogger(__name__)


class CodeOptimizer:
    """
    Optimize generated code for production
    
    CLAUDE.md #1.5: Performance optimization
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.unused_css_cache: Dict[str, Set[str]] = {}
    
    async def optimize_files(
        self,
        files: Dict[str, str],
        optimization: OptimizationSettings
    ) -> Dict[str, str]:
        """Optimize all files based on settings"""
        
        optimized = {}
        
        for file_path, content in files.items():
            path = Path(file_path)
            
            # Determine file type and optimize accordingly
            if path.suffix == '.html' and optimization.minify_html:
                optimized[file_path] = await self._optimize_html(content)
            elif path.suffix == '.css' and optimization.minify_css:
                optimized[file_path] = await self._optimize_css(
                    content,
                    optimization.purge_unused_css,
                    files
                )
            elif path.suffix in ['.js', '.jsx', '.ts', '.tsx'] and optimization.minify_js:
                optimized[file_path] = await self._optimize_javascript(content)
            elif path.suffix == '.json':
                optimized[file_path] = await self._optimize_json(content)
            else:
                # No optimization for this file type
                optimized[file_path] = content
        
        return optimized
    
    async def _optimize_html(self, html_content: str) -> str:
        """
        Optimize HTML content
        
        CLAUDE.md #7.3: HTML minification
        """
        try:
            # Remove comments (except IE conditional comments)
            html_content = re.sub(
                r'<!--(?!\[if).*?(?<!\])-->',
                '',
                html_content,
                flags=re.DOTALL
            )
            
            # Remove unnecessary whitespace between tags
            html_content = re.sub(r'>\s+<', '><', html_content)
            
            # Remove whitespace around block elements
            block_elements = [
                'div', 'p', 'h[1-6]', 'ul', 'ol', 'li', 'table', 'tr', 'td',
                'section', 'article', 'header', 'footer', 'nav', 'main'
            ]
            pattern = f"\\s*(</?(?:{'|'.join(block_elements)})[^>]*>)\\s*"
            html_content = re.sub(pattern, r'\1', html_content, flags=re.IGNORECASE)
            
            # Collapse multiple spaces
            html_content = re.sub(r'\s{2,}', ' ', html_content)
            
            # Remove quotes around safe attribute values
            html_content = re.sub(
                r'(\w+)="([a-zA-Z0-9\-_]+)"',
                r'\1=\2',
                html_content
            )
            
            # Remove optional closing tags
            optional_closing = ['</li>', '</td>', '</tr>', '</th>', '</option>']
            for tag in optional_closing:
                html_content = html_content.replace(tag, '')
            
            # Remove type="text/javascript" (default in HTML5)
            html_content = html_content.replace(' type="text/javascript"', '')
            html_content = html_content.replace(' type="text/css"', '')
            
            self.logger.info(f"HTML optimized: {len(html_content)} bytes")
            
            return html_content.strip()
            
        except Exception as e:
            self.logger.error(f"HTML optimization failed: {e}")
            return html_content
    
    async def _optimize_css(
        self,
        css_content: str,
        purge_unused: bool,
        all_files: Dict[str, str]
    ) -> str:
        """
        Optimize CSS content
        
        CLAUDE.md #6.3: Remove unused CSS
        """
        try:
            # First, minify CSS
            # Remove comments
            css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
            
            # Remove unnecessary whitespace
            css_content = re.sub(r'\s+', ' ', css_content)
            css_content = re.sub(r'\s*([{}:;,])\s*', r'\1', css_content)
            
            # Remove last semicolon before closing brace
            css_content = re.sub(r';\}', '}', css_content)
            
            # Remove units from zero values
            css_content = re.sub(r':\s*0(px|em|rem|%)', ':0', css_content)
            
            # Shorten color values
            css_content = re.sub(
                r'#([0-9a-fA-F])\1([0-9a-fA-F])\2([0-9a-fA-F])\3',
                r'#\1\2\3',
                css_content
            )
            
            # Purge unused CSS if requested
            if purge_unused:
                used_selectors = await self._find_used_selectors(all_files)
                css_content = self._purge_unused_css(css_content, used_selectors)
            
            # Combine duplicate rules
            css_content = self._combine_duplicate_rules(css_content)
            
            self.logger.info(f"CSS optimized: {len(css_content)} bytes")
            
            return css_content.strip()
            
        except Exception as e:
            self.logger.error(f"CSS optimization failed: {e}")
            return css_content
    
    async def _optimize_javascript(self, js_content: str) -> str:
        """
        Optimize JavaScript content
        
        CLAUDE.md #6.3: Basic JS minification
        """
        try:
            # Remove single-line comments
            js_content = re.sub(r'//.*?$', '', js_content, flags=re.MULTILINE)
            
            # Remove multi-line comments
            js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
            
            # Remove console.log statements (optional in production)
            js_content = re.sub(r'console\.(log|info|warn|error)\([^)]*\);?', '', js_content)
            
            # Remove unnecessary whitespace
            js_content = re.sub(r'\s+', ' ', js_content)
            
            # Remove space around operators
            operators = [
                '=', '==', '===', '!=', '!==', '>', '<', '>=', '<=',
                '+', '-', '*', '/', '%', '&&', '||', '!', '?', ':'
            ]
            for op in operators:
                # Escape special regex characters
                escaped_op = re.escape(op)
                js_content = re.sub(f'\\s*{escaped_op}\\s*', op, js_content)
            
            # Remove space after function keyword
            js_content = re.sub(r'function\s+', 'function ', js_content)
            
            # Remove trailing semicolons before closing braces
            js_content = re.sub(r';\s*\}', '}', js_content)
            
            # Tree shaking simulation - remove obviously unused functions
            js_content = self._remove_unused_functions(js_content)
            
            self.logger.info(f"JavaScript optimized: {len(js_content)} bytes")
            
            return js_content.strip()
            
        except Exception as e:
            self.logger.error(f"JavaScript optimization failed: {e}")
            return js_content
    
    async def _optimize_json(self, json_content: str) -> str:
        """Optimize JSON by removing unnecessary whitespace"""
        try:
            # Parse and re-serialize without indentation
            data = json.loads(json_content)
            return json.dumps(data, separators=(',', ':'))
        except Exception as e:
            self.logger.error(f"JSON optimization failed: {e}")
            return json_content
    
    async def _find_used_selectors(
        self,
        files: Dict[str, str]
    ) -> Set[str]:
        """Find all CSS selectors used in HTML/JS files"""
        
        used_selectors = set()
        
        # Common selectors that should always be kept
        used_selectors.update([
            '*', 'html', 'body', 'head', 'title', 'meta', 'link',
            'style', 'script', 'noscript'
        ])
        
        for file_path, content in files.items():
            path = Path(file_path)
            
            # Only analyze HTML and JS files
            if path.suffix not in ['.html', '.js', '.jsx', '.ts', '.tsx']:
                continue
            
            # Extract IDs
            id_matches = re.findall(r'id=["\']([^"\']+)["\']', content)
            used_selectors.update(f'#{id_val}' for id_val in id_matches)
            
            # Extract classes
            class_matches = re.findall(r'class=["\']([^"\']+)["\']', content)
            for class_str in class_matches:
                classes = class_str.split()
                used_selectors.update(f'.{cls}' for cls in classes)
            
            # Extract from className (React/JSX)
            className_matches = re.findall(r'className=["\']([^"\']+)["\']', content)
            for class_str in className_matches:
                classes = class_str.split()
                used_selectors.update(f'.{cls}' for cls in classes)
            
            # Extract HTML tags
            tag_matches = re.findall(r'<([a-zA-Z][a-zA-Z0-9]*)', content)
            used_selectors.update(tag_matches)
            
            # Extract from JavaScript class manipulations
            js_class_patterns = [
                r'classList\.add\(["\']([^"\']+)["\']',
                r'classList\.remove\(["\']([^"\']+)["\']',
                r'classList\.toggle\(["\']([^"\']+)["\']',
                r'querySelector\(["\']([^"\']+)["\']',
                r'querySelectorAll\(["\']([^"\']+)["\']'
            ]
            
            for pattern in js_class_patterns:
                matches = re.findall(pattern, content)
                used_selectors.update(matches)
        
        return used_selectors
    
    def _purge_unused_css(
        self,
        css_content: str,
        used_selectors: Set[str]
    ) -> str:
        """Remove unused CSS rules"""
        
        # Parse CSS rules
        rule_pattern = r'([^{]+)\{([^}]+)\}'
        rules = re.findall(rule_pattern, css_content)
        
        kept_rules = []
        
        for selector, declarations in rules:
            selector = selector.strip()
            
            # Check if any part of the selector is used
            selector_parts = re.split(r'[,\s>+~]', selector)
            
            is_used = False
            for part in selector_parts:
                part = part.strip()
                if not part:
                    continue
                
                # Check direct match
                if part in used_selectors:
                    is_used = True
                    break
                
                # Check pseudo-classes and pseudo-elements
                if ':' in part:
                    base_selector = part.split(':')[0]
                    if base_selector in used_selectors:
                        is_used = True
                        break
                
                # Check attribute selectors
                if '[' in part:
                    base_selector = re.split(r'[\[\]]', part)[0]
                    if base_selector in used_selectors:
                        is_used = True
                        break
                
                # Always keep keyframes and media queries
                if part.startswith('@'):
                    is_used = True
                    break
            
            if is_used:
                kept_rules.append(f"{selector}{{{declarations}}}")
        
        optimized_css = ''.join(kept_rules)
        
        removed_count = len(rules) - len(kept_rules)
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} unused CSS rules")
        
        return optimized_css
    
    def _combine_duplicate_rules(self, css_content: str) -> str:
        """Combine CSS rules with identical declarations"""
        
        # Parse rules
        rule_pattern = r'([^{]+)\{([^}]+)\}'
        rules = re.findall(rule_pattern, css_content)
        
        # Group by declarations
        declaration_map: Dict[str, List[str]] = {}
        
        for selector, declarations in rules:
            # Normalize declarations
            decl_normalized = ';'.join(sorted(
                d.strip() for d in declarations.split(';') if d.strip()
            ))
            
            if decl_normalized not in declaration_map:
                declaration_map[decl_normalized] = []
            
            declaration_map[decl_normalized].append(selector.strip())
        
        # Rebuild CSS with combined selectors
        combined_rules = []
        
        for declarations, selectors in declaration_map.items():
            if len(selectors) > 1:
                # Combine selectors
                combined_selector = ','.join(selectors)
                self.logger.debug(f"Combined {len(selectors)} identical rules")
            else:
                combined_selector = selectors[0]
            
            combined_rules.append(f"{combined_selector}{{{declarations}}}")
        
        return ''.join(combined_rules)
    
    def _remove_unused_functions(self, js_content: str) -> str:
        """
        Remove obviously unused functions (basic tree shaking)
        
        CLAUDE.md #6.3: Dead code elimination
        """
        # This is a very basic implementation
        # In production, use proper AST parsing
        
        # Find all function declarations
        function_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*\{[^}]*\}'
        functions = re.findall(function_pattern, js_content)
        
        # Find all function calls
        used_functions = set()
        for func_name in functions:
            # Check if function is called anywhere
            call_pattern = rf'\b{func_name}\s*\('
            if re.search(call_pattern, js_content):
                used_functions.add(func_name)
        
        # Remove unused functions
        for func_name in functions:
            if func_name not in used_functions:
                # Remove the function definition
                remove_pattern = rf'function\s+{func_name}\s*\([^)]*\)\s*\{{[^}}]*\}}'
                js_content = re.sub(remove_pattern, '', js_content)
                self.logger.debug(f"Removed unused function: {func_name}")
        
        return js_content
    
    async def optimize_bundle(
        self,
        files: Dict[str, str],
        optimization: OptimizationSettings
    ) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """
        Optimize entire bundle with advanced techniques
        
        Returns optimized files and optimization report
        """
        
        report = {
            "original_size": sum(len(content) for content in files.values()),
            "optimized_size": 0,
            "savings_percentage": 0,
            "techniques_applied": []
        }
        
        # Apply optimizations
        optimized = await self.optimize_files(files, optimization)
        
        # Calculate metrics
        report["optimized_size"] = sum(len(content) for content in optimized.values())
        
        if report["original_size"] > 0:
            savings = report["original_size"] - report["optimized_size"]
            report["savings_percentage"] = (savings / report["original_size"]) * 100
        
        # List applied techniques
        if optimization.minify_html:
            report["techniques_applied"].append("HTML minification")
        if optimization.minify_css:
            report["techniques_applied"].append("CSS minification")
        if optimization.purge_unused_css:
            report["techniques_applied"].append("Unused CSS removal")
        if optimization.minify_js:
            report["techniques_applied"].append("JavaScript minification")
        
        self.logger.info(
            f"Bundle optimization complete: "
            f"{report['savings_percentage']:.1f}% size reduction"
        )
        
        return optimized, report