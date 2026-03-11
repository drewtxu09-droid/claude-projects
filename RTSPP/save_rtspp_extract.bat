@echo off
echo ================================================
echo  RTSPP Extract - Save to Network Share
echo ================================================
echo.
echo Make sure Excel is open with RTSPP_Extract_Tool_DW.xlsm
echo and that ReadMe!E2 (filename) and ReadMe!B3 (year) are set.
echo.
pause

python "%~dp0rtspp_extract.py" save

echo.
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS - File saved.
) else (
    echo FAILED - See error above.
)
pause
