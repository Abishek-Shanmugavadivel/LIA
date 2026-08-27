@echo off
title LIA 5.0 JARVIS Desktop Launcher
echo ===================================================
echo   LIA 5.0 — GRANDMASTER JARVIS DESKTOP LAUNCHER
echo ===================================================
echo.
cd /d "%~dp0"
python start_lia.py
if errorlevel 1 (
    echo [ERROR] Failed to start LIA 5.0. Check log files.
    pause
) else (
    echo [SUCCESS] LIA 5.0 process initialized successfully.
)
