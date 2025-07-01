#!/usr/bin/env python3
"""
Canvas Editor GUI Launcher
A simple GUI to launch the Canvas Editor with options
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import webbrowser
import socket
import sys
import os
import time
import platform
from pathlib import Path


class CanvasEditorLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Canvas Editor Launcher")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Set icon if available
        try:
            if platform.system() == "Windows":
                self.root.iconbitmap(default='icon.ico')
        except:
            pass
        
        # Variables
        self.port_var = tk.StringVar(value="8550")
        self.auto_browser_var = tk.BooleanVar(value=True)
        self.server_process = None
        self.is_running = False
        
        self.setup_ui()
        self.center_window()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_ui(self):
        """Setup the user interface"""
        # Title
        title_frame = ttk.Frame(self.root, padding="20")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame,
            text="🎨 Canvas Editor",
            font=("Arial", 18, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Visual Web Component Builder",
            font=("Arial", 10)
        )
        subtitle_label.pack()
        
        # Settings frame
        settings_frame = ttk.LabelFrame(self.root, text="Settings", padding="10")
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Port setting
        port_frame = ttk.Frame(settings_frame)
        port_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(port_frame, text="Port:").pack(side=tk.LEFT, padx=(0, 10))
        port_spinbox = ttk.Spinbox(
            port_frame,
            from_=3000,
            to=9999,
            textvariable=self.port_var,
            width=10
        )
        port_spinbox.pack(side=tk.LEFT)
        
        # Auto-open browser checkbox
        browser_check = ttk.Checkbutton(
            settings_frame,
            text="Open browser automatically",
            variable=self.auto_browser_var
        )
        browser_check.pack(fill=tk.X, pady=5)
        
        # Status label
        self.status_label = ttk.Label(
            settings_frame,
            text="Status: Not running",
            foreground="gray"
        )
        self.status_label.pack(fill=tk.X, pady=10)
        
        # Buttons frame
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X)
        
        # Launch button
        self.launch_button = ttk.Button(
            button_frame,
            text="Launch Canvas Editor",
            command=self.toggle_server,
            style="Accent.TButton"
        )
        self.launch_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Open browser button
        self.browser_button = ttk.Button(
            button_frame,
            text="Open Browser",
            command=self.open_browser,
            state=tk.DISABLED
        )
        self.browser_button.pack(side=tk.LEFT, padx=5)
        
        # Configure styles
        style = ttk.Style()
        style.configure("Accent.TButton", foreground="white")
    
    def is_port_available(self, port):
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return True
        except:
            return False
    
    def find_available_port(self, start_port):
        """Find an available port"""
        port = start_port
        while port < start_port + 100:
            if self.is_port_available(port):
                return port
            port += 1
        return None
    
    def toggle_server(self):
        """Start or stop the server"""
        if self.is_running:
            self.stop_server()
        else:
            self.start_server()
    
    def start_server(self):
        """Start the Canvas Editor server"""
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            return
        
        # Check if port is available
        available_port = self.find_available_port(port)
        if not available_port:
            messagebox.showerror("Error", f"No available ports found starting from {port}")
            return
        
        if available_port != port:
            self.port_var.set(str(available_port))
            messagebox.showinfo("Port Changed", f"Port {port} was busy. Using port {available_port} instead.")
        
        # Update UI
        self.launch_button.config(text="Stop Server")
        self.status_label.config(text=f"Status: Starting on port {available_port}...", foreground="orange")
        self.browser_button.config(state=tk.NORMAL)
        
        # Start server in thread
        thread = threading.Thread(target=self.run_server, args=(available_port,))
        thread.daemon = True
        thread.start()
    
    def run_server(self, port):
        """Run the server process"""
        # Change to project directory
        project_dir = Path(__file__).parent
        os.chdir(project_dir)
        
        # Prepare command
        if platform.system() == "Windows":
            python_cmd = "python"
        else:
            python_cmd = "python3"
        
        cmd = [
            python_cmd,
            "-m",
            "flet",
            "run",
            "--web",
            "--port",
            str(port),
            "--host",
            "localhost",
            "src/main.py"
        ]
        
        try:
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Update status
            self.is_running = True
            self.root.after(1000, lambda: self.update_status(f"Status: Running on http://localhost:{port}", "green"))
            
            # Auto-open browser if enabled
            if self.auto_browser_var.get():
                time.sleep(2)
                self.open_browser()
            
            # Wait for process
            self.server_process.wait()
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to start server: {e}"))
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.reset_ui())
    
    def stop_server(self):
        """Stop the server"""
        if self.server_process:
            self.server_process.terminate()
            self.status_label.config(text="Status: Stopping...", foreground="orange")
    
    def open_browser(self):
        """Open the browser"""
        if self.is_running:
            port = self.port_var.get()
            url = f"http://localhost:{port}"
            webbrowser.open(url)
    
    def update_status(self, text, color):
        """Update status label"""
        self.status_label.config(text=text, foreground=color)
    
    def reset_ui(self):
        """Reset UI to initial state"""
        self.launch_button.config(text="Launch Canvas Editor")
        self.status_label.config(text="Status: Not running", foreground="gray")
        self.browser_button.config(state=tk.DISABLED)
        self.server_process = None
    
    def run(self):
        """Run the launcher"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            if messagebox.askokcancel("Quit", "The server is still running. Do you want to stop it and quit?"):
                self.stop_server()
                time.sleep(1)  # Give it time to stop
                self.root.destroy()
        else:
            self.root.destroy()


if __name__ == "__main__":
    launcher = CanvasEditorLauncher()
    launcher.run()