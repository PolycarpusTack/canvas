#!/usr/bin/env python3
"""
Comprehensive Flet API compatibility fix
"""

import os
import re
from pathlib import Path

def fix_flet_apis(file_path):
    """Fix all Flet API issues in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. Fix ft.icons -> ft.Icons
        content = re.sub(r'\bft\.icons\.(\w+)', r'ft.Icons.\1', content)
        
        # 2. Fix ft.colors -> ft.Colors  
        content = re.sub(r'\bft\.colors\.(\w+)', r'ft.Colors.\1', content)
        
        # 3. Fix DragTargetAcceptEvent -> DragTargetEvent
        content = content.replace('ft.DragTargetAcceptEvent', 'ft.DragTargetEvent')
        content = content.replace('DragTargetAcceptEvent', 'DragTargetEvent')
        
        # 4. Fix BoxShadow with_opacity usage
        content = re.sub(r'ft\.colors\.with_opacity\(([^,]+),\s*ft\.Colors\.(\w+)\)', r'ft.Colors.\2.with_opacity(\1)', content)
        
        # 5. Fix UserControl inheritance (warn only)
        if 'ft.UserControl' in content:
            print(f'  ⚠️  {file_path} has UserControl - consider using Container pattern')
        
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

    print("Running comprehensive Flet API fixes...")

    for py_file in src_dir.rglob('*.py'):
        if fix_flet_apis(py_file):
            fixed_files.append(py_file)
            print(f'✅ Fixed: {py_file}')

    print(f'\n📊 Summary: Fixed {len(fixed_files)} files')

if __name__ == "__main__":
    main()