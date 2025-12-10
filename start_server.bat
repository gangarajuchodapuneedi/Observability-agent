@echo off
echo ============================================================
echo Starting Observability Agent API Server
echo ============================================================
echo.

REM Set Ollama model to tinyllama for faster responses (override any existing env var)
set OLLAMA_MODEL=tinyllama
echo Using Ollama model: %OLLAMA_MODEL%

REM Check if virtual environment exists and use it
if exist "venv\Scripts\python.exe" (
    echo Using virtual environment...
    call venv\Scripts\activate.bat
    REM Set PYTHONPATH to current directory so src module can be found
    set PYTHONPATH=%CD%
    python -m src.api_server
    if %errorlevel% neq 0 (
        python src/api_server.py
    )
) else (
    echo No virtual environment found, using system Python...
    REM Set PYTHONPATH to current directory so src module can be found
    set PYTHONPATH=%CD%
    REM Set Ollama model to tinyllama (override any existing env var)
    set OLLAMA_MODEL=tinyllama
    REM Try different Python commands
    python -m src.api_server 2>nul
    if %errorlevel% neq 0 (
        python src/api_server.py 2>nul
        if %errorlevel% neq 0 (
            py src/api_server.py 2>nul
            if %errorlevel% neq 0 (
                py -m src.api_server 2>nul
                if %errorlevel% neq 0 (
                    echo ERROR: Could not find Python!
                    echo Please ensure Python is installed and in your PATH.
                    echo.
                    echo Try running manually:
                    echo   python src/api_server.py
                    echo   OR
                    echo   python -m src.api_server
                    pause
                )
            )
        )
    )
)

