@echo off
REM Quick demo launcher for Windows

echo ========================================
echo Multi-Agent System - Demo
echo ========================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Run demo
echo Running demo...
python demo.py

pause
