@echo off
title SegurifAI Frontend - Port 3000
pushd "%~dp0frontend"
echo.
echo ============================================================
echo    SegurifAI x PAQ Frontend Server
echo ============================================================
echo.
echo Project directory: %CD%
echo.
echo Starting app on http://localhost:3000
echo.
npm run dev
popd
pause
