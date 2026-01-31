"""
stage3.py - Stage 3: External connection controller
Third stage controller for connections between center and external backup points.
Supports automatic matching (parallel/L-shaped boundaries) and manual point-to-point connections.
"""

import tkinter as tk
import time
from tkinter import messagebox, simpledialog
from ..utils.helpers import format_time, find_backup_point_index, determine_boundary_for_points
from ..routing.boundary_utils import (
    check_parallel_boundaries,
    check_L_shaped_boundaries,
    create_parallel_pairs,
    create_L_shaped_pairs,
    auto_match_boundary_groups
)
from ..ui.dialogs import ParallelStrategyDialog, LShapedStrategyDialog
from ..routing.path_smoother import smooth_region_paths
from ..routing.path_merger import merge_paths


class Stage3Controller:
    """Stage 3 controller"""
    
    def __init__(self, ui):
        self.ui = ui
    
    def execute_auto(self):
        """Execute stage 3 auto mode"""
        self.ui.log(">>> Executing intelligent external connection (prioritize parallel boundaries, then L-shaped boundaries)...")
        
        c_groups = self.ui.ctx['center_backups_grouped']
        o_groups = self.ui.ctx['out_backups_grouped']
        
        self.ui.log(f"  [Info] Center active groups: {[k for k, v in c_groups.items() if len(v) > 0]}")
        self.ui.log(f"  [Info] Out active groups:    {[k for k, v in o_groups.items() if len(v) > 0]}")
        
        # Auto match boundaries
        self.ui.auto_matches, unmatched_c, unmatched_o = auto_match_boundary_groups(c_groups, o_groups)
        
        if unmatched_c or unmatched_o:
            self.ui.log(f"\n  [Warning] Unmatched boundaries exist:", 'WARNING')
            if unmatched_c:
                self.ui.log(f"    Unmatched Center boundaries: {unmatched_c}")
            if unmatched_o:
                self.ui.log(f"    Unmatched Out boundaries: {unmatched_o}")
            self.ui.log(f"  [Tip] Please use manual mode to handle these boundaries")
        
        if not self.ui.auto_matches:
            self.ui.log("[Error] No matchable boundary groups", 'ERROR')
            self.finish()
            return
        
        self.ui.current_auto_group_index = 0
        self.ui.skip_remaining_groups = False
        
        self.process_auto_group()
    
    def process_auto_group(self):
        """Process one group in auto mode"""
        if self.ui.skip_remaining_groups or self.ui.current_auto_group_index >= len(self.ui.auto_matches):
            self.finish()
            return
        
        c_pts, o_pts, ck, ok = self.ui.auto_matches[self.ui.current_auto_group_index]
        
        if not c_pts or not o_pts:
            self.ui.log(f"[Skip] Group {self.ui.current_auto_group_index+1} is empty")
            self.ui.current_auto_group_index += 1
            self.process_auto_group()
            return
        
        self.ui.log(f"\n  --- Group {self.ui.current_auto_group_index+1}/{len(self.ui.auto_matches)}: "
                f"Center-{ck} <--> Out-{ok} ---")
        
        group_start_time = time.time()
        
        # Process boundary routing
        pairs = self.process_boundary_routing(list(c_pts), list(o_pts), ck, ok)
        
        if pairs is None:
            return
        
        # Execute routing
        self.execute_group_routing(pairs, ck, ok, group_start_time)
    
    def process_boundary_routing(self, c_pts, o_pts, ck, ok):
        """Process boundary routing"""
        is_parallel, orientation = check_parallel_boundaries(ck, ok)
        is_L_shaped, vertical_boundary, horizontal_boundary = check_L_shaped_boundaries(ck, ok)

        if is_parallel:
            # Parallel boundaries
            self.ui.log(f"  [Detected parallel boundaries] Center-{ck} and Out-{ok}")
            dialog = ParallelStrategyDialog(self.ui.root, ck, ok, orientation)
            result = dialog.show()

            if result is None:
                return None

            if result == 'auto':
                # Auto test all strategies
                self.ui.log(f"  [Auto strategy selection] Starting to test all parallel boundary strategies...")
                result = self._auto_select_parallel_strategy(c_pts, o_pts, ck, ok, orientation)
                if result is None:
                    return None
                pairs, order_desc, already_routed = result
                # Mark if routing is already completed
                self.ui.ctx['_auto_already_routed'] = already_routed
            else:
                pairs, order_desc, has_mismatch = create_parallel_pairs(c_pts, o_pts, ck, ok, result)
                self.ui.log(f"  [Parallel boundary mapping] {order_desc}")
                self.ui.log(f"  [Parallel boundary mapping] Created {len(pairs)} point pairs")
                self.ui.ctx['_auto_already_routed'] = False

                if has_mismatch:
                    self.ui.log(f"  [Warning] Boundary point counts mismatch, some points cannot be paired", 'WARNING')

            return pairs

        elif is_L_shaped:
            # L-shaped boundaries
            self.ui.log(f"  [Detected L-shaped boundaries] Center-{ck} and Out-{ok}")
            self.ui.log(f"    Vertical boundary: {vertical_boundary}    Horizontal boundary: {horizontal_boundary}")

            dialog = LShapedStrategyDialog(self.ui.root, ck, ok, vertical_boundary, horizontal_boundary)
            result = dialog.show()

            if result is None:
                return None

            if result == 'auto':
                # Auto test all strategies
                self.ui.log(f"  [Auto strategy selection] Starting to test all L-shaped boundary strategies...")
                result = self._auto_select_L_shaped_strategy(
                    c_pts, o_pts, ck, ok, vertical_boundary, horizontal_boundary)
                if result is None:
                    return None
                pairs, v_order_desc, h_order_desc, already_routed = result
                # Mark if routing is already completed
                self.ui.ctx['_auto_already_routed'] = already_routed
            else:
                vertical_order, horizontal_order = result
                pairs, v_order_desc, h_order_desc, has_mismatch = create_L_shaped_pairs(
                    c_pts, o_pts, ck, ok,
                    vertical_boundary, horizontal_boundary,
                    vertical_order, horizontal_order
                )

                self.ui.log(f"  [L-shaped mapping] Vertical{v_order_desc}, Horizontal{h_order_desc}")
                self.ui.log(f"  [L-shaped mapping] Created {len(pairs)} point pairs")
                self.ui.ctx['_auto_already_routed'] = False

                if has_mismatch:
                    self.ui.log(f"  [Warning] Boundary point counts mismatch, some points cannot be paired", 'WARNING')

            return pairs
        else:
            # Other cases: direct one-to-one correspondence
            self.ui.log(f"  [Unrecognized boundary type] Using default one-to-one correspondence", 'WARNING')
            pairs = []
            min_len = min(len(c_pts), len(o_pts))
            for i in range(min_len):
                pairs.append({'start': c_pts[i], 'end': o_pts[i]})

            return pairs
    
    def execute_group_routing(self, pairs, ck, ok, group_start_time):
        """Execute one group routing"""
        # Check if routing is already completed during auto strategy selection
        already_routed = self.ui.ctx.get('_auto_already_routed', False)
        if already_routed:
            self.ui.log(f"  [Skip routing] 100% routing completed during strategy testing, using results directly")
            # Clear marker
            self.ui.ctx['_auto_already_routed'] = False
            # Calculate statistics
            group_success = len(pairs)
            group_fail = 0
        else:
            all_terminals = set(tuple(p) for p in self.ui.ctx['center_backups_ordered']) | \
                           set(tuple(p) for p in self.ui.ctx['out_backups_ordered'])

            group_success = 0
            group_fail = 0

            for pair_idx, p in enumerate(pairs):
                s, e = tuple(p['start']), tuple(p['end'])
                c_idx = find_backup_point_index(s, self.ui.ctx['center_backups_ordered'])
                o_idx = find_backup_point_index(e, self.ui.ctx['out_backups_ordered'])

                self.ui.log(f"    [{pair_idx+1}/{len(pairs)}] Routing: "
                        f"{c_idx} Center -> {o_idx} Out ...", 'PROGRESS')

                path = self.ui.router.route_single_net(
                    s, e, self.ui.ctx['current_net_id'],
                    restrict_to_bbox=None,
                    all_terminals=all_terminals,
                    restrict_poly_path=self.ui.poly_path)

                if path:
                    self.ui.ctx['external_paths'].append(path)
                    group_success += 1
                    self.ui.log(f"        ✓ Success", 'SUCCESS')
                else:
                    self.ui.log(f"        ✗ Failed (coordinates: {s}->{e})", 'WARNING')
                    group_fail += 1

                self.ui.ctx['current_net_id'] += 1
        
        group_time = time.time() - group_start_time
        self.ui.log(f"  Group {self.ui.current_auto_group_index+1} routing completed: "
                f"Success {group_success}, Failed {group_fail}",
                'SUCCESS' if group_fail == 0 else 'WARNING')
        self.ui.log(f"  [Timing] Group {self.ui.current_auto_group_index+1} routing time: "
                f"{format_time(group_time)}", 'TIMING')
        
        # Update visualization
        full_paths = self.ui.ctx['internal_paths'] + self.ui.ctx['external_paths']
        self.ui._plot_base_grid(
            title=f"Region {self.ui.task_count} - External routing progress "
                  f"(Group {self.ui.current_auto_group_index+1}/{len(self.ui.auto_matches)} completed)",
            center_backups=self.ui.ctx['center_backups_ordered'],
            out_backups=self.ui.ctx['out_backups_ordered'],
            out_points=self.ui.valid_out,
            current_paths=full_paths,
            show_region=True
        )
        
        # If there are subsequent groups
        if self.ui.current_auto_group_index < len(self.ui.auto_matches) - 1:
            self.ui.control_panel.hide_all_dynamic_frames()
            
            auto_group_frame = self.ui.control_panel.get_widget('auto_group_frame')
            auto_group_frame.pack(fill='both', expand=True, padx=12, pady=8)
            
            auto_group_label = self.ui.control_panel.get_widget('auto_group_label')
            auto_group_label.config(
                text=f"Group {self.ui.current_auto_group_index+1}/{len(self.ui.auto_matches)} completed\n"
                     f"Center-{ck} <--> Out-{ok}\n"
                     f"✓ Success: {group_success}, ✗ Failed: {group_fail}\n"
                     f"⏱️ Time: {format_time(group_time)}")
            
            btn_auto_continue = self.ui.control_panel.get_widget('btn_auto_continue')
            btn_auto_skip = self.ui.control_panel.get_widget('btn_auto_skip')
            
            btn_auto_continue.pack(fill=tk.X, pady=4)
            btn_auto_skip.pack(fill=tk.X, pady=4)
            
            stage_var = self.ui.control_panel.get_widget('stage_var')
            stage_var.set(f"🔧 Stage 3 - Group {self.ui.current_auto_group_index+1} completed")
        else:
            self.ui.current_auto_group_index += 1
            self.finish()
    
    def start_manual(self):
        """Start stage 3 manual mode"""
        self.ui.log("Starting manual external connection...")
        
        # Show reference map
        self.ui._plot_base_grid(
            title=f"[Manual Connection Reference Map] Please record required Center and Out backup point numbers",
            center_backups=self.ui.ctx['center_backups_ordered'],
            out_backups=self.ui.ctx['out_backups_ordered'],
            out_points=self.ui.valid_out,
            show_region=True
        )
        
        self.ui.log("Please refer to canvas to view point numbers...")

        num_groups = self._show_input_group_count_dialog()
        
        if num_groups is None or num_groups <= 0:
            self.ui.log("Cancel manual connection", 'WARNING')
            self.finish()
            return
        
        self.ui.total_manual_groups = num_groups
        self.ui.current_manual_group = 0
        
        self.ui.show_manual_group_input()

    def _show_input_group_count_dialog(self):
        """Show group count input dialog - enlarged version"""
        from ..config.ui_config import UI_COLORS
        from ..utils.helpers import center_window_right
        
        dialog = tk.Toplevel(self.ui.root)
        dialog.title("Manual External Connection")
        dialog.geometry("650x350")
        dialog.configure(bg=UI_COLORS['bg_panel'])
        dialog.transient(self.ui.root)
        dialog.grab_set()
        
        center_window_right(dialog, self.ui.root)
        
        result = [None]
        
        # Title
        title_frame = tk.Frame(dialog, bg=UI_COLORS['primary'], height=70)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="✋ Please enter number of groups to connect",
                font=('Microsoft YaHei', 18, 'bold'),
                fg='white', bg=UI_COLORS['primary']).pack(expand=True)
        
        # Content area
        content_frame = tk.Frame(dialog, bg=UI_COLORS['bg_panel'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        # Description text
        tk.Label(content_frame,
                text="Please enter the number of groups to connect manually\nEach group contains several Center and Out backup points",
                font=('Microsoft YaHei', 14),
                fg=UI_COLORS['text_secondary'],
                bg=UI_COLORS['bg_panel'],
                justify=tk.CENTER).pack(pady=(0, 20))
        
        # Input box
        input_frame = tk.Frame(content_frame, bg=UI_COLORS['bg_panel'])
        input_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(input_frame, text="Groups:",
                font=('Microsoft YaHei', 16, 'bold'),
                fg=UI_COLORS['text_primary'],
                bg=UI_COLORS['bg_panel']).pack(side=tk.LEFT, padx=(0, 15))
        
        entry = tk.Entry(input_frame,
                        font=('Microsoft YaHei', 18),
                        width=15,
                        bg='white',
                        fg=UI_COLORS['text_primary'],
                        relief=tk.SOLID,
                        bd=1,
                        justify=tk.CENTER)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.insert(0, "1")
        entry.select_range(0, tk.END)
        entry.focus()
        
        def validate_and_confirm():
            try:
                value = int(entry.get())
                if 1 <= value <= 100:
                    result[0] = value
                    dialog.destroy()
                elif value == 0:
                    result[0] = None
                    dialog.destroy()
                else:
                    messagebox.showwarning("Input Error", "Please enter an integer between 1 and 100", parent=dialog)
                    entry.select_range(0, tk.END)
            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid integer", parent=dialog)
                entry.delete(0, tk.END)
                entry.insert(0, "1")
                entry.select_range(0, tk.END)
        
        # Button area
        btn_frame = tk.Frame(dialog, bg=UI_COLORS['bg_panel'])
        btn_frame.pack(fill=tk.X, padx=40, pady=(0, 25))
        
        # Create centered container
        btn_container = tk.Frame(btn_frame, bg=UI_COLORS['bg_panel'])
        btn_container.pack(anchor=tk.CENTER)
        
        tk.Button(btn_container, text="✓ Confirm",
                command=validate_and_confirm,
                font=('Microsoft YaHei', 14, 'bold'),
                bg=UI_COLORS['primary'],
                fg='white',
                activebackground=UI_COLORS['primary_dark'],
                activeforeground='white',
                relief=tk.FLAT,
                cursor='hand2',
                padx=30, pady=12).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(btn_container, text="✗ Cancel",
                command=lambda: (result.__setitem__(0, None), dialog.destroy()),
                font=('Microsoft YaHei', 14, 'bold'),
                bg=UI_COLORS['text_light'],
                fg='white',
                activebackground=UI_COLORS['text_secondary'],
                activeforeground='white',
                relief=tk.FLAT,
                cursor='hand2',
                padx=30, pady=12).pack(side=tk.LEFT)
        
        entry.bind('<Return>', lambda e: validate_and_confirm())
        entry.bind('<Escape>', lambda e: (result.__setitem__(0, None), dialog.destroy()))
        
        self.ui.root.wait_window(dialog)
        return result[0]


    def _show_styled_integer_dialog(self, title, prompt, minvalue=1, maxvalue=100):
        """Show styled integer input dialog"""
        from ..config.ui_config import UI_COLORS
        from ..utils.helpers import center_window_right
        
        dialog = tk.Toplevel(self.ui.root)
        dialog.title(title)
        dialog.geometry("480x280")
        dialog.configure(bg=UI_COLORS['bg_panel'])
        dialog.transient(self.ui.root)
        dialog.grab_set()
        
        center_window_right(dialog, self.ui.root)
        
        result = [None]
        
        # Content area
        content_frame = tk.Frame(dialog, bg=UI_COLORS['bg_panel'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=25)
        
        # Prompt text
        tk.Label(content_frame, text=prompt,
                font=('Microsoft YaHei', 14, 'bold'),
                fg=UI_COLORS['text_primary'],
                bg=UI_COLORS['bg_panel']).pack(anchor=tk.W, pady=(0, 15))
        
        # Input box
        entry_frame = tk.Frame(content_frame, bg='white', relief=tk.SOLID, bd=1)
        entry_frame.pack(fill=tk.X, pady=(0, 15))
        
        entry = tk.Entry(entry_frame,
                        font=('Microsoft YaHei', 16),
                        bg='white',
                        fg=UI_COLORS['text_primary'],
                        relief=tk.FLAT,
                        justify=tk.CENTER)
        entry.pack(fill=tk.X, padx=10, pady=10)
        entry.insert(0, "1")
        entry.select_range(0, tk.END)
        entry.focus()
        
        # Range hint
        tk.Label(content_frame,
                text=f"Please enter an integer between {minvalue} and {maxvalue}",
                font=('Microsoft YaHei', 11),
                fg=UI_COLORS['text_light'],
                bg=UI_COLORS['bg_panel']).pack()
        
        def validate_and_confirm():
            try:
                value = int(entry.get())
                if minvalue <= value <= maxvalue:
                    result[0] = value
                    dialog.destroy()
                else:
                    messagebox.showwarning("Input Error", 
                                        f"Please enter an integer between {minvalue} and {maxvalue}",
                                        parent=dialog)
                    entry.select_range(0, tk.END)
                    entry.focus()
            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid integer", parent=dialog)
                entry.delete(0, tk.END)
                entry.insert(0, "1")
                entry.select_range(0, tk.END)
                entry.focus()
        
        def on_cancel():
            result[0] = None
            dialog.destroy()
        
        # Button area
        btn_frame = tk.Frame(dialog, bg=UI_COLORS['bg_panel'])
        btn_frame.pack(fill=tk.X, padx=30, pady=(0, 25))
        
        tk.Button(btn_frame, text="✓ OK",
                command=validate_and_confirm,
                font=('Microsoft YaHei', 13, 'bold'),
                bg=UI_COLORS['primary'],
                fg='white',
                activebackground=UI_COLORS['primary_dark'],
                relief=tk.FLAT,
                cursor='hand2',
                padx=25, pady=10).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(btn_frame, text="✗ Cancel",
                command=on_cancel,
                font=('Microsoft YaHei', 13, 'bold'),
                bg=UI_COLORS['text_light'],
                fg='white',
                activebackground=UI_COLORS['text_secondary'],
                relief=tk.FLAT,
                cursor='hand2',
                padx=25, pady=10).pack(side=tk.LEFT)
        
        entry.bind('<Return>', lambda e: validate_and_confirm())
        entry.bind('<Escape>', lambda e: on_cancel())
        
        self.ui.root.wait_window(dialog)
        return result[0]

    def _auto_select_parallel_strategy(self, c_pts, o_pts, ck, ok, orientation):
        """Auto test all parallel boundary strategies and select best solution"""
        if orientation == 'horizontal':
            strategies = ['c_left_o_left', 'c_left_o_right', 'c_right_o_left', 'c_right_o_right']
        else:
            strategies = ['c_top_o_top', 'c_top_o_bottom', 'c_bottom_o_top', 'c_bottom_o_bottom']

        return self._test_strategies_and_select_best(c_pts, o_pts, ck, ok, strategies, is_parallel=True)

    def _auto_select_L_shaped_strategy(self, c_pts, o_pts, ck, ok, vertical_boundary, horizontal_boundary):
        """Auto test all L-shaped boundary strategies and select best solution"""
        strategies = [
            ('bottom_to_top', 'left_to_right'),
            ('bottom_to_top', 'right_to_left'),
            ('top_to_bottom', 'left_to_right'),
            ('top_to_bottom', 'right_to_left')
        ]

        return self._test_strategies_and_select_best(
            c_pts, o_pts, ck, ok, strategies,
            is_parallel=False,
            vertical_boundary=vertical_boundary,
            horizontal_boundary=horizontal_boundary
        )

    def _test_strategies_and_select_best(self, c_pts, o_pts, ck, ok, strategies,
                                         is_parallel=True, vertical_boundary=None, horizontal_boundary=None):
        """Test all strategies and select best solution

        Logic:
        1. Test all strategies (don't terminate early)
        2. Comparison criteria: success rate > performance (nodes_explored + diagonal_checks)
        3. Don't clear data after last strategy test completes
        4. If last strategy is optimal, keep its result; otherwise clear and re-route
        """
        import copy

        all_terminals = set(tuple(p) for p in self.ui.ctx['center_backups_ordered']) | \
                       set(tuple(p) for p in self.ui.ctx['out_backups_ordered'])

        # Record results for each strategy
        strategy_results = []

        self.ui.log(f"  [Strategy Testing] {len(strategies)} strategies to test")

        # Save current complete state
        saved_occupation_grid = self.ui.router.occupation_grid.copy()
        saved_diagonal_bitmap = self.ui.router.diagonal_bitmap.copy()
        saved_reserved_points = copy.deepcopy(self.ui.router.global_reserved_points)
        saved_diagonal_occupied = copy.deepcopy(self.ui.router.diagonal_occupied_points)
        saved_net_id = self.ui.ctx['current_net_id']
        saved_external_paths = copy.deepcopy(self.ui.ctx.get('external_paths', []))
        saved_stats = copy.deepcopy(self.ui.router.stats)

        for idx, strategy in enumerate(strategies, 1):
            # Create point pairs
            if is_parallel:
                pairs, order_desc, has_mismatch = create_parallel_pairs(c_pts, o_pts, ck, ok, strategy)
                strategy_name = order_desc
            else:
                vertical_order, horizontal_order = strategy
                pairs, v_order_desc, h_order_desc, has_mismatch = create_L_shaped_pairs(
                    c_pts, o_pts, ck, ok,
                    vertical_boundary, horizontal_boundary,
                    vertical_order, horizontal_order
                )
                strategy_name = f"Vertical{v_order_desc}, Horizontal{h_order_desc}"
                order_desc = strategy_name

            self.ui.log(f"    [Test {idx}/{len(strategies)}] {strategy_name}")

            # Record statistics before testing
            stats_before = copy.deepcopy(self.ui.router.stats)

            # Test routing
            success_count = 0
            for pair in pairs:
                s, e = tuple(pair['start']), tuple(pair['end'])
                path = self.ui.router.route_single_net(
                    s, e, self.ui.ctx['current_net_id'],
                    restrict_to_bbox=None,
                    all_terminals=all_terminals,
                    restrict_poly_path=self.ui.poly_path
                )
                if path:
                    success_count += 1
                    self.ui.ctx['external_paths'].append(path)

                self.ui.ctx['current_net_id'] += 1

            # Calculate performance metrics
            nodes_explored = self.ui.router.stats['nodes_explored'] - stats_before['nodes_explored']
            diagonal_checks = self.ui.router.stats['diagonal_checks'] - stats_before['diagonal_checks']
            performance_cost = nodes_explored + diagonal_checks

            success_rate = success_count / len(pairs) if pairs else 0
            self.ui.log(f"      Success rate: {success_count}/{len(pairs)} ({success_rate*100:.1f}%)")
            self.ui.log(f"      Performance: Explored nodes{nodes_explored} + Diagonal checks{diagonal_checks} = {performance_cost}")

            # Record result
            strategy_results.append({
                'idx': idx,
                'strategy': strategy,
                'pairs': pairs,
                'desc': order_desc,
                'success_rate': success_rate,
                'performance_cost': performance_cost
            })

            # Not the last strategy, clear data to prepare for next test
            if idx < len(strategies):
                self.ui.log(f"      [State recovery] Clear test data, prepare for next strategy")
                self.ui.router.occupation_grid = saved_occupation_grid.copy()
                self.ui.router.diagonal_bitmap = saved_diagonal_bitmap.copy()
                self.ui.router.global_reserved_points = copy.deepcopy(saved_reserved_points)
                self.ui.router.diagonal_occupied_points = copy.deepcopy(saved_diagonal_occupied)
                self.ui.ctx['current_net_id'] = saved_net_id
                self.ui.ctx['external_paths'] = copy.deepcopy(saved_external_paths)
                self.ui.router.stats = copy.deepcopy(saved_stats)

        # Select best strategy: compare success rate first, then performance
        best_result = max(strategy_results, key=lambda x: (x['success_rate'], -x['performance_cost']))

        self.ui.log(f"  ✓ [Final selection] {best_result['desc']}")
        self.ui.log(f"  ✓ [Success rate] {best_result['success_rate']*100:.1f}%")
        self.ui.log(f"  ✓ [Performance cost] {best_result['performance_cost']}")
        self.ui.log(f"  ✓ [Pair count] {len(best_result['pairs'])}")

        # Determine if re-routing is needed
        already_routed = (best_result['idx'] == len(strategies))

        if already_routed:
            self.ui.log(f"  [Keep result] Last tested strategy is optimal, keep its routing result")
        else:
            self.ui.log(f"  [Re-route] Optimal strategy is not the last tested, restore initial state and re-route")
            self.ui.router.occupation_grid = saved_occupation_grid.copy()
            self.ui.router.diagonal_bitmap = saved_diagonal_bitmap.copy()
            self.ui.router.global_reserved_points = copy.deepcopy(saved_reserved_points)
            self.ui.router.diagonal_occupied_points = copy.deepcopy(saved_diagonal_occupied)
            self.ui.ctx['current_net_id'] = saved_net_id
            self.ui.ctx['external_paths'] = copy.deepcopy(saved_external_paths)
            self.ui.router.stats = copy.deepcopy(saved_stats)

        if is_parallel:
            return best_result['pairs'], best_result['desc'], already_routed
        else:
            return best_result['pairs'], best_result['desc'].split(',')[0].replace('Vertical', ''), best_result['desc'].split(',')[1].replace('Horizontal', ''), already_routed


    def finish(self):
        """Complete stage 3"""
        self.ui.control_panel.hide_all_dynamic_frames()

        self._cleanup_incomplete_paths()
        
        self.ui.stage3_time = time.time() - self.ui.stage_start_time
        region_time = time.time() - self.ui.region_start_time
        
        self.ui.log(f"Stage 3 completed, generated {len(self.ui.ctx['external_paths'])} external connections",
                'SUCCESS')
        self.ui.log(f"[Timing] Stage 3 external routing total time: {format_time(self.ui.stage3_time)}",
                'TIMING')
        self.ui.log(f"[Timing] Region {self.ui.task_count} pure routing total time: "
                f"{format_time(self.ui.stage1_time + self.ui.stage2_time + self.ui.stage3_time)}",
                'TIMING')
        
        # Print performance statistics
        stats = self.ui.router.print_stats()
        self.ui.log(f"\n  [Performance statistics]")
        self.ui.log(f"    Explored nodes: {stats['nodes_explored']}")
        self.ui.log(f"    Diagonal check count: {stats['diagonal_checks']}")
        
        timer_var = self.ui.control_panel.get_widget('timer_var')
        timer_var.set(f"⏱️ Region total time: {format_time(region_time)}")

        # Merge paths
        self._merge_routing_paths()

        smooth_result = messagebox.askyesno(
            "Path Smoothing",
            "Routing completed!\n\n"
            "Apply path smoothing to routing paths?\n\n"
            "Smoothing will:\n"
            "• Merge collinear segments, reduce redundant points\n"
            "• Optimize corners, reduce turns\n"
            "• Maintain minimum spacing constraints\n\n"
            "Note: Smoothed paths are more suitable for chip fabrication"
        )
        
        if smooth_result:
            self._apply_path_smoothing()
        else:
            # No smoothing, display merged paths
            merged_paths = self.ui.ctx.get('merged_paths', [])
            self.ui._plot_base_grid(
                title=f"Region {self.ui.task_count} - Final Result (Merged Paths)",
                center_backups=self.ui.ctx['center_backups_ordered'],
                out_backups=self.ui.ctx['out_backups_ordered'],
                out_points=self.ui.valid_out,
                current_paths=merged_paths,
                show_region=True
            )
        
        stage_var = self.ui.control_panel.get_widget('stage_var')
        stage_var.set("✅ All Stages Complete")
        self.ui._show_region_complete_buttons()
    
    def _cleanup_incomplete_paths(self):
        """
        Clean up incomplete paths and their occupation states

        When counts are inconsistent, some Out or Center backup points in stage 3 may not be connectable.
        This causes some internal paths from stage 1 or stage 2 to be unused. These isolated internal paths
        need to be deleted, and their occupation states in router (occupation_grid, diagonal_bitmap, etc.) need to be cleaned up.
        """
        if not self.ui.ctx['external_paths']:
            return

        # Collect all backup points participating in external connections
        used_center_backups = set()
        used_out_backups = set()

        for path in self.ui.ctx['external_paths']:
            if len(path) >= 2:
                start_point = tuple(path[0])
                end_point = tuple(path[-1])

                for backup in self.ui.ctx['center_backups_ordered']:
                    if tuple(backup) == start_point:
                        used_center_backups.add(start_point)
                        break

                for backup in self.ui.ctx['out_backups_ordered']:
                    if tuple(backup) == end_point:
                        used_out_backups.add(end_point)
                        break

        # Clean up unused internal paths and their occupation states
        original_internal_count = len(self.ui.ctx['internal_paths'])
        cleaned_internal_paths = []
        removed_out_paths = 0
        removed_center_paths = 0
        removed_backup_points = []

        for idx, path in enumerate(self.ui.ctx['internal_paths']):
            if len(path) < 2:
                continue

            path_start = tuple(path[0])
            path_end = tuple(path[-1])

            is_out_path = any(tuple(backup) == path_end for backup in self.ui.ctx['out_backups_ordered'])
            is_center_path = any(tuple(backup) == path_start for backup in self.ui.ctx['center_backups_ordered'])

            keep_path = True

            if is_out_path:
                if path_end not in used_out_backups:
                    keep_path = False
                    removed_out_paths += 1
                    removed_backup_points.append(path_end)
                    # Clean up occupation state of this path
                    self.ui.router.remove_path_occupation(path)
            elif is_center_path:
                if path_start not in used_center_backups:
                    keep_path = False
                    removed_center_paths += 1
                    removed_backup_points.append(path_start)
                    self.ui.router.remove_path_occupation(path)

            if keep_path:
                cleaned_internal_paths.append(path)

        # Clean up unused backup points from global_reserved_points
        for bp in removed_backup_points:
            self.ui.router.global_reserved_points.discard(bp)

        if removed_out_paths > 0 or removed_center_paths > 0:
            self.ui.ctx['internal_paths'] = cleaned_internal_paths
            self.ui.log(f"\n  [Path cleanup]", 'INFO')
            self.ui.log(f"    Original internal path count: {original_internal_count}")
            self.ui.log(f"    Removed unused Out internal paths: {removed_out_paths}")
            self.ui.log(f"    Removed unused Center internal paths: {removed_center_paths}")
            self.ui.log(f"    Cleaned backup point count: {len(removed_backup_points)}")
            self.ui.log(f"    Retained internal path count: {len(cleaned_internal_paths)}")
            self.ui.log(f"    External connection path count: {len(self.ui.ctx['external_paths'])}")
            self.ui.log(f"  ✓ Isolated paths and their occupation states cleaned up", 'SUCCESS')

    def _merge_routing_paths(self):
        """
        Merge three-stage routing paths

        Merge segmented paths into complete paths, each path from Center point to Out point.
        Number of merged paths equals min(Center point count, Out point count).
        """
        self.ui.log("\n" + "="*50)
        self.ui.log("Starting to merge routing paths...", 'INFO')
        self.ui.log("="*50)

        merge_start_time = time.time()

        try:
            # Execute path merging
            merged_paths = merge_paths(
                internal_paths=self.ui.ctx['internal_paths'],
                external_paths=self.ui.ctx['external_paths'],
                center_backups_ordered=self.ui.ctx['center_backups_ordered'],
                out_backups_ordered=self.ui.ctx['out_backups_ordered']
            )

            merge_time = time.time() - merge_start_time

            # Print merge statistics
            self.ui.log(f"\n  [Path merge statistics]", 'SUCCESS')
            self.ui.log(f"    Original internal path count: {len(self.ui.ctx['internal_paths'])}")
            self.ui.log(f"    Original external path count: {len(self.ui.ctx['external_paths'])}")
            self.ui.log(f"    Merged complete path count: {len(merged_paths)}")
            self.ui.log(f"  [Timing] Path merge time: {format_time(merge_time)}", 'TIMING')
            self.ui.log(f"  ✓ Path merge completed", 'SUCCESS')

            # Save merged paths to context
            self.ui.ctx['merged_paths'] = merged_paths

        except Exception as e:
            self.ui.log(f"Path merge failed: {str(e)}", 'ERROR')
            import traceback
            traceback.print_exc()

    def _apply_path_smoothing(self):
        """
        Apply path smoothing algorithm

        Perform smoothing processing on all paths in the current region and visualize results
        """
        self.ui.log("\n" + "="*50)
        self.ui.log("Starting path smoothing processing...", 'INFO')
        self.ui.log("="*50)

        smooth_start_time = time.time()

        try:
            # Get grid size
            grid_size = self.ui.grid_mgr.grid_size if hasattr(self.ui.grid_mgr, 'grid_size') else 15

            # Use merged paths for smoothing
            merged_paths = self.ui.ctx.get('merged_paths', [])

            smoothed_merged, _, smooth_stats = smooth_region_paths(
                internal_paths=merged_paths,
                external_paths=[],
                grid_size=grid_size,
                min_spacing=grid_size
            )

            # Save smoothed paths to context
            self.ui.ctx['smoothed_merged_paths'] = smoothed_merged

            smooth_time = time.time() - smooth_start_time

            # Print smoothing statistics
            self.ui.log(f"\n  [Path smoothing statistics]", 'SUCCESS')
            self.ui.log(f"    Total path count: {smooth_stats['total_paths']}")
            self.ui.log(f"    Original total point count: {smooth_stats['original_total_points']}")
            self.ui.log(f"    Smoothed total point count: {smooth_stats['smoothed_total_points']}")
            self.ui.log(f"    Reduced point count: {smooth_stats['point_reduction']} "
                       f"({smooth_stats['point_reduction']/smooth_stats['original_total_points']*100:.1f}%)")
            self.ui.log(f"    Average points per path: {smooth_stats['avg_points_per_path_before']:.1f} → "
                       f"{smooth_stats['avg_points_per_path_after']:.1f}")
            self.ui.log(f"    Original turn count: {smooth_stats['original_total_turns']}")
            self.ui.log(f"    Smoothed turn count: {smooth_stats['smoothed_total_turns']}")
            self.ui.log(f"    Reduced turns: {smooth_stats['turn_reduction']} "
                       f"({smooth_stats['turn_reduction']/smooth_stats['original_total_turns']*100:.1f}%)"
                       if smooth_stats['original_total_turns'] > 0 else "    Reduced turns: 0")
            self.ui.log(f"  [Timing] Path smoothing time: {format_time(smooth_time)}", 'TIMING')
            self.ui.log(f"  ✓ Path smoothing completed", 'SUCCESS')

            # Visualize smoothed paths
            self.ui._plot_base_grid(
                title=f"Region {self.ui.task_count} - Final Result (Smoothed)",
                center_backups=self.ui.ctx['center_backups_ordered'],
                out_backups=self.ui.ctx['out_backups_ordered'],
                out_points=self.ui.valid_out,
                current_paths=smoothed_merged,
                show_region=True,
                is_smoothed=True
            )

            # Ask if user wants to compare original and smoothed paths
            compare_result = messagebox.askyesno(
                "Compare Paths",
                "View comparison between original paths and smoothed paths?"
            )

            if compare_result:
                self._show_path_comparison()

        except Exception as e:
            self.ui.log(f"Path smoothing failed: {str(e)}", 'ERROR')
            import traceback
            traceback.print_exc()

            # On failure, display merged original paths
            merged_paths = self.ui.ctx.get('merged_paths', [])
            self.ui._plot_base_grid(
                title=f"Region {self.ui.task_count} - Final Result (Merged Paths)",
                center_backups=self.ui.ctx['center_backups_ordered'],
                out_backups=self.ui.ctx['out_backups_ordered'],
                out_points=self.ui.valid_out,
                current_paths=merged_paths,
                show_region=True
            )
    
    def _show_path_comparison(self):
        """Display comparison between original paths and smoothed paths"""
        # Create comparison window
        from ..config.ui_config import UI_COLORS
        from ..utils.helpers import center_window_right
        
        compare_window = tk.Toplevel(self.ui.root)
        compare_window.title("Path Comparison")
        compare_window.geometry("500x400")
        compare_window.configure(bg=UI_COLORS['bg_panel'])
        compare_window.transient(self.ui.root)
        
        center_window_right(compare_window, self.ui.root)
        
        # Title
        title_frame = tk.Frame(compare_window, bg=UI_COLORS['primary'], height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="📊 Path Comparison",
                font=('Microsoft YaHei', 14, 'bold'),
                fg='white', bg=UI_COLORS['primary']).pack(expand=True)
        
        # Content area
        content_frame = tk.Frame(compare_window, bg=UI_COLORS['bg_panel'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Description text
        tk.Label(content_frame,
                text="Click buttons to switch between viewing merged paths and smoothed paths\nCanvas view will maintain current zoom state",
                font=('Microsoft YaHei', 11),
                fg=UI_COLORS['text_secondary'],
                bg=UI_COLORS['bg_panel'],
                justify=tk.CENTER).pack(pady=(0, 15))
        
        # Buttons
        btn_frame = tk.Frame(content_frame, bg=UI_COLORS['bg_panel'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        def show_original():
            merged_paths = self.ui.ctx.get('merged_paths', [])
            total_points = sum(len(p) for p in merged_paths)

            self.ui._plot_base_grid(
                title=f"Region {self.ui.task_count} - Merged Paths (Red, {len(merged_paths)} paths, {total_points} points)",
                center_backups=self.ui.ctx['center_backups_ordered'],
                out_backups=self.ui.ctx['out_backups_ordered'],
                out_points=self.ui.valid_out,
                current_paths=merged_paths,
                show_region=True,
                is_smoothed=False
            )

        def show_smoothed():
            smoothed_merged = self.ui.ctx.get('smoothed_merged_paths', [])
            total_points = sum(len(p) for p in smoothed_merged)

            self.ui._plot_base_grid(
                title=f"Region {self.ui.task_count} - Smoothed Paths (Blue, {len(smoothed_merged)} paths, {total_points} points)",
                center_backups=self.ui.ctx['center_backups_ordered'],
                out_backups=self.ui.ctx['out_backups_ordered'],
                out_points=self.ui.valid_out,
                current_paths=smoothed_merged,
                show_region=True,
                is_smoothed=True
            )
        
        tk.Button(btn_frame, text="View Merged Paths",
                 command=show_original,
                 font=('Microsoft YaHei', 11, 'bold'),
                 bg=UI_COLORS['secondary'],
                 fg='white',
                 relief=tk.FLAT,
                 cursor='hand2',
                 padx=20, pady=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="View Smoothed Paths",
                 command=show_smoothed,
                 font=('Microsoft YaHei', 11, 'bold'),
                 bg=UI_COLORS['primary'],
                 fg='white',
                 relief=tk.FLAT,
                 cursor='hand2',
                 padx=20, pady=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Close",
                 command=compare_window.destroy,
                 font=('Microsoft YaHei', 11, 'bold'),
                 bg=UI_COLORS['text_light'],
                 fg='white',
                 relief=tk.FLAT,
                 cursor='hand2',
                 padx=20, pady=10).pack(side=tk.RIGHT, padx=5)
