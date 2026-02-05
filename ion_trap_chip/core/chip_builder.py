"""
Main chip builder that coordinates all components
"""
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCC.Core.gp import gp_Pnt

from config.chip_parameters import ChipParameters, ElectrodeParameters, RoutingParameters
from .coordinate_system import CoordinateSystem
from .geometry.cavities import CavityGenerator
from .geometry.electrodes import ElectrodeGenerator
from .routing.path_calculator import RoutingPathCalculator
from .routing.groove_generator import GrooveGenerator

class IonTrapChipGenerator:
    """Main ion trap chip generator"""

    def __init__(self, custom_electrode_params=None):
        """Initialize ion trap chip generator

        Args:
            custom_electrode_params: Optional dictionary to override individual electrode parameters.
                                    Format: {(region_key, electrode_index): {param_dict}}
                                    Example: {('left_top_left', 0): {'electrode_width': 0.080}}
        """
        # Initialize parameters
        chip_config = ChipParameters()
        electrode_config = ElectrodeParameters()
        routing_config = RoutingParameters()

        self.chip_params = chip_config.chip_params
        self.electrode_params = electrode_config.electrode_params
        self.electrode_region_counts = electrode_config.electrode_region_counts
        self.routing_params = routing_config.routing_params

        # Apply custom electrode parameters if provided
        if custom_electrode_params is not None:
            # Merge custom parameters with existing individual_electrode_params
            if 'individual_electrode_params' not in self.electrode_params:
                self.electrode_params['individual_electrode_params'] = {}
            self.electrode_params['individual_electrode_params'].update(custom_electrode_params)
        elif hasattr(electrode_config, 'individual_electrode_params'):
            # Use individual_electrode_params from config if no custom params provided
            self.electrode_params['individual_electrode_params'] = electrode_config.individual_electrode_params

        # Initialize coordinate system
        self.coord_system = CoordinateSystem(self.chip_params)

        # Initialize generators
        self.cavity_generator = CavityGenerator(self.coord_system, self.chip_params)
        self.electrode_generator = ElectrodeGenerator(self.coord_system, self.chip_params, {**self.electrode_params, **self.electrode_region_counts})
        self.routing_calculator = RoutingPathCalculator(self.coord_system, self.chip_params, self.routing_params)
        self.groove_generator = GrooveGenerator(self.routing_params)

        self.final_chip = None
    
    def generate_base_chip(self):
        """Generate base chip with cavities"""
        params = self.chip_params
        
        # Calculate base dimensions
        base_x = params['base_length'] / 2
        base_y = params['base_width'] / 2
        adj_positions = self.coord_system.get_layer_positions()
        layer_thick = params['layer_thickness']
        
        # Create three chip layers
        chip_layers = []
        z_positions = [
            adj_positions['layer1_start'], 
            adj_positions['layer2_start'], 
            adj_positions['layer3_start']
        ]
        
        for z_pos in z_positions:
            box_maker = BRepPrimAPI_MakeBox(
                gp_Pnt(-base_x, -base_y, z_pos),
                params['base_length'],
                params['base_width'], 
                layer_thick
            )
            chip_layers.append(box_maker.Shape())
        
        # Merge chip layers
        chip_union = chip_layers[0]
        for i in range(1, 3):
            union_maker = BRepAlgoAPI_Fuse(chip_union, chip_layers[i])
            union_maker.Build()
            chip_union = union_maker.Shape()
        
        # Create layered cavity structures
        orig_positions = self.coord_system.get_original_layer_positions()
        
        long_cavity = self.cavity_generator.create_layered_cavity_structure(
            length=params['trap_long_length'],
            width_surface=params['trap_long_width_surface'],
            width_interface=params['trap_long_width_interface'], 
            width_middle=params['trap_long_width_middle'],
            center_x=0, center_y=0,
            layer1_start=orig_positions['layer1_start'], 
            layer1_end=orig_positions['layer1_end'],
            layer2_start=orig_positions['layer2_start'], 
            layer2_end=orig_positions['layer2_end'],
            layer3_start=orig_positions['layer3_start'], 
            layer3_end=orig_positions['layer3_end'],
            is_vertical=False
        )
        
        short_cavity = self.cavity_generator.create_layered_cavity_structure(
            length=params['trap_short_length'],
            width_surface=params['trap_short_width_surface'],
            width_interface=params['trap_short_width_interface'],
            width_middle=params['trap_short_width_middle'],
            center_x=params['short_slot_offset'], center_y=0,
            layer1_start=orig_positions['layer1_start'], 
            layer1_end=orig_positions['layer1_end'],
            layer2_start=orig_positions['layer2_start'], 
            layer2_end=orig_positions['layer2_end'],
            layer3_start=orig_positions['layer3_start'], 
            layer3_end=orig_positions['layer3_end'],
            is_vertical=True
        )
        
        # Create circular holes
        circular_holes = self.cavity_generator.create_all_circular_holes()
        
        # Combine all cavities
        all_cavities = []
        
        if long_cavity:
            all_cavities.append(long_cavity)
        
        if short_cavity:
            all_cavities.append(short_cavity)
        
        if circular_holes:
            all_cavities.append(circular_holes)
        
        if len(all_cavities) == 0:
            return None
        
        # Merge all cavities
        combined_cavity = all_cavities[0]
        for i in range(1, len(all_cavities)):
            union_maker = BRepAlgoAPI_Fuse(combined_cavity, all_cavities[i])
            union_maker.Build()
            if union_maker.IsDone():
                combined_cavity = union_maker.Shape()
        
        # Cut cavities from chip
        cut_maker = BRepAlgoAPI_Cut(chip_union, combined_cavity)
        cut_maker.Build()
        
        if cut_maker.IsDone():
            self.final_chip = cut_maker.Shape()
            return self.final_chip
        else:
            return None
    
    def create_complete_ion_trap_chip(self):
        """Create complete chip with electrodes and routing grooves"""
        # Generate base chip
        base_chip = self.generate_base_chip()
        if not base_chip:
            return None
        
        # Generate all electrodes
        self.electrode_generator.generate_all_electrodes()
        
        # Calculate routing paths
        self.routing_calculator.calculate_all_turning_points(self.electrode_generator.electrode_extended_points)
        
        # Create electrode geometries
        electrode_geometries = self.electrode_generator.create_all_electrode_geometries()
        
        # Create routing grooves
        routing_grooves = self.groove_generator.create_all_routing_grooves(
            self.electrode_generator.electrode_corner_points, 
            self.electrode_generator.electrode_extended_points
        )
        
        # Create plane routing grooves
        first_plane_grooves = self.groove_generator.create_plane_routing_grooves(
            self.electrode_generator.electrode_extended_points,
            self.routing_calculator.first_turning_points
        )
        
        second_plane_grooves = self.groove_generator.create_plane_routing_grooves(
            self.routing_calculator.first_turning_points,
            self.routing_calculator.second_turning_points
        )
        
        # Cut electrodes from chip
        if electrode_geometries:
            cut_maker = BRepAlgoAPI_Cut(base_chip, electrode_geometries)
            cut_maker.Build()
            if cut_maker.IsDone():
                base_chip = cut_maker.Shape()
        
        # Cut routing grooves from chip
        for grooves in [first_plane_grooves, second_plane_grooves, routing_grooves]:
            if grooves:
                cut_maker = BRepAlgoAPI_Cut(base_chip, grooves)
                cut_maker.Build()
                if cut_maker.IsDone():
                    base_chip = cut_maker.Shape()

        self.final_chip = base_chip
        return self.final_chip
    
    def visualize_chip_with_points(self):
        """Visualize chip using utils module"""
        from utils.visualization import ChipVisualizer
        visualizer = ChipVisualizer()
        visualizer.visualize_chip(self.final_chip)
    
    def export_to_step(self, filename="ion_trap_chip.step"):
        """Export chip using utils module"""
        from utils.export import ChipExporter
        exporter = ChipExporter()
        return exporter.export_to_step(self.final_chip, filename)
