#!/usr/bin/env python3
"""
Minimal Canvas Editor test to identify blank screen issue
"""

import flet as ft
import asyncio
import traceback

class MinimalCanvas:
    def __init__(self):
        self.page = None
    
    async def main(self, page: ft.Page):
        """Minimal main method to test step by step"""
        try:
            print("🔍 Step 1: Setting up page...")
            self.page = page
            page.title = "Minimal Canvas Test"
            page.padding = 0
            page.theme_mode = ft.ThemeMode.LIGHT
            print("   ✓ Page setup complete")
            
            print("🔍 Step 2: Adding simple text...")
            page.add(ft.Text("Hello, Canvas Editor!", size=20))
            print("   ✓ Text added")
            
            print("🔍 Step 3: Adding basic layout...")
            page.add(
                ft.Row([
                    ft.Container(
                        content=ft.Text("Sidebar"),
                        width=80,
                        height=600,
                        bgcolor=ft.Colors.BLUE_100
                    ),
                    ft.Container(
                        content=ft.Text("Components"),
                        width=280,
                        height=600,
                        bgcolor=ft.Colors.GREEN_100
                    ),
                    ft.Container(
                        content=ft.Text("Canvas"),
                        expand=True,
                        height=600,
                        bgcolor=ft.Colors.GREY_100
                    ),
                    ft.Container(
                        content=ft.Text("Properties"),
                        width=320,
                        height=600,
                        bgcolor=ft.Colors.ORANGE_100
                    )
                ])
            )
            print("   ✓ Layout added")
            
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Minimal test successful!"),
                    duration=3000
                )
            )
            print("🎉 All steps completed successfully")
            
        except Exception as e:
            print(f"❌ Error in step: {e}")
            traceback.print_exc()
            page.add(ft.Text(f"Error: {e}", color=ft.Colors.RED))

def launch_minimal():
    print("🚀 Starting minimal Canvas Editor test...")
    try:
        canvas = MinimalCanvas()
        ft.app(
            target=canvas.main,
            view=ft.AppView.WEB_BROWSER,
            port=8552,
            assets_dir=None
        )
    except Exception as e:
        print(f"❌ Launch error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    launch_minimal()