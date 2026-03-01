@echo off
echo ================================
echo   Starting Backend (Flask)
echo ================================
cd /d %~dp0backend
call venv\Scripts\activate
python run.py
