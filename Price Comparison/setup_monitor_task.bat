@echo off
echo Registering ComparePower 4CHE Monitor task (every 30 minutes)...

schtasks /create /tn "ComparePower 4CHE Monitor" ^
  /tr "\"C:\Users\XV1S\Desktop\Claude\Price Comparison\run_4CHE_monitor.bat\"" ^
  /sc minute /mo 30 /f

echo.
echo Done! Task registered:
echo   - ComparePower 4CHE Monitor (runs every 30 minutes)
echo.
echo To verify: open Task Scheduler and look for "ComparePower 4CHE Monitor"
echo Log file:  Price Comparison\4CHE\monitor_log.txt
echo.
pause
