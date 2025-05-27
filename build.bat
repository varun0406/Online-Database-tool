@echo off
REM Build script for Online Database Checking Tool

REM Install PyInstaller if not already installed
pip show pyinstaller >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
    pip install selenium
)

REM Remove previous build/dist folders if they exist
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist master_script.spec del master_script.spec

REM Build the executable
pyinstaller --onefile --add-data "Codes;Codes" master_script.py

echo.
echo Build complete! Your EXE is in the dist folder.
pause 