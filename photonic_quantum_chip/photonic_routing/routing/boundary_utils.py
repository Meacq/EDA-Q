"""
boundary_utils.py - Boundary processing tools
Boundary processing tools including boundary identification, point sorting, and pair generation.
Supports parallel and L-shaped boundary matching strategies.
"""

def is_horizontal_boundary(boundary):
    """Check if it's a horizontal boundary (Top/Bottom)"""
    return boundary in {'Top', 'Bottom'}


def is_vertical_boundary(boundary):
    """Check if it's a vertical boundary (Left/Right)"""
    return boundary in {'Left', 'Right'}


def check_parallel_boundaries(ck, ok):
    """Check if two boundaries are parallel"""
    if is_horizontal_boundary(ck) and is_horizontal_boundary(ok):
        return True, 'horizontal'
    elif is_vertical_boundary(ck) and is_vertical_boundary(ok):
        return True, 'vertical'
    else:
        return False, None


def check_L_shaped_boundaries(ck, ok):
    """Check if two boundaries form L-shape"""
    if is_horizontal_boundary(ck) and is_vertical_boundary(ok):
        return True, ok, ck
    elif is_vertical_boundary(ck) and is_horizontal_boundary(ok):
        return True, ck, ok
    else:
        return False, None, None


def sort_points_by_position(points, boundary, order):
    """Sort points by position"""
    points_list = list(points)
    
    if is_horizontal_boundary(boundary):
        if order == 'left_to_right':
            points_list.sort(key=lambda p: p[0])
        else:
            points_list.sort(key=lambda p: p[0], reverse=True)
    else:
        if order == 'top_to_bottom':
            points_list.sort(key=lambda p: p[1], reverse=True)
        else:
            points_list.sort(key=lambda p: p[1])
    
    return points_list


def create_parallel_pairs(c_pts, o_pts, ck, ok, routing_strategy):
    """Create point pair mapping for parallel boundaries"""
    if routing_strategy == 'c_left_o_left':
        c_order = 'left_to_right'
        o_order = 'left_to_right'
        order_desc = "Center leftmost ↔ Out leftmost, then right"
    elif routing_strategy == 'c_left_o_right':
        c_order = 'left_to_right'
        o_order = 'right_to_left'
        order_desc = "Center leftmost ↔ Out rightmost, then reverse direction"
    elif routing_strategy == 'c_right_o_left':
        c_order = 'right_to_left'
        o_order = 'left_to_right'
        order_desc = "Center rightmost ↔ Out leftmost, then reverse direction"
    elif routing_strategy == 'c_right_o_right':
        c_order = 'right_to_left'
        o_order = 'right_to_left'
        order_desc = "Center rightmost ↔ Out rightmost, then left"
    elif routing_strategy == 'c_top_o_top':
        c_order = 'top_to_bottom'
        o_order = 'top_to_bottom'
        order_desc = "Center topmost ↔ Out topmost, then down"
    elif routing_strategy == 'c_top_o_bottom':
        c_order = 'top_to_bottom'
        o_order = 'bottom_to_top'
        order_desc = "Center topmost ↔ Out bottommost, then reverse direction"
    elif routing_strategy == 'c_bottom_o_top':
        c_order = 'bottom_to_top'
        o_order = 'top_to_bottom'
        order_desc = "Center bottommost ↔ Out topmost, then reverse direction"
    elif routing_strategy == 'c_bottom_o_bottom':
        c_order = 'bottom_to_top'
        o_order = 'bottom_to_top'
        order_desc = "Center bottommost ↔ Out bottommost, then up"
    else:
        c_order = 'left_to_right'
        o_order = 'left_to_right'
        order_desc = "Default order"
    
    sorted_c = sort_points_by_position(c_pts, ck, c_order)
    sorted_o = sort_points_by_position(o_pts, ok, o_order)
    
    pairs = []
    min_len = min(len(sorted_c), len(sorted_o))
    
    for i in range(min_len):
        pairs.append({
            'start': sorted_c[i],
            'end': sorted_o[i]
        })
    
    return pairs, order_desc, len(sorted_c) != len(sorted_o)


def create_L_shaped_pairs(c_pts, o_pts, ck, ok, vertical_boundary, horizontal_boundary,
                          vertical_order, horizontal_order):
    """Create point pair mapping for L-shaped boundaries"""
    if ck == vertical_boundary:
        vertical_pts = list(c_pts)
        horizontal_pts = list(o_pts)
        vertical_is_center = True
    else:
        vertical_pts = list(o_pts)
        horizontal_pts = list(c_pts)
        vertical_is_center = False
    
    vertical_pts = sort_points_by_position(vertical_pts, vertical_boundary, vertical_order)
    horizontal_pts = sort_points_by_position(horizontal_pts, horizontal_boundary, horizontal_order)
    
    pairs = []
    min_len = min(len(vertical_pts), len(horizontal_pts))
    
    for i in range(min_len):
        if vertical_is_center:
            pairs.append({
                'start': vertical_pts[i],
                'end': horizontal_pts[i]
            })
        else:
            pairs.append({
                'start': horizontal_pts[i],
                'end': vertical_pts[i]
            })
    
    v_order_desc = "Bottom to Top" if vertical_order == 'bottom_to_top' else "Top to Bottom"
    h_order_desc = "Left to Right" if horizontal_order == 'left_to_right' else "Right to Left"
    
    return pairs, v_order_desc, h_order_desc, len(vertical_pts) != len(horizontal_pts)


def auto_match_boundary_groups(c_groups, o_groups):
    """Auto match boundary groups"""
    matches = []
    used_c = set()
    used_o = set()
    
    active_c = {k: v for k, v in c_groups.items() if len(v) > 0}
    active_o = {k: v for k, v in o_groups.items() if len(v) > 0}
    
    # Round 1: Match parallel boundaries
    for ck in list(active_c.keys()):
        if ck in used_c:
            continue
        
        if ck in active_o and ck not in used_o:
            matches.append((active_c[ck], active_o[ck], ck, ck))
            used_c.add(ck)
            used_o.add(ck)
            continue
        
        parallel_pair = {'Top': 'Bottom', 'Bottom': 'Top', 'Left': 'Right', 'Right': 'Left'}
        pk = parallel_pair.get(ck)
        if pk and pk in active_o and pk not in used_o:
            matches.append((active_c[ck], active_o[pk], ck, pk))
            used_c.add(ck)
            used_o.add(pk)
    
    # Round 2: Match L-shaped boundaries
    remaining_c = [k for k in active_c.keys() if k not in used_c]
    remaining_o = [k for k in active_o.keys() if k not in used_o]
    
    for ck in remaining_c:
        if ck in used_c:
            continue
        
        for ok in remaining_o:
            if ok in used_o:
                continue
            
            is_L, _, _ = check_L_shaped_boundaries(ck, ok)
            if is_L:
                matches.append((active_c[ck], active_o[ok], ck, ok))
                used_c.add(ck)
                used_o.add(ok)
                break
    
    unmatched_c = [k for k in active_c.keys() if k not in used_c]
    unmatched_o = [k for k in active_o.keys() if k not in used_o]
    
    return matches, unmatched_c, unmatched_o
