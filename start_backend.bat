@echo off
cd /d "%~dp0backend"
if not exist .venv\Scripts\python.exe (
  py -3.11 -m venv .venv
  if errorlevel 1 goto error
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
exit /b
:error
echo Setup failed. Use Python 3.11 or follow README.md for Python 3.12.
pause
exit /b 1
