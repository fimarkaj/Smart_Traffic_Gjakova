@echo off
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *frontend_server.py*" >nul 2>&1
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'uvicorn main:app|frontend_server.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
