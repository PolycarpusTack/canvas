#!/usr/bin/env python3
"""
Canvas Editor - Main Entry Point
Run this file to start the Canvas Editor application
"""

import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now we can import from src
from src.main import main
import flet as ft

if __name__ == "__main__":
    print("🚀 Starting Canvas Editor...")
    print(f"📁 Project root: {project_root}")
    print(f"🐍 Python path includes: {project_root}")
    
    try:
        # Run the Flet app
        ft.app(
            target=main,
            view=ft.AppView.FLET_APP,
            port=8550
        )
    except KeyboardInterrupt:
        print("\n👋 Canvas Editor stopped by user")
    except Exception as e:
        print(f"❌ Error starting Canvas Editor: {e}")
        import traceback
        traceback.print_exc()