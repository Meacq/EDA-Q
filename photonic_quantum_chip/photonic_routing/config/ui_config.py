"""
ui_config.py - UI configuration
User interface configuration including color schemes, canvas settings, and size parameters.
Defines the light blue professional theme for the application.
"""

# UI theme color scheme - Light blue white theme
UI_COLORS = {
    'primary': '#4A90E2',
    'primary_light': '#E8F4FD',
    'primary_dark': '#2E5C8A',
    'secondary': '#7CB342',
    'accent': '#FFA726',
    'bg_main': '#F5F9FC',
    'bg_panel': '#FFFFFF',
    'text_primary': '#2C3E50',
    'text_secondary': '#546E7A',
    'text_light': '#90A4AE',
    'border': '#CFD8DC',
    'success': '#66BB6A',
    'warning': '#FFA726',
    'error': '#EF5350',
    'grid': '#ECEFF1',
}

# Canvas point and line color scheme
CANVAS_COLORS = {
    # Basic point colors
    'out_point': 'blue',
    'center_point': 'green',
    'obstacle': 'red',
    'chip_range': 'purple',
    
    # Current region point colors
    'current_out': 'blue',
    
    # Backup point colors
    'center_backup': 'orange',
    'center_backup_edge': 'orange',
    'center_backup_text': 'darkblue',
    
    'out_backup': 'purple',
    'out_backup_edge': 'purple',
    'out_backup_text': 'darkred',
    
    # Path colors
    'current_path': 'red',
    'finished_path': 'gray',
    
    # Region and selection
    'region_border': 'lime',
    'available_point': 'lime',
    'available_point_edge': 'black',
    'selected_point': 'cyan',
    'selected_point_edge': 'red',
    'bounding_box': 'orange',
    'rect_selector_face': 'yellow',
    'rect_selector_edge': 'red',
    
    # Grid and background
    'grid_line': 'gray',
    'background': 'white',
    
    # Text annotation
    'text_box_face': 'white',
}

# Canvas point and line size configuration
CANVAS_SIZES = {
    # Point sizes
    'base_point': 25,
    'current_out': 60,
    'backup_point': 80,
    'available_point': 100,
    'selected_point': 150,
    'background_point': 18,
    
    # Text annotation
    'text_fontsize': 9,
    'text_offset': 1.8,
    'text_padding': 0.4,
    
    # Line widths
    'current_path_width': 2.8,
    'history_path_width': 1.2,
    'border_width': 3.5,
    'point_edge_width': 2.0,
    'grid_line_width': 1.0,
    
    # Transparency configuration
    'base_point_alpha': 0.4,
    'background_point_alpha': 0.1,
    'current_path_alpha': 0.8,
    'history_path_alpha': 0.3,
    'grid_line_alpha': 0.1,
    'text_box_alpha': 0.85,
    'rect_selector_alpha': 0.3,
}

# Legend configuration
LEGEND_CONFIG = {
    'fontsize': 10,           # Font size (reduced for better fit with long English labels)
    'framealpha': 0.7,       # Background transparency (more transparent to reduce occlusion)
    'loc': 'upper center',   # Position: upper center anchor point
    'bbox_to_anchor': (0.5, -0.15),  # Place below the chart outside
    'ncol': 5,               # 5 columns horizontal arrangement (more compact)
    'fancybox': False,       # Disable rounded corners (reduce space usage)
    'shadow': False,         # No shadow
    'edgecolor': None,       # Border color
    'facecolor': 'white',    # Background color
    'borderpad': 0.3,        # Legend inner padding
    'labelspacing': 0.8,     # Label spacing (line spacing, in font size units)
    'handlelength': 0.8,     # Legend marker length (reduced to save space)
    'handletextpad': 0.3,    # Marker to text spacing (reduced to save space)
    'columnspacing': 1.5,    # Column spacing (reduced for more compact layout)
    'markerscale': 1.2,      # Marker size ratio
}
