"""
Live Temperature Chart Widget
Fixed: datetime-safe xlim, post-destroy guards, efficient rendering.
"""

import tkinter as tk
from collections import deque
from datetime import datetime, timedelta  # 🔧 FIX: added timedelta

import matplotlib

matplotlib.use("TkAgg")

import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .theme import IndustrialTheme as T


class LiveChartWidget(tk.Frame):
    def __init__(self, parent, title="Temperature (°C)", max_points=60, setpoint=65.5, **kwargs):
        super().__init__(parent, bg=T.BG_PANEL, **kwargs)
        self.max_points = max_points
        self.setpoint = setpoint
        self.timestamps = deque(maxlen=max_points)
        self.temperatures = deque(maxlen=max_points)
        self._alive = True
        self._endpoint = None
        self.fill = None

        self._build_header(title)
        self._build_chart()
        self._build_controls()

    # ------------------------------------------------------------------ BUILD
    def _build_header(self, title):
        header = tk.Frame(self, bg=T.BG_PANEL)
        header.pack(fill="x", padx=T.PADDING_MD, pady=(T.PADDING_MD, 0))
        tk.Label(header, text=title, bg=T.BG_PANEL, fg=T.TEXT_SECONDARY, font=T.FONT_MEDIUM).pack(
            side="left"
        )

    def _build_chart(self):
        self.fig = Figure(figsize=(8, 3.5), dpi=100, facecolor=T.BG_PANEL)
        self.ax = self.fig.add_subplot(111)

        self.ax.set_facecolor(T.BG_NAVY)
        self.ax.tick_params(colors=T.TEXT_SECONDARY, labelsize=8)
        self.ax.spines["bottom"].set_color(T.BORDER)
        self.ax.spines["left"].set_color(T.BORDER)
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.grid(True, linestyle=":", alpha=0.3, color=T.PRIMARY_DARK)

        # Setpoint line
        self.ax.axhline(y=self.setpoint, color=T.DANGER, linestyle="--", linewidth=1.5, alpha=0.8)
        self.ax.text(
            0.98,
            self.setpoint,
            f"{self.setpoint:.2f} SETPOINT",
            color=T.DANGER,
            fontsize=9,
            fontweight="bold",
            transform=self.ax.get_yaxis_transform(),
            ha="right",
            va="bottom",
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor=T.DANGER_BG,
                edgecolor=T.DANGER,
                alpha=0.8,
            ),
        )

        (self.line,) = self.ax.plot([], [], color=T.PRIMARY_GLOW, linewidth=2, label="Temperature")
        self.fill = None

        self.ax.set_xlabel("Time (HH:MM:SS)", color=T.TEXT_SECONDARY, fontsize=9)
        self.ax.set_ylabel("Temperature (°C)", color=T.TEXT_SECONDARY, fontsize=9)
        self.ax.set_ylim(56, 70)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))

        self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().config(bg=T.BG_PANEL, highlightthickness=0)
        self.canvas.get_tk_widget().pack(
            fill="both", expand=True, padx=T.PADDING_MD, pady=T.PADDING_SM
        )
        self.canvas.draw()

    def _build_controls(self):
        controls = tk.Frame(self, bg=T.BG_PANEL)
        controls.pack(fill="x", padx=T.PADDING_MD, pady=T.PADDING_SM)

        timeframes = ["1M", "5M", "15M", "1H", "4H", "1D", "1W", "1M"]
        self.tf_buttons = {}
        for tf in timeframes:
            btn = tk.Button(
                controls,
                text=tf,
                bg=T.PRIMARY_DARK if tf == "5M" else T.BG_NAVY,
                fg=T.PRIMARY if tf == "5M" else T.TEXT_SECONDARY,
                font=T.FONT_SMALL,
                relief="flat",
                bd=0,
                padx=12,
                pady=4,
                command=lambda t=tf: self._select_timeframe(t),
            )
            btn.pack(side="left", padx=2)
            self.tf_buttons[tf] = btn

        tk.Button(
            controls,
            text="⚙ AUTO SCALE",
            bg=T.BG_NAVY,
            fg=T.PRIMARY,
            font=T.FONT_SMALL,
            relief="flat",
            bd=0,
            padx=12,
            pady=4,
            command=self._auto_scale,
        ).pack(side="right")

    # ------------------------------------------------------------------ CONTROLS
    def _select_timeframe(self, tf):
        for t, btn in self.tf_buttons.items():
            btn.config(
                bg=T.PRIMARY_DARK if t == tf else T.BG_NAVY,
                fg=T.PRIMARY if t == tf else T.TEXT_SECONDARY,
            )

    def _auto_scale(self):
        if not self._alive:
            return
        if self.temperatures:
            self.ax.set_ylim(min(self.temperatures) - 2, max(self.temperatures) + 2)
            self.canvas.draw_idle()

    # ------------------------------------------------------------------ LIFECYCLE
    def stop(self):
        """Call from parent on_closing to prevent post-destroy updates."""
        self._alive = False

    # ------------------------------------------------------------------ DATA
    def add_point(self, temperature, timestamp=None):
        if not self._alive:
            return

        if timestamp is None:
            timestamp = datetime.now()

        self.timestamps.append(timestamp)
        self.temperatures.append(temperature)

        ts_list = list(self.timestamps)
        temp_list = list(self.temperatures)
        self.line.set_data(ts_list, temp_list)

        # Update fill
        if self.fill is not None:
            self.fill.remove()
        self.fill = self.ax.fill_between(ts_list, temp_list, alpha=0.2, color=T.PRIMARY_GLOW)

        # 🔧 FIX: datetime-safe xlim using timedelta instead of float arithmetic
        if len(ts_list) >= 2:
            t_min, t_max = ts_list[0], ts_list[-1]
            if t_min != t_max:
                self.ax.set_xlim(t_min, t_max)
            else:
                pad = timedelta(seconds=1)
                self.ax.set_xlim(t_min - pad, t_max + pad)
        elif len(ts_list) == 1:
            pad = timedelta(seconds=1)
            self.ax.set_xlim(ts_list[0] - pad, ts_list[0] + pad)
        # else: empty → skip xlim

        # Endpoint marker
        if self._endpoint is not None:
            self._endpoint.remove()
        if ts_list:
            self._endpoint = self.ax.scatter(
                [ts_list[-1]],
                [temp_list[-1]],
                color=T.PRIMARY_GLOW,
                s=80,
                zorder=5,
                edgecolors="white",
                linewidth=2,
            )

        self.fig.autofmt_xdate(rotation=0)

        try:
            self.canvas.draw_idle()
        except tk.TclError:
            self._alive = False
