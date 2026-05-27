@echo off
title SECONDS — EJ&ELLA Store
color 1F

echo.
echo  ========================================
echo   SECONDS — EJ^&ELLA Store
echo   Starting system...
echo  ========================================
echo.

:: Navigate to the script's directory
cd /d "%~dp0"

:: Activate virtual environment
call venv\Scripts\activate

:: Check if venv activated
if errorlevel 1 (
    echo  [ERROR] Could not activate virtual environment.
    echo  Make sure you have run: python -m venv venv
    pause
    exit /b 1
)

echo  [OK] Virtual environment activated.

:: Install/check requirements silently
echo  [..] Checking requirements...
pip install -r requirements.txt -q --disable-pip-version-check
echo  [OK] Requirements ready.

:: Run migrations
echo  [..] Applying database migrations...
python manage.py migrate --run-syncdb -v 0
echo  [OK] Database ready.

:: Open browser after short delay (runs in background)
echo  [..] Opening browser...
start "" timeout /t 2 /nobreak >nul && start "" "http://127.0.0.1:8000"

echo.
echo  ========================================
echo   SECONDS is running!
echo   Open: http://127.0.0.1:8000
echo   Press CTRL+C to stop the server.
echo  ========================================
echo.

:: Start server
python manage.py runserver

pause
