#!/usr/bin/env python3
"""
Canvas Editor Launcher
Starts the Flet server and opens the browser automatically
"""

import subprocess
import sys
import time
import webbrowser
import os
import socket
import threading
import platform
from pathlib import Path

# Configuration
DEFAULT_PORT = 8550
DEFAULT_HOST = "localhost"
BROWSER_DELAY = 2  # seconds to wait before opening browser


def is_port_available(port: int, host: str = "localhost") -> bool:
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return True
    except socket.error:
        return False


def find_available_port(start_port: int = DEFAULT_PORT) -> int:
    """Find an available port starting from the given port"""
    port = start_port
    while port < start_port + 100:  # Try 100 ports
        if is_port_available(port):
            return port
        port += 1
    raise RuntimeError(f"No available ports found starting from {start_port}")


def open_browser(url: str, delay: float = BROWSER_DELAY):
    """Open browser after a delay"""
    time.sleep(delay)
    print(f"Opening browser at {url}...")
    webbrowser.open(url)


def launch_canvas_editor():
    """Launch the Canvas Editor"""
    print("🎨 Canvas Editor Launcher")
    print("========================")
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    print(f"Working directory: {project_dir}")
    
    # Find available port
    try:
        port = find_available_port(DEFAULT_PORT)
        print(f"✓ Found available port: {port}")
    except RuntimeError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
    
    # Prepare the command
    if platform.system() == "Windows":
        python_cmd = "python"
    else:
        python_cmd = "python3"
    
    # Command to run the Flet app
    cmd = [
        python_cmd,
        "-m",
        "flet",
        "run",
        "--web",
        "--port",
        str(port),
        "--host",
        DEFAULT_HOST,
        "src/main.py"
    ]
    
    # URL for the browser
    url = f"http://{DEFAULT_HOST}:{port}"
    
    # Start browser opener in a separate thread
    browser_thread = threading.Thread(target=open_browser, args=(url,))
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start the server
    print(f"\n🚀 Starting Canvas Editor server on {url}")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        # Run the server
        process = subprocess.Popen(cmd)
        process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down server...")
        if process:
            process.terminate()
            process.wait()
        print("✓ Server stopped")
    except Exception as e:
        print(f"\n✗ Error running server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    launch_canvas_editor()