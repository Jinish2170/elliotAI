@echo off
title Veritas — Shutdown
echo.
echo  Stopping Veritas services...
echo.

:: Kill backend (port 8000)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING" 2^>NUL') do (
    echo  Killing backend PID %%a
    taskkill /PID %%a /F >NUL 2>&1
)

:: Kill any child python processes from backend
for /f "tokens=2" %%a in ('tasklist /FI "WINDOWTITLE eq Veritas Backend" /FO TABLE /NH 2^>NUL ^| findstr /I "python uvicorn"') do (
    taskkill /PID %%a /F >NUL 2>&1
)

:: Kill frontend (port 3000)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING" 2^>NUL') do (
    echo  Killing frontend PID %%a
    taskkill /PID %%a /F >NUL 2>&1
)

echo.
echo  All Veritas services stopped.
timeout /t 3 /nobreak >NUL
