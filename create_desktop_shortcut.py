#!/usr/bin/env python3
"""
Create Desktop Shortcut for Canvas Editor
Creates a shortcut on Windows desktop
"""

import os
import sys
import platform
from pathlib import Path

def create_windows_shortcut():
    """Create a Windows desktop shortcut"""
    try:
        import win32com.client
    except ImportError:
        print("Error: pywin32 is required for creating Windows shortcuts")
        print("Install it with: pip install pywin32")
        return False
    
    # Get paths
    desktop = Path.home() / "Desktop"
    script_dir = Path(__file__).parent
    launcher_path = script_dir / "launch_canvas_editor.bat"
    
    if not launcher_path.exists():
        print(f"Error: Launcher not found at {launcher_path}")
        return False
    
    # Create shortcut
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut_path = str(desktop / "Canvas Editor.lnk")
    shortcut = shell.CreateShortCut(shortcut_path)
    
    shortcut.Targetpath = str(launcher_path)
    shortcut.WorkingDirectory = str(script_dir)
    shortcut.Description = "Launch Canvas Editor - Visual Web Component Builder"
    
    # Try to set icon if available
    icon_path = script_dir / "icon.ico"
    if icon_path.exists():
        shortcut.IconLocation = str(icon_path)
    
    shortcut.save()
    
    print(f"✓ Shortcut created at: {shortcut_path}")
    return True

def create_linux_desktop_entry():
    """Create a Linux desktop entry"""
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    
    script_dir = Path(__file__).parent
    launcher_path = script_dir / "launch_canvas_editor.sh"
    
    if not launcher_path.exists():
        print(f"Error: Launcher not found at {launcher_path}")
        return False
    
    # Make launcher executable
    os.chmod(launcher_path, 0o755)
    
    desktop_entry = f"""[Desktop Entry]
Name=Canvas Editor
Comment=Visual Web Component Builder
Exec={launcher_path}
Terminal=false
Type=Application
Categories=Development;WebDevelopment;
Path={script_dir}
"""
    
    desktop_file = desktop_dir / "canvas-editor.desktop"
    desktop_file.write_text(desktop_entry)
    
    # Make desktop entry executable
    os.chmod(desktop_file, 0o755)
    
    print(f"✓ Desktop entry created at: {desktop_file}")
    print("You may need to log out and back in for it to appear in your application menu")
    return True

def create_macos_alias():
    """Create a macOS alias"""
    print("For macOS:")
    print("1. Open Finder and navigate to the Canvas Editor folder")
    print("2. Right-click on 'launch_canvas_editor.sh'")
    print("3. Select 'Make Alias'")
    print("4. Drag the alias to your Desktop or Applications folder")
    return True

def main():
    """Main function"""
    print("Canvas Editor Desktop Shortcut Creator")
    print("=====================================")
    
    system = platform.system()
    
    if system == "Windows":
        success = create_windows_shortcut()
    elif system == "Linux":
        success = create_linux_desktop_entry()
    elif system == "Darwin":  # macOS
        success = create_macos_alias()
    else:
        print(f"Unsupported operating system: {system}")
        success = False
    
    if success:
        print("\n✓ Shortcut created successfully!")
    else:
        print("\n✗ Failed to create shortcut")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()