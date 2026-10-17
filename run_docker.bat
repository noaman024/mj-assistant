@echo off
title MJ Assistant Docker Launcher
color 0a

echo ============================================================
echo         MJ ASSISTANT - DOCKER CONTAINER LAUNCHER
echo ============================================================
echo.

docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH!
    echo Please install Docker Desktop for Windows from https://www.docker.com
    pause
    exit /b 1
)

echo [1/2] Building and starting MJ Assistant Container...
docker-compose up -d --build

echo.
echo [2/2] Container Status:
docker-compose ps

echo.
echo ============================================================
echo MJ Server running at: http://localhost:8000
echo Desktop Cockpit HUD:  http://localhost:8000/desktop
echo Mobile Phone PWA:     http://localhost:8000/
echo ============================================================
echo.
pause
