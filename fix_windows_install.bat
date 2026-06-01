@echo off
setlocal

echo Cleaning old virtual environment...
if exist .venv rmdir /s /q .venv

echo Creating virtual environment...
python -m venv .venv
if errorlevel 1 goto fail

call .venv\Scripts\activate

echo Upgrading pip tools...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto fail

echo Installing requirements...
python -m pip install -r requirements.txt
if errorlevel 1 goto fail

echo Creating .env if needed...
python scripts\create_env.py

echo Resetting database...
python -m flask --app app reset-db
if errorlevel 1 goto fail

echo Starting Roomies...
python app.py
goto end

:fail
echo.
echo Setup failed. Copy the error text and ask ChatGPT to fix it.
exit /b 1

:end
endlocal
