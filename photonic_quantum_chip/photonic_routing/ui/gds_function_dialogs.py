"""
gds_function_dialogs.py - GDS function dialogs
Fully integrated version, all functions completed in UI, no need to call terminal
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
from pathlib import Path

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
except ImportError:
    FigureCanvasTkAgg = None
    NavigationToolbar2Tk = None

from ..config.ui_config import UI_COLORS
from ..config.paths import INPUT_DIR, INPUT_GDS_DIR, INPUT_CSV_DIR, ROUTING_DIR, GDS_DIR
from ..utils.helpers import center_window_right
from ..utils.gds_tools import GDSProcessor, PathExporter
from .styles import setup_styles


# ==================== Helper functions ====================

def create_styled_button(parent, text, command, **kwargs):
    """Create button with system color scheme

    Args:
        parent: Parent container
        text: Button text
        command: Click callback function
        **kwargs: Other tk.Button parameters

    Returns:
        tk.Button: Configured button
    """
    # Default style
    default_style = {
        'font': ('Microsoft YaHei', 10, 'bold'),
        'bg': UI_COLORS['secondary'],  # Green
        'fg': 'white',
        'activebackground': '#689F38',  # Dark green
        'activeforeground': 'white',
        'relief': tk.FLAT,
        'cursor': 'hand2',
        'padx': 15,
        'pady': 8,
        'bd': 0,
        'highlightthickness': 0
    }

    # Merge user-provided styles
    default_style.update(kwargs)

    # Create button
    btn = tk.Button(parent, text=text, command=command, **default_style)

    # Add hover effect
    def on_enter(e):
        btn.config(bg='#689F38')

    def on_leave(e):
        btn.config(bg=UI_COLORS['secondary'])

    btn.bind('<Enter>', on_enter)
    btn.bind('<Leave>', on_leave)

    return btn


# ==================== GDS coordinate extraction dialog ====================

class GDSExtractionDialog(tk.Toplevel):
    """GDS coordinate extraction dialog - fully integrated version"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("GDS Coordinate Extraction Tool")
        self.geometry("1400x900")
        center_window_right(self, parent)

        # Set dialog background color to light blue
        self.configure(bg=UI_COLORS['bg_main'])

        # Apply styles
        setup_styles()

        # Data storage
        self.gds_file = None
        self.processor = None
        self.rectangle_configs = []  # Store rectangle configuration list
        self.result_df = None
        self.result_figure = None
        self.available_cells = []

        # UI component references
        self.progress_var = None
        self.log_text = None
        self.canvas_frame = None
        self.start_button = None

        self._create_ui()

    def _create_ui(self):
        """Create UI interface"""
        # Create main container
        main_container = ttk.Frame(self, style='Dialog.TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Use Notebook to create multi-step interface
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Step 1: File selection
        self.step1_frame = self._create_step1_file_selection()
        self.notebook.add(self.step1_frame, text="1. File Selection")

        # Step 2: Rectangle configuration
        self.step2_frame = self._create_step2_rectangle_config()
        self.notebook.add(self.step2_frame, text="2. Rectangle Configuration")

        # Step 3: Grid and processing options
        self.step3_frame = self._create_step3_processing_options()
        self.notebook.add(self.step3_frame, text="3. Processing Options")

        # Step 4: Execution and results
        self.step4_frame = self._create_step4_execution()
        self.notebook.add(self.step4_frame, text="4. Execution and Results")

        # Bottom button bar
        self._create_bottom_buttons(main_container)

    def _create_step1_file_selection(self):
        """Step 1: File selection interface"""
        frame = ttk.Frame(self.notebook, padding=10, style='Dialog.TFrame')

        # GDS file selection
        file_frame = ttk.LabelFrame(frame, text="GDS File", padding=10, style='Dialog.TLabelframe')
        file_frame.pack(fill=tk.X, pady=5)

        self.gds_file_var = tk.StringVar()
        ttk.Label(file_frame, text="File path:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(file_frame, textvariable=self.gds_file_var, width=60).grid(row=0, column=1, padx=5, pady=5)
        create_styled_button(file_frame, text="Browse...", command=self.browse_gds_file).grid(row=0, column=2, pady=5)

        # Cell name
        cell_frame = ttk.LabelFrame(frame, text="Cell Selection", padding=10, style='Dialog.TLabelframe')
        cell_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(cell_frame, text="Available Cells:", style='Dialog.TLabel').pack(anchor=tk.W, pady=5)

        # Listbox to display available cells
        list_frame = ttk.Frame(cell_frame, style='Dialog.TFrame')
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.cells_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=10)
        self.cells_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.cells_listbox.yview)

        # Load button
        create_styled_button(cell_frame, text="Load GDS File", command=self.load_gds_file).pack(pady=10)

        return frame

    def _create_step2_rectangle_config(self):
        """Step 2: Rectangle configuration interface"""
        frame = ttk.Frame(self.notebook, padding=10, style='Dialog.TFrame')

        # Instruction text
        ttk.Label(frame, text="Add rectangle configurations to extract:", font=('', 10, 'bold'), style='Dialog.TLabel').pack(anchor=tk.W, pady=5)

        # Treeview to display configurations
        tree_frame = ttk.Frame(frame, style='Dialog.TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Create Treeview
        columns = ('Cell', 'Label', 'Width', 'Height', 'Position', 'Direction')
        self.rect_config_tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=15)

        # Set columns
        self.rect_config_tree.heading('#0', text='#')
        self.rect_config_tree.column('#0', width=50)

        # Set column widths
        column_widths = {
            'Cell': 150,
            'Label': 100,
            'Width': 80,
            'Height': 80,
            'Position': 120,
            'Direction': 100
        }
        for col in columns:
            self.rect_config_tree.heading(col, text=col)
            self.rect_config_tree.column(col, width=column_widths.get(col, 120))

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.rect_config_tree.yview)
        self.rect_config_tree.configure(yscrollcommand=scrollbar.set)

        self.rect_config_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        button_frame = ttk.Frame(frame, style='Dialog.TFrame')
        button_frame.pack(fill=tk.X, pady=5)

        create_styled_button(button_frame, text="Add Rectangle", command=self.add_rectangle_config).pack(side=tk.LEFT, padx=5)
        create_styled_button(button_frame, text="Edit", command=self.edit_rectangle_config).pack(side=tk.LEFT, padx=5)
        create_styled_button(button_frame, text="Delete", command=self.delete_rectangle_config).pack(side=tk.LEFT, padx=5)

        return frame

    def _create_step3_processing_options(self):
        """Step 3: Grid and processing options interface"""
        frame = ttk.Frame(self.notebook, padding=10, style='Dialog.TFrame')

        # Grid size setting
        grid_frame = ttk.LabelFrame(frame, text="Grid Settings", padding=10, style='Dialog.TLabelframe')
        grid_frame.pack(fill=tk.X, pady=5)

        ttk.Label(grid_frame, text="Grid size:", style='Dialog.TLabel').grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.grid_size_var = tk.DoubleVar(value=15.0)
        ttk.Entry(grid_frame, textvariable=self.grid_size_var, width=20).grid(row=0, column=1, padx=5, pady=5)

        # Obstacle expansion options
        obstacle_frame = ttk.LabelFrame(frame, text="Obstacle Expansion", padding=10, style='Dialog.TLabelframe')
        obstacle_frame.pack(fill=tk.X, pady=5)

        self.enable_obstacle_expansion = tk.BooleanVar(value=False)
        # Use tk.Checkbutton for better cross-platform display
        obstacle_check = tk.Checkbutton(obstacle_frame, text="Enable obstacle expansion",
                                       variable=self.enable_obstacle_expansion,
                                       command=self._toggle_obstacle_expansion,
                                       bg=UI_COLORS['bg_main'],
                                       fg='#2C3E50',
                                       activebackground=UI_COLORS['bg_main'],
                                       activeforeground='#4A90E2',
                                       selectcolor=UI_COLORS['bg_main'],
                                       font=('Microsoft YaHei', 10))
        obstacle_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        ttk.Label(obstacle_frame, text="Left/Right expansion grids:", style='Dialog.TLabel').grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.left_right_grids_var = tk.IntVar(value=1)
        self.left_right_entry = ttk.Entry(obstacle_frame, textvariable=self.left_right_grids_var, width=20, state='disabled')
        self.left_right_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(obstacle_frame, text="Top/Bottom expansion grids:", style='Dialog.TLabel').grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.top_bottom_grids_var = tk.IntVar(value=1)
        self.top_bottom_entry = ttk.Entry(obstacle_frame, textvariable=self.top_bottom_grids_var, width=20, state='disabled')
        self.top_bottom_entry.grid(row=2, column=1, padx=5, pady=5)

        # Special obstacle processing
        special_frame = ttk.LabelFrame(frame, text="Special Obstacle Processing", padding=10, style='Dialog.TLabelframe')
        special_frame.pack(fill=tk.X, pady=5)

        self.enable_special_obstacle = tk.BooleanVar(value=False)
        # Use tk.Checkbutton for better cross-platform display
        special_check = tk.Checkbutton(special_frame, text="Enable special obstacle processing",
                                      variable=self.enable_special_obstacle,
                                      command=self._toggle_special_obstacle,
                                      bg=UI_COLORS['bg_main'],
                                      fg='#2C3E50',
                                      activebackground=UI_COLORS['bg_main'],
                                      activeforeground='#4A90E2',
                                      selectcolor=UI_COLORS['bg_main'],
                                      font=('Microsoft YaHei', 10))
        special_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        ttk.Label(special_frame, text="Target label:", style='Dialog.TLabel').grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.target_label_var = tk.StringVar(value='center')
        self.target_label_entry = ttk.Entry(special_frame, textvariable=self.target_label_var, width=20, state='disabled')
        self.target_label_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(special_frame, text="Distance parameter:", style='Dialog.TLabel').grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.distance_var = tk.DoubleVar(value=100.0)
        self.distance_entry = ttk.Entry(special_frame, textvariable=self.distance_var, width=20, state='disabled')
        self.distance_entry.grid(row=2, column=1, padx=5, pady=5)

        return frame

    def _create_step4_execution(self):
        """Step 4: Execution and results interface"""
        # Create main container
        main_container = ttk.Frame(self.notebook, style='Dialog.TFrame')

        # Create scrollable Canvas
        canvas = tk.Canvas(main_container, bg=UI_COLORS['bg_main'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Dialog.TFrame')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Bind mouse wheel event - using a safer approach
        def _on_mousewheel(event):
            try:
                # Check if canvas still exists
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                # If canvas has been destroyed, ignore error
                pass

        # Directly bind to scrollable_frame, avoid using bind_all
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<MouseWheel>", _on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        frame = scrollable_frame

        # Execution control
        control_frame = ttk.LabelFrame(frame, text="Execution Control", padding=10, style='Dialog.TLabelframe')
        control_frame.pack(fill=tk.X, pady=5, padx=5)

        self.start_button = create_styled_button(control_frame, text="Start Extraction", command=self.start_extraction)
        self.start_button.pack(pady=5)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(control_frame, variable=self.progress_var, maximum=100).pack(fill=tk.X, pady=5)

        self.status_label = ttk.Label(control_frame, text="Ready", style='Dialog.TLabel')
        self.status_label.pack(pady=5)

        # Log output
        log_frame = ttk.LabelFrame(frame, text="Processing Log", padding=10, style='Dialog.TLabelframe')
        log_frame.pack(fill=tk.X, pady=5, padx=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Visualization results
        viz_frame = ttk.LabelFrame(frame, text="Visualization Results", padding=10, style='Dialog.TLabelframe')
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

        self.canvas_frame = ttk.Frame(viz_frame, style='Dialog.TFrame')
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Export buttons
        export_frame = ttk.Frame(frame, style='Dialog.TFrame')
        export_frame.pack(fill=tk.X, pady=5, padx=5)

        create_styled_button(export_frame, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        create_styled_button(export_frame, text="Save Image", command=self.save_visualization).pack(side=tk.LEFT, padx=5)

        return main_container

    def _create_bottom_buttons(self, parent):
        """Create bottom button bar"""
        button_frame = ttk.Frame(parent, style='Dialog.TFrame')
        button_frame.pack(fill=tk.X, pady=(10, 0))

        create_styled_button(button_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    # ==================== Event Handler Methods ====================

    def browse_gds_file(self):
        """Browse GDS file"""
        kwargs = {
            "title": "Select GDS File",
            "filetypes": [("GDS Files", "*.gds"), ("All Files", "*.*")]
        }
        if INPUT_GDS_DIR.exists():
            kwargs["initialdir"] = str(INPUT_GDS_DIR)

        filename = filedialog.askopenfilename(**kwargs)
        if filename:
            self.gds_file_var.set(filename)

    def load_gds_file(self):
        """Load GDS file and initialize processor"""
        gds_file = self.gds_file_var.get().strip()
        if not gds_file:
            messagebox.showerror("Error", "Please select a GDS file first")
            return

        if not os.path.exists(gds_file):
            messagebox.showerror("Error", "File does not exist")
            return

        try:
            # Create GDSProcessor instance
            self.processor = GDSProcessor(gds_file, progress_callback=self.update_progress)
            self.gds_file = gds_file

            # Get available cell list
            self.available_cells = self.processor.get_cell_names()

            # Update Listbox
            self.cells_listbox.delete(0, tk.END)
            for cell in self.available_cells:
                self.cells_listbox.insert(tk.END, cell)

            messagebox.showinfo("Success", f"GDS file loaded, found {len(self.available_cells)} cells")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load GDS file: {str(e)}")

    def add_rectangle_config(self):
        """Add rectangle configuration"""
        if not self.processor:
            messagebox.showerror("Error", "Please load a GDS file first")
            return

        dialog = RectangleConfigDialog(self, self.available_cells)
        self.wait_window(dialog)

        configs = dialog.result
        if configs:
            # New dialog returns configuration list
            if isinstance(configs, list):
                self.rectangle_configs.extend(configs)
            else:
                self.rectangle_configs.append(configs)
            self._update_config_tree()

    def edit_rectangle_config(self):
        """Edit rectangle configuration"""
        selection = self.rect_config_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a configuration to edit")
            return

        index = int(self.rect_config_tree.item(selection[0])['text']) - 1
        config = self.rectangle_configs[index]

        dialog = RectangleConfigDialog(self, self.available_cells, config)
        self.wait_window(dialog)

        new_config = dialog.result
        if new_config:
            self.rectangle_configs[index] = new_config
            self._update_config_tree()

    def delete_rectangle_config(self):
        """Delete rectangle configuration"""
        selection = self.rect_config_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a configuration to delete")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete the selected configuration?"):
            index = int(self.rect_config_tree.item(selection[0])['text']) - 1
            del self.rectangle_configs[index]
            self._update_config_tree()

    def _update_config_tree(self):
        """Update configuration tree display"""
        # Clear tree
        for item in self.rect_config_tree.get_children():
            self.rect_config_tree.delete(item)

        # Add configurations
        for i, config in enumerate(self.rectangle_configs, 1):
            direction_str = config.get('direction', '') or 'None'
            cell_name = config.get('cell_name', '')
            self.rect_config_tree.insert('', tk.END, text=str(i), values=(
                cell_name,
                config['label'],
                config['width'],
                config['height'],
                config['position'],
                direction_str
            ))

    def _toggle_obstacle_expansion(self):
        """Toggle obstacle expansion option"""
        state = 'normal' if self.enable_obstacle_expansion.get() else 'disabled'
        self.left_right_entry.config(state=state)
        self.top_bottom_entry.config(state=state)

    def _toggle_special_obstacle(self):
        """Toggle special obstacle processing option"""
        state = 'normal' if self.enable_special_obstacle.get() else 'disabled'
        self.target_label_entry.config(state=state)
        self.distance_entry.config(state=state)

    # ==================== Core Processing Methods ====================

    def start_extraction(self):
        """Start coordinate extraction (run in background thread)"""
        if not self.processor:
            messagebox.showerror("Error", "Please load GDS file first")
            return

        if not self.rectangle_configs:
            messagebox.showerror("Error", "Please add at least one rectangle configuration")
            return

        # Disable start button
        self.start_button.config(state='disabled')
        self.status_label.config(text="Processing...")

        # Clear log
        self.log_text.delete(1.0, tk.END)

        # Run extraction in background thread
        thread = threading.Thread(target=self._extraction_worker, daemon=True)
        thread.start()

    def _extraction_worker(self):
        """Background thread worker function"""
        try:
            # 1. Extract all configured rectangles
            self.update_progress("Starting rectangle extraction...", 0)

            for i, config in enumerate(self.rectangle_configs):
                # Set direction bounds (if any)
                if config.get('direction') and config.get('direction_bounds'):
                    self.processor.set_direction_bounds(
                        config['direction'],
                        **config['direction_bounds']
                    )

                # Extract rectangle
                rectangles, error = self.processor.extract_rectangles(
                    config['cell_name'],
                    config['width'],
                    config['height'],
                    config['label'],
                    config['position'],
                    config.get('direction'),
                    config.get('tolerance', 0.001)
                )

                if error:
                    self.update_progress(f"Warning: {error}", None)
                else:
                    self.processor.all_coordinates.extend(rectangles)
                    self.update_progress(f"Extracted {len(rectangles)} points ({config['label']})",
                                       (i + 1) / len(self.rectangle_configs) * 30)

            # 2. Map to grid
            self.update_progress("Mapping to grid...", 40)
            grid_size = self.grid_size_var.get()
            self.result_df = self.processor.map_to_grid(grid_size)

            # 3. Obstacle expansion (if enabled)
            if self.enable_obstacle_expansion.get():
                self.update_progress("Expanding obstacles...", 60)
                self.processor.expand_obstacles(
                    self.left_right_grids_var.get(),
                    self.top_bottom_grids_var.get()
                )

            # 4. Special obstacle processing (if enabled)
            if self.enable_special_obstacle.get():
                self.update_progress("Special obstacle processing...", 70)
                self.processor.add_obstacle_between_points(
                    self.target_label_var.get(),
                    self.distance_var.get()
                )

            # 5. Create visualization
            self.update_progress("Generating visualization...", 80)
            self.result_figure = self.processor.create_visualization()

            # 6. Update UI in main thread
            self.after(0, self._display_results)

            self.update_progress("Extraction completed!", 100)
            self.after(0, lambda: self.status_label.config(text="Completed"))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Extraction failed: {str(e)}"))
            self.after(0, lambda: self.status_label.config(text="Failed"))
        finally:
            # Re-enable start button
            self.after(0, lambda: self.start_button.config(state='normal'))

    def _display_results(self):
        """Display results in main thread"""
        # Clear previous canvas
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        # Create new matplotlib canvas
        if self.result_figure and FigureCanvasTkAgg:
            # Adjust image size to fit window, maintain reasonable aspect ratio
            # Use more reasonable dimensions to ensure complete content display
            self.result_figure.set_size_inches(12, 9)

            # Ensure compact layout to avoid content truncation
            self.result_figure.tight_layout(pad=1.0)

            canvas = FigureCanvasTkAgg(self.result_figure, master=self.canvas_frame)
            canvas.draw()

            # Add matplotlib navigation toolbar (includes zoom, pan, etc.)
            if NavigationToolbar2Tk:
                toolbar_frame = ttk.Frame(self.canvas_frame, style='Dialog.TFrame')
                toolbar_frame.pack(side=tk.TOP, fill=tk.X)
                toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
                toolbar.update()

            # Use fill=tk.BOTH and expand=True to make image adapt to window size
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)

    def update_progress(self, message, percent):
        """Update progress (thread safe)"""
        def _update():
            if percent is not None:
                self.progress_var.set(percent)
            if self.log_text:
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)

        self.after(0, _update)

    def export_csv(self):
        """Export CSV file"""
        if not self.processor or not self.processor.all_coordinates:
            messagebox.showerror("Error", "No data to export")
            return

        kwargs = {
            "defaultextension": ".csv",
            "filetypes": [("CSV Files", "*.csv"), ("All Files", "*.*")]
        }
        if INPUT_CSV_DIR.exists():
            kwargs["initialdir"] = str(INPUT_CSV_DIR)

        filename = filedialog.asksaveasfilename(**kwargs)

        if filename:
            success, message = self.processor.save_to_csv(filename)
            if success:
                messagebox.showinfo("Success", f"CSV file saved\n\n{message}")
            else:
                messagebox.showerror("Error", message)

    def save_visualization(self):
        """Save visualization image"""
        if not self.result_figure:
            messagebox.showerror("Error", "No visualization result to save")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Images", "*.png"), ("All Files", "*.*")]
        )

        if filename:
            self.result_figure.savefig(filename, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Success", f"Image saved to: {filename}")

# ==================== Rectangle Configuration Dialog ====================

class RectangleConfigDialog(tk.Toplevel):
    """Rectangle configuration dialog - supports multi-direction configuration"""

    def __init__(self, parent, cell_names, initial_config=None):
        super().__init__(parent)
        self.title("Rectangle Configuration")
        self.geometry("600x650")
        center_window_right(self, parent)

        # Set dialog background color to light blue
        self.configure(bg=UI_COLORS['bg_main'])

        # Apply styles
        setup_styles()

        self.cell_names = cell_names
        self.initial_config = initial_config
        self.result = None  # Store configuration result (may be a single or list of configurations)

        # Direction-related UI component dictionary
        self.direction_widgets = {}

        self._create_ui()

        if initial_config:
            self._load_config(initial_config)

    def _create_ui(self):
        """Create UI"""
        # Create scrollable main container
        canvas = tk.Canvas(self, bg=UI_COLORS['bg_main'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Dialog.TFrame')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Bind mouse wheel event - use safer approach
        def _on_mousewheel(event):
            try:
                # Check if canvas still exists
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                # If canvas has been destroyed, ignore error
                pass

        # Bind directly to scrollable_frame and canvas, avoid using bind_all
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<MouseWheel>", _on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        main_frame = scrollable_frame

        # Cell selection
        cell_frame = ttk.LabelFrame(main_frame, text="Cell Selection", padding=10, style='Dialog.TLabelframe')
        cell_frame.pack(fill=tk.X, pady=5)

        ttk.Label(cell_frame, text="Cell Name:", style='Dialog.TLabel').grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.cell_var = tk.StringVar()
        cell_combo = ttk.Combobox(cell_frame, textvariable=self.cell_var, values=self.cell_names, width=40)
        cell_combo.grid(row=0, column=1, padx=5, pady=5)
        if self.cell_names:
            cell_combo.current(0)

        # Basic configuration
        basic_frame = ttk.LabelFrame(main_frame, text="Basic Configuration", padding=10, style='Dialog.TLabelframe')
        basic_frame.pack(fill=tk.X, pady=5)

        ttk.Label(basic_frame, text="Label Type:", style='Dialog.TLabel').grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.label_var = tk.StringVar(value='center')
        label_combo = ttk.Combobox(basic_frame, textvariable=self.label_var,
                                   values=['center', 'out', 'obstacle', 'chip_range'], width=40)
        label_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(basic_frame, text="Rectangle Width:", style='Dialog.TLabel').grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.width_var = tk.DoubleVar(value=10.0)
        ttk.Entry(basic_frame, textvariable=self.width_var, width=42).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(basic_frame, text="Rectangle Height:", style='Dialog.TLabel').grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.height_var = tk.DoubleVar(value=10.0)
        ttk.Entry(basic_frame, textvariable=self.height_var, width=42).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(basic_frame, text="Tolerance:", style='Dialog.TLabel').grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.tolerance_var = tk.DoubleVar(value=0.001)
        ttk.Entry(basic_frame, textvariable=self.tolerance_var, width=42).grid(row=3, column=1, padx=5, pady=5)

        # Position selection when no direction filtering
        ttk.Label(basic_frame, text="Key Point Position:", style='Dialog.TLabel').grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.default_position_var = tk.StringVar(value='center')
        self.default_position_combo = ttk.Combobox(basic_frame, textvariable=self.default_position_var,
                                     values=['center', 'top_left', 'top_right', 'bottom_left', 'bottom_right', 'all_vertices'], width=40)
        self.default_position_combo.grid(row=4, column=1, padx=5, pady=5)

        # Direction filtering
        direction_frame = ttk.LabelFrame(main_frame, text="Direction Filtering (Optional)", padding=10, style='Dialog.TLabelframe')
        direction_frame.pack(fill=tk.X, pady=5)

        self.enable_direction = tk.BooleanVar(value=False)
        # Use tk.Checkbutton for better cross-platform display
        direction_check = tk.Checkbutton(direction_frame, text="Enable Direction Filtering",
                                        variable=self.enable_direction,
                                        command=self._toggle_direction,
                                        bg=UI_COLORS['bg_main'],
                                        fg='#2C3E50',
                                        activebackground=UI_COLORS['bg_main'],
                                        activeforeground='#4A90E2',
                                        selectcolor=UI_COLORS['bg_main'],
                                        font=('Microsoft YaHei', 10))
        direction_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Create 4 direction configuration areas
        self.directions_container = ttk.Frame(direction_frame, style='Dialog.TFrame')
        self.directions_container.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=5)

        directions = ['top', 'bottom', 'left', 'right']
        direction_labels = {'top': 'Top', 'bottom': 'Bottom', 'left': 'Left', 'right': 'Right'}

        for i, direction in enumerate(directions):
            self._create_direction_section(self.directions_container, direction, direction_labels[direction], i)

        # Bottom buttons
        button_frame = ttk.Frame(main_frame, style='Dialog.TFrame')
        button_frame.pack(fill=tk.X, pady=10)

        create_styled_button(button_frame, text="OK", command=self._on_ok).pack(side=tk.RIGHT, padx=5)
        create_styled_button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)

        # Initial state: disable all direction configurations
        self._toggle_direction()

    def _create_direction_section(self, parent, direction, label, row):
        """Create single direction configuration area"""
        frame = ttk.LabelFrame(parent, text=f"{label} ({direction})", padding=5, style='Dialog.TLabelframe')
        frame.grid(row=row, column=0, sticky=tk.EW, pady=3)

        # Count input
        ttk.Label(frame, text="Count:", style='Dialog.TLabel').grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        count_var = tk.IntVar(value=0)
        count_entry = ttk.Entry(frame, textvariable=count_var, width=10)
        count_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        count_entry.bind('<KeyRelease>', lambda e, d=direction: self._on_count_changed(d))

        # Position selection
        ttk.Label(frame, text="Key Point Position:", style='Dialog.TLabel').grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        position_var = tk.StringVar(value='center')
        position_combo = ttk.Combobox(frame, textvariable=position_var,
                                     values=['center', 'top_left', 'top_right', 'bottom_left', 'bottom_right', 'all_vertices'],
                                     width=15, state='disabled')
        position_combo.grid(row=0, column=3, padx=5, pady=2)

        # Boundary settings
        bounds_frame = ttk.Frame(frame, style='Dialog.TFrame')
        bounds_frame.grid(row=1, column=0, columnspan=4, sticky=tk.EW, padx=5, pady=2)

        ttk.Label(bounds_frame, text="Bounds (Leave empty=unlimited):", style='Dialog.TLabel').grid(row=0, column=0, sticky=tk.W, padx=2)

        ttk.Label(bounds_frame, text="x_min:", style='Dialog.TLabel').grid(row=0, column=1, sticky=tk.W, padx=2)
        x_min_var = tk.StringVar()
        x_min_entry = ttk.Entry(bounds_frame, textvariable=x_min_var, width=10, state='disabled')
        x_min_entry.grid(row=0, column=2, padx=2)

        ttk.Label(bounds_frame, text="x_max:", style='Dialog.TLabel').grid(row=0, column=3, sticky=tk.W, padx=2)
        x_max_var = tk.StringVar()
        x_max_entry = ttk.Entry(bounds_frame, textvariable=x_max_var, width=10, state='disabled')
        x_max_entry.grid(row=0, column=4, padx=2)

        ttk.Label(bounds_frame, text="y_min:", style='Dialog.TLabel').grid(row=1, column=1, sticky=tk.W, padx=2)
        y_min_var = tk.StringVar()
        y_min_entry = ttk.Entry(bounds_frame, textvariable=y_min_var, width=10, state='disabled')
        y_min_entry.grid(row=1, column=2, padx=2)

        ttk.Label(bounds_frame, text="y_max:", style='Dialog.TLabel').grid(row=1, column=3, sticky=tk.W, padx=2)
        y_max_var = tk.StringVar()
        y_max_entry = ttk.Entry(bounds_frame, textvariable=y_max_var, width=10, state='disabled')
        y_max_entry.grid(row=1, column=4, padx=2)

        # Save all component references
        self.direction_widgets[direction] = {
            'frame': frame,
            'count_var': count_var,
            'count_entry': count_entry,
            'position_var': position_var,
            'position_combo': position_combo,
            'x_min_var': x_min_var,
            'x_min_entry': x_min_entry,
            'x_max_var': x_max_var,
            'x_max_entry': x_max_entry,
            'y_min_var': y_min_var,
            'y_min_entry': y_min_entry,
            'y_max_var': y_max_var,
            'y_max_entry': y_max_entry
        }

    def _toggle_direction(self):
        """Toggle direction filtering option"""
        enabled = self.enable_direction.get()
        state = 'normal' if enabled else 'disabled'

        # Toggle default position selection state (opposite to direction filtering)
        self.default_position_combo.config(state='disabled' if enabled else 'readonly')

        # Toggle all direction configuration area states
        for direction, widgets in self.direction_widgets.items():
            widgets['count_entry'].config(state=state)
            if not enabled:
                # When disabled, reset all values and disable all child components
                widgets['count_var'].set(0)
                widgets['position_combo'].config(state='disabled')
                for key in ['x_min_entry', 'x_max_entry', 'y_min_entry', 'y_max_entry']:
                    widgets[key].config(state='disabled')

    def _on_count_changed(self, direction):
        """When count for a direction changes"""
        widgets = self.direction_widgets[direction]
        try:
            count = widgets['count_var'].get()
            # If retrieval fails or is empty, default to 0
            if count is None or count == '':
                count = 0
        except (tk.TclError, ValueError):
            count = 0

        # If count > 0, enable other configuration items for this direction
        state = 'normal' if count > 0 else 'disabled'
        widgets['position_combo'].config(state='readonly' if count > 0 else 'disabled')
        widgets['x_min_entry'].config(state=state)
        widgets['x_max_entry'].config(state=state)
        widgets['y_min_entry'].config(state=state)
        widgets['y_max_entry'].config(state=state)

    def _load_config(self, config):
        """Load existing configuration to UI"""
        self.cell_var.set(config.get('cell_name', ''))
        self.label_var.set(config.get('label', 'center'))
        self.width_var.set(config.get('width', 10.0))
        self.height_var.set(config.get('height', 10.0))
        self.tolerance_var.set(config.get('tolerance', 0.001))

        # If there is direction configuration, load it
        if config.get('direction'):
            self.enable_direction.set(True)
            self._toggle_direction()

            direction = config['direction']
            if direction in self.direction_widgets:
                widgets = self.direction_widgets[direction]
                widgets['count_var'].set(1)  # Assume at least 1
                widgets['position_var'].set(config.get('position', 'center'))
                self._on_count_changed(direction)

                bounds = config.get('direction_bounds', {})
                if 'x_min' in bounds:
                    widgets['x_min_var'].set(str(bounds['x_min']))
                if 'x_max' in bounds:
                    widgets['x_max_var'].set(str(bounds['x_max']))
                if 'y_min' in bounds:
                    widgets['y_min_var'].set(str(bounds['y_min']))
                if 'y_max' in bounds:
                    widgets['y_max_var'].set(str(bounds['y_max']))
        else:
            self.default_position_var.set(config.get('position', 'center'))

    def _on_ok(self):
        """OK button handler"""
        try:
            # Validate required fields
            if not self.cell_var.get():
                messagebox.showerror("Error", "Please select a Cell name")
                return

            # Basic configuration
            base_config = {
                'cell_name': self.cell_var.get(),
                'label': self.label_var.get(),
                'width': self.width_var.get(),
                'height': self.height_var.get(),
                'tolerance': self.tolerance_var.get()
            }

            # If direction filtering is not enabled, return single configuration
            if not self.enable_direction.get():
                base_config['position'] = self.default_position_var.get()
                self.result = [base_config]  # Return list for consistency
                self.destroy()
                return

            # Direction filtering enabled: collect all valid direction configurations
            configs = []
            for direction, widgets in self.direction_widgets.items():
                count = widgets['count_var'].get()
                if count > 0:
                    # Create configuration for this direction
                    dir_config = base_config.copy()
                    dir_config['direction'] = direction
                    dir_config['position'] = widgets['position_var'].get()

                    # Collect boundary settings
                    bounds = {}
                    x_min = widgets['x_min_var'].get().strip()
                    if x_min:
                        bounds['x_min'] = float(x_min)
                    x_max = widgets['x_max_var'].get().strip()
                    if x_max:
                        bounds['x_max'] = float(x_max)
                    y_min = widgets['y_min_var'].get().strip()
                    if y_min:
                        bounds['y_min'] = float(y_min)
                    y_max = widgets['y_max_var'].get().strip()
                    if y_max:
                        bounds['y_max'] = float(y_max)

                    if bounds:
                        dir_config['direction_bounds'] = bounds

                    configs.append(dir_config)

            if not configs:
                messagebox.showerror("Error", "When direction filtering is enabled, at least one direction must have count > 0")
                return

            self.result = configs
            self.destroy()

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input value: {str(e)}")



# ==================== Path Export and Merge Dialog ====================

class PathExportDialog(tk.Toplevel):
    """Path materialization and merge dialog - fully integrated version"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Path Materialization and Merge Tool")
        self.geometry("900x700")
        center_window_right(self, parent)

        # Set dialog background color to light blue
        self.configure(bg=UI_COLORS['bg_main'])

        # Apply styles
        setup_styles()

        # Data storage
        self.exporter = PathExporter(progress_callback=self.update_progress)
        self.converted_paths = None

        self._create_ui()

    def _create_ui(self):
        """Create UI interface"""
        main_container = ttk.Frame(self, padding=10, style='Dialog.TFrame')
        main_container.pack(fill=tk.BOTH, expand=True)

        # File selection section
        file_frame = ttk.LabelFrame(main_container, text="File Selection", padding=10, style='Dialog.TLabelframe')
        file_frame.pack(fill=tk.X, pady=5)

        # PKL file
        ttk.Label(file_frame, text="PKL File:", style='Dialog.TLabel').grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.pkl_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.pkl_file_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        create_styled_button(file_frame, text="Browse...", command=lambda: self._browse_file(self.pkl_file_var, "PKL Files", "*.pkl", str(ROUTING_DIR))).grid(row=0, column=2, pady=5)

        # CSV file
        ttk.Label(file_frame, text="CSV File:", style='Dialog.TLabel').grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.csv_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.csv_file_var, width=50).grid(row=1, column=1, padx=5, pady=5)
        create_styled_button(file_frame, text="Browse...", command=lambda: self._browse_file(self.csv_file_var, "CSV Files", "*.csv", str(INPUT_CSV_DIR))).grid(row=1, column=2, pady=5)

        # Target GDS file
        ttk.Label(file_frame, text="Target GDS:", style='Dialog.TLabel').grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.target_gds_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.target_gds_var, width=50).grid(row=2, column=1, padx=5, pady=5)
        create_styled_button(file_frame, text="Browse...", command=lambda: self._browse_file(self.target_gds_var, "GDS Files", "*.gds", str(INPUT_GDS_DIR))).grid(row=2, column=2, pady=5)

        # Output GDS filename
        ttk.Label(file_frame, text="Output Filename:", style='Dialog.TLabel').grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_gds_var = tk.StringVar(value="merged_output.gds")
        ttk.Entry(file_frame, textvariable=self.output_gds_var, width=50).grid(row=3, column=1, padx=5, pady=5)

        # GDS parameters section
        param_frame = ttk.LabelFrame(main_container, text="GDS Parameters", padding=10, style='Dialog.TLabelframe')
        param_frame.pack(fill=tk.X, pady=5)

        ttk.Label(param_frame, text="Grid Size:", style='Dialog.TLabel').grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.grid_size_var = tk.DoubleVar(value=15.0)
        ttk.Entry(param_frame, textvariable=self.grid_size_var, width=20).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(param_frame, text="Layer:", style='Dialog.TLabel').grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.layer_var = tk.IntVar(value=31)
        ttk.Entry(param_frame, textvariable=self.layer_var, width=20).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(param_frame, text="Datatype:", style='Dialog.TLabel').grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.datatype_var = tk.IntVar(value=0)
        ttk.Entry(param_frame, textvariable=self.datatype_var, width=20).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(param_frame, text="Path Width:", style='Dialog.TLabel').grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.path_width_var = tk.DoubleVar(value=10.0)
        ttk.Entry(param_frame, textvariable=self.path_width_var, width=20).grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(param_frame, text="Target Cell Name:", style='Dialog.TLabel').grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.target_cell_var = tk.StringVar(value="testRouting")
        ttk.Entry(param_frame, textvariable=self.target_cell_var, width=20).grid(row=2, column=1, padx=5, pady=5)

        # Execution section
        exec_frame = ttk.LabelFrame(main_container, text="Execution", padding=10, style='Dialog.TLabelframe')
        exec_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Start button
        self.start_button = create_styled_button(exec_frame, text="Start Materialization and Merge", command=self.start_export)
        self.start_button.pack(pady=5)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(exec_frame, variable=self.progress_var, maximum=100).pack(fill=tk.X, pady=5)

        # Log output
        ttk.Label(exec_frame, text="Processing Log:", style='Dialog.TLabel').pack(anchor=tk.W, pady=5)
        self.log_text = scrolledtext.ScrolledText(exec_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Bottom buttons
        button_frame = ttk.Frame(main_container, style='Dialog.TFrame')
        button_frame.pack(fill=tk.X, pady=10)

        create_styled_button(button_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def _browse_file(self, var, title, filetype, initialdir=None):
        """Browse file"""
        if filetype.startswith("*."):
            ext = filetype[1:]
            filetypes = [(f"{title}", filetype), ("All Files", "*.*")]
        else:
            filetypes = [("All Files", "*.*")]

        kwargs = {"title": f"Select {title}", "filetypes": filetypes}
        if initialdir and os.path.exists(initialdir):
            kwargs["initialdir"] = initialdir

        filename = filedialog.askopenfilename(**kwargs)
        if filename:
            var.set(filename)

    def validate_inputs(self):
        """Validate input parameters"""
        # Check if files exist
        pkl_file = self.pkl_file_var.get().strip()
        if not pkl_file or not os.path.exists(pkl_file):
            return False, "PKL file does not exist"

        csv_file = self.csv_file_var.get().strip()
        if not csv_file or not os.path.exists(csv_file):
            return False, "CSV file does not exist"

        target_gds = self.target_gds_var.get().strip()
        if not target_gds or not os.path.exists(target_gds):
            return False, "Target GDS file does not exist"

        output_name = self.output_gds_var.get().strip()
        if not output_name:
            return False, "Please enter output filename"

        # Check numeric parameters
        try:
            grid_size = self.grid_size_var.get()
            if grid_size <= 0:
                return False, "Grid size must be greater than 0"

            layer = self.layer_var.get()
            datatype = self.datatype_var.get()

            path_width = self.path_width_var.get()
            if path_width <= 0:
                return False, "Path width must be greater than 0"

            target_cell = self.target_cell_var.get().strip()
            if not target_cell:
                return False, "Please enter target Cell name"

        except tk.TclError:
            return False, "Parameter format error"

        return True, None

    def start_export(self):
        """Start materialization and merge (runs in background thread)"""
        # Validate input
        valid, error = self.validate_inputs()
        if not valid:
            messagebox.showerror("Error", error)
            return

        # Disable start button
        self.start_button.config(state='disabled')

        # Clear log
        self.log_text.delete(1.0, tk.END)

        # Run in background thread
        thread = threading.Thread(target=self._export_worker, daemon=True)
        thread.start()

    def _export_worker(self):
        """Background thread worker function"""
        try:
            # Get output path - save to data/output/gds directory
            output_gds = GDS_DIR / self.output_gds_var.get().strip()

            # Call PathExporter for export and merge
            success, message, converted_paths = self.exporter.export_and_merge(
                self.pkl_file_var.get().strip(),
                self.csv_file_var.get().strip(),
                self.target_gds_var.get().strip(),
                str(output_gds),
                self.grid_size_var.get(),
                self.layer_var.get(),
                self.datatype_var.get(),
                self.path_width_var.get(),
                self.target_cell_var.get().strip()
            )

            if success:
                self.converted_paths = converted_paths
                self.after(0, lambda: messagebox.showinfo("Success", f"{message}\n\nOutput file: {output_gds}"))
            else:
                self.after(0, lambda: messagebox.showerror("Error", message))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Processing failed: {str(e)}"))
        finally:
            # Re-enable start button
            self.after(0, lambda: self.start_button.config(state='normal'))

    def update_progress(self, message, percent):
        """Update progress (thread-safe)"""
        def _update():
            if percent is not None:
                self.progress_var.set(percent)
            if self.log_text:
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)

        self.after(0, _update)


# ==================== Public Interface Functions ====================

def show_gds_extraction_dialog(parent):
    """Show GDS coordinate extraction dialog"""
    dialog = GDSExtractionDialog(parent)
    dialog.transient(parent)
    dialog.grab_set()

def show_path_export_dialog(parent):
    """Show path export and merge dialog"""
    dialog = PathExportDialog(parent)
    dialog.transient(parent)
    dialog.grab_set()

