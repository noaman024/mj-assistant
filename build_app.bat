@echo off
title Building MJ Assistant Standalone Application
color 0b

echo ============================================================
echo       MJ ASSISTANT - STANDALONE WINDOWS PACKAGER
echo ============================================================
echo.

echo [1/3] Checking Python and PyInstaller...
python --version
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    python -m pip install pyinstaller
)

echo.
echo [2/3] Building MJ_Assistant.exe with PyInstaller...
python -m PyInstaller --noconfirm --clean ^
    --name "MJ_Assistant" ^
    --noconsole ^
    --add-data "backend\bridge\web;backend\bridge\web" ^
    --add-data "data;data" ^
    --hidden-import "customtkinter" ^
    --hidden-import "psutil" ^
    --hidden-import "pyautogui" ^
    --hidden-import "uvicorn" ^
    --hidden-import "fastapi" ^
    --hidden-import "google.genai" ^
    --hidden-import "edge_tts" ^
    --hidden-import "pyttsx3" ^
    MJ_Assistant.pyw

echo.
echo [3/3] Build Complete!
echo Standalone executable created at: dist\MJ_Assistant\MJ_Assistant.exe
echo.
pause
