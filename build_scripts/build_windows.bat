@echo off
REM ==============================================================================
REM ClassPlanner - Windows Standalone Executable Build Script
REM Builds ClassPlanner.exe in the dist\ folder.
REM ==============================================================================

echo ===================================================
echo Building ClassPlanner for Windows (Desktop EXE)
echo ===================================================

cd /d "%~dp0\.."

REM Verify python is available
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not found in PATH. Please install Python 3.10+ and add to PATH.
    pause
    exit /b 1
)

REM Ensure dependencies are installed
echo Installing / checking requirements...
pip install -r requirements.txt
pip install pyinstaller

REM Clean previous builds
echo Cleaning previous builds...
if exist build rd /s /q build
if exist dist rd /s /q dist

REM Compile executable
echo Running PyInstaller...
pyinstaller --clean build_scripts\ClassPlanner.spec

if %ERRORLEVEL% EQU 0 (
    echo ===================================================
    echo Build Successful!
    echo Standalone executable created at: dist\ClassPlanner.exe
    echo ===================================================
) else (
    echo [ERROR] PyInstaller compilation failed.
)

pause

