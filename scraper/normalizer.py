"""
Channel URL and handle normalizer.
Handles all common variations:
- https://t.me/s/durov
- https://t.me/durov
- t.me/durov
- @durov
- durov
- https://t.me/durov/531 (extracts channel and message ID)
"""

import re
from typing import Tuple, Optional


def normalize_channel_input(raw_input: str) -> Tuple[str, Optional[int]]:
    """
    Normalizes user channel input into (clean_username, optional_start_id).

    Examples:
        'https://t.me/s/durov' -> ('durov', None)
        'https://t.me/durov/531' -> ('durov', 531)
        '@durov' -> ('durov', None)
        'durov' -> ('durov', None)
        't.me/s/telegram' -> ('telegram', None)

    Raises:
        ValueError if input cannot be normalized to a valid channel name.
    """
    if not raw_input or not isinstance(raw_input, str):
        raise ValueError("Channel input cannot be empty.")

    cleaned = raw_input.strip()

    # Match post URLs like https://t.me/channel_name/123 or https://t.me/s/channel_name/123
    post_match = re.search(
        r"(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me)/(?:s/)?([a-zA-Z0-9_+]+)/(\d+)",
        cleaned,
        re.IGNORECASE,
    )
    if post_match:
        channel = post_match.group(1).lower()
        msg_id = int(post_match.group(2))
        return channel, msg_id

    # Match preview or direct links like https://t.me/s/channel_name or https://t.me/channel_name
    link_match = re.search(
        r"(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me)/(?:s/)?([a-zA-Z0-9_+]+)/?",
        cleaned,
        re.IGNORECASE,
    )
    if link_match:
        channel = link_match.group(1).lower()
        return _validate_channel_name(channel), None

    # Handle @channel_name
    if cleaned.startswith("@"):
        cleaned = cleaned[1:]

    # Remove trailing slashes and query parameters
    cleaned = cleaned.split("?")[0].split("/")[0].strip().lower()

    return _validate_channel_name(cleaned), None


def _validate_channel_name(channel: str) -> str:
    """Validates Telegram channel handle format."""
    # Channel slugs are typically >= 4 characters (Telegram public usernames >= 5, but some short slugs exist)
    if not re.match(r"^[a-zA-Z0-9_+]{3,32}$", channel):
        raise ValueError(
            f"Invalid channel identifier: '{channel}'. Channel names should be 3-32 characters long "
            f"and contain only letters, numbers, and underscores."
        )
    return channel.lower()


def get_web_preview_url(channel_name: str, before_id: Optional[int] = None) -> str:
    """Constructs Telegram web preview URL with optional pagination parameter."""
    url = f"https://t.me/s/{channel_name}"
    if before_id is not None:
        url += f"?before={before_id}"
    return url
