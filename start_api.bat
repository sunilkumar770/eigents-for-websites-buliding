@echo off
REM API server launcher for Windows

echo ========================================
echo Multi-Agent System - API Server
echo ========================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Start API server
echo Starting API server on http://localhost:8000
echo Press Ctrl+C to stop
echo.
python api/api_server.py
