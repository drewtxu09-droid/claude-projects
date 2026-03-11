@echo off
cd /d "%~dp0"
set PYTHON="C:\Program Files\Python312\python.exe"
set PIP="C:\Program Files\Python312\Scripts\pip.exe"
%PYTHON% -m pip install flask -q
start http://localhost:5050
%PYTHON% launcher.py
pause
