"""
control_panel.py - Control Panel Component
Control panel component with scrollable layout and adaptive font size functionality.
Contains all control buttons, input fields, and dynamic UI elements for routing stages.
"""

import tkinter as tk
from tkinter import ttk
from ..config.ui_config import UI_COLORS, CANVAS_SIZES


class ControlPanel:
    """Control Panel Class - Adaptive Enhanced Version"""
    
    def __init__(self, parent, callbacks):
        self.parent = parent
        self.callbacks = callbacks
        self.widgets = {}
        
        # Adaptive configuration
        self.auto_font_enabled = True  # Enable font adaptation
        self.min_font_size = 10        # Minimum font size
        self.max_font_size = 14        # Maximum font size
        
        self.create_panel()
    
    def create_panel(self):
        """Create control panel"""
        # Top title area (fixed height)
        title_frame = tk.Frame(self.parent, bg=UI_COLORS['primary'], height=60)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="Control Center", 
                            font=('Microsoft YaHei', 20, 'bold'),
                            fg='white', bg=UI_COLORS['primary'],
                            anchor='w')
        title_label.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Scrollable content area
        canvas_frame = tk.Frame(self.parent, bg=UI_COLORS['bg_panel'])
        canvas_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        # Create Canvas and scrollbar
        self.canvas = tk.Canvas(canvas_frame, bg=UI_COLORS['bg_panel'], 
                            highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", 
                                command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg=UI_COLORS['bg_panel'])
        
        # Create window
        self.canvas_window = self.canvas.create_window(
            (0, 0), 
            window=self.scrollable_frame, 
            anchor="nw"
        )
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Layout
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind configuration events
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self._on_frame_configure()
        )
        
        self.canvas.bind(
            "<Configure>",
            lambda e: self._on_canvas_configure()
        )
        
        # 🔴 Modified: Use intelligent mouse wheel binding
        # Only enable wheel when mouse is inside control panel area
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        
        # Create various cards (in scrollable_frame, in order)
        self._create_data_card(self.scrollable_frame)
        self._create_flow_card(self.scrollable_frame)        # Routing flow
        # 🔴 Boundary assignment UI has been moved to routing flow card (see _create_dynamic_buttons method)
        # self._create_boundary_card(self.scrollable_frame)
        self._create_auto_group_card(self.scrollable_frame)   # Auto grouping
        # 🔴 Manual connection UI has been moved to routing flow card (see _create_dynamic_buttons method)
        # self._create_manual_card(self.scrollable_frame)
        self._create_snapshot_card(self.scrollable_frame)     # Snapshot management

    def _on_enter(self, event):
        """Bind mouse wheel event when mouse enters control panel area"""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_leave(self, event):
        """Unbind mouse wheel event when mouse leaves control panel area"""
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        """Mouse wheel event"""
        try:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except:
            pass

    
    def _on_frame_configure(self):
        """Update scroll region when scrollable_frame size changes"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self):
        """Adjust scrollable_frame width when canvas size changes"""
        canvas_width = self.canvas.winfo_width()
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def _on_mousewheel(self, event):
        """Mouse wheel event"""
        try:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except:
            pass
    
    def _create_data_card(self, parent):
        """Create data information card"""
        data_card = ttk.LabelFrame(parent, text="📊 Data Overview", 
                                   style='Card.TLabelframe', padding=15)
        data_card.pack(fill=tk.BOTH, expand=False, padx=12, pady=(12, 8))
        
        info_frame = tk.Frame(data_card, bg=UI_COLORS['primary_light'], 
                             relief=tk.FLAT, bd=1)
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        self.widgets['data_info'] = tk.Text(
            info_frame, height=8, width=38,
            state='disabled', font=('Microsoft YaHei', 11),
            bg=UI_COLORS['primary_light'],
            fg=UI_COLORS['text_primary'],
            relief='flat', borderwidth=0,
            wrap=tk.WORD, padx=8, pady=8
        )
        self.widgets['data_info'].pack(fill=tk.BOTH, expand=True)
    
    def _create_flow_card(self, parent):
        """Create routing flow card - Adaptive Enhanced Version"""
        flow_card = ttk.LabelFrame(parent, text="🔄 Routing Flow", 
                                   style='Card.TLabelframe', padding=15)
        flow_card.pack(fill=tk.BOTH, expand=False, padx=12, pady=8)
        
        # Current status display
        status_container = tk.Frame(flow_card, bg=UI_COLORS['bg_panel'])
        status_container.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(status_container, text="Current Status:", 
                font=('Microsoft YaHei', 15, 'bold'),
                fg=UI_COLORS['text_secondary'],
                bg=UI_COLORS['bg_panel'],
                anchor='w').pack(fill=tk.X, pady=(0, 4))
        
        self.widgets['stage_var'] = tk.StringVar(value="Not Started")
        stage_display = tk.Frame(status_container, bg=UI_COLORS['primary_light'],
                                relief=tk.FLAT, bd=1)
        stage_display.pack(fill=tk.X)
        
        # 🔴 Using adaptive font Label
        self.widgets['stage_label'] = tk.Label(
            stage_display, 
            textvariable=self.widgets['stage_var'],
            font=('Microsoft YaHei', 14, 'bold'),
            foreground=UI_COLORS['primary'],
            background=UI_COLORS['primary_light'],
            wraplength=290, 
            justify=tk.LEFT,
            anchor='w', 
            padx=10, 
            pady=8
        )
        self.widgets['stage_label'].pack(fill=tk.X)
        
        # 🔴 Bind variable trace for font adaptation
        self.widgets['stage_var'].trace_add('write', 
                                           lambda *args: self._adjust_stage_font())
        
        # Timer display
        self.widgets['timer_var'] = tk.StringVar(value="")
        timer_display = tk.Frame(flow_card, bg=UI_COLORS['bg_panel'])
        timer_display.pack(fill=tk.X, pady=(0, 10))
        
        self.widgets['timer_label'] = tk.Label(
            timer_display, 
            textvariable=self.widgets['timer_var'],
            font=('Microsoft YaHei', 15, 'bold'),
            foreground=UI_COLORS['secondary'],
            background=UI_COLORS['bg_panel'],
            wraplength=300,  # ← New: Auto-wrap width
            justify=tk.LEFT,  # ← New: Multi-line left alignment
            anchor='w'
        )
        self.widgets['timer_label'].pack(fill=tk.X)
        
        # Separator
        ttk.Separator(flow_card, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Main action button
        btn_style = {
            'font': ('Microsoft YaHei', 15, 'bold'),
            'bg': UI_COLORS['primary'],
            'fg': 'white',
            'activebackground': UI_COLORS['primary_dark'],
            'activeforeground': 'white',
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'padx': 20,
            'pady': 10
        }
        
        self.widgets['btn_start_region'] = tk.Button(
            flow_card, text="▶ Start New Region",
            command=self.callbacks['start_new_region'],
            **btn_style
        )
        self.widgets['btn_start_region'].pack(fill=tk.X, pady=(0, 8))
        
        # Separator
        ttk.Separator(flow_card, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Dynamic action area
        self.widgets['stage_action_frame'] = tk.Frame(flow_card, bg=UI_COLORS['bg_panel'])
        self.widgets['stage_action_frame'].pack(fill=tk.BOTH, expand=True)
        
        # Create dynamic buttons
        self._create_dynamic_buttons()
    
    def _adjust_stage_font(self):
        """Adaptive adjustment of stage label font size - Optimized Version"""
        if not self.auto_font_enabled:
            return
        
        try:
            label = self.widgets['stage_label']
            text = self.widgets['stage_var'].get()
            
            if not text:
                return
            
            # Get actual width of Label
            label.update_idletasks()
            available_width = label.winfo_width()
            
            if available_width <= 1:
                available_width = 290  # 🔴 Modified default width
            
            # Subtract padding
            available_width -= 20  # padx=10 * 2
            
            # 🔴 Optimized: More accurate width calculation
            for font_size in range(14, 9, -1):  # 🔴 Start from size 14, minimum 10
                temp_font = ('Microsoft YaHei', font_size, 'bold')
                
                # Calculate text width (more accurate estimation)
                estimated_width = 0
                lines = text.count('\n') + 1
                
                # Consider line breaks
                for line in text.split('\n'):
                    line_width = 0
                    for char in line:
                        if '\u4e00' <= char <= '\u9fff':  # Chinese character
                            line_width += font_size * 0.7  # Chinese is wider
                        else:  # English/numbers/symbols
                            line_width += font_size * 0.55
                    
                    estimated_width = max(estimated_width, line_width)
                
                if estimated_width <= available_width:
                    label.config(font=temp_font)
                    return
            
            # Minimum font size still doesn't fit, use minimum font size
            label.config(font=('Microsoft YaHei', 10, 'bold'))
            
        except Exception as e:
            pass
    
    def _create_dynamic_buttons(self):
        """Create dynamic buttons"""
        btn_style = {
            'font': ('Microsoft YaHei', 15, 'bold'),
            'bg': UI_COLORS['secondary'],
            'fg': 'white',
            'activebackground': '#689F38',
            'activeforeground': 'white',
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'padx': 15,
            'pady': 8
        }
        
        frame = self.widgets['stage_action_frame']
        
        self.widgets['btn_auto'] = tk.Button(
            frame, text="🤖 Auto Mode",
            command=self.callbacks['select_auto_mode'],
            **btn_style
        )
        
        self.widgets['btn_manual'] = tk.Button(
            frame, text="✋ Manual Mode",
            command=self.callbacks['select_manual_mode'],
            **btn_style
        )
        
        self.widgets['btn_next'] = tk.Button(
            frame, text="➡️ Next Stage",
            command=self.callbacks['next_stage'],
            **btn_style
        )
        
        self.widgets['btn_retry'] = tk.Button(
            frame, text="🔄 Retry/Back",
            command=self.callbacks['retry_stage'],
            **btn_style
        )
        
        confirm_btn_style = btn_style.copy()
        confirm_btn_style['bg'] = UI_COLORS['primary']
        confirm_btn_style['activebackground'] = UI_COLORS['primary_dark']
        
        self.widgets['btn_confirm'] = tk.Button(
            frame, text="✅ Confirm Region",
            command=self.callbacks['confirm_region'],
            **confirm_btn_style
        )
        
        # 🔴 Boundary assignment UI (placed within routing flow card)
        self.widgets['boundary_frame'] = tk.Frame(
            frame, bg=UI_COLORS['bg_panel']
        )
        
        self.widgets['boundary_label'] = tk.Label(
            self.widgets['boundary_frame'], text="",
            font=('Microsoft YaHei', 15),
            wraplength=290,
            justify=tk.LEFT,
            fg=UI_COLORS['text_primary'],
            bg=UI_COLORS['bg_panel']
        )
        self.widgets['boundary_label'].pack(anchor=tk.W, pady=(0, 10))
        
        # Boundary assignment buttons (not packed, dynamically controlled by main_window.py)
        self.widgets['btn_boundary_confirm'] = tk.Button(
            self.widgets['boundary_frame'],
            text="✓ Confirm Current Boundary",
            command=self.callbacks['confirm_boundary_selection'],
            **btn_style
        )
        
        self.widgets['btn_boundary_undo'] = tk.Button(
            self.widgets['boundary_frame'],
            text="↶ Undo Last Point",
            command=self.callbacks['undo_boundary_point'],
            **btn_style
        )
        
        # 🔴 Manual external connection UI (placed within routing flow card)
        self.widgets['manual_external_frame'] = tk.Frame(
            frame, bg=UI_COLORS['bg_panel']
        )
        
        # Manual connection title
        self.widgets['manual_group_label'] = tk.Label(
            self.widgets['manual_external_frame'], text="",
            font=('Microsoft YaHei', 15, 'bold'),
            fg=UI_COLORS['primary'],
            bg=UI_COLORS['bg_panel']
        )
        self.widgets['manual_group_label'].pack(anchor=tk.W, pady=(0, 10))
        
        # Center input
        center_input_frame = tk.Frame(
            self.widgets['manual_external_frame'], 
            bg=UI_COLORS['bg_panel']
        )
        center_input_frame.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(center_input_frame,
                text="Center backup point numbers (space-separated):",
                font=('Microsoft YaHei', 13),
                wraplength=290,
                justify=tk.LEFT,
                fg=UI_COLORS['text_secondary'],
                bg=UI_COLORS['bg_panel']).pack(anchor=tk.W, pady=(0, 4))
        
        self.widgets['entry_center_ids'] = tk.Entry(
            center_input_frame, width=38,
            font=('Consolas', 9),
            bg='white',
            fg=UI_COLORS['text_primary'],
            relief=tk.SOLID, bd=1
        )
        self.widgets['entry_center_ids'].pack(fill=tk.X)
        
        # Out input
        out_input_frame = tk.Frame(
            self.widgets['manual_external_frame'], 
            bg=UI_COLORS['bg_panel']
        )
        out_input_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(out_input_frame,
                text="Out backup point numbers (space-separated):",
                font=('Microsoft YaHei', 13, 'bold'),
                wraplength=290,
                justify=tk.LEFT,
                fg=UI_COLORS['text_secondary'],
                bg=UI_COLORS['bg_panel']).pack(anchor=tk.W, pady=(0, 4))
        
        self.widgets['entry_out_ids'] = tk.Entry(
            out_input_frame, width=38,
            font=('Consolas', 9),
            bg='white',
            fg=UI_COLORS['text_primary'],
            relief=tk.SOLID, bd=1
        )
        self.widgets['entry_out_ids'].pack(fill=tk.X)
        
        # Button group
        manual_btn_frame = tk.Frame(
            self.widgets['manual_external_frame'], 
            bg=UI_COLORS['bg_panel']
        )
        manual_btn_frame.pack(fill=tk.X)
        
        self.widgets['btn_add_group'] = tk.Button(
            manual_btn_frame, text="✓ Add and Route",
            command=self.callbacks['add_manual_group'],
            **btn_style
        )
        self.widgets['btn_add_group'].pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        
        self.widgets['btn_skip_group'] = tk.Button(
            manual_btn_frame, text="⏭️ Skip",
            command=self.callbacks['skip_manual_group'],
            **btn_style
        )
        self.widgets['btn_skip_group'].pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(4, 0))
    
    def _create_boundary_card(self, parent):
        """Create boundary assignment card"""
        self.widgets['boundary_frame'] = ttk.LabelFrame(
            parent, text="📍 Boundary Assignment",
            style='Card.TLabelframe', padding=15
        )
        
        self.widgets['boundary_label'] = tk.Label(
            self.widgets['boundary_frame'], text="",
            font=('Microsoft YaHei', 15),
            wraplength=290,
            justify=tk.LEFT,
            fg=UI_COLORS['text_primary'],
            bg=UI_COLORS['bg_panel']
        )
        self.widgets['boundary_label'].pack(anchor=tk.W, pady=(0, 10))
        
        btn_style = {
            'font': ('Microsoft YaHei', 15, 'bold'),
            'bg': UI_COLORS['secondary'],
            'fg': 'white',
            'activebackground': '#689F38',
            'activeforeground': 'white',
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'padx': 15,
            'pady': 8
        }
        
        self.widgets['btn_boundary_confirm'] = tk.Button(
            self.widgets['boundary_frame'],
            text="✓ Confirm Current Boundary",
            command=self.callbacks['confirm_boundary_selection'],
            **btn_style
        )
        
        self.widgets['btn_boundary_undo'] = tk.Button(
            self.widgets['boundary_frame'],
            text="↶ Undo Last Point",
            command=self.callbacks['undo_boundary_point'],
            **btn_style
        )
    
    def _create_auto_group_card(self, parent):
        """Create auto mode grouping card"""
        self.widgets['auto_group_frame'] = ttk.LabelFrame(
            parent, text="🤖 Auto Group Routing",
            style='Card.TLabelframe', padding=15
        )
        
        self.widgets['auto_group_label'] = tk.Label(
            self.widgets['auto_group_frame'], text="",
            font=('Microsoft YaHei', 15),
            wraplength=290,
            justify=tk.LEFT,
            fg=UI_COLORS['text_primary'],
            bg=UI_COLORS['bg_panel']
        )
        self.widgets['auto_group_label'].pack(anchor=tk.W, pady=(0, 10))
        
        btn_style = {
            'font': ('Microsoft YaHei', 15, 'bold'),
            'bg': UI_COLORS['secondary'],
            'fg': 'white',
            'activebackground': '#689F38',
            'activeforeground': 'white',
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'padx': 15,
            'pady': 8
        }
        
        self.widgets['btn_auto_continue'] = tk.Button(
            self.widgets['auto_group_frame'],
            text="➡️ Continue to Next Group",
            command=self.callbacks['continue_auto_next_group'],
            **btn_style
        )
        
        self.widgets['btn_auto_skip'] = tk.Button(
            self.widgets['auto_group_frame'],
            text="⏭️ Skip Remaining Groups",
            command=self.callbacks['skip_auto_remaining_groups'],
            **btn_style
        )
    
    def _create_manual_card(self, parent):
        """Create manual connection card"""
        self.widgets['manual_external_frame'] = ttk.LabelFrame(
            parent, text="✋ Manual External Connection",  # 🔴 Confirm parent is scrollable_frame
            style='Card.TLabelframe', padding=15
        )
        
        self.widgets['manual_group_label'] = tk.Label(
            self.widgets['manual_external_frame'], text="",
            font=('Microsoft YaHei', 15, 'bold'),
            fg=UI_COLORS['primary'],
            bg=UI_COLORS['bg_panel']
        )
        self.widgets['manual_group_label'].pack(anchor=tk.W, pady=(0, 10))
        
        # Center input
        center_input_frame = tk.Frame(
            self.widgets['manual_external_frame'], 
            bg=UI_COLORS['bg_panel']
        )
        center_input_frame.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(center_input_frame,
                text="Center backup point numbers (space-separated):",
                font=('Microsoft YaHei', 13),
                wraplength=290,
                justify=tk.LEFT,
                fg=UI_COLORS['text_secondary'],
                bg=UI_COLORS['bg_panel']).pack(anchor=tk.W, pady=(0, 4))
        
        self.widgets['entry_center_ids'] = tk.Entry(
            center_input_frame, width=38,
            font=('Consolas', 9),
            bg='white',
            fg=UI_COLORS['text_primary'],
            relief=tk.SOLID, bd=1
        )
        self.widgets['entry_center_ids'].pack(fill=tk.X)
        
        # Out input
        out_input_frame = tk.Frame(
            self.widgets['manual_external_frame'], 
            bg=UI_COLORS['bg_panel']
        )
        out_input_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(out_input_frame,
                text="Out backup point numbers (space-separated):",
                font=('Microsoft YaHei', 13, 'bold'),
                wraplength=290,
                justify=tk.LEFT,
                fg=UI_COLORS['text_secondary'],
                bg=UI_COLORS['bg_panel']).pack(anchor=tk.W, pady=(0, 4))
        
        self.widgets['entry_out_ids'] = tk.Entry(
            out_input_frame, width=38,
            font=('Consolas', 9),
            bg='white',
            fg=UI_COLORS['text_primary'],
            relief=tk.SOLID, bd=1
        )
        self.widgets['entry_out_ids'].pack(fill=tk.X)
        
        # Button group
        btn_frame = tk.Frame(
            self.widgets['manual_external_frame'], 
            bg=UI_COLORS['bg_panel']
        )
        btn_frame.pack(fill=tk.X)
        
        btn_style = {
            'font': ('Microsoft YaHei', 15, 'bold'),
            'bg': UI_COLORS['secondary'],
            'fg': 'white',
            'activebackground': '#689F38',
            'activeforeground': 'white',
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'padx': 15,
            'pady': 8
        }
        
        self.widgets['btn_add_group'] = tk.Button(
            btn_frame, text="✓ Add and Route",
            command=self.callbacks['add_manual_group'],
            **btn_style
        )
        self.widgets['btn_add_group'].pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        
        self.widgets['btn_skip_group'] = tk.Button(
            btn_frame, text="⏭️ Skip",
            command=self.callbacks['skip_manual_group'],
            **btn_style
        )
        self.widgets['btn_skip_group'].pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(4, 0))
    
    def _create_snapshot_card(self, parent):
        """Create snapshot management card"""
        snapshot_card = ttk.LabelFrame(
            parent, text="💾 Snapshot Management",
            style='Card.TLabelframe', padding=15
        )
        snapshot_card.pack(fill=tk.BOTH, expand=False, padx=12, pady=8)
        
        btn_style = {
            'font': ('Microsoft YaHei', 15, 'bold'),
            'bg': UI_COLORS['secondary'],
            'fg': 'white',
            'activebackground': '#689F38',
            'activeforeground': 'white',
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'padx': 15,
            'pady': 8
        }
        
        tk.Button(snapshot_card, text="📋 View Snapshot List",
                 command=self.callbacks['view_snapshots'],
                 **btn_style).pack(fill=tk.X, pady=(0, 6))
        
        tk.Button(snapshot_card, text="🔄 Switch to Snapshot",
                 command=self.callbacks['switch_to_snapshot'],
                 **btn_style).pack(fill=tk.X)
    
    def get_widget(self, name):
        """Get the specified widget"""
        return self.widgets.get(name)
    
    def hide_all_dynamic_frames(self):
        """Hide all dynamic widget frames"""
        # Hide all child widgets within stage_action_frame (including boundary_frame and manual_external_frame)
        for widget in self.widgets['stage_action_frame'].winfo_children():
            widget.pack_forget()
        # auto_group_frame is still an independent card, needs to be hidden separately
        self.widgets['auto_group_frame'].pack_forget()