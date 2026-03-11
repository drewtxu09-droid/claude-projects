@echo off
cd /d "%~dp0"
set PYTHON=C:\Users\XV1S\AppData\Local\Programs\Python\Python312\python.exe
%PYTHON% -m pip install flask -q
start http://localhost:5151
%PYTHON% launcher.py
pause
