"""
path_smoother.py - Orthogonal routing path smoothing algorithm module
Based on industry-standard orthogonal routing optimization strategies.

Algorithm strategies:
1. Segment Merging - Merge continuous collinear segments
2. Dogleg Removal - Eliminate redundant backtracking like HVHV
3. Manhattan Shortcutting - Local shortest path replacement
"""

import numpy as np
from typing import List, Tuple, Set
import math


class PathSmoother:
    """
    Orthogonal routing path smoother
    
    Implements industry-standard path optimization strategies:
    - Collinear segment merging
    - Redundant corner elimination
    - Manhattan shortcutting
    """
    
    def __init__(self, grid_size=15, min_spacing=15):
        """
        Initialize path smoother
        
        Args:
            grid_size: Grid size
            min_spacing: Minimum spacing requirement
        """
        self.grid_size = grid_size
        self.min_spacing = min_spacing
        
        # Safe distance (leave some margin)
        self.safe_distance = min_spacing * 0.9
    
    def smooth_paths(self, paths: List[List[Tuple[int, int]]], 
                     all_paths: List[List[Tuple[int, int]]] = None) -> List[List[Tuple[float, float]]]:
        """
        Smooth multiple paths
        
        Args:
            paths: List of paths to smooth
            all_paths: All paths (for collision detection), if None use paths
        
        Returns:
            List of smoothed paths
        """
        if all_paths is None:
            all_paths = paths
        
        smoothed_paths = []
        
        for path_idx, path in enumerate(paths):
            if len(path) < 3:
                # Path too short, no smoothing needed
                smoothed_paths.append([(float(p[0]), float(p[1])) for p in path])
                continue
            
            # Get segments from other paths (exclude current path)
            other_segments = []
            for other_idx, other_path in enumerate(all_paths):
                if other_idx != path_idx:
                    segments = self._path_to_segments(other_path)
                    other_segments.extend(segments)
            
            # Apply multi-stage smoothing
            smoothed_path = self._multi_stage_smooth(path, other_segments)
            
            smoothed_paths.append(smoothed_path)
        
        return smoothed_paths
    
    def _multi_stage_smooth(self, path: List[Tuple[int, int]], 
                           other_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]]) -> List[Tuple[float, float]]:
        """
        Multi-stage smoothing algorithm
        
        Stage 1: Collinear segment merging
        Stage 2: Dogleg removal (HVHV -> HV)
        Stage 3: Manhattan shortcutting (local shortest path replacement)
        """
        # Stage 1: Collinear segment merging
        path = self._merge_collinear_segments(path)
        
        # Stage 2: Dogleg removal (iterate multiple times)
        for _ in range(3):  # Max 3 iterations
            new_path = self._remove_doglegs(path, other_segments)
            if len(new_path) == len(path):
                break  # No improvement, stop iteration
            path = new_path
        
        # Stage 3: Manhattan shortcutting (iterate multiple times)
        for _ in range(5):  # Max 5 iterations
            new_path = self._manhattan_shortcut(path, other_segments)
            if len(new_path) == len(path):
                break  # No improvement, stop iteration
            path = new_path
        
        # Convert to float
        return [(float(p[0]), float(p[1])) for p in path]
    
    def _merge_collinear_segments(self, path: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Stage 1: Collinear segment merging
        
        Merge continuous same-direction segments, eliminate fragmentation caused by grid
        """
        if len(path) < 3:
            return path
        
        merged = [path[0]]
        
        for i in range(1, len(path) - 1):
            prev = merged[-1]
            curr = path[i]
            next_p = path[i + 1]
            
            # Calculate direction
            dir1 = self._get_direction(prev, curr)
            dir2 = self._get_direction(curr, next_p)
            
            # If direction same, skip current point (merge)
            if dir1 == dir2:
                continue
            
            merged.append(curr)
        
        merged.append(path[-1])
        return merged
    
    def _remove_doglegs(self, path: List[Tuple[int, int]], 
                       other_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]]) -> List[Tuple[int, int]]:
        """
        Stage 2: Dogleg Removal
        
        Identify and eliminate redundant backtracking patterns, e.g.:
        - HVHV -> HV (horizontal-vertical-horizontal-vertical -> horizontal-vertical)
        - Small zigzag backtracking
        """
        if len(path) < 4:
            return path
        
        improved = True
        result = list(path)
        
        while improved:
            improved = False
            new_result = [result[0]]
            
            i = 0
            while i < len(result) - 1:
                # Try to skip intermediate backtracking points
                best_skip = 0
                
                # Try skipping 1 to 3 intermediate points
                for skip in range(1, min(4, len(result) - i)):
                    if i + skip >= len(result):
                        break
                    
                    start = result[i]
                    end = result[i + skip]
                    
                    # Check if can connect directly (Manhattan distance)
                    if self._can_manhattan_connect(start, end, other_segments):
                        best_skip = skip
                
                if best_skip > 0:
                    # Found points to skip
                    improved = True
                    i += best_skip
                    if i < len(result):
                        new_result.append(result[i])
                else:
                    # Cannot skip, add next point
                    i += 1
                    if i < len(result):
                        new_result.append(result[i])
            
            result = new_result
        
        return result
    
    def _manhattan_shortcut(self, path: List[Tuple[int, int]], 
                           other_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]]) -> List[Tuple[int, int]]:
        """
        Stage 3: Manhattan Shortcutting
        
        For any two points on the path, try to replace intermediate bend segments with Manhattan shortest path
        """
        if len(path) < 3:
            return path
        
        result = [path[0]]
        i = 0
        
        while i < len(path) - 1:
            # Try to jump from current point to farther point
            best_target = i + 1
            
            # Search forward for farthest reachable point
            for j in range(i + 2, min(i + 10, len(path))):
                if self._can_manhattan_connect(path[i], path[j], other_segments):
                    best_target = j
            
            if best_target > i + 1:
                # Found shortcut, insert Manhattan path
                shortcut = self._create_manhattan_path(path[i], path[best_target])
                # Skip start point (already in result)
                for p in shortcut[1:]:
                    if len(result) == 0 or result[-1] != p:
                        result.append(p)
                i = best_target
            else:
                # No shortcut, add next point
                i += 1
                if i < len(path) and (len(result) == 0 or result[-1] != path[i]):
                    result.append(path[i])
        
        # Ensure endpoint is added
        if result[-1] != path[-1]:
            result.append(path[-1])
        
        return result
    
    def _can_manhattan_connect(self, p1: Tuple[int, int], p2: Tuple[int, int],
                              other_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]]) -> bool:
        """
        Check if two points can be connected via Manhattan path (no conflict with other paths)

        Returns:
            True if at least one way can connect
        """
        # Try H-V path
        corner1 = (p2[0], p1[1])
        hv_path = [p1, corner1, p2]
        if self._check_path_clearance(hv_path, other_segments):
            return True

        # Try V-H path
        corner2 = (p1[0], p2[1])
        vh_path = [p1, corner2, p2]
        if self._check_path_clearance(vh_path, other_segments):
            return True

        return False
    
    def _create_manhattan_path(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Create Manhattan path between two points
        
        Prefer H-V path (horizontal then vertical)
        """
        corner = (p2[0], p1[1])
        
        # If corner coincides with start or end, return straight line
        if corner == p1:
            return [p1, p2]
        if corner == p2:
            return [p1, p2]
        
        return [p1, corner, p2]
    
    def _check_path_clearance(self, path: List[Tuple[int, int]],
                             other_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]]) -> bool:
        """
        Check if path maintains safe distance from other paths

        Args:
            path: Path to check
            other_segments: Segments of other paths
        """
        # Convert path to segments
        path_segments = self._path_to_segments(path)
        
        # Check each segment
        for seg in path_segments:
            for other_seg in other_segments:
                # Calculate distance
                dist = self._segment_to_segment_distance(seg[0], seg[1], other_seg[0], other_seg[1])
                
                if dist < self.safe_distance:
                    return False
        
        return True
    
    def _get_direction(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> str:
        """
        Get direction between two points
        
        Returns:
            'H' (horizontal), 'V' (vertical), or 'D' (diagonal/other)
        """
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        
        if dx == 0 and dy != 0:
            return 'V'  # vertical
        elif dy == 0 and dx != 0:
            return 'H'  # horizontal
        else:
            return 'D'  # diagonal or coincident
    
    def _path_to_segments(self, path: List[Tuple[int, int]]) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Convert path to segment list
        
        Returns:
            [(start, end), ...]
        """
        segments = []
        for i in range(len(path) - 1):
            p1 = (float(path[i][0]), float(path[i][1]))
            p2 = (float(path[i+1][0]), float(path[i+1][1]))
            segments.append((p1, p2))
        return segments
    
    def _segment_to_segment_distance(self, p1: Tuple[float, float], p2: Tuple[float, float],
                                     q1: Tuple[float, float], q2: Tuple[float, float]) -> float:
        """
        Calculate minimum distance between two segments
        
        Args:
            p1, p2: Endpoints of first segment
            q1, q2: Endpoints of second segment
        
        Returns:
            Minimum distance
        """
        # Check if segments intersect
        if self._segments_intersect(p1, p2, q1, q2):
            return 0.0
        
        # Calculate distances from four endpoints to opposite segment
        distances = [
            self._point_to_segment_distance(p1, q1, q2),
            self._point_to_segment_distance(p2, q1, q2),
            self._point_to_segment_distance(q1, p1, p2),
            self._point_to_segment_distance(q2, p1, p2)
        ]
        
        return min(distances)
    
    def _segments_intersect(self, p1: Tuple[float, float], p2: Tuple[float, float],
                           q1: Tuple[float, float], q2: Tuple[float, float]) -> bool:
        """
        Check if two segments intersect
        
        Use cross product judgment
        """
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
        
        return ccw(p1, q1, q2) != ccw(p2, q1, q2) and ccw(p1, p2, q1) != ccw(p1, p2, q2)
    
    def _point_to_segment_distance(self, point: Tuple[float, float],
                                   seg_start: Tuple[float, float],
                                   seg_end: Tuple[float, float]) -> float:
        """
        Calculate minimum distance from point to segment
        
        Args:
            point: Point coordinates
            seg_start, seg_end: Segment endpoints
        
        Returns:
            Minimum distance
        """
        px, py = point
        x1, y1 = seg_start
        x2, y2 = seg_end
        
        # Segment length squared
        seg_len_sq = (x2 - x1)**2 + (y2 - y1)**2
        
        if seg_len_sq == 0:
            # Segment degenerates to point
            return math.sqrt((px - x1)**2 + (py - y1)**2)
        
        # Calculate projection parameter t
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / seg_len_sq))
        
        # Projection point
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        # Distance from point to projection point
        return math.sqrt((px - proj_x)**2 + (py - proj_y)**2)
    
    def get_smoothing_stats(self, original_paths: List[List[Tuple[int, int]]], 
                           smoothed_paths: List[List[Tuple[float, float]]]) -> dict:
        """
        Get smoothing statistics
        
        Returns:
            Dictionary containing statistics
        """
        stats = {
            'total_paths': len(original_paths),
            'original_total_points': sum(len(p) for p in original_paths),
            'smoothed_total_points': sum(len(p) for p in smoothed_paths),
            'point_reduction': 0,
            'reduction_percentage': 0.0,
            'avg_points_per_path_before': 0,
            'avg_points_per_path_after': 0,
            'original_total_turns': 0,
            'smoothed_total_turns': 0,
            'turn_reduction': 0
        }
        
        # Calculate turn counts
        for path in original_paths:
            stats['original_total_turns'] += self._count_turns(path)
        
        for path in smoothed_paths:
            stats['smoothed_total_turns'] += self._count_turns([(int(p[0]), int(p[1])) for p in path])
        
        stats['turn_reduction'] = stats['original_total_turns'] - stats['smoothed_total_turns']
        
        if stats['total_paths'] > 0:
            stats['point_reduction'] = stats['original_total_points'] - stats['smoothed_total_points']
            if stats['original_total_points'] > 0:
                stats['reduction_percentage'] = (stats['point_reduction'] / stats['original_total_points']) * 100
            stats['avg_points_per_path_before'] = stats['original_total_points'] / stats['total_paths']
            stats['avg_points_per_path_after'] = stats['smoothed_total_points'] / stats['total_paths']
        
        return stats
    
    def _count_turns(self, path: List[Tuple[int, int]]) -> int:
        """
        Count number of turns in path
        
        Turn definition: Point where direction changes (horizontal to vertical, or vertical to horizontal)
        """
        if len(path) < 3:
            return 0
        
        turns = 0
        prev_dir = None
        
        for i in range(len(path) - 1):
            curr_dir = self._get_direction(path[i], path[i+1])
            
            # Skip diagonals and coincident points
            if curr_dir == 'D':
                continue
            
            # If direction changes, there's a turn
            if prev_dir is not None and prev_dir != curr_dir:
                turns += 1
            
            prev_dir = curr_dir
        
        return turns


def smooth_region_paths(internal_paths: List[List[Tuple[int, int]]], 
                       external_paths: List[List[Tuple[int, int]]],
                       grid_size: int = 15,
                       min_spacing: int = 15) -> Tuple[List[List[Tuple[float, float]]], 
                                                        List[List[Tuple[float, float]]], 
                                                        dict]:
    """
    Smooth all paths in a region (convenience function)
    
    Args:
        internal_paths: Internal path list
        external_paths: External path list
        grid_size: Grid size
        min_spacing: Minimum spacing
    
    Returns:
        (smoothed internal paths, smoothed external paths, statistics)
    """
    smoother = PathSmoother(grid_size=grid_size, min_spacing=min_spacing)
    
    # Merge all paths for collision detection
    all_paths = internal_paths + external_paths
    
    # Smooth internal paths
    smoothed_internal = smoother.smooth_paths(internal_paths, all_paths)
    
    # Smooth external paths
    smoothed_external = smoother.smooth_paths(external_paths, all_paths)
    
    # Get statistics
    original_all = internal_paths + external_paths
    smoothed_all = smoothed_internal + smoothed_external
    stats = smoother.get_smoothing_stats(original_all, smoothed_all)
    
    return smoothed_internal, smoothed_external, stats