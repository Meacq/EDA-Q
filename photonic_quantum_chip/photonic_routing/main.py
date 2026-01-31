"""
main.py - Program main entry
Application main entry point. Creates root Tkinter window and initializes routing system user interface.
"""

import tkinter as tk
import ctypes
import sys
from .ui.main_window import RoutingSystemUI


def setup_dpi_awareness():
    """Set DPI awareness to ensure correct display on high DPI monitors"""
    try:
        if sys.platform == 'win32':
            # Try to set Per-Monitor DPI Awareness V2 (Windows 10 1703+)
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except:
                # If failed, try to set Per-Monitor DPI Awareness (Windows 8.1+)
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(1)
                except:
                    # If still failed, try to set System DPI Awareness (Windows Vista+)
                    try:
                        ctypes.windll.user32.SetProcessDPIAware()
                    except:
                        pass
    except Exception as e:
        print(f"Failed to set DPI awareness: {e}")


def main():
    """Main function - Initialize GUI and start main event loop"""
    # Set DPI awareness
    setup_dpi_awareness()

    root = tk.Tk()

    # Set scaling to prevent interface from being too large
    root.tk.call('tk', 'scaling', 1.5)

    app = RoutingSystemUI(root)

    # Set window close event handler
    root.protocol("WM_DELETE_WINDOW", app.on_exit)

    # Start Tkinter main event loop
    root.mainloop()


if __name__ == "__main__":
    main()
