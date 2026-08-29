import tkinter as tk
from tkinter import ttk

class IndustrialTheme:
    BG_DARK = "#0F172A"
    BG_NAVY = "#1E293B"
    BG_PANEL = "#1E293B"
    BG_HOVER = "#334155"
    PRIMARY = "#38BDF8"
    PRIMARY_NEON = "#0EA5E9"
    PRIMARY_DARK = "#0C4A6E"
    PRIMARY_GLOW = "#7DD3FC"
    SUCCESS = "#22C55E"
    SUCCESS_DARK = "#14532D"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"
    DANGER_BG = "#450A0A"
    TEXT_PRIMARY = "#E2E8F0"
    TEXT_SECONDARY = "#94A3B8"
    TEXT_MUTED = "#64748B"
    TEXT_DIM = "#475569"
    BORDER = "#334155"
    BORDER_ACTIVE = "#38BDF8"
    FONT_XS = ("Tahoma", 10)
    FONT_SMALL = ("Tahoma", 11)
    FONT_NORMAL = ("Tahoma", 12)
    FONT_MEDIUM = ("Tahoma", 13)
    FONT_LARGE = ("Tahoma", 16, "bold")
    FONT_XXL = ("Tahoma", 36, "bold")
    FONT_TITLE = ("Tahoma", 13, "bold")
    FONT_MONO_SMALL = ("Courier New", 11)
    FONT_MONO_NORMAL = ("Courier New", 12)
    PADDING_SM = 8
    PADDING_MD = 12
    PADDING_LG = 16

    @classmethod
    def configure_styles(cls, root):
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('Panel.TFrame', background=cls.BG_PANEL)
        style.configure('Dark.TFrame', background=cls.BG_DARK)
        style.configure('Navy.TFrame', background=cls.BG_NAVY)
        style.configure('Panel.TLabel', background=cls.BG_PANEL, foreground=cls.TEXT_PRIMARY, font=cls.FONT_NORMAL)
        style.configure('Title.TLabel', background=cls.BG_PANEL, foreground=cls.PRIMARY, font=cls.FONT_TITLE)
        style.configure('Log.Treeview', background=cls.BG_NAVY, foreground=cls.TEXT_PRIMARY,
                        fieldbackground=cls.BG_NAVY, borderwidth=0, font=cls.FONT_MONO_SMALL, rowheight=26)
        style.configure('Log.Treeview.Heading', background=cls.BG_PANEL, foreground=cls.TEXT_SECONDARY,
                        font=cls.FONT_SMALL, relief='flat')
        style.map('Log.Treeview', background=[('selected', cls.PRIMARY_DARK)])
