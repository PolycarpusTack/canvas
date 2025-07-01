@echo off
REM Canvas Editor Launcher for Windows
REM Double-click this file to start the Canvas Editor

echo.
echo ==============================
echo   Canvas Editor Launcher
echo ==============================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org
    pause
    exit /b 1
)

REM Run the launcher
echo Starting Canvas Editor...
python launch_canvas_editor.py

REM If the script exits, pause to show any error messages
if errorlevel 1 (
    echo.
    echo ERROR: Failed to start Canvas Editor
    pause
)