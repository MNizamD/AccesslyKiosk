@echo off
REM ========================================================
REM  Generate Task Scheduler XML + Import + Deploy
REM  XML is stored in the same folder as this script
REM ========================================================

:: --- Elevate once at start ---
:: (Re-launch itself as Admin if not already elevated)
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Requesting admin privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: CONFIG
set TASKNAME=LockDownKiosk
set USERONLY=GVC
@REM set APPDIR=C:\Users\%USERONLY%\AppData\Roaming\NizamLab
set APPDIR=E:\Miscellaneous\NizamLab
set APPNAME=LockDown.exe

:: Paths
set CURDIR=%~dp0
set DESTDIR=%APPDIR%
set XMLFILE=%CURDIR%LockDownKiosk.xml
set APPEXEPATH=%APPDIR%\src\%APPNAME%

:: Envi
set WEXPECT_SPAWN_CLASS=SpawnPipe

:: Build ISO8601 Date for <Date>
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ss"') do set DATEISO=%%I

echo Generating Task Scheduler XML at "%XMLFILE%"...

> "%XMLFILE%" echo ^<?xml version="1.0" encoding="UTF-16"?^>
>> "%XMLFILE%" echo ^<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"^>
>> "%XMLFILE%" echo   ^<RegistrationInfo^>
>> "%XMLFILE%" echo     ^<Date^>%DATEISO%^</Date^>
>> "%XMLFILE%" echo     ^<Author^>%USERNAME%^</Author^>
>> "%XMLFILE%" echo     ^<Description^>LockDown kiosk launcher task^</Description^>
>> "%XMLFILE%" echo   ^</RegistrationInfo^>
>> "%XMLFILE%" echo   ^<Triggers^>
>> "%XMLFILE%" echo     ^<LogonTrigger^>
>> "%XMLFILE%" echo       ^<Enabled^>true^</Enabled^>
>> "%XMLFILE%" echo       ^<Delay^>PT0S^</Delay^>
>> "%XMLFILE%" echo       ^<UserId^>%USERONLY%^</UserId^>
>> "%XMLFILE%" echo     ^</LogonTrigger^>
>> "%XMLFILE%" echo   ^</Triggers^>
>> "%XMLFILE%" echo   ^<Principals^>
>> "%XMLFILE%" echo     ^<Principal id="Author"^>
>> "%XMLFILE%" echo       ^<UserId^>%USERONLY%^</UserId^>
>> "%XMLFILE%" echo       ^<RunLevel^>HighestAvailable^</RunLevel^>
>> "%XMLFILE%" echo     ^</Principal^>
>> "%XMLFILE%" echo   ^</Principals^>
>> "%XMLFILE%" echo   ^<Settings^>
>> "%XMLFILE%" echo     ^<MultipleInstancesPolicy^>IgnoreNew^</MultipleInstancesPolicy^>
>> "%XMLFILE%" echo     ^<DisallowStartIfOnBatteries^>false^</DisallowStartIfOnBatteries^>
>> "%XMLFILE%" echo     ^<StopIfGoingOnBatteries^>false^</StopIfGoingOnBatteries^>
>> "%XMLFILE%" echo     ^<AllowHardTerminate^>true^</AllowHardTerminate^>
>> "%XMLFILE%" echo     ^<StartWhenAvailable^>true^</StartWhenAvailable^>
>> "%XMLFILE%" echo     ^<RunOnlyIfNetworkAvailable^>false^</RunOnlyIfNetworkAvailable^>
>> "%XMLFILE%" echo   ^</Settings^>
>> "%XMLFILE%" echo   ^<Actions Context="Author"^>
>> "%XMLFILE%" echo     ^<Exec^>
>> "%XMLFILE%" echo       ^<Command^>"%APPEXEPATH%"^</Command^>
>> "%XMLFILE%" echo     ^</Exec^>
>> "%XMLFILE%" echo   ^</Actions^>
>> "%XMLFILE%" echo ^</Task^>

echo Importing task...
schtasks /create /tn "%TASKNAME%" /xml "%XMLFILE%" /f
if %ERRORLEVEL%==0 (
    echo Task imported successfully.

    echo Cleaning old folder...
    if exist "%DESTDIR%" rmdir /S /Q "%DESTDIR%"

    echo Copying files to "%DESTDIR%"...
    mkdir "%DESTDIR%"
    xcopy "%CURDIR%*" "%DESTDIR%\" /E /H /C /I /Y >nul
    if %ERRORLEVEL%==0 (
        echo Files copied successfully.
    ) else (
        echo File copy failed!
    )
) else (
    echo Failed to import task!
)

pause
