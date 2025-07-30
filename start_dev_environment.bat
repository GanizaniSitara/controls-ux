setlocal enabledelayedexpansion

echo ===================================================
echo    Fitness Functions Development Environment Setup
echo ===================================================

REM Ask for proxy information
set /p USE_PROXY="Do you need to use a proxy? (y/n): "
if /i "%USE_PROXY%"=="y" (
    set /p PROXY_STRING="Enter your proxy URL (e.g., http://proxy.example.com:8080): "
    set "HTTP_PROXY=%PROXY_STRING%"
    set "HTTPS_PROXY=%PROXY_STRING%"
    echo Proxy has been set to: %PROXY_STRING%
) else (
    echo No proxy will be used.
)

REM Create and activate Python virtual environment for API
echo.
echo Setting up API (Backend)...
cd api

if exist venv (
    echo Found existing virtual environment.
) else (
    echo Creating new Python virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
if /i "%USE_PROXY%"=="y" (
    pip install -r requirements.txt --proxy %PROXY_STRING%
) else (
    pip install -r requirements.txt
)

REM Keep this shell for the API server, but start it after UI setup
echo.
echo API setup complete!

REM Setup UI (Frontend) in a new command window
echo.
echo Setting up UI (Frontend)...
cd ..
cd ui

echo Installing npm packages...
if /i "%USE_PROXY%"=="y" (
    set "npm_config_proxy=%PROXY_STRING%"
    set "npm_config_https_proxy=%PROXY_STRING%"
    echo Using proxy for npm: %PROXY_STRING%
)

call npm install

REM Start UI in a separate window and return to this window
echo.
echo Starting UI server in a new window...
start cmd /k "cd %cd% && npm start"

REM Go back to API directory and start the API server
echo.
echo Starting API server...
cd ..
cd api
echo Starting uvicorn server on http://localhost:8000
call uvicorn app:app --reload

REM Deactivate virtual environment before exit
call deactivate

echo.
echo Development environment shutdown. Have a nice day!
