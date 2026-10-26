"""
HTTP client for fetching Telegram web preview pages with rate-limiting defense,
browser emulation, and retry logic.
"""

import asyncio
import random
import logging
from typing import Optional, Dict
import httpx

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


class TelegramScraperError(Exception):
    """Base exception for Telegram scraper."""
    pass


class ChannelNotFoundError(TelegramScraperError):
    """Raised when channel does not exist or preview is disabled."""
    pass


class RateLimitError(TelegramScraperError):
    """Raised when Telegram throttles requests."""
    pass


class TelegramWebClient:
    """Async HTTP client tailored for scraping Telegram web preview endpoint."""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_retries: int = 4,
        timeout: float = 20.0,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.base_delay = max(0.2, base_delay)
        self.max_retries = max_retries
        self.timeout = timeout
        self.headers = headers or DEFAULT_HEADERS.copy()
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            headers=self.headers,
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def fetch_page(self, channel_name: str, before_id: Optional[int] = None) -> str:
        """
        Fetches the HTML of a channel preview page with automatic retry and backoff.
        """
        if not self._client:
            self._client = httpx.AsyncClient(
                headers=self.headers,
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
            )

        url = f"https://t.me/s/{channel_name}"
        params = {}
        if before_id is not None:
            params["before"] = str(before_id)

        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self._client.get(url, params=params)

                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 10))
                    jitter = random.uniform(1.0, 3.0)
                    wait_time = retry_after + jitter
                    logger.warning(f"Rate limited (429). Backing off for {wait_time:.1f}s (attempt {attempt}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
                    continue

                if response.status_code == 404:
                    raise ChannelNotFoundError(
                        f"Channel '@{channel_name}' was not found. Please verify the username."
                    )

                response.raise_for_status()
                html = response.text

                # Check if Telegram returned an error page or empty redirect
                if "tgme_channel_info" not in html and "tgme_widget_message" not in html:
                    if "If you have <strong>Telegram</strong>, you can contact" in html or "View in Telegram" in html:
                        raise ChannelNotFoundError(
                            f"Channel '@{channel_name}' exists as a private entity or user account, but has no public web preview."
                        )

                # Polite inter-request delay with slight jitter
                delay = self.base_delay + random.uniform(0.1, 0.4)
                await asyncio.sleep(delay)

                return html

            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_error = e
                backoff = (2 ** attempt) + random.uniform(0.5, 1.5)
                logger.warning(
                    f"Request failed for {channel_name} (before={before_id}): {e}. Retrying in {backoff:.1f}s..."
                )
                await asyncio.sleep(backoff)

        raise TelegramScraperError(
            f"Failed to fetch channel '@{channel_name}' after {self.max_retries} attempts: {last_error}"
        )

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
