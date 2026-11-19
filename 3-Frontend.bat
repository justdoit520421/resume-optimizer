@echo off
chcp 65001 >nul
title Frontend (port 5173)
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [FIRST RUN] Installing frontend dependencies, please wait ...
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed. Try a mirror:
        echo         npm config set registry https://registry.npmmirror.com
        pause
        exit /b 1
    )
)

echo Frontend running at http://localhost:5173
echo.
call npm run dev
pause
