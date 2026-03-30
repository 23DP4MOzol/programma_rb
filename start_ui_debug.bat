@echo off
setlocal
cd /d "%~dp0"

echo [DEBUG] Starting programma_rb Desktop UI...
echo (If it closes, copy the error text)

set PY=%LocalAppData%\Microsoft\WindowsApps\python3.13.exe
if exist "%PY%" (
  "%PY%" "%~dp0main.py" ui
  echo.
  echo Exit code: %ERRORLEVEL%
  pause
  exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if not errorlevel 1 (
  python "%~dp0main.py" ui
  echo.
  echo Exit code: %ERRORLEVEL%
  pause
  exit /b %ERRORLEVEL%
)

echo ERROR: Python not found.
pause
exit /b 1
