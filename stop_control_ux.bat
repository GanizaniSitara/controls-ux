@echo off
echo Stopping Control-UX Platform...
echo.

REM Kill API server
echo Stopping API server...
taskkill /FI "WINDOWTITLE eq Control-UX API*" /F 2>nul
taskkill /FI "WINDOWTITLE eq uvicorn*" /F 2>nul

REM Kill UI server  
echo Stopping UI server...
taskkill /FI "WINDOWTITLE eq Control-UX UI*" /F 2>nul
taskkill /FI "WINDOWTITLE eq npm*" /F 2>nul

REM Kill node processes on port 3004
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3004" ^| find "LISTENING"') do taskkill /f /pid %%a 2>nul

REM Kill python processes on port 8002
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8002" ^| find "LISTENING"') do taskkill /f /pid %%a 2>nul

echo.
echo Control-UX stopped.
pause