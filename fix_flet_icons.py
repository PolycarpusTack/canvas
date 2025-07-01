#!/usr/bin/env python3
"""Fix Flet icons API changes"""

import os
import re

def fix_icons_in_file(filepath):
    """Fix ft.icons to ft.Icons in a file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Replace ft.icons. with ft.Icons.
    content = re.sub(r'ft\.icons\.', 'ft.Icons.', content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Fixed: {filepath}")
        return True
    return False

def main():
    """Fix all Python files"""
    print("Fixing Flet icons API...")
    
    fixed_count = 0
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_icons_in_file(filepath):
                    fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} files")

if __name__ == "__main__":
    main()