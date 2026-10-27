"""
MessageTable Widget — Data table with searching, filtering, and sorting.
Features:
- Paper White card container with 20px radius and 1-px card border
- Interactive filter toolbar: text query, media category, and live counter
- ttk.Treeview with zebra rows, Graphite text, and Electric Blue selection highlight
- Light scrollbars and column sorting toggles
"""

from typing import List, Optional, Callable, Dict
import customtkinter as ctk
from tkinter import ttk

from scraper.models import TelegramMessage
from ui.theme import THEME, _F


class MessageTable(ctk.CTkFrame):
    """Data table showcasing scraped Telegram messages with search, filter, and inspect."""

    def __init__(
        self,
        parent,
        on_message_double_click: Optional[Callable[[TelegramMessage], None]] = None,
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
        self.on_message_double_click = on_message_double_click
        self.messages: List[TelegramMessage] = []
        self._sort_reverse: Dict[str, bool] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_ui()

    def _build_ui(self):
        # ── Filter toolbar ────────────────────────────────────────────
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")

        ctk.CTkLabel(
            filter_bar,
            text="Filter",
            font=_F(13, "bold"),
            text_color=THEME["text_graphite"],
        ).pack(side="left", padx=(0, 8))

        self.search_entry = ctk.CTkEntry(
            filter_bar,
            placeholder_text="Search text, IDs, or forward info…",
            width=280,
            height=30,
            font=_F(13),
            corner_radius=14,
            fg_color=THEME["bg_input"],
            border_width=1,
            border_color=THEME["border_input"],
            text_color=THEME["text_graphite"],
            placeholder_text_color=THEME["text_body"],
        )
        self.search_entry.pack(side="left", padx=(0, 12))
        self.search_entry.bind("<KeyRelease>", lambda e: self.apply_filter())

        self.filter_media_combo = ctk.CTkComboBox(
            filter_bar,
            values=["All", "Has Media Only", "Forwarded Only", "With Stars Only"],
            width=165,
            height=30,
            font=_F(13),
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
            command=lambda v: self.apply_filter(),
        )
        self.filter_media_combo.set("All")
        self.filter_media_combo.pack(side="left", padx=4)

        self.table_count_lbl = ctk.CTkLabel(
            filter_bar,
            text="Showing 0 messages",
            font=_F(13, "bold"),
            text_color=THEME["text_body"],
        )
        self.table_count_lbl.pack(side="right", padx=6)

        # ── ttk.Treeview — styled to design tokens ────────────────────
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=THEME["table_row_even"],
            foreground=THEME["table_text"],
            fieldbackground=THEME["table_bg"],
            rowheight=30,
            font=("Inter", 10),
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=THEME["table_header_bg"],
            foreground=THEME["table_header_fg"],
            font=("Inter", 10, "bold"),
            relief="flat",
            padding=(8, 6),
        )
        style.map(
            "Treeview",
            background=[("selected", THEME["table_select_bg"])],
            foreground=[("selected", THEME["table_select_fg"])],
        )

        style.configure(
            "Vertical.TScrollbar",
            background=THEME["bg_subcard"],
            troughcolor=THEME["bg_card"],
            arrowcolor=THEME["text_body"],
            borderwidth=0,
        )
        style.configure(
            "Horizontal.TScrollbar",
            background=THEME["bg_subcard"],
            troughcolor=THEME["bg_card"],
            arrowcolor=THEME["text_body"],
            borderwidth=0,
        )

        columns = ("id", "date", "views", "reactions", "stars", "media", "fwd", "text")
        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        # Zebra tags — near-white alternating rows
        self.tree.tag_configure("evenrow", background=THEME["table_row_even"], foreground=THEME["table_text"])
        self.tree.tag_configure("oddrow",  background=THEME["table_row_odd"],  foreground=THEME["table_text"])

        self.tree.heading("id",        text="ID",                   command=lambda: self.sort_by("id"))
        self.tree.heading("date",      text="Date (Local)",          command=lambda: self.sort_by("date"))
        self.tree.heading("views",     text="Views",                 command=lambda: self.sort_by("views"))
        self.tree.heading("reactions", text="Reactions",             command=lambda: self.sort_by("reactions"))
        self.tree.heading("stars",     text="⭐ Stars",              command=lambda: self.sort_by("stars"))
        self.tree.heading("media",     text="Media")
        self.tree.heading("fwd",       text="Forwarded")
        self.tree.heading("text",      text="Message Text Snippet")

        self.tree.column("id",        width=65,  anchor="center")
        self.tree.column("date",      width=145, anchor="center")
        self.tree.column("views",     width=90,  anchor="e")
        self.tree.column("reactions", width=95,  anchor="e")
        self.tree.column("stars",     width=80,  anchor="e")
        self.tree.column("media",     width=80,  anchor="center")
        self.tree.column("fwd",       width=110, anchor="w")
        self.tree.column("text",      width=360, anchor="w")

        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=1, column=0, sticky="nsew", padx=(12, 0), pady=(0, 6))
        v_scroll.grid(row=1, column=1, sticky="ns", padx=(0, 12), pady=(0, 6))
        h_scroll.grid(row=2, column=0, sticky="ew", padx=(12, 0), pady=(0, 8))

        self.tree.bind("<Double-1>", self._on_double_click)

    def _on_double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region not in ("cell", "tree"):
            return

        item_id = self.tree.focus()
        if not item_id:
            return

        msg = next((m for m in self.messages if str(m.id) == item_id), None)
        if msg and self.on_message_double_click:
            self.on_message_double_click(msg)

    def insert_message(self, msg: TelegramMessage):
        """Inserts a single message row into the Treeview and internal list."""
        if any(m.id == msg.id for m in self.messages):
            return

        self.messages.append(msg)
        row_tag = "evenrow" if len(self.messages) % 2 == 0 else "oddrow"
        self._render_row(msg, tag=row_tag)
        self.table_count_lbl.configure(text=f"Showing {len(self.messages):,} messages")

    def _render_row(self, msg: TelegramMessage, tag: str = "evenrow"):
        if self.tree.exists(str(msg.id)):
            return

        clean_text = msg.text_clean.replace("\n", " ").strip()
        snippet = (clean_text[:65] + "…") if len(clean_text) > 65 else clean_text
        if not snippet and msg.media:
            snippet = f"[{msg.media_type or 'Media'} attachment]"

        react_preview = f"{msg.total_reactions:,}" if msg.total_reactions > 0 else "—"
        stars_str = f"{msg.paid_reactions:,}" if msg.paid_reactions > 0 else "—"
        fwd_str = (msg.forwarded_from_title[:15] + "…") if msg.forwarded_from_title else "—"

        self.tree.insert(
            "",
            "end",
            iid=str(msg.id),
            tags=(tag,),
            values=(
                msg.id,
                msg.datetime_local,
                f"{msg.views:,}" if msg.views else "—",
                react_preview,
                stars_str,
                msg.media_type or "—",
                fwd_str,
                snippet,
            ),
        )

    def clear_table(self):
        """Empties the Treeview and clears stored messages."""
        self.messages.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.table_count_lbl.configure(text="Showing 0 messages")

    def apply_filter(self):
        """Applies search query and media category filters across all loaded messages."""
        query = self.search_entry.get().lower().strip()
        media_filter = self.filter_media_combo.get()

        for item in self.tree.get_children():
            self.tree.delete(item)

        matched = 0
        for msg in self.messages:
            text_match = (
                not query
                or query in str(msg.id)
                or query in msg.text_clean.lower()
                or (msg.forwarded_from_title and query in msg.forwarded_from_title.lower())
            )

            type_match = True
            if media_filter == "Has Media Only":
                type_match = bool(msg.media)
            elif media_filter == "Forwarded Only":
                type_match = msg.is_forward
            elif media_filter == "With Stars Only":
                type_match = msg.paid_reactions > 0

            if text_match and type_match:
                row_tag = "evenrow" if matched % 2 == 0 else "oddrow"
                self._render_row(msg, tag=row_tag)
                matched += 1

        self.table_count_lbl.configure(text=f"Showing {matched:,} of {len(self.messages):,} messages")

    def sort_by(self, col: str):
        """Sorts messages by the given column, toggling between descending and ascending."""
        if not self.messages:
            return

        rev = self._sort_reverse.get(col, False)
        reverse = not rev
        self._sort_reverse[col] = reverse

        if col == "id":
            self.messages.sort(key=lambda m: m.id, reverse=reverse)
        elif col == "date":
            self.messages.sort(key=lambda m: m.datetime_iso, reverse=reverse)
        elif col == "views":
            self.messages.sort(key=lambda m: m.views, reverse=reverse)
        elif col == "reactions":
            self.messages.sort(key=lambda m: m.total_reactions, reverse=reverse)
        elif col == "stars":
            self.messages.sort(key=lambda m: m.paid_reactions, reverse=reverse)

        self.apply_filter()
