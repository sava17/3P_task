@echo off
echo Starting BR18 Document Automation CLI Demo...
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Activate Anaconda environment
echo Activating Anaconda environment: 3P
call E:\Anaconda_envs\3P\Scripts\activate.bat

if errorlevel 1 (
    echo.
    echo Error: Failed to activate Anaconda environment.
    echo Please ensure the environment exists at: E:\Anaconda_envs\3P
    echo.
    pause
    exit /b 1
)

echo Running CLI demo...
python demo.py

pause
