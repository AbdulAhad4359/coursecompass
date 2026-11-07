@echo off
cd /d "%~dp0frontend"
call npm ci
if errorlevel 1 goto error
call npm run dev
pause
exit /b
:error
echo Setup failed. Check Node.js is installed and your internet connection works.
pause
exit /b 1
