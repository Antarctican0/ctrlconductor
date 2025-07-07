"""
Simple build script for Run8 Control Conductor

This script creates a standalone single-file executable using PyInstaller.
No spec file required, no extra files or folders needed for distribution.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_previous_builds():
    """Remove previous build artifacts"""
    # Clean folders created by PyInstaller
    for folder in ['build', 'dist', 'release', '__pycache__']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"✓ Cleaned {folder} directory")
    
    # Clean any .spec files
    for spec_file in Path('.').glob('*.spec'):
        os.remove(spec_file)
        print(f"✓ Removed {spec_file}")
    
    # Clean __pycache__ directories
    import glob
    for cache_dir in glob.glob("**/__pycache__", recursive=True):
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
    print("✓ Cleaned Python cache directories")

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
