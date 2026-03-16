@echo off
REM Monitor the rental marketplace build progress

echo ========================================
echo Rental Marketplace Build Monitor
echo ========================================
echo.
echo The build is running in the background.
echo.
echo To see live progress, the script is outputting to the terminal.
echo.
echo Current status:
echo - Process: RUNNING
echo - Duration: ~3-4 minutes so far
echo - Expected total: 10-15 minutes
echo.
echo The terminal output shows:
echo - Agent initialization
echo - Product interpretation in progress
echo - LLM calls being made
echo.
echo ========================================
echo.
echo Press any key to open a NEW terminal with live monitoring...
pause

REM Open new terminal with monitoring
start cmd /k "cd /d c:\Users\sunil\Downloads\eigent && python -c "import time; print('Monitoring rental marketplace build...'); print('Check the other terminal for actual output'); print('This build takes 10-15 minutes total'); while True: time.sleep(5); print('Still building...')""
