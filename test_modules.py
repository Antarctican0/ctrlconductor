#!/usr/bin/env python3
"""
Test script for Run8 Control Conductor modules

This script performs basic tests to verify all modules can be imported
and basic functionality works correctly.
"""

import sys
import os
import traceback

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported without errors"""
    print("Testing module imports...")
    
    try:
        import config
        print("✓ config module imported successfully")
        
        import utils
        print("✓ utils module imported successfully")
        
        import networking
        print("✓ networking module imported successfully")
        
        import input_handler
        print("✓ input_handler module imported successfully")
        
        import mapping_logic
        print("✓ mapping_logic module imported successfully")
        
        import ui_components
        print("✓ ui_components module imported successfully")
        
        print("All modules imported successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality of key classes"""
    print("\nTesting basic functionality...")
    
    try:
        # Test config
        from config import ThemeConfig, FunctionMapping, DEFAULT_IP, DEFAULT_PORT
        print("✓ Config constants accessible")
        
        # Test networking
        from networking import UDPClient
        client = UDPClient(DEFAULT_IP, DEFAULT_PORT)
        print("✓ UDPClient created")
        
        # Test input handler
        from input_handler import InputManager
        input_mgr = InputManager()
        print("✓ InputManager created")
        
        # Test mapping logic
        from mapping_logic import InputMapper
        mapper = InputMapper()
        print("✓ InputMapper created")
        
        # Test utils
        from utils import StateTracker, PeriodicTimer
        tracker = StateTracker()
        print("✓ StateTracker created")
        
        print("Basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Functionality test error: {e}")
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration values"""
    print("\nTesting configuration...")
    
    try:
        from config import FunctionMapping, ThemeConfig
        
        # Test function mappings
        assert len(FunctionMapping.FUNCTIONS) > 0, "No functions defined"
        assert len(FunctionMapping.INPUT_TYPES) > 0, "No input types defined"
        assert len(FunctionMapping.CATEGORIES) > 0, "No categories defined"
        print("✓ Function mappings are valid")
        
        # Test theme config
        assert hasattr(ThemeConfig, 'DARK_BG'), "Theme colors missing"
        print("✓ Theme configuration is valid")
        
        print("Configuration tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Configuration test error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Run8 Control Conductor - Module Tests")
    print("=" * 50)
    
    all_passed = True
    
    # Run tests
    all_passed &= test_imports()
    all_passed &= test_basic_functionality()
    all_passed &= test_configuration()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! The modules are working correctly.")
        print("You can now run the application with: python main.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
    print("=" * 50)

if __name__ == "__main__":
    main()
