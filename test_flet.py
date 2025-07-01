"""
Simple test to verify Flet is working
Run: python test_flet.py
"""

import flet as ft

def main(page: ft.Page):
    page.title = "Canvas Editor - Flet Test"
    page.window.width = 600
    page.window.height = 400
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Test counter
    counter = ft.Text("0", size=40, weight=ft.FontWeight.BOLD)
    
    def increment(e):
        counter.value = str(int(counter.value) + 1)
        page.update()
    
    def decrement(e):
        counter.value = str(int(counter.value) - 1)
        page.update()
    
    page.add(
        ft.Column(
            controls=[
                ft.Text("✅ Flet is working!", size=24, color=ft.colors.GREEN),
                ft.Container(height=20),
                ft.Text("Test the counter:"),
                ft.Row(
                    controls=[
                        ft.IconButton(ft.icons.REMOVE, on_click=decrement),
                        counter,
                        ft.IconButton(ft.icons.ADD, on_click=increment),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Open Canvas Editor",
                    icon=ft.icons.LAUNCH,
                    on_click=lambda e: print("Ready to build Canvas Editor!")
                ),
                ft.Container(height=20),
                ft.Text(
                    "If you see this window, Flet is installed correctly!",
                    size=12,
                    color=ft.colors.GREY_600
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        )
    )

if __name__ == "__main__":
    ft.app(target=main)