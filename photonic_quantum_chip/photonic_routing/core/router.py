"""
router.py - Advanced router
Advanced router using unidirectional A* search algorithm, 8-direction search (including diagonals), Euclidean distance heuristic.
"""

import heapq
import numpy as np
from .data_structures import DiagonalBitmap
from ..utils.geometry import euclidean_dist_numba


class AdvancedRouter:
    """
    Advanced router (using unidirectional A* search - 8-direction Euclidean distance version)
    - Uses DiagonalBitmap for diagonal conflict detection
    - Unidirectional A* search generates more regular and controllable routing paths
    - 8-direction movement (up/down/left/right + four diagonals) + Euclidean distance heuristic
    - Diagonal occupation strategy: prevents spacing conflicts
    """

    def __init__(self, grid_mgr):
        self.grid_mgr = grid_mgr
        self.h, self.w = grid_mgr.h, grid_mgr.w

        # Occupation grid
        self.occupation_grid = np.zeros((self.h, self.w), dtype=int)
        obs_idx = np.where(grid_mgr.grid == 3)
        self.occupation_grid[obs_idx] = -1

        # Optimized data structures
        self.diagonal_bitmap = DiagonalBitmap()

        # Diagonal occupation markers: record which grid points are marked as occupied due to diagonal occupation
        # Format: {(x, y): net_id} indicates this point is occupied by net_id's diagonal
        self.diagonal_occupied_points = {}

        # Global reserved points
        self.global_reserved_points = set()

        # Statistics
        self.stats = {
            'nodes_explored': 0,
            'diagonal_checks': 0
        }

    def euclidean_dist(self, p1, p2):
        """Euclidean distance (for non-A* scenarios)"""
        return euclidean_dist_numba(p1[0], p1[1], p2[0], p2[1])

    def check_diagonal_conflict_fast(self, start, end, net_id):
        """O(1) diagonal conflict detection"""
        self.stats['diagonal_checks'] += 1
        return self.diagonal_bitmap.check_conflict(start[0], start[1], end[0], end[1], net_id)
    
    def mark_diagonal_occupation(self, x1, y1, x2, y2, net_id):
        """
        Mark diagonal occupation strategy
        When a diagonal path exists within a grid, mark remaining two diagonal grid points of that grid as occupied
        
        For example: if diagonal goes from (x1,y1) to (x2,y2), mark other two corner points as occupied
        For main diagonal (bottom-left to top-right or top-right to bottom-left): mark top-left and bottom-right
        For anti-diagonal (top-left to bottom-right or bottom-right to top-left): mark bottom-left and top-right
        """
        dx = x2 - x1
        dy = y2 - y1
        
        # Only handle diagonal movement
        if abs(dx) != 1 or abs(dy) != 1:
            return
        
        # Determine bottom-left corner coordinates of grid
        cell_x = min(x1, x2)
        cell_y = min(y1, y2)
        
        # Four corner points of grid
        corners = [
            (cell_x, cell_y),      # Bottom-left
            (cell_x + 1, cell_y),  # Bottom-right
            (cell_x, cell_y + 1),  # Top-left
            (cell_x + 1, cell_y + 1)  # Top-right
        ]
        
        # Determine diagonal type and points to mark
        if dx * dy > 0:  # Main diagonal (bottom-left to top-right)
            # Mark top-left and bottom-right
            points_to_mark = [(cell_x, cell_y + 1), (cell_x + 1, cell_y)]
        else:  # Anti-diagonal (top-left to bottom-right)
            # Mark bottom-left and top-right
            points_to_mark = [(cell_x, cell_y), (cell_x + 1, cell_y + 1)]
        
        # Mark these points as occupied (unless they are start or end points)
        for px, py in points_to_mark:
            if (px, py) != (x1, y1) and (px, py) != (x2, y2):
                # Only mark points within grid range
                if 0 <= px < self.w and 0 <= py < self.h:
                    self.diagonal_occupied_points[(px, py)] = net_id

    def generate_backup_points_projection_pairs(self, boundary, points, target_bbox):
        """Generate backup point projection pairs (original method, for Out points)"""
        if len(points) == 0:
            return []

        xmin, ymin, xmax, ymax = target_bbox

        # Group by lines perpendicular to boundary
        from collections import defaultdict
        lines = defaultdict(list)
        for cp in points:
            cx, cy = int(cp[0]), int(cp[1])
            if boundary in ['Top', 'Bottom']:
                proj_y = ymax if boundary == 'Top' else ymin
                dist = abs(cy - proj_y)
                lines[cx].append({'origin': cp, 'proj': (cx, proj_y), 'dist': dist})
            else:
                proj_x = xmin if boundary == 'Left' else xmax
                dist = abs(cx - proj_x)
                lines[cy].append({'origin': cp, 'proj': (proj_x, cy), 'dist': dist})

        # Sort by distance within each line
        for key in lines:
            lines[key].sort(key=lambda x: x['dist'])

        # Collect all points and sort by distance to determine processing order
        all_candidates = []
        for key, pts in lines.items():
            for p in pts:
                p['line_key'] = key
                all_candidates.append(p)
        all_candidates.sort(key=lambda x: x['dist'])

        connection_pairs = []
        processed_lines = set()  # Record processed lines

        for cand in all_candidates:
            px, py = cand['proj']
            line_key = cand['line_key']
            is_first_on_line = line_key not in processed_lines
            processed_lines.add(line_key)

            # First point (closest) tries direct vertical projection, others bidirectional search
            if is_first_on_line:
                search_offsets = [0]
                for i in range(1, max(self.w, self.h)):
                    search_offsets.extend([i, -i])
            else:
                search_offsets = []
                for i in range(1, max(self.w, self.h)):
                    search_offsets.extend([i, -i])

            found = False
            for offset in search_offsets:
                tx, ty = px, py
                if boundary in ['Top', 'Bottom']:
                    tx = px + offset
                else:
                    ty = py + offset

                if not (0 <= tx < self.w and 0 <= ty < self.h):
                    continue
                if (tx, ty) in self.global_reserved_points:
                    continue
                if self.grid_mgr.grid[ty, tx] == 3:
                    continue
                if self.grid_mgr.grid[ty, tx] == 2:
                    continue
                if self.occupation_grid[ty, tx] != 0:
                    continue

                self.global_reserved_points.add((tx, ty))
                connection_pairs.append((cand['origin'], (tx, ty)))
                found = True
                break

            if not found:
                print(f"Warning: Point {cand['origin']} on {boundary} cannot project (full boundary)!")

        return connection_pairs

    def generate_backup_points_avoid_obstacles_center(self, boundary, points, target_bbox):
        """
        Obstacle-aware projection algorithm grouped by vertical lines

        Args:
            boundary: Boundary direction ('Top'/'Bottom'/'Left'/'Right')
            points: Center point list
            target_bbox: Target area bounding box

        Returns:
            List of projection pairs sorted by vertical distance to boundary [(origin_point, backup_point), ...]
        """
        if len(points) == 0:
            return []
        
        # Vertical boundaries use original logic
        if boundary in ['Left', 'Right']:
            return self.generate_backup_points_projection_pairs(boundary, points, target_bbox)
        
        xmin, ymin, xmax, ymax = target_bbox
        projection_y = ymax if boundary == 'Top' else ymin
        
        # ===== Step 1: Group by x coordinate (form vertical lines) =====
        from collections import defaultdict
        vertical_lines = defaultdict(list)
        
        for cp in points:
            cx, cy = int(cp[0]), int(cp[1])
            dist_to_boundary = abs(cy - projection_y)
            vertical_lines[cx].append((cx, cy, cp, dist_to_boundary))
        
        print(f"[Vertical line grouping] Projection for horizontal boundary '{boundary}':")
        print(f"[Vertical line grouping] Total {len(points)} points, divided into {len(vertical_lines)} vertical lines")
        
        # ===== Step 2: Sort within each vertical line =====
        for x_coord in vertical_lines:
            # Sort by distance to boundary (near→far)
            vertical_lines[x_coord].sort(key=lambda p: p[3])
        
        # ===== Step 3: Detect obstacle positions between center points (excluding boundaries) =====
        # Collect x coordinates of all center points
        center_x_coords = set()
        for x in range(self.w):
            for y in range(self.h):
                if self.grid_mgr.grid[y, x] == 2:  # Center point
                    center_x_coords.add(x)
        
        # Only detect obstacles between center points
        obstacle_x_coords = set()
        for x in range(self.w):
            # Only check obstacles within center point range
            if x in center_x_coords:
                continue  # Center point itself is not an obstacle
            
            # Check if this column has obstacles
            has_obstacle = False
            for y in range(self.h):
                if self.grid_mgr.grid[y, x] == 3:
                    has_obstacle = True
                    break
            
            if has_obstacle:
                # Check if this obstacle is between center points (has center points on both sides)
                has_left_center = any(cx < x for cx in center_x_coords)
                has_right_center = any(cx > x for cx in center_x_coords)
                if has_left_center and has_right_center:
                    obstacle_x_coords.add(x)
        
        print(f"[Vertical line grouping] Detected {len(obstacle_x_coords)} obstacle columns between center points")
        print(f"[Vertical line grouping] Bounding box range: x=[{xmin}, {xmax}], y=[{ymin}, {ymax}]")
        
        # ===== Step 4: Process mapping by vertical line (x coordinate) order =====
        x_coords_sorted = sorted(vertical_lines.keys())

        # Use list to store mapping results, each element contains (origin_point, backup_point, dist_to_boundary)
        connection_pairs_with_dist = []

        for x_coord in x_coords_sorted:
            points_in_line = vertical_lines[x_coord]
            
            print(f"\n[Vertical line grouping] Processing vertical line x={x_coord}, total {len(points_in_line)} points:")
            
            # ===== Key fix: Determine unified projection direction for entire vertical line =====
            # 1. First check if this vertical line is on bounding box boundary
            is_on_left_boundary = (x_coord == xmin)
            is_on_right_boundary = (x_coord == xmax)
            
            if is_on_left_boundary:
                # On left boundary → project left (outward)
                line_direction = -1
                direction_str = "Left (left boundary, outward projection)"
            elif is_on_right_boundary:
                # On right boundary → project right (outward)
                line_direction = 1
                direction_str = "Right (right boundary, outward projection)"
            else:
                # Not on boundary → check left and right neighbors of all center points on this vertical line
                # Count obstacles in left and right neighbors
                left_neighbor_x = x_coord - 1
                right_neighbor_x = x_coord + 1
                
                left_obstacle_count = 0
                right_obstacle_count = 0
                
                # Traverse all center points on this vertical line
                for cx, cy, original_point, dist in points_in_line:
                    # Check left neighbor of this center point (same row)
                    if 0 <= left_neighbor_x < self.w and 0 <= cy < self.h:
                        if self.grid_mgr.grid[cy, left_neighbor_x] == 3:
                            left_obstacle_count += 1
                    
                    # Check right neighbor of this center point (same row)
                    if 0 <= right_neighbor_x < self.w and 0 <= cy < self.h:
                        if self.grid_mgr.grid[cy, right_neighbor_x] == 3:
                            right_obstacle_count += 1
                
                # Determine unified projection direction for this vertical line
                if left_obstacle_count > right_obstacle_count:
                    # More obstacles on left → project right (away from obstacles)
                    line_direction = 1  # Positive direction (right)
                    direction_str = f"Right (left_obs={left_obstacle_count}, right_obs={right_obstacle_count})"
                elif right_obstacle_count > left_obstacle_count:
                    # More obstacles on right → project left (away from obstacles)
                    line_direction = -1  # Negative direction (left)
                    direction_str = f"Left (left_obs={left_obstacle_count}, right_obs={right_obstacle_count})"
                else:
                    # Equal count → default right
                    line_direction = 1
                    direction_str = f"Right (default, left_obs={left_obstacle_count}, right_obs={right_obstacle_count})"
            
            print(f"[Vertical line grouping] Unified projection direction for this vertical line: {direction_str}")
            
            # Process each point on this vertical line
            for idx, (cx, cy, original_point, dist) in enumerate(points_in_line):
                proj_x, proj_y = cx, projection_y
                
                if idx == 0:
                    # ===== Closest point on this vertical line → direct mapping (offset=0) =====
                    search_offsets = [0]
                    # If direct mapping position unavailable, small range offset in unified direction
                    for i in range(1, 5):
                        search_offsets.append(line_direction * i)
                    
                    point_direction_str = "Direct mapping (closest in vertical line)"
                    
                else:
                    # ===== Other points on this vertical line → incremental offset in unified direction =====
                    # Offset starts from idx (2nd point offset 1, 3rd point offset 2...)
                    search_offsets = []
                    for i in range(idx, max(self.w, self.h)):
                        search_offsets.append(line_direction * i)
                    
                    point_direction_str = f"Offset {line_direction * idx}+ (unified direction)"
                
                print(f"  Point{idx+1}/{len(points_in_line)}: ({cx},{cy}) distance={dist:.1f} → {point_direction_str}")
                
                # ===== Step 5: Search available points (allow on bounding box boundary extension) =====
                found = False
                for offset in search_offsets:
                    tx = proj_x + offset
                    ty = proj_y

                    # Boundary check (just need to be in routing area, not limited to bounding box)
                    if not (0 <= tx < self.w and 0 <= ty < self.h):
                        continue

                    # Check if available
                    if (tx, ty) in self.global_reserved_points:
                        print(f"      ({tx},{ty}) skip: global_reserved_points")
                        continue
                    if self.grid_mgr.grid[ty, tx] == 3:  # Obstacle
                        print(f"      ({tx},{ty}) skip: Obstacle")
                        continue
                    if self.grid_mgr.grid[ty, tx] == 2:  # Center point
                        print(f"      ({tx},{ty}) skip: Center point")
                        continue
                    if self.occupation_grid[ty, tx] != 0:  # Already occupied
                        print(f"      ({tx},{ty}) skip: Occupied net={self.occupation_grid[ty, tx]}")
                        continue

                    # Found available point, record mapping result and distance
                    self.global_reserved_points.add((tx, ty))
                    connection_pairs_with_dist.append((original_point, (tx, ty), dist))
                    found = True
                    
                    # Determine if outside bounding box
                    in_bbox = (xmin <= tx <= xmax)
                    location_str = "Inside bounding box" if in_bbox else "Outside bounding box (extension line)"
                    print(f"    ✓ Mapped to ({tx}, {ty}), offset={offset}, {location_str}")
                    break
                
                if not found:
                    print(f"    ✗ Warning: Point ({cx}, {cy}) cannot map (boundary full)")
        
        # ===== Step 6: Sort by vertical distance to boundary (key fix) =====
        # Ensure routing order is from points near boundary to points far from boundary
        connection_pairs_with_dist.sort(key=lambda x: x[2])
        
        # Extract sorted mapping pairs (remove distance info)
        connection_pairs = [(origin, backup) for origin, backup, dist in connection_pairs_with_dist]
        
        print(f"\n[Vertical line grouping] Complete: Generated {len(connection_pairs)} backup points")
        print(f"[Vertical line grouping] Routing order: Sorted by vertical distance to boundary (near→far)")
        print(f"[Vertical line grouping] Closest point on each vertical line maps directly (offset=0)")
        
        return connection_pairs

    def a_star(self, start, end, net_id, search_area=None, forbidden_points=None,
               restrict_poly_path=None):
        """
        Unidirectional A* search algorithm (8-direction, Euclidean distance version)
        """
        start, end = tuple(map(int, start)), tuple(map(int, end))
        
        open_set = [(0, 0, start[0], start[1])]
        came_from = {}
        g_score = {start: 0}
        
        # 8 directions: up/down/left/right + four diagonals
        straight_directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        diagonal_directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        
        while open_set:
            f, cg, cx, cy = heapq.heappop(open_set)
            current = (cx, cy)
            
            self.stats['nodes_explored'] += 1
            
            if current == end:
                path = [end]
                while path[-1] in came_from:
                    path.append(came_from[path[-1]])
                path = path[::-1]
                
                # Record path to diagonal_bitmap
                for i in range(len(path) - 1):
                    p1, p2 = path[i], path[i + 1]

                    # If diagonal movement, record to diagonal_bitmap and mark occupation
                    dx = abs(p2[0] - p1[0])
                    dy = abs(p2[1] - p1[1])
                    if dx == 1 and dy == 1:
                        self.diagonal_bitmap.add_diagonal(p1[0], p1[1], p2[0], p2[1], net_id)
                        self.mark_diagonal_occupation(p1[0], p1[1], p2[0], p2[1], net_id)
                
                return path
            
            # Try all 8 directions
            for dx, dy in straight_directions + diagonal_directions:
                nx, ny = cx + dx, cy + dy
                neighbor = (nx, ny)
                
                # Boundary check
                if not (0 <= nx < self.w and 0 <= ny < self.h):
                    continue
                
                # Search area limit
                if search_area:
                    if not (search_area[0] <= nx <= search_area[2] and
                           search_area[1] <= ny <= search_area[3]):
                        if neighbor != end:
                            continue
                
                # Polygon area limit
                if restrict_poly_path:
                    if not restrict_poly_path.contains_point((nx, ny)):
                        if neighbor != end and neighbor != start:
                            continue
                
                # Occupation check
                occ = self.occupation_grid[ny, nx]
                if occ != 0 and occ != net_id and neighbor != end:
                    continue
                
                # Forbidden points check
                if forbidden_points and neighbor in forbidden_points and neighbor != end:
                    continue
                
                # Diagonal occupation strategy check
                if neighbor in self.diagonal_occupied_points:
                    occupied_by = self.diagonal_occupied_points[neighbor]
                    if occupied_by != net_id and neighbor != end:
                        continue
                
                # Diagonal conflict detection (only needed for diagonal movement)
                is_diagonal = abs(dx) == 1 and abs(dy) == 1
                if is_diagonal:
                    if self.check_diagonal_conflict_fast(current, neighbor, net_id):
                        continue
                
                # Calculate movement cost: straight 1.0, diagonal 1.414
                if is_diagonal:
                    move_cost = 1.414
                else:
                    move_cost = 1.0
                
                tentative_g = cg + move_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    h = euclidean_dist_numba(nx, ny, end[0], end[1])
                    f_score = tentative_g + h
                    heapq.heappush(open_set, (f_score, tentative_g, nx, ny))
                    came_from[neighbor] = current
        
        return None

    def route_single_net(self, start, end, net_id, restrict_to_bbox=None, 
                        all_terminals=None, restrict_poly_path=None):
        """Route single net"""
        effective_bbox = restrict_to_bbox
        if restrict_to_bbox:
            b_xmin, b_ymin, b_xmax, b_ymax = restrict_to_bbox
            new_xmin = min(b_xmin, start[0], end[0])
            new_ymin = min(b_ymin, start[1], end[1])
            new_xmax = max(b_xmax, start[0], end[0])
            new_ymax = max(b_ymax, start[1], end[1])
            effective_bbox = (new_xmin, new_ymin, new_xmax, new_ymax)
        
        path = self.a_star(
            start, end, net_id,
            search_area=effective_bbox,
            forbidden_points=all_terminals,
            restrict_poly_path=restrict_poly_path
        )
        
        if path:
            for x, y in path:
                self.occupation_grid[y, x] = net_id
        
        return path
    
    def print_stats(self):
        """Print statistics"""
        return {
            'nodes_explored': self.stats['nodes_explored'],
            'diagonal_checks': self.stats['diagonal_checks']
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {'nodes_explored': 0, 'diagonal_checks': 0}

    def remove_path_occupation(self, path):
        """Remove all occupation states for specified path"""
        if not path or len(path) < 2:
            return

        # Get net_id used by this path (read from occupation_grid)
        net_ids = set()
        for x, y in path:
            if 0 <= y < self.h and 0 <= x < self.w:
                val = self.occupation_grid[y, x]
                if val > 0:
                    net_ids.add(val)

        # Clean occupation_grid
        for x, y in path:
            if 0 <= y < self.h and 0 <= x < self.w:
                if self.occupation_grid[y, x] > 0:
                    self.occupation_grid[y, x] = 0

        # Clean diagonal_bitmap and diagonal_occupied_points
        for net_id in net_ids:
            self.diagonal_bitmap.remove_net(net_id)
            keys_to_remove = [k for k, v in self.diagonal_occupied_points.items() if v == net_id]
            for k in keys_to_remove:
                del self.diagonal_occupied_points[k]