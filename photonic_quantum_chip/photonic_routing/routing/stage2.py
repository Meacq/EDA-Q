"""
stage2.py - Stage 2: Center point internal routing controller
Stage 2 controller for Center point internal routing.
Maps Center points to boundaries and creates backup points with optimized order.
"""

import time
from ..utils.helpers import format_time
from ..utils.geometry import euclidean_dist_numba
from tkinter import messagebox


class Stage2Controller:
    """Stage 2 controller"""
    
    def __init__(self, ui):
        self.ui = ui
    
    def execute_auto(self):
        """Execute stage 2 auto mode"""
        self.ui.log("Executing automated Center mapping...")
        
        # Simplified auto matching: assign Center points based on nearest Out point
        self.ui.ctx['center_boundary_map'] = {'Top': [], 'Bottom': [], 'Left': [], 'Right': []}
        center_list = list(self.ui.valid_center)
        out_list = list(self.ui.valid_out)
        
        for center_pt in center_list:
            min_dist = float('inf')
            nearest_out = None
            for out_pt in out_list:
                d = euclidean_dist_numba(center_pt[0], center_pt[1],
                                        out_pt[0], out_pt[1])
                if d < min_dist:
                    min_dist = d
                    nearest_out = out_pt
            
            if nearest_out is not None:
                label = self.ui.grid_mgr.get_out_label(nearest_out[0], nearest_out[1])
                target_boundary = label if label in self.ui.ctx['center_boundary_map'] else 'Right'
                self.ui.ctx['center_boundary_map'][target_boundary].append(center_pt)
        
        self.execute_routing()
    
    def start_manual(self):
        """Start stage 2 manual mode"""
        self.ui.log("Starting manual Center boundary assignment...")
        self.ui.ctx['center_boundary_map'] = {'Top': [], 'Bottom': [], 'Left': [], 'Right': []}
        
        self.ui.boundary_assignments = {'Top': [], 'Bottom': [], 'Left': [], 'Right': []}
        self.ui.boundary_directions = ['Top', 'Bottom', 'Left', 'Right']
        self.ui.boundary_direction_index = 0
        self.ui.boundary_points_pool = list(self.ui.valid_center)
        self.ui.boundary_point_type = 'Center'
        self.ui.boundary_bbox = self.ui.ctx['center_bbox']
        
        self.ui.start_boundary_direction_selection()
    
    def execute_routing(self):
        """Execute stage 2 routing"""
        self.ui.log("Starting Center internal routing...")
        
        all_terminals = set(tuple(p) for p in self.ui.valid_center)
        boundary_order = ['Top', 'Bottom', 'Left', 'Right']
        
        for b in boundary_order:
            pts = self.ui.ctx['center_boundary_map'][b]
            if not pts:
                continue
            
            self.ui.log(f"  Processing {len(pts)} Center points on {b} boundary...")

            pairs = self.ui.router.generate_backup_points_avoid_obstacles_center(
                b, pts, self.ui.ctx['center_bbox'])

            for origin_center, backup_point in pairs:
                self.ui.ctx['center_backups_ordered'].append(backup_point)
                self.ui.ctx['center_backups_grouped'][b].append(backup_point)
                
                start_pt = tuple(backup_point)
                end_pt = tuple(origin_center)
                
                path = self.ui.router.route_single_net(
                    start_pt, end_pt, self.ui.ctx['current_net_id'],
                    restrict_to_bbox=None,
                    all_terminals=all_terminals,
                    restrict_poly_path=self.ui.poly_path)
                
                if path:
                    self.ui.ctx['internal_paths'].append(path)
                else:
                    self.ui.log(f"  Center routing failed: {start_pt}->{end_pt}", 'WARNING')
                
                self.ui.ctx['current_net_id'] += 1
        
        self.ui.stage2_time = time.time() - self.ui.stage_start_time
        self.ui.log(f"Stage 2 completed, generated {len(self.ui.ctx['center_backups_ordered'])} Center backup points",
                'SUCCESS')
        self.ui.log(f"[Timing] Stage 2 Center internal routing time: {format_time(self.ui.stage2_time)}",
                'TIMING')
        
        timer_var = self.ui.control_panel.get_widget('timer_var')
        timer_var.set(f"⏱️ Stage 2 time: {format_time(self.ui.stage2_time)}")
        
        self.ui._plot_base_grid(
            title=f"Region {self.ui.task_count} - Stage 2 Complete (Center Internal)",
            center_backups=self.ui.ctx['center_backups_ordered'],
            out_backups=self.ui.ctx['out_backups_ordered'],
            out_points=self.ui.valid_out,
            current_paths=self.ui.ctx['internal_paths'],
            show_region=True
        )
        
        stage_var = self.ui.control_panel.get_widget('stage_var')
        stage_var.set("✅ Stage 2 Complete")

        if messagebox.askyesno("Print Labels",
                              "Print backup point label summary?\n\n"
                              "This will help you perform external connections in manual mode"):
            self.ui.show_backup_points_summary()

        self.ui._show_stage_complete_buttons()