"""
snapshot_manager.py - Snapshot manager
Snapshot manager supports saving, restoring, and switching between different routing states.
Enables repeatable navigation operations on routing history.
"""

import copy
from datetime import datetime


class GlobalSnapshotManager:
    """Global snapshot manager - Enhanced version, supports snapshot switching"""
    
    def __init__(self):
        self.snapshots = []
        self.current_snapshot_index = -1  # Currently used snapshot index

    def save_snapshot(self, task_count, router, all_finished_paths):
        """Save snapshot"""
        snapshot = {
            'task_count': task_count,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'router_state': {
                'occupation_grid': copy.deepcopy(router.occupation_grid),
                'diagonal_bitmap': router.diagonal_bitmap.copy(),
                'global_reserved_points': copy.deepcopy(router.global_reserved_points)
            },
            'all_finished_paths': copy.deepcopy(all_finished_paths)
        }
        self.snapshots.append(snapshot)
        self.current_snapshot_index = len(self.snapshots) - 1

    def list_snapshots(self):
        """List all snapshots"""
        return self.snapshots

    def restore_snapshot(self, index, router):
        """Restore to specified snapshot, supports repeated switching"""
        if 0 <= index < len(self.snapshots):
            snap = self.snapshots[index]
            router.occupation_grid = copy.deepcopy(snap['router_state']['occupation_grid'])

            # Compatible with old version snapshots (without diagonal_bitmap)
            if 'diagonal_bitmap' in snap['router_state']:
                router.diagonal_bitmap = snap['router_state']['diagonal_bitmap'].copy()
            else:
                from ..core.data_structures import DiagonalBitmap
                router.diagonal_bitmap = DiagonalBitmap()

            # Note: spatial_hash is no longer used, ignore if present in old snapshots

            router.global_reserved_points = copy.deepcopy(
                snap['router_state']['global_reserved_points']
            )

            # Update current snapshot index
            self.current_snapshot_index = index

            return (snap['task_count'], copy.deepcopy(snap['all_finished_paths']))
        return None
    
    def get_current_snapshot_index(self):
        """Get current snapshot index"""
        return self.current_snapshot_index
    
    def clear(self):
        """Clear all snapshots"""
        self.snapshots.clear()
        self.current_snapshot_index = -1
