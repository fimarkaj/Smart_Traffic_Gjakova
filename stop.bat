@echo off
title SmartTraffic AI - Stop
color 0C

echo.
echo  Stopping SmartTraffic AI...
echo.

:: Kill uvicorn (API)
taskkill /FI "WINDOWTITLE eq SmartTraffic - API*" /T /F >nul 2>&1

:: Kill detector
taskkill /FI "WINDOWTITLE eq SmartTraffic - Detector*" /T /F >nul 2>&1

:: Kill frontend (vite)
taskkill /FI "WINDOWTITLE eq SmartTraffic - Frontend*" /T /F >nul 2>&1

echo  [OK] All services stopped.
echo.
pause
