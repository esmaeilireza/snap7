import tkinter as tk
from .theme import IndustrialTheme as T
from .widgets import StatusIndicator, InfoRow


class ForkBuildCard(tk.Frame):
    def __init__(self, parent, info, server_mode, **kwargs):
        super().__init__(parent, bg=T.BG_PANEL, **kwargs)
        header = tk.Frame(self, bg=T.BG_PANEL)
        header.pack(fill='x', padx=T.PADDING_MD, pady=(T.PADDING_MD, T.PADDING_SM))
        tk.Label(header, text="FORK BUILD (THIS REPO)", bg=T.BG_PANEL,
                 fg=T.PRIMARY, font=T.FONT_TITLE).pack(side='left')
        InfoRow(self, "Upstream", info.get("upstream", "n/a"), T.TEXT_SECONDARY).pack(
            fill='x', padx=T.PADDING_MD, pady=(0, 2))
        InfoRow(self, "Branch", info.get("branch", "n/a")).pack(
            fill='x', padx=T.PADDING_MD, pady=(2, 2))
        InfoRow(self, "Commit", info.get("commit", "n/a")).pack(
            fill='x', padx=T.PADDING_MD, pady=(2, 2))
        InfoRow(self, "DLL SHA256", info.get("dll_sha", "n/a")).pack(
            fill='x', padx=T.PADDING_MD, pady=(2, 2))
        InfoRow(self, "Server Mode", server_mode, T.SUCCESS).pack(
            fill='x', padx=T.PADDING_MD, pady=(2, 2))
        tk.Label(self, text="Both ends of the wire run THIS repo's compiled code.",
                 bg=T.BG_PANEL, fg=T.TEXT_DIM, font=T.FONT_XS,
                 wraplength=260, justify='left').pack(
            anchor='w', padx=T.PADDING_MD, pady=(2, T.PADDING_MD))


class ConnectionCard(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=T.BG_PANEL, **kwargs)
        header = tk.Frame(self, bg=T.BG_PANEL)
        header.pack(fill='x', padx=T.PADDING_MD, pady=(T.PADDING_MD, T.PADDING_SM))
        tk.Label(header, text="PLC CONNECTION", bg=T.BG_PANEL,
                 fg=T.PRIMARY, font=T.FONT_TITLE).pack(side='left')
        
        self.status_indicator = StatusIndicator(self, size=12, color=T.SUCCESS)
        self.status_indicator.pack(anchor='w', padx=T.PADDING_MD, pady=(0, 2))
        
        status_frame = tk.Frame(self, bg=T.BG_PANEL)
        status_frame.pack(fill='x', padx=T.PADDING_MD)
        tk.Label(status_frame, text="Status:", bg=T.BG_PANEL,
                 fg=T.TEXT_SECONDARY, font=T.FONT_SMALL).pack(side='left')
        self.status_label = tk.Label(status_frame, text="ONLINE", bg=T.BG_PANEL,
                                     fg=T.SUCCESS, font=T.FONT_MEDIUM)
        self.status_label.pack(side='right')
        
        self.ip_row = InfoRow(self, "PLC IP Address", "127.0.0.1")
        self.ip_row.pack(fill='x', padx=T.PADDING_MD, pady=(T.PADDING_SM, 0))
        self.rack_row = InfoRow(self, "Rack / Slot", "0 / 1")
        self.rack_row.pack(fill='x', padx=T.PADDING_MD, pady=(2, 0))
        self.time_row = InfoRow(self, "Connection Time", "00:00:00")
        self.time_row.pack(fill='x', padx=T.PADDING_MD, pady=(2, T.PADDING_MD))

    def set_status(self, online):
        """Safely toggle status without creating duplicate pulse timers."""
        # Delegate all LED logic to the indicator's set_status method
        self.status_indicator.set_status(online)
        # Update the text label accordingly
        if online:
            self.status_label.config(text="ONLINE", fg=T.SUCCESS)
        else:
            self.status_label.config(text="OFFLINE", fg=T.DANGER)

    def set_connection_time(self, seconds):
        h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
        self.time_row.set_value(f"{h:02d}:{m:02d}:{s:02d}")


class SystemStatusBar(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=T.BG_PANEL, **kwargs)
        container = tk.Frame(self, bg=T.BG_PANEL)
        container.pack(fill='x', padx=T.PADDING_MD, pady=T.PADDING_SM)
        self.temp_label = self._add_metric(container, "TEMP", "--", T.PRIMARY)
        self.cpu_label = self._add_metric(container, "CPU USAGE", "0%", T.PRIMARY)
        self.mem_label = self._add_metric(container, "MEMORY USAGE", "0%", T.PRIMARY)
        self.net_label = self._add_metric(container, "NETWORK", "0 KB/s", T.PRIMARY)
        self.uptime_label = self._add_metric(container, "UPTIME", "0s", T.TEXT_PRIMARY)

    def _add_metric(self, parent, title, value, value_color):
        frame = tk.Frame(parent, bg=T.BG_PANEL)
        frame.pack(side='left', padx=T.PADDING_SM)
        tk.Label(frame, text=title, bg=T.BG_PANEL, fg=T.TEXT_SECONDARY,
                 font=T.FONT_XS).pack(anchor='w')
        value_label = tk.Label(frame, text=value, bg=T.BG_PANEL,
                               fg=value_color, font=T.FONT_MEDIUM)
        value_label.pack(anchor='w')
        return value_label

    def update_values(self, temp=0, cpu=0, mem=0, net_up=0, net_down=0, uptime_seconds=0):
        self.temp_label.config(text=f"{temp:.2f} C")
        self.cpu_label.config(text=f"{cpu:.0f}%")
        self.mem_label.config(text=f"{mem:.0f}%")
        self.net_label.config(text=f"{net_up + net_down:.1f} KB/s")
        self.uptime_label.config(text=f"{uptime_seconds}s")