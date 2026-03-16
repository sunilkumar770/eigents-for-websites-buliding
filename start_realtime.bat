@echo off
REM Quick Start - Real-time Agent Monitoring

echo ========================================
echo Real-time Agent Monitoring
echo ========================================
echo.
echo Choose how you want to interact with agents:
echo.
echo 1. CLI with live progress (Easiest)
echo 2. Python real-time monitor
echo 3. WebSocket dashboard (Browser)
echo 4. Start API server only
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto cli
if "%choice%"=="2" goto python
if "%choice%"=="3" goto websocket
if "%choice%"=="4" goto api
goto end

:cli
echo.
echo Starting CLI with live progress...
echo.
set /p prompt="Enter your app idea: "
python api/cli.py create "%prompt%" --watch
goto end

:python
echo.
echo Starting Python real-time monitor...
echo.
python examples/realtime_monitor.py
goto end

:websocket
echo.
echo Starting API server and opening dashboard...
echo.
start python api/api_server.py
timeout /t 3 /nobreak >nul
start examples/websocket_client.html
echo.
echo Dashboard opened in browser!
echo API server running on http://localhost:8000
echo Press Ctrl+C to stop
pause
goto end

:api
echo.
echo Starting API server...
echo Visit: http://localhost:8000/docs
echo.
python api/api_server.py
goto end

:end
