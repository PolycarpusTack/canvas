#!/usr/bin/env python3
"""Test if implementation is complete (no stubs)"""

import os
import re
import sys

def check_stubs(directory):
    stub_patterns = [
        (r'\bTODO\b', 'TODO comment'),
        (r'\bFIXME\b', 'FIXME comment'),
        (r'pass\s*$', 'Empty function'),
        (r'pass\s*#', 'Stub pass statement'),
        (r'NotImplementedError', 'Not implemented'),
        (r'return\s*None\s*#.*stub', 'Stub return'),
        (r'print\(.*coming soon', 'Coming soon message'),
        (r'\bmock\b', 'Mock implementation'),
        (r'return\s*{\s*}\s*#', 'Empty dict return'),
        (r'return\s*\[\s*\]\s*#', 'Empty list return'),
        (r'\.\.\.', 'Ellipsis placeholder'),
    ]
    
    issues = []
    
    for root, dirs, files in os.walk(directory):
        # Skip test directories and __pycache__
        if 'test' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    for line_no, line in enumerate(lines, 1):
                        for pattern, description in stub_patterns:
                            if re.search(pattern, line):
                                # Skip legitimate uses
                                if 'mock' in pattern.lower() and 'mockup' in line.lower():
                                    continue
                                issues.append(f"{filepath}:{line_no} - {description}: {line.strip()}")
                except Exception as e:
                    print(f"Warning: Could not read {filepath}: {e}")
    
    return issues

def check_empty_functions(directory):
    """Check for functions that only contain pass or print statements"""
    issues = []
    
    for root, dirs, files in os.walk(directory):
        if 'test' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Find function definitions
                    func_pattern = r'def\s+(\w+)\s*\([^)]*\)\s*:\s*\n((?:\s+.+\n)*)'
                    
                    for match in re.finditer(func_pattern, content):
                        func_name = match.group(1)
                        func_body = match.group(2)
                        
                        # Skip special methods
                        if func_name.startswith('__') and func_name.endswith('__'):
                            continue
                        
                        # Check if function only contains pass or print
                        body_lines = [line.strip() for line in func_body.split('\n') if line.strip()]
                        
                        if len(body_lines) == 1:
                            if body_lines[0] == 'pass':
                                line_no = content[:match.start()].count('\n') + 1
                                issues.append(f"{filepath}:{line_no} - Empty function: {func_name}")
                            elif body_lines[0].startswith('print('):
                                line_no = content[:match.start()].count('\n') + 1
                                issues.append(f"{filepath}:{line_no} - Print-only function: {func_name}")
                
                except Exception as e:
                    print(f"Warning: Could not analyze {filepath}: {e}")
    
    return issues

if __name__ == "__main__":
    print("🔍 Checking for stub code...\n")
    
    src_dir = 'src'
    if not os.path.exists(src_dir):
        print(f"❌ Directory '{src_dir}' not found!")
        print("   Run this from the canvas project root directory.")
        sys.exit(1)
    
    # Check for stub patterns
    stub_issues = check_stubs(src_dir)
    
    # Check for empty functions
    empty_issues = check_empty_functions(src_dir)
    
    all_issues = stub_issues + empty_issues
    
    if all_issues:
        print("❌ STUB CODE DETECTED:\n")
        for issue in sorted(all_issues):
            print(f"  {issue}")
        print(f"\n{len(all_issues)} issues found!")
        print("\nFix all stubs before proceeding to the next task.")
        sys.exit(1)
    else:
        print("✅ No stubs detected - implementation appears complete!")
        print("\nVerified:")
        print("  - No TODO/FIXME comments")
        print("  - No empty functions")
        print("  - No mock implementations")
        print("  - No placeholder returns")
        print("\nYou can proceed to the next task! 🎉")
        sys.exit(0)