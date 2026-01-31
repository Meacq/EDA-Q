"""
gds_function_dialogs.py - GDS Function Dialogs
Fully integrated version, all functions completed in UI, no need to call terminal
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict

try:
    import gdspy
except ImportError:
    gdspy = None

try:
    import pickle
except ImportError:
    pickle = None

from ..config.ui_config import UI_COLORS
from ..utils.helpers import center_window_right


# ==================== GDS Coordinate Extraction Tool ====================

class GDSProcessor:
    """GDS coordinate extraction processor"""
    def __init__(self, gds_file):
        if gdspy is None:
            raise ImportError("Need to install gdspy library: pip install gdspy")

        self.gds_file = gds_file
        self.lib = gdspy.GdsLibrary(infile=gds_file)
        self.all_coordinates = []
        self.grid_size = None

    def extract_rectangles(self, cell_name, width, height, label, position='center', direction=None, tolerance=0.001):
        """Extract key points of rectangles with specified dimensions"""
        rectangles = []
        if cell_name not in self.lib.cells:
            return rectangles, f"Warning: cell '{cell_name}' not found"

        cell = self.lib.cells[cell_name]
        all_polygons = cell.get_polygons(by_spec=True)
        for polygons in all_polygons.values():
            for polygon in polygons:
                if self._is_rectangle_with_size(polygon, width, height, tolerance):
                    if label == 'chip_range':
                        # chip_range extract four corners
                        x_coords = polygon[:, 0]
                        y_coords = polygon[:, 1]
                        x_min, x_max = np.min(x_coords), np.max(x_coords)
                        y_min, y_max = np.min(y_coords), np.max(y_coords)
                        rectangles.extend([
                            {'x': x_min, 'y': y_min, 'layer': label, 'direction': ''},
                            {'x': x_max, 'y': y_min, 'layer': label, 'direction': ''},
                            {'x': x_min, 'y': y_max, 'layer': label, 'direction': ''},
                            {'x': x_max, 'y': y_max, 'layer': label, 'direction': ''}
                        ])
                    else:
                        point = self._extract_key_point(polygon, position, direction)
                        if point:
                            rectangles.append({'x': point[0], 'y': point[1], 'layer': label, 'direction': direction if direction else ''})

        return rectangles, None

    def _is_rectangle_with_size(self, polygon, target_width, target_height, tolerance):
        """Check if polygon is a rectangle with specified dimensions"""
        if len(polygon) not in [4, 5]:
            return False
        x_coords = polygon[:, 0]
        y_coords = polygon[:, 1]
        width = np.max(x_coords) - np.min(x_coords)
        height = np.max(y_coords) - np.min(y_coords)
        return abs(width - target_width) < tolerance and abs(height - target_height) < tolerance

    def _extract_key_point(self, polygon, position, direction=None):
        """Extract key point of rectangle"""
        x_coords = polygon[:, 0]
        y_coords = polygon[:, 1]
        x_min, x_max = np.min(x_coords), np.max(x_coords)
        y_min, y_max = np.min(y_coords), np.max(y_coords)
