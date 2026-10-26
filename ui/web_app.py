"""
Modern Web Dashboard for Telegram Channel Scraper using Gradio.
Allows browser-based scraping, data inspection, and instant file downloads.
"""

import os
import asyncio
from typing import Tuple
from datetime import datetime
import pandas as pd

try:
    import gradio as gr
except ImportError:
    gr = None


class _DummyProgress:
    def __call__(self, *args, **kwargs):
        pass


from scraper.crawler import TelegramCrawler
from scraper.normalizer import normalize_channel_input
from scraper.exporter import export_messages
from scraper.media_downloader import MediaDownloader


def run_web_scraper(
    channel_input: str,
    max_messages: int,
    delay: float,
    download_media: bool,
    progress=None,
):
    """Executes scraping task from the web dashboard."""
    if progress is None:
        progress = gr.Progress() if gr else _DummyProgress()

    if not channel_input or not channel_input.strip():
        if gr:
            raise gr.Error("Please provide a valid Telegram channel handle or URL.")
        raise ValueError("Please provide a valid Telegram channel handle or URL.")

    clean_channel, _ = normalize_channel_input(channel_input)
    crawler = TelegramCrawler(base_delay=float(delay))

    def on_progress(prog, batch):
        if prog.target_count and prog.target_count > 0:
            pct = min(1.0, prog.scraped_count / prog.target_count)
            progress(pct, desc=f"Scraped {prog.scraped_count}/{prog.target_count} msgs ({prog.messages_per_sec} msg/s)")
        else:
            progress(0.5, desc=f"Scraped {prog.scraped_count} msgs ({prog.messages_per_sec} msg/s)")

    # Run in asyncio event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        metadata, messages = loop.run_until_complete(
            crawler.scrape_channel(
                channel_input=clean_channel,
                max_messages=int(max_messages),
                progress_callback=on_progress,
            )
        )

        if download_media and messages:
            progress(0.9, desc="Downloading media assets locally...")
            downloader = MediaDownloader()
            loop.run_until_complete(downloader.download_message_media(messages, metadata.username))

    finally:
        loop.close()

    if not messages:
        raise gr.Error(f"No messages could be extracted from @{clean_channel}. The channel may be empty or private.")

    # Generate Exports
    os.makedirs("exports", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"exports/{clean_channel}_{ts}.csv"
    json_file = f"exports/{clean_channel}_{ts}.json"
    xlsx_file = f"exports/{clean_channel}_{ts}.xlsx"

    export_messages(messages, "csv", csv_file)
    export_messages(messages, "json", json_file, metadata)
    export_messages(messages, "xlsx", xlsx_file, metadata)

    # Prepare DataFrame
    flat_data = [m.to_flat_dict() for m in messages]
    df = pd.DataFrame(flat_data)

    # Metric summaries
    tot_views = sum(m.views for m in messages)
    tot_react = sum(m.total_reactions for m in messages)
    tot_stars = sum(m.paid_reactions for m in messages)

    stats_md = f"""
### 📊 Channel Overview: **{metadata.title or clean_channel}** (@{clean_channel})
- **Subscribers**: {metadata.subscribers or 'Unknown'}
- **Messages Collected**: {len(messages):,}
- **Total Views**: {tot_views:,}
- **Total Reactions**: {tot_react:,}
- **Telegram Stars (⭐)**: {tot_stars:,}
- **Description**: *{metadata.description[:200] if metadata.description else 'No description available'}*
"""

    return (
        stats_md,
        df,
        csv_file,
        xlsx_file,
        json_file,
    )


def create_web_ui():
    """Builds and returns the Gradio Blocks UI."""
    with gr.Blocks(title="Telegram Channel Scraper (2026 Edition)") as demo:
        gr.Markdown(
            """
# ⚡ Telegram Channel Scraper (2026 Edition)
### Zero-Auth • 100% Free Public Telegram Data Extractor
Extract messages, views, dates, forwards, reactions, Telegram Stars, and media without API keys or phone numbers.
            """
        )

        with gr.Row():
            with gr.Column(scale=3):
                channel_input = gr.Textbox(
                    label="Channel Handle or URL",
                    placeholder="e.g. durov, @durov, https://t.me/durov",
                    value="durov",
                )
            with gr.Column(scale=1):
                max_msgs = gr.Slider(
                    minimum=10,
                    maximum=1000,
                    value=50,
                    step=10,
                    label="Max Messages Limit",
                )
            with gr.Column(scale=1):
                delay_slider = gr.Slider(
                    minimum=0.5,
                    maximum=3.0,
                    value=1.0,
                    step=0.1,
                    label="Politeness Delay (s)",
                )

        with gr.Row():
            download_media_check = gr.Checkbox(
                label="Download photos and thumbnails to local disk",
                value=False,
            )
            scrape_btn = gr.Button("🚀 Start Scraping", variant="primary", scale=2)

        stats_output = gr.Markdown()

        with gr.Row():
            csv_download = gr.File(label="Download CSV (Excel UTF-8)")
            xlsx_download = gr.File(label="Download Excel (.xlsx)")
            json_download = gr.File(label="Download JSON")

        table_output = gr.DataFrame(
            label="Extracted Telegram Messages",
            interactive=False,
            wrap=True,
        )

        scrape_btn.click(
            fn=run_web_scraper,
            inputs=[channel_input, max_msgs, delay_slider, download_media_check],
            outputs=[stats_output, table_output, csv_download, xlsx_download, json_download],
        )

    return demo


def launch_web_app(port: int = 7860, share: bool = False):
    """Launches the Gradio web server."""
    demo = create_web_ui()
    demo.launch(server_name="0.0.0.0", server_port=port, share=share)


if __name__ == "__main__":
    launch_web_app()
