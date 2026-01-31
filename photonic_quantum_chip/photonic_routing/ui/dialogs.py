"""
dialogs.py - Dialog Components
Dialog components for user interaction, including strategy selection and manual input functions.
Features a unified design style with enhanced visual effects.
"""

import tkinter as tk
from tkinter import messagebox
from ..config.ui_config import UI_COLORS
from ..utils.helpers import center_window_right


class ParallelStrategyDialog:
    """Parallel Boundary Strategy Selection Dialog - Optimized Version"""
    
    def __init__(self, parent, ck, ok, orientation):
        self.parent = parent
        self.ck = ck
        self.ok = ok
        self.orientation = orientation
        self.result = None
        
    def show(self):
        """Show dialog"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Select Parallel Boundary Routing Strategy")
        dialog.geometry("850x700")  # 🔴 Increase window size to accommodate auto strategy button
        dialog.configure(bg=UI_COLORS['bg_panel'])
        dialog.transient(self.parent)
        dialog.grab_set()
        
        center_window_right(dialog, self.parent)
        
        # 🔴 Optimization: Title bar - increased height and font size
        title_frame = tk.Frame(dialog, bg=UI_COLORS['primary'], height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        # Title container
        title_container = tk.Frame(title_frame, bg=UI_COLORS['primary'])
        title_container.pack(expand=True, fill=tk.BOTH, padx=25, pady=20)
        
        # Main title
        tk.Label(title_container, 
                text=f"🔀 Parallel Boundary Routing Strategy Selection",
                font=('Microsoft YaHei', 18, 'bold'),
                fg='white', 
                bg=UI_COLORS['primary']).pack(anchor=tk.W)
        
        # Subtitle
        tk.Label(title_container,
                text=f"Center-{self.ck} Boundary  ↔  Out-{self.ok} Boundary",
                font=('Microsoft YaHei', 14),
                fg='#E8F4FD',
                bg=UI_COLORS['primary']).pack(anchor=tk.W, pady=(5, 0))
        
        # 🔴 Optimization: Description area - increased padding and font size
        desc_frame = tk.Frame(dialog, bg=UI_COLORS['bg_panel'])
        desc_frame.pack(fill=tk.X, padx=25, pady=20)
        
        # Description text background box
        desc_box = tk.Frame(desc_frame, bg=UI_COLORS['primary_light'], 
                           relief=tk.FLAT, bd=1)
        desc_box.pack(fill=tk.X)
        
        if self.orientation == 'horizontal':
            desc_text = "This is a horizontal parallel boundary, please select point pair mapping and routing order strategy:"
            strategies = [
                ("1. Center leftmost ↔ Out leftmost\nThen route sequentially to the right", 'c_left_o_left'),
                ("2. Center leftmost ↔ Out rightmost\nThen route sequentially in reverse direction", 'c_left_o_right'),
                ("3. Center rightmost ↔ Out leftmost\nThen route sequentially in reverse direction", 'c_right_o_left'),
                ("4. Center rightmost ↔ Out rightmost\nThen route sequentially to the left", 'c_right_o_right'),
            ]
        else:
            desc_text = "This is a vertical parallel boundary, please select point pair mapping and routing order strategy:"
            strategies = [
                ("1. Center topmost ↔ Out topmost\nThen route sequentially downward", 'c_top_o_top'),
                ("2. Center topmost ↔ Out bottommost\nThen route sequentially in reverse direction", 'c_top_o_bottom'),
                ("3. Center bottommost ↔ Out topmost\nThen route sequentially in reverse direction", 'c_bottom_o_top'),
                ("4. Center bottommost ↔ Out bottommost\nThen route sequentially upward", 'c_bottom_o_bottom'),
            ]
        
        # 🔴 Increase description text font size
        tk.Label(desc_box, text=desc_text,
                font=('Microsoft YaHei', 13, 'bold'),
                fg=UI_COLORS['text_primary'],
                bg=UI_COLORS['primary_light'],
                wraplength=780,
                justify=tk.LEFT,
                padx=20, pady=15).pack(anchor=tk.W)
        
        # 🔴 Optimization: Strategy button area - 2x2 grid, increased spacing
        btn_frame = tk.Frame(dialog, bg=UI_COLORS['bg_panel'])
        btn_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(10, 25))

        btn_container = tk.Frame(btn_frame, bg=UI_COLORS['bg_panel'])
        btn_container.pack(fill=tk.BOTH, expand=True)

        btn_container.grid_columnconfigure(0, weight=1, uniform='col')
        btn_container.grid_columnconfigure(1, weight=1, uniform='col')
        btn_container.grid_rowconfigure(0, weight=1, uniform='row')
        btn_container.grid_rowconfigure(1, weight=1, uniform='row')
        btn_container.grid_rowconfigure(2, weight=1, uniform='row')

        for idx, (text, strategy) in enumerate(strategies):
            def make_callback(s):
                def callback():
                    self.result = s
                    dialog.destroy()
                return callback

            row = idx // 2
            col = idx % 2

            # 🔴 Button container (add shadow effect)
            btn_wrapper = tk.Frame(btn_container, bg=UI_COLORS['bg_panel'])
            btn_wrapper.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')

            # 🔴 Optimization: Increased button font size and padding
            btn = tk.Button(btn_wrapper, text=text,
                        command=make_callback(strategy),
                        font=('Microsoft YaHei', 14, 'bold'),  # Changed from 9 to 14
                        bg=UI_COLORS['secondary'],
                        fg='white',
                        activebackground='#689F38',
                        activeforeground='white',
                        relief=tk.FLAT,
                        cursor='hand2',
                        wraplength=340,
                        justify=tk.LEFT,
                        padx=20,
                        pady=20,  # Increased vertical padding
                        bd=0,
                        highlightthickness=0)
            btn.pack(fill=tk.BOTH, expand=True)

            # 🔴 Mouse hover effect
            def on_enter(e, b=btn):
                b.config(bg='#689F38')

            def on_leave(e, b=btn):
                b.config(bg=UI_COLORS['secondary'])

            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)

        # Auto strategy button
        auto_wrapper = tk.Frame(btn_container, bg=UI_COLORS['bg_panel'])
        auto_wrapper.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

        auto_btn = tk.Button(auto_wrapper, text="🤖 Auto select optimal strategy\nProgram will automatically test all strategies and select the one with highest success rate",
                    command=lambda: (setattr(self, 'result', 'auto'), dialog.destroy()),
                    font=('Microsoft YaHei', 14, 'bold'),
                    bg=UI_COLORS['primary'],
                    fg='white',
                    activebackground=UI_COLORS['primary_dark'],
                    activeforeground='white',
                    relief=tk.FLAT,
                    cursor='hand2',
                    wraplength=700,
                    justify=tk.CENTER,
                    padx=20,
                    pady=20,
                    bd=0,
                    highlightthickness=0)
        auto_btn.pack(fill=tk.BOTH, expand=True)

        def on_auto_enter(e):
            auto_btn.config(bg=UI_COLORS['primary_dark'])

        def on_auto_leave(e):
            auto_btn.config(bg=UI_COLORS['primary'])

        auto_btn.bind('<Enter>', on_auto_enter)
        auto_btn.bind('<Leave>', on_auto_leave)
        
        self.parent.wait_window(dialog)
        return self.result


class LShapedStrategyDialog:
    """L-shaped boundary strategy selection dialog - Optimized corrected version"""
    
    def __init__(self, parent, ck, ok, vertical_boundary, horizontal_boundary):
        self.parent = parent
        self.ck = ck
        self.ok = ok
        self.vertical_boundary = vertical_boundary
        self.horizontal_boundary = horizontal_boundary
        self.result = None
    
    def show(self):
        """Show dialog"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Select L-shaped Boundary Routing Strategy")
        dialog.geometry("900x740")  # 🔴 Increase window size to accommodate auto strategy button
        dialog.configure(bg=UI_COLORS['bg_panel'])
        dialog.transient(self.parent)
        dialog.grab_set()
        
        center_window_right(dialog, self.parent)
        
        # Title bar
        title_frame = tk.Frame(dialog, bg=UI_COLORS['primary'], height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_container = tk.Frame(title_frame, bg=UI_COLORS['primary'])
        title_container.pack(expand=True, fill=tk.BOTH, padx=25, pady=20)
        
        # Main title
        tk.Label(title_container, 
                text="🔀 L-shaped Boundary Routing Strategy Selection",
                font=('Microsoft YaHei', 18, 'bold'),
                fg='white', 
                bg=UI_COLORS['primary']).pack(anchor=tk.W)
        
        # Subtitle
        tk.Label(title_container,
                text=f"Center-{self.ck} Boundary  ↔  Out-{self.ok} Boundary",
                font=('Microsoft YaHei', 14),
                fg='#E8F4FD',
                bg=UI_COLORS['primary']).pack(anchor=tk.W, pady=(5, 0))
        
        # Description area
        desc_frame = tk.Frame(dialog, bg=UI_COLORS['bg_panel'])
        desc_frame.pack(fill=tk.X, padx=25, pady=20)
        
        desc_box = tk.Frame(desc_frame, bg=UI_COLORS['primary_light'], 
                           relief=tk.FLAT, bd=1)
        desc_box.pack(fill=tk.X)
        
        # Boundary information
        info_container = tk.Frame(desc_box, bg=UI_COLORS['primary_light'])
        info_container.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        tk.Label(info_container, 
                text=f"Vertical boundary: {self.vertical_boundary}",
                font=('Microsoft YaHei', 13, 'bold'),
                fg=UI_COLORS['primary'],
                bg=UI_COLORS['primary_light']).pack(side=tk.LEFT, padx=(0, 30))
        
        tk.Label(info_container,
                text=f"Horizontal boundary: {self.horizontal_boundary}",
                font=('Microsoft YaHei', 13, 'bold'),
                fg=UI_COLORS['primary'],
                bg=UI_COLORS['primary_light']).pack(side=tk.LEFT)
        
        # 🔴 Correction: Description text - separate Label parameters and pack parameters
        desc_label = tk.Label(desc_box,
                text="Please select point pair mapping and routing order strategy:",
                font=('Microsoft YaHei', 13, 'bold'),
                wraplength=700,
                justify=tk.LEFT,
                fg=UI_COLORS['text_primary'],
                bg=UI_COLORS['primary_light'],
                padx=20,   # Label padding
                pady=10)   # Label padding
        desc_label.pack(anchor=tk.W, pady=(0, 15))  # pack margin
        
        # Strategy button area
        btn_frame = tk.Frame(dialog, bg=UI_COLORS['bg_panel'])
        btn_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(10, 25))

        btn_container = tk.Frame(btn_frame, bg=UI_COLORS['bg_panel'])
        btn_container.pack(fill=tk.BOTH, expand=True)

        btn_container.grid_columnconfigure(0, weight=1, uniform='col')
        btn_container.grid_columnconfigure(1, weight=1, uniform='col')
        btn_container.grid_rowconfigure(0, weight=1, uniform='row')
        btn_container.grid_rowconfigure(1, weight=1, uniform='row')
        btn_container.grid_rowconfigure(2, weight=1, uniform='row')

        # Strategy list
        strategies = [
            ("1. Vertical boundary bottom ↔ Horizontal boundary left\nThen route in reverse direction (vertical ↑, horizontal →)",
             'bottom_to_top', 'left_to_right'),
            ("2. Vertical boundary bottom ↔ Horizontal boundary right\nThen route in reverse direction (vertical ↑, horizontal ←)",
             'bottom_to_top', 'right_to_left'),
            ("3. Vertical boundary top ↔ Horizontal boundary left\nThen route in reverse direction (vertical ↓, horizontal →)",
             'top_to_bottom', 'left_to_right'),
            ("4. Vertical boundary top ↔ Horizontal boundary right\nThen route in reverse direction (vertical ↓, horizontal ←)",
             'top_to_bottom', 'right_to_left'),
        ]

        for idx, (text, v_order, h_order) in enumerate(strategies):
            def make_callback(vo, ho):
                def callback():
                    self.result = (vo, ho)
                    dialog.destroy()
                return callback

            row = idx // 2
            col = idx % 2

            btn_wrapper = tk.Frame(btn_container, bg=UI_COLORS['bg_panel'])
            btn_wrapper.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')

            btn = tk.Button(btn_wrapper, text=text,
                        command=make_callback(v_order, h_order),
                        font=('Microsoft YaHei', 13, 'bold'),
                        bg=UI_COLORS['secondary'],
                        fg='white',
                        activebackground='#689F38',
                        activeforeground='white',
                        relief=tk.FLAT,
                        cursor='hand2',
                        wraplength=380,
                        justify=tk.LEFT,
                        padx=20,
                        pady=20,
                        bd=0,
                        highlightthickness=0)
            btn.pack(fill=tk.BOTH, expand=True)

            def on_enter(e, b=btn):
                b.config(bg='#689F38')

            def on_leave(e, b=btn):
                b.config(bg=UI_COLORS['secondary'])

            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)

        # Auto strategy button
        auto_wrapper = tk.Frame(btn_container, bg=UI_COLORS['bg_panel'])
        auto_wrapper.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

        auto_btn = tk.Button(auto_wrapper, text="🤖 Auto select optimal strategy\nProgram will automatically test all strategies and select the one with highest success rate",
                    command=lambda: (setattr(self, 'result', 'auto'), dialog.destroy()),
                    font=('Microsoft YaHei', 14, 'bold'),
                    bg=UI_COLORS['primary'],
                    fg='white',
                    activebackground=UI_COLORS['primary_dark'],
                    activeforeground='white',
                    relief=tk.FLAT,
                    cursor='hand2',
                    wraplength=750,
                    justify=tk.CENTER,
                    padx=20,
                    pady=20,
                    bd=0,
                    highlightthickness=0)
        auto_btn.pack(fill=tk.BOTH, expand=True)

        def on_auto_enter(e):
            auto_btn.config(bg=UI_COLORS['primary_dark'])

        def on_auto_leave(e):
            auto_btn.config(bg=UI_COLORS['primary'])

        auto_btn.bind('<Enter>', on_auto_enter)
        auto_btn.bind('<Leave>', on_auto_leave)
        
        self.parent.wait_window(dialog)
        return self.result


class SnapshotListDialog:
    """Snapshot list dialog - Optimized version"""
    
    def __init__(self, parent, snapshots, current_index):
        self.parent = parent
        self.snapshots = snapshots
        self.current_index = current_index
    
    def show(self):
        """Show dialog"""
        window = tk.Toplevel(self.parent)
        window.title("Snapshot List")
        window.geometry("850x600")
        window.configure(bg=UI_COLORS['bg_panel'])
        window.transient(self.parent)
        
        center_window_right(window, self.parent)
        
        # 🔴 Optimization: Title bar
        title_frame = tk.Frame(window, bg=UI_COLORS['primary'], height=70)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_container = tk.Frame(title_frame, bg=UI_COLORS['primary'])
        title_container.pack(expand=True, fill=tk.BOTH, padx=25, pady=15)
        
        tk.Label(title_container, text="💾 Routing Snapshot List",
                font=('Microsoft YaHei', 18, 'bold'),
                fg='white', bg=UI_COLORS['primary']).pack(side=tk.LEFT)
        
        tk.Label(title_container, text=f"Total: {len(self.snapshots)} snapshots",
                font=('Microsoft YaHei', 13),
                fg='#E8F4FD', bg=UI_COLORS['primary']).pack(side=tk.RIGHT)
        
        # Current snapshot indicator
        if self.current_index >= 0:
            info_frame = tk.Frame(window, bg=UI_COLORS['primary_light'])
            info_frame.pack(fill=tk.X, padx=25, pady=15)
            
            tk.Label(info_frame, 
                    text=f"✓ Currently using: Snapshot #{self.current_index + 1}",
                    font=('Microsoft YaHei', 13, 'bold'),
                    foreground=UI_COLORS['primary'],
                    bg=UI_COLORS['primary_light'],
                    padx=20, pady=12).pack(fill=tk.X)
        
        # List
        list_frame = tk.Frame(window, bg=UI_COLORS['bg_panel'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 20))
        
        # 🔴 Optimization: Increased list font size
        listbox = tk.Listbox(list_frame, 
                            font=('Consolas', 12),  # Changed from 9 to 12
                            height=15,
                            bg='white',
                            fg=UI_COLORS['text_primary'],
                            selectbackground=UI_COLORS['primary_light'],
                            selectforeground=UI_COLORS['text_primary'],
                            relief=tk.FLAT,
                            bd=1,
                            highlightthickness=1,
                            highlightcolor=UI_COLORS['border'],
                            highlightbackground=UI_COLORS['border'])
        listbox.pack(fill=tk.BOTH, expand=True)
        
        for i, snap in enumerate(self.snapshots):
            prefix = "➤ " if i == self.current_index else "  "
            item = (f"{prefix}[{i+1}] Region {snap['task_count']} - "
                   f"{snap['timestamp']} - Total {len(snap['all_finished_paths'])} paths")
            listbox.insert(tk.END, item)
            
            if i == self.current_index:
                listbox.itemconfig(i, {'bg': UI_COLORS['primary_light']})
        
        # Buttons
        btn_frame = tk.Frame(window, bg=UI_COLORS['bg_panel'])
        btn_frame.pack(fill=tk.X, padx=25, pady=(0, 20))
        
        # 🔴 Optimization: Increased button font size
        tk.Button(btn_frame, text="✗ Close",
                 command=window.destroy,
                 font=('Microsoft YaHei', 14, 'bold'),  # Changed from 10 to 14
                 bg=UI_COLORS['secondary'],
                 fg='white',
                 activebackground='#689F38',
                 relief=tk.FLAT,
                 cursor='hand2',
                 padx=30, pady=12).pack()


def show_help_dialog(parent):
    """Show help dialog - Optimized version"""
    
    # Create dialog
    dialog = tk.Toplevel(parent)
    dialog.title("Usage Instructions")
    dialog.geometry("900x700")
    dialog.configure(bg=UI_COLORS['bg_panel'])
    dialog.transient(parent)
    dialog.grab_set()
    
    center_window_right(dialog, parent)
    
    # 🔴 Optimization: Title bar
    title_frame = tk.Frame(dialog, bg=UI_COLORS['primary'], height=70)
    title_frame.pack(fill=tk.X)
    title_frame.pack_propagate(False)
    
    tk.Label(title_frame, text="📘 Photonic Quantum Chip Routing System - Usage Instructions",
            font=('Microsoft YaHei', 18, 'bold'),
            wraplength=1000,
            justify=tk.CENTER,
            fg='white', bg=UI_COLORS['primary']).pack(expand=True, pady=15)
    
    # Content area
    content_frame = tk.Frame(dialog, bg=UI_COLORS['bg_panel'])
    content_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
    
    # Use ScrolledText to display content
    from tkinter import scrolledtext
    
    text_widget = scrolledtext.ScrolledText(
        content_frame,
        wrap=tk.WORD,
        font=('Microsoft YaHei', 12),  # 🔴 Increased font size
        bg='white',
        fg=UI_COLORS['text_primary'],
        relief=tk.FLAT,
        bd=1,
        highlightthickness=1,
        highlightcolor=UI_COLORS['border'],
        highlightbackground=UI_COLORS['border'],
        padx=20,
        pady=15
    )
    text_widget.pack(fill=tk.BOTH, expand=True)
    
    help_text = """📘 Photonic Quantum Chip Routing System - Usage Instructions

【Core Features】
✓ DiagonalBitmap O(1) diagonal collision detection
✓ One-way A* search algorithm
✓ Numba JIT acceleration support (optional)
✓ Snapshot switching functionality - supports repeated switching
✓ Light blue and white professional UI theme

【Operation Flow】
1. Import CSV data file (or load existing .pkl data)
2. Click "Start New Region"
3. Drag to select routing region on canvas
4. Complete the three stages of routing sequentially

【Three-Stage Routing】
• Stage 1: Out point internal routing
• Stage 2: Center point internal routing
• Stage 3: External connection (intelligent boundary matching)

【Boundary Handling】
• Parallel boundaries: 4 mapping strategies
• L-shaped boundaries: 4 mapping strategies
• Automatic boundary matching and grouping

【Snapshot Management】
• Automatic snapshot creation after each region
• Support for viewing snapshot list
• Support for switching to any snapshot (repeatable switching)
• Continue working or save after switching

【Keyboard Shortcuts】
Ctrl+O - Import CSV data
Ctrl+L - Load routing data
Ctrl+S - Save routing data
Ctrl+N - Start new region
F5 - Refresh canvas
"""
    
    text_widget.insert(tk.END, help_text)
    text_widget.config(state='disabled')
    
    # Close button
    tk.Button(dialog, text="✓ I understand",
             command=dialog.destroy,
             font=('Microsoft YaHei', 14, 'bold'),
             bg=UI_COLORS['primary'],
             fg='white',
             activebackground=UI_COLORS['primary_dark'],
             relief=tk.FLAT,
             cursor='hand2',
             padx=30, pady=12).pack(pady=(0, 20))


def show_about_dialog(parent):
    """Show about dialog - Optimized version"""
    
    dialog = tk.Toplevel(parent)
    dialog.title("About")
    dialog.geometry("600x500")
    dialog.configure(bg=UI_COLORS['bg_panel'])
    dialog.transient(parent)
    dialog.grab_set()
    
    center_window_right(dialog, parent)
    
    # Title area
    title_frame = tk.Frame(dialog, bg=UI_COLORS['primary'], height=100)
    title_frame.pack(fill=tk.X)
    title_frame.pack_propagate(False)
    
    title_container = tk.Frame(title_frame, bg=UI_COLORS['primary'])
    title_container.pack(expand=True)
    
    tk.Label(title_container, text="Photonic Quantum Chip Routing System",
            font=('Microsoft YaHei', 22, 'bold'),
            fg='white', bg=UI_COLORS['primary']).pack()
    
    tk.Label(title_container, text="v0.0.0",
            font=('Microsoft YaHei', 14),
            fg='#E8F4FD', bg=UI_COLORS['primary']).pack(pady=(5, 0))
    
    # Content area
    content_frame = tk.Frame(dialog, bg=UI_COLORS['bg_panel'])
    content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
    
    about_text = """🚀 Core Technology

• DiagonalBitmap diagonal collision detection
• One-way A* search algorithm
• Numba JIT acceleration

✨ Some Features

• Light blue and white professional UI theme
• Optimized control panel layout
• Snapshot repeated switching support
• Intelligent boundary matching
• Clear grid line display
• Adaptive font and scrolling
• Optimized dialog visual effects

"""
    
    tk.Label(content_frame, text=about_text,
            font=('Microsoft YaHei', 13),
            fg=UI_COLORS['text_primary'],
            bg=UI_COLORS['bg_panel'],
            justify=tk.LEFT).pack()
    
    # Close button
    tk.Button(dialog, text="✓ Close",
             command=dialog.destroy,
             font=('Microsoft YaHei', 14, 'bold'),
             bg=UI_COLORS['primary'],
             fg='white',
             activebackground=UI_COLORS['primary_dark'],
             relief=tk.FLAT,
             cursor='hand2',
             padx=30, pady=12).pack(pady=(0, 25))


class RoutingConfigDialog:
    """Routing parameter configuration dialog"""

    def __init__(self, parent):
        self.parent = parent
        self.result = None

    def show(self):
        """Show dialog"""
        from ..config.constants import DEFAULT_GRID_SIZE

        dialog = tk.Toplevel(self.parent)
        dialog.title("Routing Parameter Configuration")
        dialog.geometry("650x550")
        dialog.configure(bg=UI_COLORS['bg_panel'])
        dialog.transient(self.parent)
        dialog.grab_set()

        center_window_right(dialog, self.parent)

        # Title area
        title_frame = tk.Frame(dialog, bg=UI_COLORS['primary'], height=70)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text="⚙️ Routing Parameter Configuration",
                font=('Microsoft YaHei', 18, 'bold'),
                fg='white', bg=UI_COLORS['primary']).pack(expand=True)

        # Content area
        content_frame = tk.Frame(dialog, bg=UI_COLORS['bg_panel'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)

        # Grid size
        grid_frame = tk.Frame(content_frame, bg=UI_COLORS['bg_panel'])
        grid_frame.pack(fill=tk.X, pady=10)

        tk.Label(grid_frame, text="Grid Size:",
                font=('Microsoft YaHei', 13, 'bold'),
                fg=UI_COLORS['text_primary'],
                bg=UI_COLORS['bg_panel']).pack(side=tk.LEFT)

        self.grid_size_var = tk.StringVar(value=str(DEFAULT_GRID_SIZE))
        grid_entry = tk.Entry(grid_frame, textvariable=self.grid_size_var,
                             font=('Microsoft YaHei', 14), width=10,
                             justify=tk.CENTER)
        grid_entry.pack(side=tk.RIGHT)

        tk.Label(content_frame, text="Control grid cell size, affects routing accuracy and performance",
                font=('Microsoft YaHei', 10),
                wraplength=450,
                justify=tk.LEFT,
                fg=UI_COLORS['text_light'],
                bg=UI_COLORS['bg_panel']).pack(anchor=tk.W)

        # Button area
        btn_frame = tk.Frame(dialog, bg=UI_COLORS['bg_panel'])
        btn_frame.pack(fill=tk.X, padx=40, pady=(0, 25))

        btn_container = tk.Frame(btn_frame, bg=UI_COLORS['bg_panel'])
        btn_container.pack(anchor=tk.CENTER)

        def on_confirm():
            try:
                grid_size = int(self.grid_size_var.get())
                if grid_size < 1:
                    raise ValueError("Parameter must be greater than 0")
                self.result = {'grid_size': grid_size}
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Input Error", f"Please enter a valid positive integer\n{str(e)}", parent=dialog)

        def on_default():
            self.grid_size_var.set(str(DEFAULT_GRID_SIZE))

        tk.Button(btn_container, text="✓ Confirm",
                 command=on_confirm,
                 font=('Microsoft YaHei', 13, 'bold'),
                 bg=UI_COLORS['primary'],
                 fg='white',
                 activebackground=UI_COLORS['primary_dark'],
                 relief=tk.FLAT,
                 cursor='hand2',
                 padx=25, pady=10).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_container, text="Restore Default",
                 command=on_default,
                 font=('Microsoft YaHei', 13, 'bold'),
                 bg=UI_COLORS['secondary'],
                 fg='white',
                 activebackground=UI_COLORS['secondary'],
                 relief=tk.FLAT,
                 cursor='hand2',
                 padx=25, pady=10).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_container, text="✗ Cancel",
                 command=dialog.destroy,
                 font=('Microsoft YaHei', 13, 'bold'),
                 bg=UI_COLORS['text_light'],
                 fg='white',
                 activebackground=UI_COLORS['text_secondary'],
                 relief=tk.FLAT,
                 cursor='hand2',
                 padx=25, pady=10).pack(side=tk.LEFT, padx=5)

        grid_entry.focus()
        grid_entry.bind('<Return>', lambda e: on_confirm())

        self.parent.wait_window(dialog)
        return self.result
