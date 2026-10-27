"""
Desktop GUI for Telegram Channel Scraper — GazandoTD Component Architecture.
Coordinates modular UI widgets (HeaderBar, ControlsFrame, MetricsBar, MessageTable, FooterBar)
with background asynchronous scraping and data export operations.
"""

import sys
import os
import threading
import asyncio
import subprocess
from datetime import datetime
from typing import List, Optional
from tkinter import messagebox, filedialog

import customtkinter as ctk

from scraper.models import TelegramMessage, ChannelMetadata, ScrapeProgress
from scraper.crawler import TelegramCrawler
from scraper.normalizer import normalize_channel_input
from scraper.exporter import export_messages
from scraper.media_downloader import MediaDownloader

from ui.theme import THEME, _F
from ui.dialogs import MessageDetailDialog
from ui.widgets import HeaderBar, ControlsFrame, MetricsBar, MessageTable, FooterBar


class TelegramScraperApp(ctk.CTk):
    """Main Application Window — Coordinates widgets and scraping workflows."""

    def __init__(self):
        super().__init__()

        self.title("Telegram Channel Scraper")
        self.geometry("1140x820")
        self.minsize(940, 680)
        self.configure(fg_color=THEME["bg_window"])

        # Scraper state
        self.channel_metadata: Optional[ChannelMetadata] = None
        self.is_scraping = False
        self.is_paused = False

        # Threading / Async events
        self.cancel_event: Optional[asyncio.Event] = None
        self.pause_event: Optional[asyncio.Event] = None
        self.scrape_thread: Optional[threading.Thread] = None

        # Resolve and apply window icon
        self.icon_path = self._resolve_asset_path("assets/icon.ico")
        if self.icon_path:
            try:
                self.iconbitmap(self.icon_path)
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
        self.grid_rowconfigure(3, weight=1)  # Table expands to fill available height

        # 1. Header Bar (Navigation + Status Pill)
        self.header = HeaderBar(self)
        self.header.grid(row=0, column=0, sticky="ew")

        # 2. Controls Frame (Channel input, buttons, delay, limit, media)
        self.controls = ControlsFrame(
            self,
            on_start=self._start_scrape,
            on_pause=self._toggle_pause,
            on_stop=self._stop_scrape,
            on_clear=self._clear_results,
        )
        self.controls.grid(row=1, column=0, padx=20, pady=(12, 6), sticky="ew")

        # 3. Metrics Bar (4 overview metric cards)
        self.metrics = MetricsBar(self)
        self.metrics.grid(row=2, column=0, padx=20, pady=4, sticky="ew")

        # 4. Message Table (Search toolbar, Treeview, sorting)
        self.table = MessageTable(
            self,
            on_message_double_click=self._on_message_double_click,
        )
        self.table.grid(row=3, column=0, padx=20, pady=6, sticky="nsew")

        # 5. Footer Bar (Progress bar, status message, export buttons)
        self.footer = FooterBar(
            self,
            on_export=self._export_data,
            on_open_folder=self._open_output_folder,
        )
        self.footer.grid(row=4, column=0, sticky="ew")

    # ── Convenient widget backward-compatibility aliases ───────────────────
    @property
    def messages(self) -> List[TelegramMessage]:
        return self.table.messages

    @property
    def tree(self):
        return self.table.tree

    @property
    def search_entry(self):
        return self.table.search_entry

    @property
    def filter_media_combo(self):
        return self.table.filter_media_combo

    @property
    def table_count_lbl(self):
        return self.table.table_count_lbl

    @property
    def card_msgs(self):
        return self.metrics.card_msgs

    @property
    def card_views(self):
        return self.metrics.card_views

    @property
    def card_reacts(self):
        return self.metrics.card_reacts

    @property
    def card_speed(self):
        return self.metrics.card_speed

    @property
    def progress_bar(self):
        return self.footer.progress_bar

    @property
    def progress_status_lbl(self):
        return self.footer.progress_status_lbl

    @property
    def status_pill(self):
        return None

    @property
    def start_btn(self):
        return self.controls.start_btn

    @property
    def pause_btn(self):
        return self.controls.pause_btn

    @property
    def stop_btn(self):
        return self.controls.stop_btn

    @property
    def clear_btn(self):
        return self.controls.clear_btn

    @property
    def channel_entry(self):
        return self.controls.channel_entry

    @property
    def limit_combo(self):
        return self.controls.limit_combo

    @property
    def delay_slider(self):
        return self.controls.delay_slider

    @property
    def download_media_var(self):
        return self.controls.download_media_var

    # ── Scraping Coordination & Background Threading ───────────────────────
    def _start_scrape(
        self,
        channel_input: str,
        max_messages: int,
        delay: float,
        download_media: bool,
    ):
        self.is_scraping = True
        self.is_paused = False

        self.controls.set_scraping_state(True)
        self.header.set_status("Scraping...", "scraping")
        self.footer.set_progress(0)

        # Clear existing messages if scraping a new channel
        clean_channel, _ = normalize_channel_input(channel_input)
        if not self.messages or (self.messages and self.messages[0].channel != clean_channel):
            self._clear_results()

        # Spawn background crawler thread
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
                self.after(0, lambda: self.footer.set_status("Downloading media files..."))
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
        # Add new messages to memory and table
        if new_batch:
            for msg in new_batch:
                self.table.insert_message(msg)

        tot_views = sum(m.views for m in self.messages)
        tot_react = sum(m.total_reactions for m in self.messages)
        self.metrics.update_metrics(
            msgs=prog.scraped_count,
            views=tot_views,
            reacts=tot_react,
            speed=f"{prog.messages_per_sec} msg/s",
        )
        self.footer.set_status(f"Status: {prog.status}")

        if prog.target_count and prog.target_count > 0:
            self.footer.set_progress(prog.scraped_count / prog.target_count)
        else:
            self.footer.step_progress()

    def _on_scrape_finished(self, error: Optional[Exception]):
        self.is_scraping = False
        self.is_paused = False

        self.controls.set_scraping_state(False)

        if error:
            self.header.set_status("Failed", "failed")
            self.footer.set_status(f"Error: {error}")
            messagebox.showerror("Scraping Error", f"An error occurred while scraping:\n\n{error}")
        elif self.cancel_event and self.cancel_event.is_set():
            self.header.set_status("Stopped", "paused")
            self.footer.set_status(f"Scraper stopped. Collected {len(self.messages):,} messages.")
        else:
            self.header.set_status("Completed", "completed")
            self.footer.set_progress(1.0)
            self.footer.set_status(f"Finished! Collected {len(self.messages):,} messages successfully.")

    def _toggle_pause(self):
        if not self.is_scraping or not self.pause_event:
            return

        if not self.is_paused:
            self.pause_event.set()
            self.is_paused = True
            self.controls.set_paused_state(True)
            self.header.set_status("Paused", "paused")
        else:
            self.pause_event.clear()
            self.is_paused = False
            self.controls.set_paused_state(False)
            self.header.set_status("Scraping...", "scraping")

    def _stop_scrape(self):
        if self.cancel_event:
            self.cancel_event.set()
        if self.pause_event and self.is_paused:
            self.pause_event.clear()
        self.footer.set_status("Stopping scraper…")

    def _clear_results(self):
        if self.is_scraping:
            return
        self.table.clear_table()
        self.metrics.reset()
        self.footer.set_progress(0)
        self.header.set_status("Ready", "ready")

    # ── Table Interactivity ────────────────────────────────────────────────
    def _on_message_double_click(self, msg: TelegramMessage):
        MessageDetailDialog(self, msg, icon_path=self.icon_path)

    def _insert_table_row(self, msg: TelegramMessage, tag: str = "evenrow"):
        """Backward-compatibility delegator to MessageTable."""
        self.table.insert_message(msg)

    def _apply_filter(self):
        """Backward-compatibility delegator to MessageTable."""
        self.table.apply_filter()

    def _sort_by(self, col: str):
        """Backward-compatibility delegator to MessageTable."""
        self.table.sort_by(col)

    # ── Export & File Handling ─────────────────────────────────────────────
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
