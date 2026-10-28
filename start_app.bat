@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m agarwood_minims gui
) else (
  echo Install first: python -m pip install .
  python -m agarwood_minims gui
)
if errorlevel 1 pause
