"""
Enhanced Canvas Editor - Integrated Entry Point
Production-ready entry point with comprehensive error handling and logging

CLAUDE.md Implementation:
- #2.1.1: Comprehensive error handling and logging
- #1.5: Performance-optimized application startup
- #3.1: Clean application initialization
- #9.1: Accessible error reporting
"""

import flet as ft
import asyncio
import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import enhanced application
from app_integrated import create_enhanced_canvas_editor


def setup_logging():
    """
    Set up comprehensive logging system
    
    CLAUDE.md Implementation:
    - #12.1: Production logging configuration
    - #2.1.1: Error tracking and debugging
    """
    try:
        # Create logs directory
        logs_dir = Path(__file__).parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Configure logging
        log_filename = logs_dir / f"canvas_editor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Set specific logger levels
        logging.getLogger('flet').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        
        logger = logging.getLogger(__name__)
        logger.info("Logging system initialized")
        logger.info(f"Log file: {log_filename}")
        
        return logger
        
    except Exception as e:
        print(f"Failed to setup logging: {e}")
        # Fallback to basic logging
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)


async def main(page: ft.Page):
    """
    Enhanced main entry point for Canvas Editor
    
    CLAUDE.md Implementation:
    - #2.1.1: Comprehensive error handling
    - #1.5: Performance-optimized initialization
    - #9.1: Accessible error reporting
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Enhanced Canvas Editor...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Flet version: {ft.__version__}")
        
        # Create enhanced editor instance
        editor = create_enhanced_canvas_editor(page)
        logger.info("Enhanced Canvas Editor instance created")
        
        # Initialize the editor
        await editor.initialize()
        logger.info("Enhanced Canvas Editor initialized successfully")
        
        # Set up global error handler
        def handle_unhandled_exception(loop, context):
            """Handle unhandled asyncio exceptions"""
            try:
                exception = context.get('exception')
                if exception:
                    logger.error(f"Unhandled exception: {exception}")
                    logger.error(f"Exception context: {context}")
                    
                    # Show error to user if possible
                    if hasattr(editor, 'integrated_system') and editor.integrated_system:
                        asyncio.create_task(
                            editor.integrated_system._show_error_feedback(
                                f"Unexpected error: {str(exception)}"
                            )
                        )
                else:
                    logger.error(f"Unhandled error context: {context}")
            except Exception as e:
                logger.error(f"Error in exception handler: {e}")
        
        # Set exception handler for asyncio loop
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(handle_unhandled_exception)
        
        logger.info("Enhanced Canvas Editor started successfully")
        
    except Exception as e:
        logger.error(f"Critical error initializing Canvas Editor: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Show critical error dialog
        await show_critical_error_dialog(page, e)


async def show_critical_error_dialog(page: ft.Page, error: Exception):
    """
    Show critical error dialog when initialization fails
    
    CLAUDE.md Implementation:
    - #2.1.1: Graceful error handling
    - #9.1: Accessible error reporting
    """
    try:
        # Set basic page properties
        page.title = "Canvas Editor - Critical Error"
        page.theme_mode = ft.ThemeMode.LIGHT
        
        # Create error dialog content
        error_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.ERROR, color="#EF4444", size=32),
                ft.Text("Critical Error", size=20, weight=ft.FontWeight.BOLD)
            ], spacing=12),
            content=ft.Container(
                width=500,
                content=ft.Column([
                    ft.Text(
                        "Canvas Editor failed to start due to a critical error:",
                        size=16,
                        color="#374151"
                    ),
                    ft.Container(
                        bgcolor="#FEE2E2",
                        border_radius=8,
                        padding=12,
                        margin=ft.margin.symmetric(vertical=16),
                        content=ft.Text(
                            str(error),
                            size=14,
                            color="#7F1D1D",
                            selectable=True
                        )
                    ),
                    ft.Text(
                        "Possible solutions:",
                        size=14,
                        weight=ft.FontWeight.W_500,
                        color="#374151"
                    ),
                    ft.Column([
                        ft.Text("• Restart the application", size=12, color="#6B7280"),
                        ft.Text("• Check system requirements", size=12, color="#6B7280"),
                        ft.Text("• Update application dependencies", size=12, color="#6B7280"),
                        ft.Text("• Contact support if issue persists", size=12, color="#6B7280")
                    ], spacing=4)
                ], spacing=8)
            ),
            actions=[
                ft.Row([
                    ft.TextButton(
                        "Copy Error Details",
                        on_click=lambda e: copy_error_to_clipboard(page, error)
                    ),
                    ft.ElevatedButton(
                        "Close Application",
                        on_click=lambda e: page.window.close(),
                        style=ft.ButtonStyle(bgcolor="#EF4444", color="#FFFFFF")
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=8)
            ]
        )
        
        # Show dialog
        page.overlay.append(error_dialog)
        error_dialog.open = True
        page.update()
        
    except Exception as dialog_error:
        # Fallback if dialog creation fails
        print(f"Critical error dialog failed: {dialog_error}")
        print(f"Original error: {error}")
        
        # Create minimal error display
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("Critical Error", size=24, color="#EF4444"),
                    ft.Text(str(error), size=16, color="#374151"),
                    ft.ElevatedButton("Close", on_click=lambda e: page.window.close())
                ], spacing=16),
                alignment=ft.alignment.center,
                expand=True
            )
        )


def copy_error_to_clipboard(page: ft.Page, error: Exception):
    """
    Copy error details to clipboard for support
    
    CLAUDE.md Implementation:
    - #9.1: Accessible error reporting
    - #2.1.1: Comprehensive error information
    """
    try:
        error_details = f"""Canvas Editor Critical Error Report
Generated: {datetime.now().isoformat()}
Python Version: {sys.version}
Flet Version: {ft.__version__}

Error Type: {type(error).__name__}
Error Message: {str(error)}

Traceback:
{traceback.format_exc()}

System Information:
Platform: {sys.platform}
"""
        
        # Copy to clipboard (note: actual clipboard access would require additional libraries)
        # For now, we'll show the details in a text field for manual copying
        details_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Error Details"),
            content=ft.Container(
                width=600,
                height=400,
                content=ft.TextField(
                    value=error_details,
                    multiline=True,
                    read_only=True,
                    min_lines=20,
                    max_lines=20,
                    border_color="#D1D5DB"
                )
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: close_details_dialog(page))
            ]
        )
        
        page.overlay.append(details_dialog)
        details_dialog.open = True
        page.update()
        
    except Exception as e:
        print(f"Failed to copy error details: {e}")


def close_details_dialog(page: ft.Page):
    """Close error details dialog"""
    try:
        if len(page.overlay) > 1:
            page.overlay.pop()
            page.update()
    except Exception as e:
        print(f"Error closing details dialog: {e}")


def check_system_requirements():
    """
    Check system requirements before starting
    
    CLAUDE.md Implementation:
    - #2.1.1: Proactive requirement validation
    - #1.5: Performance prerequisite checking
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            raise RuntimeError("Python 3.8 or higher is required")
        
        # Check required modules
        required_modules = ['flet', 'asyncio', 'pathlib', 'typing']
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            raise RuntimeError(f"Missing required modules: {', '.join(missing_modules)}")
        
        # Check disk space (optional)
        try:
            import shutil
            free_space = shutil.disk_usage('.').free
            if free_space < 100 * 1024 * 1024:  # 100MB
                logger.warning("Low disk space detected")
        except Exception:
            pass  # Disk space check is optional
        
        logger.info("System requirements check passed")
        return True
        
    except Exception as e:
        logger.error(f"System requirements check failed: {e}")
        return False


def main_entry():
    """
    Main entry point with comprehensive error handling
    
    CLAUDE.md Implementation:
    - #2.1.1: Production-grade error handling
    - #1.5: Optimized application startup
    """
    # Set up logging first
    logger = setup_logging()
    
    try:
        logger.info("=" * 60)
        logger.info("Enhanced Canvas Editor Starting")
        logger.info("=" * 60)
        
        # Check system requirements
        if not check_system_requirements():
            print("System requirements check failed. Please check the logs.")
            sys.exit(1)
        
        # Start the application
        logger.info("Starting Flet application...")
        
        ft.app(
            target=main,
            view=ft.AppView.FLET_APP,
            port=8550,
            assets_dir="assets" if Path("assets").exists() else None
        )
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error in main entry: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        logger.info("Enhanced Canvas Editor shutdown")


if __name__ == "__main__":
    main_entry()