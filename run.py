#!/usr/bin/env python3
"""
Run8 Control Conductor - Launch Script

Convenience script to launch the Run8 Control Conductor application.
This script handles common startup tasks and provides helpful information.
"""

import sys
import os

def main():
    """Launch the Run8 Control Conductor application"""
    print("🚂 Run8 Control Conductor v3.0 - Modular Edition")
    print("=" * 50)
    
    try:
        # Add current directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Import and run the main application
        from main import main as run_main
        
        print("Starting application...")
        print("Close the GUI window to exit.")
        print("=" * 50)
        
        # Run the main application
        run_main()
        
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
        sys.exit(0)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check the console output for more details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
