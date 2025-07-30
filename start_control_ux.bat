@echo off
echo Starting Control-UX Platform...
echo.

REM Start API server
echo Starting API server on port 8002...
start "Control-UX API" cmd /k "cd api && venv\Scripts\activate && uvicorn app:app --reload --port 8002"

REM Wait a moment for API to start
timeout /t 3 /nobreak > nul

REM Start UI server
echo Starting UI server on port 3004...
start "Control-UX UI" cmd /k "cd ui && npm start"

echo.
echo Control-UX is starting up...
echo API: http://localhost:8002
echo UI:  http://localhost:3004
echo.
echo Press any key to close this window (servers will continue running)
pause > nul