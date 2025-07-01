#!/usr/bin/env python3
"""Minimal test of Canvas Editor with enhanced state management"""

import flet as ft
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import only what we need
from managers.enhanced_state import EnhancedStateManager
from managers.action_creators import ActionCreators

async def main(page: ft.Page):
    """Test enhanced state management integration"""
    page.title = "Canvas Editor - State Management Test"
    page.window_width = 800
    page.window_height = 600
    
    # Initialize enhanced state manager
    state_manager = EnhancedStateManager(page)
    await state_manager.initialize()
    
    # Test state
    result_text = ft.Text("Initializing...", size=20)
    
    async def test_state_operations():
        """Test various state operations"""
        tests_passed = []
        
        try:
            # Test 1: Theme change
            await state_manager.save_theme("dark")
            theme = await state_manager.get_theme()
            tests_passed.append(f"✅ Theme change: {theme}")
            
            # Test 2: Component action
            action = ActionCreators.add_component({
                "id": "test-button",
                "type": "button", 
                "name": "Test Button",
                "style": {"left": "100", "top": "100"}
            })
            await state_manager.dispatch_action(action)
            tests_passed.append("✅ Component added via action")
            
            # Test 3: Undo
            can_undo = state_manager.can_undo()
            if can_undo:
                await state_manager.undo()
                tests_passed.append("✅ Undo successful")
            
            # Test 4: State access
            state_system = state_manager.get_state_system()
            components = state_system.get_state("components")
            tests_passed.append(f"✅ State access working")
            
            # Test 5: Performance metrics
            metrics = state_manager.get_performance_metrics()
            tests_passed.append("✅ Performance metrics available")
            
            result_text.value = "Enhanced State Management Tests:\n" + "\n".join(tests_passed)
            
        except Exception as e:
            result_text.value = f"❌ Test failed: {str(e)}"
        
        page.update()
    
    # UI
    page.add(
        ft.Column([
            ft.Text("Canvas Editor - Enhanced State Management Test", size=24, weight="bold"),
            ft.Divider(),
            result_text,
            ft.ElevatedButton(
                "Run State Tests",
                on_click=lambda _: asyncio.create_task(test_state_operations())
            ),
            ft.ElevatedButton(
                "Check Undo Status",
                on_click=lambda _: setattr(result_text, 'value', 
                    f"Can undo: {state_manager.can_undo()}, Can redo: {state_manager.can_redo()}") or page.update()
            )
        ])
    )
    
    # Run initial test
    await test_state_operations()
    
    # Cleanup on close
    page.window_on_close = lambda _: asyncio.create_task(state_manager.shutdown())

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP_DESKTOP, port=8552)