@echo off
title Hermes Agent Web UI
chcp 65001 >nul

set "PROJ_DIR=C:\Users\User\PycharmProjects\HERMES AGENT\hermes-agent-windows-ru"
set "HERMES_HOME=%USERPROFILE%\.hermes"

cls
echo ==========================================
echo     Hermes Agent Web UI Launcher
echo ==========================================
echo Timestamp: %DATE% %TIME%
echo.

:: --- Kill previous processes ---
echo [PRE] Killing previous Hermes processes...
echo         Ports: 8642 (gateway), 9119 (webui)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /c:":8642 " ^| findstr LISTENING 2^>nul') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /c:":9119 " ^| findstr LISTENING 2^>nul') do taskkill /F /PID %%a >nul 2>&1
del /q "%HERMES_HOME%\gateway.pid" 2>nul
del /q "%HERMES_HOME%\gateway.lock" 2>nul
del /q "%HERMES_HOME%\webui.pid" 2>nul
del /q "%HERMES_HOME%\webui.lock" 2>nul
timeout /t 2 /nobreak >nul
echo.

:: Check venv
if not exist "%PROJ_DIR%\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo         Expected: %PROJ_DIR%\venv\Scripts\python.exe
    echo.
    echo Solution: Create venv first:
    echo   cd /d "%PROJ_DIR%"
    echo   python -m venv venv
    echo   .\venv\Scripts\pip install -e .
    pause
    exit /b 1
)

:: Set environment
echo [1/3] Setting environment...
set PYTHONIOENCODING=utf-8
set API_SERVER_ENABLED=true

:: Launch
echo [2/3] Starting Hermes Agent Web UI...
echo [3/3] Opening browser...
cd /d "%PROJ_DIR%"

start "" http://localhost:9119 2>nul

echo.
echo ==========================================
echo  Hermes Agent is running.
echo  Close this window to stop the server.
echo ==========================================
echo.

"%PROJ_DIR%\venv\Scripts\python.exe" -m hermes_cli.main web

echo.
echo Server stopped.
pause
