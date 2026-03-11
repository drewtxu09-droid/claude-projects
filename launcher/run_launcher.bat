@echo off
cd /d "%~dp0"
pip install flask -q
start http://localhost:5050
python launcher.py
pause
