"""
Simple build script for Run8 Control Conductor

This script creates a standalone single-file executable using PyInstaller.
No spec file required, no extra files or folders needed for distribution.
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

# --- Configuration ---
APP_NAME = "Run8ControlConductor"
SCRIPT_TO_BUILD = "main.py"
# --- End Configuration ---

# Derived paths
SPEC_FILE = f"{APP_NAME}.spec"
EXE_NAME = f"{APP_NAME}.exe"
DIST_PATH = "dist"
FINAL_EXE_PATH = os.path.join(DIST_PATH, EXE_NAME)

def clean_previous_builds():
    """Remove previous build artifacts."""
    print("--- Cleaning up previous build artifacts ---")
    folders_to_remove = ["build", "dist"]
    for folder in folders_to_remove:
        if os.path.exists(folder):
            print(f"Removing {folder}...")
            # Retry logic to handle PermissionError
            for i in range(3): # Try 3 times
                try:
                    shutil.rmtree(folder)
                    print(f"✓ Removed {folder}")
                    break # Success
                except PermissionError:
                    print(f"  ...{folder} is locked, retrying in 2 seconds...")
                    time.sleep(2)
                except Exception as e:
                    print(f"✗ An unexpected error occurred while removing {folder}: {e}")
                    return False # Unrecoverable error
            else: # This block executes if the loop completes without break
                print(f"✗ Error: Could not remove '{folder}'.")
                print("  Please close any running instances of the application or processes that might be using this directory and try again.")
                return False # Failed to clean

    if os.path.exists(SPEC_FILE):
        print(f"Removing {SPEC_FILE}...")
        os.remove(SPEC_FILE)
        print(f"✓ Removed {SPEC_FILE}")

    print("--- Cleanup complete ---")
    return True

def build_executable():
    """Build the standalone executable"""
    print("\nBuilding single executable file...")
    try:
        # Build the executable with PyInstaller
        cmd = "pyinstaller --onefile --noconsole --clean main.py --name Run8ControlConductor"
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("✓ PyInstaller completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ PyInstaller failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main build process"""
    print("=" * 60)
    print("Run8 Control Conductor - Simple Build Script")
    print("=" * 60)
    
    # Check if PyInstaller is available
    try:
        import PyInstaller
        print("✓ PyInstaller is available")
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        try:
            subprocess.run("pip install pyinstaller", shell=True, check=True)
            print("✓ PyInstaller installed successfully")
        except subprocess.CalledProcessError:
            print("✗ Failed to install PyInstaller")
            return False
    
    # Clean previous builds
    clean_previous_builds()
    
    # Build the executable
    if not build_executable():
        return False
    
    # Check if executable was created
    exe_path = Path("dist") / "Run8ControlConductor.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n✓ Executable created successfully!")
        print(f"  Location: {exe_path.absolute()}")
        print(f"  Size: {size_mb:.1f} MB")
        
        # Move executable to root directory for easy access
        root_exe = Path("Run8ControlConductor.exe")
        if root_exe.exists():
            os.remove(root_exe)
        shutil.copy(exe_path, root_exe)
        print(f"✓ Copied executable to {root_exe.absolute()}")
        
        print("\n" + "=" * 60)
        print("BUILD COMPLETE!")
        print("=" * 60)
        print(f"The standalone executable is: {root_exe.absolute()}")
        print("This is the ONLY file you need to distribute to users.")
        return True
    else:
        print("✗ Failed to create executable")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
