@echo off
echo ================================================
echo  RTSPP Extract v2 - Automated Monthly Pull
echo ================================================
echo.

python "%~dp0rtspp_extract_v2.py"

echo.
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS - Review the Extract sheet in Excel, then run save_rtspp_extract.bat
) else (
    echo FAILED - Check the error above. A Teams alert has been sent.
)
pause
