"""
S7 SCADA Dashboard UI - Integrated with ViewManager
Fixed: Parent-child relationship for Dashboard view.
Fixed: Order of UI creation so ViewManager exists before AssetPanel.
Fixed: main_dashboard property defined.
"""

import queue
import threading
import tkinter as tk
from datetime import datetime

from fork_bridge import (
    DB1_CPU_OFFSET,
    DB1_RAM_OFFSET,
    DB1_SETPOINT_OFFSET,
    DB1_TEMP_OFFSET,
)

from .asset_panel import AssetPanel
from .chart_widget import LiveChartWidget
from .log_widget import LogWidget
from .status_cards import ConnectionCard, ForkBuildCard, SystemStatusBar
from .theme import IndustrialTheme as T
from .views import (
    AlarmsView,
    AssetsView,
    DashboardView,
    DataMonitorView,
    ReportsView,
    SettingsView,
    TrendsView,
    ViewManager,
)
from .widgets import Badge, MetricDisplay


# ======================================================================
# TopBar
# ======================================================================
class TopBar(tk.Frame):
    """Header bar with logo, title, and live clock."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=T.BG_DARK, **kwargs)
        self._alive = True
        self._build_ui()
        self._update_clock()

    def _build_ui(self):
        # --- Logo ---
        logo_frame = tk.Frame(self, bg=T.BG_DARK)
        logo_frame.pack(side="left", padx=T.PADDING_LG, pady=T.PADDING_SM)

        s7_frame = tk.Frame(logo_frame, bg=T.BG_DARK)
        s7_frame.pack(anchor="w")

        tk.Label(
            s7_frame,
            text="S7",
            bg=T.BG_DARK,
            fg=T.PRIMARY,
            font=T.FONT_LOGO,
        ).pack(side="left")

        tk.Label(
            s7_frame,
            text=" SCADA",
            bg=T.BG_DARK,
            fg=T.TEXT_PRIMARY,
            font=T.FONT_SUBTITLE,
        ).pack(side="left")

        tk.Label(
            logo_frame,
            text="INDUSTRIAL SUITE",
            bg=T.BG_DARK,
            fg=T.TEXT_DIM,
            font=T.FONT_XS,
        ).pack(anchor="w")

        # --- Title ---
        title_frame = tk.Frame(self, bg=T.BG_DARK)
        title_frame.pack(side="left", fill="x", expand=True)
        tk.Label(
            title_frame,
            text="PLC COMMUNICATION & SENSOR MONITORING",
            bg=T.BG_DARK,
            fg=T.TEXT_SECONDARY,
            font=T.FONT_NORMAL,
        ).pack(side="left")

        # --- Clock ---
        right_frame = tk.Frame(self, bg=T.BG_DARK)
        right_frame.pack(side="right", padx=T.PADDING_LG)

        self.clock_label = tk.Label(
            right_frame,
            text="--:--:--",
            bg=T.BG_DARK,
            fg=T.TEXT_PRIMARY,
            font=T.FONT_CLOCK,
        )
        self.clock_label.pack(anchor="e")

        self.date_label = tk.Label(
            right_frame,
            text="",
            bg=T.BG_DARK,
            fg=T.TEXT_MUTED,
            font=T.FONT_SMALL,
        )
        self.date_label.pack(anchor="e")

    def stop(self):
        """Signal the clock loop to halt."""
        self._alive = False

    def _update_clock(self):
        if not self._alive:
            return
        try:
            now = datetime.now()
            self.clock_label.config(text=now.strftime("%H:%M:%S"))
            self.date_label.config(text=now.strftime("%b %d, %Y"))
            self.after(1000, self._update_clock)
        except tk.TclError:
            self._alive = False


# ======================================================================
# NavigationSidebar
# ======================================================================
class NavigationSidebar(tk.Frame):
    """Left navigation rail with active-state indicator and hover effects."""

    MENU_ITEMS = [
        ("Dashboard", True, None),
        ("Assets", False, None),
        ("Data Monitor", False, None),
        ("Alarms", False, 2),
        ("Trends", False, None),
        ("Reports", False, None),
        ("Settings", False, None),
    ]

    def __init__(self, parent, on_navigate=None, **kwargs):
        super().__init__(parent, bg=T.BG_NAVY, width=240, **kwargs)
        self.pack_propagate(False)
        self.on_navigate = on_navigate
        self._menu_widgets = {}
        self._current_active = "Dashboard"
        self._build_ui()

    def _build_ui(self):
        tk.Label(
            self,
            text="NAVIGATION",
            bg=T.BG_NAVY,
            fg=T.PRIMARY,
            font=T.FONT_TITLE,
        ).pack(anchor="w", padx=T.PADDING_MD, pady=(T.PADDING_LG, T.PADDING_SM))

        for name, active, badge in self.MENU_ITEMS:
            self._create_menu_item(name, active, badge)

    def _create_menu_item(self, name, active, badge_count=None):
        bg = T.BG_NAVY
        fg = T.TEXT_MUTED

        item = tk.Frame(self, bg=bg, cursor="hand2", height=38)
        item.pack(fill="x", padx=T.PADDING_SM, pady=2)
        item.pack_propagate(False)

        indicator = None
        if active:
            indicator = tk.Frame(item, width=3, bg=T.PRIMARY)
            indicator.place(x=0, y=0, relheight=1)
            bg = T.PRIMARY_DARK
            fg = T.TEXT_PRIMARY

        icon_char = "●" if active else "○"
        icon_lbl = tk.Label(item, text=icon_char, bg=bg, fg=fg, font=T.FONT_NORMAL)
        icon_lbl.pack(side="left", padx=(T.PADDING_MD, T.PADDING_SM))

        name_lbl = tk.Label(
            item,
            text=name,
            bg=bg,
            fg=fg,
            font=T.FONT_NORMAL,
            anchor="w",
        )
        name_lbl.pack(side="left", fill="x", expand=True, padx=(0, T.PADDING_SM))

        if badge_count:
            Badge(item, text=str(badge_count), color=T.DANGER, size=18).pack(
                side="right",
                padx=(0, T.PADDING_MD),
            )

        # Store references for dynamic updates
        self._menu_widgets[name] = {
            "frame": item,
            "indicator": indicator,
            "icon": icon_lbl,
            "label": name_lbl,
            "active": active,
        }

        def on_enter(e, _name=name):
            current_act = self._menu_widgets[_name]["active"]
            if not current_act:
                item.config(bg=T.BG_HOVER)
                icon_lbl.config(bg=T.BG_HOVER, fg=T.TEXT_SECONDARY)
                name_lbl.config(bg=T.BG_HOVER, fg=T.TEXT_SECONDARY)

        def on_leave(e, _name=name):
            current_act = self._menu_widgets[_name]["active"]
            if not current_act:
                item.config(bg=T.BG_NAVY)
                icon_lbl.config(bg=T.BG_NAVY, fg=T.TEXT_MUTED)
                name_lbl.config(bg=T.BG_NAVY, fg=T.TEXT_MUTED)

        def on_click(e=None, _name=name):
            self.set_active(_name)
            if self.on_navigate:
                self.on_navigate(_name)

        for w in (item, icon_lbl, name_lbl):
            w.bind("<Button-1>", on_click)
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

    def set_active(self, name):
        """Update visual state of menu items."""
        if name not in self._menu_widgets:
            return

        for n, widgets in self._menu_widgets.items():
            is_active = n == name
            widgets["active"] = is_active

            bg = T.PRIMARY_DARK if is_active else T.BG_NAVY
            fg = T.TEXT_PRIMARY if is_active else T.TEXT_MUTED

            widgets["frame"].config(bg=bg)
            widgets["icon"].config(bg=bg, fg=fg, text="●" if is_active else "○")
            widgets["label"].config(bg=bg, fg=fg)

            if is_active:
                if not widgets["indicator"]:
                    ind = tk.Frame(widgets["frame"], width=3, bg=T.PRIMARY)
                    ind.place(x=0, y=0, relheight=1)
                    widgets["indicator"] = ind
                else:
                    widgets["indicator"].config(bg=T.PRIMARY)
            else:
                if widgets["indicator"]:
                    widgets["indicator"].config(bg=T.BG_NAVY)


# ======================================================================
# MainDashboard
# ======================================================================
class MainDashboard(tk.Frame):
    """Central content area: temperature card, chart, log, and right panel."""

    def __init__(self, parent, client=None, build_info=None, server_mode="", **kwargs):
        super().__init__(parent, bg=T.BG_DARK, **kwargs)
        self.client = client
        self.build_info = build_info or {}
        self.server_mode = server_mode
        self._build_ui()

    def _build_ui(self):
        # ===== FIX: Use grid to avoid conflict with ViewManager's place() =====
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)   # Main area expands
        self.grid_columnconfigure(1, weight=0)   # Right panel fixed

        main_area = tk.Frame(self, bg=T.BG_DARK)
        main_area.grid(row=0, column=0, sticky="nsew", padx=T.PADDING_SM)

        # --- Temperature Card ---
        temp_card = tk.Frame(main_area, bg=T.BG_PANEL)
        temp_card.pack(fill="both", expand=True, pady=(T.PADDING_SM, T.PADDING_SM))

        header = tk.Frame(temp_card, bg=T.BG_PANEL)
        header.pack(fill="x", padx=T.PADDING_MD, pady=(T.PADDING_MD, 0))
        tk.Label(
            header,
            text="TEMPERATURE SENSOR 01",
            bg=T.BG_PANEL,
            fg=T.TEXT_PRIMARY,
            font=T.FONT_TITLE,
        ).pack(side="left")

        live_badge = tk.Frame(header, bg=T.SUCCESS_DARK)
        live_badge.pack(side="right")
        tk.Label(
            live_badge,
            text="LIVE",
            bg=T.SUCCESS_DARK,
            fg=T.SUCCESS,
            font=T.FONT_SMALL,
            padx=T.PADDING_SM,
            pady=2,
        ).pack()

        # Metrics row
        metrics_row = tk.Frame(temp_card, bg=T.BG_PANEL)
        metrics_row.pack(fill="x", padx=T.PADDING_MD, pady=T.PADDING_MD)

        self.current_temp_metric = MetricDisplay(
            metrics_row,
            "Current Temperature",
            "--",
            "°C",
            value_color=T.PRIMARY,
        )
        self.current_temp_metric.pack(side="left", fill="x", expand=True)

        tk.Frame(metrics_row, width=1, bg=T.BORDER).pack(
            side="left",
            fill="y",
            padx=T.PADDING_MD,
        )

        self.target_metric = MetricDisplay(
            metrics_row,
            "Target Setpoint",
            "--",
            "°C",
            value_color=T.DANGER,
        )
        self.target_metric.pack(side="left", fill="x", expand=True)

        # Setpoint control
        ctrl = tk.Frame(temp_card, bg=T.BG_PANEL)
        ctrl.pack(fill="x", padx=T.PADDING_MD, pady=(0, T.PADDING_SM))
        tk.Label(
            ctrl,
            text="Operator Setpoint:",
            bg=T.BG_PANEL,
            fg=T.TEXT_SECONDARY,
            font=T.FONT_NORMAL,
        ).pack(side="left")

        self.setpoint_var = tk.StringVar(value="65.50")
        tk.Entry(
            ctrl,
            textvariable=self.setpoint_var,
            width=8,
            bg=T.BG_NAVY,
            fg=T.TEXT_PRIMARY,
            insertbackground=T.PRIMARY,
            font=T.FONT_MONO_NORMAL,
            relief="flat",
        ).pack(side="left", padx=T.PADDING_SM)

        tk.Button(
            ctrl,
            text="APPLY SETPOINT",
            bg=T.PRIMARY_DARK,
            fg=T.PRIMARY,
            font=T.FONT_SMALL,
            relief="flat",
            bd=0,
            padx=12,
            pady=4,
            command=self.on_setpoint_apply,
        ).pack(side="left")

        # Chart
        self.chart = LiveChartWidget(temp_card, setpoint=65.5)
        self.chart.pack(fill="both", expand=True, padx=T.PADDING_MD, pady=(0, T.PADDING_MD))

        # Log panel
        log_card = tk.Frame(main_area, bg=T.BG_PANEL, height=180)
        log_card.pack(fill="x", pady=(T.PADDING_SM, 0))
        log_card.pack_propagate(False)
        self.log_widget = LogWidget(log_card, max_entries=50)
        self.log_widget.pack(fill="both", expand=True)

        # --- Right Panel ---
        # ===== FIX: Reduced to 180 to give more room for chart =====
        right_panel = tk.Frame(self, bg=T.BG_DARK, width=180)
        right_panel.grid(row=0, column=1, sticky="ns", padx=(0, T.PADDING_SM))
        right_panel.grid_propagate(False)

        ForkBuildCard(right_panel, self.build_info, self.server_mode).pack(
            fill="x",
            pady=(T.PADDING_SM, T.PADDING_SM),
        )
        self.connection_card = ConnectionCard(right_panel)
        self.connection_card.pack(fill="x", pady=(T.PADDING_SM, T.PADDING_SM))

    def on_setpoint_apply(self):
        try:
            value = float(self.setpoint_var.get())
        except ValueError:
            self.log_widget.add_entry("WARNING", "UI", "Invalid setpoint value")
            return

        if self.client:
            try:
                self.client.write_real(1, DB1_SETPOINT_OFFSET, value)
                self.log_widget.add_entry(
                    "INFO",
                    "UI",
                    f"Setpoint updated to {value:.2f} °C in DB1.DBD12",
                )
            except Exception as e:
                self.log_widget.add_entry("ERROR", "UI", f"Write Setpoint failed: {e}")
        else:
            self.log_widget.add_entry(
                "WARNING",
                "UI",
                "No PLC connection - setpoint not applied",
            )

    # ===== FIX: Public method to force chart resize after DPI scaling =====
    def refresh_chart(self):
        if hasattr(self, "chart"):
            self.chart.update_idletasks()
            if hasattr(self.chart, "resize"):
                self.chart.resize()


# ======================================================================
# SCADADashboard (Root Window)
# ======================================================================
class SCADADashboard(tk.Tk):
    """Application root with safe lifecycle management."""

    def __init__(
        self,
        client=None,
        build_info=None,
        server_mode="",
        sensor_sim=None,
        system_sim=None,
        resolved_font=None,
    ):
        super().__init__()

        self.client = client
        self.sensor_sim = sensor_sim
        self.system_sim = system_sim
        self.connect_start = None
        self.on_shutdown = None
        self.build_info = build_info or {}
        self.server_mode = server_mode
        self._alive = True

        # Apply validated font AND rebuild all font tokens
        if resolved_font:
            T.RESOLVED_FONT_FAMILY = resolved_font
            T._rebuild_font_cache()
            for _name, _value in T._build_fonts().items():
                setattr(T, _name, _value)

        self.title("S7 SCADA - Industrial Monitoring Suite")
        # ===== FIX: Further increased geometry =====
        self.geometry("1800x1020")
        self.minsize(1600, 900)
        self.configure(bg=T.BG_DARK)

        # ===== FIX: REMOVED EARLY DPI SCALING =====
        T.configure_styles(self)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self._build_ui()

        # Non-blocking PLC reader via queue
        self._data_q = queue.Queue(maxsize=100)
        self._stop_evt = threading.Event()
        self._reader = None

        if self.client is not None:
            self._reader = threading.Thread(
                target=self._plc_reader_loop,
                daemon=True,
            )
            self._reader.start()
            self.drain_queue()
        else:
            self.schedule_simulation_poll()

    # ------------------------------------------------------------------ Build
    def _build_ui(self):
        self._topbar = TopBar(self)
        self._topbar.pack(fill="x")

        main_container = tk.Frame(self, bg=T.BG_DARK)
        main_container.pack(fill="both", expand=True)

        # Sidebar with navigation callback
        self._sidebar = NavigationSidebar(
            main_container,
            on_navigate=self._on_navigate,
        )
        self._sidebar.pack(side="left", fill="y")

        # ===== FIX: Create ViewManager BEFORE AssetPanel =====
        self.view_manager = ViewManager(main_container)
        self.view_manager.pack(side="left", fill="both", expand=True)

        # Asset Panel (its callback will now see self.view_manager exists)
        self.asset_panel = AssetPanel(
            main_container,
            on_asset_select=self._on_asset_select,
        )
        self.asset_panel.pack(side="left", fill="y", padx=T.PADDING_SM)

        # ===== FIX: Create DashboardView with MainDashboard as child =====
        def create_dashboard_view(parent):
            view = DashboardView(parent)
            # Create MainDashboard as a child of the view itself
            main = MainDashboard(
                view,   # parent is the DashboardView
                client=self.client,
                build_info=self.build_info,
                server_mode=self.server_mode,
            )
            view.inner = main
            main.place(relx=0, rely=0, relwidth=1, relheight=1)
            return view

        self.view_manager.register("Dashboard", create_dashboard_view)

        # Register other views
        self.view_manager.register("Assets", lambda p: AssetsView(p, asset_panel=self.asset_panel))
        self.view_manager.register("Data Monitor", lambda p: DataMonitorView(p))
        self.view_manager.register("Alarms", lambda p: AlarmsView(p))

        def trends_chart_factory(parent):
            return LiveChartWidget(parent, setpoint=65.5)

        self.view_manager.register(
            "Trends", lambda p: TrendsView(p, chart_factory=trends_chart_factory)
        )

        self.view_manager.register("Reports", lambda p: ReportsView(p))
        self.view_manager.register("Settings", lambda p: SettingsView(p))

        # Show default view
        self.view_manager.show("Dashboard")

        self.status_bar = SystemStatusBar(self)
        self.status_bar.pack(fill="x", side="bottom")

    @property
    def main_dashboard(self):
        """Return the MainDashboard instance that is inside the DashboardView."""
        dash_view = self.view_manager._views.get("Dashboard")
        if dash_view and hasattr(dash_view, "inner"):
            return dash_view.inner
        return None

    # ------------------------------------------------------------------ Events
    def _on_navigate(self, name):
        if not self._alive:
            return
        try:
            self.view_manager.show(name)
            self._sidebar.set_active(name)
            if self.main_dashboard:
                self.main_dashboard.log_widget.add_entry("INFO", "NAV", f"Switched to: {name}")
        except KeyError as e:
            print(f"[NAV ERROR] {e}")

    def _on_asset_select(self, asset):
        if not self._alive:
            return
        md = self.main_dashboard
        if md and hasattr(md, "log_widget"):
            md.log_widget.add_entry(
                "INFO",
                "UI",
                f"Selected asset: {asset.name} ({asset.ip})",
            )

    def log_message(self, level, source, message):
        """Thread-safe public logging API for external modules."""
        if not self._alive:
            return
        md = self.main_dashboard
        if md and hasattr(md, "log_widget"):
            md.log_widget.add_entry(level, source, message)

    # ------------------------------------------------------------------ PLC Reader
    def _plc_reader_loop(self):
        while not self._stop_evt.is_set():
            try:
                temp = self.client.read_real(1, DB1_TEMP_OFFSET)
                cpu = self.client.read_real(1, DB1_CPU_OFFSET)
                mem = self.client.read_real(1, DB1_RAM_OFFSET)
                sp = self.client.read_real(1, DB1_SETPOINT_OFFSET)
                self._data_q.put_nowait(("ok", (temp, cpu, mem, sp)))
            except queue.Full:
                pass
            except Exception as e:
                try:
                    self._data_q.put_nowait(("err", str(e)))
                except queue.Full:
                    pass
            self._stop_evt.wait(0.5)

    # ------------------------------------------------------------------ Queue Drain
    def drain_queue(self):
        if not self._alive:
            return

        latest = None
        while True:
            try:
                latest = self._data_q.get_nowait()
            except queue.Empty:
                break

        if latest is not None:
            kind, payload = latest
            if kind == "ok":
                self._apply_sample(payload)
            else:
                if self.main_dashboard:
                    self.main_dashboard.connection_card.set_status(False)
                    self.main_dashboard.log_widget.add_entry(
                        "ERROR",
                        "SNAP7",
                        f"PLC read failed: {payload}",
                    )
                self.connect_start = None

        self.after(200, self.drain_queue)

    def _apply_sample(self, data):
        if not self._alive:
            return

        temp, cpu, mem, setpoint = data

        if self.connect_start is None:
            self.connect_start = datetime.now()

        md = self.main_dashboard
        if md:
            md.chart.add_point(temp)
            md.current_temp_metric.set_value(f"{temp:.2f}")
            md.target_metric.set_value(f"{setpoint:.2f}")

            elapsed = int((datetime.now() - self.connect_start).total_seconds())
            md.connection_card.set_connection_time(elapsed)
            md.connection_card.set_status(True)

        metrics = self.system_sim.get_metrics() if self.system_sim else {}
        self.status_bar.update_values(
            temp=temp,
            cpu=cpu,
            mem=mem,
            net_up=metrics.get("net_up", 0),
            net_down=metrics.get("net_down", 0),
            uptime_seconds=metrics.get("uptime_seconds", 0),
        )

        dm_view = self.view_manager._views.get("Data Monitor")
        if dm_view:
            dm_view.update_tags(
                {"TEMP_01": {"value": f"{temp:.2f}", "unit": "°C", "quality": "GOOD"}}
            )

        trends_view = self.view_manager._views.get("Trends")
        if trends_view:
            trends_view.push_point("TEMP_01", temp)

    # ------------------------------------------------------------------ Simulation Fallback
    def schedule_simulation_poll(self):
        if not self._alive:
            return
        self._simulate_data()
        self.after(500, self.schedule_simulation_poll)

    def _simulate_data(self):
        if not self._alive:
            return
        value = self.sensor_sim.read() if self.sensor_sim else 65.5
        if self.main_dashboard:
            self.main_dashboard.chart.add_point(value)
            self.main_dashboard.current_temp_metric.set_value(f"{value:.2f}")

    # ------------------------------------------------------------------ Shutdown
    def on_closing(self):
        self._alive = False

        if hasattr(self, "_topbar"):
            self._topbar.stop()

        if hasattr(self, "main_dashboard"):
            if hasattr(self.main_dashboard, "chart"):
                self.main_dashboard.chart.stop()

        if self._reader is not None:
            self._stop_evt.set()
            self._reader.join(timeout=2.0)

        if self.on_shutdown:
            try:
                self.on_shutdown()
            except Exception:
                pass

        try:
            self.tk.eval('catch {bind . <<ThemeChanged>> ""}')
            self.tk.eval("""
                catch {
                    foreach w [winfo children .] {
                        catch {bind $w <<ThemeChanged>> ""}
                    }
                }
            """)
        except Exception:
            pass

        try:
            after_ids = self.tk.eval("after info").split()
            for aid in after_ids:
                try:
                    self.after_cancel(aid)
                except Exception:
                    pass
        except Exception:
            pass

        try:
            self.withdraw()
            self.update_idletasks()
        except Exception:
            pass

        try:
            self.quit()
            self.destroy()
        except tk.TclError:
            pass