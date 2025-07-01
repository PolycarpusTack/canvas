# Canvas Editor Launch Options

This document describes the various ways to launch the Canvas Editor application.

## 🚀 Quick Start

### Windows Users
- **Double-click** `launch_canvas_editor.bat`
- Or run `python launch_canvas_editor.py` in Command Prompt

### Mac/Linux Users
- **Run** `./launch_canvas_editor.sh` in Terminal
- Or run `python3 launch_canvas_editor.py`

## 📋 Available Launchers

### 1. **Simple Python Launcher** (`launch_canvas_editor.py`)
- Cross-platform Python script
- Automatically finds available port
- Opens browser after server starts
- Shows server output in terminal

**Usage:**
```bash
python launch_canvas_editor.py
```

### 2. **Batch File** (`launch_canvas_editor.bat`) - Windows Only
- Double-click to launch
- No command line needed
- Checks Python installation
- Shows errors if any

### 3. **Shell Script** (`launch_canvas_editor.sh`) - Mac/Linux
- Make executable first: `chmod +x launch_canvas_editor.sh`
- Run with: `./launch_canvas_editor.sh`
- Checks Python 3 installation

### 4. **GUI Launcher** (`launch_gui.py`)
- Graphical interface
- Configure port
- Start/stop server
- Open browser button
- Shows server status

**Usage:**
```bash
python launch_gui.py
```

**Features:**
- Change port if default is busy
- Toggle auto-browser opening
- Visual status indicators
- Clean shutdown handling

## 🖥️ Creating Desktop Shortcuts

Run the shortcut creator:
```bash
python create_desktop_shortcut.py
```

This will:
- **Windows**: Create a `.lnk` file on Desktop
- **Linux**: Create a `.desktop` entry in applications menu
- **macOS**: Provide instructions for creating an alias

## 🔧 Manual Launch

If you prefer to launch manually:

```bash
# Navigate to project directory
cd /path/to/canvas

# Run with Flet
python -m flet run --web --port 8550 src/main.py
```

## 📝 Configuration Options

### Default Settings
- **Port**: 8550 (automatically finds next available if busy)
- **Host**: localhost
- **Browser**: Opens automatically after 2 seconds

### Custom Port
Edit the port in any launcher:
- `launch_canvas_editor.py`: Change `DEFAULT_PORT`
- `launch_gui.py`: Use the port spinner
- Manual: Add `--port YOUR_PORT`

## 🛠️ Troubleshooting

### Python Not Found
- Ensure Python 3.8+ is installed
- Add Python to system PATH
- Windows: Use Python installer from python.org

### Port Already in Use
- The launchers automatically find available ports
- Or manually specify a different port

### Browser Doesn't Open
- Check firewall settings
- Manually navigate to `http://localhost:8550`
- Ensure default browser is set

### Permission Denied (Linux/Mac)
```bash
chmod +x launch_canvas_editor.sh
```

## 🎯 Recommended Usage

1. **For Development**: Use `launch_canvas_editor.py` for console output
2. **For End Users**: Use GUI launcher or desktop shortcut
3. **For Testing**: Use manual launch with custom parameters

## 🔒 Security Notes

- Server runs on localhost only (not exposed to network)
- No authentication required for local development
- For production deployment, use proper web server configuration

## 📦 Dependencies

The launchers require:
- Python 3.8 or higher
- Flet framework (installed via requirements.txt)
- Modern web browser (Chrome, Firefox, Edge, Safari)

Optional for GUI launcher:
- tkinter (usually included with Python)

Optional for Windows shortcuts:
- pywin32: `pip install pywin32`