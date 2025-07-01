#!/usr/bin/env python3
"""
Fix Flet 0.24.1 compatibility by updating color references
"""

import re

def fix_flet_compatibility():
    """Update ft.Colors to ft.colors for Flet 0.24.1"""
    main_file = '/mnt/c/Projects/canvas/src/main.py'
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix ft.Colors -> ft.colors
    content = content.replace('ft.Colors.', 'ft.colors.')
    
    # Fix ft.Icons -> ft.icons (just in case)
    content = content.replace('ft.Icons.', 'ft.icons.')
    
    # Fix ft.MouseCursor constants
    content = content.replace('ft.MouseCursor.RESIZE_LEFT_RIGHT', 'ft.MouseCursor.RESIZE_LEFT_RIGHT')
    content = content.replace('ft.MouseCursor.RESIZE_UP_DOWN', 'ft.MouseCursor.RESIZE_UP_DOWN')
    content = content.replace('ft.MouseCursor.BASIC', 'ft.MouseCursor.BASIC')
    
    # Write back
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed Flet compatibility - updated color references")

if __name__ == "__main__":
    fix_flet_compatibility()