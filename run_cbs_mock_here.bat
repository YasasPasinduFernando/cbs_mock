@echo off
setlocal

set "MOCK_DIR=%~dp0"
cd /d "%MOCK_DIR%"

echo Starting T24/CBS mock server...
echo.
echo UI will open at:
echo   http://127.0.0.1:8780/__mock/ui
echo.
echo Keep this window open while testing. Press Ctrl+C to stop.
echo.

start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8780/__mock/ui'"
python "%MOCK_DIR%mock_t24_cbs.py"

echo.
echo Mock server stopped.
pause
