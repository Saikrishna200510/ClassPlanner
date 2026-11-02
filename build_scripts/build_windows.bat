@echo off
REM ==============================================================================
REM ClassPlanner - Windows Build & Installer Script
REM Compiles ClassPlanner.exe and builds ClassPlanner-v1.0.0-Windows-Setup.exe
REM ==============================================================================

echo ===================================================
echo Building ClassPlanner for Windows (Setup Wizard EXE)
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
pip install pyinstaller Pillow

REM Clean previous builds
echo Cleaning previous builds...
if exist build rd /s /q build
if exist dist rd /s /q dist

REM Compile executable
echo Running PyInstaller...
pyinstaller --clean build_scripts\ClassPlanner.spec

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller compilation failed.
    pause
    exit /b 1
)

echo Standalone executable created at: dist\ClassPlanner.exe

REM Look for Inno Setup Compiler (ISCC)
set ISCC_PATH="ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set ISCC_PATH="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set ISCC_PATH="%ProgramFiles%\Inno Setup 6\ISCC.exe"

echo Checking for Inno Setup Compiler...
%ISCC_PATH% /? >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Building Windows Setup Installer Wizard...
    %ISCC_PATH% build_scripts\windows_installer.iss
    if %ERRORLEVEL% EQU 0 (
        echo ===================================================
        echo Installer Successfully Built!
        echo Installer path: dist\ClassPlanner-v1.0.0-Windows-Setup.exe
        echo ===================================================
    ) else (
        echo [WARNING] Inno Setup compilation failed. Standalone EXE remains available in dist\
    )
) else (
    echo [INFO] Inno Setup is not installed or not in PATH.
    echo Standalone ClassPlanner.exe is available in dist\
    echo Install Inno Setup 6 to compile the Windows Setup Wizard.
)

pause
