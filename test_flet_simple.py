#!/usr/bin/env python3
"""Simple Flet test to verify installation"""

import flet as ft

def main(page: ft.Page):
    page.title = "Flet Test"
    page.add(ft.Text("Flet is working!"))
    print("Flet app created successfully")

if __name__ == "__main__":
    print("Starting Flet test...")
    ft.app(target=main, view=None, port=8551)
    print("Flet app completed")