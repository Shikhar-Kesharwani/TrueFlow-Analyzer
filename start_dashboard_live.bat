@echo off
cd /d "%~dp0"
echo ========================================================
echo STARTING DPI DASHBOARD: LIVE WI-FI MODE
echo ========================================================
echo WARNING: This script MUST be run as Administrator!
echo WARNING: You MUST have Npcap installed for this to work.

echo [1/3] Starting Backend API...
start cmd /k "cd dashboard-server && node server.js"

echo [2/3] Starting Frontend React UI...
start cmd /k "cd dashboard && npm run dev"

echo [3/3] Starting Python ML Engine (Live Mode)...
start cmd /k "python live_dpi_engine.py --mode live"

echo All systems are starting. The dashboard will open in your browser shortly!
