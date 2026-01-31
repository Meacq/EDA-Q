"""
styles.py - UI style settings
User interface style configuration for ttk components with light blue theme.
"""

from tkinter import ttk
from ..config.ui_config import UI_COLORS


def setup_styles():
    """Configure professional UI styles - light blue and white theme"""
    style = ttk.Style()
    style.theme_use('clam')

    # Title style
    style.configure('Title.TLabel',
                   font=('Microsoft YaHei', 17, 'bold'),
                   foreground=UI_COLORS['primary_dark'],
                   background=UI_COLORS['bg_panel'],
                   padding=8)

    # Subtitle style
    style.configure('Subtitle.TLabel',
                   font=('Microsoft YaHei', 15),
                   foreground=UI_COLORS['text_secondary'],
                   background=UI_COLORS['bg_panel'],
                   padding=4)

    # Small title style
    style.configure('SmallTitle.TLabel',
                   font=('Microsoft YaHei', 15, 'bold'),
                   foreground=UI_COLORS['text_primary'],
                   background=UI_COLORS['bg_panel'],
                   padding=3)

    # Status style
    style.configure('Status.TLabel',
                   font=('Microsoft YaHei', 15, 'bold'),
                   foreground=UI_COLORS['text_light'],
                   background=UI_COLORS['bg_main'],
                   padding=4)

    # Button styles
    style.configure('Primary.TButton',
                   font=('Microsoft YaHei', 15, 'bold'),
                   padding=10,
                   background=UI_COLORS['primary'],
                   foreground='white')
    style.map('Primary.TButton',
             background=[('active', UI_COLORS['primary_dark'])],
             foreground=[('active', 'white')])

    style.configure('Success.TButton',
                   font=('Microsoft YaHei', 15, 'bold'),
                   padding=8,
                   background=UI_COLORS['secondary'])
    style.map('Success.TButton',
             background=[('active', '#689F38')])

    style.configure('Stage.TButton',
                   font=('Microsoft YaHei', 15, 'bold'),
                   padding=12)

    # Frame styles
    style.configure('Panel.TFrame',
                   background=UI_COLORS['bg_panel'],
                   relief='flat')

    style.configure('Main.TFrame',
                   background=UI_COLORS['bg_main'],
                   relief='flat')

    # LabelFrame styles
    style.configure('Card.TLabelframe',
                   background=UI_COLORS['bg_panel'],
                   relief='solid',
                   borderwidth=1,
                   bordercolor=UI_COLORS['border'])

    style.configure('Card.TLabelframe.Label',
                   font=('Microsoft YaHei', 15, 'bold'),
                   foreground=UI_COLORS['primary'],
                   background=UI_COLORS['bg_panel'],
                   padding=4)

    # Separator style
    style.configure('TSeparator',
                   background=UI_COLORS['border'])

    # Sash style
    style.configure('Sash', background=UI_COLORS['primary'], relief='raised')

    # Checkbutton style - fix X display issue
    # Use indicatoron=1 to ensure standard checkbox display instead of button style
    style.configure('TCheckbutton',
                   background=UI_COLORS['bg_panel'],
                   foreground=UI_COLORS['text_primary'],
                   font=('Microsoft YaHei', 10),
                   indicatorcolor='white',
                   indicatorrelief='flat',
                   borderwidth=1)
    style.map('TCheckbutton',
             background=[('active', UI_COLORS['bg_panel']), ('selected', UI_COLORS['bg_panel'])],
             foreground=[('active', UI_COLORS['primary']), ('selected', UI_COLORS['primary'])],
             indicatorcolor=[('selected', UI_COLORS['primary']), ('!selected', 'white')])

    # Dialog-specific Checkbutton style
    style.configure('Dialog.TCheckbutton',
                   background='white',
                   foreground=UI_COLORS['text_primary'],
                   font=('Microsoft YaHei', 10),
                   indicatorcolor='white',
                   indicatorrelief='flat',
                   borderwidth=1)
    style.map('Dialog.TCheckbutton',
             background=[('active', 'white'), ('selected', 'white')],
             foreground=[('active', UI_COLORS['primary']), ('selected', UI_COLORS['primary'])],
             indicatorcolor=[('selected', UI_COLORS['primary']), ('!selected', 'white')])

    # Notebook style - for dialog tabs
    style.configure('TNotebook',
                   background=UI_COLORS['bg_main'],
                   borderwidth=0,
                   relief='flat')

    style.configure('TNotebook.Tab',
                   background=UI_COLORS['bg_main'],  # Light blue background
                   foreground=UI_COLORS['text_primary'],
                   padding=[15, 8],
                   font=('Microsoft YaHei', 10, 'bold'),
                   borderwidth=1)

    style.map('TNotebook.Tab',
             background=[('selected', UI_COLORS['bg_panel']), ('active', UI_COLORS['primary_light'])],
             foreground=[('selected', UI_COLORS['primary']), ('active', UI_COLORS['primary'])],
             expand=[('selected', [1, 1, 1, 0])])

    # Dialog-specific Frame style
    style.configure('Dialog.TFrame',
                   background=UI_COLORS['bg_main'])

    # Dialog-specific LabelFrame style
    style.configure('Dialog.TLabelframe',
                   background=UI_COLORS['bg_main'],
                   relief='solid',
                   borderwidth=1,
                   bordercolor=UI_COLORS['border'])

    style.configure('Dialog.TLabelframe.Label',
                   font=('Microsoft YaHei', 10, 'bold'),
                   foreground=UI_COLORS['primary'],
                   background=UI_COLORS['bg_main'],
                   padding=4)

    # Dialog-specific Label style
    style.configure('Dialog.TLabel',
                   background=UI_COLORS['bg_main'],
                   foreground=UI_COLORS['text_primary'],
                   font=('Microsoft YaHei', 10))

    # Dialog-specific Entry style
    style.configure('Dialog.TEntry',
                   fieldbackground='white',
                   background='white',
                   foreground=UI_COLORS['text_primary'],
                   bordercolor=UI_COLORS['border'],
                   lightcolor=UI_COLORS['primary_light'],
                   darkcolor=UI_COLORS['border'])

    # Dialog-specific Combobox style
    style.configure('Dialog.TCombobox',
                   fieldbackground='white',
                   background='white',
                   foreground=UI_COLORS['text_primary'],
                   bordercolor=UI_COLORS['border'],
                   arrowcolor=UI_COLORS['primary'])

