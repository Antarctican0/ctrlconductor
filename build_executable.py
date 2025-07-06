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
    
    # Clean previous builds
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("✓ Cleaned previous build directory")
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("✓ Cleaned previous dist directory")
    
    # PyInstaller command
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",  # Create single executable file
        "--windowed",  # Hide console window (GUI app)
        "--name=Run8ControlConductor",
        "--icon=icon.ico" if os.path.exists("icon.ico") else "",
        "--add-data=input_mappings.csv;." if os.path.exists("input_mappings.csv") else "",
        "--hidden-import=pygame",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=config",
        "--hidden-import=networking",
        "--hidden-import=input_handler",
        "--hidden-import=mapping_logic",
        "--hidden-import=ui_components",
        "--hidden-import=utils",
        "--collect-all=pygame",
        "main.py"
    ]
    
    # Remove empty parameters
    pyinstaller_cmd = [arg for arg in pyinstaller_cmd if arg]
    
    # Get the virtual environment path
    venv_path = os.path.join(os.getcwd(), '.venv', 'Scripts', 'pyinstaller.exe')
    
    # Run PyInstaller using the spec file for better reliability
    spec_file = "Run8ControlConductor.spec"
    if os.path.exists(spec_file):
        if os.path.exists(venv_path):
            cmd_str = f'"{venv_path}" {spec_file}'
        else:
            cmd_str = f"pyinstaller {spec_file}"
        
        if not run_command(cmd_str, "Building executable with PyInstaller (using spec file)"):
            return False
    else:
        # Fallback to command line approach
        if os.path.exists(venv_path):
            cmd_str = f'"{venv_path}" ' + " ".join(pyinstaller_cmd[1:])  # Skip 'pyinstaller' itself
        else:
            cmd_str = " ".join(pyinstaller_cmd)
        
        if not run_command(cmd_str, "Building executable with PyInstaller"):
            return False
    
    # Check if executable was created
    exe_path = dist_dir / "Run8ControlConductor.exe"
    if exe_path.exists():
        print(f"✓ Executable created successfully: {exe_path}")
        print(f"  Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
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

For support, visit: https://github.com/your-username/ctrlconductor
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
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
