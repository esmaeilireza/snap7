"""
Communication Log Widget
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from .theme import IndustrialTheme as T

class LogWidget(tk.Frame):
    LEVEL_COLORS = {
        'INFO': T.SUCCESS, 'DEBUG': T.PRIMARY, 
        'WARNING': T.WARNING, 'ERROR': T.DANGER,
    }
    # Maximum number of rows to keep (prevents memory bloat and rendering slowdowns)
    MAX_ROWS = 500

    def __init__(self, parent, max_entries=50, **kwargs):
        super().__init__(parent, bg=T.BG_PANEL, **kwargs)
        # max_entries is kept for backward compatibility but we use MAX_ROWS for the tree.
        self.max_entries = max_entries
        self._build_header()
        self._build_table()

    def _build_header(self):
        header = tk.Frame(self, bg=T.BG_PANEL)
        header.pack(fill='x', padx=T.PADDING_MD, pady=(T.PADDING_MD, T.PADDING_SM))
        tk.Label(header, text="📋 COMMUNICATION LOG", bg=T.BG_PANEL, fg=T.TEXT_PRIMARY, 
                font=T.FONT_TITLE).pack(side='left')
        tk.Button(header, text="🗑 CLEAR", bg=T.DANGER_BG, fg=T.DANGER,
                 font=T.FONT_SMALL, relief='flat', bd=0, padx=12, pady=4,
                 command=self.clear).pack(side='right')

    def _build_table(self):
        container = tk.Frame(self, bg=T.BORDER)
        container.pack(fill='both', expand=True, padx=T.PADDING_MD, pady=T.PADDING_SM)

        columns = ('time', 'level', 'source', 'message')
        self.tree = ttk.Treeview(container, columns=columns, show='headings', 
                                style='Log.Treeview', height=8)

        self.tree.heading('time', text='TIME')
        self.tree.heading('level', text='LEVEL')
        self.tree.heading('source', text='SOURCE')
        self.tree.heading('message', text='MESSAGE')

        self.tree.column('time', width=100, anchor='w')
        self.tree.column('level', width=70, anchor='center')
        self.tree.column('source', width=140, anchor='w')
        self.tree.column('message', width=400, anchor='w')

        scrollbar = ttk.Scrollbar(container, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        for level, color in self.LEVEL_COLORS.items():
            self.tree.tag_configure(level.lower(), foreground=color)

    def add_entry(self, level, source, message, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()
        time_str = timestamp.strftime('%H:%M:%S.%f')[:-3]
        # Insert at the top (index 0) – newest first
        self.tree.insert('', 0, values=(time_str, level, source, message), 
                         tags=(level.lower(),))

        # Enforce row limit: remove oldest rows from the bottom
        children = self.tree.get_children()
        while len(children) > self.MAX_ROWS:
            # The oldest is the last child (since we insert at top, index increases downward)
            self.tree.delete(children[-1])
            children = children[:-1]  # update list to avoid re-fetching

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)