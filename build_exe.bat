@echo off
REM Build a single-file Windows executable using PyInstaller
REM Usage: run inside an activated virtualenv where pyinstaller is installed

pip install pyinstaller --upgrade
pyinstaller --noconfirm --clean IA_Sentiment.spec

echo Build complete. See the dist\IA_Sentiment.exe file.
pause
