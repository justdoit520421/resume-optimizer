@echo off
chcp 65001 >nul
title Backend (port 8000)
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
    echo [FIRST RUN] Creating Python virtual environment ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Make sure Python 3.11+ is installed and in PATH.
        pause
        exit /b 1
    )
    echo [FIRST RUN] Installing backend dependencies, please wait ...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] pip install failed. Try a mirror:
        echo         .venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
        pause
        exit /b 1
    )
)

echo Backend running at http://127.0.0.1:8000
echo API docs at      http://127.0.0.1:8000/docs
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000
pause
