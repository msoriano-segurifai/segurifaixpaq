@echo off
setlocal
title SegurifAI x PAQ - Dev Environment

REM Change to the script's directory (handles spaces in path)
pushd "%~dp0"

echo ============================================================
echo   Starting SegurifAI x PAQ Development Servers
echo ============================================================
echo   Project Root: %CD%
echo ============================================================
echo.

REM Backend (Django) - new window using short path format to avoid space issues
echo [1/2] Starting backend on http://localhost:8000 ...
start "SegurifAI Backend" /D "%CD%" cmd /k "call venv\Scripts\activate.bat && python manage.py runserver 0.0.0.0:8000"

REM Frontend (React - Vite) - new window
echo [2/2] Starting frontend on http://localhost:3000 ...
start "SegurifAI Frontend" /D "%CD%\frontend" cmd /k "npm run dev"

echo.
echo Done. Two windows should open: one for backend, one for frontend.
echo Leave them open while developing. Close this window if you wish.

popd
endlocal
exit /b 0
