@echo off
title SmartTraffic AI Launcher
color 0A

echo.
echo  ================================
echo   SmartTraffic AI v2.1 - Starting
echo  ================================
echo.

:: ---------------------------------------------------------------
:: CONFIGURATION — edit these two lines to match your setup
:: ---------------------------------------------------------------
set "CONDA_ENV=smarttraffic"
set "CONDA_ACTIVATE=%USERPROFILE%\anaconda3\Scripts\activate.bat"
:: If you use Miniconda, try: %USERPROFILE%\miniconda3\Scripts\activate.bat
:: ---------------------------------------------------------------

set "ROOT=%~dp0"
set "FRONTEND_DIR=%ROOT%frontend"
set "API_DIR=%ROOT%api"

:: Check conda
if not exist "%CONDA_ACTIVATE%" (
    echo [WARN] Could not find conda at: %CONDA_ACTIVATE%
    echo        Edit CONDA_ACTIVATE in start.bat to point to your activate.bat
    echo        Attempting to run with system Python instead...
    set "USE_SYSTEM_PYTHON=1"
)

:: Check Node
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Install from https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js found

:: Create data dirs if needed
if not exist "%ROOT%data"   mkdir "%ROOT%data"
if not exist "%ROOT%data\clips" mkdir "%ROOT%data\clips"
if not exist "%ROOT%models" mkdir "%ROOT%models"

:: Check model
if not exist "%ROOT%models\best.pt" (
    echo.
    echo [INFO] Custom weights models\best.pt not found.
    echo        The detector will automatically use the standard YOLOv11 fallback model.
    echo.
)

:: Install frontend deps if needed
pushd "%FRONTEND_DIR%"
if not exist "node_modules" (
    echo [SETUP] Installing frontend dependencies...
    call npm install
)
popd

:: Start API + Detector
echo [START] Launching API + Detector...
if defined USE_SYSTEM_PYTHON (
    start "SmartTraffic - API" cmd /k "cd /d "%API_DIR%" && pip install -r requirements.txt -r "%ROOT%detector\requirements.txt" -q && uvicorn main:app --host 0.0.0.0 --port 8000"
) else (
    start "SmartTraffic - API" cmd /k "call "%CONDA_ACTIVATE%" "%CONDA_ENV%" && cd /d "%API_DIR%" && uvicorn main:app --host 0.0.0.0 --port 8000"
)


timeout /t 5 /nobreak >nul

:: Start Frontend dev server
echo [START] Launching Frontend...
start "SmartTraffic - Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

timeout /t 4 /nobreak >nul

:: Open browser
start http://localhost:5173

echo.
echo  ================================
echo   Dashboard : http://localhost:5173
echo   API docs  : http://localhost:8000/docs
echo   Login     : admin / admin
echo  ================================
echo.
pause
