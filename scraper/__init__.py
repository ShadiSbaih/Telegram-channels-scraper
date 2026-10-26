"""
Telegram Channel Scraper Package (2026 Edition)
100% Free, Zero-Authentication Scraper Engine for Public Telegram Channels.
"""

from .models import TelegramMessage, ChannelMetadata, ScrapeProgress, MediaItem
from .normalizer import normalize_channel_input
from .client import TelegramWebClient
from .parser import TelegramHTMLParser
from .crawler import TelegramCrawler
from .exporter import export_messages
from .media_downloader import MediaDownloader

__all__ = [
    "TelegramMessage",
    "ChannelMetadata",
    "ScrapeProgress",
    "MediaItem",
    "normalize_channel_input",
    "TelegramWebClient",
    "TelegramHTMLParser",
    "TelegramCrawler",
    "export_messages",
    "MediaDownloader",
]
