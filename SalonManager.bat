@echo off
setlocal
cd /d "%~dp0"
title Rayla Salon - System Manager

echo Starting Salon System...
echo.

:: 1. Force kill anything on port 5000 just in case
powershell -Command "Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }" 2>nul

:: 2. Start the engine directly in this window first to see errors
echo [STEP 1] Starting the Salon Engine...
echo (If you see an error here, please tell me what it says)
echo.

:: We'll try to run it. If it works, we open the browser.
:: If it fails, the 'pause' will catch it.
start "" "http://localhost:5000/admin"
python backend/app.py

echo.
echo Engine stopped.
pause
