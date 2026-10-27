"""
MetricsBar Widget — CleanShot X styled metric cards.
Features:
- Four compact Paper White cards with 20px radius and 1-px subtle borders
- Soft Charcoal uppercase micro-labels (11px/bold)
- Saturated focal accents: Electric Blue, Emerald Green, Amber, and Graphite
"""

import customtkinter as ctk
from ui.theme import THEME, _F


class MetricsBar(ctk.CTkFrame):
    """Four-card overview of scraping statistics and throughput."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self._build_ui()

    def _build_ui(self):
        self.card_msgs   = self._create_card(0, "MESSAGES",          "0",         THEME["electric_blue"])
        self.card_views  = self._create_card(1, "TOTAL VIEWS",       "0",         THEME["state_green"])
        self.card_reacts = self._create_card(2, "REACTIONS & STARS", "0",         THEME["state_amber"])
        self.card_speed  = self._create_card(3, "SPEED",             "0.0 msg/s", THEME["text_graphite"])

    def _create_card(self, col: int, title: str, initial: str, accent: str) -> ctk.CTkLabel:
        card = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=20,
            height=72,
        )
        card.grid(row=0, column=col, padx=4, sticky="ew")

        ctk.CTkLabel(
            card,
            text=title,
            font=_F(11, "bold"),
            text_color=THEME["text_body"],
        ).pack(anchor="w", padx=16, pady=(10, 0))

        val_lbl = ctk.CTkLabel(
            card,
            text=initial,
            font=_F(20, "bold"),
            text_color=accent,
        )
        val_lbl.pack(anchor="w", padx=16, pady=(0, 10))
        return val_lbl

    def update_metrics(self, msgs: int, views: int, reacts: int, speed: str):
        """Updates values across all 4 metric cards."""
        self.card_msgs.configure(text=f"{msgs:,}")
        self.card_views.configure(text=f"{views:,}")
        self.card_reacts.configure(text=f"{reacts:,}")
        self.card_speed.configure(text=speed)

    def reset(self):
        """Resets all metrics to zero."""
        self.update_metrics(0, 0, 0, "0.0 msg/s")
