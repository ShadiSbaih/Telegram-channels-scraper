"""
HTML parser for Telegram Web Preview pages (2026 Edition).
Extracts structured message data, channel metadata, reactions, Stars, and media.
"""

import re
import html
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup

from .models import TelegramMessage, ChannelMetadata, MediaItem


class TelegramHTMLParser:
    """Parses Telegram web preview HTML into structured data objects."""

    def __init__(self, parser_backend: str = "lxml"):
        # Will fallback to html.parser if lxml is missing
        self.parser_backend = parser_backend

    def _get_soup(self, html_content: str) -> BeautifulSoup:
        try:
            return BeautifulSoup(html_content, self.parser_backend)
        except Exception:
            return BeautifulSoup(html_content, "html.parser")

    def parse_channel_metadata(self, html_content: str, channel_username: str) -> ChannelMetadata:
        """Extracts channel title, description, subscriber count, and avatar."""
        soup = self._get_soup(html_content)

        title = ""
        title_el = soup.select_one(".tgme_channel_info_header_title, .tgme_page_title")
        if title_el:
            title = title_el.get_text(strip=True)

        description = ""
        desc_el = soup.select_one(".tgme_channel_info_description, .tgme_page_description")
        if desc_el:
            description = desc_el.get_text(separator="\n", strip=True)

        subscribers = ""
        sub_count = None
        counter_el = soup.select_one(".tgme_channel_info_counter .counter_value, .tgme_page_extra")
        if counter_el:
            subscribers = counter_el.get_text(strip=True)
            sub_count = self._parse_numeric_count(subscribers)

        avatar_url = None
        img_el = soup.select_one(".tgme_page_photo_image img, .tgme_channel_info_header img")
        if img_el and img_el.get("src"):
            avatar_url = img_el["src"]

        is_verified = bool(soup.select_one(".verified-icon, .icon-verified"))

        return ChannelMetadata(
            username=channel_username,
            title=title,
            description=description,
            subscribers=subscribers,
            subscribers_count=sub_count,
            avatar_url=avatar_url,
            is_verified=is_verified,
        )

    def parse_messages(self, html_content: str, channel_username: str) -> List[TelegramMessage]:
        """Parses all messages found in a web preview page."""
        soup = self._get_soup(html_content)
        messages: List[TelegramMessage] = []

        widgets = soup.select(".tgme_widget_message_wrap")
        for wrap in widgets:
            msg_el = wrap.select_one(".tgme_widget_message")
            if not msg_el:
                continue

            msg = self._parse_single_message(msg_el, channel_username)
            if msg:
                messages.append(msg)

        return messages

    def parse_pagination(self, html_content: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Extracts (before_id, after_id) for pagination.
        before_id points to older messages; after_id points to newer messages.
        """
        before_match = re.search(r'href="[^"]*[?&]before=(\d+)[^"]*"', html_content)
        after_match = re.search(r'href="[^"]*[?&]after=(\d+)[^"]*"', html_content)

        before_id = int(before_match.group(1)) if before_match else None
        after_id = int(after_match.group(1)) if after_match else None

        return before_id, after_id

    def _parse_single_message(self, msg_el: BeautifulSoup, channel_username: str) -> Optional[TelegramMessage]:
        """Parses an individual message container."""
        # 1. Message ID & URL
        data_post = msg_el.get("data-post", "")
        if "/" in data_post:
            channel_slug, msg_id_str = data_post.split("/", 1)
            try:
                msg_id = int(msg_id_str)
            except ValueError:
                return None
            channel = channel_slug
            msg_url = f"https://t.me/{data_post}"
        else:
            date_link = msg_el.select_one("a.tgme_widget_message_date")
            if date_link and date_link.get("href"):
                msg_url = date_link["href"]
                parts = msg_url.rstrip("/").split("/")
                try:
                    msg_id = int(parts[-1])
                    channel = parts[-2]
                except (ValueError, IndexError):
                    return None
            else:
                return None

        # 2. Date and Time
        time_el = msg_el.select_one(".tgme_widget_message_date time")
        datetime_iso = ""
        datetime_local = ""
        if time_el and time_el.get("datetime"):
            datetime_iso = time_el["datetime"]
            try:
                dt = datetime.fromisoformat(datetime_iso.replace("Z", "+00:00"))
                datetime_local = dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                datetime_local = datetime_iso

        # 3. Message Text (Handle text or media caption)
        text_clean = ""
        text_html = ""
        text_el = msg_el.select_one(".tgme_widget_message_text")
        if text_el:
            text_html = str(text_el)
            # Replace <br> with newlines before extracting clean text
            for br in text_el.find_all("br"):
                br.replace_with("\n")
            text_clean = text_el.get_text().strip()

        # 4. Views Count
        views_raw = ""
        views_count = 0
        views_el = msg_el.select_one(".tgme_widget_message_views")
        if views_el:
            views_raw = views_el.get_text(strip=True)
            views_count = self._parse_numeric_count(views_raw)

        # 5. Forwarded Metadata
        forwarded_from_title = None
        forwarded_from_url = None
        fwd_el = msg_el.select_one(".tgme_widget_message_forwarded_from_name")
        if fwd_el:
            forwarded_from_title = fwd_el.get_text(strip=True)
            forwarded_from_url = fwd_el.get("href")

        is_forward = bool(fwd_el)

        # 6. Reply To Metadata
        reply_to_id = None
        reply_to_url = None
        reply_el = msg_el.select_one("a.tgme_widget_message_reply")
        if reply_el and reply_el.get("href"):
            reply_to_url = reply_el["href"]
            match = re.search(r"/(\d+)$", reply_to_url)
            if match:
                reply_to_id = int(match.group(1))

        # 7. Reactions & Telegram Stars (2026 Support)
        reactions: Dict[str, int] = {}
        paid_stars = 0

        # Parse reaction container
        react_box = msg_el.select_one(".tgme_widget_message_reactions, .js-message_reactions")
        if react_box:
            for react_item in react_box.select(".tgme_reaction"):
                classes = react_item.get("class", [])

                # Check if this is a paid Telegram Stars reaction
                if "tgme_reaction_paid" in classes or react_item.select_one(".icon-telegram-stars"):
                    count_text = react_item.get_text(strip=True)
                    paid_stars += self._parse_numeric_count(count_text)
                    continue

                # Normal or custom emoji
                count_el = react_item.select_one(".tgme_widget_message_reaction_count")
                emoji_el = react_item.select_one(".tgme_widget_message_reaction_emoji, tg-emoji")

                if count_el and emoji_el:
                    emoji = emoji_el.get_text(strip=True) or emoji_el.get("emoji-id", "✨")
                    count = self._parse_numeric_count(count_el.get_text(strip=True))
                    reactions[emoji] = count
                else:
                    # Fallback for inline reaction structure: text contains emoji + count
                    item_text = react_item.get_text(strip=True)
                    # Extract trailing numbers (e.g., '👍 12.3K' or '🔥54.6K')
                    count_match = re.search(r"([\d\.,]+[KMkm]?)$", item_text)
                    if count_match:
                        c_str = count_match.group(1)
                        count = self._parse_numeric_count(c_str)
                        emoji = item_text[:count_match.start()].strip() or "✨"
                        reactions[emoji] = count

        total_reactions = sum(reactions.values()) + paid_stars

        # 8. Media Extraction (Photos, Videos, Audios, Docs)
        media_items: List[MediaItem] = []

        # Photos
        photo_elements = msg_el.select(".tgme_widget_message_photo_wrap")
        for p_el in photo_elements:
            style = p_el.get("style", "")
            img_url = self._extract_background_url(style)
            if img_url:
                media_items.append(MediaItem(url=img_url, media_type="photo"))

        # Videos
        video_elements = msg_el.select(".tgme_widget_message_video_player, .tgme_widget_message_video_wrap")
        for v_el in video_elements:
            thumb_el = v_el.select_one(".tgme_widget_message_video_thumb")
            thumb_url = self._extract_background_url(thumb_el.get("style", "")) if thumb_el else None
            # Video stream source or video tag
            video_src = None
            vid_tag = v_el.select_one("video")
            if vid_tag and vid_tag.get("src"):
                video_src = vid_tag["src"]

            best_url = video_src or thumb_url
            if best_url:
                media_items.append(
                    MediaItem(
                        url=best_url,
                        media_type="video" if video_src else "video_thumb",
                    )
                )

        # Documents & Voice Notes
        doc_elements = msg_el.select(".tgme_widget_message_document")
        for d_el in doc_elements:
            doc_title_el = d_el.select_one(".tgme_widget_message_document_title")
            doc_title = doc_title_el.get_text(strip=True) if doc_title_el else "document"
            media_items.append(
                MediaItem(
                    url=msg_url,  # documents in web preview don't expose direct download link without bot API
                    media_type="document",
                    filename=doc_title,
                )
            )

        # Voice notes
        voice_el = msg_el.select_one(".tgme_widget_message_voice")
        if voice_el:
            media_items.append(
                MediaItem(url=msg_url, media_type="voice")
            )

        # Determine overall media type classification
        media_type = None
        if len(photo_elements) > 1:
            media_type = "album"
        elif photo_elements:
            media_type = "photo"
        elif video_elements:
            media_type = "video"
        elif doc_elements:
            media_type = "document"
        elif voice_el:
            media_type = "voice"

        # 9. Pinned status
        is_pinned = "tgme_widget_message_pinned" in msg_el.get("class", [])

        return TelegramMessage(
            id=msg_id,
            channel=channel,
            url=msg_url,
            datetime_iso=datetime_iso,
            datetime_local=datetime_local,
            text_clean=text_clean,
            text_html=text_html,
            views=views_count,
            views_raw=views_raw,
            forwarded_from_title=forwarded_from_title,
            forwarded_from_url=forwarded_from_url,
            reply_to_id=reply_to_id,
            reply_to_url=reply_to_url,
            reactions=reactions,
            paid_reactions=paid_stars,
            total_reactions=total_reactions,
            media=media_items,
            media_type=media_type,
            is_pinned=is_pinned,
            is_forward=is_forward,
        )

    @staticmethod
    def _extract_background_url(style_attr: str) -> Optional[str]:
        """Extracts URL from CSS background-image:url('...') attribute."""
        if not style_attr:
            return None
        match = re.search(r"background-image:\s*url\(['\"]?(.*?)['\"]?\)", style_attr, re.IGNORECASE)
        if match:
            return html.unescape(match.group(1))
        return None

    @staticmethod
    def _parse_numeric_count(text: str) -> int:
        """
        Converts human-readable counters like '5.84M', '12.3K', '950', '1,234' into integers.
        """
        if not text:
            return 0
        cleaned = text.strip().replace(",", "").replace(" ", "").upper()
        try:
            if cleaned.endswith("M"):
                return int(float(cleaned[:-1]) * 1_000_000)
            elif cleaned.endswith("K"):
                return int(float(cleaned[:-1]) * 1_000)
            elif cleaned.endswith("B"):
                return int(float(cleaned[:-1]) * 1_000_000_000)
            return int(float(cleaned))
        except (ValueError, TypeError):
            return 0
