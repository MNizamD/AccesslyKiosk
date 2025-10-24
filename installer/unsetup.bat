@echo off
REM ========================================================
REM  Uninstall Kiosk Launcher Setup
REM  - Removes Scheduled Task
REM  - Deletes NizamLab folder from Program Files
REM ========================================================


:: --- Elevate once at start ---
:: (Re-launch itself as Admin if not already elevated)
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Requesting admin privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: CHANGE THESE if needed
set TASKNAME=LockDownKiosk
set USERONLY=GVC
set DESTDIR=E:\Miscellaneous\NizamLab

echo Removing Scheduled Task "%TASKNAME%"...
schtasks /delete /tn "%TASKNAME%" /f

if %ERRORLEVEL%==0 (
    echo Task removed successfully.
) else (
    echo Failed to remove task. Task may not exist.
)

echo.
echo Deleting "%DESTDIR%" folder...
if exist "%DESTDIR%" (
    rmdir /s /q "%DESTDIR%"
    if exist "%DESTDIR%" (
        echo Failed to delete "%DESTDIR%". Check permissions.
    ) else (
        echo Folder deleted successfully.
    )
) else (
    echo Folder not found, nothing to delete.
)

echo.
echo Kiosk setup has been undone.
pause
