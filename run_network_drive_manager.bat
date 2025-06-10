@echo off
echo Network Drive Manager wird gestartet...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Fehler: Python ist nicht installiert oder nicht im PATH verfügbar.
    echo Bitte installieren Sie Python von https://python.org
    pause
    exit /b 1
)

REM Run the application
python network_drive_manager.py

REM Keep console open if there's an error
if %errorlevel% neq 0 (
    echo.
    echo Ein Fehler ist aufgetreten. Drücken Sie eine beliebige Taste zum Beenden...
    pause >nul
) 