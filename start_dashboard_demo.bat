@echo off
cd /d "%~dp0"
echo ========================================================
echo STARTING DPI DASHBOARD: DEMO MODE (PCAP REPLAY)
echo ========================================================

echo [1/3] Starting Backend API...
start cmd /k "cd dashboard-server && node server.js"

echo [2/3] Starting Frontend React UI...
start cmd /k "cd dashboard && npm run dev"

echo [3/3] Starting Python ML Engine (Demo Mode)...
start cmd /k "python live_dpi_engine.py --mode demo"

echo All systems are starting. The dashboard will open in your browser shortly!
