#!/usr/bin/env python3
"""
Startup Script
Main entry point for the Photonic Quantum Chip Routing System.
Responsible for environment setup, Pickle compatibility handling, and data directory initialization.
"""

import sys
import os

# Add project path to system path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def setup_pickle_compatibility():
    """Setup Pickle serialization compatibility, register data structure classes to main module"""
    import __main__

    try:
        from photonic_routing.core.data_structures import DiagonalBitmap
        __main__.DiagonalBitmap = DiagonalBitmap
        print("[Compatibility] Pickle serialization class registered")
        return True
    except ImportError as e:
        print(f"[Warning] Failed to import data structure class: {e}")
        return False

def setup_data_directories():
    """Initialize data directory structure"""
    try:
        from photonic_routing.config.paths import ensure_directories, print_paths
        ensure_directories()
        print_paths()
        return True
    except Exception as e:
        print(f"[Warning] Failed to initialize data directories: {e}")
        return False

# Execute initialization
setup_pickle_compatibility()
setup_data_directories()

if __name__ == "__main__":
    try:
        print("Starting Photonic Quantum Chip Routing System...")
        from photonic_routing.main import main
        main()
    except ImportError as e:
        print(f"\n[Error] Module import failed: {e}")
        print("\nPlease check:")
        print("1. Whether all required files exist")
        print("2. Whether all directories contain __init__.py files")
        print("3. Whether required dependencies are installed (numpy, pandas, matplotlib)")
        print("\nRun the following command to check if dependencies are installed:")
        print("pip list | findstr \"numpy pandas matplotlib\"")
        input("\nPress Enter to exit...")
    except Exception as e:
        print(f"\n[Error] Program startup failed: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")