@echo off
setlocal
if not exist "%~dp0.runtime\venv\Scripts\python.exe" (
  echo Run setup.ps1 before using concat-desk. 1>&2
  exit /b 1
)
"%~dp0.runtime\venv\Scripts\python.exe" "%~dp0concat-desk.py" %*
