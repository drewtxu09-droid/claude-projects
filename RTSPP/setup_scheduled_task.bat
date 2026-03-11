@echo off
echo ================================================
echo  RTSPP Extract - Scheduled Task Setup
echo ================================================
echo.
echo This will create a Windows Scheduled Task that runs the RTSPP
echo extract automatically on the 2nd of every month at 8:00 AM.
echo.
echo If the computer is off or asleep on the 2nd, the task will run
echo automatically the next time the computer is online.
echo.
pause

:: Run the PowerShell setup script
powershell -ExecutionPolicy Bypass -File "%~dp0setup_scheduled_task.ps1"

echo.
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS - Scheduled task created.
    echo You can view it in Task Scheduler under: Task Scheduler Library
    echo Task name: RTSPP Monthly Extract
) else (
    echo FAILED - See error above. Try running this as Administrator.
)
pause
