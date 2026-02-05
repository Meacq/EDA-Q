"""
Chip parameter configurations
"""

class ChipParameters:
    """Base chip parameters configuration"""
    
    def __init__(self):
        self.chip_params = {
            'base_length': 20.0,      # mm Base plate length
            'base_width': 15.0,       # mm Base plate width
            'layer_thickness': 0.5,   # mm Thickness of each layer
            'layer_spacing': 0.0,     # mm Spacing between layers
            
            # Ion trap hollow area parameters
            'trap_long_length': 8.0,   # mm Long slot length
            'trap_short_length': 4.0,  # mm Short slot length
            
            # Long slot widths (decreasing from outside to inside)
            'trap_long_width_surface': 1.6,      # mm Surface long slot width
            'trap_long_width_interface': 0.6,    # mm Long slot width near middle layer
            'trap_long_width_middle': 0.6,       # mm Middle layer long slot width
            
            # Short slot widths (decreasing from outside to inside)
            'trap_short_width_surface': 1.6,     # mm Surface short slot width
            'trap_short_width_interface': 0.6,   # mm Short slot width near middle layer
            'trap_short_width_middle': 0.4,      # mm Middle layer short slot width
            
            # Short slot offset
            'short_slot_offset': 1.0,  # mm Offset of short slot along long slot direction
            
            # Taper cutting control parameters
            'taper_depth_ratio': 0.8,           # Ratio of upper and lower layer taper depth to layer thickness
            'middle_taper_depth_ratio': 0.05,   # Ratio of middle layer taper depth to layer thickness
            
            # Circular hollow area parameters
            'circular_holes': {
                'enabled': True,                 # Whether to enable circular hollowing
                'radius': 1.0,                   # mm Radius of circular hollow
                'positions': [
                    (-6.0, -5.0),               # Lower left position (x, y)
                    (6.0, 5.0)                  # Upper right position (x, y)
                ],
                'through_all_layers': True,      # Whether to penetrate all layers
            }
        }

class ElectrodeParameters:
    """Electrode configuration parameters"""
    
    def __init__(self):
        self.electrode_params = {
            # Basic electrode specifications
            'electrode_depth': 0.1,              # mm Electrode depth
            'electrode_width': 0.060,            # mm Electrode width (protruding part)
            'gap_width': 0.040,                  # mm Gap width (recessed part)
            'electrode_height': 1.0,             # mm Electrode height (Z-direction extension)
            'cross_safety_margin': 0.06,         # mm Starting segment length of cross area
        }
        
        # Electrode count configuration for 8 regions (extending from 4 intersections in 8 directions)
        self.electrode_region_counts = {
            'left_top_left': 8,      # Upper left intersection - left direction
            'left_top_up': 8,        # Upper left intersection - up direction
            'right_top_right': 8,    # Upper right intersection - right direction
            'right_top_up': 8,       # Upper right intersection - up direction
            'left_bottom_left': 8,   # Lower left intersection - left direction
            'left_bottom_down': 8,   # Lower left intersection - down direction
            'right_bottom_right': 8, # Lower right intersection - right direction
            'right_bottom_down': 8,  # Lower right intersection - down direction
        }

        # Individual electrode parameters - override default parameters for specific electrodes
        # Key format: (region_key, electrode_index)
        # Value: dictionary of parameters to override (electrode_depth, electrode_width, gap_width, electrode_height)
        # Example:
        #   ('left_top_left', 0): {'electrode_width': 0.080, 'gap_width': 0.045}
        # This allows customizing individual electrodes while maintaining spatial consistency
        self.individual_electrode_params = {
            # Add custom electrode parameters here
            # Example: ('left_top_left', 0): {'electrode_width': 0.080},
        }

class RoutingParameters:
    """Routing groove parameters"""
    
    def __init__(self):
        self.routing_params = {
            'chamfer_offset': 0.01,              # mm Chamfer translation distance
            
            # X-coordinate configuration of first plane inflection point - offset relative to short slot center line
            'left_turning_offset': 2.0,         # mm Offset distance of first plane inflection point in left area to the left of short slot center line
            'right_turning_offset': 2.0,        # mm Offset distance of first plane inflection point in right area to the right of short slot center line
        }