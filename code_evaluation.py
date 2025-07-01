#!/usr/bin/env python3
"""
Comprehensive Code Evaluation for Canvas Editor State Management
Performs syntax validation, code quality checks, and pattern evaluation
"""

import ast
import sys
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict

class CodeEvaluator:
    """Evaluates code quality, patterns, and potential issues"""
    
    def __init__(self):
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)
        self.patterns = defaultdict(list)
        
    def evaluate_file(self, filepath: Path) -> Dict[str, Any]:
        """Evaluate a single Python file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse AST
            tree = ast.parse(content, filename=str(filepath))
            
            # Run evaluations
            self._check_syntax_and_structure(tree, filepath)
            self._check_imports(tree, filepath)
            self._check_error_handling(tree, filepath)
            self._check_type_hints(tree, filepath)
            self._check_async_patterns(tree, filepath)
            self._check_docstrings(tree, filepath)
            self._check_code_patterns(tree, filepath, content)
            self._check_security_patterns(content, filepath)
            
            return {"success": True, "file": str(filepath)}
            
        except SyntaxError as e:
            self.issues["syntax_errors"].append({
                "file": str(filepath),
                "line": e.lineno,
                "error": str(e)
            })
            return {"success": False, "file": str(filepath), "error": str(e)}
            
        except Exception as e:
            self.issues["parse_errors"].append({
                "file": str(filepath),
                "error": str(e)
            })
            return {"success": False, "file": str(filepath), "error": str(e)}
    
    def _check_syntax_and_structure(self, tree: ast.AST, filepath: Path):
        """Check syntax and structural patterns"""
        for node in ast.walk(tree):
            # Check for problematic patterns
            if isinstance(node, ast.Lambda) and len(ast.dump(node)) > 200:
                self.issues["complex_lambdas"].append({
                    "file": str(filepath),
                    "line": node.lineno
                })
            
            # Check for nested functions depth
            if isinstance(node, ast.FunctionDef):
                depth = self._get_nesting_depth(node)
                if depth > 3:
                    self.issues["deep_nesting"].append({
                        "file": str(filepath),
                        "function": node.name,
                        "depth": depth
                    })
                
                # Count function
                self.stats["total_functions"] += 1
                
            # Check for class definitions
            if isinstance(node, ast.ClassDef):
                self.stats["total_classes"] += 1
                
                # Check for proper __init__
                has_init = any(
                    isinstance(n, ast.FunctionDef) and n.name == "__init__"
                    for n in node.body
                )
                if not has_init and not any(
                    isinstance(base, ast.Name) and base.id in ["Enum", "Protocol"]
                    for base in node.bases
                ):
                    self.issues["missing_init"].append({
                        "file": str(filepath),
                        "class": node.name
                    })
    
    def _check_imports(self, tree: ast.AST, filepath: Path):
        """Check import patterns and issues"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node)
                
                # Check for star imports
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name == "*":
                            self.issues["star_imports"].append({
                                "file": str(filepath),
                                "line": node.lineno,
                                "module": node.module
                            })
                
                # Check for duplicate imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_name = alias.asname or alias.name
                        if import_name in [n.asname or n.name for n in imports[:-1]]:
                            self.issues["duplicate_imports"].append({
                                "file": str(filepath),
                                "line": node.lineno,
                                "import": import_name
                            })
        
        self.stats["total_imports"] += len(imports)
    
    def _check_error_handling(self, tree: ast.AST, filepath: Path):
        """Check error handling patterns"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                self.stats["try_blocks"] += 1
                
                # Check for bare except
                for handler in node.handlers:
                    if handler.type is None:
                        self.issues["bare_except"].append({
                            "file": str(filepath),
                            "line": handler.lineno
                        })
                    
                    # Check for pass in except
                    if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                        self.issues["silent_except"].append({
                            "file": str(filepath),
                            "line": handler.lineno
                        })
            
            # Check for proper logging in functions
            if isinstance(node, ast.FunctionDef):
                has_error_handling = any(
                    isinstance(n, ast.Try) for n in ast.walk(node)
                )
                has_logging = any(
                    isinstance(n, ast.Attribute) and 
                    isinstance(n.value, ast.Name) and 
                    n.value.id == "logger"
                    for n in ast.walk(node)
                )
                
                if has_error_handling and not has_logging:
                    self.patterns["error_without_logging"].append({
                        "file": str(filepath),
                        "function": node.name
                    })
    
    def _check_type_hints(self, tree: ast.AST, filepath: Path):
        """Check type hint coverage"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for return type hint
                if node.returns is None and node.name != "__init__":
                    self.issues["missing_return_type"].append({
                        "file": str(filepath),
                        "function": node.name,
                        "line": node.lineno
                    })
                
                # Check for parameter type hints
                for arg in node.args.args:
                    if arg.annotation is None and arg.arg not in ["self", "cls"]:
                        self.issues["missing_param_type"].append({
                            "file": str(filepath),
                            "function": node.name,
                            "param": arg.arg,
                            "line": node.lineno
                        })
    
    def _check_async_patterns(self, tree: ast.AST, filepath: Path):
        """Check async/await patterns"""
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                self.stats["async_functions"] += 1
                
                # Check if async function has await
                has_await = any(
                    isinstance(n, ast.Await) for n in ast.walk(node)
                )
                if not has_await:
                    self.issues["async_without_await"].append({
                        "file": str(filepath),
                        "function": node.name,
                        "line": node.lineno
                    })
            
            # Check for blocking calls in async context
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ["sleep", "input"]:
                    # Check if in async context
                    parent = self._get_parent_function(node)
                    if parent and isinstance(parent, ast.AsyncFunctionDef):
                        self.issues["blocking_in_async"].append({
                            "file": str(filepath),
                            "line": node.lineno,
                            "call": node.func.id
                        })
    
    def _check_docstrings(self, tree: ast.AST, filepath: Path):
        """Check docstring coverage"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                if not docstring:
                    if not node.name.startswith("_") or node.name == "__init__":
                        self.issues["missing_docstring"].append({
                            "file": str(filepath),
                            "type": type(node).__name__,
                            "name": node.name,
                            "line": node.lineno
                        })
                elif len(docstring) < 10:
                    self.issues["short_docstring"].append({
                        "file": str(filepath),
                        "name": node.name,
                        "length": len(docstring)
                    })
    
    def _check_code_patterns(self, tree: ast.AST, filepath: Path, content: str):
        """Check for code patterns and best practices"""
        # Check line length
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                self.issues["long_lines"].append({
                    "file": str(filepath),
                    "line": i,
                    "length": len(line)
                })
        
        # Check for TODO/FIXME comments
        todo_pattern = re.compile(r'#\s*(TODO|FIXME|XXX|HACK):(.*)', re.IGNORECASE)
        for i, line in enumerate(lines, 1):
            match = todo_pattern.search(line)
            if match:
                self.patterns["todo_comments"].append({
                    "file": str(filepath),
                    "line": i,
                    "type": match.group(1),
                    "comment": match.group(2).strip()
                })
        
        # Check for magic numbers
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)) and node.value not in [0, 1, -1, 2, 100]:
                    self.patterns["magic_numbers"].append({
                        "file": str(filepath),
                        "line": node.lineno,
                        "value": node.value
                    })
    
    def _check_security_patterns(self, content: str, filepath: Path):
        """Check for security patterns"""
        # Check for hardcoded secrets
        secret_patterns = [
            (r'(password|passwd|pwd)\s*=\s*["\']([^"\']+)["\']', "hardcoded_password"),
            (r'(api_key|apikey)\s*=\s*["\']([^"\']+)["\']', "hardcoded_api_key"),
            (r'(secret|token)\s*=\s*["\']([^"\']+)["\']', "hardcoded_secret"),
        ]
        
        for pattern, issue_type in secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match.group(2)) > 5:  # Ignore short placeholders
                    self.issues[issue_type].append({
                        "file": str(filepath),
                        "match": match.group(1)
                    })
        
        # Check for SQL injection vulnerabilities
        sql_pattern = re.compile(r'(execute|executemany)\s*\([^)]*%[^)]*\)', re.IGNORECASE)
        if sql_pattern.search(content):
            self.issues["sql_injection_risk"].append({
                "file": str(filepath)
            })
    
    def _get_nesting_depth(self, node: ast.AST, depth: int = 0) -> int:
        """Get the nesting depth of a function"""
        max_depth = depth
        for child in ast.walk(node):
            if isinstance(child, ast.FunctionDef) and child != node:
                child_depth = self._get_nesting_depth(child, depth + 1)
                max_depth = max(max_depth, child_depth)
        return max_depth
    
    def _get_parent_function(self, node: ast.AST) -> Optional[ast.AST]:
        """Get the parent function of a node (simplified)"""
        # This is a simplified version - in practice you'd need the full AST context
        return None
    
    def generate_report(self) -> str:
        """Generate evaluation report"""
        report = []
        report.append("# Canvas Editor Code Evaluation Report")
        report.append("=" * 70)
        
        # Statistics
        report.append("\n## Code Statistics")
        report.append(f"- Total Functions: {self.stats['total_functions']}")
        report.append(f"- Total Classes: {self.stats['total_classes']}")
        report.append(f"- Total Imports: {self.stats['total_imports']}")
        report.append(f"- Async Functions: {self.stats['async_functions']}")
        report.append(f"- Try/Except Blocks: {self.stats['try_blocks']}")
        
        # Issues Summary
        report.append("\n## Issues Summary")
        total_issues = sum(len(issues) for issues in self.issues.values())
        report.append(f"Total Issues Found: {total_issues}")
        
        if total_issues > 0:
            report.append("\n### Critical Issues")
            critical = ["syntax_errors", "parse_errors", "bare_except", "hardcoded_password", 
                       "hardcoded_api_key", "hardcoded_secret", "sql_injection_risk"]
            for issue_type in critical:
                if issue_type in self.issues:
                    report.append(f"- {issue_type}: {len(self.issues[issue_type])}")
            
            report.append("\n### Code Quality Issues")
            quality = ["missing_return_type", "missing_param_type", "missing_docstring",
                      "star_imports", "duplicate_imports", "async_without_await",
                      "blocking_in_async", "deep_nesting", "complex_lambdas"]
            for issue_type in quality:
                if issue_type in self.issues:
                    report.append(f"- {issue_type}: {len(self.issues[issue_type])}")
        
        # Patterns Found
        report.append("\n## Code Patterns")
        if self.patterns:
            for pattern_type, instances in self.patterns.items():
                report.append(f"- {pattern_type}: {len(instances)}")
        
        # Detailed Issues
        if self.issues:
            report.append("\n## Detailed Issues")
            for issue_type, instances in self.issues.items():
                if instances:
                    report.append(f"\n### {issue_type.replace('_', ' ').title()}")
                    for instance in instances[:5]:  # Show first 5
                        report.append(f"- {instance}")
                    if len(instances) > 5:
                        report.append(f"  ... and {len(instances) - 5} more")
        
        return "\n".join(report)


def main():
    """Run code evaluation on Canvas Editor managers"""
    print("🔍 Running Code Evaluation on Canvas Editor State Management...")
    
    evaluator = CodeEvaluator()
    managers_path = Path("src/managers")
    
    # Evaluate all Python files
    files_evaluated = 0
    for py_file in managers_path.glob("*.py"):
        if py_file.name != "__init__.py":
            result = evaluator.evaluate_file(py_file)
            files_evaluated += 1
            if result["success"]:
                print(f"✅ {py_file.name}")
            else:
                print(f"❌ {py_file.name}: {result.get('error', 'Unknown error')}")
    
    # Generate report
    report = evaluator.generate_report()
    
    # Save report
    report_path = Path("code_evaluation_report.md")
    report_path.write_text(report)
    
    print(f"\n📊 Evaluation complete. {files_evaluated} files analyzed.")
    print(f"📄 Report saved to: {report_path}")
    print("\n" + report)
    
    # Return success if no critical issues
    critical_count = sum(
        len(evaluator.issues.get(issue_type, []))
        for issue_type in ["syntax_errors", "parse_errors", "bare_except", 
                          "hardcoded_password", "hardcoded_api_key", 
                          "hardcoded_secret", "sql_injection_risk"]
    )
    
    return critical_count == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)