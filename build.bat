@echo off
rem Build BountyRadar.exe — requires:  pip install pyinstaller
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python not found on PATH.
  pause
  exit /b 1
)
python -m PyInstaller --version >nul 2>nul
if errorlevel 1 (
  echo Installing PyInstaller...
  python -m pip install --user pyinstaller
)
python build_exe.py %*
echo.
echo Output is under dist\
pause
