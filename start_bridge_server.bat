@echo off
title MJ Assistant Bridge Server
color 0b
echo ===================================================
echo     MJ ASSISTANT - CROSS-DEVICE BRIDGE SERVER
echo ===================================================
echo Starting FastAPI server on port 8000 for Mobile Cockpit...
cd /d "%~dp0"
python -m uvicorn backend.bridge.server:app --host 0.0.0.0 --port 8000
pause
