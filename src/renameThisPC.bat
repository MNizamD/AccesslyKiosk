@echo off
setlocal

:: Ask for a number
set /p pcnum="Enter PC number (e.g., 2): "

:: Check if input is numeric
for /f "delims=0123456789" %%a in ("%pcnum%") do (
    echo Invalid input. Must be a number.
    echo Aborting.
    pause
    exit /b
)

:: Pad with leading zero if < 10
if %pcnum% LSS 10 (
    set pcnum=0%pcnum%
)

:: Build new PC name
set newname=LAB-%pcnum%

:: Preview the new name
echo New PC name will be: %newname%

:: Get confirmation
set /p confirm="To confirm, type 'yes' (case-sensitive): "

if "%confirm%"=="yes" (
    echo Renaming PC to %newname% using PowerShell...
    
    powershell -Command "Try { Rename-Computer -NewName '%newname%' -Force -ErrorAction Stop } Catch { Write-Host 'ERROR: Failed to rename PC. Run as Administrator.'; exit 1 }"

    if errorlevel 1 (
        echo Aborting due to error.
        pause
        exit /b
    )

    echo PC will now restart...
    shutdown /r /t 5

    if errorlevel 1 (
        echo ERROR: Failed to initiate restart.
        pause
        exit /b
    )

) else (
    echo Confirmation failed. Aborting.
)

endlocal
pause
