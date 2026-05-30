@echo off
title Hermes Agent Web UI
chcp 65001 >nul

set "PROJ_DIR=C:\Users\User\PycharmProjects\HERMES AGENT\hermes-agent-windows-ru"
set "HERMES_HOME=%USERPROFILE%\.hermes"

cls
echo.
echo ==========================================
echo     Hermes Agent Web UI Launcher
echo ==========================================
echo.

:: Check venv
if not exist "%PROJ_DIR%\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo         Expected: %PROJ_DIR%\venv\Scripts\python.exe
    echo.
    echo Solution: Run these commands in PowerShell:
    echo   cd /d "%PROJ_DIR%"
    echo   python -m venv venv
    echo   .\venv\Scripts\pip install -e .
    pause
    exit /b 1
)

:: Kill stale processes
echo [1/4] Cleaning stale processes...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: Remove stale PID files
for %%f in (gateway.pid gateway.lock webui.pid webui.lock) do (
    if exist "%HERMES_HOME%\%%f" del /q "%HERMES_HOME%\%%f" 2>nul
)

:: Set environment
echo [2/4] Setting environment...
set PYTHONIOENCODING=utf-8
set API_SERVER_ENABLED=true

:: Launch server
echo [3/4] Starting Hermes Agent Web UI...
echo [4/4] Opening browser...
cd /d "%PROJ_DIR%"

:: Open browser
start "" http://localhost:9119 2>nul

:: Run server (this window stays open)
"%PROJ_DIR%\venv\Scripts\python.exe" -m hermes_cli.main web

echo.
echo Server stopped.
pause
