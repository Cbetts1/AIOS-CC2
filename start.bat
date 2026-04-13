@echo off
REM AI-OS CC2 — Windows launcher
REM Usage: start.bat [terminal|web|none] [port]
REM Double-click this file, or run from Command Prompt

SET UI=%1
IF "%UI%"=="" SET UI=terminal

SET PORT=%2
IF "%PORT%"=="" SET PORT=1313

echo ======================================================
echo   AI-OS CC2 ^— Starting in %UI% mode on port %PORT%
echo ======================================================

REM Check Python is available
where python >nul 2>&1
IF ERRORLEVEL 1 (
    echo ERROR: Python not found.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

FOR /F "tokens=*" %%v IN ('python --version') DO echo   Python: %%v

IF "%UI%"=="web" (
    echo   Web UI will be at: http://localhost:%PORT%
    echo   Open that URL in your browser after launch.
)

REM Windows terminal UI requires windows-curses
IF "%UI%"=="terminal" (
    python -c "import curses" >nul 2>&1
    IF ERRORLEVEL 1 (
        echo   NOTE: curses not found. Installing windows-curses...
        pip install windows-curses
    )
)

echo.
python aios\main.py --ui %UI% --port %PORT%

IF ERRORLEVEL 1 (
    echo.
    echo AI-OS exited with an error. See above for details.
    pause
)
