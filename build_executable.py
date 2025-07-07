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
    
    # Clean previous builds and cache
    dist_dir = Path("dist")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("✓ Cleaned previous dist directory")
    import glob
    for cache_dir in glob.glob("**/__pycache__", recursive=True):
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
    print("✓ Cleaned Python cache directories")
    
    # No icon required for build. Skipping icon checks.
    print("✓ Skipping icon checks (no icon required)")
    
    # Build a single-file executable with PyInstaller (no .spec, no icon, no docs)
    if not run_command(
        'pyinstaller --onefile --noconsole --clean main.py --name Run8ControlConductor',
        'Building single-file executable with PyInstaller'):
        return False
    
    # Check if executable was created
    exe_path = dist_dir / "Run8ControlConductor.exe"
    if exe_path.exists():
        print(f"✓ Executable created successfully: {exe_path}")
        print(f"  Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
    else:
        print("✗ Executable not found after build")
        return False
    print("\nBUILD COMPLETE!")
    print(f"Your single-file executable is at: {exe_path}")
    print("Distribute this .exe file to users. No extra files needed.")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
