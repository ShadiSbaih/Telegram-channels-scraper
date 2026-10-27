"""
FooterBar Widget — CleanShot X styled footer strip.
Features:
- Paper White background with 1-px subtle top divider
- Electric Blue progress bar with Soft Charcoal status label
- White outline secondary export buttons (14px radius, 1-px Graphite outline)
"""

from typing import Callable, Optional
import customtkinter as ctk
from ui.theme import THEME, _F


class FooterBar(ctk.CTkFrame):
    """Footer bar holding progress indicator and export action controls."""

    def __init__(
        self,
        parent,
        on_export: Optional[Callable[[str], None]] = None,
        on_open_folder: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(
            parent,
            fg_color=THEME["bg_header"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=0,
            height=64,
            **kwargs,
        )
        self.on_export = on_export
        self.on_open_folder = on_open_folder

        self._build_ui()

    def _build_ui(self):
        # ── Progress + Status ─────────────────────────────────────────
        p_box = ctk.CTkFrame(self, fg_color="transparent")
        p_box.pack(side="left", fill="x", expand=True, padx=24, pady=10)

        self.progress_bar = ctk.CTkProgressBar(
            p_box,
            height=6,
            corner_radius=3,
            progress_color=THEME["electric_blue"],
            fg_color=THEME["border_card"],
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(2, 4))

        self.progress_status_lbl = ctk.CTkLabel(
            p_box,
            text="Double-click any row to inspect the full message.",
            font=_F(12),
            text_color=THEME["text_body"],
        )
        self.progress_status_lbl.pack(anchor="w")

        # ── Export buttons — White Outline style ──────────────────────
        export_box = ctk.CTkFrame(self, fg_color="transparent")
        export_box.pack(side="right", padx=24, pady=10)

        def _obtn(label: str, cmd: Callable):
            return ctk.CTkButton(
                export_box,
                text=label,
                width=118,
                height=34,
                font=_F(12, "bold"),
                corner_radius=14,
                fg_color=THEME["bg_card"],
                hover_color=THEME["bg_subcard"],
                text_color=THEME["text_graphite"],
                border_width=1,
                border_color=THEME["border_dark"],
                command=cmd,
            )

        self.btn_csv    = _obtn("Export CSV",    lambda: self._handle_export("csv"))
        self.btn_excel  = _obtn("Export Excel",  lambda: self._handle_export("xlsx"))
        self.btn_json   = _obtn("Export JSON",   lambda: self._handle_export("json"))
        self.btn_folder = _obtn("Output Folder", self._handle_open_folder)

        self.btn_csv.pack(side="left", padx=4)
        self.btn_excel.pack(side="left", padx=4)
        self.btn_json.pack(side="left", padx=4)
        self.btn_folder.pack(side="left", padx=4)

    def _handle_export(self, fmt: str):
        if self.on_export:
            self.on_export(fmt)

    def _handle_open_folder(self):
        if self.on_open_folder:
            self.on_open_folder()

    def set_progress(self, pct: float):
        """Sets the progress bar ratio between 0.0 and 1.0."""
        self.progress_bar.set(min(1.0, max(0.0, pct)))

    def step_progress(self):
        """Steps progress bar in indeterminate fashion."""
        self.progress_bar.step()

    def set_status(self, text: str):
        """Updates the status description text."""
        self.progress_status_lbl.configure(text=text)
