"""
__main__.py - Module entry point
Module entry point, supports running via `python -m photonic_routing`.
Responsible for environment setup, including Pickle compatibility handling and data directory initialization.
"""

import sys
import os

def setup_environment():
    """Configure runtime environment, including Pickle compatibility settings and data directory initialization"""
    import __main__

    try:
        from photonic_routing.core.data_structures import DiagonalBitmap
        __main__.DiagonalBitmap = DiagonalBitmap
        print("[Compatibility] Pickle serialization class registered")
    except ImportError as e:
        print(f"[Warning] Failed to import data structure class: {e}")

    try:
        from photonic_routing.config.paths import ensure_directories
        ensure_directories()
    except Exception as e:
        print(f"[Warning] Failed to initialize data directories: {e}")

def main():
    """Main entry function"""
    print("=" * 60)
    print("Photonic Quantum Chip Routing System v0.0.0")
    print("Photonic Quantum Chip Routing System")
    print("=" * 60)
    
    setup_environment()
    
    try:
        from photonic_routing.main import main as app_main
        app_main()
    except ImportError as e:
        print(f"\n[Error] Module import failed: {e}")
        print("\nPlease check:")
        print("1. Whether all required files exist")
        print("2. Whether dependencies are installed")
        print("\nRun the following command to install dependencies:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n[Error] Program startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()