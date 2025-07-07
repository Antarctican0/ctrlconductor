"""
Simple build script for Run8 Control Conductor

This script creates an executable using the PyInstaller spec file.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Build the executable using PyInstaller"""
    print("=" * 50)
    print("Building Run8 Control Conductor...")
    print("=" * 50)
    
    # Check if spec file exists
    spec_file = "Run8ControlConductor.spec"
    if not os.path.exists(spec_file):
        print(f"Error: {spec_file} not found!")
        return False
    
    # Build using PyInstaller
    try:
        print("Running PyInstaller...")
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller", 
            "--clean", spec_file
        ], check=True, capture_output=True, text=True)
        
        print("✓ Build completed successfully!")
        
        # Check if executable was created
        exe_path = Path("dist") / "Run8ControlConductor.exe"
        if exe_path.exists():
            print(f"✓ Executable created: {exe_path}")
            print(f"  Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
            return True
        else:
            print("✗ Executable not found!")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\nBuild completed! Check the 'dist' folder for the executable.")
    else:
        print("\nBuild failed!")
        sys.exit(1)
