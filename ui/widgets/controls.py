"""
ControlsFrame Widget — Scraping parameters and action controls.
Features:
- Paper White surface, 20px radius, 1-px card border
- Electric Capture Blue CTA start button
- White outline secondary pause and stop buttons
- Parameter controls: limit dropdown, delay slider, media toggle, clear table button
"""

from typing import Callable, Optional
import customtkinter as ctk
from tkinter import messagebox
from ui.theme import THEME, _F


class ControlsFrame(ctk.CTkFrame):
    """Configuration and action bar for executing and controlling channel scraping."""

    def __init__(
        self,
        parent,
        on_start: Optional[Callable[[str, int, float, bool], None]] = None,
        on_pause: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        on_clear: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(
            parent,
            fg_color=THEME["bg_card"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=20,
            **kwargs,
        )
        self.on_start = on_start
        self.on_pause = on_pause
        self.on_stop = on_stop
        self.on_clear = on_clear

        self._build_ui()

    def _build_ui(self):
        # ── Row 1: Channel + Action Buttons ───────────────────────────
        r1 = ctk.CTkFrame(self, fg_color="transparent")
        r1.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            r1,
            text="Channel",
            font=_F(13, "bold"),
            text_color=THEME["text_graphite"],
        ).pack(side="left", padx=(0, 10))

        self.channel_entry = ctk.CTkEntry(
            r1,
            placeholder_text="durov, @durov, https://t.me/durov …",
            height=36,
            font=_F(13),
            corner_radius=14,
            fg_color=THEME["bg_input"],
            border_width=1,
            border_color=THEME["border_input"],
            text_color=THEME["text_graphite"],
            placeholder_text_color=THEME["text_body"],
        )
        self.channel_entry.pack(side="left", fill="x", expand=True, padx=(0, 14))
        self.channel_entry.insert(0, "durov")

        # Electric Purchase Button — filled CTA
        self.start_btn = ctk.CTkButton(
            r1,
            text="▶  Start Scraping",
            font=_F(13, "bold"),
            corner_radius=14,
            fg_color=THEME["electric_blue"],
            hover_color=THEME["electric_blue_h"],
            text_color=THEME["text_white"],
            border_width=1,
            border_color=THEME["electric_blue"],
            height=36,
            width=150,
            command=self._handle_start,
        )
        self.start_btn.pack(side="left", padx=4)

        # White Outline style — Pause (idle/disabled)
        self.pause_btn = ctk.CTkButton(
            r1,
            text="⏸  Pause",
            font=_F(13, "bold"),
            corner_radius=14,
            fg_color=THEME["bg_card"],
            hover_color=THEME["bg_subcard"],
            text_color=THEME["text_body"],
            border_width=1,
            border_color=THEME["border_card"],
            height=36,
            width=100,
            state="disabled",
            command=self._handle_pause,
        )
        self.pause_btn.pack(side="left", padx=4)

        # Transparent Outline style — Stop (idle/disabled)
        self.stop_btn = ctk.CTkButton(
            r1,
            text="⏹  Stop",
            font=_F(13, "bold"),
            corner_radius=14,
            fg_color=THEME["bg_card"],
            hover_color=THEME["bg_subcard"],
            text_color=THEME["text_body"],
            border_width=1,
            border_color=THEME["border_card"],
            height=36,
            width=90,
            state="disabled",
            command=self._handle_stop,
        )
        self.stop_btn.pack(side="left", padx=4)

        # ── Row 2: Parameters ─────────────────────────────────────────
        r2 = ctk.CTkFrame(self, fg_color="transparent")
        r2.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            r2,
            text="Max messages",
            font=_F(12, "bold"),
            text_color=THEME["text_body"],
        ).pack(side="left", padx=(0, 6))

        self.limit_combo = ctk.CTkComboBox(
            r2,
            values=["50", "100", "200", "500", "1000", "All (Max)"],
            width=115,
            height=30,
            font=_F(12),
            corner_radius=14,
            fg_color=THEME["bg_input"],
            border_width=1,
            border_color=THEME["border_input"],
            text_color=THEME["text_graphite"],
            button_color=THEME["border_input"],
            button_hover_color=THEME["border_focus"],
            dropdown_fg_color=THEME["bg_card"],
            dropdown_text_color=THEME["text_graphite"],
            dropdown_hover_color=THEME["bg_subcard"],
        )
        self.limit_combo.set("100")
        self.limit_combo.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            r2,
            text="Delay",
            font=_F(12, "bold"),
            text_color=THEME["text_body"],
        ).pack(side="left", padx=(0, 6))

        self.delay_slider = ctk.CTkSlider(
            r2,
            from_=0.5,
            to=3.0,
            number_of_steps=10,
            width=130,
            height=14,
            progress_color=THEME["electric_blue"],
            button_color=THEME["electric_blue"],
            button_hover_color=THEME["electric_blue_h"],
            command=self._on_delay_change,
        )
        self.delay_slider.set(1.0)
        self.delay_slider.pack(side="left", padx=(0, 6))

        self.delay_lbl = ctk.CTkLabel(
            r2,
            text="1.0 s",
            width=44,
            font=_F(12, "bold"),
            text_color=THEME["text_graphite"],
        )
        self.delay_lbl.pack(side="left", padx=(0, 20))

        self.download_media_var = ctk.BooleanVar(value=False)
        self.media_check = ctk.CTkCheckBox(
            r2,
            text="Download media locally",
            variable=self.download_media_var,
            font=_F(12, "bold"),
            text_color=THEME["text_graphite"],
            checkmark_color=THEME["text_white"],
            fg_color=THEME["electric_blue"],
            hover_color=THEME["electric_blue_h"],
            border_color=THEME["border_input"],
        )
        self.media_check.pack(side="left", padx=10)

        # Clear — transparent outline button
        self.clear_btn = ctk.CTkButton(
            r2,
            text="Clear Table",
            width=110,
            height=30,
            font=_F(12, "bold"),
            corner_radius=14,
            fg_color=THEME["bg_card"],
            hover_color=THEME["bg_subcard"],
            text_color=THEME["text_graphite"],
            border_width=1,
            border_color=THEME["border_dark"],
            command=self._handle_clear,
        )
        self.clear_btn.pack(side="right", padx=4)

    def _on_delay_change(self, val):
        self.delay_lbl.configure(text=f"{val:.1f} s")

    def _handle_start(self):
        channel_input = self.channel_entry.get().strip()
        if not channel_input:
            messagebox.showwarning("Channel Required", "Please enter a Telegram channel handle or URL.")
            return

        limit_str = self.limit_combo.get()
        max_messages = 0 if "All" in limit_str else int(limit_str)
        delay = float(self.delay_slider.get())
        download_media = self.download_media_var.get()

        if self.on_start:
            self.on_start(channel_input, max_messages, delay, download_media)

    def _handle_pause(self):
        if self.on_pause:
            self.on_pause()

    def _handle_stop(self):
        if self.on_stop:
            self.on_stop()

    def _handle_clear(self):
        if self.on_clear:
            self.on_clear()

    def set_scraping_state(self, is_scraping: bool):
        """Switches controls between active scraping and idle states."""
        if is_scraping:
            self.start_btn.configure(
                state="disabled",
                fg_color=THEME["bg_subcard"],
                text_color=THEME["text_body"],
                border_color=THEME["border_card"],
            )
            self.pause_btn.configure(
                state="normal",
                text="⏸  Pause",
                fg_color=THEME["state_amber"],
                hover_color=THEME["state_amber_h"],
                text_color=THEME["text_white"],
                border_color=THEME["state_amber"],
            )
            self.stop_btn.configure(
                state="normal",
                fg_color=THEME["state_red"],
                hover_color=THEME["state_red_h"],
                text_color=THEME["text_white"],
                border_color=THEME["state_red"],
            )
            self.clear_btn.configure(
                state="disabled",
                fg_color=THEME["bg_subcard"],
                text_color=THEME["text_body"],
                border_color=THEME["border_card"],
            )
        else:
            self.start_btn.configure(
                state="normal",
                fg_color=THEME["electric_blue"],
                text_color=THEME["text_white"],
                border_color=THEME["electric_blue"],
            )
            self.pause_btn.configure(
                state="disabled",
                text="⏸  Pause",
                fg_color=THEME["bg_card"],
                text_color=THEME["text_body"],
                border_color=THEME["border_card"],
            )
            self.stop_btn.configure(
                state="disabled",
                fg_color=THEME["bg_card"],
                text_color=THEME["text_body"],
                border_color=THEME["border_card"],
            )
            self.clear_btn.configure(
                state="normal",
                fg_color=THEME["bg_card"],
                text_color=THEME["text_graphite"],
                border_color=THEME["border_dark"],
            )

    def set_paused_state(self, is_paused: bool):
        """Updates the pause button styling to toggle between Resume and Pause."""
        if is_paused:
            self.pause_btn.configure(
                text="▶  Resume",
                fg_color=THEME["state_green"],
                hover_color=THEME["state_green_h"],
                text_color=THEME["text_white"],
                border_color=THEME["state_green"],
            )
        else:
            self.pause_btn.configure(
                text="⏸  Pause",
                fg_color=THEME["state_amber"],
                hover_color=THEME["state_amber_h"],
                text_color=THEME["text_white"],
                border_color=THEME["state_amber"],
            )
