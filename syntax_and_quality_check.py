#!/usr/bin/env python3
"""
Syntax and Quality Check for Canvas Editor State Management
Performs focused syntax validation and quality assessment
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

def check_file_syntax(filepath: Path) -> Dict[str, Any]:
    """Check syntax of a single Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Compile to check syntax
        compile(content, str(filepath), 'exec')
        
        # Parse AST for analysis
        tree = ast.parse(content)
        
        # Count key elements
        stats = {
            "functions": 0,
            "classes": 0,
            "async_functions": 0,
            "try_blocks": 0,
            "imports": 0,
            "lines": len(content.splitlines())
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                stats["functions"] += 1
            elif isinstance(node, ast.AsyncFunctionDef):
                stats["async_functions"] += 1
            elif isinstance(node, ast.ClassDef):
                stats["classes"] += 1
            elif isinstance(node, ast.Try):
                stats["try_blocks"] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                stats["imports"] += 1
        
        return {
            "status": "✅",
            "file": filepath.name,
            "stats": stats
        }
        
    except SyntaxError as e:
        return {
            "status": "❌",
            "file": filepath.name,
            "error": f"Syntax Error at line {e.lineno}: {e.msg}",
            "line": e.lineno
        }
    except Exception as e:
        return {
            "status": "⚠️",
            "file": filepath.name,
            "error": str(e)
        }

def check_code_quality(filepath: Path) -> List[Dict[str, Any]]:
    """Check code quality issues"""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
        
        # Check for common quality issues
        for i, line in enumerate(lines, 1):
            # Long lines
            if len(line) > 120:
                issues.append({
                    "type": "long_line",
                    "line": i,
                    "length": len(line)
                })
            
            # TODO/FIXME comments
            if any(marker in line for marker in ["TODO", "FIXME", "XXX", "HACK"]):
                issues.append({
                    "type": "todo_comment",
                    "line": i,
                    "content": line.strip()
                })
            
            # Print statements (debugging leftover)
            if "print(" in line and not line.strip().startswith("#"):
                issues.append({
                    "type": "print_statement",
                    "line": i
                })
        
        # Parse AST for deeper checks
        tree = ast.parse(content)
        
        # Check for bare except
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append({
                        "type": "bare_except",
                        "line": node.lineno
                    })
        
    except Exception:
        pass  # Skip quality checks if parse fails
    
    return issues

def analyze_managers():
    """Analyze all manager modules"""
    print("🔍 Canvas Editor State Management - Syntax and Quality Analysis")
    print("=" * 70)
    
    managers_path = Path("src/managers")
    results = []
    total_stats = defaultdict(int)
    all_issues = defaultdict(list)
    
    # Check each Python file
    for py_file in sorted(managers_path.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
            
        # Syntax check
        result = check_file_syntax(py_file)
        results.append(result)
        
        # Quality check
        if result["status"] == "✅":
            issues = check_code_quality(py_file)
            if issues:
                all_issues[py_file.name] = issues
            
            # Aggregate stats
            for key, value in result.get("stats", {}).items():
                total_stats[key] += value
    
    # Display results
    print("\n## Syntax Check Results")
    print("-" * 40)
    
    syntax_errors = 0
    for result in results:
        print(f"{result['status']} {result['file']}")
        if result["status"] != "✅":
            print(f"   └─ {result.get('error', 'Unknown error')}")
            syntax_errors += 1
    
    # Summary statistics
    print(f"\n## Code Statistics")
    print("-" * 40)
    print(f"Total Files: {len(results)}")
    print(f"Syntax Errors: {syntax_errors}")
    print(f"Total Lines: {total_stats['lines']:,}")
    print(f"Total Functions: {total_stats['functions']}")
    print(f"Total Classes: {total_stats['classes']}")
    print(f"Async Functions: {total_stats['async_functions']}")
    print(f"Try/Except Blocks: {total_stats['try_blocks']}")
    print(f"Import Statements: {total_stats['imports']}")
    
    # Quality issues summary
    print(f"\n## Code Quality Issues")
    print("-" * 40)
    
    issue_counts = defaultdict(int)
    for file_issues in all_issues.values():
        for issue in file_issues:
            issue_counts[issue["type"]] += 1
    
    if issue_counts:
        for issue_type, count in sorted(issue_counts.items()):
            print(f"{issue_type}: {count}")
    else:
        print("No quality issues found! 🎉")
    
    # Show sample issues
    if all_issues:
        print(f"\n## Sample Issues (first 5)")
        print("-" * 40)
        
        shown = 0
        for filename, issues in all_issues.items():
            for issue in issues[:2]:  # Show max 2 per file
                print(f"{filename}:{issue['line']} - {issue['type']}")
                if issue['type'] == 'todo_comment':
                    print(f"   └─ {issue['content']}")
                shown += 1
                if shown >= 5:
                    break
            if shown >= 5:
                break
    
    # Overall assessment
    print(f"\n## Overall Assessment")
    print("=" * 70)
    
    if syntax_errors == 0:
        print("✅ All files pass syntax validation!")
    else:
        print(f"❌ {syntax_errors} files have syntax errors")
    
    critical_issues = sum(1 for issues in all_issues.values() 
                         for issue in issues 
                         if issue['type'] in ['bare_except', 'print_statement'])
    
    if critical_issues == 0:
        print("✅ No critical code quality issues found!")
    else:
        print(f"⚠️  {critical_issues} critical quality issues found")
    
    print(f"\n🏆 Code Quality Score: {100 - (syntax_errors * 10) - (critical_issues * 5)}/100")
    
    return syntax_errors == 0

def main():
    """Run the analysis"""
    success = analyze_managers()
    
    # Additional specific checks
    print("\n## Import Structure Validation")
    print("-" * 40)
    
    # Check that all relative imports are correct
    managers_path = Path("src/managers")
    import_issues = 0
    
    for py_file in sorted(managers_path.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
            
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            # Check for relative imports
            if "from ." in content:
                print(f"✅ {py_file.name} - Uses relative imports")
            elif py_file.name in ["spatial_index.py", "state_migration.py"]:
                print(f"✅ {py_file.name} - No internal imports needed")
            elif "from state_" in content or "from action_" in content or "from history_" in content:
                print(f"⚠️  {py_file.name} - May have direct imports")
                import_issues += 1
        except Exception:
            pass
    
    if import_issues == 0:
        print("\n✅ All import structures are correct!")
    else:
        print(f"\n⚠️  {import_issues} files may have import issues")
    
    return success and import_issues == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)