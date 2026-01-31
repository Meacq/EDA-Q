"""
log_panel.py - Log panel component
Panel component for displaying system logs, with different colors for different severity levels.
"""

import tkinter as tk
from tkinter import scrolledtext
from ..config.ui_config import UI_COLORS


class LogPanel:
    """Log panel class - responsible for log display and management"""
    
    def __init__(self, parent, callbacks):
        self.parent = parent
        self.callbacks = callbacks
        self.log_text = None
        
        self.create_panel()
    
    def create_panel(self):
        """Create log panel"""
        # Top title
        title_frame = tk.Frame(self.parent, bg=UI_COLORS['primary'], height=70)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="System Log", 
                              font=('Arial', 20, 'bold'),
                              fg='white', bg=UI_COLORS['primary'],
                              anchor='w')
        title_label.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Log text area
        log_frame = tk.Frame(self.parent, bg=UI_COLORS['bg_panel'])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(12, 8))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            state='disabled',
            font=('Arial', 12),
            bg='#F8F9FA',
            fg=UI_COLORS['text_primary'],
            insertbackground=UI_COLORS['primary'],
            relief='flat',
            borderwidth=0,
            padx=8,
            pady=8
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Configure log level colors
        self.log_text.tag_config('INFO', foreground=UI_COLORS['text_primary'])
        self.log_text.tag_config('SUCCESS', foreground=UI_COLORS['secondary'],
                                font=('Arial', 12, 'bold'))
        self.log_text.tag_config('WARNING', foreground=UI_COLORS['warning'])
        self.log_text.tag_config('ERROR', foreground=UI_COLORS['error'],
                                font=('Arial', 12, 'bold'))
        self.log_text.tag_config('TIMING', foreground=UI_COLORS['primary'])
        self.log_text.tag_config('PROGRESS', foreground='#00897B')
        
        # Bottom control buttons
        btn_frame = tk.Frame(self.parent, bg=UI_COLORS['bg_panel'])
        btn_frame.pack(fill=tk.X, padx=12, pady=(0, 12))
        
        tk.Button(btn_frame, text="🗑️ Clear Log",
                command=self.callbacks['clear_log'],
                font=('Arial', 15, 'bold'),
                bg=UI_COLORS['secondary'],
                fg='white',
                activebackground='#689F38',
                activeforeground='white',
                relief=tk.FLAT,
                cursor='hand2',
                padx=15, 
                pady=8).pack(fill=tk.X)
    
    def add_log(self, message, level='INFO'):
        """Add log message"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message, level)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def clear(self):
        """Clear all logs"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
