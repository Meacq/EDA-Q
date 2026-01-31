"""
grid_manager.py - Grid manager
Grid manager responsible for grid initialization, coordinate mapping, and point classification.
"""

import numpy as np
from ..config.constants import DEFAULT_GRID_SIZE


class GridManager:
    """Grid manager class"""
    
    def __init__(self, df, grid_size=DEFAULT_GRID_SIZE):
        self.raw_df = df
        self.grid_size = grid_size
        self.init_mapping()
        self.label_out_points()

    def init_mapping(self):
        """Initialize coordinate mapping, grid_x/grid_y in CSV are grid coordinates"""
        # Filter rows with NA in grid_x or grid_y
        self.raw_df = self.raw_df.dropna(subset=['grid_x', 'grid_y'])

        self.x_min, self.x_max = self.raw_df['grid_x'].min(), self.raw_df['grid_x'].max()
        self.y_min, self.y_max = self.raw_df['grid_y'].min(), self.raw_df['grid_y'].max()

        margin = 2 * self.grid_size
        self.x_min -= margin
        self.y_min -= margin

        # grid_x/grid_y are grid coordinates, calculate grid indices
        self.raw_df['grid_x_idx'] = ((self.raw_df['grid_x'] - self.x_min) / self.grid_size).astype(int)
        self.raw_df['grid_y_idx'] = ((self.raw_df['grid_y'] - self.y_min) / self.grid_size).astype(int)

        self.w = self.raw_df['grid_x_idx'].max() + 3
        self.h = self.raw_df['grid_y_idx'].max() + 3

        self.grid = np.zeros((self.h, self.w), dtype=int)

        for _, row in self.raw_df.iterrows():
            val = 0
            if row['layer'] == 'out':
                val = 1
            elif row['layer'] == 'center':
                val = 2
            elif row['layer'] == 'obstacle':
                val = 3
            elif row['layer'] == 'chip_range':
                val = 4

            if 0 <= row['grid_y_idx'] < self.h and 0 <= row['grid_x_idx'] < self.w:
                self.grid[row['grid_y_idx'], row['grid_x_idx']] = val

    def label_out_points(self):
        """Calculate orientation labels for Out points based on CSV direction column"""
        out_df = self.raw_df[self.raw_df['layer'] == 'out'].copy()
        self.out_labels = {}

        direction_map = {'top': 'Top', 'bottom': 'Bottom', 'left': 'Left', 'right': 'Right'}

        for _, row in out_df.iterrows():
            direction = row.get('direction', '')
            label = direction_map.get(str(direction).lower().strip(), 'Unknown')
            self.out_labels[(row['grid_x_idx'], row['grid_y_idx'])] = label

    def get_points_by_type(self, layer_type):
        """Get point set by type"""
        return self.raw_df[self.raw_df['layer'] == layer_type][['grid_x_idx', 'grid_y_idx']].values

    def get_out_label(self, x, y):
        """Get orientation label of Out point"""
        return self.out_labels.get((x, y), 'Unknown')
