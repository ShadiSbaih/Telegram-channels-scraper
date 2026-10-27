"""
Message Detail Modal Dialog.
Presents complete details for an individual scraped message:
text, reactions breakdown, stars, media preview URLs, copy actions, and web link.
"""

import sys
import os
import json
import webbrowser
from typing import Optional
from tkinter import messagebox

import customtkinter as ctk

from scraper.models import TelegramMessage
from ui.theme import THEME, _F


class MessageDetailDialog(ctk.CTkToplevel):
    """Modal showing complete message details, reactions, and media."""

    def __init__(self, parent, message: TelegramMessage, icon_path: Optional[str] = None):
        super().__init__(parent)
        self.title(f"Message Details — @{message.channel}/{message.id}")
        self.geometry("720x660")
        self.minsize(580, 480)
        self.configure(fg_color=THEME["bg_window"])
        self.message = message

        self.transient(parent)
        self.grab_set()

        if icon_path and os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Header bar ────────────────────────────────────────────────
        header = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=14,
        )
        header.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")

        ctk.CTkLabel(
            header,
            text=f"Post #{self.message.id}  ·  {self.message.datetime_local}",
            font=_F(15, "bold"),
            text_color=THEME["text_graphite"],
        ).pack(side="left", padx=16, pady=12)

        ctk.CTkButton(
            header,
            text="Open on Telegram ↗",
            width=148,
            height=32,
            font=_F(13, "bold"),
            corner_radius=14,
            fg_color=THEME["electric_blue"],
            hover_color=THEME["electric_blue_h"],
            text_color=THEME["text_white"],
            border_width=1,
            border_color=THEME["electric_blue"],
            command=lambda: webbrowser.open(self.message.url),
        ).pack(side="right", padx=16, pady=12)

        # ── Scrollable content ────────────────────────────────────────
        content = ctk.CTkScrollableFrame(
            self,
            fg_color=THEME["bg_subcard"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=14,
        )
        content.grid(row=1, column=0, padx=16, pady=8, sticky="nsew")

        # Stats strip
        stats = ctk.CTkFrame(
            content,
            fg_color=THEME["bg_card"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=12,
        )
        stats.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            stats,
            text=f"👁  {self.message.views:,} views",
            font=_F(13, "bold"),
            text_color=THEME["text_graphite"],
        ).pack(side="left", padx=16, pady=10)

        ctk.CTkLabel(
            stats,
            text=f"💖  {self.message.total_reactions:,} reactions",
            font=_F(13, "bold"),
            text_color=THEME["text_body"],
        ).pack(side="left", padx=12, pady=10)

        if self.message.paid_reactions > 0:
            ctk.CTkLabel(
                stats,
                text=f"⭐  {self.message.paid_reactions:,} stars",
                font=_F(13, "bold"),
                text_color=THEME["state_amber"],
            ).pack(side="left", padx=12, pady=10)

        # Forwarded info
        if self.message.is_forward:
            fwd = ctk.CTkFrame(
                content,
                fg_color=THEME["bg_card"],
                border_width=1,
                border_color=THEME["border_card"],
                corner_radius=12,
            )
            fwd.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(
                fwd,
                text=f"↩  Forwarded from: {self.message.forwarded_from_title or 'Unknown'}",
                font=_F(13),
                text_color=THEME["text_body"],
            ).pack(side="left", padx=16, pady=8)

        # Reactions breakdown
        if self.message.reactions:
            r_box = ctk.CTkFrame(
                content,
                fg_color=THEME["bg_card"],
                border_width=1,
                border_color=THEME["border_card"],
                corner_radius=12,
            )
            r_box.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(
                r_box,
                text="Reactions breakdown",
                font=_F(12, "bold"),
                text_color=THEME["text_body"],
            ).pack(anchor="w", padx=16, pady=(10, 4))
            items_str = "    ".join(f"{emoji} {count:,}" for emoji, count in self.message.reactions.items())
            ctk.CTkLabel(
                r_box,
                text=items_str,
                font=_F(14, "bold"),
                text_color=THEME["text_graphite"],
            ).pack(anchor="w", padx=16, pady=(0, 10))

        # Message text
        ctk.CTkLabel(
            content,
            text="Message text",
            font=_F(13, "bold"),
            text_color=THEME["text_body"],
        ).pack(anchor="w", pady=(4, 4))

        text_box = ctk.CTkTextbox(
            content,
            height=200,
            wrap="word",
            fg_color=THEME["bg_card"],
            border_width=1,
            border_color=THEME["border_card"],
            corner_radius=12,
            text_color=THEME["text_graphite"],
            font=_F(13),
        )
        text_box.pack(fill="both", expand=True, pady=(0, 12))
        text_box.insert("1.0", self.message.text_clean or "[No text content — media-only message]")
        text_box.configure(state="disabled")

        # Media info
        if self.message.media:
            m_box = ctk.CTkFrame(
                content,
                fg_color=THEME["bg_card"],
                border_width=1,
                border_color=THEME["border_card"],
                corner_radius=12,
            )
            m_box.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(
                m_box,
                text=f"Media attachments  ({len(self.message.media)} items · {self.message.media_type})",
                font=_F(12, "bold"),
                text_color=THEME["text_body"],
            ).pack(anchor="w", padx=16, pady=(10, 4))
            for m in self.message.media:
                ctk.CTkLabel(
                    m_box,
                    text=f"·  [{m.media_type.upper()}]  {m.url[:85]}…",
                    font=_F(11),
                    text_color=THEME["electric_blue"],
                ).pack(anchor="w", padx=16, pady=3)

        # ── Bottom action bar ─────────────────────────────────────────
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.grid(row=2, column=0, padx=16, pady=12, sticky="ew")

        ctk.CTkButton(
            btn_bar,
            text="Copy Text",
            width=110,
            height=34,
            font=_F(13, "bold"),
            corner_radius=14,
            fg_color=THEME["electric_blue"],
            hover_color=THEME["electric_blue_h"],
            text_color=THEME["text_white"],
            command=self._copy_text,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_bar,
            text="Copy JSON",
            width=110,
            height=34,
            font=_F(13, "bold"),
            corner_radius=14,
            fg_color=THEME["bg_card"],
            hover_color=THEME["bg_subcard"],
            text_color=THEME["text_graphite"],
            border_width=1,
            border_color=THEME["border_dark"],
            command=self._copy_json,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_bar,
            text="Close",
            width=90,
            height=34,
            font=_F(13, "bold"),
            corner_radius=14,
            fg_color=THEME["bg_card"],
            hover_color=THEME["bg_subcard"],
            text_color=THEME["text_body"],
            border_width=1,
            border_color=THEME["border_card"],
            command=self.destroy,
        ).pack(side="right", padx=4)

    def _copy_text(self):
        self.clipboard_clear()
        self.clipboard_append(self.message.text_clean)
        messagebox.showinfo("Copied", "Message text copied to clipboard!")

    def _copy_json(self):
        self.clipboard_clear()
        self.clipboard_append(json.dumps(self.message.to_dict(), indent=2, ensure_ascii=False))
        messagebox.showinfo("Copied", "JSON copied to clipboard!")
