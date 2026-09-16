@echo off
rem ============================================================
rem  Bounty Radar Pro - launcher. Double-click this file.
rem  Opens the modern web UI in your default browser.
rem  (ASCII only on purpose: cmd.exe on Windows uses cp1252)
rem ============================================================
cd /d "%~dp0"

if not exist "bounty_radar.py" (
  echo bounty_radar.py was not found next to this launcher.
  pause
  exit /b 1
)

if not exist "ui\index.html" (
  echo ui\index.html was not found. The web UI needs this folder.
  pause
  exit /b 1
)

where pythonw >nul 2>nul
if %errorlevel%==0 (
  start "" pythonw "bounty_radar.py"
  exit /b 0
)

where py >nul 2>nul
if %errorlevel%==0 (
  start "" py -3 "bounty_radar.py"
  exit /b 0
)

where python >nul 2>nul
if %errorlevel%==0 (
  python "bounty_radar.py"
  exit /b 0
)

echo.
echo Python 3 was not found on this machine.
echo Install it from https://www.python.org/downloads/  ^(tick "Add python.exe to PATH"^)
echo then run this file again. Nothing else needs installing.
echo.
pause
exit /b 1
