"""
geometry.py - Geometry calculation tools
Geometry calculation utilities, including Euclidean distance calculation.
Provides Numba accelerated version and pure Python implementation version.
"""

import math
from ..config.constants import NUMBA_AVAILABLE, jit


if NUMBA_AVAILABLE:
    @jit(nopython=True, cache=True)
    def euclidean_dist_numba(x1, y1, x2, y2):
        """Calculate Euclidean distance between two points (Numba accelerated)"""
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
else:
    def euclidean_dist_numba(x1, y1, x2, y2):
        """Calculate Euclidean distance between two points (pure Python)"""
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)