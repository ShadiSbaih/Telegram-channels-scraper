"""
Data models for Telegram messages, reactions, media, and scraping state.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class MediaItem:
    url: str
    media_type: str  # 'photo', 'video_thumb', 'video', 'document', 'audio', 'voice', 'sticker'
    filename: Optional[str] = None
    file_size_bytes: Optional[int] = None
    caption: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReactionItem:
    emoji: str
    count: int
    is_paid: bool = False  # Telegram Stars

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TelegramMessage:
    id: int
    channel: str
    url: str
    datetime_iso: str
    datetime_local: str
    text_clean: str
    text_html: str
    views: int
    views_raw: str
    forwarded_from_title: Optional[str] = None
    forwarded_from_url: Optional[str] = None
    reply_to_id: Optional[int] = None
    reply_to_url: Optional[str] = None
    reactions: Dict[str, int] = field(default_factory=dict)
    paid_reactions: int = 0  # Telegram Stars count
    total_reactions: int = 0
    media: List[MediaItem] = field(default_factory=list)
    media_type: Optional[str] = None
    is_pinned: bool = False
    is_forward: bool = False
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["media"] = [m.to_dict() if isinstance(m, MediaItem) else m for m in self.media]
        return data

    def to_flat_dict(self) -> Dict[str, Any]:
        """Returns a flat dictionary suitable for CSV / Excel export."""
        reactions_str = ", ".join(f"{k}: {v}" for k, v in self.reactions.items())
        if self.paid_reactions > 0:
            reactions_str += f", ⭐ Stars: {self.paid_reactions}" if reactions_str else f"⭐ Stars: {self.paid_reactions}"

        media_urls = "; ".join(m.url for m in self.media) if self.media else ""

        return {
            "ID": self.id,
            "Channel": self.channel,
            "Date (ISO)": self.datetime_iso,
            "Date (Local)": self.datetime_local,
            "Views": self.views,
            "Views Display": self.views_raw,
            "Total Reactions": self.total_reactions,
            "Reactions Breakdown": reactions_str,
            "Stars": self.paid_reactions,
            "Media Type": self.media_type or "None",
            "Media URLs": media_urls,
            "Is Forward": self.is_forward,
            "Forwarded From": self.forwarded_from_title or "",
            "Forwarded URL": self.forwarded_from_url or "",
            "Reply To ID": self.reply_to_id or "",
            "Message URL": self.url,
            "Clean Text": self.text_clean,
        }


@dataclass
class ChannelMetadata:
    username: str
    title: str = ""
    description: str = ""
    subscribers: str = ""
    subscribers_count: Optional[int] = None
    avatar_url: Optional[str] = None
    is_verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScrapeProgress:
    channel: str
    scraped_count: int = 0
    target_count: Optional[int] = None
    current_before_id: Optional[int] = None
    elapsed_seconds: float = 0.0
    messages_per_sec: float = 0.0
    status: str = "Ready"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
