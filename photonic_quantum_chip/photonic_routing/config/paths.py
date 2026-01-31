"""
paths.py - Path management configuration
Unified path management for all data files including input, output, routing, and figures.
Provides centralized directory structure and file path generation functionality.
"""

import os
from pathlib import Path

# ========== 1. Determine project root directory ==========
# __file__ is the path of current file: .../photonic_routing/config/paths.py
# .parent is parent directory: .../photonic_routing/config/
# .parent.parent is project root: .../photonic_routing/
# .absolute() converts to absolute path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
# Result: /home/user/photonic-chip-routing/photonic_routing


# ========== 2. Define data directory structure ==========
DATA_DIR = PROJECT_ROOT / "data"                    # Data root directory
INPUT_DIR = DATA_DIR / "input"                      # Input data
INPUT_GDS_DIR = INPUT_DIR / "gds"                   # Input GDS files
INPUT_CSV_DIR = INPUT_DIR / "csv"                   # Input CSV files
OUTPUT_DIR = DATA_DIR / "output"                    # Output data
ROUTING_DIR = OUTPUT_DIR / "routing"                # Routing files
FIGURES_DIR = OUTPUT_DIR / "figures"                # Figure files
GDS_DIR = OUTPUT_DIR / "gds"                        # Output GDS files
CACHE_DIR = DATA_DIR / "cache"                      # Temporary cache

# Path objects support / operator, very elegant:
# PROJECT_ROOT / "data" is equivalent to os.path.join(PROJECT_ROOT, "data")


# ========== 3. Auto-create directories ==========
def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        DATA_DIR,
        INPUT_DIR,
        INPUT_GDS_DIR,
        INPUT_CSV_DIR,
        OUTPUT_DIR,
        ROUTING_DIR,
        FIGURES_DIR,
        GDS_DIR,
        CACHE_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        # parents=True: create all parent directories
        # exist_ok=True: do not raise error if directory already exists
    
    print(f"[Path Management] Data directories initialized: {DATA_DIR}")


# ========== 4. Default file paths ==========
DEFAULT_INPUT_CSV = INPUT_DIR / "chip_layout.csv"
DEFAULT_ROUTING_PREFIX = ROUTING_DIR / "routing"
DEFAULT_FIGURE_PREFIX = FIGURES_DIR / "stage"


# ========== 5. Path generation functions ==========
def get_routing_file(task_count=None):
    """
    Get routing file path
    
    Examples:
        get_routing_file(1) → .../data/output/routing/routing_1.pkl
        get_routing_file() → .../data/output/routing/routing_latest.pkl
    """
    if task_count is None:
        return ROUTING_DIR / "routing_latest.pkl"
    return ROUTING_DIR / f"routing_{task_count}.pkl"


def get_figure_file(stage_name, task_count):
    """
    Get figure save path
    
    Examples:
        get_figure_file("Stage1", 5) 
        → .../data/output/figures/stage1_region_5.png
    """
    return FIGURES_DIR / f"{stage_name.lower()}_region_{task_count}.png"


# ========== 6. List files ==========
def list_routing_files():
    """List all routing files, sorted by modification time"""
    if not ROUTING_DIR.exists():
        return []
    
    files = list(ROUTING_DIR.glob("*.pkl"))
    # glob("*.pkl") finds all .pkl files
    
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    # Sort by modification time in descending order (newest first)
    
    return files


# ========== 7. Debug helper functions ==========
def print_paths():
    """Print all configured paths (for debugging)"""
    print("\n=== Path Configuration ===")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Data directory: {DATA_DIR}")
    print(f"Input directory: {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Routing files directory: {ROUTING_DIR}")
    print(f"Figure output directory: {FIGURES_DIR}")
    print(f"Cache directory: {CACHE_DIR}")
    print("=" * 40 + "\n")