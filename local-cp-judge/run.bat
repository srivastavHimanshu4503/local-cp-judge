@echo off
setlocal enabledelayedexpansion

:: Switch to the directory containing this batch file
cd /d "%~dp0"

echo =====================================================================
echo                      Local CP Judge -- Launcher
echo =====================================================================
echo Working Directory: %CD%

:: Check for Python in PATH
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found in your system PATH.
    echo Please install Python 3.10+ from https://www.python.org/ and check "Add python.exe to PATH".
    pause
    exit /b 1
)

:: Create virtual environment if it does not already exist
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Virtual environment not detected. Creating .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment (.venv^).
        pause
        exit /b 1
    )
    echo [INFO] Installing dependencies from requirements.txt...
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo [INFO] Environment setup completed successfully.
)

:: Launch the default browser and start the web server
echo [INFO] Starting Local CP Judge on http://127.0.0.1:8080 ...
start "" "http://127.0.0.1:8080"

:: Start Uvicorn ASGI server
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8080
if errorlevel 1 (
    echo.
    echo [INFO] Server stopped or exited with an error.
    pause
)
