@echo off
REM Setup script for Python project

REM Set the project directory
SET PROJECT_DIR=%~dp0

REM Create a virtual environment
echo Creating a virtual environment...
python -m venv venv

REM Activate the virtual environment
echo Activating the virtual environment...
call venv\Scripts\activate

REM Install required packages
echo Installing required packages...
pip install -r requirements.txt

REM Run the application (optional)
echo Running the application...
python main.py

REM Deactivate the virtual environment
echo Deactivating the virtual environment...
deactivate

echo Setup complete!
pause