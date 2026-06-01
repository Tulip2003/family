@echo off
setlocal
cd /d "%~dp0"
echo ================================
echo Roomies Enterprise - Windows Start
echo ================================
echo.
if not exist app.py (
  echo ERROR: app.py not found. Please run this file from the project folder.
  pause
  exit /b 1
)
if not exist requirements.txt (
  echo ERROR: requirements.txt not found. Please run this file from the project folder.
  pause
  exit /b 1
)
if exist .venv (
  echo Using existing virtual environment.
) else (
  echo Creating virtual environment...
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
if not exist .env (
  python scripts\create_env.py
)
python scripts\doctor.py
python -m flask --app app reset-db
python app.py
pause
