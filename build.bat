@echo off
echo ============================================================
echo Run8 Control Conductor - Build Executable
echo ============================================================
echo.

echo Checking PyInstaller...
python -c "import PyInstaller; print('PyInstaller version:', PyInstaller.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo PyInstaller not found, installing...
    pip install pyinstaller
)

echo.
echo Building executable with PyInstaller...
pyinstaller --clean Run8ControlConductor.spec

echo.
if exist "dist\Run8ControlConductor.exe" (
    echo ✓ Build successful! Executable created at: dist\Run8ControlConductor.exe
) else (
    echo ✗ Build failed! Executable not found.
)

echo.
echo Tip: Use build_executable.py for a complete release build with documentation.
pause
