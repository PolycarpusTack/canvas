#!/usr/bin/env python3
"""
Fix relative import issues in all Python files
"""

import os
import re
from pathlib import Path

def fix_imports(file_path):
    """Fix relative imports in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix relative imports
        # Pattern: from .module import ... -> from module import ...
        content = re.sub(r'from \.([a-zA-Z_][a-zA-Z0-9_]*) import', r'from \1 import', content)
        
        # Pattern: from ..module import ... -> from module import ...
        content = re.sub(r'from \.\.([a-zA-Z_][a-zA-Z0-9_]*) import', r'from \1 import', content)
        
        # Pattern: from ...module import ... -> from module import ...
        content = re.sub(r'from \.\.\.([a-zA-Z_][a-zA-Z0-9_]*) import', r'from \1 import', content)
        
        # Pattern: from ....module import ... -> from module import ...
        content = re.sub(r'from \.\.\.\.([a-zA-Z_][a-zA-Z0-9_]*) import', r'from \1 import', content)
        
        # Pattern: from ..sub.module import ... -> from sub.module import ...
        content = re.sub(r'from \.\.([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_.]*) import', r'from \1 import', content)
        
        # Pattern: from ...sub.module import ... -> from sub.module import ...  
        content = re.sub(r'from \.\.\.([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_.]*) import', r'from \1 import', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f'Error processing {file_path}: {e}')
        return False

def main():
    # Process all Python files in src/
    src_dir = Path('src')
    fixed_files = []

    print("Fixing relative imports...")

    for py_file in src_dir.rglob('*.py'):
        if fix_imports(py_file):
            fixed_files.append(py_file)
            print(f'✅ Fixed: {py_file}')

    print(f'\n📊 Summary: Fixed {len(fixed_files)} files')

if __name__ == "__main__":
    main()