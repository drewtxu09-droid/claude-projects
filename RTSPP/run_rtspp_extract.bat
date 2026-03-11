@echo off
echo ================================================
echo  RTSPP Extract - SAP Pull
echo ================================================
echo.
echo Make sure Excel is open with RTSPP_Extract_Tool_DW.xlsm
echo and that SAP GUI scripting is enabled.
echo.
pause

python "%~dp0rtspp_extract.py"

echo.
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS - Extract complete.
) else (
    echo FAILED - See error above.
)
pause
