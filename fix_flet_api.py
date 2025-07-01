#!/usr/bin/env python3
"""Fix Flet API compatibility issues"""

import os
import re

def fix_file(filepath):
    """Fix Flet API issues in a file"""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Fix UserControl -> just inherit from Container instead
    content = re.sub(r'class\s+(\w+)\(ft\.UserControl\):', r'class \1(ft.Container):', content)
    
    # Fix DragTargetAcceptEvent -> DragTargetEvent
    content = content.replace('ft.DragTargetAcceptEvent', 'ft.DragTargetEvent')
    content = content.replace('ft.DragTargetLeaveEvent', 'ft.DragTargetEvent')
    
    # Fix any other common API changes
    # UserControl.build() -> just use __init__ and set content
    if 'def build(self):' in content and 'UserControl' in original:
        # This is more complex - need manual fixing
        print(f"  - Warning: {filepath} needs manual fix for build() method")
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Fixed: {filepath}")
        return True
    return False

def main():
    """Fix all Python files in the project"""
    print("Fixing Flet API compatibility issues...")
    
    fixed_count = 0
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_file(filepath):
                    fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} files")
    print("\nNote: Some files may need manual adjustment for UserControl.build() pattern")

if __name__ == "__main__":
    main()