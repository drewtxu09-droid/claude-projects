@echo off
echo Installing dependencies...
py -m pip install -r requirements.txt
echo.
echo Starting Oncor TDU Dashboard...
echo Open your browser to http://localhost:8050
echo.
py app.py
pause
