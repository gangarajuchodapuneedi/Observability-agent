@echo off
echo ============================================================
echo Setting up Virtual Environment for Observability Agent
echo ============================================================
echo.

REM Check if venv already exists
if exist "venv" (
    echo Virtual environment already exists.
    echo Activating and installing/updating dependencies...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    echo.
    echo Setup complete! You can now run: start_server.bat
) else (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment!
        echo Make sure Python is installed and in your PATH.
        pause
        exit /b 1
    )
    
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    
    echo Installing dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
    
    echo.
    echo ============================================================
    echo Setup complete!
    echo ============================================================
    echo.
    echo To start the server, run: start_server.bat
    echo Or manually activate venv and run: python src/api_server.py
    echo.
)

pause
