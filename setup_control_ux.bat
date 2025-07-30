@echo off
echo Setting up Control-UX Platform...
echo.

REM Check if we're in the right directory
if not exist "api\requirements.txt" (
    echo ERROR: Please run this script from the control-ux directory
    pause
    exit /b 1
)

REM Setup API
echo Setting up API backend...
cd api
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Installing API dependencies...
call venv\Scripts\activate
pip install -r requirements.txt
cd ..

REM Setup UI
echo.
echo Setting up UI frontend...
cd ui
echo Installing UI dependencies...
npm install
cd ..

echo.
echo Setup complete!
echo.
echo To start Control-UX, run: start_control_ux.bat
echo To stop Control-UX, run: stop_control_ux.bat
echo.
pause