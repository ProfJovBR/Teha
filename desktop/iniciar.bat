@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\pythonw.exe (
  echo Execute primeiro: py -3 -m venv .venv
  echo Depois: .venv\Scripts\python.exe -m pip install -r requirements.txt
  pause
  exit /b 1
)
start "Teha" ".venv\Scripts\pythonw.exe" main.py
