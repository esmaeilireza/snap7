import tkinter as tk

from .theme import IndustrialTheme as T


class StatusIndicator(tk.Canvas):
    """Glowing status LED with safe, non‑exploding pulse animation."""

    def __init__(self, parent, size=12, color=T.SUCCESS, **kwargs):
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=T.BG_PANEL,
            highlightthickness=0,
            **kwargs,
        )
        self.size = size
        self.color = color
        self._pulsing = False  # kept for compatibility
        self._pulse_job = None  # pending after() id
        self._pulse_on = False  # current pulse phase
        self._last_status = None  # True = online, False = offline, None = unknown

        # Create persistent canvas items
        self._dot_id = self.create_oval(
            1, 1, self.size - 1, self.size - 1, fill=self.color, outline=self.color
        )
        self._highlight_id = self.create_oval(
            self.size // 4,
            self.size // 4,
            self.size // 4 + self.size // 3,
            self.size // 4 + self.size // 3,
            fill="white",
            outline="",
            stipple="gray25",
        )

    def _draw(self, dim=False):
        fill = self.color if not dim else T.BG_HOVER
        self.itemconfig(self._dot_id, fill=fill, outline=fill)

    def set_color(self, color):
        self.color = color
        self._draw()

    def set_status(self, active: bool):
        """Set the LED state: True = online (pulsing), False = offline (solid danger)."""
        # Only act if the status actually changed
        if active == self._last_status:
            return  # no change → do nothing
        self._last_status = active
        self.stop_pulse()  # kill any existing pulse chain
        if active:
            self.start_pulse()
        else:
            self.color = T.DANGER  # set color for offline
            self._draw(dim=False)  # solid colour, no dimming

    def start_pulse(self):
        """Start pulsing if not already pulsing."""
        if self._pulse_job is not None:
            return  # already pulsing
        self._pulse_on = False  # start with 'off' phase
        self._pulse_step()

    def _pulse_step(self):
        self._pulse_on = not self._pulse_on
        self._draw(dim=not self._pulse_on)  # dim when off, bright when on
        self._pulse_job = self.after(600, self._pulse_step)

    def stop_pulse(self):
        """Cancel any pending pulse and turn the LED bright (solid)."""
        if self._pulse_job is not None:
            self.after_cancel(self._pulse_job)
            self._pulse_job = None
        self._draw(dim=False)  # return to full brightness

    def destroy(self):
        self.stop_pulse()  # prevent callbacks on a dead widget
        super().destroy()


class Badge(tk.Canvas):
    def __init__(self, parent, text="0", color=T.DANGER, size=20, **kwargs):
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=T.BG_DARK,
            highlightthickness=0,
            **kwargs,
        )
        self.text = text
        self.color = color
        self.size = size
        self._draw()

    def _draw(self):
        self.delete("all")
        self.create_oval(1, 1, self.size - 1, self.size - 1, fill=self.color, outline="")
        self.create_text(
            self.size // 2,
            self.size // 2,
            text=str(self.text),
            fill="white",
            font=("Tahoma", 9, "bold"),
        )


class MetricDisplay(tk.Frame):
    def __init__(
        self,
        parent,
        title="Metric",
        value="--",
        unit="",
        value_color=T.PRIMARY,
        **kwargs,
    ):
        super().__init__(parent, bg=T.BG_PANEL, **kwargs)
        tk.Label(self, text=title.upper(), bg=T.BG_PANEL, fg=T.TEXT_SECONDARY, font=T.FONT_XS).pack(
            anchor="w"
        )
        value_frame = tk.Frame(self, bg=T.BG_PANEL)
        value_frame.pack(anchor="w", pady=(2, 0))
        self.value_label = tk.Label(
            value_frame, text=str(value), bg=T.BG_PANEL, fg=value_color, font=T.FONT_XXL
        )
        self.value_label.pack(side="left")
        if unit:
            tk.Label(
                value_frame,
                text=unit,
                bg=T.BG_PANEL,
                fg=T.TEXT_SECONDARY,
                font=T.FONT_LARGE,
            ).pack(side="left", padx=(4, 0), pady=(14, 0))

    def set_value(self, value):
        self.value_label.config(text=str(value))


class InfoRow(tk.Frame):
    """A row with a label on the left and a value on the right."""

    def __init__(self, parent, label, value, value_color=None, **kwargs):
        super().__init__(parent, bg=T.BG_PANEL, **kwargs)

        self.label_widget = tk.Label(
            self,
            text=label,
            bg=T.BG_PANEL,
            fg=T.TEXT_SECONDARY,
            font=T.FONT_SMALL,
            anchor="w",
        )
        # InfoRow grid layout: label ثابت، value کشسان و بدون هم‌پوشانی
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.label_widget.grid(row=0, column=0, sticky="w", padx=(0, 8))

        # FIX: Use monospaced font and right alignment to prevent clipping
        color = value_color if value_color else T.TEXT_PRIMARY
        self.value_widget = tk.Label(
            self,
            text=str(value),
            bg=T.BG_PANEL,
            fg=color,
            font=T.FONT_MONO_SMALL,
            anchor="e",
        )
        self.value_widget.grid(row=0, column=1, sticky="ew")

    def set_value(self, value):
        self.value_widget.config(text=str(value))
