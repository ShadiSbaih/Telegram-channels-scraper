"""
Design Tokens & Font Helpers for Telegram Channel Scraper.
Follows the GazandoTD / CleanShot X light-mode style specifications.
"""

from typing import Dict
import customtkinter as ctk

# ── Appearance Mode ────────────────────────────────────────────────────────
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

# ── Design Tokens ──────────────────────────────────────────────────────────
THEME: Dict[str, str] = {
    # Surfaces
    "bg_window":        "#ffffff",   # Paper White — page background
    "bg_header":        "#ffffff",   # Paper White — nav / header strip
    "bg_card":          "#ffffff",   # Lifted White — card surface
    "bg_subcard":       "#f8f8f9",   # Slightly off-white inset
    "bg_input":         "#ffffff",   # Input field background
    "bg_studio":        "#0f0f12",   # Studio Black — dark bands / badges

    # Borders
    "border_card":      "#e8e8ea",   # Subtle 1-px outline on cards
    "border_input":     "#d0d0d3",   # Input border
    "border_focus":     "#0d44e8",   # Electric Capture Blue focus ring
    "border_dark":      "#161618",   # Graphite outline (nav buttons)

    # Text
    "text_display":     "#000000",   # Absolute Ink — hero / section headings
    "text_graphite":    "#161618",   # Graphite — nav labels, card body
    "text_body":        "#6a6a6b",   # Soft Charcoal — descriptions / metadata
    "text_white":       "#ffffff",   # Paper White text on dark surfaces
    "text_badge":       "#ffffff",   # Badge text on Studio Black

    # Primary action
    "electric_blue":    "#0d44e8",   # Electric Capture Blue — CTA fills
    "electric_blue_h":  "#0b38c5",   # Slightly darker hover

    # Functional state colours
    "state_green":      "#059669",
    "state_green_h":    "#047857",
    "state_amber":      "#d97706",
    "state_amber_h":    "#b45309",
    "state_red":        "#dc2626",
    "state_red_h":      "#b91c1c",

    # Table
    "table_bg":         "#ffffff",
    "table_row_even":   "#ffffff",
    "table_row_odd":    "#f8f8f9",
    "table_text":       "#161618",   # Graphite row text
    "table_header_bg":  "#f0f0f2",
    "table_header_fg":  "#161618",
    "table_select_bg":  "#0d44e8",
    "table_select_fg":  "#ffffff",
}


# ── Font helper ────────────────────────────────────────────────────────────
def _F(size: int, weight: str = "normal") -> ctk.CTkFont:
    """Return a CTkFont with Inter (CleanShot X / Mac system sans-serif)."""
    return ctk.CTkFont(family="Inter", size=size, weight=weight)
