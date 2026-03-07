@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting Oncor TDU Dashboard...
echo Open your browser to http://localhost:8050
echo.
python app.py
pause
