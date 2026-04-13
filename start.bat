@echo off
REM AI-OS CC2 — Windows launcher
REM Usage: start.bat [terminal|web|none] [port] [operator-token]
REM        start.bat check                      (preflight validation)
REM Double-click this file, or run from Command Prompt

REM ── Check mode ─────────────────────────────────────────────────────────────
IF /I "%1"=="check" (
    echo ======================================================
    echo   AI-OS CC2 ^— Preflight Check
    echo ======================================================
    where python >nul 2>&1
    IF ERRORLEVEL 1 (
        echo   ERROR: Python not found.
        pause & exit /b 1
    )
    FOR /F "tokens=*" %%v IN ('python --version') DO echo   Python: %%v
    IF NOT EXIST "aios\identity\identity.lock" (
        echo   ERROR: aios\identity\identity.lock not found.
        pause & exit /b 1
    )
    echo   identity.lock: found
    FOR /F "tokens=*" %%t IN ('python -c "import json,hashlib; d=json.load(open('aios/identity/identity.lock')); raw=(d['operator']+'-'+d['created']).encode(); print(hashlib.sha256(raw).hexdigest())"') DO echo   Operator token: %%t
    echo.
    echo   Preflight complete. Run: start.bat [terminal^|web^|none] [port]
    pause
    exit /b 0
)

REM ── Normal launch ──────────────────────────────────────────────────────────
SET UI=%1
IF "%UI%"=="" SET UI=terminal

SET PORT=%2
IF "%PORT%"=="" SET PORT=1313

SET TOKEN=%3

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
IF "%TOKEN%"=="" (
    python aios\main.py --ui %UI% --port %PORT%
) ELSE (
    python aios\main.py --ui %UI% --port %PORT% --operator-token %TOKEN%
)

IF ERRORLEVEL 1 (
    echo.
    echo AI-OS exited with an error. See above for details.
    pause
)
