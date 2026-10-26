"""
Orchestrates backwards pagination, rate limiting, and progress tracking
for scraping Telegram channels.
"""

import asyncio
import time
import logging
from typing import List, Optional, Callable, Tuple
from datetime import datetime

from .models import TelegramMessage, ChannelMetadata, ScrapeProgress
from .normalizer import normalize_channel_input
from .client import TelegramWebClient, TelegramScraperError
from .parser import TelegramHTMLParser

logger = logging.getLogger(__name__)


class TelegramCrawler:
    """Manages the full lifecycle of crawling a Telegram channel."""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_retries: int = 4,
        timeout: float = 20.0,
    ):
        self.base_delay = base_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.parser = TelegramHTMLParser()

    async def scrape_channel(
        self,
        channel_input: str,
        max_messages: int = 100,
        start_before_id: Optional[int] = None,
        date_after: Optional[datetime] = None,
        progress_callback: Optional[Callable[[ScrapeProgress, List[TelegramMessage]], None]] = None,
        cancel_event: Optional[asyncio.Event] = None,
        pause_event: Optional[asyncio.Event] = None,
    ) -> Tuple[ChannelMetadata, List[TelegramMessage]]:
        """
        Scrapes a Telegram channel backwards from newest to older messages.

        Args:
            channel_input: Raw channel name, URL, or handle.
            max_messages: Max messages to collect (0 or -1 for all available).
            start_before_id: Starting message ID for pagination.
            date_after: Stop crawling if messages are older than this date.
            progress_callback: Callback receiving (ScrapeProgress, new_batch_messages).
            cancel_event: Async event to signal cancellation.
            pause_event: Async event to pause/resume crawling.

        Returns:
            Tuple of (ChannelMetadata, List[TelegramMessage])
        """
        clean_channel, input_msg_id = normalize_channel_input(channel_input)
        current_before_id = start_before_id or input_msg_id

        all_messages: List[TelegramMessage] = []
        seen_ids = set()
        metadata = ChannelMetadata(username=clean_channel)

        start_time = time.time()
        client = TelegramWebClient(
            base_delay=self.base_delay,
            max_retries=self.max_retries,
            timeout=self.timeout,
        )

        progress = ScrapeProgress(
            channel=clean_channel,
            scraped_count=0,
            target_count=max_messages if max_messages > 0 else None,
            current_before_id=current_before_id,
            elapsed_seconds=0.0,
            messages_per_sec=0.0,
            status="Connecting to Telegram...",
        )
        if progress_callback:
            progress_callback(progress, [])

        try:
            async with client:
                consecutive_empty_batches = 0

                while True:
                    # Check cancellation
                    if cancel_event and cancel_event.is_set():
                        progress.status = "Cancelled by user"
                        break

                    # Check pause
                    if pause_event and pause_event.is_set():
                        progress.status = "Paused"
                        if progress_callback:
                            progress_callback(progress, [])
                        while pause_event.is_set():
                            if cancel_event and cancel_event.is_set():
                                break
                            await asyncio.sleep(0.5)
                        if cancel_event and cancel_event.is_set():
                            break
                        progress.status = "Resuming..."

                    progress.status = f"Fetching batch (before={current_before_id or 'latest'})..."
                    if progress_callback:
                        progress_callback(progress, [])

                    html_content = await client.fetch_page(clean_channel, before_id=current_before_id)

                    # Extract channel metadata from the first response
                    if not metadata.title:
                        metadata = self.parser.parse_channel_metadata(html_content, clean_channel)

                    # Parse messages from current page
                    batch_messages = self.parser.parse_messages(html_content, clean_channel)
                    before_id, after_id = self.parser.parse_pagination(html_content)

                    # Filter new messages not yet seen
                    new_messages = []
                    stop_date_reached = False

                    for msg in batch_messages:
                        if msg.id in seen_ids:
                            continue
                        seen_ids.add(msg.id)

                        # Check date cutoff
                        if date_after and msg.datetime_iso:
                            try:
                                msg_dt = datetime.fromisoformat(msg.datetime_iso.replace("Z", "+00:00"))
                                if msg_dt.timestamp() < date_after.timestamp():
                                    stop_date_reached = True
                                    continue
                            except Exception:
                                pass

                        new_messages.append(msg)

                    if not new_messages:
                        consecutive_empty_batches += 1
                        if consecutive_empty_batches >= 2 or not before_id:
                            # Reached end of accessible preview history
                            logger.info("No further messages found or reached history limit.")
                            break
                    else:
                        consecutive_empty_batches = 0
                        all_messages.extend(new_messages)

                    # Update statistics
                    elapsed = max(0.001, time.time() - start_time)
                    progress.scraped_count = len(all_messages)
                    progress.elapsed_seconds = elapsed
                    progress.messages_per_sec = round(len(all_messages) / elapsed, 1)
                    progress.current_before_id = current_before_id

                    if progress_callback:
                        progress_callback(progress, new_messages)

                    # Check max messages condition
                    if max_messages > 0 and len(all_messages) >= max_messages:
                        all_messages = all_messages[:max_messages]
                        progress.scraped_count = len(all_messages)
                        progress.status = f"Completed target of {max_messages} messages"
                        break

                    if stop_date_reached:
                        progress.status = "Reached date threshold"
                        break

                    # Update next pagination target
                    # If parser found before_id, use it. Otherwise, use minimum message ID from this batch.
                    if before_id:
                        current_before_id = before_id
                    elif batch_messages:
                        min_id = min(m.id for m in batch_messages)
                        current_before_id = min_id
                    else:
                        # Cannot paginate further
                        break

            # Sort descending by ID
            all_messages.sort(key=lambda m: m.id, reverse=True)
            if progress.status not in ["Cancelled by user", "Reached date threshold"]:
                progress.status = f"Completed! Total {len(all_messages)} messages scraped."

            if progress_callback:
                progress_callback(progress, [])

            return metadata, all_messages

        except Exception as e:
            progress.status = f"Error: {str(e)}"
            if progress_callback:
                progress_callback(progress, [])
            raise
