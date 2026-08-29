import tkinter as tk
from datetime import datetime
import queue
import threading

from .theme import IndustrialTheme as T
from .widgets import Badge, MetricDisplay
from .chart_widget import LiveChartWidget
from .log_widget import LogWidget
from .asset_panel import AssetPanel
from .status_cards import (ForkBuildCard, ConnectionCard, SystemStatusBar)
from fork_bridge import (DB1_TEMP_OFFSET, DB1_CPU_OFFSET, DB1_RAM_OFFSET,
                         DB1_SETPOINT_OFFSET)


class TopBar(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=T.BG_DARK, **kwargs)
        self._build_ui()
        self._update_clock()

    def _build_ui(self):
        logo_frame = tk.Frame(self, bg=T.BG_DARK)
        logo_frame.pack(side='left', padx=T.PADDING_LG, pady=T.PADDING_SM)
        s7_frame = tk.Frame(logo_frame, bg=T.BG_DARK)
        s7_frame.pack(anchor='w')
        tk.Label(s7_frame, text="S7", bg=T.BG_DARK, fg=T.PRIMARY,
                 font=('Tahoma', 22, 'bold')).pack(side='left')
        tk.Label(s7_frame, text=" SCADA", bg=T.BG_DARK, fg=T.TEXT_PRIMARY,
                 font=('Tahoma', 16, 'bold')).pack(side='left')
        tk.Label(logo_frame, text="INDUSTRIAL SUITE", bg=T.BG_DARK,
                 fg=T.TEXT_DIM, font=('Tahoma', 9)).pack(anchor='w')
        title_frame = tk.Frame(self, bg=T.BG_DARK)
        title_frame.pack(side='left', fill='x', expand=True)
        tk.Label(title_frame, text="PLC COMMUNICATION & SENSOR MONITORING",
                 bg=T.BG_DARK, fg=T.TEXT_SECONDARY, font=('Tahoma', 12)).pack(side='left')
        right_frame = tk.Frame(self, bg=T.BG_DARK)
        right_frame.pack(side='right', padx=T.PADDING_LG)
        self.clock_label = tk.Label(right_frame, text="--:--:--", bg=T.BG_DARK,
                                    fg=T.TEXT_PRIMARY, font=('Courier New', 14, 'bold'))
        self.clock_label.pack(anchor='e')
        self.date_label = tk.Label(right_frame, text="", bg=T.BG_DARK,
                                   fg=T.TEXT_MUTED, font=T.FONT_SMALL)
        self.date_label.pack(anchor='e')

    def _update_clock(self):
        now = datetime.now()
        self.clock_label.config(text=now.strftime('%H:%M:%S'))
        self.date_label.config(text=now.strftime('%B %d, %Y'))
        self.after(1000, self._update_clock)


class NavigationSidebar(tk.Frame):
    MENU_ITEMS = [('Dashboard', True, None), ('Assets', False, None),
                  ('Data Monitor', False, None), ('Alarms', False, 2),
                  ('Trends', False, None), ('Reports', False, None),
                  ('Settings', False, None)]

    def __init__(self, parent, on_navigate=None, **kwargs):
        super().__init__(parent, bg=T.BG_NAVY, width=220, **kwargs)
        self.pack_propagate(False)
        self.on_navigate = on_navigate
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="NAVIGATION", bg=T.BG_NAVY, fg=T.PRIMARY,
                 font=T.FONT_TITLE).pack(anchor='w', padx=T.PADDING_MD,
                                         pady=(T.PADDING_LG, T.PADDING_SM))
        for name, active, badge in self.MENU_ITEMS:
            self._create_menu_item(name, active, badge)

    def _create_menu_item(self, name, active, badge_count=None):
        bg = T.PRIMARY_DARK if active else T.BG_NAVY
        fg = T.TEXT_PRIMARY if active else T.TEXT_SECONDARY
        item = tk.Frame(self, bg=bg, cursor='hand2')
        item.pack(fill='x', padx=T.PADDING_SM, pady=2)
        name_label = tk.Label(item, text=name, bg=bg, fg=fg, font=T.FONT_NORMAL)
        name_label.pack(side='left', padx=T.PADDING_MD)
        if badge_count:
            Badge(item, text=str(badge_count), color=T.DANGER, size=20).pack(
                side='right', padx=T.PADDING_SM)
        if active:
            tk.Frame(item, width=3, bg=T.PRIMARY).pack(side='left', fill='y')

        def on_click(e=None):
            if self.on_navigate:
                self.on_navigate(name)

        def on_enter(e):
            if not active:
                item.config(bg=T.BG_HOVER)
                name_label.config(bg=T.BG_HOVER)

        def on_leave(e):
            if not active:
                item.config(bg=T.BG_NAVY)
                name_label.config(bg=T.BG_NAVY)

        for w in (item, name_label):
            w.bind('<Button-1>', on_click)
            w.bind('<Enter>', on_enter)
            w.bind('<Leave>', on_leave)


class MainDashboard(tk.Frame):
    def __init__(self, parent, client=None, build_info=None, server_mode="", **kwargs):
        super().__init__(parent, bg=T.BG_DARK, **kwargs)
        self.client = client
        self.build_info = build_info or {}
        self.server_mode = server_mode
        self._build_ui()

    def _build_ui(self):
        main_area = tk.Frame(self, bg=T.BG_DARK)
        main_area.pack(side='left', fill='both', expand=True, padx=T.PADDING_SM)

        temp_card = tk.Frame(main_area, bg=T.BG_PANEL)
        temp_card.pack(fill='both', expand=True, pady=(T.PADDING_SM, T.PADDING_SM))
        header = tk.Frame(temp_card, bg=T.BG_PANEL)
        header.pack(fill='x', padx=T.PADDING_MD, pady=(T.PADDING_MD, 0))
        tk.Label(header, text="TEMPERATURE SENSOR 01", bg=T.BG_PANEL,
                 fg=T.TEXT_PRIMARY, font=T.FONT_TITLE).pack(side='left')
        live_badge = tk.Frame(header, bg=T.SUCCESS_DARK)
        live_badge.pack(side='right')
        tk.Label(live_badge, text="LIVE", bg=T.SUCCESS_DARK, fg=T.SUCCESS,
                 font=('Tahoma', 10, 'bold'), padx=T.PADDING_SM, pady=2).pack()

        metrics_row = tk.Frame(temp_card, bg=T.BG_PANEL)
        metrics_row.pack(fill='x', padx=T.PADDING_MD, pady=T.PADDING_MD)
        self.current_temp_metric = MetricDisplay(metrics_row, "Current Temperature",
                                                 "--", "C", value_color=T.PRIMARY)
        self.current_temp_metric.pack(side='left', fill='x', expand=True)
        tk.Frame(metrics_row, width=1, bg=T.BORDER).pack(side='left', fill='y',
                                                         padx=T.PADDING_MD)
        self.target_metric = MetricDisplay(metrics_row, "Target Setpoint",
                                           "--", "C", value_color=T.DANGER)
        self.target_metric.pack(side='left', fill='x', expand=True)

        ctrl = tk.Frame(temp_card, bg=T.BG_PANEL)
        ctrl.pack(fill='x', padx=T.PADDING_MD, pady=(0, T.PADDING_SM))
        tk.Label(ctrl, text="Operator Setpoint:", bg=T.BG_PANEL,
                 fg=T.TEXT_SECONDARY, font=T.FONT_NORMAL).pack(side='left')
        self.setpoint_var = tk.StringVar(value="65.50")
        tk.Entry(ctrl, textvariable=self.setpoint_var, width=8,
                 bg=T.BG_NAVY, fg=T.TEXT_PRIMARY, insertbackground=T.PRIMARY,
                 font=T.FONT_MONO_NORMAL, relief='flat').pack(side='left', padx=T.PADDING_SM)
        tk.Button(ctrl, text="APPLY SETPOINT", bg=T.PRIMARY_DARK, fg=T.PRIMARY,
                  font=T.FONT_SMALL, relief='flat', bd=0, padx=12, pady=4,
                  command=self.on_setpoint_apply).pack(side='left')

        self.chart = LiveChartWidget(temp_card, setpoint=65.5)
        self.chart.pack(fill='both', expand=True, padx=T.PADDING_MD,
                        pady=(0, T.PADDING_MD))

        log_card = tk.Frame(main_area, bg=T.BG_PANEL, height=200)
        log_card.pack(fill='x', pady=(0, T.PADDING_SM))
        log_card.pack_propagate(False)
        self.log_widget = LogWidget(log_card, max_entries=50)
        self.log_widget.pack(fill='both', expand=True)

        right_panel = tk.Frame(self, bg=T.BG_DARK, width=320)
        right_panel.pack(side='right', fill='y', padx=(0, T.PADDING_SM))
        right_panel.pack_propagate(False)

        ForkBuildCard(right_panel, self.build_info, self.server_mode).pack(
            fill='x', pady=(T.PADDING_SM, T.PADDING_SM))
        self.connection_card = ConnectionCard(right_panel)
        self.connection_card.pack(fill='x', pady=(T.PADDING_SM, T.PADDING_SM))

    def on_setpoint_apply(self):
        try:
            value = float(self.setpoint_var.get())
        except ValueError:
            self.log_widget.add_entry('WARNING', 'UI', 'Invalid setpoint value')
            return
        if self.client:
            try:
                self.client.write_real(1, DB1_SETPOINT_OFFSET, value)
                self.log_widget.add_entry('INFO', 'UI',
                                          f'Setpoint updated to {value:.2f} C in DB1.DBD12')
            except Exception as e:
                self.log_widget.add_entry('ERROR', 'UI', f'Write Setpoint failed: {e}')
        else:
            self.log_widget.add_entry('WARNING', 'UI', 'No PLC connection - setpoint not applied')


class SCADADashboard(tk.Tk):
    def __init__(self, client=None, build_info=None, server_mode="",
                 sensor_sim=None, system_sim=None):
        super().__init__()
        self.client = client
        self.sensor_sim = sensor_sim
        self.system_sim = system_sim
        self.connect_start = None          # when current connection began
        self.on_shutdown = None
        self.build_info = build_info or {}
        self.server_mode = server_mode

        self.title("S7 SCADA - Industrial Monitoring Suite")
        self.geometry("1400x850")
        self.minsize(1200, 700)
        self.configure(bg=T.BG_DARK)
        T.configure_styles(self)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self._build_ui()

        # Queue and thread for non‑blocking PLC reads
        self._data_q = queue.Queue(maxsize=100)
        self._stop_evt = threading.Event()
        self._reader = None
        if self.client is not None:
            self._reader = threading.Thread(target=self._plc_reader_loop, daemon=True)
            self._reader.start()
            self.drain_queue()                # start UI queue processing
        else:
            # Simulation mode: use old after‑based polling (non‑blocking)
            self.schedule_simulation_poll()

    def _build_ui(self):
        TopBar(self).pack(fill='x')
        main_container = tk.Frame(self, bg=T.BG_DARK)
        main_container.pack(fill='both', expand=True)
        NavigationSidebar(main_container, on_navigate=self._on_navigate).pack(side='left', fill='y')
        self.asset_panel = AssetPanel(main_container, on_asset_select=self._on_asset_select)
        self.asset_panel.pack(side='left', fill='y', padx=T.PADDING_SM)
        self.main_dashboard = MainDashboard(main_container, client=self.client,
                                            build_info=self.build_info,
                                            server_mode=self.server_mode)
        self.main_dashboard.pack(side='left', fill='both', expand=True)
        self.status_bar = SystemStatusBar(self)
        self.status_bar.pack(fill='x', side='bottom')

    def _on_navigate(self, name):
        self.main_dashboard.log_widget.add_entry('INFO', 'NAV', f'Opened view: {name}')

    def _on_asset_select(self, asset):
        if hasattr(self, 'main_dashboard'):
            self.main_dashboard.log_widget.add_entry('INFO', 'UI',
                                                     f'Selected asset: {asset.name} ({asset.ip})')

    # ------------------------------------------------------------------
    # Public logging API (called from external modules)
    # ------------------------------------------------------------------
    def log_message(self, level, source, message):
        """Add an entry to the UI log widget from anywhere (e.g., main)."""
        if hasattr(self, 'main_dashboard') and self.main_dashboard:
            self.main_dashboard.log_widget.add_entry(level, source, message)

    # ------------------------------------------------------------------
    # Background PLC reader (runs in its own thread)
    # ------------------------------------------------------------------
    def _plc_reader_loop(self):
        """Read PLC data in a loop and put results into the queue."""
        while not self._stop_evt.is_set():
            try:
                temp = self.client.read_real(1, DB1_TEMP_OFFSET)
                cpu  = self.client.read_real(1, DB1_CPU_OFFSET)
                mem  = self.client.read_real(1, DB1_RAM_OFFSET)
                sp   = self.client.read_real(1, DB1_SETPOINT_OFFSET)
                self._data_q.put_nowait(('ok', (temp, cpu, mem, sp)))
            except queue.Full:
                pass   # UI is behind, skip this sample
            except Exception as e:
                try:
                    self._data_q.put_nowait(('err', str(e)))
                except queue.Full:
                    pass
            self._stop_evt.wait(0.5)   # poll every 500 ms, but can be interrupted

    # ------------------------------------------------------------------
    # UI thread: drain the queue and update widgets
    # ------------------------------------------------------------------
    def drain_queue(self):
        """Process the latest PLC data sample from the queue (main thread)."""
        latest = None
        while True:
            try:
                latest = self._data_q.get_nowait()
            except queue.Empty:
                break

        if latest is not None:
            kind, payload = latest
            if kind == 'ok':
                self._apply_sample(payload)
            else:
                # PLC read error
                self.main_dashboard.connection_card.set_status(False)
                self.main_dashboard.log_widget.add_entry('ERROR', 'SNAP7',
                                                         f'PLC read failed: {payload}')
                # Reset connection timer so it restarts when we reconnect
                self.connect_start = None

        self.after(200, self.drain_queue)   # check queue every 200 ms

    def _apply_sample(self, data):
        """Update all UI widgets with a fresh PLC sample (called from main thread)."""
        temp, cpu, mem, setpoint = data

        # Reset connection timer if this is the first sample after an error
        if self.connect_start is None:
            self.connect_start = datetime.now()

        # Update charts and metrics
        self.main_dashboard.chart.add_point(temp)
        self.main_dashboard.current_temp_metric.set_value(f"{temp:.2f}")
        self.main_dashboard.target_metric.set_value(f"{setpoint:.2f}")

        # System metrics
        metrics = self.system_sim.get_metrics() if self.system_sim else {}
        self.status_bar.update_values(
            temp=temp,
            cpu=cpu,
            mem=mem,
            net_up=metrics.get('net_up', 0),
            net_down=metrics.get('net_down', 0),
            uptime_seconds=metrics.get('uptime_seconds', 0)
        )

        # Connection uptime
        elapsed = int((datetime.now() - self.connect_start).total_seconds())
        self.main_dashboard.connection_card.set_connection_time(elapsed)
        self.main_dashboard.connection_card.set_status(True)

    # ------------------------------------------------------------------
    # Simulation mode (no real PLC)
    # ------------------------------------------------------------------
    def schedule_simulation_poll(self):
        self._simulate_data()
        self.after(500, self.schedule_simulation_poll)

    def _simulate_data(self):
        """Update widgets with simulated data (runs on main thread)."""
        value = self.sensor_sim.read() if self.sensor_sim else 65.5
        self.main_dashboard.chart.add_point(value)
        self.main_dashboard.current_temp_metric.set_value(f"{value:.2f}")

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------
    def on_closing(self):
        """Stop the background thread and destroy the window."""
        if self._reader is not None:
            self._stop_evt.set()
            self._reader.join(timeout=2.0)
        if self.on_shutdown:
            try:
                self.on_shutdown()
            except Exception:
                pass
        self.destroy()