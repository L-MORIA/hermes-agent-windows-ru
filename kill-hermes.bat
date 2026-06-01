@echo off
title Kill Hermes Agent Processes
echo Killing previous Hermes processes...
echo   Ports: 8642 (gateway), 9119 (webui)

:: Kill by ports
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /c:":8642 " ^| findstr LISTENING 2^>nul') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /c:":9119 " ^| findstr LISTENING 2^>nul') do taskkill /F /PID %%a >nul 2>&1

:: Remove stale PID files
set "HERMES_HOME=%USERPROFILE%\.hermes"
del /q "%HERMES_HOME%\gateway.pid" 2>nul
del /q "%HERMES_HOME%\gateway.lock" 2>nul
del /q "%HERMES_HOME%\webui.pid" 2>nul
del /q "%HERMES_HOME%\webui.lock" 2>nul

timeout /t 1 /nobreak >nul
