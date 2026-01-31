"""
config - Configuration module
Configuration module includes user interface configuration, constants, and path management.
"""

from .ui_config import UI_COLORS, CANVAS_COLORS, CANVAS_SIZES
from .constants import (
    NUMBA_AVAILABLE,
    DEFAULT_GRID_SIZE
)

from .paths import (
    PROJECT_ROOT,
    DATA_DIR,
    INPUT_DIR,
    OUTPUT_DIR,
    ROUTING_DIR,
    FIGURES_DIR,
    CACHE_DIR,
    ensure_directories,
    get_routing_file,
    get_figure_file,
    list_routing_files,
    print_paths
)

__all__ = [
    'UI_COLORS',
    'CANVAS_COLORS',
    'CANVAS_SIZES',
    'NUMBA_AVAILABLE',
    'DEFAULT_GRID_SIZE',
    'PROJECT_ROOT',
    'DATA_DIR',
    'INPUT_DIR',
    'OUTPUT_DIR',
    'ROUTING_DIR',
    'FIGURES_DIR',
    'CACHE_DIR',
    'ensure_directories',
    'get_routing_file',
    'get_figure_file',
    'list_routing_files',
    'print_paths'
]
