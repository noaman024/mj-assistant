@echo off
title Push MJ Assistant to GitHub
color 0b
echo ========================================================
echo   Pushing MJ Assistant Project to GitHub...
echo   Repository: https://github.com/noaman024/mj-assistant.git
echo ========================================================
echo.
cd /d "C:\Users\sabir\antigravity\assistant"

git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo ========================================================
    echo   Browser login nahi hua? Koi baat nahi!
    echo   Apna GitHub Token (ghp_... ya github_pat_...) yahan paste karein:
    echo ========================================================
    set /p GHTOKEN="GitHub Token daalein: "
    if defined GHTOKEN (
        git push -u https://%GHTOKEN%@github.com/noaman024/mj-assistant.git main
    )
)

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo   [SUCCESS] Code successfully pushed to GitHub!
    echo   Ab is link par ja kar apna APK download karein:
    echo   https://github.com/noaman024/mj-assistant/actions
    echo ========================================================
)

echo.
pause
