"""
canvas_area.py - Canvas area component
Canvas area component for visualization and rendering using Matplotlib.
Capable of handling grid plotting, path display, region selection, and interactive selectors.
"""

import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.widgets import PolygonSelector, RectangleSelector
import matplotlib.patches as patches

from ..config.ui_config import UI_COLORS, CANVAS_COLORS, CANVAS_SIZES, LEGEND_CONFIG


class CanvasArea:
    """Canvas area class - responsible for drawing and visualization"""
    
    def __init__(self, parent, callbacks):
        self.parent = parent
        self.callbacks = callbacks
        self.fig = None
        self.ax = None
        self.canvas = None
        self.polygon_selector = None
        self.rect_selector = None
        self._selected_points_artist = None
        
        # 🔴 New: Save view state
        self.view_state = {
            'xlim': None,
            'ylim': None,
            'has_custom_view': False
        }
        
        self.create_canvas()
    
    def create_canvas(self):
        """Create canvas area"""
        # Top title bar
        title_frame = tk.Frame(self.parent, bg=UI_COLORS['bg_panel'], height=60)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)
        
        title_container = tk.Frame(title_frame, bg=UI_COLORS['bg_panel'])
        title_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        tk.Label(title_container, text="Routing Canvas", 
                font=('Microsoft YaHei', 20, 'bold'),
                fg=UI_COLORS['primary_dark'],
                bg=UI_COLORS['bg_panel']).pack(side=tk.LEFT)

        tk.Label(title_container, text="Left:Select | Right:Box Select",
                font=('Microsoft YaHei', 15),
                fg=UI_COLORS['text_light'],
                bg=UI_COLORS['bg_panel']).pack(side=tk.RIGHT)
                
        # Canvas container
        canvas_frame = tk.Frame(self.parent, bg='white', relief=tk.SOLID, bd=1)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Matplotlib canvas
        self.fig, self.ax = plt.subplots(figsize=(14, 10), facecolor='white')
        self.fig.tight_layout(pad=2)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        
        # Toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, canvas_frame)
        toolbar.update()
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Bind events
        self.canvas.mpl_connect('button_press_event', self.callbacks['on_canvas_click'])
        self.canvas.mpl_connect('key_press_event', self.callbacks['on_canvas_key'])
        
        # Initial welcome screen
        self.show_welcome()
    
    def show_welcome(self):
        """Display welcome screen"""
        self.ax.clear()
        self.ax.text(0.5, 0.5,
                    'Photonic Quantum Chip Routing System\n\nv0.0.0\n\n'
                    'Please import CSV data file first',
                    ha='center', va='center',
                    fontsize=16, color=UI_COLORS['text_light'],
                    transform=self.ax.transAxes)
        self.ax.axis('off')
        self.canvas.draw()
    
    def plot_base_grid(self, grid_mgr, all_finished_paths=None, title="",
                      center_backups=None, out_backups=None, out_points=None,
                      current_paths=None, show_region=False, poly_path=None,
                      selected_vertices=None, is_smoothed=False,
                      center_backups_grouped=None, out_backups_grouped=None):
        """
        Plot base grid and all paths and points
        
        Args:
            is_smoothed: Whether it's a smoothed path (affects drawing style)
        """
        if grid_mgr is None:
            return
        
        # 🔴 Save current view state (if user has zoomed/panned)
        self._save_current_view_state()
        
        self.ax.clear()
        
        # Configure color mapping
        colors = {
            1: CANVAS_COLORS['out_point'],
            2: CANVAS_COLORS['center_point'],
            3: CANVAS_COLORS['obstacle'],
            4: CANVAS_COLORS['chip_range']
        }
        labels = {1: 'Out Point', 2: 'Center Point', 3: 'Obstacle', 4: 'Chip Boundary'}
        
        # Plot base points
        for val, color in colors.items():
            points = np.argwhere(grid_mgr.grid == val)
            if len(points) > 0:
                if val == 1 and out_points is not None:
                    continue
                self.ax.scatter(points[:, 1], points[:, 0], c=color, 
                            s=CANVAS_SIZES['base_point'],
                            label=labels[val], 
                            alpha=CANVAS_SIZES['base_point_alpha'], 
                            edgecolors='none')
        
        # Historical paths
        if all_finished_paths:
            for i, path in enumerate(all_finished_paths):
                lbl = 'Completed Routing' if i == 0 else None
                self.ax.plot(np.array(path)[:, 0], np.array(path)[:, 1],
                        color=CANVAS_COLORS['finished_path'],
                        linewidth=CANVAS_SIZES['history_path_width'],
                        alpha=CANVAS_SIZES['history_path_alpha'], 
                        label=lbl)
        
        # Current region Out points
        if out_points is not None and len(out_points) > 0:
            out_pts = np.array(out_points)
            self.ax.scatter(out_pts[:, 0], out_pts[:, 1], 
                        c=CANVAS_COLORS['current_out'],
                        s=CANVAS_SIZES['current_out'],
                        label='Current Region Out Points', 
                        edgecolors='#01579B', 
                        linewidth=CANVAS_SIZES['point_edge_width'],
                        zorder=5)

        # Center backup points (with numbering)
        if center_backups is not None and len(center_backups) > 0:
            cb_pts = np.array(center_backups)
            self.ax.scatter(cb_pts[:, 0], cb_pts[:, 1],
                        c=CANVAS_COLORS['center_backup'],
                        marker='s',
                        s=CANVAS_SIZES['backup_point'],
                        label='Center Backup Points',
                        edgecolors=CANVAS_COLORS['center_backup_edge'],
                        linewidth=CANVAS_SIZES['point_edge_width'],
                        zorder=6)

            if len(center_backups) < 100:
                # Create point to boundary mapping
                point_to_boundary = {}
                if center_backups_grouped:
                    for boundary, pts in center_backups_grouped.items():
                        for pt in pts:
                            point_to_boundary[tuple(pt)] = boundary

                for i, p in enumerate(center_backups):
                    # Determine label position based on boundary
                    boundary = point_to_boundary.get(tuple(p), None)
                    if boundary == 'Left':
                        x_offset = -CANVAS_SIZES['text_offset']
                        y_offset = 0
                        ha, va = 'right', 'center'
                    elif boundary == 'Right':
                        x_offset = CANVAS_SIZES['text_offset']
                        y_offset = 0
                        ha, va = 'left', 'center'
                    elif boundary == 'Top':
                        x_offset = 0
                        y_offset = CANVAS_SIZES['text_offset']
                        ha, va = 'center', 'bottom'
                    elif boundary == 'Bottom':
                        x_offset = 0
                        y_offset = -CANVAS_SIZES['text_offset']
                        ha, va = 'center', 'top'
                    else:
                        # Default position (above)
                        x_offset = 0
                        y_offset = CANVAS_SIZES['text_offset']
                        ha, va = 'center', 'bottom'

                    self.ax.text(p[0] + x_offset, p[1] + y_offset,
                            str(i+1), color=CANVAS_COLORS['center_backup_text'],
                            fontsize=CANVAS_SIZES['text_fontsize'],
                            fontweight='bold', ha=ha, va=va,
                            bbox=dict(boxstyle='round,pad=' + str(CANVAS_SIZES['text_padding']),
                                        facecolor=CANVAS_COLORS['text_box_face'],
                                        edgecolor=CANVAS_COLORS['center_backup'],
                                        alpha=CANVAS_SIZES['text_box_alpha'],
                                        linewidth=1.5),
                            zorder=11)

        # Out backup points (with numbering)
        if out_backups is not None and len(out_backups) > 0:
            ob_pts = np.array(out_backups)
            self.ax.scatter(ob_pts[:, 0], ob_pts[:, 1],
                        c=CANVAS_COLORS['out_backup'],
                        marker='^',
                        s=CANVAS_SIZES['backup_point'],
                        label='Out Backup Points',
                        edgecolors=CANVAS_COLORS['out_backup_edge'],
                        linewidth=CANVAS_SIZES['point_edge_width'],
                        zorder=6)

            if len(out_backups) < 100:
                # Create point to boundary mapping
                point_to_boundary = {}
                if out_backups_grouped:
                    for boundary, pts in out_backups_grouped.items():
                        for pt in pts:
                            point_to_boundary[tuple(pt)] = boundary

                for i, p in enumerate(out_backups):
                    # Determine label position based on boundary
                    boundary = point_to_boundary.get(tuple(p), None)
                    if boundary == 'Left':
                        x_offset = -CANVAS_SIZES['text_offset']
                        y_offset = 0
                        ha, va = 'right', 'center'
                    elif boundary == 'Right':
                        x_offset = CANVAS_SIZES['text_offset']
                        y_offset = 0
                        ha, va = 'left', 'center'
                    elif boundary == 'Top':
                        x_offset = 0
                        y_offset = CANVAS_SIZES['text_offset']
                        ha, va = 'center', 'bottom'
                    elif boundary == 'Bottom':
                        x_offset = 0
                        y_offset = -CANVAS_SIZES['text_offset']
                        ha, va = 'center', 'top'
                    else:
                        # Default position (above)
                        x_offset = 0
                        y_offset = CANVAS_SIZES['text_offset']
                        ha, va = 'center', 'bottom'

                    self.ax.text(p[0] + x_offset, p[1] + y_offset,
                            str(i+1), color=CANVAS_COLORS['out_backup_text'],
                            fontsize=CANVAS_SIZES['text_fontsize'],
                            fontweight='bold', ha=ha, va=va,
                            bbox=dict(boxstyle='round,pad=' + str(CANVAS_SIZES['text_padding']),
                                        facecolor=CANVAS_COLORS['text_box_face'],
                                        edgecolor=CANVAS_COLORS['out_backup'],
                                        alpha=CANVAS_SIZES['text_box_alpha'],
                                        linewidth=1.5),
                            zorder=11)
        
        # Region boundary
        if show_region and poly_path and selected_vertices and len(selected_vertices) > 0:
            patch = patches.PathPatch(poly_path, facecolor='none',
                                    edgecolor=CANVAS_COLORS['region_border'],
                                    linestyle='--',
                                    linewidth=CANVAS_SIZES['border_width'],
                                    label='Current Routing Region', zorder=4)
            self.ax.add_patch(patch)
        
        # Current paths
        if current_paths:
            for i, path in enumerate(current_paths):
                if is_smoothed:
                    # 🔴 Smoothed path: use dark blue thick line
                    lbl = 'Smoothed Routing' if i == 0 else None
                    path_array = np.array(path)
                    self.ax.plot(path_array[:, 0], path_array[:, 1],
                            color='#1976D2',  # Dark blue
                            linewidth=3.5,  # 🔴 Thicker
                            alpha=0.9,  # 🔴 More opaque
                            label=lbl, zorder=7,
                            linestyle='-',
                            marker='o',
                            markersize=5,  # 🔴 Larger marker points
                            markerfacecolor='#1976D2',
                            markeredgecolor='white',
                            markeredgewidth=1.0)
                else:
                    # 🔴 Original path: use red thin line
                    lbl = 'New Routing' if i == 0 else None
                    self.ax.plot(np.array(path)[:, 0], np.array(path)[:, 1],
                            color='#D32F2F',  # 🔴 Changed to red for distinction
                            linewidth=2.0,  # 🔴 Thinner
                            alpha=0.7,  # 🔴 More transparent
                            label=lbl, zorder=7,
                            linestyle='-',
                            marker='.',
                            markersize=3)
        
        # Draw grid lines
        for x in range(grid_mgr.w):
            self.ax.axvline(x=x, color=CANVAS_COLORS['grid_line'], linestyle='-',
                        alpha=CANVAS_SIZES['grid_line_alpha'], 
                        linewidth=CANVAS_SIZES['grid_line_width'])
        for y in range(grid_mgr.h):
            self.ax.axhline(y=y, color=CANVAS_COLORS['grid_line'], linestyle='-',
                        alpha=CANVAS_SIZES['grid_line_alpha'], 
                        linewidth=CANVAS_SIZES['grid_line_width'])
        
        self.ax.set_xlim(-1, grid_mgr.w)
        self.ax.set_ylim(-1, grid_mgr.h)
        self.ax.set_aspect('equal')
        self.ax.set_facecolor(CANVAS_COLORS['background'])
        self.ax.set_title(title if title else "Photonic Quantum Chip Routing System",
                        fontsize=14, fontweight='bold', pad=15,
                        color=UI_COLORS['text_primary'])
        
        # Legend optimization - use settings from config file to avoid obscuring routing content
        handles, labels_list = self.ax.get_legend_handles_labels()
        by_label = dict(zip(labels_list, handles))

        # Build legend parameters (including all spacing and size controls)
        legend_params = {
            'loc': LEGEND_CONFIG['loc'],
            'fontsize': LEGEND_CONFIG['fontsize'],
            'framealpha': LEGEND_CONFIG['framealpha'],
            'fancybox': LEGEND_CONFIG['fancybox'],
            'shadow': LEGEND_CONFIG['shadow'],
            'ncol': LEGEND_CONFIG['ncol'],
            'borderpad': LEGEND_CONFIG['borderpad'],
            'labelspacing': LEGEND_CONFIG['labelspacing'],
            'handlelength': LEGEND_CONFIG['handlelength'],
            'handletextpad': LEGEND_CONFIG['handletextpad'],
            'columnspacing': LEGEND_CONFIG['columnspacing'],
            'markerscale': LEGEND_CONFIG['markerscale']
        }

        # Add border color (if specified in config)
        if LEGEND_CONFIG['edgecolor'] is not None:
            legend_params['edgecolor'] = LEGEND_CONFIG['edgecolor']
        else:
            legend_params['edgecolor'] = UI_COLORS['border']

        # Add bbox_to_anchor (if specified in config)
        if LEGEND_CONFIG['bbox_to_anchor'] is not None:
            legend_params['bbox_to_anchor'] = LEGEND_CONFIG['bbox_to_anchor']

        legend = self.ax.legend(by_label.values(), by_label.keys(), **legend_params)
        legend.get_frame().set_facecolor(LEGEND_CONFIG['facecolor'])
        
        self.ax.grid(False)
        
        # 🔴 Restore view state (if exists)
        self._restore_view_state(grid_mgr)
        
        self.canvas.draw()
    
    def plot_boundary_selection(self, grid_mgr, direction, available_points,
                                bounding_box, selected_points):
        """Plot boundary selection interface"""
        # 🔴 Save current view state
        self._save_current_view_state()
        
        self.ax.clear()
        
        colors = {
            1: CANVAS_COLORS['out_point'],
            2: CANVAS_COLORS['center_point'],
            3: CANVAS_COLORS['obstacle'],
            4: CANVAS_COLORS['chip_range']
        }
        
        # Draw background points (semi-transparent)
        for val, color in colors.items():
            points = np.argwhere(grid_mgr.grid == val)
            if len(points) > 0:
                self.ax.scatter(points[:, 1], points[:, 0], c=color, 
                            s=CANVAS_SIZES['background_point'],
                            alpha=CANVAS_SIZES['background_point_alpha'], 
                            edgecolors='none')
        
        # Draw bounding box
        xmin, ymin, xmax, ymax = bounding_box
        rect = patches.Rectangle((xmin, ymin), xmax-xmin, ymax-ymin,
                                linewidth=CANVAS_SIZES['border_width'],
                                edgecolor=CANVAS_COLORS['bounding_box'],
                                facecolor='none', linestyle='--')
        self.ax.add_patch(rect)
        
        # Draw available points
        if len(available_points) > 0:
            avail = np.array(available_points)
            self.ax.scatter(avail[:, 0], avail[:, 1], 
                        c=CANVAS_COLORS['available_point'],
                        s=CANVAS_SIZES['available_point'],
                        edgecolors=CANVAS_COLORS['available_point_edge'], 
                        linewidth=CANVAS_SIZES['point_edge_width'],
                        label='Available Points', zorder=5)
        
        # Draw selected points
        if len(selected_points) > 0:
            sel_pts = np.array(selected_points)
            self._selected_points_artist = self.ax.scatter(
                sel_pts[:, 0], sel_pts[:, 1], 
                c=CANVAS_COLORS['selected_point'],
                s=CANVAS_SIZES['selected_point'],
                marker='*', 
                edgecolors=CANVAS_COLORS['selected_point_edge'], 
                linewidths=CANVAS_SIZES['border_width'],
                label='Selected Points', zorder=10
            )
        
        # Draw grid lines
        for x in range(grid_mgr.w):
            self.ax.axvline(x=x, color=CANVAS_COLORS['grid_line'], linestyle='-',
                        alpha=CANVAS_SIZES['grid_line_alpha'], 
                        linewidth=CANVAS_SIZES['grid_line_width'])
        for y in range(grid_mgr.h):
            self.ax.axhline(y=y, color=CANVAS_COLORS['grid_line'], linestyle='-',
                        alpha=CANVAS_SIZES['grid_line_alpha'], 
                        linewidth=CANVAS_SIZES['grid_line_width'])
        
        self.ax.set_xlim(-1, grid_mgr.w)
        self.ax.set_ylim(-1, grid_mgr.h)
        self.ax.set_aspect('equal')
        self.ax.set_facecolor(CANVAS_COLORS['background'])
        self.ax.set_title(f"📍 Please select points belonging to [{direction} boundary]\n"
                        f"Left click to select | Right drag to box select | Ctrl+Z to undo | "
                        f"Selected: {len(selected_points)} points",
                        fontsize=12, fontweight='bold', pad=15,
                        color=UI_COLORS['text_primary'])
        
        # Legend - use settings from config file (including all spacing controls)
        legend_params = {
            'loc': LEGEND_CONFIG['loc'],
            'fontsize': LEGEND_CONFIG['fontsize'],
            'framealpha': LEGEND_CONFIG['framealpha'],
            'fancybox': LEGEND_CONFIG['fancybox'],
            'shadow': LEGEND_CONFIG['shadow'],
            'ncol': LEGEND_CONFIG['ncol'],
            'borderpad': LEGEND_CONFIG['borderpad'],
            'labelspacing': LEGEND_CONFIG['labelspacing'],
            'handlelength': LEGEND_CONFIG['handlelength'],
            'handletextpad': LEGEND_CONFIG['handletextpad'],
            'columnspacing': LEGEND_CONFIG['columnspacing'],
            'markerscale': LEGEND_CONFIG['markerscale']
        }
        if LEGEND_CONFIG['edgecolor'] is not None:
            legend_params['edgecolor'] = LEGEND_CONFIG['edgecolor']
        else:
            legend_params['edgecolor'] = UI_COLORS['border']

        if LEGEND_CONFIG['bbox_to_anchor'] is not None:
            legend_params['bbox_to_anchor'] = LEGEND_CONFIG['bbox_to_anchor']

        legend = self.ax.legend(**legend_params)
        legend.get_frame().set_facecolor(LEGEND_CONFIG['facecolor'])
        
        # 🔴 Restore view state
        self._restore_view_state(grid_mgr)
        
        self.canvas.draw()
    
    def update_selected_points_display(self, selected_points):
        """Incrementally update selected points display"""
        if self._selected_points_artist:
            try:
                self._selected_points_artist.remove()
            except:
                pass
        
        if len(selected_points) > 0:
            sel_pts = np.array(selected_points)
            self._selected_points_artist = self.ax.scatter(
                sel_pts[:, 0], sel_pts[:, 1], 
                c=CANVAS_COLORS['selected_point'],
                s=CANVAS_SIZES['selected_point'],
                marker='*', 
                edgecolors=CANVAS_COLORS['selected_point_edge'], 
                linewidths=CANVAS_SIZES['border_width'],
                label='Selected Points', zorder=10
            )
        
        # Update title
        current_title = self.ax.get_title()
        base_title = current_title.split('\n')[0]
        self.ax.set_title(f"{base_title}\n"
                        f"Left click to select | Right drag to box select | Ctrl+Z to undo | "
                        f"Selected: {len(selected_points)} points",
                        fontsize=12, fontweight='bold', pad=15,
                        color=UI_COLORS['text_primary'])
        
        self.canvas.draw_idle()
    
    def setup_polygon_selector(self, on_region_selected):
        """Setup polygon selector"""
        self.polygon_selector = PolygonSelector(
            self.ax,
            on_region_selected,
            props=dict(color='#66BB6A', linestyle='--', linewidth=2.8, alpha=0.6),
            handle_props=dict(markersize=10, markerfacecolor='#66BB6A',
                            markeredgecolor='#43A047')
        )
    
    def setup_rect_selector(self, on_rect_select):
        """Setup rectangle selector"""
        if self.rect_selector:
            try:
                self.rect_selector.set_active(False)
            except:
                pass
        
        self.rect_selector = RectangleSelector(
            self.ax, on_rect_select,
            useblit=True,
            button=[3],
            minspanx=5, minspany=5,
            spancoords='pixels',
            interactive=False,
            props=dict(facecolor=CANVAS_COLORS['rect_selector_face'],
                    edgecolor=CANVAS_COLORS['rect_selector_edge'],
                    alpha=CANVAS_SIZES['rect_selector_alpha'],
                    linewidth=2)
        )
    
    def clear_selectors(self):
        """Clear all selectors"""
        if self.polygon_selector:
            try:
                self.polygon_selector.disconnect_events()
            except:
                pass
            self.polygon_selector = None
        
        if self.rect_selector:
            try:
                self.rect_selector.set_active(False)
            except:
                pass
            self.rect_selector = None
    
    def _save_current_view_state(self):
        """Save current view state (zoom and pan)"""
        if self.ax is not None:
            try:
                current_xlim = self.ax.get_xlim()
                current_ylim = self.ax.get_ylim()
                
                # 🔴 Fix: only save valid view state
                # Check if it's a meaningful view range (not initial 0-1 range)
                if current_xlim is not None and current_ylim is not None:
                    # Only save if view range is not default 0-1
                    # This avoids saving welcome screen view state
                    xlim_range = current_xlim[1] - current_xlim[0]
                    ylim_range = current_ylim[1] - current_ylim[0]
                    
                    # Only save if range > 2 (indicates actual grid view)
                    if xlim_range > 2 and ylim_range > 2:
                        self.view_state['xlim'] = current_xlim
                        self.view_state['ylim'] = current_ylim
                        self.view_state['has_custom_view'] = True
            except:
                pass
    
    def _restore_view_state(self, grid_mgr):
        """Restore view state"""
        if self.view_state['has_custom_view'] and self.view_state['xlim'] is not None:
            try:
                # 🔴 Fix: restore custom view after setting default range
                # This ensures axis is initialized
                self.ax.set_xlim(self.view_state['xlim'])
                self.ax.set_ylim(self.view_state['ylim'])
            except Exception as e:
                # If restore fails, use default view
                print(f"Failed to restore view: {e}")
                self.ax.set_xlim(-1, grid_mgr.w)
                self.ax.set_ylim(-1, grid_mgr.h)
                # Clear failed view state
                self.view_state['has_custom_view'] = False
    
    def reset_view_state(self):
        """Reset view state to default"""
        self.view_state = {
            'xlim': None,
            'ylim': None,
            'has_custom_view': False
        }
