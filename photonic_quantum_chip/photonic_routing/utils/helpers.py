"""
helpers.py - Helper utility functions
Helper tools for formatting, sorting, file operations, and user interface positioning.
"""

import numpy as np
import re

def natural_sort_key(text):
    """
    Natural sort key function (similar to Windows file manager)
    
    Example: routing_2.pkl comes before routing_10.pkl
    
    Args:
        text: Text to sort
    
    Returns:
        Sort key (tuple list)
    """
    def convert(text_part):
        """Convert text to integer or lowercase text"""
        if text_part.isdigit():
            return int(text_part)
        else:
            return text_part.lower()
    
    # Split into numeric and non-numeric parts
    parts = re.split(r'(\d+)', text)
    return [convert(part) for part in parts if part]


def extract_region_number(filename):
    """
    Extract region number from filename
    
    Supports formats: routing_20.pkl, region20.pkl, task_3_backup.pkl, etc.
    
    Args:
        filename: Filename
    
    Returns:
        Region number (integer) or None
    """
    patterns = [
        r'routing[_\s-]*(\d+)',
        r'region[_\s-]*(\d+)',
        r'task[_\s-]*(\d+)',
        r'area[_\s-]*(\d+)',
        r'[_\s-](\d+)[_\s-]',
        r'^(\d+)',
        r'(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return None


def format_file_size(size_bytes):
    """
    Format file size (similar to Windows display)
    
    Args:
        size_bytes: Number of bytes
    
    Returns:
        Formatted string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_time(seconds):
    """Format seconds into readable string"""
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes} min {secs:.2f} sec"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours} hr {minutes} min {secs:.2f} sec"


def find_backup_point_index(point, backup_list):
    """Find the index of a point in the backup point list"""
    pt_tuple = tuple(point) if not isinstance(point, tuple) else point
    for i, backup_pt in enumerate(backup_list):
        backup_tuple = tuple(backup_pt) if not isinstance(backup_pt, tuple) else backup_pt
        if pt_tuple == backup_tuple:
            return str(i + 1)
    return "Unknown"


def determine_boundary_for_points(points, backups_grouped):
    """Determine the main boundary that a set of points belongs to"""
    boundary_counts = {'Top': 0, 'Bottom': 0, 'Left': 0, 'Right': 0}
    
    for pt in points:
        pt_tuple = tuple(pt) if not isinstance(pt, tuple) else pt
        for boundary, pts_list in backups_grouped.items():
            for backup_pt in pts_list:
                backup_tuple = tuple(backup_pt) if not isinstance(backup_pt, tuple) else backup_pt
                if pt_tuple == backup_tuple:
                    boundary_counts[boundary] += 1
                    break
    
    max_boundary = max(boundary_counts, key=boundary_counts.get)
    if boundary_counts[max_boundary] > 0:
        return max_boundary
    return None


def center_window_right(window, root, offset_x=100):
    """Position window to center-right of main window"""
    window.update_idletasks()
    window.after(10, lambda: _do_center(window, root, offset_x))


def _do_center(window, root, offset_x):
    """Execute window centering positioning"""
    try:
        # Get main window info
        root_x = root.winfo_x()
        root_y = root.winfo_y()
        root_width = root.winfo_width()
        root_height = root.winfo_height()
        
        # Get popup window size
        window_width = window.winfo_width()
        window_height = window.winfo_height()
        
        if window_width <= 1:
            window_width = window.winfo_reqwidth()
        if window_height <= 1:
            window_height = window.winfo_reqheight()
        
        # Calculate position
        x = root_x + (root_width - window_width) // 2 + offset_x
        y = root_y + (root_height - window_height) // 2
        
        # Ensure not off screen
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        if x + window_width > screen_width:
            x = screen_width - window_width - 20
        if y + window_height > screen_height:
            y = screen_height - window_height - 20
        if x < 0:
            x = 20
        if y < 0:
            y = 20
        
        window.geometry(f"+{x}+{y}")
    except Exception as e:
        print(f"Window positioning failed: {e}")
