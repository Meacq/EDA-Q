"""
Path merging module

After three-stage routing is complete, merge segmented paths into complete paths.
Each complete path starts from Center point, passes through backup points, and finally reaches Out point.
"""

def merge_paths(internal_paths, external_paths, center_backups_ordered, out_backups_ordered):
    """
    Merge three-stage routing paths

    Args:
        internal_paths: Internal path list from stage 1 and stage 2
        external_paths: External connection path list from stage 3
        center_backups_ordered: Center backup point list (ordered)
        out_backups_ordered: Out backup point list (ordered)

    Returns:
        merged_paths: Merged complete path list, each path from Center to Out
    """
    # Build backup point to path mapping
    center_backup_to_path = {}
    out_backup_to_path = {}

    # Iterate through internal paths, identify start and end points
    for path in internal_paths:
        if not path or len(path) < 2:
            continue

        start, end = tuple(path[0]), tuple(path[-1])

        # Determine if it's Center path or Out path
        # Stage 2: Center backup → Center point (end is Center point)
        if start in center_backups_ordered:
            center_backup_to_path[start] = path
        # Stage 1: Out point → Out backup (end is Out backup)
        elif end in out_backups_ordered:
            out_backup_to_path[end] = path

    # Build external path mapping: Center backup point -> Out backup point
    external_connections = {}
    for path in external_paths:
        if not path or len(path) < 2:
            continue
        start, end = tuple(path[0]), tuple(path[-1])
        external_connections[start] = (end, path)

    # Merge paths
    merged_paths = []

    for center_backup in center_backups_ordered:
        center_backup = tuple(center_backup)

        # Check if there's a corresponding external connection
        if center_backup not in external_connections:
            continue

        out_backup, external_path = external_connections[center_backup]

        # Check if there's a corresponding internal path
        if center_backup not in center_backup_to_path or out_backup not in out_backup_to_path:
            continue

        # Get three segments of path
        center_internal = center_backup_to_path[center_backup]  # Center backup → Center
        out_internal = out_backup_to_path[out_backup]  # Out → Out backup

        # Merge paths: Center internal path (reversed) + external path + Out internal path (reversed)
        # Stage 2 reversed: Center → Center backup
        # Stage 3: Center backup → Out backup
        # Stage 1 reversed: Out backup → Out
        merged = list(reversed(center_internal)) + external_path[1:] + list(reversed(out_internal))[1:]

        merged_paths.append(merged)

    return merged_paths
