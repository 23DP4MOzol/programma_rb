@echo off
setlocal
cd /d "%~dp0"

echo Starting programma_rb Desktop UI...
set LOG=%~dp0start_ui.log
echo [%date% %time%] start_ui.bat launching... > "%LOG%"

REM Prefer pythonw (no console window). Fallback to python.
set PYW=%LocalAppData%\Microsoft\WindowsApps\pythonw3.13.exe
set PY=%LocalAppData%\Microsoft\WindowsApps\python3.13.exe

if exist "%PYW%" (
  start "programma_rb" /b "%PYW%" "%~dp0main.py" 1>>"%LOG%" 2>>&1
  exit /b 0
)

if exist "%PY%" (
  start "programma_rb" /b "%PY%" "%~dp0main.py" 1>>"%LOG%" 2>>&1
  exit /b 0
)

where pythonw >nul 2>nul
if not errorlevel 1 (
  start "programma_rb" /b pythonw "%~dp0main.py" 1>>"%LOG%" 2>>&1
  exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
  start "programma_rb" /b python "%~dp0main.py" 1>>"%LOG%" 2>>&1
  exit /b 0
)

echo ERROR: Python not found. Install Python and try again.
echo ERROR: Python not found >> "%LOG%"
echo Try running: python .\main.py
pause
exit /b 1
