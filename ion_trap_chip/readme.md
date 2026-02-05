# Ion Trap Chip Design System

Ion trap chip design code for generating three-dimensional ion trap chip geometry.

## Directory Structure

```
ion_trap_chip/
├── config/                    # Configuration and parameters
│   └── chip_parameters.py     # All parameter definitions
├── core/                      # Core functionality
│   ├── chip_builder.py        # Main builder
│   ├── coordinate_system.py   # Coordinate system management
│   ├── geometry/              # 3D geometry generation
│   │   ├── base_shapes.py     # Basic geometric shapes
│   │   ├── cavities.py        # Ion trap cavities
│   │   └── electrodes.py      # Electrode structures
│   └── routing/               # Routing path calculation
│       ├── path_calculator.py # Path planning
│       └── groove_generator.py # Groove geometry
└── utils/                     # Utility functions
    ├── visualization.py       # 3D visualization
    └── export.py              # Export functionality
```

## Quick Start

### Basic Usage

```python
from ion_trap_chip.core.chip_builder import IonTrapChipGenerator

# Create chip generator
chip_gen = IonTrapChipGenerator()

# Generate complete ion trap chip
chip = chip_gen.create_complete_ion_trap_chip()

# Visualize
chip_gen.visualize_chip_with_points()

# Export to STEP file
chip_gen.export_to_step("my_ion_trap_chip.step")
```

## Parameter Configuration

### Chip Base Parameters

The `ChipParameters` class in `config/chip_parameters.py` defines the basic chip dimensions:

```python
chip_params = {
    'base_length': 20.0,      # mm Base plate length
    'base_width': 15.0,       # mm Base plate width
    'layer_thickness': 0.5,   # mm Layer thickness
    'trap_long_length': 8.0,  # mm Long slot length
    'trap_short_length': 4.0, # mm Short slot length
    # ... more parameters
}
```

### Electrode Parameter Configuration

#### Default Electrode Parameters

Default parameters for all electrodes are defined in the `ElectrodeParameters` class:

```python
electrode_params = {
    'electrode_depth': 0.1,      # mm Electrode depth
    'electrode_width': 0.060,    # mm Electrode width
    'gap_width': 0.040,          # mm Gap width
    'electrode_height': 1.0,     # mm Electrode height
    'cross_safety_margin': 0.06, # mm Cross area starting segment length
}
```

#### Electrode Region Configuration

The chip has 8 electrode regions extending from 4 intersection points in 8 directions:

```python
electrode_region_counts = {
    'left_top_left': 8,      # Upper left intersection - left direction
    'left_top_up': 8,        # Upper left intersection - up direction
    'right_top_right': 8,    # Upper right intersection - right direction
    'right_top_up': 8,       # Upper right intersection - up direction
    'left_bottom_left': 8,   # Lower left intersection - left direction
    'left_bottom_down': 8,   # Lower left intersection - down direction
    'right_bottom_right': 8, # Lower right intersection - right direction
    'right_bottom_down': 8,  # Lower right intersection - down direction
}
```

## Individual Electrode Parameter Customization

### Feature Overview

The system supports setting parameters for each electrode individually while automatically maintaining spatial consistency between electrodes. When modifying an electrode's parameters, the system will:

1. **Automatically adjust subsequent electrode positions**: Since electrode positions are calculated cumulatively, modifying the width or gap of earlier electrodes will automatically adjust the positions of all subsequent electrodes
2. **Dynamically calculate region total length**: The system calculates the true total length of a region based on the actual parameters of all electrodes
3. **Maintain geometric consistency**: Ensures the electrode chain geometry is correct without overlaps or incorrect gaps

### Position Relationship

Electrode positions within the same region are calculated **cumulatively**:

```
Electrode 0 center position = start + direction × (w_0/2)
Electrode 1 center position = start + direction × (w_0 + g_0 + w_1/2)
Electrode 2 center position = start + direction × (w_0 + g_0 + w_1 + g_1 + w_2/2)
Electrode 3 center position = start + direction × (w_0 + g_0 + w_1 + g_1 + w_2 + g_2 + w_3/2)
```

Where:
- `w_i` = width of electrode i
- `g_i` = gap width after electrode i
- `start` = region start point
- `direction` = region direction vector

**Key constraint**: Modifying the width or gap of electrode i will cause all electrodes i+1, i+2... through the last electrode to shift positions.

### Usage Methods

#### Method 1: Direct Configuration File Modification

Edit the `individual_electrode_params` dictionary in `config/chip_parameters.py`:

```python
class ElectrodeParameters:
    def __init__(self):
        # ... default parameters ...

        # Individual electrode parameters
        self.individual_electrode_params = {
            # Format: (region_key, electrode_index): {parameter_dict}

            # Example 1: Set electrode 0 in left_top_left region
            ('left_top_left', 0): {
                'electrode_width': 0.080,    # Custom width
                'gap_width': 0.045,          # Custom gap
                'electrode_depth': 0.15,     # Custom depth
            },

            # Example 2: Only modify width of electrode 1
            ('left_top_left', 1): {
                'electrode_width': 0.070,
            },

            # Example 3: Set electrode 3 in right_top_right region
            ('right_top_right', 3): {
                'electrode_width': 0.075,
                'gap_width': 0.050,
            },
        }
```

#### Method 2: Programmatic Configuration

Set individual parameters dynamically in code:

```python
from config.chip_parameters import ElectrodeParameters
from core.chip_builder import IonTrapChipGenerator

# Create electrode parameter configuration
electrode_config = ElectrodeParameters()

# Set parameters for specific electrodes
electrode_config.individual_electrode_params = {
    ('left_top_left', 0): {
        'electrode_width': 0.080,
        'gap_width': 0.045,
    },
    ('left_top_left', 2): {
        'electrode_width': 0.070,
    },
}

# Note: Parameters must be set before creating IonTrapChipGenerator
# Or modify the configuration file and re-import
```

### Configurable Parameters

Each electrode can individually set the following parameters:

| Parameter | Description | Default | Unit |
|-----------|-------------|---------|------|
| `electrode_depth` | Electrode depth (recess depth) | 0.1 | mm |
| `electrode_width` | Electrode width (protruding part) | 0.060 | mm |
| `gap_width` | Gap width (recessed part) | 0.040 | mm |
| `electrode_height` | Electrode height (Z-direction extension) | 1.0 | mm |

**Notes**:
- Only set the parameters you want to modify; unset parameters will use default values
- Modifying `electrode_width` and `gap_width` affects subsequent electrode positions
- `electrode_depth` and `electrode_height` only affect the electrode's own geometry

### Practical Application Examples

#### Example 1: Create Gradient Width Electrode Chain

```python
# Set in chip_parameters.py
self.individual_electrode_params = {
    ('left_top_left', 0): {'electrode_width': 0.080},
    ('left_top_left', 1): {'electrode_width': 0.075},
    ('left_top_left', 2): {'electrode_width': 0.070},
    ('left_top_left', 3): {'electrode_width': 0.065},
    ('left_top_left', 4): {'electrode_width': 0.060},
    # Subsequent electrodes use default value 0.060
}
```

#### Example 2: Special Function Electrode

```python
# Set electrode 0 as a wider loading electrode
self.individual_electrode_params = {
    ('left_top_left', 0): {
        'electrode_width': 0.100,
        'gap_width': 0.060,
        'electrode_depth': 0.15,
    },
}
```

#### Example 3: Symmetric Configuration Across Multiple Regions

```python
# Set same parameters at same positions in multiple regions
regions = ['left_top_left', 'right_top_right', 'left_bottom_left', 'right_bottom_right']
self.individual_electrode_params = {}

for region in regions:
    self.individual_electrode_params[(region, 0)] = {
        'electrode_width': 0.080,
        'gap_width': 0.045,
    }
```

### Impact Analysis

Impact of modifying electrode parameters:

```
Original configuration (all electrodes identical):
w = 0.060, g = 0.040
Electrode 0 center: 0.030
Electrode 1 center: 0.130
Electrode 2 center: 0.230
Region total length: 0.800 mm (8 electrodes)

After modifying electrode 0:
w_0 = 0.080, g_0 = 0.040
Electrode 0 center: 0.040  (shifted backward 0.010)
Electrode 1 center: 0.150  (shifted backward 0.020)
Electrode 2 center: 0.250  (shifted backward 0.020)
Region total length: 0.820 mm (increased by 0.020)
```

### Technical Implementation

The system ensures spatial consistency through the following mechanisms:

1. **Dynamic length calculation** (`_calculate_region_total_length` method):
   - When generating electrode regions, iterate through all electrodes
   - Accumulate the actual width and gap of each electrode
   - Calculate the true total length of the region

2. **Cumulative position calculation** (`generate_region_electrode_chain` method):
   - Start from the starting point and place electrodes one by one
   - Each electrode's position = cumulative length of all preceding electrodes + half its own width
   - Update cumulative offset using actual parameters

3. **Parameter lookup priority**:
   - First look up `individual_electrode_params[(region_key, electrode_index)]`
   - If exists, use individual parameters
   - If not exists, use default parameters

### Important Notes

1. **Spatial constraints**: Ensure modified electrode chains don't exceed chip boundaries
2. **Symmetry**: If symmetric design is needed, remember to set same parameters in corresponding regions
3. **Testing and validation**: After modifying parameters, visualize first to ensure correct geometry
4. **Recommended parameter ranges**:
   - Electrode width: 0.040 - 0.120 mm
   - Gap width: 0.030 - 0.080 mm
   - Electrode depth: 0.05 - 0.20 mm
5. **Cascade effect**: Modifying earlier electrodes affects all subsequent electrode positions; adjust carefully

## Export and Visualization

### Export STEP File

```python
chip_gen.export_to_step("output_filename.step")
```

### 3D Visualization

```python
chip_gen.visualize_chip_with_points()
```

## Technical Details

### Coordinate System

- Origin at chip center
- X-axis: Horizontal direction
- Y-axis: Vertical direction
- Z-axis: Height direction (positive upward)

### Layer Structure

The chip consists of three layers:
- Layer 1 (Top): Contains top surface electrodes
- Layer 2 (Middle): Ion trap cavity
- Layer 3 (Bottom): Contains bottom surface electrodes

### Electrode Region Identifiers

Key names for the 8 electrode regions:

| Region Key | Description | Direction |
|-----------|-------------|-----------|
| `left_top_left` | Upper left intersection | Left (-X) |
| `left_top_up` | Upper left intersection | Up (+Y) |
| `right_top_right` | Upper right intersection | Right (+X) |
| `right_top_up` | Upper right intersection | Up (+Y) |
| `left_bottom_left` | Lower left intersection | Left (-X) |
| `left_bottom_down` | Lower left intersection | Down (-Y) |
| `right_bottom_right` | Lower right intersection | Right (+X) |
| `right_bottom_down` | Lower right intersection | Down (-Y) |

Electrode indices in each region start from 0.

## Dependencies

- PythonOCC: For 3D geometric modeling
- NumPy: Numerical computation
- Other standard Python libraries

## Changelog

### v1.1 - Individual Electrode Parameter Support
- Added `individual_electrode_params` configuration option
- Implemented dynamic region length calculation
- Support for setting individual electrode parameters
- Automatic maintenance of spatial consistency for electrode positions

## License

[Add license information]

## Contributing

[Add contribution guidelines]

## Contact

[Add contact information]
