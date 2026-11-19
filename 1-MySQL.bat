@echo off
chcp 65001 >nul
title MySQL (port 3307)

cd /d "%~dp0"
set "MYSQL_DATA=%~dp0backend\mysql_data"
set "MYSQL_PORT=3307"
set "MYSQL_BIN=D:\MySQL\mysql-9.7.0-winx64\bin\mysqld.exe"

rem Not found at the default path? Look it up in PATH.
if not exist "%MYSQL_BIN%" for /f "delims=" %%i in ('where mysqld.exe 2^>nul') do set "MYSQL_BIN=%%i"

if not exist "%MYSQL_BIN%" (
    echo [ERROR] mysqld.exe not found.
    echo         Install MySQL, or edit MYSQL_BIN in this file.
    pause
    exit /b 1
)

for %%i in ("%MYSQL_BIN%") do set "MYSQL_CLIENT=%%~dpimysql.exe"

if not exist "%MYSQL_DATA%\mysql" (
    echo [FIRST RUN] Initializing data directory ...
    "%MYSQL_BIN%" --initialize-insecure --datadir="%MYSQL_DATA%"
    if errorlevel 1 (
        echo [ERROR] Initialization failed.
        pause
        exit /b 1
    )
    echo [FIRST RUN] Starting a temporary server to create the database ...
    start "MySQL-Init" /min "%MYSQL_BIN%" --datadir="%MYSQL_DATA%" --port=%MYSQL_PORT%
    timeout /t 12 /nobreak >nul
    "%MYSQL_CLIENT%" --user=root --host=127.0.0.1 --port=%MYSQL_PORT% --execute="ALTER USER 'root'@'localhost' IDENTIFIED BY '123456'; CREATE DATABASE IF NOT EXISTS resume_optimizer DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    "%MYSQL_CLIENT%" --user=root --password=123456 --host=127.0.0.1 --port=%MYSQL_PORT% --execute="SHUTDOWN;"
    timeout /t 5 /nobreak >nul
    echo [FIRST RUN] Done. root password = 123456, database = resume_optimizer
    echo.
)

echo Data dir : %MYSQL_DATA%
echo Port     : %MYSQL_PORT%  (3307 is used to avoid clashing with an installed MySQL on 3306)
echo Starting MySQL, wait for "ready for connections" ...
echo.
"%MYSQL_BIN%" --datadir="%MYSQL_DATA%" --port=%MYSQL_PORT% --console
pause
