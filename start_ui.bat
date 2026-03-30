@echo off
setlocal
cd /d "%~dp0"

echo Starting programma_rb Desktop UI...

REM Prefer pythonw (no console window). Fallback to python.
set PYW=%LocalAppData%\Microsoft\WindowsApps\pythonw3.13.exe
set PY=%LocalAppData%\Microsoft\WindowsApps\python3.13.exe

if exist "%PYW%" (
  "%PYW%" "%~dp0main.py"
  exit /b 0
)

if exist "%PY%" (
  "%PY%" "%~dp0main.py"
  exit /b 0
)

where pythonw >nul 2>nul
if not errorlevel 1 (
  pythonw "%~dp0main.py"
  exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
  python "%~dp0main.py"
  exit /b 0
)

echo ERROR: Python not found. Install Python and try again.
pause
exit /b 1
