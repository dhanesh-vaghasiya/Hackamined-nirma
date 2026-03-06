@echo off
echo ================================
echo   Starting Backend (Flask)
echo ================================
echo To run JSON file processor instead, use:
echo   backend\hack-env\Scripts\python.exe backend\process_user_file.py
cd /d %~dp0backend
if exist hack-env\Scripts\python.exe (
	hack-env\Scripts\python.exe run.py
) else (
	echo ERROR: Python virtual environment not found at backend\hack-env
	echo Create it or update this script path.
	exit /b 1
)
