"""
Asynchronous media downloader for Telegram messages.
Downloads photos and video previews into a dedicated channel folder.
"""

import asyncio
import os
import re
from pathlib import Path
from typing import List, Optional, Callable
import httpx

from .models import TelegramMessage, MediaItem


class MediaDownloader:
    """Handles downloading media assets from scraped messages."""

    def __init__(self, download_dir: str = "downloads", max_concurrent: int = 5):
        self.base_dir = Path(download_dir)
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def download_message_media(
        self,
        messages: List[TelegramMessage],
        channel_name: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> int:
        """
        Downloads all media items associated with the provided messages.

        Args:
            messages: List of TelegramMessage objects.
            channel_name: Name of the channel for folder grouping.
            progress_callback: Callback receiving (completed, total, current_filename).

        Returns:
            Count of successfully downloaded files.
        """
        target_dir = self.base_dir / channel_name / "media"
        target_dir.mkdir(parents=True, exist_ok=True)

        # Collect tasks
        download_tasks = []
        for msg in messages:
            for idx, item in enumerate(msg.media):
                if item.url.startswith("http"):
                    # Generate safe filename
                    ext = self._guess_extension(item.url, item.media_type)
                    filename = f"msg_{msg.id}_{idx + 1}.{ext}"
                    dest_path = target_dir / filename
                    item.filename = str(dest_path)
                    download_tasks.append((item.url, dest_path, filename))

        if not download_tasks:
            return 0

        total = len(download_tasks)
        completed = 0
        success_count = 0

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            async def _download_one(url: str, path: Path, fname: str):
                nonlocal completed, success_count
                async with self.semaphore:
                    try:
                        # Avoid redownloading if file exists and has size
                        if path.exists() and path.stat().st_size > 0:
                            success_count += 1
                        else:
                            resp = await client.get(url)
                            if resp.status_code == 200:
                                with open(path, "wb") as f:
                                    f.write(resp.content)
                                success_count += 1
                    except Exception:
                        pass
                    finally:
                        completed += 1
                        if progress_callback:
                            progress_callback(completed, total, fname)

            await asyncio.gather(*[_download_one(u, p, fn) for u, p, fn in download_tasks])

        return success_count

    @staticmethod
    def _guess_extension(url: str, media_type: str) -> str:
        # Check URL query or path
        clean_url = url.split("?")[0].lower()
        for ext in ["jpg", "jpeg", "png", "webp", "mp4", "gif"]:
            if clean_url.endswith(f".{ext}"):
                return ext
        if "video" in media_type:
            return "mp4"
        return "jpg"
