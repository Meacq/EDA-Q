"""
main_window.py - Main window controller
Main window controller is responsible for coordinating all user interface components and routing logic.
Manages application state, file operations, and three-stage routing process.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pandas as pd
import os
import time
import copy
import numpy as np
from datetime import datetime
from matplotlib.path import Path

from .styles import setup_styles
from .control_panel import ControlPanel
from .canvas_area import CanvasArea
from .log_panel import LogPanel
from .dialogs import (
    ParallelStrategyDialog,
    LShapedStrategyDialog,
    SnapshotListDialog,
    RoutingConfigDialog,
    show_help_dialog,
    show_about_dialog
)
from .gds_function_dialogs import (
    show_gds_extraction_dialog,
    show_path_export_dialog
)

from ..core import GridManager, AdvancedRouter
from ..managers import StateManager, GlobalSnapshotManager, PersistenceManager
from ..utils.logger import LogManager
from ..utils.helpers import format_time, find_backup_point_index, determine_boundary_for_points
from ..routing.boundary_utils import (
    check_parallel_boundaries,
    check_L_shaped_boundaries,
    create_parallel_pairs,
    create_L_shaped_pairs,
    auto_match_boundary_groups
)
from ..config.ui_config import UI_COLORS
from ..config.constants import VERSION, APP_TITLE
from photonic_routing.config.paths import INPUT_DIR, INPUT_CSV_DIR, ROUTING_DIR, FIGURES_DIR

class RoutingSystemUI:
    """Main window class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} v{VERSION}")
        
        # Setup window
        self._setup_window()
        
        # Initialize data
        self._init_data()
        
        # Initialize managers
        self._init_managers()

        self._init_stage_controllers()  # ← Add this line        
        
        # Create UI
        setup_styles()
        self._create_ui()
        
        # Start log update
        self._start_log_update()
        
        self.log("System startup complete", 'SUCCESS')
        from ..config.constants import NUMBA_AVAILABLE
        if NUMBA_AVAILABLE:
            self.log("Numba JIT acceleration enabled", 'SUCCESS')
        else:
            self.log("Numba not installed, using pure Python implementation", 'WARNING')

    def _init_stage_controllers(self):
        """Initialize stage controllers"""
        from ..routing.stage1 import Stage1Controller
        from ..routing.stage2 import Stage2Controller
        from ..routing.stage3 import Stage3Controller
        
        self.stage1_ctrl = Stage1Controller(self)
        self.stage2_ctrl = Stage2Controller(self)
        self.stage3_ctrl = Stage3Controller(self)

    def execute_stage1_auto(self):
        """Execute stage 1 auto mode"""
        self.stage1_ctrl.execute_auto()
    
    def start_stage1_manual(self):
        """Start stage 1 manual mode"""
        self.stage1_ctrl.start_manual()
    
    def execute_stage2_auto(self):
        """Execute stage 2 auto mode"""
        self.stage2_ctrl.execute_auto()
    
    def start_stage2_manual(self):
        """Start stage 2 manual mode"""
        self.stage2_ctrl.start_manual()
    
    def execute_stage3_auto(self):
        """Execute stage 3 auto mode"""
        self.stage3_ctrl.execute_auto()
    
    def start_stage3_manual(self):
        """Start stage 3 manual mode"""
        self.stage3_ctrl.start_manual()
    
    def continue_auto_next_group(self):
        """Continue processing next auto group"""
        self.current_auto_group_index += 1
        auto_group_frame = self.control_panel.get_widget('auto_group_frame')
        auto_group_frame.pack_forget()
        self.stage3_ctrl.process_auto_group()
    
    def skip_auto_remaining_groups(self):
        """Skip remaining auto groups"""
        self.log("Skipped remaining groups")
        self.skip_remaining_groups = True
        auto_group_frame = self.control_panel.get_widget('auto_group_frame')
        auto_group_frame.pack_forget()
        self.stage3_ctrl.finish()
    
    # ===========================
    # Boundary selection related methods
    # ===========================
    
    def start_boundary_direction_selection(self):
        """Start boundary selection for one direction"""
        if self.boundary_direction_index >= len(self.boundary_directions):
            self.finish_boundary_assignment()
            return
        
        direction = self.boundary_directions[self.boundary_direction_index]
        self.current_boundary_direction = direction
        
        assigned = [p for pts in self.boundary_assignments.values() for p in pts]
        available = [p for p in self.boundary_points_pool 
                    if not any(np.array_equal(p, a) for a in assigned)]
        
        if len(available) == 0:
            self.log(f"[{direction}] No available points, skipping")
            self.boundary_direction_index += 1
            self.start_boundary_direction_selection()
            return
        
        self.boundary_available_points = available
        self.selected_boundary_points = []
        self.boundary_assigner_active = True
        
        self.control_panel.hide_all_dynamic_frames()
        boundary_frame = self.control_panel.get_widget('boundary_frame')
        boundary_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        
        boundary_label = self.control_panel.get_widget('boundary_label')
        boundary_label.config(
            text=f"Please select {self.boundary_point_type} points belonging to [{direction} boundary]\n"
                 f"Left click to select | Right click drag to box select\n"
                 f"Ctrl+Z to undo | Click confirm when done")
        
        btn_boundary_confirm = self.control_panel.get_widget('btn_boundary_confirm')
        btn_boundary_undo = self.control_panel.get_widget('btn_boundary_undo')
        btn_boundary_confirm.pack(fill=tk.X, pady=4)
        btn_boundary_undo.pack(fill=tk.X, pady=4)
        
        self.canvas_area.plot_boundary_selection(
            self.grid_mgr, direction, available, 
            self.boundary_bbox, self.selected_boundary_points
        )
        
        # Create box selector
        self.canvas_area.setup_rect_selector(self.on_rect_select)
        
        self.update_status(f"Select points belonging to [{direction} boundary]")
        self.log(f">>> Please select points to assign to [{direction}]")
        self.log(f">>> Left click to select single point | Right click drag to box select multiple points")
        self.log(f">>> Ctrl+Z to undo | Enter or click confirm button to finish")
    
    def on_rect_select(self, eclick, erelease):
        """Rectangle box selection event"""
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        
        if x1 is None or y1 is None or x2 is None or y2 is None:
            return
        
        xmin_sel = min(x1, x2)
        xmax_sel = max(x1, x2)
        ymin_sel = min(y1, y2)
        ymax_sel = max(y1, y2)
        
        count_added = 0
        avail = np.array(self.boundary_available_points)
        for pt in avail:
            if xmin_sel <= pt[0] <= xmax_sel and ymin_sel <= pt[1] <= ymax_sel:
                if not any(np.array_equal(pt, p) for p in self.selected_boundary_points):
                    self.selected_boundary_points.append(pt)
                    count_added += 1
        
        if count_added > 0:
            self.log(f"  [Box select] Selected {count_added} points - "
                    f"Total {len(self.selected_boundary_points)} points")
            self.canvas_area.update_selected_points_display(self.selected_boundary_points)
    
    def on_canvas_click(self, event):
        """Canvas click event"""
        if not self.boundary_assigner_active:
            return
        
        if event.button != 1 or event.inaxes != self.canvas_area.ax:
            return
        
        cx, cy = event.xdata, event.ydata
        if cx is None or cy is None:
            return
        
        avail = np.array(self.boundary_available_points)
        dists = np.sqrt((avail[:, 0] - cx)**2 + (avail[:, 1] - cy)**2)
        idx = np.argmin(dists)
        
        if dists[idx] < 3.0:
            pt = self.boundary_available_points[idx]
            if not any(np.array_equal(pt, p) for p in self.selected_boundary_points):
                self.selected_boundary_points.append(pt)
                self.log(f"  [Click] Selected point ({pt[0]}, {pt[1]}) - "
                        f"Total {len(self.selected_boundary_points)} points")
                self.canvas_area.update_selected_points_display(self.selected_boundary_points)
    
    def on_canvas_key(self, event):
        """Canvas key press event"""
        if event.key == 'ctrl+z' and self.boundary_assigner_active:
            self.undo_boundary_point()
        elif event.key == 'enter' and self.boundary_assigner_active:
            self.confirm_boundary_selection()
    
    def undo_boundary_point(self):
        """Undo last selected point"""
        if self.selected_boundary_points:
            removed = self.selected_boundary_points.pop()
            self.log(f"  [Undo] Removed point ({removed[0]}, {removed[1]}) - "
                    f"Remaining {len(self.selected_boundary_points)} points")
            self.canvas_area.update_selected_points_display(self.selected_boundary_points)
        else:
            self.log("  Hint: No points to undo")
    
    def confirm_boundary_selection(self):
        """Confirm current boundary selection"""
        direction = self.current_boundary_direction
        
        if len(self.selected_boundary_points) == 0:
            self.log(f"[{direction}] No points selected")
        else:
            self.log(f"[{direction}] Confirmed selection of {len(self.selected_boundary_points)} points",
                    'SUCCESS')
            self.boundary_assignments[direction].extend(self.selected_boundary_points)
        
        self.boundary_assigner_active = False
        self.canvas_area.clear_selectors()
        
        self.boundary_direction_index += 1
        self.start_boundary_direction_selection()
    
    def finish_boundary_assignment(self):
        """Complete boundary assignment (modified version: only process user-selected points)"""
        self.boundary_assigner_active = False
        boundary_frame = self.control_panel.get_widget('boundary_frame')
        boundary_frame.pack_forget()
        
        # New logic: only use user-selected points, do not auto-assign unselected points
        assigned_set = set(tuple(p) for pts in self.boundary_assignments.values() for p in pts)
        unassigned_count = len(self.boundary_points_pool) - len(assigned_set)
        
        # Record user's actually selected points
        if self.current_stage == 1:
            # Stage 1: Record selected Out points
            self.ctx['out_boundary_map'] = self.boundary_assignments
            self.ctx['selected_out_points'] = assigned_set.copy()
            
            # Log hint
            if unassigned_count > 0:
                self.log(f"✓ Manual mode: Selected {len(assigned_set)} Out points", 'SUCCESS')
                self.log(f"⚠ Unassigned {unassigned_count} Out points (these will be ignored)", 'WARNING')
            else:
                self.log(f"✓ Manual mode: Selected all {len(assigned_set)} Out points", 'SUCCESS')
            
            self.stage1_ctrl.execute_routing()
            
        elif self.current_stage == 2:
            # Stage 2: Record selected Center points
            self.ctx['center_boundary_map'] = self.boundary_assignments
            self.ctx['selected_center_points'] = assigned_set.copy()
            
            # Log hint
            if unassigned_count > 0:
                self.log(f"✓ Manual mode: Selected {len(assigned_set)} Center points", 'SUCCESS')
                self.log(f"⚠ Unassigned {unassigned_count} Center points (these will be ignored)", 'WARNING')
            else:
                self.log(f"✓ Manual mode: Selected all {len(assigned_set)} Center points", 'SUCCESS')
            
            self.stage2_ctrl.execute_routing()
    
    # ===========================
    # Manual external connection related methods
    # ===========================
    
    def show_manual_group_input(self):
        """Show manual input interface"""
        if self.current_manual_group >= self.total_manual_groups:
            self.stage3_ctrl.finish()
            return
        
        self.control_panel.hide_all_dynamic_frames()
        manual_external_frame = self.control_panel.get_widget('manual_external_frame')
        manual_external_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        
        manual_group_label = self.control_panel.get_widget('manual_group_label')
        manual_group_label.config(
            text=f"📝 Group {self.current_manual_group+1}/{self.total_manual_groups}")
        
        entry_center_ids = self.control_panel.get_widget('entry_center_ids')
        entry_out_ids = self.control_panel.get_widget('entry_out_ids')
        entry_center_ids.delete(0, tk.END)
        entry_out_ids.delete(0, tk.END)
        
        stage_var = self.control_panel.get_widget('stage_var')
        stage_var.set(f"✋ Manual connection - Group {self.current_manual_group+1}/"
                     f"{self.total_manual_groups}")
        self.log(f"\n--- Group {self.current_manual_group+1}/{self.total_manual_groups} ---")
    
    def add_manual_group(self):
        """Add a manual connection group"""
        entry_center_ids = self.control_panel.get_widget('entry_center_ids')
        entry_out_ids = self.control_panel.get_widget('entry_out_ids')
        
        center_input = entry_center_ids.get().strip()
        out_input = entry_out_ids.get().strip()
        
        if not center_input or not out_input:
            self.log("[Error] Input cannot be empty, please re-enter this group.", 'ERROR')
            messagebox.showwarning("Warning", "Please enter Center and Out backup point numbers")
            return
        
        try:
            c_idxs = [int(x)-1 for x in center_input.split()]
            o_idxs = [int(x)-1 for x in out_input.split()]
        except ValueError:
            self.log("[Error] Input format error, please enter numbers separated by spaces.", 'ERROR')
            messagebox.showerror("Error", "Input format error, please enter numbers separated by spaces")
            return
        
        # Check index range
        if any(i < 0 or i >= len(self.ctx['center_backups_ordered']) for i in c_idxs):
            self.log(f"[Error] Center backup point number out of range "
                    f"(1-{len(self.ctx['center_backups_ordered'])})", 'ERROR')
            messagebox.showerror("Error",
                               f"Center number out of range (1-{len(self.ctx['center_backups_ordered'])})")
            return
        if any(i < 0 or i >= len(self.ctx['out_backups_ordered']) for i in o_idxs):
            self.log(f"[Error] Out backup point number out of range "
                    f"(1-{len(self.ctx['out_backups_ordered'])})", 'ERROR')
            messagebox.showerror("Error",
                               f"Out number out of range (1-{len(self.ctx['out_backups_ordered'])})")
            return
        
        curr_Starts = [self.ctx['center_backups_ordered'][i] for i in c_idxs]
        curr_Ends = [self.ctx['out_backups_ordered'][i] for i in o_idxs]
        
        # Check if counts match
        if len(curr_Starts) != len(curr_Ends):
            self.log(f"[Warning] Count mismatch! Center: {len(curr_Starts)} points, "
                    f"Out: {len(curr_Ends)} points", 'WARNING')
            result = messagebox.askyesno("Count Mismatch",
                                         f"Center: {len(curr_Starts)} points, "
                                         f"Out: {len(curr_Ends)} points\n"
                                         f"Count mismatch!\n\n"
                                         f"Click 'Yes' to re-enter this group\n"
                                         f"Click 'No' to skip this group")
            if result:
                return
            else:
                self.skip_manual_group()
                return
        
        group_start_time = time.time()
        
        # Detect boundary type and generate point pairs
        ck = determine_boundary_for_points(curr_Starts, self.ctx['center_backups_grouped'])
        ok = determine_boundary_for_points(curr_Ends, self.ctx['out_backups_grouped'])
        
        if ck and ok:
            self.log(f"  [Detection] Center points mainly located on [{ck}] boundary, "
                    f"Out points mainly located on [{ok}] boundary")
            pairs = self.stage3_ctrl.process_boundary_routing(curr_Starts, curr_Ends, ck, ok)
        else:
            self.log("  [Hint] Cannot determine boundary type, map directly in input order")
            pairs = []
            for i in range(len(curr_Starts)):
                pairs.append({'start': curr_Starts[i], 'end': curr_Ends[i]})
        
        if not pairs:
            self.current_manual_group += 1
            if self.current_manual_group < self.total_manual_groups:
                self.show_manual_group_input()
            else:
                self.stage3_ctrl.finish()
            return
        
        # Execute routing
        all_terminals = set(tuple(p) for p in self.ctx['center_backups_ordered']) | \
                       set(tuple(p) for p in self.ctx['out_backups_ordered'])
        
        group_success = 0
        group_fail = 0
        
        for pair_idx, p in enumerate(pairs):
            s, e = tuple(p['start']), tuple(p['end'])
            c_idx = find_backup_point_index(s, self.ctx['center_backups_ordered'])
            o_idx = find_backup_point_index(e, self.ctx['out_backups_ordered'])
            
            self.log(f"    [{pair_idx+1}/{len(pairs)}] Routing: "
                    f"Center #{c_idx} -> Out #{o_idx} ...", 'PROGRESS')
            
            path = self.router.route_single_net(
                s, e, self.ctx['current_net_id'],
                restrict_to_bbox=None,
                all_terminals=all_terminals,
                restrict_poly_path=self.poly_path)
            
            if path:
                self.ctx['external_paths'].append(path)
                group_success += 1
                self.log(f"        ✓ Success", 'SUCCESS')
            else:
                self.log(f"        ✗ Failed (coordinates: {s}->{e})", 'WARNING')
                group_fail += 1
            
            self.ctx['current_net_id'] += 1
        
        group_time = time.time() - group_start_time
        self.current_manual_group += 1
        self.log(f"  Group {self.current_manual_group} routing complete: "
                f"Success {group_success}, Failed {group_fail}",
                'SUCCESS' if group_fail == 0 else 'WARNING')
        self.log(f"  [Timing] Group {self.current_manual_group} routing time: "
                f"{format_time(group_time)}", 'TIMING')
        
        # Update display
        full_paths = self.ctx['internal_paths'] + self.ctx['external_paths']
        self._plot_base_grid(
            title=f"Area {self.task_count} - External routing progress "
                  f"(Group {self.current_manual_group}/{self.total_manual_groups} completed)",
            center_backups=self.ctx['center_backups_ordered'],
            out_backups=self.ctx['out_backups_ordered'],
            out_points=self.valid_out,
            current_paths=full_paths,
            show_region=True
        )
        
        # Continue next group or finish
        if self.current_manual_group < self.total_manual_groups:
            cont = messagebox.askyesno("Continue", 
                                       f"Group {self.current_manual_group} completed\n"
                                       f"✓ Success: {group_success}, ✗ Failed: {group_fail}\n"
                                       f"⏱️ Time: {format_time(group_time)}\n\n"
                                       f"Continue to next group?")
            if cont:
                self.show_manual_group_input()
            else:
                self.stage3_ctrl.finish()
        else:
            self.stage3_ctrl.finish()
    
    def skip_manual_group(self):
        """Skip current manual group"""
        self.log(f"Skipped group {self.current_manual_group+1}")
        self.current_manual_group += 1
        
        if self.current_manual_group < self.total_manual_groups:
            self.show_manual_group_input()
        else:
            self.stage3_ctrl.finish()
    
    # ===========================
    # Backup point numbering print
    # ===========================
    
    def show_backup_points_summary(self):
        """Show backup point numbering summary"""
        if self.ctx is None or not self.ctx.get('center_backups_ordered') or not self.ctx.get('out_backups_ordered'):
            messagebox.showwarning("Warning", "No available backup point data\nPlease complete stage 1 and stage 2 first")
            return
        
        # Create print order selection dialog
        self._show_print_order_dialog()
    
    def _show_print_order_dialog(self):
        """Show print order selection dialog"""
        from ..utils.helpers import center_window_right
        
        order_window = tk.Toplevel(self.root)
        order_window.title("Select Print Order")
        order_window.geometry("600x750")
        order_window.configure(bg=UI_COLORS['bg_panel'])
        order_window.transient(self.root)
        order_window.grab_set()
        
        center_window_right(order_window, self.root)
        
        # ... (Dialog content implementation)
        self._create_print_order_dialog_content(order_window)
    
    def _create_print_order_dialog_content(self, window):
        """Create print order dialog content - fixed version"""
        # Title
        title_frame = tk.Frame(window, bg=UI_COLORS['primary'], height=70)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="📋 Backup Point Numbering Print Order Settings",
                font=('Microsoft YaHei', 16, 'bold'),
                wraplength=700,
                justify=tk.CENTER,
                fg='white', bg=UI_COLORS['primary']).pack(expand=True, pady=18)
        
        # Main content area
        content_frame = tk.Frame(window, bg=UI_COLORS['bg_panel'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # Information
        info_box = tk.Frame(content_frame, bg=UI_COLORS['primary_light'], relief=tk.FLAT, bd=1)
        info_box.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(info_box,
                text="Please select the print order for backup point numbering\nThis will affect the arrangement of backup points in the log",
                font=('Microsoft YaHei', 12),
                wraplength=700,
                fg=UI_COLORS['text_secondary'],
                bg=UI_COLORS['primary_light'],
                justify=tk.LEFT,
                padx=15,
                pady=12).pack(fill=tk.X)
        
        # Horizontal boundary order
        h_frame = ttk.LabelFrame(content_frame, text="Horizontal Boundary (Top/Bottom) Print Order",
                                style='Card.TLabelframe', padding=20)
        h_frame.pack(fill=tk.X, pady=(0, 15))
        
        h_var = tk.StringVar(value=self.h_print_order)
        
        tk.Radiobutton(h_frame, text="Left to Right →",
                    variable=h_var, value='left_to_right',
                    bg=UI_COLORS['bg_panel'],
                    fg=UI_COLORS['text_primary'],
                    font=('Microsoft YaHei', 13),
                    selectcolor=UI_COLORS['primary_light'],
                    activebackground=UI_COLORS['bg_panel']).pack(anchor=tk.W, pady=5)
        
        tk.Radiobutton(h_frame, text="Right to Left ←",
                    variable=h_var, value='right_to_left',
                    bg=UI_COLORS['bg_panel'],
                    fg=UI_COLORS['text_primary'],
                    font=('Microsoft YaHei', 13),
                    selectcolor=UI_COLORS['primary_light'],
                    activebackground=UI_COLORS['bg_panel']).pack(anchor=tk.W, pady=5)
        
        # Vertical boundary order
        v_frame = ttk.LabelFrame(content_frame, text="Vertical Boundary (Left/Right) Print Order",
                                style='Card.TLabelframe', padding=20)
        v_frame.pack(fill=tk.X)
        
        v_var = tk.StringVar(value=self.v_print_order)
        
        tk.Radiobutton(v_frame, text="Top to Bottom ↓",
                    variable=v_var, value='top_to_bottom',
                    bg=UI_COLORS['bg_panel'],
                    fg=UI_COLORS['text_primary'],
                    font=('Microsoft YaHei', 13),
                    selectcolor=UI_COLORS['primary_light'],
                    activebackground=UI_COLORS['bg_panel']).pack(anchor=tk.W, pady=5)
        
        tk.Radiobutton(v_frame, text="Bottom to Top ↑",
                    variable=v_var, value='bottom_to_top',
                    bg=UI_COLORS['bg_panel'],
                    fg=UI_COLORS['text_primary'],
                    font=('Microsoft YaHei', 13),
                    selectcolor=UI_COLORS['primary_light'],
                    activebackground=UI_COLORS['bg_panel']).pack(anchor=tk.W, pady=5)
        
        # 🔴 Fix: Button area - use centered layout to ensure buttons are visible
        btn_frame = tk.Frame(window, bg=UI_COLORS['bg_panel'])
        btn_frame.pack(fill=tk.X, padx=25, pady=(10, 20))  # Add top/bottom margins
        
        def do_print():
            """Execute print"""
            # Save selection
            self.h_print_order = h_var.get()
            self.v_print_order = v_var.get()
            
            # Close window
            window.destroy()
            
            # Execute print
            self._print_backup_points()
        
        def do_cancel():
            """Cancel"""
            window.destroy()
        
        # Create centered container to ensure buttons are visible
        btn_container = tk.Frame(btn_frame, bg=UI_COLORS['bg_panel'])
        btn_container.pack(anchor=tk.CENTER)
        
        # Confirm button
        tk.Button(btn_container, text="✓ Confirm and Print",
                command=do_print,
                font=('Microsoft YaHei', 14, 'bold'),
                bg=UI_COLORS['primary'],
                fg='white',
                activebackground=UI_COLORS['primary_dark'],
                activeforeground='white',
                relief=tk.FLAT,
                cursor='hand2',
                padx=30, pady=12).pack(side=tk.LEFT, padx=(0, 10))
        
        # Cancel button
        tk.Button(btn_container, text="✗ Cancel",
                command=do_cancel,
                font=('Microsoft YaHei', 14, 'bold'),
                bg=UI_COLORS['text_light'],
                fg='white',
                activebackground=UI_COLORS['text_secondary'],
                activeforeground='white',
                relief=tk.FLAT,
                cursor='hand2',
                padx=30, pady=12).pack(side=tk.LEFT)


    def _print_backup_points(self):
        """Execute backup point numbering print"""
        from ..routing.boundary_utils import is_horizontal_boundary
        
        h_order_desc = "Left to Right" if self.h_print_order == 'left_to_right' else "Right to Left"
        v_order_desc = "Top to Bottom" if self.v_print_order == 'top_to_bottom' else "Bottom to Top"
        
        self.log("="*50)
        self.log("[Backup Point Numbering Summary] - For external routing manual mode group filling", 'SUCCESS')
        self.log("="*50)
        self.log(f"Horizontal boundaries print in [{h_order_desc}] order")
        self.log(f"Vertical boundaries print in [{v_order_desc}] order")
        self.log("-"*50)
        
        horizontal_boundaries = ['Top', 'Bottom']
        vertical_boundaries = ['Left', 'Right']

        # Print Center backup points
        self.log("[Center Backup Point Numbering]", 'SUCCESS')
        for boundary in ['Top', 'Bottom', 'Left', 'Right']:
            pts = self.ctx['center_backups_grouped'].get(boundary, [])
            if len(pts) == 0:
                continue
            
            indexed_pts = []
            for pt in pts:
                idx = find_backup_point_index(pt, self.ctx['center_backups_ordered'])
                if idx != "Unknown":
                    indexed_pts.append({'index': int(idx), 'point': pt})
            
            if len(indexed_pts) == 0:
                continue
            
            if boundary in horizontal_boundaries:
                if self.h_print_order == 'left_to_right':
                    indexed_pts.sort(key=lambda x: x['point'][0])
                else:
                    indexed_pts.sort(key=lambda x: x['point'][0], reverse=True)
                order_desc = h_order_desc
            else:
                if self.v_print_order == 'top_to_bottom':
                    indexed_pts.sort(key=lambda x: x['point'][1], reverse=True)
                else:
                    indexed_pts.sort(key=lambda x: x['point'][1])
                order_desc = v_order_desc
            
            sorted_indices = [str(p['index']) for p in indexed_pts]
            self.log(f"  [{boundary} boundary] ({order_desc}, total {len(sorted_indices)}):")
            self.log(f"    Numbers: {' '.join(sorted_indices)}")
        
        # Print Out backup points
        self.log("[Out Backup Point Numbering]", 'SUCCESS')
        for boundary in ['Top', 'Bottom', 'Left', 'Right']:
            pts = self.ctx['out_backups_grouped'].get(boundary, [])
            if len(pts) == 0:
                continue
            
            indexed_pts = []
            for pt in pts:
                idx = find_backup_point_index(pt, self.ctx['out_backups_ordered'])
                if idx != "Unknown":
                    indexed_pts.append({'index': int(idx), 'point': pt})
            
            if len(indexed_pts) == 0:
                continue
            
            if boundary in horizontal_boundaries:
                if self.h_print_order == 'left_to_right':
                    indexed_pts.sort(key=lambda x: x['point'][0])
                else:
                    indexed_pts.sort(key=lambda x: x['point'][0], reverse=True)
                order_desc = h_order_desc
            else:
                if self.v_print_order == 'top_to_bottom':
                    indexed_pts.sort(key=lambda x: x['point'][1], reverse=True)
                else:
                    indexed_pts.sort(key=lambda x: x['point'][1])
                order_desc = v_order_desc
            
            sorted_indices = [str(p['index']) for p in indexed_pts]
            self.log(f"  [{boundary} boundary] ({order_desc}, total {len(sorted_indices)}):")
            self.log(f"    Numbers: {' '.join(sorted_indices)}")
        
        self.log("="*50)
        self.log("💡 Hint: Above numbers can be copied directly for manual mode group input")
        self.log("="*50)
    
    def ask_save_figure(self, suffix):
        """Ask whether to save figure"""
        result = messagebox.askyesno("Save Figure",
                                     f"Save current [{suffix}] figure?")
        if result:
            default_name = f"result_Region{self.task_count}_{suffix}.png"
            file_path = filedialog.asksaveasfilename(
                title="Save Figure",
                initialfile=default_name,
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png")]
            )
            if file_path:
                try:
                    self.canvas_area.fig.savefig(file_path, dpi=300, bbox_inches='tight',
                                   facecolor='white')
                    self.log(f"Figure saved as {os.path.basename(file_path)}", 'SUCCESS')
                except Exception as e:
                    self.log(f"Save failed: {e}", 'ERROR')


    def _setup_window(self):
        """Setup window"""
        self.root.configure(bg=UI_COLORS['bg_main'])
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = min(1920, int(screen_width * 0.95))
        window_height = min(1080, int(screen_height * 0.9))
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def _init_data(self):
        """Initialize data"""
        # Core data
        self.grid_mgr = None
        self.router = None
        self.all_finished_paths = []
        self.task_count = 1
        self.total_connected_centers = 0
        self.routing_config = {}  # User configured routing parameters
        
        # Region selection related
        self.poly_path = None
        self.selected_vertices = []
        self.valid_out = None
        self.valid_center = None
        self.out_groups = {}
        self.force_manual = False
        
        # Current stage context
        self.ctx = None
        self.current_stage = 0
        
        # Timing related
        self.region_start_time = None
        self.stage_start_time = None
        self.stage1_time = 0
        self.stage2_time = 0
        self.stage3_time = 0
        
        # Boundary assigner related
        self.boundary_assigner_active = False
        self.boundary_assignments = {}
        self.current_boundary_direction = None
        self.selected_boundary_points = []
        self.boundary_available_points = []
        self.boundary_directions = []
        self.boundary_direction_index = 0
        self.boundary_points_pool = []
        self.boundary_point_type = ''
        self.boundary_bbox = None
        
        # Stage 3 auto mode related
        self.auto_matches = []
        self.current_auto_group_index = 0
        self.skip_remaining_groups = False
        
        # Stage 3 manual mode related
        self.total_manual_groups = 0
        self.current_manual_group = 0
        
        # Backup point print order settings
        self.h_print_order = 'left_to_right'
        self.v_print_order = 'top_to_bottom'
    
    def _init_managers(self):
        """Initialize managers"""
        self.state_mgr = StateManager()
        self.snapshot_mgr = GlobalSnapshotManager()
        self.persistence_mgr = PersistenceManager()
        self.log_mgr = LogManager()
    
    def _create_ui(self):
        """Create UI"""
        # Create menu
        self._create_menu()
        
        # Main layout
        self._create_main_layout()
        
        # Status bar
        self._create_status_bar()
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root, bg=UI_COLORS['bg_panel'], fg=UI_COLORS['text_primary'])
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=UI_COLORS['bg_panel'], 
                           fg=UI_COLORS['text_primary'])
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import CSV Data...", command=self.load_csv, 
                             accelerator="Ctrl+O")
        file_menu.add_command(label="Load Routing Data (.pkl)...", command=self.load_routing_data,
                             accelerator="Ctrl+L")
        file_menu.add_separator()
        file_menu.add_command(label="Save Routing Data", command=self.save_routing_data, 
                             accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_as_routing_data)
        file_menu.add_separator()
        file_menu.add_command(label="Export Image...", command=self.export_image,
                             accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit,
                             accelerator="Ctrl+Q")
        
        # Routing menu
        routing_menu = tk.Menu(menubar, tearoff=0, bg=UI_COLORS['bg_panel'],
                              fg=UI_COLORS['text_primary'])
        menubar.add_cascade(label="Routing", menu=routing_menu)
        routing_menu.add_command(label="Start New Region", command=self.start_new_region,
                                accelerator="Ctrl+N")
        routing_menu.add_separator()
        routing_menu.add_command(label="Print Backup Point Numbers", command=self.show_backup_points_summary)
        routing_menu.add_separator()
        routing_menu.add_command(label="View Snapshot List", command=self.view_snapshots,
                                accelerator="Ctrl+H")
        routing_menu.add_command(label="Switch to Snapshot...", command=self.switch_to_snapshot,
                                accelerator="Ctrl+T")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0, bg=UI_COLORS['bg_panel'],
                           fg=UI_COLORS['text_primary'])
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh Canvas", command=self.refresh_canvas,
                             accelerator="F5")
        view_menu.add_command(label="Clear Log", command=self.clear_log)

        # Function menu
        function_menu = tk.Menu(menubar, tearoff=0, bg=UI_COLORS['bg_panel'],
                               fg=UI_COLORS['text_primary'])
        menubar.add_cascade(label="Function", menu=function_menu)
        function_menu.add_command(label="GDS Coordinate Extraction Tool",
                                 command=lambda: show_gds_extraction_dialog(self.root))
        function_menu.add_command(label="Path Export and Merge Tool",
                                 command=lambda: show_path_export_dialog(self.root))

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=UI_COLORS['bg_panel'],
                           fg=UI_COLORS['text_primary'])
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Manual", command=lambda: show_help_dialog(self.root),
                             accelerator="F1")
        help_menu.add_command(label="Shortcut List", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=lambda: show_about_dialog(self.root))
        
        # Bind shortcuts
        self._bind_shortcuts()
    
    def _bind_shortcuts(self):
        """Bind shortcuts"""
        self.root.bind('<Control-o>', lambda e: self.load_csv())
        self.root.bind('<Control-l>', lambda e: self.load_routing_data())
        self.root.bind('<Control-s>', lambda e: self.save_routing_data())
        self.root.bind('<Control-e>', lambda e: self.export_image())
        self.root.bind('<Control-q>', lambda e: self.on_exit())
        self.root.bind('<Control-n>', lambda e: self.start_new_region())
        self.root.bind('<Control-h>', lambda e: self.view_snapshots())
        self.root.bind('<Control-t>', lambda e: self.switch_to_snapshot())
        self.root.bind('<F5>', lambda e: self.refresh_canvas())
        self.root.bind('<F1>', lambda e: show_help_dialog(self.root))
    
    def _create_main_layout(self):
        """Create main layout"""
        main_container = tk.Frame(self.root, bg=UI_COLORS['bg_main'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left control panel
        left_panel = tk.Frame(main_container, bg=UI_COLORS['bg_panel'], 
                            relief=tk.FLAT, bd=0, width=360)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        left_panel.pack_propagate(False)
        
        # Create control panel callbacks
        control_callbacks = {
            'start_new_region': self.start_new_region,
            'select_auto_mode': self.select_auto_mode,
            'select_manual_mode': self.select_manual_mode,
            'next_stage': self.next_stage,
            'retry_stage': self.retry_stage,
            'confirm_region': self.confirm_region,
            'confirm_boundary_selection': self.confirm_boundary_selection,
            'undo_boundary_point': self.undo_boundary_point,
            'continue_auto_next_group': self.continue_auto_next_group,
            'skip_auto_remaining_groups': self.skip_auto_remaining_groups,
            'add_manual_group': self.add_manual_group,
            'skip_manual_group': self.skip_manual_group,
            'view_snapshots': self.view_snapshots,
            'switch_to_snapshot': self.switch_to_snapshot,
        }
        self.control_panel = ControlPanel(left_panel, control_callbacks)
        
        # Separator
        separator = tk.Frame(main_container, bg=UI_COLORS['border'], width=2)
        separator.pack(side=tk.LEFT, fill=tk.Y)
        
        # Right container (canvas + log)
        right_container = tk.PanedWindow(main_container, 
                                        orient=tk.HORIZONTAL,
                                        sashwidth=8,
                                        sashrelief=tk.RAISED,
                                        bg=UI_COLORS['border'],
                                        bd=0,
                                        sashpad=2)
        right_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Center canvas area
        center_panel = tk.Frame(right_container, bg=UI_COLORS['bg_main'])
        right_container.add(center_panel, minsize=400, stretch='always')
        
        canvas_callbacks = {
            'on_canvas_click': self.on_canvas_click,
            'on_canvas_key': self.on_canvas_key,
        }
        self.canvas_area = CanvasArea(center_panel, canvas_callbacks)
        
        # Right log panel
        right_panel = tk.Frame(right_container, bg=UI_COLORS['bg_panel'],
                            relief=tk.FLAT, bd=0)
        right_container.add(right_panel, minsize=300, stretch='always')
        
        log_callbacks = {
            'clear_log': self.clear_log,
        }
        self.log_panel = LogPanel(right_panel, log_callbacks)
        
        # Set initial split position
        def set_initial_sash():
            try:
                total_width = right_container.winfo_width()
                if total_width > 100:
                    right_container.sashpos(0, int(total_width * 0.7))
            except:
                pass
        
        self.root.after(100, set_initial_sash)
    
    def _create_status_bar(self):
        """Create status bar"""
        status_bar = tk.Frame(self.root, relief=tk.FLAT, 
                            bg=UI_COLORS['primary_light'],
                            height=35)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        status_bar.pack_propagate(False)
        
        status_container = tk.Frame(status_bar, bg=UI_COLORS['primary_light'])
        status_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=6)
        
        # Left status (original code: 15, 'bold')
        self.status_label = tk.Label(status_container, text="✓ Ready",
                                    font=('Microsoft YaHei', 15, 'bold'),
                                    fg=UI_COLORS['text_primary'],
                                    bg=UI_COLORS['primary_light'])
        self.status_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Region count (original code: 15, 'bold')
        self.region_label = tk.Label(status_container, text="Region: 0",
                                    font=('Microsoft YaHei', 15, 'bold'),
                                    fg=UI_COLORS['text_secondary'],
                                    bg=UI_COLORS['primary_light'])
        self.region_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Path count (original code: 15, 'bold')
        self.path_label = tk.Label(status_container, text="Path: 0",
                                font=('Microsoft YaHei', 15, 'bold'),
                                fg=UI_COLORS['text_secondary'],
                                bg=UI_COLORS['primary_light'])
        self.path_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Right time (original code: 15, 'bold')
        self.time_label = tk.Label(status_container, text="",
                                font=('Microsoft YaHei', 15, 'bold'),
                                fg=UI_COLORS['text_light'],
                                bg=UI_COLORS['primary_light'])
        self.time_label.pack(side=tk.RIGHT)
        
        self._update_time()

    
    def _start_log_update(self):
        """Start log update"""
        self._update_log()
    
    def _update_log(self):
        """Update log display"""
        try:
            log_queue = self.log_mgr.get_log_queue()
            while not log_queue.empty():
                message, level = log_queue.get_nowait()
                self.log_panel.add_log(message, level)
        except:
            pass
        self.root.after(100, self._update_log)
    
    def _update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=f"🕐 {current_time}")
        self.root.after(1000, self._update_time)
    
    # Log methods
    def log(self, message, level='INFO'):
        """Add log"""
        self.log_mgr.log(message, level)
    
    def clear_log(self):
        """Clear log"""
        self.log_panel.clear()
        self.log("Log cleared", 'INFO')
    
    def update_status(self, text):
        """Update status bar"""
        self.status_label.config(text=f"✓ {text}")
    
    def update_data_info(self):
        """Update data information display"""
        if self.grid_mgr is None:
            return
        
        out_points = self.grid_mgr.get_points_by_type('out')
        center_points = self.grid_mgr.get_points_by_type('center')
        
        info = f"Total Out Points: {len(out_points)}\n"
        info += f"Total Center Points: {len(center_points)}\n"
        info += f"Grid Size: {self.grid_mgr.w} × {self.grid_mgr.h}\n"
        info += f"Completed Paths: {len(self.all_finished_paths)}\n"
        info += f"Current Region: {self.task_count}\n"
        info += f"Snapshot Count: {len(self.snapshot_mgr.snapshots)}\n"
        
        current_idx = self.snapshot_mgr.get_current_snapshot_index()
        if current_idx >= 0:
            info += f"Current Snapshot: #{current_idx + 1}"
        
        data_info_widget = self.control_panel.get_widget('data_info')
        data_info_widget.config(state='normal')
        data_info_widget.delete(1.0, tk.END)
        data_info_widget.insert(1.0, info)
        data_info_widget.config(state='disabled')
        
        self.region_label.config(text=f"Region: {self.task_count}")
        self.path_label.config(text=f"Paths: {len(self.all_finished_paths)}")
    
    def refresh_canvas(self):
        """Refresh canvas"""
        if self.grid_mgr:
            self._plot_base_grid()
            self.log("Canvas refreshed", 'INFO')
        else:
            self.log("No data to refresh", 'WARNING')
    
    def _plot_base_grid(self, **kwargs):
        """Plot base grid (internal method)"""
        # Automatically add grouped backup point dictionary (if exists)
        if 'center_backups_grouped' not in kwargs and self.ctx:
            kwargs['center_backups_grouped'] = self.ctx.get('center_backups_grouped')
        if 'out_backups_grouped' not in kwargs and self.ctx:
            kwargs['out_backups_grouped'] = self.ctx.get('out_backups_grouped')

        self.canvas_area.plot_base_grid(
            self.grid_mgr,
            self.all_finished_paths,
            poly_path=self.poly_path,
            selected_vertices=self.selected_vertices,
            **kwargs
        )
    
    def on_exit(self):
        """Exit program"""
        if self.router and len(self.all_finished_paths) > 0:
            result = messagebox.askyesnocancel("Exit", 
                                               "Save final routing data before exit?\n\n"
                                               "Yes - Save and exit\n"
                                               "No - Exit without saving\n"
                                               "Cancel - Return to program")
            if result is None:
                return
            elif result:
                self.save_routing_data()
        
        self.root.quit()
    # Continue adding methods in RoutingSystemUI class
    
    # ===========================
    # Data Loading and Saving
    # ===========================
    
    def load_csv(self):
        """Import CSV data"""
        file_path = filedialog.askopenfilename(
            title="Select CSV Data File",
            initialdir=INPUT_CSV_DIR,
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )

        if not file_path:
            return

        try:
            # Clean up large data structures from old instances
            if self.router:
                self.router.occupation_grid = None
                if hasattr(self.router, 'diagonal_bitmap'):
                    self.router.diagonal_bitmap.clear()
                    self.router.diagonal_bitmap = None
                if hasattr(self.router, 'global_reserved_points'):
                    self.router.global_reserved_points.clear()

            if self.snapshot_mgr:
                self.snapshot_mgr.clear()

            df = pd.read_csv(file_path)

            # Show parameter configuration dialog
            config_dialog = RoutingConfigDialog(self.root)
            config = config_dialog.show()

            if config is None:
                self.log("Parameter configuration cancelled, using default values", 'WARNING')
                from ..config.constants import DEFAULT_GRID_SIZE
                config = {'grid_size': DEFAULT_GRID_SIZE}

            # Save user configuration
            self.routing_config = config
            self.log(f"Routing parameters: Grid size={config['grid_size']}")

            self.grid_mgr = GridManager(df, grid_size=config['grid_size'])
            self.router = AdvancedRouter(self.grid_mgr)
            self.all_finished_paths = []
            self.task_count = 1
            self.total_connected_centers = 0
            self.snapshot_mgr = GlobalSnapshotManager()

            self.log(f"Successfully loaded: {os.path.basename(file_path)}", 'SUCCESS')
            self.log(f"Grid size: {self.grid_mgr.w} × {self.grid_mgr.h}")

            self.update_data_info()
            self._plot_base_grid()
            self.update_status("CSV data loading completed")

            stage_var = self.control_panel.get_widget('stage_var')
            stage_var.set("📥 Data loaded, waiting to start")

        except Exception as e:
            self.log(f"Loading failed: {str(e)}", 'ERROR')
            messagebox.showerror("Error", f"Data loading failed:\n{str(e)}")
    
    def load_routing_data(self):
        """Load routing data"""
        files = self.persistence_mgr.list_available_files()
        
        if not files:
            file_path = filedialog.askopenfilename(
                title="Select Routing Data File",
                initialdir=ROUTING_DIR,
                filetypes=[("Pickle Files", "*.pkl"), ("All Files", "*.*")]
            )
            if not file_path:
                messagebox.showinfo("Info", "No file selected, please import CSV data first")
                return
            selected_file = file_path
        else:
            selected_file = self._show_file_selection_dialog(files)
            if not selected_file:
                return
        
        try:
            loaded_data = self.persistence_mgr.load_from_file(selected_file)
            
            if self.grid_mgr is None:
                messagebox.showwarning("Warning", "Please import CSV data file first")
                return

            # Use saved configuration or default values
            self.router = AdvancedRouter(self.grid_mgr)
            self.router.occupation_grid = loaded_data['router_state']['occupation_grid']

            # Compatible with old version
            if 'diagonal_bitmap' in loaded_data['router_state']:
                self.router.diagonal_bitmap = loaded_data['router_state']['diagonal_bitmap']
            else:
                from ..core.data_structures import DiagonalBitmap
                self.router.diagonal_bitmap = DiagonalBitmap()

            # Note: spatial_hash is no longer used, ignore if present in old files

            self.router.global_reserved_points = loaded_data['router_state']['global_reserved_points']

            self.all_finished_paths = loaded_data['all_finished_paths']
            self.task_count = loaded_data['task_count'] + 1

            # Restore connected center point count (compatible with old version)
            self.total_connected_centers = loaded_data.get('total_connected_centers', 0)
            
            if 'snapshots' in loaded_data:
                self.snapshot_mgr.snapshots = loaded_data['snapshots']
            
            self.log(f"Data loaded successfully (saved at: {loaded_data['timestamp']})", 'SUCCESS')
            self.log(f"Completed paths: {len(self.all_finished_paths)}")
            self.log(f"Available snapshots: {len(self.snapshot_mgr.snapshots)}")
            self.log(f"Will start from region {self.task_count}")

            self.update_data_info()
            self._plot_base_grid()

            stage_var = self.control_panel.get_widget('stage_var')
            stage_var.set(f"📥 Loaded, starting from region {self.task_count}")

            # Show center point connection status popup
            self._show_center_connection_status()
            
        except Exception as e:
            self.log(f"Loading failed: {str(e)}", 'ERROR')
            messagebox.showerror("Error", f"Loading failed:\n{str(e)}")

    def _show_center_connection_status(self):
        """Show center point connection status popup"""
        if self.grid_mgr is None:
            return

        total_center = len(self.grid_mgr.get_points_by_type('center'))
        connected = self.total_connected_centers if self.total_connected_centers > 0 else len(self.all_finished_paths)
        remaining = total_center - connected

        message = (
            f"Center Point Connection Status\n\n"
            f"Total Center Points: {total_center}\n"
            f"Connected: {connected}\n"
            f"Remaining: {remaining}"
        )
        messagebox.showinfo("Routing Data Loading Completed", message)

    def _show_file_selection_dialog(self, files):
        """Show file selection dialog - Windows style intelligent sorting"""
        from ..utils.helpers import center_window_right, extract_region_number, format_file_size, natural_sort_key
        from datetime import datetime
        
        select_window = tk.Toplevel(self.root)
        select_window.title("Select File to Load")
        select_window.geometry("950x680")
        select_window.configure(bg=UI_COLORS['bg_panel'])
        select_window.transient(self.root)
        select_window.grab_set()
        
        center_window_right(select_window, self.root)
        
        # Title bar
        title_frame = tk.Frame(select_window, bg=UI_COLORS['primary'], height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_container = tk.Frame(title_frame, bg=UI_COLORS['primary'])
        title_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=12)
        
        tk.Label(title_container, text="💾 Select Routing Data to Load",
                font=('Microsoft YaHei', 14, 'bold'),
                fg='white', bg=UI_COLORS['primary']).pack(side=tk.LEFT)
        
        tk.Label(title_container, text=f"Total {len(files)} files",
                font=('Microsoft YaHei', 10),
                fg='#E8F4FD', bg=UI_COLORS['primary']).pack(side=tk.RIGHT)
        
        # Sort options area
        sort_frame = tk.Frame(select_window, bg=UI_COLORS['bg_panel'])
        sort_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # Left sort label
        sort_label_frame = tk.Frame(sort_frame, bg=UI_COLORS['bg_panel'])
        sort_label_frame.pack(side=tk.LEFT)
        
        tk.Label(sort_label_frame, text="📊 Sort by:",
                font=('Microsoft YaHei', 10, 'bold'),
                fg=UI_COLORS['text_primary'],
                bg=UI_COLORS['bg_panel']).pack(side=tk.LEFT, padx=(0, 15))
        
        sort_var = tk.StringVar(value="name_asc")
        
        # Windows style sort options
        sort_options = [
            ("Name ↑", "name_asc", "Sort by filename ascending (A-Z, 1-9)"),
            ("Name ↓", "name_desc", "Sort by filename descending (Z-A, 9-1)"),
            ("Modified ↓", "time_desc", "Most recently modified first"),
            ("Modified ↑", "time_asc", "Least recently modified first"),
            ("Size ↓", "size_desc", "Largest files first"),
            ("Size ↑", "size_asc", "Smallest files first"),
            ("Type", "type", "Sort by file type"),
        ]
        
        sort_buttons_frame = tk.Frame(sort_frame, bg=UI_COLORS['bg_panel'])
        sort_buttons_frame.pack(side=tk.LEFT)
        
        for text, value, tooltip in sort_options:
            rb = tk.Radiobutton(
                sort_buttons_frame, 
                text=text, 
                variable=sort_var, 
                value=value,
                bg=UI_COLORS['bg_panel'],
                fg=UI_COLORS['text_primary'],
                font=('Microsoft YaHei', 9),
                selectcolor=UI_COLORS['primary_light'],
                activebackground=UI_COLORS['bg_panel'],
                command=lambda: update_list()
            )
            rb.pack(side=tk.LEFT, padx=6)
        
        # Separator
        ttk.Separator(select_window, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Statistics bar
        stats_frame = tk.Frame(select_window, bg=UI_COLORS['primary_light'])
        stats_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        stats_label = tk.Label(stats_frame, text="",
                            font=('Microsoft YaHei', 9),
                            fg=UI_COLORS['text_secondary'],
                            bg=UI_COLORS['primary_light'],
                            anchor='w')
        stats_label.pack(fill=tk.X, padx=10, pady=6)
        
        # List area
        list_frame = tk.Frame(select_window, bg=UI_COLORS['bg_panel'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        # Create Treeview
        columns = ('filename', 'region', 'size', 'time', 'type')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configure column headers (support click to sort)
        tree.heading('filename', text='📄 Filename', anchor='w')
        tree.heading('region', text='🎯 Region', anchor='center')
        tree.heading('size', text='📦 Size', anchor='center')
        tree.heading('time', text='🕐 Modified', anchor='center')
        tree.heading('type', text='📋 Type', anchor='center')
        
        # Configure column widths
        tree.column('filename', width=320, anchor='w')
        tree.column('region', width=100, anchor='center')
        tree.column('size', width=120, anchor='center')
        tree.column('time', width=200, anchor='center')
        tree.column('type', width=80, anchor='center')
        
        # Add smart scroll wheel binding
        def on_tree_enter(event):
            """Bind scroll wheel when mouse enters Treeview"""
            tree.bind("<MouseWheel>", lambda e: tree.yview_scroll(int(-1*(e.delta/120)), "units"))

        def on_tree_leave(event):
            """Unbind scroll wheel when mouse leaves Treeview"""
            tree.unbind("<MouseWheel>")

        tree.bind("<Enter>", on_tree_enter)
        tree.bind("<Leave>", on_tree_leave)

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(xscrollcommand=h_scrollbar.set)
        
        tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        def get_file_type(filename):
            """Get file type description"""
            if filename.startswith('routing'):
                return "Routing"
            elif filename.startswith('backup'):
                return "Backup"
            elif filename.startswith('test'):
                return "Test"
            else:
                return "Data"
        
        def update_stats(file_data):
            """Update statistics information"""
            if not file_data:
                stats_label.config(text="No available files")
                return
            
            total_size = sum(d['size'] for d in file_data)
            total_size_str = format_file_size(total_size)
            
            # Statistics of region distribution
            regions = [d['region'] for d in file_data if d['region'] is not None]
            if regions:
                min_region = min(regions)
                max_region = max(regions)
                region_info = f"Region range: {min_region}-{max_region}"
            else:
                region_info = "No region information"
            
            stats_text = f"📊 {len(file_data)} files  |  💾 Total size: {total_size_str}  |  {region_info}"
            stats_label.config(text=stats_text)
        
        def update_list():
            """Update list display"""
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)
            
            # Prepare file information
            file_data = []
            for f in files:
                try:
                    # Use smart function to extract information
                    full_path = ROUTING_DIR / f
                    region_num = extract_region_number(f)
                    size_bytes = full_path.stat().st_size
                    mtime = full_path.stat().st_mtime
                    mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    file_type = get_file_type(f)
                    
                    file_data.append({
                        'filename': f,
                        'region': region_num,
                        'size': size_bytes,
                        'mtime': mtime,
                        'type': file_type,
                        'region_display': f"Region {region_num}" if region_num is not None else "-",
                        'size_display': format_file_size(size_bytes),
                        'time_display': mtime_str
                    })
                except Exception as e:
                    print(f"Error processing file {f}: {e}")
                    continue
            
            # Sort according to selected sort method
            sort_method = sort_var.get()
            
            if sort_method == "name_asc":
                # Use natural sort (ascending)
                file_data.sort(key=lambda x: natural_sort_key(x['filename']))
            elif sort_method == "name_desc":
                # Use natural sort (descending)
                file_data.sort(key=lambda x: natural_sort_key(x['filename']), reverse=True)
            elif sort_method == "time_desc":
                file_data.sort(key=lambda x: x['mtime'], reverse=True)
            elif sort_method == "time_asc":
                file_data.sort(key=lambda x: x['mtime'])
            elif sort_method == "size_desc":
                file_data.sort(key=lambda x: x['size'], reverse=True)
            elif sort_method == "size_asc":
                file_data.sort(key=lambda x: x['size'])
            elif sort_method == "type":
                # Sort by type first, then by natural sort
                file_data.sort(key=lambda x: (x['type'], natural_sort_key(x['filename'])))
            
            # Fill list
            for i, data in enumerate(file_data):
                tag = 'oddrow' if i % 2 else 'evenrow'
                tree.insert('', tk.END, 
                        values=(data['filename'], data['region_display'], 
                                data['size_display'], data['time_display'], data['type']), 
                        tags=(tag,), 
                        iid=str(i))
            
            # Configure row colors
            tree.tag_configure('oddrow', background='#F8F9FA')
            tree.tag_configure('evenrow', background='white')
            
            # Update statistics information
            update_stats(file_data)
            
            # Select first item
            if file_data:
                tree.selection_set('0')
                tree.focus('0')
                tree.see('0')
        
        # Initialize list
        update_list()
        
        selected_file = [None]
        
        def on_select():
            """Select file"""
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Info", "Please select a file first", parent=select_window)
                return
            
            item = tree.item(selection[0])
            selected_file[0] = item['values'][0]
            select_window.destroy()
        
        def on_double_click(event):
            """Double click to load directly"""
            on_select()
        
        def on_browse():
            """Browse other files"""
            fp = filedialog.askopenfilename(
                title="Select Other Routing Data File",
                filetypes=[("Pickle Files", "*.pkl"), ("All Files", "*.*")],
                parent=select_window
            )
            if fp:
                selected_file[0] = fp
                select_window.destroy()
        
        # Bind double click event
        tree.bind('<Double-Button-1>', on_double_click)
        
        # Click column header to sort
        def on_column_click(col):
            """Click column header to toggle sort"""
            col_sort_map = {
                'filename': ('name_asc', 'name_desc'),
                'size': ('size_asc', 'size_desc'),
                'time': ('time_asc', 'time_desc'),
                'type': ('type', 'type'),
            }
            
            if col in col_sort_map:
                current = sort_var.get()
                options = col_sort_map[col]
                
                # Toggle ascending/descending
                if current == options[0]:
                    sort_var.set(options[1])
                else:
                    sort_var.set(options[0])
                
                update_list()
        
        for col in ['filename', 'size', 'time', 'type']:
            tree.heading(col, command=lambda c=col: on_column_click(c))
        
        # Bottom button area
        btn_frame = tk.Frame(select_window, bg=UI_COLORS['bg_panel'])
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        btn_style = {
            'font': ('Microsoft YaHei', 10, 'bold'),
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'padx': 25,
            'pady': 10
        }
        
        left_btns = tk.Frame(btn_frame, bg=UI_COLORS['bg_panel'])
        left_btns.pack(side=tk.LEFT)
        
        tk.Button(left_btns, text="✓ Load Selected File",
                command=on_select,
                bg=UI_COLORS['primary'],
                fg='white',
                activebackground=UI_COLORS['primary_dark'],
                activeforeground='white',
                **btn_style).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(left_btns, text="📁 Browse Other Files",
                command=on_browse,
                bg=UI_COLORS['secondary'],
                fg='white',
                activebackground='#689F38',
                activeforeground='white',
                **btn_style).pack(side=tk.LEFT)
        
        tk.Button(btn_frame, text="✗ Cancel",
                command=select_window.destroy,
                bg=UI_COLORS['text_light'],
                fg='white',
                activebackground=UI_COLORS['text_secondary'],
                activeforeground='white',
                **btn_style).pack(side=tk.RIGHT)
        
        # Keyboard shortcuts
        def on_key(event):
            if event.keysym == 'Return':
                on_select()
            elif event.keysym == 'Escape':
                select_window.destroy()
        
        select_window.bind('<Key>', on_key)
        
        def on_closing():
            selected_file[0] = None
            select_window.destroy()
        
        select_window.protocol("WM_DELETE_WINDOW", on_closing)
        
        self.root.wait_window(select_window)
        
        return selected_file[0]

    def save_routing_data(self):
        """Save routing data"""
        if self.router is None:
            messagebox.showwarning("Warning", "No data to save")
            return
        
        default_name = f"routing_region{self.task_count}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        
        file_path = filedialog.asksaveasfilename(
            title="Save Routing Data",
            initialdir=ROUTING_DIR,
            initialfile=default_name,
            defaultextension=".pkl",
            filetypes=[("Pickle Files", "*.pkl"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        if not os.path.basename(file_path).startswith('routing_'):
            dir_name = os.path.dirname(file_path)
            base_name = 'routing_' + os.path.basename(file_path)
            file_path = os.path.join(dir_name, base_name)
        
        try:
            success = self.persistence_mgr.save_to_file(
                self.task_count, self.router, self.all_finished_paths,
                self.snapshot_mgr.snapshots, file_path, self.total_connected_centers
            )
            
            if success:
                self.log(f"Data saved: {os.path.basename(file_path)}", 'SUCCESS')
                messagebox.showinfo("Success", f"Data saved successfully\n{file_path}")
                
        except Exception as e:
            self.log(f"Save failed: {str(e)}", 'ERROR')
            messagebox.showerror("Error", f"Save failed:\n{str(e)}")
    
    def save_as_routing_data(self):
        """Save routing data as"""
        self.save_routing_data()
    
    def export_image(self):
        """Export image"""
        if self.grid_mgr is None:
            messagebox.showwarning("Warning", "No image to export")
            return
        
        default_name = f"routing_region{self.task_count}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        file_path = filedialog.asksaveasfilename(
            title="Export Image",
            initialdir=FIGURES_DIR,
            initialfile=default_name,
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                self.canvas_area.fig.savefig(file_path, dpi=300, bbox_inches='tight', 
                                            facecolor='white')
                self.log(f"Image exported: {os.path.basename(file_path)}", 'SUCCESS')
                messagebox.showinfo("Success", "Image exported successfully")
            except Exception as e:
                self.log(f"Export failed: {str(e)}", 'ERROR')
                messagebox.showerror("Error", f"Export failed:\n{str(e)}")
    
    # ===========================
    # Snapshot Management
    # ===========================
    
    def view_snapshots(self):
        """View snapshot list"""
        snapshots = self.snapshot_mgr.list_snapshots()
        if not snapshots:
            messagebox.showinfo("Info", "No available snapshots")
            return
        
        current_idx = self.snapshot_mgr.get_current_snapshot_index()
        SnapshotListDialog(self.root, snapshots, current_idx).show()
    
    def switch_to_snapshot(self):
        """Switch to specified snapshot"""
        snapshots = self.snapshot_mgr.list_snapshots()
        if not snapshots:
            messagebox.showinfo("Info", "No available snapshots")
            return
        
        from .dialogs import center_window_right
        
        window = tk.Toplevel(self.root)
        window.title("Switch Snapshot")
        window.geometry("750x550")
        window.configure(bg=UI_COLORS['bg_panel'])
        window.transient(self.root)
        window.grab_set()
        
        center_window_right(window, self.root)
        
        self._show_snapshot_switch_dialog(window, snapshots)
    
    def _show_snapshot_switch_dialog(self, window, snapshots):
        """Show snapshot switch dialog content"""
        current_idx = self.snapshot_mgr.get_current_snapshot_index()
        
        # Title
        title_frame = tk.Frame(window, bg=UI_COLORS['primary'], height=50)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="🔄 Select Snapshot to Switch To",
                font=('Microsoft YaHei', 12, 'bold'),
                fg='white', bg=UI_COLORS['primary']).pack(pady=12)
        
        # Current snapshot indicator
        if current_idx >= 0:
            info_frame = tk.Frame(window, bg=UI_COLORS['primary_light'])
            info_frame.pack(fill=tk.X, padx=15, pady=10)
            
            info_container = tk.Frame(info_frame, bg=UI_COLORS['primary_light'])
            info_container.pack(fill=tk.X, padx=10, pady=8)
            
            tk.Label(info_container, text=f"Current Snapshot: #{current_idx + 1}",
                    font=('Microsoft YaHei', 10, 'bold'),
                    foreground=UI_COLORS['primary'],
                    bg=UI_COLORS['primary_light']).pack(side=tk.LEFT)
            
            tk.Label(info_container, text="(Can switch to other snapshots repeatedly)",
                    font=('Microsoft YaHei', 9),
                    foreground=UI_COLORS['text_light'],
                    bg=UI_COLORS['primary_light']).pack(side=tk.LEFT, padx=10)
        
        # List
        list_frame = tk.Frame(window, bg=UI_COLORS['bg_panel'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        listbox = tk.Listbox(list_frame, font=('Consolas', 9), height=15,
                            bg='white',
                            fg=UI_COLORS['text_primary'],
                            selectbackground=UI_COLORS['primary_light'],
                            selectforeground=UI_COLORS['text_primary'])
        listbox.pack(fill=tk.BOTH, expand=True)
        
        # Add "Original State" option
        prefix_blank = "➤ " if current_idx == -1 else "  "
        item_blank = f"{prefix_blank}[0] Original State - Blank state after CSV import (no routing)"
        listbox.insert(tk.END, item_blank)
        if current_idx == -1:
            listbox.itemconfig(0, {'bg': UI_COLORS['primary_light']})
        
        for i, snap in enumerate(snapshots):
            prefix = "➤ " if i == current_idx else "  "
            item = (f"{prefix}[{i+1}] Region {snap['task_count']} - "
                   f"{snap['timestamp']} - Total {len(snap['all_finished_paths'])} paths")
            listbox.insert(tk.END, item)
            
            if i == current_idx:
                listbox.itemconfig(i, {'bg': UI_COLORS['primary_light']})
        
        def do_switch():
            sel = listbox.curselection()
            if not sel:
                messagebox.showwarning("Warning", "Please select a snapshot")
                return
            
            idx = sel[0]
            
            # Handle original state (index 0)
            if idx == 0:
                result = messagebox.askyesno(
                    "Confirm Revert to Original State",
                    "Are you sure you want to revert to the original state?\n\n"
                    "This will clear all routed region data,\n"
                    "and restore to the state just after importing the CSV file.\n\n"
                    "Original State:\n"
                    "• Clear all completed paths\n"
                    "• Clear occupation_grid\n"
                    "• Clear DiagonalBitmap\n"
                    "• Keep CSV data and grid configuration"
                )
                if result:
                    window.destroy()
                    self._reset_to_blank_state()
                return
            
            # Adjust index (because item 0 is original state, actual snapshots start from index 1)
            snapshot_idx = idx - 1
            
            if snapshot_idx == current_idx:
                result = messagebox.askyesno("Confirm",
                                            f"You are using snapshot #{idx}\n\n"
                                            f"Do you want to reload this snapshot?\n"
                                            f"(This will discard current unsaved changes)")
                if not result:
                    return
            
            result = self.snapshot_mgr.restore_snapshot(snapshot_idx, self.router)
            
            if result:
                self.task_count, self.all_finished_paths = result
                
                self.log("="*50)
                self.log(f"[Success] Switched to snapshot #{idx}", 'SUCCESS')
                self.log(f"Region: {self.task_count}")
                self.log(f"Total paths: {len(self.all_finished_paths)}")
                self.log("="*50)
                
                save_result = messagebox.askyesno("Save",
                                                  f"Switched to snapshot #{idx}\n\n"
                                                  f"Do you want to save current state to file?")
                if save_result:
                    self.save_routing_data()
                
                # Reset state
                self.task_count += 1
                self.ctx = None
                self.poly_path = None
                self.current_stage = 0
                
                self.update_data_info()
                self._plot_base_grid()
                self.control_panel.hide_all_dynamic_frames()
                
                stage_var = self.control_panel.get_widget('stage_var')
                stage_var.set(f"🔄 Switched to snapshot #{idx}, starting from region {self.task_count}")
                
                window.destroy()
                
                messagebox.showinfo("Success",
                                   f"Switched to snapshot #{idx}\n"
                                   f"Can now continue working from region {self.task_count}")
            else:
                messagebox.showerror("Error", "Snapshot switching failed")
        
        # Buttons
        btn_frame = tk.Frame(window, bg=UI_COLORS['bg_panel'])
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        btn_style = {
            'font': ('Microsoft YaHei', 10, 'bold'),
            'fg': 'white',
            'activeforeground': 'white',
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'padx': 20,
            'pady': 8
        }
        
        tk.Button(btn_frame, text="✓ Switch to Selected Snapshot",
                 command=do_switch,
                 bg=UI_COLORS['primary'],
                 activebackground=UI_COLORS['primary_dark'],
                 **btn_style).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="✗ Cancel",
                 command=window.destroy,
                 bg=UI_COLORS['text_light'],
                 activebackground=UI_COLORS['text_secondary'],
                 **btn_style).pack(side=tk.RIGHT, padx=5)
    
    def show_shortcuts(self):
        """Show keyboard shortcuts list"""
        shortcuts_text = """⌨️ Keyboard Shortcuts List

【File Operations】
Ctrl+O      Import CSV Data
Ctrl+L      Load Routing Data (.pkl)
Ctrl+S      Save Routing Data
Ctrl+E      Export Image

【Routing Operations】
Ctrl+N      Start New Region
Ctrl+H      View Snapshot List
Ctrl+T      Switch to Snapshot

【View Operations】
F5          Refresh Canvas

【Boundary Selection】
Left Click   Select single point
Right Drag   Select multiple points
Ctrl+Z      Undo last point
Enter        Confirm selection

【Other】
F1          User Guide
Ctrl+Q      Exit Program
"""
        messagebox.showinfo("Keyboard Shortcuts List", shortcuts_text)

    # Continue adding methods in RoutingSystemUI class
    
    # ===========================
    # Region Selection
    # ===========================
    
    def start_new_region(self):
        """Start new region - Enhanced: supports resetting current region"""
        if self.grid_mgr is None:
            messagebox.showwarning("Warning", "Please import CSV data file first")
            return
        
        # New: Check if routing is in progress
        if self.current_stage > 0 and self.ctx is not None:
            result = messagebox.askyesnocancel(
                "Confirm Restart",
                f"Detected region {self.task_count} is being routed (stage {self.current_stage})\n\n"
                "Do you want to abandon current progress and restart this region?\n\n"
                "• Yes - Restart current region\n"
                "• No - Continue current region\n"
                "• Cancel - Return"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - Restart
                self.log("="*50, 'WARNING')
                self.log(f"[User Action] Abandon region {self.task_count} current progress, restart", 'WARNING')
                self.log("="*50, 'WARNING')
                
                # Completely clean up current region state
                self._reset_current_region()
            else:  # No - Continue
                self.log(f"[User Action] Continue routing region {self.task_count}", 'INFO')
                return
        
        self.region_start_time = time.time()
        
        self.log("="*50)
        self.log(f"Start routing task for region {self.task_count}", 'SUCCESS')
        self.log("="*50)
        
        stage_var = self.control_panel.get_widget('stage_var')
        stage_var.set(f"📐 Region {self.task_count} - Select Region")
        self.update_status("Please select region on canvas")
        
        self.control_panel.hide_all_dynamic_frames()
        stage_action_frame = self.control_panel.get_widget('stage_action_frame')
        
        tk.Label(stage_action_frame,
                text="Selecting region...\nClick canvas to draw polygon\nPress Enter to confirm selection",
                font=('Microsoft YaHei', 15, 'bold'),
                fg=UI_COLORS['text_secondary'],
                bg=UI_COLORS['bg_panel'],
                wraplength=310,
                justify=tk.LEFT).pack(pady=5)
        
        self._plot_base_grid(title=f"[Region {self.task_count}] Please select routing region - Press Enter to confirm")
        
        # Set up polygon selector
        self.canvas_area.setup_polygon_selector(self.on_region_selected)

    def _reset_current_region(self):
        """
        Completely reset all state of current region
        Clear all caches, restore to state before region started
        """
        try:
            # 1. Reset stage state
            self.current_stage = 0
            self.stage1_time = 0
            self.stage2_time = 0
            self.stage3_time = 0
            
            # 2. Clean up context
            if self.ctx:
                # Get all network IDs for current region
                net_id_start = 1000 * self.task_count
                net_id_end = net_id_start + 1000
                
                # Clean up current region's occupation in occupation_grid
                for y in range(self.router.h):
                    for x in range(self.router.w):
                        net_id = self.router.occupation_grid[y, x]
                        if net_id_start <= net_id < net_id_end:
                            self.router.occupation_grid[y, x] = 0
                
                # Clean up current region's diagonal lines in DiagonalBitmap
                if hasattr(self.router, 'diagonal_bitmap'):
                    cells_to_clean = []
                    for cell_key, cell_data in self.router.diagonal_bitmap.cells.items():
                        keys_to_remove = []
                        for diag_type, net_id in cell_data.items():
                            if net_id_start <= net_id < net_id_end:
                                keys_to_remove.append(diag_type)
                        
                        for k in keys_to_remove:
                            del cell_data[k]
                        
                        if not cell_data:
                            cells_to_clean.append(cell_key)
                    
                    for cell_key in cells_to_clean:
                        del self.router.diagonal_bitmap.cells[cell_key]
                
                # Clean up current region's backup points in global reserved points
                if self.ctx.get('center_backups_ordered'):
                    for point in self.ctx['center_backups_ordered']:
                        pt_tuple = tuple(point)
                        if pt_tuple in self.router.global_reserved_points:
                            self.router.global_reserved_points.discard(pt_tuple)
                
                if self.ctx.get('out_backups_ordered'):
                    for point in self.ctx['out_backups_ordered']:
                        pt_tuple = tuple(point)
                        if pt_tuple in self.router.global_reserved_points:
                            self.router.global_reserved_points.discard(pt_tuple)

                # Clear diagonal occupied points of current region in diagonal_occupied_points
                if hasattr(self.router, 'diagonal_occupied_points'):
                    points_to_remove = []
                    for point, net_id in self.router.diagonal_occupied_points.items():
                        if net_id_start <= net_id < net_id_end:
                            points_to_remove.append(point)

                    for point in points_to_remove:
                        del self.router.diagonal_occupied_points[point]
            
            # 3. Clear current region data
            self.ctx = None
            self.poly_path = None
            self.selected_vertices = []
            self.valid_out = None
            self.valid_center = None
            self.out_groups = {}
            self.force_manual = False
            
            # 4. Clear boundary assigner state
            self.boundary_assigner_active = False
            self.boundary_assignments = {}
            self.current_boundary_direction = None
            self.selected_boundary_points = []
            self.boundary_available_points = []
            self.boundary_directions = []
            self.boundary_direction_index = 0
            self.boundary_points_pool = []
            self.boundary_point_type = ''
            self.boundary_bbox = None
            
            # 5. Clear stage 3 related state
            self.auto_matches = []
            self.current_auto_group_index = 0
            self.skip_remaining_groups = False
            self.total_manual_groups = 0
            self.current_manual_group = 0
            
            # 6. Clear stage state in state manager
            self.state_mgr.clear()
            
            # 7. Reset statistics
            if hasattr(self.router, 'stats'):
                self.router.reset_stats()
            
            # 8. Clear canvas selectors
            self.canvas_area.clear_selectors()
            
            # 9. Hide all dynamic controls
            self.control_panel.hide_all_dynamic_frames()
            
            # 10. Reset timer
            stage_var = self.control_panel.get_widget('stage_var')
            stage_var.set("⏳ Reset, waiting to restart")
            
            timer_var = self.control_panel.get_widget('timer_var')
            timer_var.set("")
            
            self.log("✓ Current region state fully reset", 'SUCCESS')
            
        except Exception as e:
            self.log(f"Error resetting region state: {str(e)}", 'ERROR')
            import traceback
            traceback.print_exc()


    

    def _reset_to_blank_state(self):
        """Reset to original blank state"""
        try:
            self.log("Resetting to original state...", 'INFO')

            # 1. Clear all completed paths
            self.all_finished_paths = []
            self.total_connected_centers = 0
            
            # 2. Clear occupation_grid
            if self.router:
                self.router.occupation_grid = np.zeros((self.router.h, self.router.w), dtype=int)
                # Re-mark obstacles
                obs_idx = np.where(self.grid_mgr.grid == 3)
                self.router.occupation_grid[obs_idx] = -1
            
            # 3. Clear DiagonalBitmap
            if self.router:
                if hasattr(self.router, 'diagonal_bitmap'):
                    self.router.diagonal_bitmap.clear()
                if hasattr(self.router, 'global_reserved_points'):
                    self.router.global_reserved_points.clear()
            
            # 4. Clear current region data
            self.ctx = None
            self.poly_path = None
            self.selected_vertices = []
            self.valid_out = None
            self.valid_center = None
            self.out_groups = {}
            self.force_manual = False
            
            # 5. Clear snapshots
            self.snapshot_mgr.clear()
            
            # 6. Reset task count
            self.task_count = 0
            
            # 7. Clear state manager
            self.state_mgr.clear()
            
            # 8. Reset statistics
            if hasattr(self.router, 'stats'):
                self.router.reset_stats()
            
            # 9. Clear canvas selectors
            self.canvas_area.clear_selectors()
            
            # 10. Hide all dynamic controls
            self.control_panel.hide_all_dynamic_frames()
            
            # 11. Reset UI state
            stage_var = self.control_panel.get_widget('stage_var')
            stage_var.set("⭕ Original state - No routing")
            
            timer_var = self.control_panel.get_widget('timer_var')
            timer_var.set("")
            
            # 12. Redraw canvas
            self._plot_base_grid(
                title="Original state - Waiting to start new region"
            )
            
            self.log("✓ Reset to original blank state", 'SUCCESS')
            self.log("All routing data cleared, CSV data and grid configuration retained", 'INFO')
            messagebox.showinfo("Completed", "Successfully reset to original state\n\nAll routing data cleared\nCSV data and grid configuration retained")
            
        except Exception as e:
            self.log(f"Error resetting to original state: {str(e)}", 'ERROR')
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Reset failed:\n{str(e)}")

    def on_region_selected(self, vertices):
        """Region selection completed"""
        self.selected_vertices = vertices

        # Ensure polygon path is closed: if start and end vertices are different, add start vertex to end
        vertices_array = np.array(vertices)
        if len(vertices_array) > 0:
            # Check if start and end are the same (allow small error)
            if not np.allclose(vertices_array[0], vertices_array[-1], atol=1e-10):
                # Add start vertex to end to close path
                closed_vertices = np.vstack([vertices_array, vertices_array[0:1]])
            else:
                closed_vertices = vertices_array
            self.poly_path = Path(closed_vertices)
        else:
            self.poly_path = Path(vertices)
        
        # Clear selectors
        self.canvas_area.clear_selectors()
        
        all_out = self.grid_mgr.get_points_by_type('out')
        all_center = self.grid_mgr.get_points_by_type('center')
        self.valid_out = all_out[self.poly_path.contains_points(all_out)]
        self.valid_center = all_center[self.poly_path.contains_points(all_center)]
        
        self.out_groups = {'Top': [], 'Bottom': [], 'Left': [], 'Right': []}
        for p in self.valid_out:
            label = self.grid_mgr.get_out_label(p[0], p[1])
            if label in self.out_groups:
                self.out_groups[label].append(p)
        
        self.log(f"Region selected, contains {len(vertices)} vertices", 'SUCCESS')
        self.log(f"Out points in region: {len(self.valid_out)}")
        self.log(f"Center points in region: {len(self.valid_center)}")
        
        self.log("【Out Points Statistics in Region】")
        for k, v in self.out_groups.items():
            if len(v) > 0:
                self.log(f"  {k} side: {len(v)}")
        
        # Check if counts are consistent
        if len(self.valid_out) != len(self.valid_center):
            self.log(f"[Warning] Out({len(self.valid_out)}) and "
                    f"Center({len(self.valid_center)}) counts are inconsistent!", 'WARNING')
            
            result = messagebox.askyesno(
                "Count Inconsistent",
                f"Detected inconsistent point counts:\n\n"
                f"Out points: {len(self.valid_out)}\n"
                f"Center points: {len(self.valid_center)}\n\n"
                f"Do you want to reselect region?\n\n"
                f"Select 'Yes': Reselect region\n"
                f"Select 'No': Continue with current region\n\n"
                f"Note: When counts are inconsistent, Stage 3 auto mode will connect\n"
                f"in routing order, some points may not be connected."
            )
            
            if result:
                self.log("User chose to reselect region", 'INFO')
                self.poly_path = None
                self.selected_vertices = []
                self.valid_out = None
                self.valid_center = None
                self.out_groups = {}
                self.start_new_region()
                return
            else:
                self.log("User chose to continue with current region (counts inconsistent, some points may not be connected in Stage 3)", 'INFO')
                self.force_manual = False
        else:
            self.force_manual = False
        
        self.initialize_context()
        
        self._plot_base_grid(
            title=f"Region {self.task_count} - Selected "
                f"(Out:{len(self.valid_out)}, Center:{len(self.valid_center)})",
            out_points=self.valid_out,
            show_region=True
        )
        
        stage_var = self.control_panel.get_widget('stage_var')
        stage_var.set(f"✓ Region {self.task_count} - Stage 1 Ready")
        self.current_stage = 1
        self.prepare_stage1()
    
    def initialize_context(self):
        """Initialize routing context"""
        self.ctx = {
            'router': self.router,
            'current_net_id': 1000 * self.task_count,
            'out_bbox': None,
            'center_bbox': None,
            'out_boundary_map': {},
            'center_boundary_map': {},
            'internal_paths': [],
            'external_paths': [],
            'center_backups_ordered': [],
            'out_backups_ordered': [],
            'center_backups_grouped': {'Top': [], 'Bottom': [], 'Left': [], 'Right': []},
            'out_backups_grouped': {'Top': [], 'Bottom': [], 'Left': [], 'Right': []}
        }
        self.state_mgr = StateManager()
        self.stage1_time = 0
        self.stage2_time = 0
        self.stage3_time = 0
    
    # ===========================
    # Stage Control
    # ===========================
    
    def prepare_stage1(self):
        """Prepare Stage 1"""
        self.log("-"*40)
        self.log(f"Stage 1/3: Out point internal routing (Region {self.task_count})")
        self.log("-"*40)
        
        self.stage_start_time = time.time()
        
        self.state_mgr.save_state('stage_1', {
            'router_occupation': copy.deepcopy(self.router.occupation_grid),
            'router_diagonal': self.router.diagonal_bitmap.copy(),
            'router_reserved': copy.deepcopy(self.router.global_reserved_points),
            'router_diagonal_occupied': copy.deepcopy(self.router.diagonal_occupied_points),
            'ctx': copy.deepcopy(self.ctx)
        })
        
        o_min = self.valid_out.min(axis=0)
        o_max = self.valid_out.max(axis=0)
        self.ctx['out_bbox'] = (max(0, int(o_min[0])-1), max(0, int(o_min[1])-1),
                                min(self.grid_mgr.w-1, int(o_max[0])+1),
                                min(self.grid_mgr.h-1, int(o_max[1])+1))
        
        stage_var = self.control_panel.get_widget('stage_var')
        stage_var.set("🔧 Stage 1 - Select Out Mapping Mode")
        
        self._show_mode_selection("Stage 1: Out Internal Routing")
        btn_auto = self.control_panel.get_widget('btn_auto')
        btn_auto.config(state='normal')
    
    def prepare_stage2(self):
        """Prepare Stage 2"""
        self.current_stage = 2
        self.stage_start_time = time.time()

        self.log("-"*40)
        self.log(f"Stage 2/3: Center point internal routing (Region {self.task_count})")
        self.log("-"*40)

        # Calculate center_bbox first, then save state
        c_min = self.valid_center.min(axis=0)
        c_max = self.valid_center.max(axis=0)
        self.ctx['center_bbox'] = (max(0, int(c_min[0])-1), max(0, int(c_min[1])-1),
                                   min(self.grid_mgr.w-1, int(c_max[0])+1),
                                   min(self.grid_mgr.h-1, int(c_max[1])+1))

        self.state_mgr.save_state('stage_2', {
            'router_occupation': copy.deepcopy(self.router.occupation_grid),
            'router_diagonal': self.router.diagonal_bitmap.copy(),
            'router_reserved': copy.deepcopy(self.router.global_reserved_points),
            'router_diagonal_occupied': copy.deepcopy(self.router.diagonal_occupied_points),
            'ctx': copy.deepcopy(self.ctx)
        })
        
        stage_var = self.control_panel.get_widget('stage_var')
        stage_var.set("🔧 Stage 2 - Select Center Mapping Mode")
        
        self._show_mode_selection("Stage 2: Center Internal Routing")
        btn_auto = self.control_panel.get_widget('btn_auto')
        btn_auto.config(state='normal')
    
    def prepare_stage3(self):
        """Prepare Stage 3"""
        self.current_stage = 3
        self.stage_start_time = time.time()
        
        self.log("-"*40)
        self.log(f"Stage 3/3: External routing (Region {self.task_count})")
        self.log("-"*40)
        
        self.state_mgr.save_state('stage_3', {
            'router_occupation': copy.deepcopy(self.router.occupation_grid),
            'router_diagonal': self.router.diagonal_bitmap.copy(),
            'router_reserved': copy.deepcopy(self.router.global_reserved_points),
            'router_diagonal_occupied': copy.deepcopy(self.router.diagonal_occupied_points),
            'ctx': copy.deepcopy(self.ctx)
        })
        
        stage_var = self.control_panel.get_widget('stage_var')
        stage_var.set("🔧 Stage 3 - Select External Connection Mode")
        
        self._show_mode_selection("Stage 3: External Connection")
        btn_auto = self.control_panel.get_widget('btn_auto')
        btn_auto.config(state='normal')
    
    def select_auto_mode(self):
        """Select auto mode"""
        if self.current_stage == 1:
            self.execute_stage1_auto()
        elif self.current_stage == 2:
            self.execute_stage2_auto()
        elif self.current_stage == 3:
            self.execute_stage3_auto()
    
    def select_manual_mode(self):
        """Select manual mode"""
        if self.current_stage == 1:
            self.start_stage1_manual()
        elif self.current_stage == 2:
            self.start_stage2_manual()
        elif self.current_stage == 3:
            self.start_stage3_manual()
    
    def next_stage(self):
        """Enter next stage"""
        if self.current_stage == 1:
            self.prepare_stage2()
        elif self.current_stage == 2:
            self.prepare_stage3()
    
    def retry_stage(self):
        """Retry current stage (improved: clear memory data and UI paths)"""
        stage_name = f'stage_{self.current_stage}'
        saved = self.state_mgr.load_state(stage_name)

        if saved:
            # Restore router state
            self.router.occupation_grid = saved['router_occupation']
            self.router.diagonal_bitmap = saved['router_diagonal']
            self.router.global_reserved_points = saved['router_reserved']
            self.router.diagonal_occupied_points = saved.get('router_diagonal_occupied', {})
            self.ctx = saved['ctx']

            self.log(f"[System] Restored to state before Stage {self.current_stage} started", 'SUCCESS')

            # Update UI immediately, clear paths on canvas
            self._refresh_canvas_after_retry()

            # Reset stage start time
            self.stage_start_time = time.time()

            # Update UI state
            stage_var = self.control_panel.get_widget('stage_var')
            if self.current_stage == 1:
                stage_var.set("🔧 Stage 1 - Select Out Mapping Mode")
                self._show_mode_selection("Stage 1: Out Internal Routing")
                btn_auto = self.control_panel.get_widget('btn_auto')
                btn_auto.config(state='normal')
            elif self.current_stage == 2:
                stage_var.set("🔧 Stage 2 - Select Center Mapping Mode")
                self._show_mode_selection("Stage 2: Center Internal Routing")
            elif self.current_stage == 3:
                stage_var.set("🔧 Stage 3 - Select External Connection Mode")
                self._show_mode_selection("Stage 3: External Connection")
        else:
            self.log("No state to rollback", 'WARNING')

    def _refresh_canvas_after_retry(self):
        """Refresh canvas after rollback, display cleared state"""
        if self.current_stage == 1:
            # Stage 1 rollback: only show region and Out points
            self._plot_base_grid(
                title=f"Region {self.task_count} - Stage 1 Retry (previous routing cleared)",
                out_points=self.valid_out,
                show_region=True
            )
        elif self.current_stage == 2:
            # Stage 2 rollback: show Stage 1 results
            self._plot_base_grid(
                title=f"Region {self.task_count} - Stage 2 Retry (previous routing cleared)",
                out_backups=self.ctx.get('out_backups_ordered', []),
                out_points=self.valid_out,
                current_paths=self.ctx.get('internal_paths', []),
                show_region=True
            )
        elif self.current_stage == 3:
            # Stage 3 rollback: show Stage 1 and Stage 2 results
            self._plot_base_grid(
                title=f"Region {self.task_count} - Stage 3 Retry (previous routing cleared)",
                center_backups=self.ctx.get('center_backups_ordered', []),
                out_backups=self.ctx.get('out_backups_ordered', []),
                out_points=self.valid_out,
                current_paths=self.ctx.get('internal_paths', []),
                show_region=True
            )
    
    def confirm_region(self):
        """Confirm completion of current region"""
        # Display routing success rate statistics
        num_center = len(self.valid_center)
        num_out = len(self.valid_out)
        target_connections = min(num_center, num_out)
        successful_connections = len(self.ctx['external_paths'])

        # Calculate number of unconnected center points in entire layout
        total_center_points = len(self.grid_mgr.get_points_by_type('center'))
        remaining_center = total_center_points - (self.total_connected_centers + successful_connections)

        if target_connections > 0:
            success_percentage = (successful_connections / target_connections) * 100
        else:
            success_percentage = 0

        message = (
            f"Region {self.task_count} Routing Statistics\n\n"
            f"Routing Success Rate: {success_percentage:.0f}% ({successful_connections}/{target_connections})\n"
            f"Successfully Connected: {successful_connections} Center→Out\n"
            f"Remaining to Connect: {remaining_center} Center Points"
        )

        messagebox.showinfo("Routing Success Rate Statistics", message)

        # Update cumulative connection count
        self.total_connected_centers += successful_connections

        # Prefer smoothed merged paths, then merged paths, finally original paths
        if 'smoothed_merged_paths' in self.ctx and self.ctx['smoothed_merged_paths']:
            self.all_finished_paths.extend(self.ctx['smoothed_merged_paths'])
        elif 'merged_paths' in self.ctx and self.ctx['merged_paths']:
            self.all_finished_paths.extend(self.ctx['merged_paths'])
        else:
            # Compatible with old version: use original internal and external paths
            self.all_finished_paths.extend(self.ctx['internal_paths'])
            self.all_finished_paths.extend(self.ctx['external_paths'])
        
        self.snapshot_mgr.save_snapshot(self.task_count, self.router,
                                       self.all_finished_paths)
        
        self.log("="*30)
        self.log(f"Region {self.task_count} task archived", 'SUCCESS')
        self.log("="*30)
        self.update_data_info()
        
        save_result = messagebox.askyesno("Save Data", 
                                          f"Region {self.task_count} completed!\n\n"
                                          f"Do you want to save current routing data to pkl file?")
        if save_result:
            self.save_routing_data()
        else:
            self.log("[Info] Not saved to file this time, data only kept in memory (snapshots can be used for rollback)")
        
        satisfied = messagebox.askyesno("Confirm", 
                                        f"Are you satisfied with the routing result of region {self.task_count}?\n\n"
                                        f"Select 'No' to switch to previous snapshot")
        
        if not satisfied:
            self.log("[Rollback Feature]")
            self.switch_to_snapshot()
            return
        
        continue_result = messagebox.askyesno("Continue",
                                             "Do you want to continue with next region routing task?")
        
        if continue_result:
            self.task_count += 1
            self.ctx = None
            self.poly_path = None
            self.valid_out = None
            self.valid_center = None
            self.current_stage = 0
            
            self.control_panel.hide_all_dynamic_frames()
            stage_var = self.control_panel.get_widget('stage_var')
            stage_var.set("⏳ Waiting to start new region")
            
            timer_var = self.control_panel.get_widget('timer_var')
            timer_var.set("")
            
            self._plot_base_grid()
            self.update_data_info()
        else:
            final_save = messagebox.askyesno("Exit", "Save final routing data before exit?")
            if final_save:
                self.save_routing_data()
            
            self.log("Program ended.")
            self.control_panel.hide_all_dynamic_frames()
            stage_var = self.control_panel.get_widget('stage_var')
            stage_var.set("✅ Task Completed")
    
    # ===========================
    # UI Helper Methods
    # ===========================
    
    def _show_mode_selection(self, stage_name):
        """Show auto/manual mode selection buttons"""
        self.control_panel.hide_all_dynamic_frames()
        
        stage_action_frame = self.control_panel.get_widget('stage_action_frame')
        
        # Use consistent font size with other modules (15, 'bold')
        tk.Label(stage_action_frame,
                text=f"{stage_name}\nPlease select mode:",
                font=('Microsoft YaHei', 15, 'bold'),
                fg=UI_COLORS['text_secondary'],
                bg=UI_COLORS['bg_panel'],
                wraplength=310,
                justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 8))
        
        btn_auto = self.control_panel.get_widget('btn_auto')
        btn_manual = self.control_panel.get_widget('btn_manual')
        
        btn_auto.pack(fill=tk.X, pady=4)
        btn_manual.pack(fill=tk.X, pady=4)

    
    def _show_stage_complete_buttons(self):
        """Show buttons after stage completion"""
        self.control_panel.hide_all_dynamic_frames()
        
        stage_action_frame = self.control_panel.get_widget('stage_action_frame')
        
        # Unified font size + automatic line wrapping
        tk.Label(stage_action_frame,
                text="✅ Stage completed, please select:",
                font=('Microsoft YaHei', 15, 'bold'),
                fg=UI_COLORS['secondary'],
                bg=UI_COLORS['bg_panel'],
                wraplength=300,  # Add automatic line wrapping width
                justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 8))
        # Added wraplength and justify parameters
        
        btn_next = self.control_panel.get_widget('btn_next')
        btn_retry = self.control_panel.get_widget('btn_retry')
        
        btn_next.pack(fill=tk.X, pady=4)
        btn_retry.pack(fill=tk.X, pady=4)

    def _show_region_complete_buttons(self):
        """Show buttons after region completion"""
        self.control_panel.hide_all_dynamic_frames()
        
        stage_action_frame = self.control_panel.get_widget('stage_action_frame')
        
        # Unified font size + automatic line wrapping
        tk.Label(stage_action_frame,
                text="🎉 All stages completed:",
                font=('Microsoft YaHei', 15, 'bold'),
                fg=UI_COLORS['primary'],
                bg=UI_COLORS['bg_panel'],
                wraplength=300,  # Add automatic line wrapping width
                justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 8))
        # Added wraplength and justify parameters
        
        btn_confirm = self.control_panel.get_widget('btn_confirm')
        btn_retry = self.control_panel.get_widget('btn_retry')
        
        btn_confirm.pack(fill=tk.X, pady=4)
        btn_retry.pack(fill=tk.X, pady=4)