#!/usr/bin/env python3
"""
Update code for latest Flet version (0.28.3+)
"""

def fix_latest_flet():
    """Update code for latest Flet version"""
    main_file = '/mnt/c/Projects/canvas/src/main.py'
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Revert to newer API: ft.colors -> ft.Colors
    content = content.replace('ft.colors.', 'ft.Colors.')
    
    # Update other newer API elements
    content = content.replace('ft.AppView.FLET_APP', 'ft.AppView.FLET_APP_WEB')
    
    # Write back
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Updated code for latest Flet version")

if __name__ == "__main__":
    fix_latest_flet()