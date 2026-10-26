"""
Modern High-Contrast Desktop GUI for Telegram Channel Scraper using CustomTkinter.
Features enhanced contrast, zebra-striped table, live metrics,
real-time message stream, message inspector modal, filtering, and multi-format exports.
"""

import sys
import os
import threading
import asyncio
import webbrowser
import subprocess
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog

from scraper.models import TelegramMessage, ChannelMetadata, ScrapeProgress
from scraper.crawler import TelegramCrawler
from scraper.normalizer import normalize_channel_input
from scraper.exporter import export_messages
from scraper.media_downloader import MediaDownloader

# Configure default appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# High-Contrast Color Palette
THEME = {
    # Backgrounds
    "bg_window": "#080E18",        # Deep midnight background
    "bg_header": "#050B14",        # Header dark strip
    "bg_card": "#0F1A2C",          # Main panels / containers
    "bg_subcard": "#070E1A",       # Metric cards & insets
    "bg_input": "#040812",         # Form fields & entries
    
    # Borders
    "border_card": "#1E3A5F",      # Crisp container border
    "border_input": "#334E68",     # Input border
    "border_focus": "#38BDF8",     # Active accent border
    
    # Text
    "text_white": "#FFFFFF",       # 100% white for titles and primary text
    "text_silver": "#E2E8F0",      # Bright light-slate for labels and body
    "text_muted": "#CBD5E1",       # Clear silver-slate for metadata & subtitles
    "text_dim": "#64748B",         # Disabled/faint text
    
    # Accents & Badges
    "accent_cyan": "#38BDF8",      # Bright cyan (views, active links)
    "accent_green": "#10B981",     # Emerald green (start, success)
    "accent_green_hover": "#059669",
    "accent_amber": "#F59E0B",     # Warm amber (pause, speed)
    "accent_amber_hover": "#D97706",
    "accent_rose": "#FB7185",      # Coral rose (reactions)
    "accent_red": "#EF4444",       # Red (stop, errors)
    "accent_red_hover": "#DC2626",
    "accent_blue": "#0284C7",      # Sky blue (export csv, links)
    "accent_blue_hover": "#0369A1",
    "accent_purple": "#8B5CF6",    # Electric violet (export json)
    "accent_purple_hover": "#7C3AED",
    
    # Table Zebra Striping
    "table_bg": "#050B14",
    "table_row_even": "#0F1A2C",   # Slate row
    "table_row_odd": "#080F1D",    # Midnight row
    "table_row_text": "#FFFFFF",   # Crisp pure white text
    "table_header_bg": "#162842",  # Distinct deep navy header
    "table_header_fg": "#FFFFFF",  # Bold white header text
    "table_select_bg": "#0284C7",  # Bright selected row
    "table_select_fg": "#FFFFFF",
}


class MessageDetailDialog(ctk.CTkToplevel):
    """Modal popup displaying complete message details, reactions, and media."""

    def __init__(self, parent, message: TelegramMessage):
        super().__init__(parent)
        self.title(f"Message Details - @{message.channel}/{message.id}")
        self.geometry("720x660")
        self.minsize(580, 480)
        self.configure(fg_color=THEME["bg_window"])
        self.message = message

        self.transient(parent)
        self.grab_set()

        # Set dialog icon if available
        icon_path = TelegramScraperApp._resolve_asset_path("assets/icon.ico")
        if icon_path:
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header info
        header_frame = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=8,
        )
        header_frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")

        title_lbl = ctk.CTkLabel(
            header_frame,
            text=f"Post #{self.message.id} • {self.message.datetime_local}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=THEME["accent_cyan"],
        )
        title_lbl.pack(side="left", padx=14, pady=10)

        link_btn = ctk.CTkButton(
            header_frame,
            text="Open on Telegram ↗",
            width=140,
            height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=THEME["accent_blue"],
            hover_color=THEME["accent_blue_hover"],
            text_color=THEME["text_white"],
            command=lambda: webbrowser.open(self.message.url),
        )
        link_btn.pack(side="right", padx=14, pady=10)

        # Main scrollable content
        content_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=THEME["bg_subcard"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=8,
        )
        content_frame.grid(row=1, column=0, padx=16, pady=8, sticky="nsew")

        # Stats strip
        stats_box = ctk.CTkFrame(
            content_frame,
            fg_color=THEME["bg_card"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=6,
        )
        stats_box.pack(fill="x", pady=(0, 12))

        views_lbl = ctk.CTkLabel(
            stats_box,
            text=f"👁 Views: {self.message.views:,} ({self.message.views_raw})",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=THEME["text_white"],
        )
        views_lbl.pack(side="left", padx=14, pady=10)

        react_lbl = ctk.CTkLabel(
            stats_box,
            text=f"💖 Total Reactions: {self.message.total_reactions:,}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=THEME["accent_rose"],
        )
        react_lbl.pack(side="left", padx=14, pady=10)

        if self.message.paid_reactions > 0:
            stars_lbl = ctk.CTkLabel(
                stats_box,
                text=f"⭐ Stars: {self.message.paid_reactions:,}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=THEME["accent_amber"],
            )
            stars_lbl.pack(side="left", padx=14, pady=10)

        # Forwarded info
        if self.message.is_forward:
            fwd_box = ctk.CTkFrame(
                content_frame,
                fg_color="#1E293B",
                border_width=1,
                border_color=THEME["border_card"],
                corner_radius=6,
            )
            fwd_box.pack(fill="x", pady=(0, 12))
            fwd_text = f"Forwarded from: {self.message.forwarded_from_title or 'Unknown channel'}"
            ctk.CTkLabel(
                fwd_box,
                text=fwd_text,
                font=ctk.CTkFont(size=13, slant="italic"),
                text_color=THEME["text_silver"],
            ).pack(side="left", padx=14, pady=8)

        # Reactions Breakdown
        if self.message.reactions:
            r_box = ctk.CTkFrame(
                content_frame,
                fg_color=THEME["bg_card"],
                border_width=1,
                border_color=THEME["border_card"],
                corner_radius=6,
            )
            r_box.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(
                r_box,
                text="Reactions Breakdown:",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=THEME["text_muted"],
            ).pack(anchor="w", padx=14, pady=(8, 4))

            items_str = "    ".join(f"{emoji} {count:,}" for emoji, count in self.message.reactions.items())
            ctk.CTkLabel(
                r_box,
                text=items_str,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=THEME["text_white"],
            ).pack(anchor="w", padx=14, pady=(0, 10))

        # Message Text
        ctk.CTkLabel(
            content_frame,
            text="Message Text:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=THEME["text_muted"],
        ).pack(anchor="w", pady=(4, 4))

        text_box = ctk.CTkTextbox(
            content_frame,
            height=200,
            wrap="word",
            fg_color=THEME["bg_input"],
            border_width=1,
            border_color=THEME["border_card"],
            text_color=THEME["text_white"],
            font=ctk.CTkFont(size=13),
        )
        text_box.pack(fill="both", expand=True, pady=(0, 12))
        text_box.insert("1.0", self.message.text_clean or "[No text content - Media only message]")
        text_box.configure(state="disabled")

        # Media Info
        if self.message.media:
            m_box = ctk.CTkFrame(
                content_frame,
                fg_color=THEME["bg_card"],
                border_width=1,
                border_color=THEME["border_card"],
                corner_radius=6,
            )
            m_box.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(
                m_box,
                text=f"Media Attachments ({len(self.message.media)} items, Type: {self.message.media_type}):",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=THEME["text_muted"],
            ).pack(anchor="w", padx=14, pady=(8, 4))

            for m in self.message.media:
                m_line = ctk.CTkLabel(
                    m_box,
                    text=f"• [{m.media_type.upper()}] {m.url[:85]}...",
                    font=ctk.CTkFont(size=11),
                    text_color=THEME["accent_cyan"],
                )
                m_line.pack(anchor="w", padx=14, pady=3)

        # Bottom Action Bar
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=16, pady=12, sticky="ew")

        copy_text_btn = ctk.CTkButton(
            btn_frame,
            text="Copy Text",
            width=110,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=THEME["accent_blue"],
            hover_color=THEME["accent_blue_hover"],
            text_color=THEME["text_white"],
            command=self._copy_text,
        )
        copy_text_btn.pack(side="left", padx=4)

        copy_json_btn = ctk.CTkButton(
            btn_frame,
            text="Copy JSON",
            width=110,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=THEME["accent_purple"],
            hover_color=THEME["accent_purple_hover"],
            text_color=THEME["text_white"],
            command=self._copy_json,
        )
        copy_json_btn.pack(side="left", padx=4)

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Close",
            width=90,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            text_color=THEME["text_white"],
            command=self.destroy,
        )
        close_btn.pack(side="right", padx=4)

    def _copy_text(self):
        self.clipboard_clear()
        self.clipboard_append(self.message.text_clean)
        messagebox.showinfo("Copied", "Message text copied to clipboard!")

    def _copy_json(self):
        import json
        self.clipboard_clear()
        self.clipboard_append(json.dumps(self.message.to_dict(), indent=2, ensure_ascii=False))
        messagebox.showinfo("Copied", "JSON copied to clipboard!")


class TelegramScraperApp(ctk.CTk):
    """Main Application Window for Telegram Scraper with enhanced color contrast."""

    def __init__(self):
        super().__init__()

        self.title("⚡ Telegram Channel Scraper (2026 Edition)")
        self.geometry("1120x800")
        self.minsize(920, 680)
        self.configure(fg_color=THEME["bg_window"])

        # Scraper state
        self.messages: List[TelegramMessage] = []
        self.filtered_messages: List[TelegramMessage] = []
        self.channel_metadata: Optional[ChannelMetadata] = None
        self.is_scraping = False
        self.is_paused = False
        self.crawler = TelegramCrawler()

        # Threading / Async events
        self.cancel_event: Optional[asyncio.Event] = None
        self.pause_event: Optional[asyncio.Event] = None
        self.scrape_thread: Optional[threading.Thread] = None

        # Set window icon (supports development and PyInstaller onefile)
        icon_path = self._resolve_asset_path("assets/icon.ico")
        if icon_path:
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self._init_layout()

    @staticmethod
    def _resolve_asset_path(relative_path: str) -> Optional[str]:
        """Resolves resource path correctly in dev and PyInstaller onefile bundles."""
        if hasattr(sys, "_MEIPASS"):
            candidate = os.path.join(sys._MEIPASS, relative_path)
            if os.path.exists(candidate):
                return candidate
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(base_dir, relative_path)
        if os.path.exists(candidate):
            return candidate
        if os.path.exists(relative_path):
            return os.path.abspath(relative_path)
        return None

    def _init_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Table expands

        self._build_header()
        self._build_controls()
        self._build_metrics_bar()
        self._build_table_section()
        self._build_bottom_bar()

    def _build_header(self):
        header = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_header"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=0,
            height=72,
        )
        header.grid(row=0, column=0, sticky="ew")

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", padx=20, pady=12)

        main_title = ctk.CTkLabel(
            title_box,
            text="⚡ Telegram Channel Scraper",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=THEME["text_white"],
        )
        main_title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Zero-Auth • 100% Free Public Channel Data Extractor (2026 Edition)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=THEME["text_muted"],
        )
        subtitle.pack(anchor="w")

        # High-contrast status pill badge
        self.status_pill = ctk.CTkLabel(
            header,
            text="● Ready",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#34D399",
            fg_color="#064E3B",
            corner_radius=12,
            padx=16,
            pady=5,
        )
        self.status_pill.pack(side="right", padx=20, pady=18)

    def _build_controls(self):
        ctrl_frame = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=10,
        )
        ctrl_frame.grid(row=1, column=0, padx=20, pady=(12, 6), sticky="ew")

        # Row 1: Channel input & main actions
        r1 = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        r1.pack(fill="x", padx=16, pady=(12, 8))

        ctk.CTkLabel(
            r1,
            text="Channel URL or Handle:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=THEME["text_white"],
        ).pack(side="left", padx=(0, 10))

        self.channel_entry = ctk.CTkEntry(
            r1,
            placeholder_text="e.g. durov, @durov, https://t.me/durov, or t.me/s/channel",
            height=38,
            font=ctk.CTkFont(size=13),
            fg_color=THEME["bg_input"],
            border_width=1,
            border_color=THEME["border_input"],
            text_color=THEME["text_white"],
            placeholder_text_color="#829AB1",
        )
        self.channel_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.channel_entry.insert(0, "durov")

        self.start_btn = ctk.CTkButton(
            r1,
            text="▶ Start Scraping",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=THEME["accent_green"],
            hover_color=THEME["accent_green_hover"],
            text_color=THEME["text_white"],
            height=38,
            width=145,
            command=self._start_scrape,
        )
        self.start_btn.pack(side="left", padx=4)

        self.pause_btn = ctk.CTkButton(
            r1,
            text="⏸ Pause",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#1E293B",
            hover_color="#334155",
            text_color="#94A3B8",
            border_width=1,
            border_color="#334E68",
            height=38,
            width=95,
            state="disabled",
            command=self._toggle_pause,
        )
        self.pause_btn.pack(side="left", padx=4)

        self.stop_btn = ctk.CTkButton(
            r1,
            text="⏹ Stop",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#1E293B",
            hover_color="#334155",
            text_color="#94A3B8",
            border_width=1,
            border_color="#334E68",
            height=38,
            width=85,
            state="disabled",
            command=self._stop_scrape,
        )
        self.stop_btn.pack(side="left", padx=4)

        # Row 2: Parameters (Limits, Delay, Options)
        r2 = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        r2.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            r2,
            text="Max Messages:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=THEME["text_silver"],
        ).pack(side="left", padx=(0, 6))

        self.limit_combo = ctk.CTkComboBox(
            r2,
            values=["50", "100", "200", "500", "1000", "All (Max)"],
            width=115,
            height=30,
            fg_color=THEME["bg_input"],
            border_width=1,
            border_color=THEME["border_input"],
            text_color=THEME["text_white"],
            button_color="#1E3A5F",
            button_hover_color="#243B53",
            dropdown_fg_color="#0F172A",
            dropdown_text_color=THEME["text_white"],
            dropdown_hover_color="#1E3A5F",
        )
        self.limit_combo.set("100")
        self.limit_combo.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            r2,
            text="Delay (seconds):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=THEME["text_silver"],
        ).pack(side="left", padx=(0, 6))

        self.delay_slider = ctk.CTkSlider(
            r2,
            from_=0.5,
            to=3.0,
            number_of_steps=10,
            width=130,
            height=16,
            progress_color=THEME["accent_cyan"],
            button_color=THEME["accent_blue"],
            button_hover_color=THEME["accent_cyan"],
            command=self._on_delay_change,
        )
        self.delay_slider.set(1.0)
        self.delay_slider.pack(side="left", padx=(0, 6))

        self.delay_lbl = ctk.CTkLabel(
            r2,
            text="1.0s",
            width=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=THEME["text_white"],
        )
        self.delay_lbl.pack(side="left", padx=(0, 20))

        self.download_media_var = ctk.BooleanVar(value=False)
        self.media_check = ctk.CTkCheckBox(
            r2,
            text="Download media files locally",
            variable=self.download_media_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=THEME["text_white"],
            checkmark_color="#FFFFFF",
            fg_color=THEME["accent_blue"],
            border_color=THEME["border_input"],
        )
        self.media_check.pack(side="left", padx=10)

        self.clear_btn = ctk.CTkButton(
            r2,
            text="🧹 Clear Table",
            width=115,
            height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1E293B",
            hover_color="#334155",
            text_color=THEME["text_white"],
            border_width=1,
            border_color=THEME["border_input"],
            command=self._clear_results,
        )
        self.clear_btn.pack(side="right", padx=4)

    def _on_delay_change(self, val):
        self.delay_lbl.configure(text=f"{val:.1f}s")

    def _build_metrics_bar(self):
        m_frame = ctk.CTkFrame(self, fg_color="transparent")
        m_frame.grid(row=2, column=0, padx=20, pady=4, sticky="ew")
        m_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_msgs = self._create_metric_card(m_frame, 0, "MESSAGES", "0", THEME["accent_cyan"])
        self.card_views = self._create_metric_card(m_frame, 1, "TOTAL VIEWS", "0", THEME["accent_green"])
        self.card_reacts = self._create_metric_card(m_frame, 2, "REACTIONS & STARS", "0", THEME["accent_rose"])
        self.card_speed = self._create_metric_card(m_frame, 3, "SPEED", "0.0 msg/s", THEME["accent_amber"])

    def _create_metric_card(self, parent, col, title, initial_val, color):
        # High contrast card with dark inset & distinct border
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME["bg_subcard"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=8,
            height=68,
        )
        card.grid(row=0, column=col, padx=4, sticky="ew")

        t_lbl = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=THEME["text_muted"],
        )
        t_lbl.pack(anchor="w", padx=14, pady=(8, 0))

        v_lbl = ctk.CTkLabel(
            card,
            text=initial_val,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=color,
        )
        v_lbl.pack(anchor="w", padx=14, pady=(0, 8))
        return v_lbl

    def _build_table_section(self):
        table_container = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=10,
        )
        table_container.grid(row=3, column=0, padx=20, pady=6, sticky="nsew")
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(1, weight=1)

        # Search and quick filter toolbar
        filter_bar = ctk.CTkFrame(table_container, fg_color="transparent")
        filter_bar.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="ew")

        ctk.CTkLabel(
            filter_bar,
            text="Filter Results:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=THEME["text_white"],
        ).pack(side="left", padx=(0, 8))

        self.search_entry = ctk.CTkEntry(
            filter_bar,
            placeholder_text="Search text, IDs, or forward info...",
            width=280,
            height=30,
            fg_color=THEME["bg_input"],
            border_width=1,
            border_color=THEME["border_input"],
            text_color=THEME["text_white"],
            placeholder_text_color="#829AB1",
        )
        self.search_entry.pack(side="left", padx=(0, 12))
        self.search_entry.bind("<KeyRelease>", lambda e: self._apply_filter())

        self.filter_media_var = ctk.StringVar(value="All")
        self.filter_media_combo = ctk.CTkComboBox(
            filter_bar,
            values=["All", "Has Media Only", "Forwarded Only", "With Stars Only"],
            width=160,
            height=30,
            fg_color=THEME["bg_input"],
            border_width=1,
            border_color=THEME["border_input"],
            text_color=THEME["text_white"],
            button_color="#1E3A5F",
            button_hover_color="#243B53",
            dropdown_fg_color="#0F172A",
            dropdown_text_color=THEME["text_white"],
            dropdown_hover_color="#1E3A5F",
            command=lambda v: self._apply_filter(),
        )
        self.filter_media_combo.set("All")
        self.filter_media_combo.pack(side="left", padx=4)

        self.table_count_lbl = ctk.CTkLabel(
            filter_bar,
            text="Showing 0 messages",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=THEME["accent_cyan"],
        )
        self.table_count_lbl.pack(side="right", padx=6)

        # Custom styled Treeview with high-contrast styling
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=THEME["table_row_even"],
            foreground=THEME["table_row_text"],
            fieldbackground=THEME["table_bg"],
            rowheight=30,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=THEME["table_header_bg"],
            foreground=THEME["table_header_fg"],
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padding=(8, 8),
        )
        style.map(
            "Treeview",
            background=[("selected", THEME["table_select_bg"])],
            foreground=[("selected", THEME["table_select_fg"])],
        )

        columns = ("id", "date", "views", "reactions", "stars", "media", "fwd", "text")
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        # Configure zebra row striping tags for maximum contrast readability
        self.tree.tag_configure("evenrow", background=THEME["table_row_even"], foreground=THEME["table_row_text"])
        self.tree.tag_configure("oddrow", background=THEME["table_row_odd"], foreground=THEME["table_row_text"])

        self.tree.heading("id", text="ID", command=lambda: self._sort_by("id"))
        self.tree.heading("date", text="Date (Local)", command=lambda: self._sort_by("date"))
        self.tree.heading("views", text="Views", command=lambda: self._sort_by("views"))
        self.tree.heading("reactions", text="Reactions", command=lambda: self._sort_by("reactions"))
        self.tree.heading("stars", text="⭐ Stars", command=lambda: self._sort_by("stars"))
        self.tree.heading("media", text="Media")
        self.tree.heading("fwd", text="Forwarded")
        self.tree.heading("text", text="Message Text Snippet")

        self.tree.column("id", width=65, anchor="center")
        self.tree.column("date", width=145, anchor="center")
        self.tree.column("views", width=90, anchor="e")
        self.tree.column("reactions", width=95, anchor="e")
        self.tree.column("stars", width=80, anchor="e")
        self.tree.column("media", width=80, anchor="center")
        self.tree.column("fwd", width=110, anchor="w")
        self.tree.column("text", width=360, anchor="w")

        # Scrollbars
        v_scroll = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=1, column=0, sticky="nsew", padx=(12, 0), pady=(0, 6))
        v_scroll.grid(row=1, column=1, sticky="ns", padx=(0, 12), pady=(0, 6))
        h_scroll.grid(row=2, column=0, sticky="ew", padx=(12, 0), pady=(0, 8))

        # Double-click to inspect
        self.tree.bind("<Double-1>", self._on_row_double_click)

    def _build_bottom_bar(self):
        bottom = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_header"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=0,
            height=65,
        )
        bottom.grid(row=4, column=0, sticky="ew")

        # Progress bar & status
        p_box = ctk.CTkFrame(bottom, fg_color="transparent")
        p_box.pack(side="left", fill="x", expand=True, padx=20, pady=10)

        self.progress_bar = ctk.CTkProgressBar(p_box, height=10, progress_color=THEME["accent_cyan"])
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(2, 4))

        self.progress_status_lbl = ctk.CTkLabel(
            p_box,
            text="Double-click any message row to view full text and media.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=THEME["text_muted"],
        )
        self.progress_status_lbl.pack(anchor="w")

        # Export buttons with bold, high-contrast text and vibrant accents
        export_box = ctk.CTkFrame(bottom, fg_color="transparent")
        export_box.pack(side="right", padx=20, pady=10)

        self.btn_csv = ctk.CTkButton(
            export_box,
            text="📄 Export CSV",
            width=115,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=THEME["accent_blue"],
            hover_color=THEME["accent_blue_hover"],
            text_color=THEME["text_white"],
            command=lambda: self._export_data("csv"),
        )
        self.btn_csv.pack(side="left", padx=4)

        self.btn_excel = ctk.CTkButton(
            export_box,
            text="📊 Export Excel",
            width=120,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=THEME["accent_green"],
            hover_color=THEME["accent_green_hover"],
            text_color=THEME["text_white"],
            command=lambda: self._export_data("xlsx"),
        )
        self.btn_excel.pack(side="left", padx=4)

        self.btn_json = ctk.CTkButton(
            export_box,
            text="💾 Export JSON",
            width=115,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=THEME["accent_purple"],
            hover_color=THEME["accent_purple_hover"],
            text_color=THEME["text_white"],
            command=lambda: self._export_data("json"),
        )
        self.btn_json.pack(side="left", padx=4)

        self.btn_folder = ctk.CTkButton(
            export_box,
            text="📁 Output Folder",
            width=125,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1E293B",
            hover_color="#334155",
            text_color=THEME["text_white"],
            border_width=1,
            border_color="#475569",
            command=self._open_output_folder,
        )
        self.btn_folder.pack(side="left", padx=4)

    def _set_status_badge(self, text: str, status_type: str = "ready"):
        """Updates the status pill badge with high-contrast colors."""
        badge_configs = {
            "ready": {"fg": "#064E3B", "text": "#34D399"},
            "scraping": {"fg": "#0C4A6E", "text": "#38BDF8"},
            "completed": {"fg": "#064E3B", "text": "#34D399"},
            "paused": {"fg": "#78350F", "text": "#FBBF24"},
            "failed": {"fg": "#7F1D1D", "text": "#F87171"},
        }
        cfg = badge_configs.get(status_type, badge_configs["ready"])
        self.status_pill.configure(
            text=f"● {text}",
            fg_color=cfg["fg"],
            text_color=cfg["text"],
        )

    # -------------------------------------------------------------
    # Scraping Logic & Threading
    # -------------------------------------------------------------

    def _start_scrape(self):
        channel_input = self.channel_entry.get().strip()
        if not channel_input:
            messagebox.showwarning("Channel Required", "Please enter a Telegram channel handle or URL.")
            return

        limit_str = self.limit_combo.get()
        max_messages = 0 if "All" in limit_str else int(limit_str)

        delay = float(self.delay_slider.get())
        download_media = self.download_media_var.get()

        # Update UI state with high-contrast active buttons
        self.is_scraping = True
        self.is_paused = False
        self.start_btn.configure(state="disabled", fg_color="#1E293B", text_color="#64748B")
        self.pause_btn.configure(
            state="normal",
            text="⏸ Pause",
            fg_color=THEME["accent_amber"],
            hover_color=THEME["accent_amber_hover"],
            text_color=THEME["text_white"],
            border_color=THEME["accent_amber"],
        )
        self.stop_btn.configure(
            state="normal",
            fg_color=THEME["accent_red"],
            hover_color=THEME["accent_red_hover"],
            text_color=THEME["text_white"],
            border_color=THEME["accent_red"],
        )
        self._set_status_badge("Scraping...", "scraping")
        self.progress_bar.set(0)

        # Clear existing if scraping new channel
        clean_channel, _ = normalize_channel_input(channel_input)
        if not self.messages or (self.messages and self.messages[0].channel != clean_channel):
            self._clear_results()

        # Spawn background scraping thread
        self.scrape_thread = threading.Thread(
            target=self._run_crawler_thread,
            args=(channel_input, max_messages, delay, download_media),
            daemon=True,
        )
        self.scrape_thread.start()

    def _run_crawler_thread(
        self,
        channel_input: str,
        max_messages: int,
        delay: float,
        download_media: bool,
    ):
        """Runs the async crawler in a separate background event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        self.cancel_event = asyncio.Event()
        self.pause_event = asyncio.Event()

        crawler = TelegramCrawler(base_delay=delay)

        def on_progress(prog: ScrapeProgress, new_batch: List[TelegramMessage]):
            self.after(0, self._update_progress_ui, prog, new_batch)

        try:
            metadata, msgs = loop.run_until_complete(
                crawler.scrape_channel(
                    channel_input=channel_input,
                    max_messages=max_messages,
                    progress_callback=on_progress,
                    cancel_event=self.cancel_event,
                    pause_event=self.pause_event,
                )
            )
            self.channel_metadata = metadata

            # Media download if requested
            if download_media and msgs:
                self.after(0, lambda: self.progress_status_lbl.configure(text="Downloading media files..."))
                downloader = MediaDownloader()
                loop.run_until_complete(
                    downloader.download_message_media(msgs, metadata.username)
                )

            self.after(0, self._on_scrape_finished, None)

        except Exception as e:
            self.after(0, self._on_scrape_finished, e)
        finally:
            loop.close()

    def _update_progress_ui(self, prog: ScrapeProgress, new_batch: List[TelegramMessage]):
        self.card_msgs.configure(text=f"{prog.scraped_count:,}")
        self.card_speed.configure(text=f"{prog.messages_per_sec} msg/s")
        self.progress_status_lbl.configure(text=f"Status: {prog.status}")

        if prog.target_count and prog.target_count > 0:
            pct = min(1.0, prog.scraped_count / prog.target_count)
            self.progress_bar.set(pct)
        else:
            self.progress_bar.step()

        # Add new messages to memory and table with zebra striping
        if new_batch:
            for msg in new_batch:
                self.messages.append(msg)
                row_tag = "evenrow" if len(self.messages) % 2 == 0 else "oddrow"
                self._insert_table_row(msg, tag=row_tag)

            tot_views = sum(m.views for m in self.messages)
            tot_react = sum(m.total_reactions for m in self.messages)
            self.card_views.configure(text=f"{tot_views:,}")
            self.card_reacts.configure(text=f"{tot_react:,}")

            self.table_count_lbl.configure(text=f"Showing {len(self.messages):,} messages")

    def _insert_table_row(self, msg: TelegramMessage, tag: str = "evenrow"):
        # Format text snippet
        clean_text = msg.text_clean.replace("\n", " ").strip()
        snippet = (clean_text[:65] + "...") if len(clean_text) > 65 else clean_text
        if not snippet and msg.media:
            snippet = f"[{msg.media_type or 'Media'} attachment]"

        # Format reactions
        react_preview = f"{msg.total_reactions:,}" if msg.total_reactions > 0 else "-"
        stars_str = f"{msg.paid_reactions:,}" if msg.paid_reactions > 0 else "-"
        fwd_str = (msg.forwarded_from_title[:15] + "...") if msg.forwarded_from_title else "-"

        self.tree.insert(
            "",
            "end",
            iid=str(msg.id),
            tags=(tag,),
            values=(
                msg.id,
                msg.datetime_local,
                f"{msg.views:,}" if msg.views else "-",
                react_preview,
                stars_str,
                msg.media_type or "-",
                fwd_str,
                snippet,
            ),
        )

    def _on_scrape_finished(self, error: Optional[Exception]):
        self.is_scraping = False
        self.is_paused = False
        self.start_btn.configure(
            state="normal",
            fg_color=THEME["accent_green"],
            text_color=THEME["text_white"],
        )
        self.pause_btn.configure(
            state="disabled",
            text="⏸ Pause",
            fg_color="#1E293B",
            text_color="#94A3B8",
            border_color="#334E68",
        )
        self.stop_btn.configure(
            state="disabled",
            fg_color="#1E293B",
            text_color="#94A3B8",
            border_color="#334E68",
        )

        if error:
            self._set_status_badge("Failed", "failed")
            self.progress_status_lbl.configure(text=f"Error: {error}")
            messagebox.showerror("Scraping Error", f"An error occurred while scraping:\n\n{error}")
        else:
            self._set_status_badge("Completed", "completed")
            self.progress_bar.set(1.0)
            self.progress_status_lbl.configure(
                text=f"Finished! Successfully collected {len(self.messages):,} messages."
            )

    def _toggle_pause(self):
        if not self.is_scraping or not self.pause_event:
            return

        if not self.is_paused:
            self.pause_event.set()
            self.is_paused = True
            self.pause_btn.configure(
                text="▶ Resume",
                fg_color=THEME["accent_green"],
                hover_color=THEME["accent_green_hover"],
            )
            self._set_status_badge("Paused", "paused")
        else:
            self.pause_event.clear()
            self.is_paused = False
            self.pause_btn.configure(
                text="⏸ Pause",
                fg_color=THEME["accent_amber"],
                hover_color=THEME["accent_amber_hover"],
            )
            self._set_status_badge("Scraping...", "scraping")

    def _stop_scrape(self):
        if self.cancel_event:
            self.cancel_event.set()
        if self.pause_event and self.is_paused:
            self.pause_event.clear()
        self.progress_status_lbl.configure(text="Stopping scraper...")

    def _clear_results(self):
        self.messages.clear()
        self.filtered_messages.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.card_msgs.configure(text="0")
        self.card_views.configure(text="0")
        self.card_reacts.configure(text="0")
        self.card_speed.configure(text="0.0 msg/s")
        self.table_count_lbl.configure(text="Showing 0 messages")
        self.progress_bar.set(0)
        self._set_status_badge("Ready", "ready")

    # -------------------------------------------------------------
    # Table Interactivity & Filtering
    # -------------------------------------------------------------

    def _on_row_double_click(self, event):
        item_id = self.tree.focus()
        if not item_id:
            return

        msg = next((m for m in self.messages if str(m.id) == item_id), None)
        if msg:
            MessageDetailDialog(self, msg)

    def _apply_filter(self):
        query = self.search_entry.get().lower().strip()
        media_filter = self.filter_media_combo.get()

        for item in self.tree.get_children():
            self.tree.delete(item)

        matched = 0
        for msg in self.messages:
            # Query match
            text_match = (
                not query
                or query in str(msg.id)
                or query in msg.text_clean.lower()
                or (msg.forwarded_from_title and query in msg.forwarded_from_title.lower())
            )

            # Dropdown match
            type_match = True
            if media_filter == "Has Media Only":
                type_match = bool(msg.media)
            elif media_filter == "Forwarded Only":
                type_match = msg.is_forward
            elif media_filter == "With Stars Only":
                type_match = msg.paid_reactions > 0

            if text_match and type_match:
                row_tag = "evenrow" if matched % 2 == 0 else "oddrow"
                self._insert_table_row(msg, tag=row_tag)
                matched += 1

        self.table_count_lbl.configure(text=f"Showing {matched:,} of {len(self.messages):,} messages")

    def _sort_by(self, col):
        if not self.messages:
            return
        if col == "id":
            self.messages.sort(key=lambda m: m.id, reverse=True)
        elif col == "date":
            self.messages.sort(key=lambda m: m.datetime_iso, reverse=True)
        elif col == "views":
            self.messages.sort(key=lambda m: m.views, reverse=True)
        elif col == "reactions":
            self.messages.sort(key=lambda m: m.total_reactions, reverse=True)
        elif col == "stars":
            self.messages.sort(key=lambda m: m.paid_reactions, reverse=True)

        self._apply_filter()

    # -------------------------------------------------------------
    # Exports & Directory Management
    # -------------------------------------------------------------

    def _export_data(self, fmt: str):
        if not self.messages:
            messagebox.showinfo("No Data", "There are no scraped messages to export. Scrape a channel first!")
            return

        channel = self.messages[0].channel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"{channel}_{timestamp}.{fmt}"

        file_types = {
            "csv": [("CSV Files", "*.csv")],
            "xlsx": [("Excel Files", "*.xlsx")],
            "json": [("JSON Files", "*.json")],
        }

        dest_file = filedialog.asksaveasfilename(
            title=f"Export as {fmt.upper()}",
            initialdir=os.path.abspath("exports"),
            initialfile=default_name,
            filetypes=file_types.get(fmt, [("All Files", "*.*")]),
            defaultextension=f".{fmt}",
        )

        if not dest_file:
            return

        try:
            saved_path = export_messages(
                messages=self.messages,
                export_format=fmt,
                output_path=dest_file,
                channel_metadata=self.channel_metadata,
            )
            messagebox.showinfo("Export Successful", f"Saved {len(self.messages):,} messages to:\n{saved_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export messages:\n{e}")

    def _open_output_folder(self):
        folder = os.path.abspath("exports")
        os.makedirs(folder, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(folder)
        else:
            subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", folder])


def launch_desktop_app():
    """Starts the CustomTkinter desktop GUI."""
    app = TelegramScraperApp()
    app.mainloop()


if __name__ == "__main__":
    launch_desktop_app()
