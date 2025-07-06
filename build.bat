@echo off
echo ============================================================
echo Run8 Control Conductor - Build Executable
echo ============================================================
echo.

echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building executable...
python build_executable.py

echo.
echo Build complete! Check the 'release' folder for the executable.
pause
