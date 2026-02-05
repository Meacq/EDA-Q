"""
Electrode generation and management
"""
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.gp import gp_Pnt
import math

class ElectrodeGenerator:
    """Generator for electrodes and electrode regions"""
    
    def __init__(self, coord_system, chip_params, electrode_params):
        self.coord_system = coord_system
        self.chip_params = chip_params
        self.electrode_params = electrode_params
        self.electrode_counter = 0
        self.electrode_regions = {}
        self.electrode_corner_points = []
        self.electrode_extended_points = []
    
    def calculate_interface_layer_intersection_points(self):
        """Calculate intersection points at interface layer width"""
        long_half_width = self.chip_params['trap_long_width_interface'] / 2
        short_half_width = self.chip_params['trap_short_width_interface'] / 2
        short_offset = self.chip_params['short_slot_offset']
        
        intersection_points = [
            (short_offset - short_half_width, long_half_width),   # Upper left
            (short_offset + short_half_width, long_half_width),   # Upper right  
            (short_offset - short_half_width, -long_half_width),  # Lower left
            (short_offset + short_half_width, -long_half_width),  # Lower right
        ]
            
        return intersection_points
    
    def generate_electrode_regions(self, intersection_points):
        """Generate electrode regions for 8 directions"""
        regions = []
        safety_margin = self.electrode_params['cross_safety_margin']
        
        region_configs = [
            (0, (-1, 0), "left_top_left", self.electrode_params.get('left_top_left', 8)),
            (0, (0, 1), "left_top_up", self.electrode_params.get('left_top_up', 8)),
            (1, (1, 0), "right_top_right", self.electrode_params.get('right_top_right', 8)),
            (1, (0, 1), "right_top_up", self.electrode_params.get('right_top_up', 8)),
            (2, (-1, 0), "left_bottom_left", self.electrode_params.get('left_bottom_left', 8)),
            (2, (0, -1), "left_bottom_down", self.electrode_params.get('left_bottom_down', 8)),
            (3, (1, 0), "right_bottom_right", self.electrode_params.get('right_bottom_right', 8)),
            (3, (0, -1), "right_bottom_down", self.electrode_params.get('right_bottom_down', 8)),
        ]
        
        for point_index, (dx, dy), region_key, electrode_count in region_configs:
            cx, cy = intersection_points[point_index]
            
            in_long_slot = self._is_in_long_slot_region(cx, cy, dx, dy)
            
            start_x = cx + dx * safety_margin
            start_y = cy + dy * safety_margin

            # Calculate total length considering individual electrode parameters
            total_length = self._calculate_region_total_length(region_key, electrode_count)

            end_x = start_x + dx * total_length
            end_y = start_y + dy * total_length
            
            region = {
                'id': len(regions),
                'key': region_key,
                'label': region_key.replace('_', '-'),
                'intersection_point': (cx, cy),
                'start_point': (start_x, start_y),
                'end_point': (end_x, end_y),
                'direction': (dx, dy),
                'total_length': total_length,
                'available_length': total_length - safety_margin * 0.5,
                'is_horizontal': abs(dx) > abs(dy),
                'in_long_slot': in_long_slot,
                'electrode_count': electrode_count
            }
            
            regions.append(region)
        
        return regions
    
    def _is_in_long_slot_region(self, cx, cy, dx, dy):
        """Check if electrode region is in long slot area"""
        long_half_width = self.chip_params['trap_long_width_interface'] / 2

        if abs(dx) > 0 and abs(cy) <= long_half_width * 0.9:
            return True

        if abs(dy) > 0 and abs(cy) <= long_half_width:
            return True

        return False

    def _calculate_region_total_length(self, region_key, electrode_count):
        """Calculate actual total length of region considering individual electrode parameters

        This method accounts for custom electrode widths and gaps to ensure accurate
        spatial layout when individual electrodes have different dimensions.

        Args:
            region_key: Region identifier (e.g., 'left_top_left')
            electrode_count: Number of electrodes in the region

        Returns:
            Total length in mm required for all electrodes in the region
        """
        total_length = 0.0

        # Get default parameters
        default_width = self.electrode_params.get('electrode_width', 0.060)
        default_gap = self.electrode_params.get('gap_width', 0.040)

        # Get individual electrode parameters if they exist
        individual_params = self.electrode_params.get('individual_electrode_params', {})

        # Sum up the length for each electrode
        for electrode_index in range(electrode_count):
            key = (region_key, electrode_index)

            if key in individual_params:
                # Use custom parameters for this electrode
                custom = individual_params[key]
                width = custom.get('electrode_width', default_width)
                gap = custom.get('gap_width', default_gap)
            else:
                # Use default parameters
                width = default_width
                gap = default_gap

            total_length += (width + gap)

        return total_length

    def generate_region_electrode_chain(self, region):
        """Generate electrode chain for a single region

        This method creates a chain of electrodes along a region, supporting individual
        electrode parameters. Each electrode's position is calculated cumulatively based
        on the actual widths and gaps of all preceding electrodes.

        Args:
            region: Region dictionary containing start point, direction, and electrode count

        Returns:
            List of electrode data dictionaries with positions and parameters
        """
        is_horizontal = region['is_horizontal']
        electrode_count = region['electrode_count']
        region_key = region['key']

        start_x, start_y = region['start_point']
        direction_x, direction_y = region['direction']

        # Get default parameters
        default_depth = self.electrode_params.get('electrode_depth', 0.1)
        default_width = self.electrode_params.get('electrode_width', 0.060)
        default_gap = self.electrode_params.get('gap_width', 0.040)
        default_height = self.electrode_params.get('electrode_height', 1.0)

        # Get individual electrode parameters if they exist
        individual_params = self.electrode_params.get('individual_electrode_params', {})

        region_electrodes = []
        current_position_offset = 0.0

        for electrode_index in range(electrode_count):
            # Get parameters for this specific electrode
            key = (region_key, electrode_index)

            if key in individual_params:
                # Use custom parameters for this electrode
                custom = individual_params[key]
                electrode_depth = custom.get('electrode_depth', default_depth)
                electrode_width = custom.get('electrode_width', default_width)
                gap_width = custom.get('gap_width', default_gap)
                electrode_height = custom.get('electrode_height', default_height)
            else:
                # Use default parameters
                electrode_depth = default_depth
                electrode_width = default_width
                gap_width = default_gap
                electrode_height = default_height

            # Calculate electrode center position
            electrode_center_offset = current_position_offset + electrode_width / 2

            electrode_center_x = start_x + direction_x * electrode_center_offset
            electrode_center_y = start_y + direction_y * electrode_center_offset

            electrode_data = {
                'local_id': electrode_index,
                'global_id': self.electrode_counter,
                'center': (electrode_center_x, electrode_center_y),
                'depth': electrode_depth,
                'width': electrode_width,
                'height': electrode_height,
                'is_horizontal': is_horizontal,
                'region_id': region['id'],
                'region_key': region_key,
            }

            region_electrodes.append(electrode_data)
            self.electrode_counter += 1

            # Update cumulative offset using actual electrode width and gap
            current_position_offset += (electrode_width + gap_width)

        return region_electrodes
    
    def create_region_electrode_geometry(self, electrode_data):
        """Create geometry for a single electrode in region"""
        center_x, center_y = electrode_data['center']
        electrode_depth = electrode_data['depth']          
        electrode_width = electrode_data['width']         
        is_horizontal = electrode_data['is_horizontal']
        region_key = electrode_data['region_key']
        
        long_regions = ['left_top_left', 'right_top_right', 'left_bottom_left', 'right_bottom_right']
        is_long_slot = region_key in long_regions
        
        layer_thickness = self.chip_params['layer_thickness']
        taper_depth_ratio = self.chip_params['taper_depth_ratio']
        
        if is_long_slot:
            width_surface = self.chip_params['trap_long_width_surface']
            width_interface = self.chip_params['trap_long_width_interface']
        else:
            width_surface = self.chip_params['trap_short_width_surface']
            width_interface = self.chip_params['trap_short_width_interface']
        
        electrode_height = (1 - taper_depth_ratio) * layer_thickness + (taper_depth_ratio * electrode_depth / (width_surface - width_interface)) * layer_thickness

        if is_horizontal:
            box_length_x = electrode_width
            box_width_y = electrode_depth
        else:
            box_length_x = electrode_depth
            box_width_y = electrode_width
        
        adj_positions = self.coord_system.get_layer_positions()
        layer1_end = adj_positions['layer1_end']
        layer3_start = adj_positions['layer3_start']
        
        electrode_shapes = []
        
        # Top layer electrode
        top_box = BRepPrimAPI_MakeBox(
            gp_Pnt(center_x - box_length_x/2, center_y - box_width_y/2, layer1_end - electrode_height),
            box_length_x, box_width_y, electrode_height
        )
        electrode_shapes.append(top_box.Shape())
        
        # Bottom layer electrode
        bottom_box = BRepPrimAPI_MakeBox(
            gp_Pnt(center_x - box_length_x/2, center_y - box_width_y/2, layer3_start),
            box_length_x, box_width_y, electrode_height
        )
        electrode_shapes.append(bottom_box.Shape())
        
        return electrode_shapes
    
    def create_all_electrode_geometries(self):
        """Create all electrode geometries"""
        all_electrode_shapes = []
        
        for region_key, region_data in self.electrode_regions.items():
            electrodes = region_data['electrodes']
            
            for electrode_data in electrodes:
                electrode_shapes = self.create_region_electrode_geometry(electrode_data)
                all_electrode_shapes.extend(electrode_shapes)
        
        if len(all_electrode_shapes) == 0:
            return None
        
        combined_electrodes = all_electrode_shapes[0]
        for i in range(1, len(all_electrode_shapes)):
            union_maker = BRepAlgoAPI_Fuse(combined_electrodes, all_electrode_shapes[i])
            union_maker.Build()
            if union_maker.IsDone():
                combined_electrodes = union_maker.Shape()
        
        return combined_electrodes
    
    def generate_all_electrodes(self):
        """Generate all electrode regions and electrodes"""
        intersection_points = self.calculate_interface_layer_intersection_points()
        regions = self.generate_electrode_regions(intersection_points)
        
        self.electrode_regions = {}
        
        for region in regions:
            region_electrodes = self.generate_region_electrode_chain(region)
            self.electrode_regions[region['key']] = {
                'region_info': region,
                'electrodes': region_electrodes
            }
            
            # Calculate corner points and extended points for each electrode
            for electrode_data in region_electrodes:
                corner_points = self.calculate_electrode_corner_points(electrode_data)
                self.electrode_corner_points.extend(corner_points)
                
                for corner_point in corner_points:
                    extended_point = self.calculate_extended_surface_points(corner_point)
                    self.electrode_extended_points.append(extended_point)
    
    def calculate_electrode_corner_points(self, electrode_data):
        """Calculate electrode corner points for routing"""
        center_x, center_y = electrode_data['center']
        electrode_depth = electrode_data['depth']          
        electrode_width = electrode_data['width']         
        is_horizontal = electrode_data['is_horizontal']
        region_key = electrode_data['region_key']
        
        if is_horizontal:
            box_length_x = electrode_width
            box_width_y = electrode_depth
        else:
            box_length_x = electrode_depth
            box_width_y = electrode_width
        
        corner_points = [
            (center_x - box_length_x/2, center_y - box_width_y/2),  # Lower left
            (center_x + box_length_x/2, center_y - box_width_y/2),  # Lower right
            (center_x + box_length_x/2, center_y + box_width_y/2),  # Upper right
            (center_x - box_length_x/2, center_y + box_width_y/2),  # Upper left
        ]
        
        far_corner_indices = self._get_far_corner_indices(region_key)
        far_corners = [corner_points[i] for i in far_corner_indices]
        
        # Calculate electrode height and Z coordinates
        long_regions = ['left_top_left', 'right_top_right', 'left_bottom_left', 'right_bottom_right']
        is_long_slot = region_key in long_regions
        
        layer_thickness = self.chip_params['layer_thickness']
        taper_depth_ratio = self.chip_params['taper_depth_ratio']
        
        if is_long_slot:
            width_surface = self.chip_params['trap_long_width_surface']
            width_interface = self.chip_params['trap_long_width_interface']
        else:
            width_surface = self.chip_params['trap_short_width_surface']
            width_interface = self.chip_params['trap_short_width_interface']
        
        electrode_height = (1 - taper_depth_ratio) * layer_thickness + (taper_depth_ratio * electrode_depth / (width_surface - width_interface)) * layer_thickness
        
        adj_positions = self.coord_system.get_layer_positions()
        layer1_end = adj_positions['layer1_end']
        layer3_start = adj_positions['layer3_start']
        
        top_z = layer1_end - electrode_height
        bottom_z = layer3_start + electrode_height
        
        result_points = []
        
        for corner_x, corner_y in far_corners:
            result_points.append({
                'x': corner_x,
                'y': corner_y,
                'z': top_z,
                'layer': 'top',
                'electrode_id': electrode_data['global_id'],
                'region_key': region_key
            })
            
            result_points.append({
                'x': corner_x,
                'y': corner_y,
                'z': bottom_z,
                'layer': 'bottom',
                'electrode_id': electrode_data['global_id'],
                'region_key': region_key
            })
        
        return result_points
    
    def _get_far_corner_indices(self, region_key):
        """Get far corner indices based on region"""
        corner_mapping = {
            'left_top_left': [2, 3],     # Upper right, Upper left
            'left_top_up': [0, 3],       # Lower left, Upper left
            'right_top_right': [2, 3],   # Upper right, Upper left
            'right_top_up': [1, 2],      # Lower right, Upper right
            'left_bottom_left': [0, 1],  # Lower left, Lower right
            'left_bottom_down': [0, 3],  # Lower left, Upper left
            'right_bottom_right': [0, 1], # Lower left, Lower right
            'right_bottom_down': [1, 2], # Lower right, Upper right
        }
        return corner_mapping.get(region_key, [0, 2])
    
    def calculate_extended_surface_points(self, corner_point):
        """Calculate extended surface points for routing"""
        region_key = corner_point['region_key']
        original_x = corner_point['x']
        original_y = corner_point['y']
        layer = corner_point['layer']
        
        slope_dx, slope_dy = self._get_region_slope_direction(region_key)
        
        long_regions = ['left_top_left', 'right_top_right', 'left_bottom_left', 'right_bottom_right']
        is_long_slot = region_key in long_regions
        
        if is_long_slot:
            target_surface_width = self.chip_params['trap_long_width_surface']
        else:
            target_surface_width = self.chip_params['trap_short_width_surface']
        
        target_half_width = target_surface_width / 2
        
        if is_long_slot:
            if slope_dy > 0:
                target_y = target_half_width
                distance = (target_y - original_y) / slope_dy
                new_x = original_x + slope_dx * distance
                new_y = target_y
            else:
                target_y = -target_half_width
                distance = (target_y - original_y) / slope_dy
                new_x = original_x + slope_dx * distance
                new_y = target_y
        else:
            short_offset = self.chip_params['short_slot_offset']
            if slope_dx > 0:
                target_x = short_offset + target_half_width
                distance = (target_x - original_x) / slope_dx
                new_x = target_x
                new_y = original_y + slope_dy * distance
            else:
                target_x = short_offset - target_half_width
                distance = (target_x - original_x) / slope_dx
                new_x = target_x
                new_y = original_y + slope_dy * distance
        
        adj_positions = self.coord_system.get_layer_positions()
        if layer == 'top':
            surface_z = adj_positions['layer1_start']
        else:
            surface_z = adj_positions['layer3_end']
        
        return {
            'x': new_x,
            'y': new_y,
            'z': surface_z,
            'layer': layer,
            'electrode_id': corner_point['electrode_id'],
            'region_key': region_key,
            'original_corner': (original_x, original_y, corner_point['z']),
            'slope_direction': (slope_dx, slope_dy),
            'is_long_slot': is_long_slot
        }
    
    def _get_region_slope_direction(self, region_key):
        """Get 45-degree slope direction for region"""
        sqrt2_inv = 1.0 / math.sqrt(2)
        
        direction_mapping = {
            'left_top_left': (-sqrt2_inv, sqrt2_inv),
            'left_top_up': (-sqrt2_inv, sqrt2_inv),
            'right_top_right': (sqrt2_inv, sqrt2_inv),
            'right_top_up': (sqrt2_inv, sqrt2_inv),
            'left_bottom_left': (-sqrt2_inv, -sqrt2_inv),
            'left_bottom_down': (-sqrt2_inv, -sqrt2_inv),
            'right_bottom_right': (sqrt2_inv, -sqrt2_inv),
            'right_bottom_down': (sqrt2_inv, -sqrt2_inv),
        }
        return direction_mapping.get(region_key, (0, 0))