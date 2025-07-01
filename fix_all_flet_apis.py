#!/usr/bin/env python3
"""Fix all Flet API changes for 0.28.3"""

import os
import re

def fix_file(filepath):
    """Fix all Flet API issues in a file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Fix icons
    content = re.sub(r'ft\.icons\.', 'ft.Icons.', content)
    
    # Fix colors
    content = re.sub(r'ft\.colors\.', 'ft.Colors.', content)
    
    # Fix specific color methods
    content = content.replace('ft.Colors.with_opacity(', 'ft.colors.with_opacity(')
    
    # Fix AppView
    content = content.replace('ft.AppView.FLET_APP_DESKTOP', 'ft.AppView.FLET_APP')
    content = content.replace('ft.AppView.FLET_WEB_VIEW', 'ft.AppView.WEB_BROWSER')
    
    # Fix DragTargetEvent
    content = content.replace('DragTargetAcceptEvent', 'DragTargetEvent')
    content = content.replace('DragTargetLeaveEvent', 'DragTargetEvent')
    
    # Fix UserControl - comment out for now
    # This needs manual fixing
    if 'ft.UserControl' in content:
        print(f"  ⚠️  {filepath} has UserControl - needs manual fix")
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Fixed: {filepath}")
        return True
    return False

def main():
    """Fix all Python files"""
    print("Fixing Flet API compatibility issues...")
    
    fixed_count = 0
    needs_manual = []
    
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_file(filepath):
                    fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} files automatically")
    
    if needs_manual:
        print(f"\n⚠️  {len(needs_manual)} files need manual UserControl fixes:")
        for f in needs_manual:
            print(f"   - {f}")

if __name__ == "__main__":
    main()