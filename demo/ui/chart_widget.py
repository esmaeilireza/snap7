"""
Live Temperature Chart Widget
"""
import tkinter as tk
from datetime import datetime
from collections import deque
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from .theme import IndustrialTheme as T

class LiveChartWidget(tk.Frame):
    def __init__(self, parent, title="Temperature (°C)", max_points=60, setpoint=65.5, **kwargs):
        super().__init__(parent, bg=T.BG_PANEL, **kwargs)
        self.max_points = max_points
        self.setpoint = setpoint
        self.timestamps = deque(maxlen=max_points)
        self.temperatures = deque(maxlen=max_points)
        
        self._build_header(title)
        self._build_chart()
        self._build_controls()
    
    def _build_header(self, title):
        header = tk.Frame(self, bg=T.BG_PANEL)
        header.pack(fill='x', padx=T.PADDING_MD, pady=(T.PADDING_MD, 0))
        tk.Label(header, text=title, bg=T.BG_PANEL, fg=T.TEXT_SECONDARY, 
                font=T.FONT_MEDIUM).pack(side='left')
    
    def _build_chart(self):
        self.fig = Figure(figsize=(8, 3.5), dpi=100, facecolor=T.BG_PANEL)
        self.ax = self.fig.add_subplot(111)
        
        # Styling
        self.ax.set_facecolor(T.BG_NAVY)
        self.ax.tick_params(colors=T.TEXT_SECONDARY, labelsize=8)
        self.ax.spines['bottom'].set_color(T.BORDER)
        self.ax.spines['left'].set_color(T.BORDER)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.grid(True, linestyle=':', alpha=0.3, color=T.PRIMARY_DARK)
        
        # Setpoint Line
        self.ax.axhline(y=self.setpoint, color=T.DANGER, linestyle='--', linewidth=1.5, alpha=0.8)
        self.ax.text(0.98, self.setpoint, f"{self.setpoint:.2f} SETPOINT", color=T.DANGER, 
                    fontsize=9, fontweight='bold', transform=self.ax.get_yaxis_transform(),
                    ha='right', va='bottom', bbox=dict(boxstyle='round,pad=0.3', 
                    facecolor=T.DANGER_BG, edgecolor=T.DANGER, alpha=0.8))
        
        # Data Line
        self.line, = self.ax.plot([], [], color=T.PRIMARY_GLOW, linewidth=2, label='Temperature')
        self.fill = None
        
        self.ax.set_xlabel('Time (HH:MM:SS)', color=T.TEXT_SECONDARY, fontsize=9)
        self.ax.set_ylabel('Temperature (°C)', color=T.TEXT_SECONDARY, fontsize=9)
        self.ax.set_ylim(56, 70)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        self.fig.tight_layout()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().config(bg=T.BG_PANEL, highlightthickness=0)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=T.PADDING_MD, pady=T.PADDING_SM)
        self.canvas.draw()
    
    def _build_controls(self):
        controls = tk.Frame(self, bg=T.BG_PANEL)
        controls.pack(fill='x', padx=T.PADDING_MD, pady=T.PADDING_SM)
        
        timeframes = ['1M', '5M', '15M', '1H', '4H', '1D', '1W', '1M']
        self.tf_buttons = {}
        for tf in timeframes:
            btn = tk.Button(controls, text=tf, bg=T.PRIMARY_DARK if tf == '5M' else T.BG_NAVY,
                           fg=T.PRIMARY if tf == '5M' else T.TEXT_SECONDARY, font=T.FONT_SMALL,
                           relief='flat', bd=0, padx=12, pady=4,
                           command=lambda t=tf: self._select_timeframe(t))
            btn.pack(side='left', padx=2)
            self.tf_buttons[tf] = btn
        
        tk.Button(controls, text="⚙ AUTO SCALE", bg=T.BG_NAVY, fg=T.PRIMARY,
                 font=T.FONT_SMALL, relief='flat', bd=0, padx=12, pady=4,
                 command=self._auto_scale).pack(side='right')
    
    def _select_timeframe(self, tf):
        for t, btn in self.tf_buttons.items():
            btn.config(bg=T.PRIMARY_DARK if t == tf else T.BG_NAVY,
                      fg=T.PRIMARY if t == tf else T.TEXT_SECONDARY)
    
    def _auto_scale(self):
        if self.temperatures:
            self.ax.set_ylim(min(self.temperatures) - 2, max(self.temperatures) + 2)
            self.canvas.draw()
    
    def add_point(self, temperature, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()
        self.timestamps.append(timestamp)
        self.temperatures.append(temperature)
        
        self.line.set_data(list(self.timestamps), list(self.temperatures))
        if self.fill:
            self.fill.remove()
        self.fill = self.ax.fill_between(list(self.timestamps), list(self.temperatures), 
                                        alpha=0.2, color=T.PRIMARY_GLOW)
        
        if self.timestamps:
            self.ax.set_xlim(self.timestamps[0], self.timestamps[-1])
        
        if hasattr(self, '_endpoint'):
            self._endpoint.remove()
        if self.timestamps:
            self._endpoint = self.ax.scatter([self.timestamps[-1]], [self.temperatures[-1]],
                                            color=T.PRIMARY_GLOW, s=80, zorder=5,
                                            edgecolors='white', linewidth=2)
        
        self.fig.autofmt_xdate(rotation=0)
        self.canvas.draw_idle()