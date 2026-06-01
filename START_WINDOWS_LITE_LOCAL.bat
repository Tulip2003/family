@echo off
setlocal
cd /d "%~dp0"
echo Roomies local start without cloud drivers...
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-lite.txt
if not exist .env python scripts\create_env.py
python -m flask --app app reset-db
python app.py
pause
