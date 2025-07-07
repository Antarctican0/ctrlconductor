"""
Build script for creating a standalone executable of Run8 Control Conductor

This script uses PyInstaller to create a single executable file that includes
all necessary dependencies and can be run without Python installed.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main build process"""
    print("=" * 60)
    print("Run8 Control Conductor - Executable Build Script")
    print("=" * 60)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✓ PyInstaller is available")
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        if not run_command("pip install pyinstaller", "Installing PyInstaller"):
            return False
    
    # Create build directory
    build_dir = Path("build")
    dist_dir = Path("dist")
    
    # Clean previous builds and cache
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("✓ Cleaned previous build directory")
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("✓ Cleaned previous dist directory")
    
    # Clean Python cache directories to ensure fresh build
    import glob
    for cache_dir in glob.glob("**/__pycache__", recursive=True):
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
    print("✓ Cleaned Python cache directories")
    
    # Check for icon file (optional)
    if not os.path.exists("train.ico"):
        print("⚠ train.ico not found in project root. Building without custom icon.")
    else:
        print("✓ train.ico found")
        # Verify it's a proper .ico file by checking file header
        try:
            with open("train.ico", "rb") as f:
                header = f.read(4)
                if header[:2] != b'\x00\x00' or header[2:4] != b'\x01\x00':
                    print("⚠ Warning: train.ico may not be a valid Windows icon file")
                else:
                    print("✓ train.ico appears to be a valid Windows icon file")
        except Exception as e:
            print(f"⚠ Warning: Could not verify train.ico format: {e}")
    
    # Always use the .spec file for building, to ensure icon and all settings are correct
    spec_file = "Run8ControlConductor.spec"
    venv_path = os.path.join(os.getcwd(), '.venv', 'Scripts', 'pyinstaller.exe')
    if os.path.exists(spec_file):
        if os.path.exists(venv_path):
            cmd_str = f'"{venv_path}" {spec_file}'
        else:
            cmd_str = f"pyinstaller {spec_file}"
        if not run_command(cmd_str, "Building executable with PyInstaller (.spec file, includes icon)"):
            return False
    else:
        print(f"✗ Spec file {spec_file} not found. Please ensure it exists in the project root.")
        return False
    
    # Check if executable was created
    exe_path = dist_dir / "Run8ControlConductor.exe"
    if exe_path.exists():
        print(f"✓ Executable created successfully: {exe_path}")
        print(f"  Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
        
        # Check if the icon was embedded properly
        try:
            import subprocess
            result = subprocess.run(['powershell', '-Command', 
                f'(Get-ItemProperty "{exe_path}").VersionInfo.FileDescription'], 
                capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✓ Executable properties accessible")
        except Exception:
            pass  # Icon verification failed, but continue
            
    else:
        print("✗ Executable not found after build")
        return False
    
    # Create release directory
    release_dir = Path("release")
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    # Copy executable to release directory
    shutil.copy(exe_path, release_dir / "Run8ControlConductor.exe")
    
    # Copy icon to release directory as well
    if os.path.exists("train.ico"):
        shutil.copy("train.ico", release_dir / "train.ico")
        print("✓ Copied train.ico to release directory")
    
    # Create user guide
    user_guide_content = """# Run8 Control Conductor - User Guide

## Quick Start

1. **Download and Run**:
   - Download `Run8ControlConductor.exe`
   - Run the executable (no installation required)
   - Windows may show a security warning - click "More info" then "Run anyway"

2. **First Time Setup**:
   - Connect your joystick/gamepad to your computer
   - Make sure Run8 Train Simulator is running
   - In the application, click "Refresh Devices" to detect your controller
   - Check the box next to your controller to enable it

3. **Map Your Controls**:
   - Navigate through the tabs (Main Controls, Lights & Wipers, etc.)
   - Click "Map Input" next to any function you want to control
   - Move/press the desired control on your joystick within 5 seconds
   - Repeat for all functions you want to use

4. **Start Using**:
   - Click "Start" to begin processing inputs
   - Your joystick inputs will now control Run8 functions
   - Click "Stop" to pause input processing

## Tips

- **Save Your Mappings**: Click "Save Mappings" to save your controller setup
- **Load Mappings**: Click "Load Mappings" to restore previously saved settings
- **Reverse Axis**: For lever controls, check "Reverse" if the direction feels wrong
- **Multiple Controllers**: You can enable and use multiple controllers simultaneously

## Troubleshooting

- **Controller not detected**: Make sure it's connected and working in Windows
- **No response in Run8**: Check that Run8 is running and the IP/port settings are correct
- **Wrong direction**: Use the "Reverse" checkbox for lever controls

## System Requirements

- Windows 10/11 (64-bit)
- Run8 Train Simulator
- USB joystick/gamepad

For support, visit: https://github.com/Antarctican0/ctrlconductor
"""
    
    with open(release_dir / "USER_GUIDE.txt", "w") as f:
        f.write(user_guide_content)
    
    # Copy important files to release directory
    files_to_copy = [
        "README.md",
        "LICENSE",
        "CHANGELOG.md"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy(file, release_dir / file)
    
    print("\n" + "=" * 60)
    print("BUILD COMPLETE!")
    print("=" * 60)
    print(f"✓ Executable: {release_dir / 'Run8ControlConductor.exe'}")
    print(f"✓ User Guide: {release_dir / 'USER_GUIDE.txt'}")
    print(f"✓ Documentation: {release_dir / 'README.md'}")
    print("\nThe 'release' folder contains everything users need!")
    print("You can zip this folder and distribute it to users.")
    
    print("\n" + "=" * 60)
    print("ICON TROUBLESHOOTING")
    print("=" * 60)
    print("If the executable icon doesn't appear correctly:")
    print("1. Try renaming the .exe file to force Windows to refresh")
    print("2. Clear Windows icon cache:")
    print("   - Press Win+R, type 'ie4uinit.exe -show' and press Enter")
    print("   - Or restart Windows Explorer (Ctrl+Shift+Esc > Restart)")
    print("3. Verify train.ico is a proper Windows icon file with multiple sizes")
    print("4. Check if antivirus software is interfering with the executable")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
