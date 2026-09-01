"""
S7 SCADA Industrial Theme
Unified color palette + dynamic font resolution + ttk style configuration.
"""

from tkinter import ttk


class IndustrialTheme:
    # ==================================================================
    # Color Palette
    # ==================================================================
    # Backgrounds (layered for visual depth)
    BG_DARK = "#0B1120"  # Main application background
    BG_NAVY = "#151E32"  # Sidebar / navigation rail
    BG_PANEL = "#1E293B"  # Card / widget surface
    BG_HOVER = "#334155"  # Interactive hover state

    # Primary accent
    PRIMARY = "#38BDF8"
    PRIMARY_NEON = "#0EA5E9"
    PRIMARY_DARK = "#0C4A6E"
    PRIMARY_GLOW = "#7DD3FC"

    # Semantic colors
    SUCCESS = "#22C55E"
    SUCCESS_DARK = "#14532D"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"
    DANGER_BG = "#450A0A"

    # Text hierarchy
    TEXT_PRIMARY = "#F1F5F9"  # High‑emphasis (WCAG AA on BG_DARK/BG_NAVY)
    TEXT_SECONDARY = "#94A3B8"  # Medium‑emphasis
    TEXT_MUTED = "#64748B"  # Low‑emphasis / placeholders
    TEXT_DIM = "#475569"  # Minimal / disabled

    # Borders
    BORDER = "#334155"
    BORDER_ACTIVE = "#38BDF8"

    # Spacing scale (px)
    PADDING_SM = 6
    PADDING_MD = 10
    PADDING_LG = 14

    # ==================================================================
    # Dynamic Font System
    # ==================================================================
    # 🔧 Overridden at runtime by scada_dashboard._resolve_font_family()
    RESOLVED_FONT_FAMILY = "Segoe UI Variable"
    MONO_FAMILY = "Consolas"

    @classmethod
    def _font(cls, size, weight="normal"):
        """Build a font tuple using the resolved proportional family."""
        return (cls.RESOLVED_FONT_FAMILY, size, weight)

    @classmethod
    def _mono(cls, size, weight="normal"):
        """Build a font tuple using the monospace family."""
        return (cls.MONO_FAMILY, size, weight)

    @classmethod
    def _build_fonts(cls):
        """Build all font tuples using current RESOLVED_FONT_FAMILY."""
        f = cls._font
        m = cls._mono
        return {
            "FONT_XS": f(9),
            "FONT_SMALL": f(10),
            "FONT_NORMAL": f(11),
            "FONT_MEDIUM": f(12),
            "FONT_LARGE": f(14),
            "FONT_XXL": f(28),
            "FONT_TITLE": f(11, "bold"),
            "FONT_SUBTITLE": f(14),
            "FONT_LOGO": f(20, "bold"),
            "FONT_MONO": m(10),
            "FONT_MONO_SMALL": m(10),
            "FONT_MONO_NORMAL": m(11),
            "FONT_CLOCK": m(13),
        }

    # Class‑level font cache – rebuilt when RESOLVED_FONT_FAMILY changes
    _font_cache = {}

    @classmethod
    def _rebuild_font_cache(cls):
        cls._font_cache = cls._build_fonts()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._rebuild_font_cache()

    @classmethod
    def __class_getitem__(cls, key):
        if key in cls._font_cache:
            return cls._font_cache[key]
        raise KeyError(key)

    # ==================================================================
    # TTK Style Configuration
    # ==================================================================
    @classmethod
    def configure_styles(cls, root):
        """Apply theme to all ttk widgets using the resolved font family."""
        style = ttk.Style(root)
        style.theme_use("clam")

        family = cls.RESOLVED_FONT_FAMILY
        mono = cls.MONO_FAMILY

        # Global default
        style.configure(
            ".",
            background=cls.BG_DARK,
            foreground=cls.TEXT_PRIMARY,
            font=(family, 10),
            borderwidth=0,
        )

        # Frames
        style.configure("Panel.TFrame", background=cls.BG_PANEL)
        style.configure("Dark.TFrame", background=cls.BG_DARK)
        style.configure("Navy.TFrame", background=cls.BG_NAVY)

        # Labels
        style.configure(
            "Panel.TLabel",
            background=cls.BG_PANEL,
            foreground=cls.TEXT_PRIMARY,
            font=(family, 11),
        )
        style.configure(
            "Title.TLabel",
            background=cls.BG_PANEL,
            foreground=cls.PRIMARY,
            font=(family, 11, "bold"),
        )

        # ================================================================
        # FIX: Generic Treeview with proper rowheight for ALL treeviews
        # ================================================================
        import tkinter.font as _tkfont
        _rowh = _tkfont.Font(family=mono, size=10).metrics("linespace") + 10
        style.configure(
            "Treeview",
            background=cls.BG_PANEL,
            fieldbackground=cls.BG_PANEL,
            foreground=cls.TEXT_PRIMARY,
            borderwidth=0,
            font=(mono, 10),
            rowheight=_rowh,
        )
        style.configure(
            "Treeview.Heading",
            background=cls.BG_NAVY,
            foreground=cls.TEXT_SECONDARY,
            relief="flat",
            padding=(6, 6),
            font=(family, 10, "bold"),
        )
        style.map(
            "Treeview",
            background=[("selected", cls.PRIMARY_DARK)],
            foreground=[("selected", cls.TEXT_PRIMARY)],
        )

        # Log Treeview – now a child style to inherit rowheight
        style.configure(
            "Treeview.Log",
            background=cls.BG_NAVY,
            foreground=cls.TEXT_PRIMARY,
            fieldbackground=cls.BG_NAVY,
            borderwidth=0,
            font=(mono, 10),
            # rowheight is inherited from base "Treeview"
        )
        style.configure(
            "Treeview.Log.Heading",
            background=cls.BG_PANEL,
            foreground=cls.TEXT_SECONDARY,
            font=(family, 10),
            relief="flat",
        )
        style.map(
            "Treeview.Log",
            background=[("selected", cls.PRIMARY_DARK)],
        )

        # Buttons (flat industrial look)
        style.configure(
            "Industrial.TButton",
            background=cls.PRIMARY_DARK,
            foreground=cls.PRIMARY,
            font=(family, 10),
            padding=(12, 4),
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Industrial.TButton",
            background=[("active", cls.BG_HOVER)],
        )

        # Entry fields
        style.configure(
            "Industrial.TEntry",
            fieldbackground=cls.BG_NAVY,
            foreground=cls.TEXT_PRIMARY,
            insertcolor=cls.PRIMARY,
            font=(mono, 11),
            borderwidth=0,
            padding=4,
        )

        # Progress bars
        style.configure(
            "Industrial.Horizontal.TProgressbar",
            troughcolor=cls.BG_NAVY,
            background=cls.PRIMARY,
            borderwidth=0,
        )

        # Scrollbars
        style.configure(
            "Industrial.Vertical.TScrollbar",
            background=cls.BG_PANEL,
            troughcolor=cls.BG_DARK,
            borderwidth=0,
            arrowsize=0,
        )
        style.map(
            "Industrial.Vertical.TScrollbar",
            background=[("active", cls.BG_HOVER)],
        )


# ======================================================================
# 🔧 Finalise font cache and inject font tokens as real class attributes
# ======================================================================
IndustrialTheme._rebuild_font_cache()

for _name, _value in IndustrialTheme._build_fonts().items():
    setattr(IndustrialTheme, _name, _value)