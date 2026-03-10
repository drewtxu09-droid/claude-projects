@echo off
echo Registering ComparePower 4CHE scheduled tasks...

schtasks /create /tn "ComparePower 4CHE 8am"  /tr "\"C:\Users\XV1S\Desktop\Claude\Price Comparison\run_4CHE_alert.bat\"" /sc daily /st 08:00 /f
schtasks /create /tn "ComparePower 4CHE 12pm" /tr "\"C:\Users\XV1S\Desktop\Claude\Price Comparison\run_4CHE_alert.bat\"" /sc daily /st 12:00 /f
schtasks /create /tn "ComparePower 4CHE 5pm"  /tr "\"C:\Users\XV1S\Desktop\Claude\Price Comparison\run_4CHE_alert.bat\"" /sc daily /st 17:00 /f

echo.
echo Done! Tasks registered:
echo   - ComparePower 4CHE 8am   (8:00 AM daily)
echo   - ComparePower 4CHE 12pm  (12:00 PM daily)
echo   - ComparePower 4CHE 5pm   (5:00 PM daily)
echo.
pause
