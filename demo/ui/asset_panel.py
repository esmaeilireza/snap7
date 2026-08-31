"""
Asset Panel - List of connected PLCs and sensors
Fixed: Add Asset dialog implemented, exception handling corrected,
       font fallback applied.
"""
import tkinter as tk
from tkinter import simpledialog
from .theme import IndustrialTheme as T
from .widgets import StatusIndicator


class AssetItem(tk.Frame):
    ICONS = {
        'plc': '\U0001f5a5\ufe0f',
        'temperature': '\U0001f321\ufe0f',
        'pressure': '\u26a1',
        'flow': '\U0001f4a7',
        'motor': '\u2699\ufe0f',
        'valve': '\U0001f527',
    }
    STATUS_COLORS = {
        'ONLINE': T.SUCCESS,
        'POLLING': T.PRIMARY,
        'OFFLINE': T.TEXT_DIM,
        'ALARM': T.DANGER,
    }

    def __init__(self, parent, name, ip, status, asset_type='plc', on_select=None, **kwargs):
        super().__init__(parent, bg=T.BG_PANEL, **kwargs)
        self.name = name
        self.ip = ip
        self.status = status
        self.asset_type = asset_type
        self.on_select = on_select
        self.selected = False
        self._build_ui()
        self.bind('<Button-1>', self._on_click)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)

    def _build_ui(self):
        container = tk.Frame(self, bg=T.BG_PANEL)
        container.pack(fill='x', padx=T.PADDING_SM, pady=2)

        icon_text = self.ICONS.get(self.asset_type, '\U0001f4e6')
        # FIX: Use resolved theme font instead of hardcoded 'Segoe UI'
        self.icon_label = tk.Label(
            container, text=icon_text, bg=T.BG_PANEL, font=T.FONT_LARGE,
        )
        self.icon_label.pack(side='left', padx=(0, T.PADDING_SM))
        self.icon_label.bind('<Button-1>', self._on_click)

        info_frame = tk.Frame(container, bg=T.BG_PANEL)
        info_frame.pack(side='left', fill='x', expand=True)
        info_frame.bind('<Button-1>', self._on_click)

        self.name_label = tk.Label(
            info_frame, text=self.name, bg=T.BG_PANEL, fg=T.TEXT_PRIMARY,
            font=T.FONT_NORMAL, anchor='w',
        )
        self.name_label.pack(anchor='w')
        self.name_label.bind('<Button-1>', self._on_click)

        self.ip_label = tk.Label(
            info_frame, text=self.ip, bg=T.BG_PANEL, fg=T.TEXT_MUTED,
            font=T.FONT_MONO_SMALL, anchor='w',
        )
        self.ip_label.pack(anchor='w')
        self.ip_label.bind('<Button-1>', self._on_click)

        status_color = self.STATUS_COLORS.get(self.status, T.TEXT_DIM)
        self.status_indicator = StatusIndicator(container, size=10, color=status_color)
        self.status_indicator.pack(side='right', padx=(T.PADDING_SM, 4))

        self.status_label = tk.Label(
            container, text=self.status, bg=T.BG_PANEL, fg=status_color,
            font=T.FONT_XS,
        )
        self.status_label.pack(side='right')

    def _on_click(self, event=None):
        if self.on_select:
            self.on_select(self)

    def _on_enter(self, event):
        if not self.selected:
            self.config(bg=T.BG_HOVER)
            for child in self.winfo_children():
                try:
                    child.config(bg=T.BG_HOVER)
                    for subchild in child.winfo_children():
                        subchild.config(bg=T.BG_HOVER)
                except tk.TclError:
                    pass

    def _on_leave(self, event):
        if not self.selected:
            self.config(bg=T.BG_PANEL)
            for child in self.winfo_children():
                try:
                    child.config(bg=T.BG_PANEL)
                    for subchild in child.winfo_children():
                        subchild.config(bg=T.BG_PANEL)
                except tk.TclError:
                    pass

    def set_selected(self, selected):
        self.selected = selected
        bg_color = T.PRIMARY_DARK if selected else T.BG_PANEL
        fg_color = T.PRIMARY if selected else T.TEXT_PRIMARY
        self.config(bg=bg_color)
        for child in self.winfo_children():
            try:
                child.config(bg=bg_color)
                for subchild in child.winfo_children():
                    subchild.config(bg=bg_color)
                    if isinstance(subchild, tk.Label) and subchild != self.status_label:
                        if subchild == self.name_label:
                            subchild.config(fg=fg_color)
            except tk.TclError:
                pass

    def set_status(self, status):
        self.status = status
        color = self.STATUS_COLORS.get(status, T.TEXT_DIM)
        self.status_label.config(text=status, fg=color)
        self.status_indicator.set_color(color)


class AssetPanel(tk.Frame):
    def __init__(self, parent, on_asset_select=None, **kwargs):
        super().__init__(parent, bg=T.BG_PANEL, **kwargs)
        self.on_asset_select = on_asset_select
        self.assets = {}
        self.selected_asset = None
        self._build_header()
        self._build_search()
        self._build_list()
        self._build_add_button()

    def _build_header(self):
        tk.Label(
            self, text="\U0001f3ed CONNECTED ASSETS", bg=T.BG_PANEL, fg=T.PRIMARY,
            font=T.FONT_TITLE,
        ).pack(anchor='w', padx=T.PADDING_MD, pady=(T.PADDING_MD, T.PADDING_SM))

    def _build_search(self):
        search_frame = tk.Frame(self, bg=T.BG_NAVY)
        search_frame.pack(fill='x', padx=T.PADDING_MD, pady=(0, T.PADDING_SM))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._filter_assets)
        self.placeholder = "Filter assets..."
        search_entry = tk.Entry(
            search_frame, textvariable=self.search_var, bg=T.BG_NAVY,
            fg=T.TEXT_PRIMARY, insertbackground=T.PRIMARY, relief='flat',
            font=T.FONT_SMALL,
        )
        search_entry.insert(0, self.placeholder)
        search_entry.pack(fill='x', padx=T.PADDING_SM, pady=T.PADDING_SM)

        def on_focus_in(e):
            if search_entry.get() == self.placeholder:
                search_entry.delete(0, 'end')

        def on_focus_out(e):
            if not search_entry.get():
                search_entry.insert(0, self.placeholder)

        search_entry.bind('<FocusIn>', on_focus_in)
        search_entry.bind('<FocusOut>', on_focus_out)

    def _build_list(self):
        self.list_container = tk.Frame(self, bg=T.BG_PANEL)
        self.list_container.pack(fill='both', expand=True, padx=T.PADDING_MD)
        default_assets = [
            ('PLC_01', '127.0.0.1', 'ONLINE', 'plc'),
            ('TEMP_SENSOR_01', '127.0.0.1', 'POLLING', 'temperature'),
            ('PRESS_SENSOR_01', '127.0.0.1', 'ONLINE', 'pressure'),
            ('FLOW_METER_01', '127.0.0.1', 'ONLINE', 'flow'),
            ('MOTOR_01', '127.0.0.1', 'ONLINE', 'motor'),
            ('VALVE_01', '127.0.0.1', 'OFFLINE', 'valve'),
        ]
        for name, ip, status, asset_type in default_assets:
            self.add_asset(name, ip, status, asset_type)
        if self.assets:
            self._select_asset(list(self.assets.values())[0])

    def _build_add_button(self):
        # FIX: Replaced dummy print() with actual dialog callback
        tk.Button(
            self, text="+ ADD ASSET", bg=T.PRIMARY_DARK, fg=T.PRIMARY,
            font=T.FONT_MEDIUM, relief='flat', bd=1, pady=T.PADDING_SM,
            command=self._open_add_asset_dialog,
        ).pack(fill='x', padx=T.PADDING_MD, pady=T.PADDING_MD)

    def _open_add_asset_dialog(self):
        """Open a dialog to add a new asset."""
        dialog = tk.Toplevel(self)
        dialog.title("Add New Asset")
        dialog.geometry("350x280")
        dialog.configure(bg=T.BG_PANEL)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        tk.Label(dialog, text="ADD NEW ASSET", bg=T.BG_PANEL,
                 fg=T.PRIMARY, font=T.FONT_TITLE).pack(pady=(T.PADDING_MD, T.PADDING_SM))

        form = tk.Frame(dialog, bg=T.BG_PANEL)
        form.pack(fill='x', padx=T.PADDING_MD)

        fields = {}
        field_defs = [
            ("Name:", "NEW_ASSET"),
            ("IP Address:", "127.0.0.1"),
            ("Type:", "plc"),
            ("Status:", "ONLINE"),
        ]

        for i, (label, default) in enumerate(field_defs):
            tk.Label(form, text=label, bg=T.BG_PANEL, fg=T.TEXT_SECONDARY,
                     font=T.FONT_SMALL).grid(row=i, column=0, sticky='w', pady=4)
            var = tk.StringVar(value=default)
            tk.Entry(form, textvariable=var, bg=T.BG_NAVY, fg=T.TEXT_PRIMARY,
                     insertbackground=T.PRIMARY, font=T.FONT_SMALL,
                     relief='flat').grid(row=i, column=1, sticky='ew', padx=T.PADDING_SM, pady=4)
            fields[label] = var

        form.grid_columnconfigure(1, weight=1)

        def on_submit():
            name = fields["Name:"].get().strip()
            ip = fields["IP Address:"].get().strip()
            asset_type = fields["Type:"].get().strip().lower()
            status = fields["Status:"].get().strip().upper()

            if not name:
                return
            if name in self.assets:
                tk.messagebox.showwarning("Duplicate", f"Asset '{name}' already exists.",
                                          parent=dialog)
                return

            self.add_asset(name, ip, status if status in AssetItem.STATUS_COLORS else 'ONLINE',
                           asset_type if asset_type in AssetItem.ICONS else 'plc')
            dialog.destroy()

        btn_frame = tk.Frame(dialog, bg=T.BG_PANEL)
        btn_frame.pack(fill='x', padx=T.PADDING_MD, pady=T.PADDING_MD)
        tk.Button(btn_frame, text="ADD", bg=T.PRIMARY_DARK, fg=T.PRIMARY,
                  font=T.FONT_SMALL, relief='flat', padx=20,
                  command=on_submit).pack(side='left')
        tk.Button(btn_frame, text="CANCEL", bg=T.BG_NAVY, fg=T.TEXT_SECONDARY,
                  font=T.FONT_SMALL, relief='flat', padx=20,
                  command=dialog.destroy).pack(side='right')

    def add_asset(self, name, ip, status, asset_type):
        item = AssetItem(
            self.list_container, name, ip, status, asset_type,
            on_select=self._select_asset,
        )
        item.pack(fill='x')
        self.assets[name] = item

    def _select_asset(self, asset):
        if self.selected_asset:
            self.selected_asset.set_selected(False)
        asset.set_selected(True)
        self.selected_asset = asset
        if self.on_asset_select:
            self.on_asset_select(asset)

    def _filter_assets(self, *args):
        query = self.search_var.get().lower()
        if query == self.placeholder.lower():
            query = ""
        for name, asset in self.assets.items():
            if query in name.lower() or query in asset.ip.lower():
                asset.pack(fill='x')
            else:
                asset.pack_forget()