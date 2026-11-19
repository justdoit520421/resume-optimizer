@echo off
chcp 65001 >nul
title Resume Optimizer - One Click Start
cd /d "%~dp0"
set "ROOT=%~dp0"

echo ==================================================
echo    Resume Optimizer  -  One Click Start
echo ==================================================
echo.
echo [1/3] MySQL    --^> port 3307
start "1-MySQL" cmd /k call "%ROOT%1-MySQL.bat"
echo       waiting 8 seconds for MySQL ...
timeout /t 8 /nobreak >nul
echo.

echo [2/3] Backend  --^> http://127.0.0.1:8000
start "2-Backend" cmd /k call "%ROOT%2-Backend.bat"
echo       waiting 6 seconds for Backend ...
timeout /t 6 /nobreak >nul
echo.

echo [3/3] Frontend --^> http://localhost:5173
start "3-Frontend" cmd /k call "%ROOT%3-Frontend.bat"
echo       waiting 10 seconds for Frontend ...
timeout /t 10 /nobreak >nul
echo.

echo Opening browser ...
start "" http://localhost:5173
echo.
echo --------------------------------------------------
echo  3 windows opened:
echo    1-MySQL      - keep it running (database)
echo    2-Backend    - keep it running (API)
echo    3-Frontend   - keep it running (web page)
echo  Close those windows to stop all services.
echo --------------------------------------------------
pause
