"""
Command-Line Interface for Telegram Channel Scraper using Rich.
Enables headless, scheduled, and scriptable Telegram channel data extraction.
"""

import sys
import os
import asyncio
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from scraper.crawler import TelegramCrawler
from scraper.normalizer import normalize_channel_input
from scraper.exporter import export_messages


def run_cli(channel: str, limit: int = 50, export_format: str = "all"):
    # Fix Windows UTF-8 stdout encoding for emojis
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    console = Console()
    console.rule("[bold cyan]⚡ Telegram Channel Scraper (2026 Edition)[/bold cyan]")

    clean_channel, _ = normalize_channel_input(channel)
    console.print(f"[green]Target Channel:[/green] @{clean_channel}")
    console.print(f"[green]Limit:[/green] {limit} messages | [green]Format:[/green] {export_format.upper()}")

    crawler = TelegramCrawler(base_delay=1.0)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"[cyan]Scraping @{clean_channel}...", total=limit)

        def on_progress(prog, batch):
            progress.update(task, completed=prog.scraped_count, description=f"[cyan]{prog.status}")

        try:
            metadata, messages = loop.run_until_complete(
                crawler.scrape_channel(
                    channel_input=clean_channel,
                    max_messages=limit,
                    progress_callback=on_progress,
                )
            )
        finally:
            loop.close()

    if not messages:
        console.print(f"[bold red]❌ No messages extracted from @{clean_channel}.[/bold red]")
        return

    # Print Summary Table
    table = Table(title=f"Sample Extracted Messages (@{clean_channel})", show_lines=True)
    table.add_column("ID", justify="center", style="cyan", no_wrap=True)
    table.add_column("Date", justify="center", style="magenta")
    table.add_column("Views", justify="right", style="green")
    table.add_column("Reactions", justify="right", style="red")
    table.add_column("Stars ⭐", justify="right", style="yellow")
    table.add_column("Media", justify="center", style="blue")
    table.add_column("Text Snippet", style="white")

    for msg in messages[:8]:
        snippet = (msg.text_clean[:60] + "...") if len(msg.text_clean) > 60 else msg.text_clean
        if not snippet and msg.media:
            snippet = f"[{msg.media_type or 'Media'} attachment]"
        table.add_row(
            str(msg.id),
            msg.datetime_local,
            f"{msg.views:,}" if msg.views else "-",
            f"{msg.total_reactions:,}" if msg.total_reactions else "-",
            f"{msg.paid_reactions:,}" if msg.paid_reactions else "-",
            msg.media_type or "-",
            snippet or "[No text]",
        )

    console.print(table)

    # Save exports
    os.makedirs("exports", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    formats_to_save = ["csv", "json", "xlsx"] if export_format == "all" else [export_format]
    saved_files = []

    for fmt in formats_to_save:
        out_file = f"exports/{clean_channel}_{ts}.{fmt}"
        path = export_messages(messages, fmt, out_file, metadata)
        saved_files.append(path)

    console.print("\n[bold green]✔ Exports saved successfully:[/bold green]")
    for p in saved_files:
        console.print(f"  • [cyan]{p}[/cyan]")


if __name__ == "__main__":
    run_cli("durov", limit=20)
