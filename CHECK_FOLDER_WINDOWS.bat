@echo off
cd /d "%~dp0"
echo Current folder: %cd%
echo.
dir app.py requirements.txt scripts templates static css js
pause
