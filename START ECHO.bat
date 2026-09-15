@echo off
cd /d "%~dp0"
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8765'"
python server.py
echo.
echo Server stopped. Review any error above before closing this window.
pause
