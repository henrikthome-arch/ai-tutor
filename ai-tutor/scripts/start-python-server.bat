@echo off
echo Starting AI Tutor Data Server (Python version)
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found, starting server...
echo Server will be available at: http://localhost:3000
echo Health check: http://localhost:3000/health
echo Tools manifest: http://localhost:3000/mcp/tools
echo.
echo Press Ctrl+C to stop the server
echo.

python ../backend/session-enhanced-server.py

pause