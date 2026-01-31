"""
gds_tools.py - GDS processing utility class
Contains core functionality for GDS coordinate extraction and path export
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path

try:
    import gdspy
except ImportError:
    gdspy = None

try:
    import pickle
except ImportError:
    pickle = None


class GDSProcessor:
    """GDS coordinate extraction processor"""

    def __init__(self, gds_file, progress_callback=None):
        """
        Initialize GDS processor

        Args:
            gds_file: GDS file path
            progress_callback: Progress callback function callback(message, percent)
        """
        if gdspy is None:
            raise ImportError("Need to install gdspy library: pip install gdspy")

        self.gds_file = gds_file
        self.lib = gdspy.GdsLibrary(infile=gds_file)
        self.all_coordinates = []
        self.grid_size = None
        self.direction_bounds = {}
        self.progress_callback = progress_callback

    def _log(self, message, percent=None):
        """Log message"""
        if self.progress_callback:
            self.progress_callback(message, percent)

    def get_cell_names(self):
        """Get all cell names"""
        return list(self.lib.cells.keys())

    def extract_rectangles(self, cell_name, width, height, label, position='center', direction=None, tolerance=0.001):
        """
        Extract rectangle key points of specified dimensions

        Args:
            cell_name: Cell name
            width: Rectangle width
            height: Rectangle height
            label: Label type (center/out/obstacle/chip_range)
            position: Key point position (center/top_left/top_right/bottom_left/bottom_right/all_vertices)
            direction: Direction filter (top/bottom/left/right)
            tolerance: Dimension tolerance

        Returns:
            (rectangles, error_message): Extracted rectangle list and error message
        """
        rectangles = []
        if cell_name not in self.lib.cells:
            return rectangles, f"Warning: Cell '{cell_name}' not found"

        cell = self.lib.cells[cell_name]
        all_polygons = cell.get_polygons(by_spec=True)

        for polygons in all_polygons.values():
            for polygon in polygons:
                if self._is_rectangle_with_size(polygon, width, height, tolerance):
                    if label == 'chip_range' or position == 'all_vertices':
                        # chip_range or all_vertices extract four corners
                        x_coords = polygon[:, 0]
                        y_coords = polygon[:, 1]
                        x_min, x_max = np.min(x_coords), np.max(x_coords)
                        y_min, y_max = np.min(y_coords), np.max(y_coords)

                        # If direction filter exists, check if rectangle center is in specified direction
                        if direction:
                            center_x = (x_min + x_max) / 2
                            center_y = (y_min + y_max) / 2
                            if not self._check_direction(center_x, center_y, direction):
                                continue

                        rectangles.extend([
                            {'x': x_min, 'y': y_min, 'layer': label, 'direction': direction if direction else ''},
                            {'x': x_max, 'y': y_min, 'layer': label, 'direction': direction if direction else ''},
                            {'x': x_min, 'y': y_max, 'layer': label, 'direction': direction if direction else ''},
                            {'x': x_max, 'y': y_max, 'layer': label, 'direction': direction if direction else ''}
                        ])
                    else:
                        point = self._extract_key_point(polygon, position, direction)
                        if point:
                            rectangles.append({
                                'x': point[0],
                                'y': point[1],
                                'layer': label,
                                'direction': direction if direction else ''
                            })

        if not rectangles:
            return rectangles, f"Warning: No {width}x{height} rectangle found in cell '{cell_name}'"

        return rectangles, None

    def _is_rectangle_with_size(self, polygon, target_width, target_height, tolerance):
        """Check if polygon is a rectangle of specified dimensions"""
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

        # Direction filter
        if direction:
            center_x = (x_min + x_max) / 2
            center_y = (y_min + y_max) / 2
            if not self._check_direction(center_x, center_y, direction):
                return None

        # Position selection
        if position == 'center':
            return ((x_min + x_max) / 2, (y_min + y_max) / 2)
        elif position == 'top_left':
            return (x_min, y_max)
        elif position == 'top_right':
            return (x_max, y_max)
        elif position == 'bottom_left':
            return (x_min, y_min)
        elif position == 'bottom_right':
            return (x_max, y_min)
        return None

    def _check_direction(self, x, y, direction):
        """Check if point is in specified direction"""
        if direction not in self.direction_bounds:
            return True
        bounds = self.direction_bounds[direction]
        if 'x_min' in bounds and x < bounds['x_min']:
            return False
        if 'x_max' in bounds and x > bounds['x_max']:
            return False
        if 'y_min' in bounds and y < bounds['y_min']:
            return False
        if 'y_max' in bounds and y > bounds['y_max']:
            return False
        return True

    def set_direction_bounds(self, direction, x_min=None, x_max=None, y_min=None, y_max=None):
        """Set direction bounds"""
        if direction not in self.direction_bounds:
            self.direction_bounds[direction] = {}
        if x_min is not None:
            self.direction_bounds[direction]['x_min'] = x_min
        if x_max is not None:
            self.direction_bounds[direction]['x_max'] = x_max
        if y_min is not None:
            self.direction_bounds[direction]['y_min'] = y_min
        if y_max is not None:
            self.direction_bounds[direction]['y_max'] = y_max

    def map_to_grid(self, grid_size):
        """
        Map coordinates to grid

        Args:
            grid_size: Grid size

        Returns:
            DataFrame: Mapped coordinate data
        """
        self.grid_size = grid_size
        df = pd.DataFrame(self.all_coordinates)

        if df.empty:
            return df

        # x/y keep original coordinates, grid_x/grid_y are mapped grid coordinates
        df['grid_x'] = np.round(df['x'] / grid_size) * grid_size
        df['grid_y'] = np.round(df['y'] / grid_size) * grid_size

        # Deduplication based on grid coordinates and layer
        df = df.drop_duplicates(subset=['grid_x', 'grid_y', 'layer']).reset_index(drop=True)
        self.all_coordinates = df.to_dict('records')

        self._log(f"Coordinates mapped to grid size {grid_size}", 40)
        return df

    def expand_obstacles(self, left_right_grids, top_bottom_grids):
        """
        Expand existing obstacle coordinates

        Args:
            left_right_grids: Number of grids to expand left/right
            top_bottom_grids: Number of grids to expand top/bottom
        """
        df = pd.DataFrame(self.all_coordinates)
        if df.empty or 'obstacle' not in df['layer'].values:
            self._log("No obstacles to expand", 60)
            return

        obstacle_points = df[df['layer'] == 'obstacle'][['grid_x', 'grid_y']].values

        new_obstacles = set()
        for gx, gy in obstacle_points:
            for dx in range(-left_right_grids, left_right_grids + 1):
                for dy in range(-top_bottom_grids, top_bottom_grids + 1):
                    gx_new = gx + dx * self.grid_size
                    gy_new = gy + dy * self.grid_size
                    new_obstacles.add((gx_new, gy_new))

        # Remove original obstacle points, add expanded points
        self.all_coordinates = [c for c in self.all_coordinates if c['layer'] != 'obstacle']
        for gx, gy in new_obstacles:
            self.all_coordinates.append({
                'x': gx, 'y': gy, 'layer': 'obstacle',
                'direction': '', 'grid_x': gx, 'grid_y': gy
            })

        self._log(f"Obstacle expansion complete, total {len(new_obstacles)} obstacle points", 70)

    def add_obstacle_between_points(self, label, distance):
        """
        Add obstacles between points of specified label at specific distance

        Args:
            label: Target label
            distance: Distance parameter
        """
        df = pd.DataFrame(self.all_coordinates)
        if df.empty or label not in df['layer'].values:
            self._log(f"No points with label '{label}' found", 80)
            return

        target_points = df[df['layer'] == label][['grid_x', 'grid_y']].values

        new_obstacles = set()
        y_groups = defaultdict(list)
        for gx, gy in target_points:
            y_groups[gy].append(gx)

        for gy, gx_list in y_groups.items():
            gx_sorted = sorted(gx_list)
            for i in range(len(gx_sorted)):
                for j in range(i + 1, len(gx_sorted)):
                    gx1, gx2 = gx_sorted[i], gx_sorted[j]
                    if abs(gx2 - gx1) == distance:
                        steps = int(distance / self.grid_size)
                        for k in range(1, steps):
                            gx_between = gx1 + k * self.grid_size
                            if (gx_between, gy) not in [(px, py) for px, py in target_points]:
                                new_obstacles.add((gx_between, gy))

        for gx, gy in new_obstacles:
            self.all_coordinates.append({
                'x': gx, 'y': gy, 'layer': 'obstacle',
                'direction': '', 'grid_x': gx, 'grid_y': gy
            })

        self._log(f"Added {len(new_obstacles)} obstacle points between points with label '{label}'", 90)

    def create_visualization(self):
        """
        Create visualization figure

        Returns:
            matplotlib.figure.Figure: Figure object
        """
        df = pd.DataFrame(self.all_coordinates)
        if df.empty:
            return None

        layer_colors = {
            'center': '#d62728',
            'out': '#1f77b4',
            'obstacle': '#2ca02c',
            'chip_range': '#9467bd'
        }

        fig = plt.figure(figsize=(12, 9), dpi=100)

        for layer_type in df['layer'].unique():
            layer_data = df[df['layer'] == layer_type]
            color = layer_colors.get(layer_type, '#ff7f0e')
            plt.scatter(layer_data['grid_x'], layer_data['grid_y'],
                       c=color, label=layer_type, s=5, alpha=0.9,
                       edgecolors='none', zorder=10)

        x_min = df['grid_x'].min() - 2 * self.grid_size
        x_max = df['grid_x'].max() + 2 * self.grid_size
        y_min = df['grid_y'].min() - 2 * self.grid_size
        y_max = df['grid_y'].max() + 2 * self.grid_size

        plt.xlim(x_min, x_max)
        plt.ylim(y_min, y_max)

        grid_x_range = np.arange(np.floor(x_min/self.grid_size)*self.grid_size,
                                 np.ceil(x_max/self.grid_size)*self.grid_size + self.grid_size,
                                 self.grid_size)
        grid_y_range = np.arange(np.floor(y_min/self.grid_size)*self.grid_size,
                                 np.ceil(y_max/self.grid_size)*self.grid_size + self.grid_size,
                                 self.grid_size)

        for x in grid_x_range:
            plt.axvline(x=x, color='gray', linestyle='-', linewidth=0.3, alpha=0.1, zorder=0)
        for y in grid_y_range:
            plt.axhline(y=y, color='gray', linestyle='-', linewidth=0.3, alpha=0.1, zorder=0)

        plt.xlabel('X Coordinate', fontsize=12)
        plt.ylabel('Y Coordinate', fontsize=12)
        plt.title(f'GDS Coordinate Extraction and Grid Mapping (Grid Size = {self.grid_size})',
                 fontsize=14, fontweight='bold')
        plt.legend(loc='best', fontsize=10, framealpha=0.8)
        plt.gca().set_facecolor('#f8f8f8')
        plt.tight_layout()

        # Set default subplot margin parameters to ensure complete content display
        fig.subplots_adjust(left=0.064, bottom=0.395, right=0.976, top=0.971,
                           wspace=0.243, hspace=0.255)

        self._log("Visualization figure generated", 95)
        return fig

    def save_to_csv(self, filename):
        """
        Save to CSV file

        Args:
            filename: Output file path

        Returns:
            (success, message): Success flag and message
        """
        try:
            df = pd.DataFrame(self.all_coordinates)
            if df.empty:
                return False, "No data to save"

            df = df.drop_duplicates(subset=['grid_x', 'grid_y', 'layer']).reset_index(drop=True)

            # For non-out/center points, set x/y to empty
            # First convert x and y columns to object type to avoid dtype incompatibility warnings
            mask = ~df['layer'].isin(['out', 'center'])
            df['x'] = df['x'].astype(object)
            df['y'] = df['y'].astype(object)
            df.loc[mask, 'x'] = ''
            df.loc[mask, 'y'] = ''

            cols = ['grid_x', 'grid_y', 'layer', 'direction', 'x', 'y']
            df = df[[c for c in cols if c in df.columns]]

            df.to_csv(filename, index=False)

            stats = f"Total points: {len(df)}\n"
            for layer in df['layer'].unique():
                count = len(df[df['layer'] == layer])
                stats += f"  {layer}: {count} points\n"

            self._log(f"Coordinates saved to: {filename}\n{stats}", 100)
            return True, stats
        except Exception as e:
            return False, f"Save failed: {str(e)}"


class UnpicklerWithoutImports(pickle.Unpickler):
    """Custom Unpickler to avoid importing modules"""
    def find_class(self, module, name):
        if module.startswith('photonic_routing'):
            return type(name, (), {})
        return super().find_class(module, name)


class PathExporter:
    """Path export and merge processor"""

    def __init__(self, progress_callback=None):
        """
        Initialize path exporter

        Args:
            progress_callback: Progress callback function callback(message, percent)
        """
        if gdspy is None:
            raise ImportError("Need to install gdspy library: pip install gdspy")
        if pickle is None:
            raise ImportError("Need to install pickle library")

        self.progress_callback = progress_callback

    def _log(self, message, percent=None):
        """Log message"""
        if self.progress_callback:
            self.progress_callback(message, percent)

    def export_and_merge(self, pkl_path, csv_path, target_gds, output_gds,
                        grid_size, layer, datatype, path_width, target_cell_name):
        """
        Convert paths to continuous polygon GDS and merge to target file

        Args:
            pkl_path: PKL file path
            csv_path: CSV coordinate file path
            target_gds: Target GDS file path
            output_gds: Output GDS file path
            grid_size: Grid size
            layer: GDS layer number
            datatype: GDS data type
            path_width: Path width
            target_cell_name: Target cell name

        Returns:
            (success, message, converted_paths): Success flag, message and converted paths
        """
        try:
            # Read CSV to get coordinate range and mapping relationship
            self._log("Reading CSV file...", 10)
            df = pd.read_csv(csv_path)
            x_min_orig = df['grid_x'].min()
            y_min_orig = df['grid_y'].min()

            # Calculate conversion parameters
            margin = 2 * grid_size
            x_min = x_min_orig - margin
            y_min = y_min_orig - margin

            # Build coordinate mapping from CSV
            coord_map = {}
            if 'grid_x' in df.columns and 'grid_y' in df.columns:
                for _, row in df.iterrows():
                    coord_map[(row['grid_x'], row['grid_y'])] = (row['x'], row['y'])

            # Load pkl file
            self._log("Reading PKL file...", 20)
            with open(pkl_path, 'rb') as f:
                data = UnpicklerWithoutImports(f).load()

            all_paths = data.get('all_finished_paths', [])
            self._log(f"Found {len(all_paths)} paths", 30)

            # Convert path coordinates
            self._log("Converting path coordinates...", 40)
            converted_paths = self._convert_paths(all_paths, grid_size, x_min, y_min, coord_map)

            # Read target GDS
            self._log("Reading target GDS file...", 60)
            target_lib = gdspy.GdsLibrary(infile=target_gds)

            if target_cell_name not in target_lib.cells:
                return False, f"Error: {target_cell_name} layer not found in {target_gds}", []

            target_cell = target_lib.cells[target_cell_name]

            # Add paths
            self._log("Adding paths to GDS...", 70)
            path_count = 0
            for path_coords in converted_paths:
                if len(path_coords) < 2:
                    continue

                flexpath = self._create_flexpath(path_coords, path_width, layer, datatype)
                if flexpath:
                    target_cell.add(flexpath)
                    path_count += 1

            # Save merged GDS
            self._log("Saving GDS file...", 90)
            target_lib.write_gds(output_gds)

            message = f"Successfully merged {path_count} continuous paths to {target_cell_name} layer"
            self._log(message, 100)

            return True, message, converted_paths

        except Exception as e:
            return False, f"Processing failed: {str(e)}", []

    def _convert_paths(self, all_paths, grid_size, x_min, y_min, coord_map):
        """Convert path coordinates"""
        converted_paths = []

        for path in all_paths:
            if not path:
                continue

            converted_path = []
            start_grid_coords = None
            second_grid_coords = None
            end_grid_coords = None

            for i, (grid_x, grid_y) in enumerate(path):
                if i == 0:
                    start_grid_coords = (grid_x, grid_y)
                elif i == 1:
                    second_grid_coords = (grid_x, grid_y)
                elif i == len(path) - 1:
                    end_grid_coords = (grid_x, grid_y)

                orig_x = grid_x * grid_size + x_min
                orig_y = grid_y * grid_size + y_min

                if (i == 0 or i == len(path) - 1) and (orig_x, orig_y) in coord_map:
                    real_x, real_y = coord_map[(orig_x, orig_y)]
                    converted_path.append((real_x, real_y))
                else:
                    converted_path.append((orig_x, orig_y))

            # Adjust second point to fix start offset
            if len(converted_path) >= 3 and start_grid_coords and second_grid_coords:
                x0, y0 = converted_path[0]
                x1, y1 = converted_path[1]
                _, y2 = converted_path[2]

                start_orig_x = start_grid_coords[0] * grid_size + x_min
                start_orig_y = start_grid_coords[1] * grid_size + y_min
                if (start_orig_x, start_orig_y) in coord_map:
                    x0_original, y0_original = coord_map[(start_orig_x, start_orig_y)]
                else:
                    x0_original, y0_original = x0, y0

                second_orig_y = second_grid_coords[1] * grid_size + y_min

                if second_orig_y == start_orig_y:
                    converted_path[1] = (x1, y0_original)
                else:
                    converted_path[1] = (x0_original, y2)
            elif len(converted_path) == 2 and start_grid_coords:
                x0, y0 = converted_path[0]
                x1, y1 = converted_path[1]

                start_orig_x = start_grid_coords[0] * grid_size + x_min
                start_orig_y = start_grid_coords[1] * grid_size + y_min
                if (start_orig_x, start_orig_y) in coord_map:
                    _, y0_for_comparison = coord_map[(start_orig_x, start_orig_y)]
                else:
                    y0_for_comparison = y0

                if y1 != y0_for_comparison:
                    dx = abs(x1 - x0)
                    dy = abs(y1 - y0)
                    if dx < dy:
                        converted_path[1] = (x0, y1)
                    else:
                        converted_path[1] = (x1, y0)

            # Adjust second-to-last point to fix end offset
            if len(converted_path) >= 2 and end_grid_coords:
                end_orig_x = end_grid_coords[0] * grid_size + x_min
                end_orig_y = end_grid_coords[1] * grid_size + y_min

                if (end_orig_x, end_orig_y) in coord_map:
                    end_x_original, end_y_original = coord_map[(end_orig_x, end_orig_y)]
                else:
                    end_x_original, end_y_original = converted_path[-1]

                if len(converted_path) >= 2:
                    second_last_x, second_last_y = converted_path[-2]

                    dx_offset = abs(second_last_x - end_x_original)
                    dy_offset = abs(second_last_y - end_y_original)

                    if dx_offset < dy_offset:
                        converted_path[-2] = (end_x_original, second_last_y)
                    else:
                        converted_path[-2] = (second_last_x, end_y_original)

            converted_paths.append(converted_path)

        return converted_paths

    def _create_flexpath(self, path_coords, width, layer, datatype):
        """Create path with rounded corners using FlexPath"""
        if len(path_coords) < 2:
            return None

        return gdspy.FlexPath(path_coords, width, layer=layer, datatype=datatype,
                             corners='circular bend', bend_radius=width,
                             tolerance=0.001, max_points=0)

    def save_path_coordinates(self, converted_paths, output_file):
        """
        Save converted path coordinates to text file

        Args:
            converted_paths: List of converted paths
            output_file: Output file path

        Returns:
            (success, message): Success flag and message
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("Converted path coordinates (mapped to original coordinates with second and second-to-last point corrections)\n")
                f.write("=" * 80 + "\n\n")

                for i, path_coords in enumerate(converted_paths, 1):
                    f.write(f"Path {i} (total {len(path_coords)} points):\n")
                    for j, (x, y) in enumerate(path_coords):
                        f.write(f"  Point {j+1}: ({x:.6f}, {y:.6f})\n")
                    f.write("\n")

                f.write("=" * 80 + "\n")
                f.write(f"Total: {len(converted_paths)} paths\n")
                f.write("=" * 80 + "\n")

            return True, f"Path coordinates saved to: {output_file}"
        except Exception as e:
            return False, f"Save failed: {str(e)}"
