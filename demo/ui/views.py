"""
ViewManager + pluggable views for the S7 SCADA dashboard.
All views subclass BaseView; grid-based layout; theme constants verified
against theme.py (FALLBACK covers any constant that might be missing).
FIXED: DashboardView simplified (inner widget is placed by factory).
FIXED: All Treeview styles use dot‑free names and explicit rowheight.
"""

import csv
import os
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
import tkinter.font as tkfont

from .theme import IndustrialTheme as T

# Fallbacks for theme constants that may not exist in every theme.py version
FALLBACK = {
    "BG_DARK": "#0F172A",
    "BG_NAVY": "#1E293B",
    "BG_PANEL": "#1E293B",
    "BG_HOVER": "#334155",
    "PRIMARY": "#38BDF8",
    "PRIMARY_DARK": "#0C4A6E",
    "PRIMARY_GLOW": "#7DD3FC",
    "SUCCESS": "#22C55E",
    "SUCCESS_DARK": "#14532D",
    "WARNING": "#F59E0B",
    "DANGER": "#EF4444",
    "DANGER_BG": "#450A0A",
    "TEXT_PRIMARY": "#E2E8F0",
    "TEXT_SECONDARY": "#94A3B8",
    "TEXT_MUTED": "#64748B",
    "TEXT_DIM": "#475569",
    "BORDER": "#334155",
    "BORDER_ACTIVE": "#38BDF8",
    "FONT_XS": ("Tahoma", 10),
    "FONT_SMALL": ("Tahoma", 11),
    "FONT_NORMAL": ("Tahoma", 12),
    "FONT_MEDIUM": ("Tahoma", 13),
    "FONT_LARGE": ("Tahoma", 16, "bold"),
    "FONT_TITLE": ("Tahoma", 13, "bold"),
    "FONT_MONO_SMALL": ("Segoe UI", 9),
    "FONT_MONO_NORMAL": ("Segoe UI", 10),
    "PADDING_SM": 8,
    "PADDING_MD": 12,
    "PADDING_LG": 16,
}


def _c(name):
    """Get a theme constant, falling back if missing."""
    return getattr(T, name, FALLBACK.get(name, "#000000"))


def _get_rowheight():
    """Compute rowheight from the theme's monospaced font."""
    try:
        return tkfont.Font(font=T.FONT_MONO_SMALL).metrics("linespace") + 8
    except:
        return 28  # safe fallback


class BaseView(tk.Frame):
    """Base class for all views with show/hide hooks."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=_c("BG_DARK"), **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def on_show(self):
        pass

    def on_hide(self):
        pass


# ======================================================================
# FIXED DashboardView – simple container, inner widget placed by factory
# ======================================================================
class DashboardView(BaseView):
    """Wraps the MainDashboard widget. The inner widget is created and
    placed by the factory in dashboard_ui.py."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.inner = None   # will be set by the factory


class ViewManager(tk.Frame):
    """Container that lazily builds, caches and swaps views via tkraise."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=_c("BG_DARK"), **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._views = {}
        self._factories = {}
        self._current_name = None
        self._container = tk.Frame(self, bg=_c("BG_DARK"))
        self._container.grid(row=0, column=0, sticky="nsew")
        self._container.grid_rowconfigure(0, weight=1)
        self._container.grid_columnconfigure(0, weight=1)

    def register(self, name, factory):
        self._factories[name] = factory

    @property
    def current(self):
        return self._current_name

    def show(self, name):
        if name == self._current_name:
            return self._views.get(name)
        if name not in self._factories:
            raise KeyError(f"View '{name}' is not registered")
        if name not in self._views:
            self._views[name] = self._factories[name](self._container)
            self._views[name].grid(row=0, column=0, sticky="nsew")
        old = self._views.get(self._current_name)
        if old is not None:
            old.on_hide()
        self._views[name].on_show()
        self._views[name].tkraise()
        self._current_name = name
        return self._views[name]


# ---------------------------------------------------------------------------
# Helper for building Treeview tables with theme styles
# ---------------------------------------------------------------------------

def make_tree(parent, columns, widths=None, height=12):
    container = tk.Frame(parent, bg=_c("BORDER"))
    container.grid(sticky="nsew")

    style = ttk.Style()
    rowh = _get_rowheight()
    style.configure("Custom.Treeview",
                    font=_c("FONT_MONO_SMALL"),
                    rowheight=rowh)
    style.configure("Custom.Treeview.Heading",
                    font=_c("FONT_MONO_SMALL"))

    tree = ttk.Treeview(
        container,
        columns=columns,
        show="headings",
        style="Custom.Treeview",
        height=height,
    )
    for col in columns:
        tree.heading(col, text=col.title(), command=lambda c=col: None)
        tree.column(
            col, width=(widths or {}).get(col, 120), anchor="w", stretch=True
        )
    sb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return tree, container


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class AssetsView(BaseView):
    COLUMNS = ("Tag", "Type", "Zone", "Status", "Last Value", "Updated")

    def __init__(self, parent, asset_panel=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.asset_panel = asset_panel
        self._sort_col = "Tag"
        self._sort_desc = False
        self._rows = []

        header = tk.Frame(self, bg=_c("BG_PANEL"))
        header.grid(row=0, column=0, sticky="ew", padx=_c("PADDING_MD"), pady=_c("PADDING_SM"))
        tk.Label(
            header,
            text="ASSET TABLE",
            bg=_c("BG_PANEL"),
            fg=_c("PRIMARY"),
            font=_c("FONT_TITLE"),
        ).pack(side="left", padx=_c("PADDING_SM"))

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        tree_frame = tk.Frame(self, bg=_c("BG_DARK"))
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=_c("PADDING_MD"))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # ===== FIXED style definitions =====
        style = ttk.Style()
        rowh = _get_rowheight()
        style.configure("Asset.Treeview",
                        background=_c("BG_DARK"),
                        foreground=_c("TEXT_PRIMARY"),
                        fieldbackground=_c("BG_DARK"),
                        font=_c("FONT_MONO_SMALL"),
                        borderwidth=0,
                        relief="flat",
                        rowheight=rowh)
        style.configure("Asset.Treeview.Heading",
                        background=_c("BG_NAVY"),
                        foreground=_c("PRIMARY"),
                        font=_c("FONT_MONO_SMALL"),
                        borderwidth=1,
                        relief="flat")
        style.map("Asset.Treeview",
                  background=[("selected", _c("PRIMARY_DARK"))],
                  foreground=[("selected", _c("TEXT_PRIMARY"))])
        style.map("Asset.Treeview.Heading",
                  background=[("active", _c("BG_HOVER"))])

        self.tree = ttk.Treeview(
            tree_frame,
            columns=self.COLUMNS,
            show="headings",
            style="Asset.Treeview",
            height=14,
        )

        self.tree.column("Tag", width=160, minwidth=120, anchor="w", stretch=True)
        self.tree.column("Type", width=100, minwidth=80, anchor="w", stretch=True)
        self.tree.column("Zone", width=100, minwidth=80, anchor="w", stretch=True)
        self.tree.column("Status", width=100, minwidth=80, anchor="w", stretch=True)
        self.tree.column("Last Value", width=110, minwidth=90, anchor="w", stretch=True)
        self.tree.column("Updated", width=130, minwidth=110, anchor="w", stretch=True)

        for col in self.COLUMNS:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_by(c))

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

        btn_bar = tk.Frame(self, bg=_c("BG_DARK"))
        btn_bar.grid(row=2, column=0, sticky="ew", padx=_c("PADDING_MD"), pady=_c("PADDING_SM"))
        tk.Button(
            btn_bar,
            text="REFRESH FROM PANEL",
            bg=_c("PRIMARY_DARK"),
            fg=_c("PRIMARY"),
            font=_c("FONT_SMALL"),
            relief="flat",
            takefocus=True,
            command=self.refresh_from_panel,
        ).pack(side="left")

    def _sort_by(self, col):
        if self._sort_col == col:
            self._sort_desc = not self._sort_desc
        else:
            self._sort_col = col
            self._sort_desc = False
        self._render()

    def refresh(self, rows):
        self._rows = [tuple(r) for r in rows]
        self._render()

    def refresh_from_panel(self):
        if not self.asset_panel:
            return
        rows = []
        assets_dict = getattr(self.asset_panel, "assets", {})
        for name, item in assets_dict.items():
            atype = getattr(item, "asset_type", "Unknown")
            status = getattr(item, "status", "UNKNOWN")
            rows.append(
                (
                    name,
                    atype,
                    getattr(item, "zone", "-"),
                    status,
                    getattr(item, "last_value", "-"),
                    getattr(item, "updated", "-"),
                )
            )
        self.refresh(rows)

    def _render(self):
        self.tree.delete(*self.tree.get_children())
        rows = sorted(
            self._rows,
            key=lambda r: str(r[self.COLUMNS.index(self._sort_col)]),
            reverse=self._sort_desc,
        )
        for r in rows:
            self.tree.insert("", "end", values=r)

    def on_show(self):
        self.refresh_from_panel()


class DataMonitorView(BaseView):
    COLUMNS = ("tag", "value", "unit", "quality", "timestamp")

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        tk.Label(
            self,
            text="LIVE DATA MONITOR",
            bg=_c("BG_DARK"),
            fg=_c("PRIMARY"),
            font=_c("FONT_TITLE"),
        ).grid(row=0, column=0, sticky="w", padx=_c("PADDING_MD"), pady=_c("PADDING_SM"))
        frame = tk.Frame(self, bg=_c("BG_DARK"))
        frame.grid(row=1, column=0, sticky="nsew", padx=_c("PADDING_MD"))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        rowh = _get_rowheight()
        style.configure("DataMonitor.Treeview",
                        font=_c("FONT_MONO_SMALL"),
                        rowheight=rowh)
        style.configure("DataMonitor.Treeview.Heading",
                        font=_c("FONT_MONO_SMALL"))

        self.tree = ttk.Treeview(
            frame,
            columns=self.COLUMNS,
            show="headings",
            style="DataMonitor.Treeview",
            height=16,
        )
        for col, w in (
            ("tag", 180),
            ("value", 120),
            ("unit", 80),
            ("quality", 100),
            ("timestamp", 180),
        ):
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=w, anchor="w", stretch=True)
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.tag_configure("GOOD", foreground=_c("SUCCESS"))
        self.tree.tag_configure("BAD", foreground=_c("DANGER"))
        self.tree.tag_configure("UNCERTAIN", foreground=_c("WARNING"))
        self._items = {}

    def update_tags(self, data):
        now = datetime.now().strftime("%H:%M:%S")
        for tag, info in data.items():
            if isinstance(info, dict):
                value = info.get("value", "--")
                unit = info.get("unit", "")
                quality = info.get("quality", "GOOD")
            else:
                value, unit, quality = info, "", "GOOD"
            row = (tag, value, unit, quality, now)
            if tag in self._items and self.tree.exists(self._items[tag]):
                self.tree.item(self._items[tag], values=row)
            else:
                self._items[tag] = self.tree.insert("", "end", values=row, tags=(quality,))


class AlarmsView(BaseView):
    COLUMNS = ("Time", "Severity", "Source", "Message", "State")

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        tk.Label(
            self,
            text="ALARM MANAGEMENT",
            bg=_c("BG_DARK"),
            fg=_c("DANGER"),
            font=_c("FONT_TITLE"),
        ).grid(row=0, column=0, sticky="w", padx=_c("PADDING_MD"), pady=_c("PADDING_SM"))
        frame = tk.Frame(self, bg=_c("BG_DARK"))
        frame.grid(row=1, column=0, sticky="nsew", padx=_c("PADDING_MD"))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        rowh = _get_rowheight()
        style.configure("Alarm.Treeview",
                        font=_c("FONT_MONO_SMALL"),
                        rowheight=rowh)
        style.configure("Alarm.Treeview.Heading",
                        font=_c("FONT_MONO_SMALL"))

        self.tree = ttk.Treeview(
            frame,
            columns=self.COLUMNS,
            show="headings",
            style="Alarm.Treeview",
            height=14,
        )
        for col, w in (
            ("Time", 110),
            ("Severity", 90),
            ("Source", 130),
            ("Message", 400),
            ("State", 100),
        ):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="w", stretch=True)
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.tag_configure("CRITICAL", foreground=_c("DANGER"))
        self.tree.tag_configure("WARNING", foreground=_c("WARNING"))
        self.tree.tag_configure("INFO", foreground=_c("PRIMARY"))
        self.tree.tag_configure("ACKED", foreground=_c("TEXT_MUTED"))

        btn_bar = tk.Frame(self, bg=_c("BG_DARK"))
        btn_bar.grid(row=2, column=0, sticky="ew", padx=_c("PADDING_MD"), pady=_c("PADDING_SM"))
        tk.Button(
            btn_bar,
            text="ACKNOWLEDGE SELECTED",
            bg=_c("PRIMARY_DARK"),
            fg=_c("PRIMARY"),
            font=_c("FONT_SMALL"),
            relief="flat",
            takefocus=True,
            command=self.acknowledge_selected,
        ).pack(side="left")
        tk.Button(
            btn_bar,
            text="ACK ALL",
            bg=_c("BG_NAVY"),
            fg=_c("TEXT_SECONDARY"),
            font=_c("FONT_SMALL"),
            relief="flat",
            takefocus=True,
            command=self._ack_all,
        ).pack(side="left", padx=_c("PADDING_SM"))

    def add_alarm(
        self,
        severity="WARNING",
        source="PLC",
        message="Alarm",
        state="ACTIVE",
        timestamp=None,
    ):
        ts = (timestamp or datetime.now()).strftime("%H:%M:%S")
        tag = "ACKED" if state == "ACKED" else severity
        try:
            self.tree.insert("", "end", values=(ts, severity, source, message, state), tags=(tag,))
        except tk.TclError:
            pass

    def acknowledge_selected(self):
        for item in self.tree.selection():
            try:
                values = list(self.tree.item(item, "values"))
                values[4] = "ACKED"
                self.tree.item(item, values=values, tags=("ACKED",))
            except tk.TclError:
                pass

    def _ack_all(self):
        for item in self.tree.get_children():
            try:
                values = list(self.tree.item(item, "values"))
                values[4] = "ACKED"
                self.tree.item(item, values=values, tags=("ACKED",))
            except tk.TclError:
                pass


class TrendsView(BaseView):
    TIMEFRAMES = ("1m", "5m", "15m", "1h")

    def __init__(self, parent, chart_factory=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._chart_factory = chart_factory
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top = tk.Frame(self, bg=_c("BG_DARK"))
        top.grid(row=0, column=0, sticky="ew", padx=_c("PADDING_MD"), pady=_c("PADDING_SM"))
        tk.Label(
            top,
            text="TAG:",
            bg=_c("BG_DARK"),
            fg=_c("TEXT_SECONDARY"),
            font=_c("FONT_NORMAL"),
        ).pack(side="left")
        self.tag_var = tk.StringVar()
        self.tag_combo = ttk.Combobox(
            top,
            textvariable=self.tag_var,
            values=["TEMP_01"],
            width=20,
            state="readonly",
        )
        self.tag_combo.pack(side="left", padx=_c("PADDING_SM"))
        for tf in self.TIMEFRAMES:
            tk.Button(
                top,
                text=tf,
                bg=_c("BG_NAVY"),
                fg=_c("PRIMARY"),
                font=_c("FONT_SMALL"),
                relief="flat",
                takefocus=True,
                command=lambda t=tf: self._select_tf(t),
            ).pack(side="left", padx=2)
        self._active_tf = "5m"

        chart_holder = tk.Frame(self, bg=_c("BG_PANEL"))
        chart_holder.grid(row=1, column=0, sticky="nsew", padx=_c("PADDING_MD"))
        chart_holder.grid_rowconfigure(0, weight=1)
        chart_holder.grid_columnconfigure(0, weight=1)
        if chart_factory is not None:
            self.chart = chart_factory(chart_holder)
            self.chart.grid(row=0, column=0, sticky="nsew")
        else:
            self.chart = None
            tk.Label(
                chart_holder,
                text="No chart available",
                bg=_c("BG_PANEL"),
                fg=_c("TEXT_MUTED"),
            ).grid(row=0, column=0)

    def _select_tf(self, tf):
        self._active_tf = tf

    def set_tags(self, tags):
        self.tag_combo["values"] = list(tags)
        if tags:
            self.tag_var.set(list(tags)[0])

    def push_point(self, tag, value):
        if self.chart is not None and tag == (self.tag_var.get() or tag):
            self.chart.add_point(value)


class ReportsView(BaseView):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        form = tk.Frame(self, bg=_c("BG_PANEL"))
        form.grid(row=0, column=0, sticky="ew", padx=_c("PADDING_MD"), pady=_c("PADDING_SM"))
        tk.Label(
            form,
            text="GENERATE REPORT",
            bg=_c("BG_PANEL"),
            fg=_c("PRIMARY"),
            font=_c("FONT_TITLE"),
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, _c("PADDING_SM")))
        tk.Label(
            form,
            text="From (YYYY-MM-DD):",
            bg=_c("BG_PANEL"),
            fg=_c("TEXT_SECONDARY"),
            font=_c("FONT_SMALL"),
        ).grid(row=1, column=0, sticky="w")
        self.from_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(form, textvariable=self.from_var, takefocus=True).grid(
            row=1, column=1, sticky="ew", padx=_c("PADDING_SM")
        )
        tk.Label(
            form,
            text="To (YYYY-MM-DD):",
            bg=_c("BG_PANEL"),
            fg=_c("TEXT_SECONDARY"),
            font=_c("FONT_SMALL"),
        ).grid(row=1, column=2, sticky="w")
        self.to_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(form, textvariable=self.to_var, takefocus=True).grid(
            row=1, column=3, sticky="ew", padx=_c("PADDING_SM")
        )
        tk.Label(
            form,
            text="Report type:",
            bg=_c("BG_PANEL"),
            fg=_c("TEXT_SECONDARY"),
            font=_c("FONT_SMALL"),
        ).grid(row=2, column=0, sticky="w", pady=(_c("PADDING_SM"), 0))
        self.type_var = tk.StringVar(value="Temperature History")
        ttk.Combobox(
            form,
            textvariable=self.type_var,
            takefocus=True,
            values=[
                "Temperature History",
                "Alarm Summary",
                "Data Quality",
                "Full Export",
            ],
            state="readonly",
            width=24,
        ).grid(
            row=2,
            column=1,
            sticky="w",
            padx=_c("PADDING_SM"),
            pady=(_c("PADDING_SM"), 0),
        )
        tk.Button(
            form,
            text="GENERATE CSV",
            bg=_c("PRIMARY_DARK"),
            fg=_c("PRIMARY"),
            font=_c("FONT_SMALL"),
            relief="flat",
            takefocus=True,
            command=self.generate_csv,
        ).grid(row=2, column=2, sticky="w", pady=(_c("PADDING_SM"), 0))
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(3, weight=1)

        self.status_var = tk.StringVar(value="")
        tk.Label(
            self,
            textvariable=self.status_var,
            bg=_c("BG_DARK"),
            fg=_c("SUCCESS"),
            font=_c("FONT_SMALL"),
        ).grid(row=1, column=0, sticky="w", padx=_c("PADDING_MD"))

        frame = tk.Frame(self, bg=_c("BG_DARK"))
        frame.grid(row=2, column=0, sticky="nsew", padx=_c("PADDING_MD"), pady=_c("PADDING_SM"))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        cols = ("timestamp", "tag", "value", "unit")

        style = ttk.Style()
        rowh = _get_rowheight()
        style.configure("Report.Treeview",
                        font=_c("FONT_MONO_SMALL"),
                        rowheight=rowh)
        style.configure("Report.Treeview.Heading",
                        font=_c("FONT_MONO_SMALL"))

        self.tree = ttk.Treeview(
            frame, columns=cols, show="headings", style="Report.Treeview", height=10
        )
        for col, w in (("timestamp", 160), ("tag", 140), ("value", 120), ("unit", 80)):
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=w, anchor="w", stretch=True)
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

    def generate_csv(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(os.getcwd(), f"report_{ts}.csv")
        rows = []
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["timestamp", "tag", "value", "unit"])
                now = datetime.now()
                for i in range(10):
                    t = now.strftime("%Y-%m-%d %H:%M:%S")
                    value = round(60 + i * 0.5, 2)
                    w.writerow([t, "TEMP_01", value, "C"])
                    rows.append((t, "TEMP_01", value, "C"))
            self.status_var.set(f"Report written: {path}")
        except Exception as e:
            self.status_var.set(f"Report failed: {e}")
            return
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("", "end", values=r)


class SettingsView(BaseView):
    DEFAULTS = {
        "host": "127.0.0.1",
        "port": 102,
        "unit_id": 1,
        "poll_interval_ms": 500,
        "simulation": True,
        "theme": "Industrial Dark",
    }

    def __init__(self, parent, on_save=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_save = on_save
        self.grid_columnconfigure(0, weight=1)

        form = tk.Frame(self, bg=_c("BG_PANEL"))
        form.grid(row=0, column=0, sticky="nsew", padx=_c("PADDING_MD"), pady=_c("PADDING_MD"))
        form.grid_columnconfigure(1, weight=1)

        def add_row(r, label):
            tk.Label(
                form,
                text=label,
                bg=_c("BG_PANEL"),
                fg=_c("TEXT_SECONDARY"),
                font=_c("FONT_SMALL"),
            ).grid(row=r, column=0, sticky="w", pady=4, padx=_c("PADDING_SM"))
            return r + 1

        r = add_row(0, "PLC Host:")
        self.host_var = tk.StringVar(value=self.DEFAULTS["host"])
        ttk.Entry(form, textvariable=self.host_var, takefocus=True).grid(
            row=r - 1, column=1, sticky="ew", padx=_c("PADDING_SM"), pady=4
        )

        r = add_row(r, "Port:")
        self.port_var = tk.StringVar(value=str(self.DEFAULTS["port"]))
        ttk.Entry(form, textvariable=self.port_var, takefocus=True).grid(
            row=r - 1, column=1, sticky="ew", padx=_c("PADDING_SM"), pady=4
        )

        r = add_row(r, "Unit ID:")
        self.unit_var = tk.StringVar(value=str(self.DEFAULTS["unit_id"]))
        ttk.Entry(form, textvariable=self.unit_var, takefocus=True).grid(
            row=r - 1, column=1, sticky="ew", padx=_c("PADDING_SM"), pady=4
        )

        r = add_row(r, "Poll Interval (ms):")
        self.poll_var = tk.StringVar(value=str(self.DEFAULTS["poll_interval_ms"]))
        ttk.Entry(form, textvariable=self.poll_var, takefocus=True).grid(
            row=r - 1, column=1, sticky="ew", padx=_c("PADDING_SM"), pady=4
        )

        r = add_row(r, "Simulation Mode:")
        self.sim_var = tk.BooleanVar(value=self.DEFAULTS["simulation"])
        ttk.Checkbutton(form, variable=self.sim_var, takefocus=True).grid(
            row=r - 1, column=1, sticky="w", padx=_c("PADDING_SM"), pady=4
        )

        r = add_row(r, "Theme:")
        self.theme_var = tk.StringVar(value=self.DEFAULTS["theme"])
        ttk.Combobox(
            form,
            textvariable=self.theme_var,
            takefocus=True,
            values=["Industrial Dark", "Light"],
            state="readonly",
        ).grid(row=r - 1, column=1, sticky="ew", padx=_c("PADDING_SM"), pady=4)

        btns = tk.Frame(form, bg=_c("BG_PANEL"))
        btns.grid(
            row=r,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=_c("PADDING_SM"),
            pady=_c("PADDING_MD"),
        )
        tk.Button(
            btns,
            text="SAVE",
            bg=_c("PRIMARY_DARK"),
            fg=_c("PRIMARY"),
            font=_c("FONT_SMALL"),
            relief="flat",
            takefocus=True,
            command=self._save,
        ).pack(side="left")
        tk.Button(
            btns,
            text="RESET DEFAULTS",
            bg=_c("BG_NAVY"),
            fg=_c("TEXT_SECONDARY"),
            font=_c("FONT_SMALL"),
            relief="flat",
            takefocus=True,
            command=self._reset,
        ).pack(side="left", padx=_c("PADDING_SM"))

    def _save(self):
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Invalid Port", "Port must be an integer (1-65535).")
            return
        if not (1 <= port <= 65535):
            messagebox.showerror("Invalid Port", "Port must be between 1 and 65535.")
            return
        try:
            interval = int(self.poll_var.get())
        except ValueError:
            messagebox.showerror("Invalid Interval", "Poll interval must be an integer (ms).")
            return
        if interval < 50:
            messagebox.showerror("Invalid Interval", "Poll interval must be at least 50 ms.")
            return
        settings = {
            "host": self.host_var.get().strip() or "127.0.0.1",
            "port": port,
            "unit_id": int(self.unit_var.get() or 1),
            "poll_interval_ms": interval,
            "simulation": self.sim_var.get(),
            "theme": self.theme_var.get(),
        }
        if self.on_save:
            self.on_save(settings)

    def _reset(self):
        self.host_var.set(self.DEFAULTS["host"])
        self.port_var.set(str(self.DEFAULTS["port"]))
        self.unit_var.set(str(self.DEFAULTS["unit_id"]))
        self.poll_var.set(str(self.DEFAULTS["poll_interval_ms"]))
        self.sim_var.set(self.DEFAULTS["simulation"])
        self.theme_var.set(self.DEFAULTS["theme"])