"""
stage1.py - Stage 1: Out point internal routing controller
Stage 1 controller for Out point internal routing.
Maps Out points to boundaries and creates backup points through projection.
"""

import time
from ..utils.helpers import format_time


class Stage1Controller:
    """Stage 1 controller"""
    
    def __init__(self, ui):
        self.ui = ui
    
    def execute_auto(self):
        """Execute stage 1 auto mode"""
        self.ui.log("Executing automated Out mapping...")
        
        target_map = {'Top': 'Bottom', 'Bottom': 'Top', 'Left': 'Right', 'Right': 'Left'}
        self.ui.ctx['out_boundary_map'] = {'Top': [], 'Bottom': [], 'Left': [], 'Right': []}
        
        for label, pts in self.ui.out_groups.items():
            if not pts:
                continue
            target_dir = target_map.get(label, 'Right')
            for p in pts:
                self.ui.ctx['out_boundary_map'][target_dir].append(p)
        
        self.execute_routing()
    
    def start_manual(self):
        """Start stage 1 manual mode"""
        self.ui.log("Starting manual Out boundary assignment...")
        self.ui.ctx['out_boundary_map'] = {'Top': [], 'Bottom': [], 'Left': [], 'Right': []}
        
        self.ui.boundary_assignments = {'Top': [], 'Bottom': [], 'Left': [], 'Right': []}
        self.ui.boundary_directions = ['Top', 'Bottom', 'Left', 'Right']
        self.ui.boundary_direction_index = 0
        self.ui.boundary_points_pool = list(self.ui.valid_out)
        self.ui.boundary_point_type = 'Out'
        self.ui.boundary_bbox = self.ui.ctx['out_bbox']
        
        self.ui.start_boundary_direction_selection()
    
    def execute_routing(self):
        """Execute stage 1 routing"""
        self.ui.log("Starting Out internal routing...")
        
        boundary_order = ['Top', 'Bottom', 'Left', 'Right']
        all_terminals = set(tuple(p) for p in self.ui.valid_out)
        
        for b in boundary_order:
            pts = self.ui.ctx['out_boundary_map'][b]
            if not pts:
                continue
            
            pairs = self.ui.router.generate_backup_points_projection_pairs(
                b, pts, self.ui.ctx['out_bbox'])
            pairs.sort(key=lambda x: self.ui.router.euclidean_dist(x[0], x[1]))
            
            for start, end in pairs:
                start, end = tuple(start), tuple(end)
                self.ui.ctx['out_backups_ordered'].append(end)
                self.ui.ctx['out_backups_grouped'][b].append(end)
                
                path = self.ui.router.route_single_net(
                    start, end, self.ui.ctx['current_net_id'],
                    restrict_to_bbox=self.ui.ctx['out_bbox'],
                    all_terminals=all_terminals)
                
                if path:
                    self.ui.ctx['internal_paths'].append(path)
                else:
                    self.ui.log(f"  Out routing failed: {start}->{end}", 'WARNING')
                
                self.ui.ctx['current_net_id'] += 1
        
        self.ui.stage1_time = time.time() - self.ui.stage_start_time
        self.ui.log(f"Stage 1 completed, generated {len(self.ui.ctx['out_backups_ordered'])} Out backup points",
                'SUCCESS')
        self.ui.log(f"[Timing] Stage 1 Out internal routing time: {format_time(self.ui.stage1_time)}",
                'TIMING')
        
        timer_var = self.ui.control_panel.get_widget('timer_var')
        timer_var.set(f"⏱️ Stage 1 time: {format_time(self.ui.stage1_time)}")
        
        self.ui._plot_base_grid(
            title=f"Region {self.ui.task_count} - Stage 1 Complete (Out Internal)",
            out_backups=self.ui.ctx['out_backups_ordered'],
            out_points=self.ui.valid_out,
            current_paths=self.ui.ctx['internal_paths'],
            show_region=True
        )
        
        stage_var = self.ui.control_panel.get_widget('stage_var')
        stage_var.set("✅ Stage 1 Complete")
        self.ui._show_stage_complete_buttons()
