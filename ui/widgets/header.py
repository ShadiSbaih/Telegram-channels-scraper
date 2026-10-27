"""
HeaderBar Widget — GazandoTD CleanShot X styled top navigation bar.
Features:
- Paper White background with 1-px subtle bottom divider
- Compact Graphite wordmark (20px/bold) & Soft Charcoal metadata (12px)
- Studio Black status badge with functional state text tints
"""

from typing import Dict
import customtkinter as ctk
from ui.theme import THEME, _F


class HeaderBar(ctk.CTkFrame):
    """Top navigation and title header bar with live status badge."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=THEME["bg_header"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=0,
            height=68,
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self):
        title_box = ctk.CTkFrame(self, fg_color="transparent")
        title_box.pack(side="left", padx=24, pady=10)

        ctk.CTkLabel(
            title_box,
            text="Telegram Channel Scraper",
            font=_F(20, "bold"),
            text_color=THEME["text_graphite"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Zero-Auth · 100% Free Public Channel Data Extractor (2026 Edition)",
            font=_F(12),
            text_color=THEME["text_body"],
        ).pack(anchor="w")

    def set_status(self, text: str, status_type: str = "ready"):
        """No-op retained for backward compatibility."""
        pass
