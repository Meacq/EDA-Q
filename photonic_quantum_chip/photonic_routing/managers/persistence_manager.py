"""
persistence_manager.py - Persistence manager
Persistence manager for saving and loading routing data in pickle format.
Integrated with unified path management system.
"""

import pickle
import os
from datetime import datetime
from pathlib import Path


def _merge_collinear_points(path):
    """Merge collinear points in path, keep only corner points"""
    if len(path) < 3:
        return path

    merged = [path[0]]

    for i in range(1, len(path) - 1):
        prev = merged[-1]
        curr = path[i]
        next_p = path[i + 1]

        # Calculate direction
        dx1 = curr[0] - prev[0]
        dy1 = curr[1] - prev[1]
        dx2 = next_p[0] - curr[0]
        dy2 = next_p[1] - curr[1]

        # Check if same direction (horizontal or vertical)
        same_direction = (dx1 == 0 and dx2 == 0) or (dy1 == 0 and dy2 == 0)

        if not same_direction:
            merged.append(curr)

    merged.append(path[-1])
    return merged


class PersistenceManager:
    """Persistence manager - Improved version (maintains interface compatibility)"""
    
    def __init__(self):
        # Delay import to avoid circular dependency
        from ..config.paths import (
            ensure_directories, 
            get_routing_file,
            ROUTING_DIR
        )
        
        self.get_routing_file = get_routing_file
        self.routing_dir = ROUTING_DIR
        
        # Ensure directories exist
        ensure_directories()

    def save_to_file(self, task_count, router, all_finished_paths, snapshots, filename=None, total_connected_centers=0):
        """
        Save to file

        Args:
            task_count: Task number
            router: Router object
            all_finished_paths: All completed paths
            snapshots: Snapshot list
            filename: Filename (optional, defaults to routing_{task_count}.pkl)
            total_connected_centers: Total number of connected center points
        """
        # If no filename specified, use default naming
        if filename is None:
            filepath = self.get_routing_file(task_count)
        else:
            # Support relative and absolute paths
            filepath = Path(filename)
            if not filepath.is_absolute():
                filepath = self.routing_dir / filename

        # Merge collinear points, keep only corner points
        simplified_paths = [_merge_collinear_points(path) for path in all_finished_paths]

        data = {
            'task_count': task_count,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'router_state': {
                'occupation_grid': router.occupation_grid,
                'diagonal_bitmap': router.diagonal_bitmap,
                'global_reserved_points': router.global_reserved_points,
                'h': router.h,
                'w': router.w
            },
            'all_finished_paths': simplified_paths,
            'snapshots': snapshots,
            'total_connected_centers': total_connected_centers
        }

        try:
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            file_size_kb = filepath.stat().st_size / 1024
            print(f"[Save Successful] {filepath.name}")
            print(f"[File Size] {file_size_kb:.2f} KB")
            print(f"[Save Path] {filepath}")
            
            return True
        except Exception as e:
            print(f"Save failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load_from_file(self, filename=None):
        """
        Load from file - compatible with old format
        
        Args:
            filename: Filename (optional)
                - None: Load latest file
                - Integer: Load routing_{integer}.pkl
                - String: Load specified file
        """
        # Determine file path
        if filename is None:
            # Load latest file
            filepath = self._get_latest_file()
            if filepath is None:
                print("[Error] No routing files found")
                return None
        elif isinstance(filename, int):
            # Load by task number
            filepath = self.get_routing_file(filename)
        else:
            # Specified filename
            filepath = Path(filename)
            if not filepath.is_absolute():
                filepath = self.routing_dir / filename
        
        print(f"\n[PersistenceManager] Attempting to load file: {filepath.name}")
        print(f"[Full path] {filepath}")
        
        if not filepath.exists():
            print(f"[Error] File does not exist: {filepath}")
            return None

        try:
            file_size = filepath.stat().st_size
            print(f"[Info] File size: {file_size / 1024:.2f} KB")
            
            if file_size == 0:
                print("[Error] File is empty")
                return None
            
            # Ensure Pickle compatibility
            self._ensure_pickle_compatibility()
            
            print("[Info] Reading file...")
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            print("[Info] Pickle deserialization successful")
            
            if not isinstance(data, dict):
                print(f"[Error] Data type error: {type(data)}")
                return None
            
            print(f"[Info] Data contains keys: {list(data.keys())}")
            
            # Verify required fields
            required_keys = ['task_count', 'router_state', 'all_finished_paths']
            for key in required_keys:
                if key not in data:
                    print(f"[Error] Missing required field: '{key}'")
                    return None
            
            # Print statistics
            router_state = data['router_state']
            paths_count = len(data['all_finished_paths'])
            print(f"[Info] Task number: {data['task_count']}")
            print(f"[Info] Contains {paths_count} paths")
            
            if 'snapshots' in data:
                print(f"[Info] Contains {len(data['snapshots'])} snapshots")
            
            if 'timestamp' in data:
                print(f"[Info] Save time: {data['timestamp']}")
            
            print(f"[Success] File loaded successfully\n")
            return data
            
        except Exception as e:
            print(f"[Error] Loading failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_latest_file(self):
        """Get latest routing file"""
        if not self.routing_dir.exists():
            return None
        
        pkl_files = list(self.routing_dir.glob("*.pkl"))
        if not pkl_files:
            return None
        
        # Sort by modification time
        pkl_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return pkl_files[0]
    
    def _ensure_pickle_compatibility(self):
        """Ensure Pickle compatibility"""
        import __main__
        from ..core.data_structures import DiagonalBitmap

        if not hasattr(__main__, 'DiagonalBitmap'):
            __main__.DiagonalBitmap = DiagonalBitmap
            print("[Compatibility] Registered DiagonalBitmap to __main__")

    def list_available_files(self, directory=None):
        """
        List available files - natural sort (compatible with old interface)
        
        Args:
            directory: Directory path (optional, maintained for compatibility but ignored)
        
        Returns:
            Filename list (string list, maintained for compatibility)
        """
        from ..utils.helpers import natural_sort_key
        
        try:
            if not self.routing_dir.exists():
                return []
            
            # Find all .pkl files
            pkl_files = list(self.routing_dir.glob("*.pkl"))
            
            if not pkl_files:
                return []
            
            # Extract filenames
            filenames = [f.name for f in pkl_files]
            
            # Use natural sort
            filenames.sort(key=natural_sort_key, reverse=True)
            
            return filenames
            
        except Exception as e:
            print(f"Failed to list files: {e}")
            return []
    
    def get_file_info(self, filename):
        """
        Get file detailed information (new method)
        
        Args:
            filename: Filename
        
        Returns:
            Dictionary containing name, path, size, mtime
        """
        try:
            filepath = self.routing_dir / filename
            if not filepath.exists():
                return None
            
            stat = filepath.stat()
            return {
                'name': filepath.name,
                'path': filepath,
                'size': stat.st_size,
                'mtime': stat.st_mtime,
            }
        except Exception as e:
            print(f"Failed to get file info: {e}")
            return None
    
    def list_files_with_info(self):
        """
        List files with detailed information (new method)
        
        Returns:
            List of dictionaries, each containing name, path, size, mtime
        """
        from ..utils.helpers import natural_sort_key
        
        try:
            if not self.routing_dir.exists():
                return []
            
            # Find all .pkl files
            pkl_files = list(self.routing_dir.glob("*.pkl"))
            
            if not pkl_files:
                return []
            
            # Prepare file information
            file_info = []
            for filepath in pkl_files:
                stat = filepath.stat()
                file_info.append({
                    'name': filepath.name,
                    'path': filepath,
                    'size': stat.st_size,
                    'mtime': stat.st_mtime,
                })
            
            # Use natural sort
            file_info.sort(key=lambda x: natural_sort_key(x['name']), reverse=True)
            
            return file_info
            
        except Exception as e:
            print(f"Failed to list files: {e}")
            return []
    
    def delete_file(self, filename):
        """
        Delete specified file
        
        Args:
            filename: Filename
        
        Returns:
            bool: Whether successful
        """
        try:
            filepath = self.routing_dir / filename
            if filepath.exists():
                filepath.unlink()
                print(f"[Delete Success] {filename}")
                return True
            else:
                print(f"[Error] File does not exist: {filename}")
                return False
        except Exception as e:
            print(f"[Error] Delete failed: {e}")
            return False