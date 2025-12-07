@echo off
echo Starting BR18 Document Automation GUI Demo...
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Activate Anaconda environment
echo Activating Anaconda environment: 3P
call E:\Anaconda\Scripts\activate.bat E:\Anaconda
call conda activate 3P

if errorlevel 1 (
    echo.
    echo Error: Failed to activate Anaconda environment.
    echo Please ensure the environment exists at: E:\Anaconda_envs\3P
    echo.
    pause
    exit /b 1
)

echo Running GUI...
python demo_gui.py

if errorlevel 1 (
    echo.
    echo Error: Failed to start the GUI.
    echo Please ensure you have installed the required dependencies:
    echo   pip install customtkinter
    echo.
    pause
)
