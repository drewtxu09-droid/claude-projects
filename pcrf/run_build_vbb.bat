@echo off
cd /d "%~dp0"
set PYTHON=C:\Users\XV1S\AppData\Local\Programs\Python\Python312\python.exe
%PYTHON% -m pip install hdbcli pyyaml -q
%PYTHON% build_vbb_products.py
pause
