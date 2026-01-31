"""
constants.py - Constants definition
System-wide constants including Numba JIT compilation configuration, default parameters, and version information.
"""

import matplotlib.pyplot as plt

# Try to import numba for JIT acceleration
try:
    from numba import jit
    NUMBA_AVAILABLE = True
    print("[System] Numba JIT acceleration enabled")
except ImportError:
    NUMBA_AVAILABLE = False
    print("[Warning] Numba not installed, will use pure Python implementation")
    # Define empty decorator
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# Set Chinese font support
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# Default configuration
DEFAULT_GRID_SIZE = 15

# Version information
VERSION = "0.0.0"
APP_TITLE = "Photonic Quantum Chip Routing System"
