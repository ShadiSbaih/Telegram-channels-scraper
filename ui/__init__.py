"""
UI Package for Telegram Channel Scraper.
Provides Desktop GUI (CustomTkinter) and Web Dashboard (Gradio).
"""

from .desktop_app import launch_desktop_app

try:
    from .web_app import launch_web_app
    __all__ = ["launch_desktop_app", "launch_web_app"]
except ImportError:
    launch_web_app = None
    __all__ = ["launch_desktop_app"]

