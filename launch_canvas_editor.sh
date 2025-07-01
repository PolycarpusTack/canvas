#!/bin/bash
# Canvas Editor Launcher for Linux/Mac
# Make this file executable: chmod +x launch_canvas_editor.sh

echo ""
echo "=============================="
echo "   Canvas Editor Launcher"
echo "=============================="
echo ""

# Change to the script directory
cd "$(dirname "$0")"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Run the launcher
echo "Starting Canvas Editor..."
python3 launch_canvas_editor.py

# Check exit status
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to start Canvas Editor"
    read -p "Press Enter to exit..."
fi