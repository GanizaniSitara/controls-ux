@echo off
setlocal enabledelayedexpansion

echo =========================================
echo    Fitness Functions Testing Strategy
echo =========================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js/npm is not installed or not in PATH
    pause
    exit /b 1
)

REM Run the Python test runner
echo Running Python test runner...
python test_runner.py

if %errorlevel% neq 0 (
    echo.
    echo Testing failed. Check the output above.
    pause
    exit /b 1
)

echo.
echo Testing completed successfully!
pause