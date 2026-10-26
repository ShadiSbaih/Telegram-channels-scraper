"""
Main entry point for Telegram Channel Scraper.
Supports Desktop GUI (default), Web Dashboard (--web), and Terminal CLI (--cli).
"""

import sys
import os
import argparse

# Ensure stdout and stderr exist even in windowed/noconsole PyInstaller builds
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="⚡ Telegram Channel Scraper (2026 Edition) - Zero-auth public channel scraper."
    )
    parser.add_argument(
        "--web",
        "-w",
        action="store_true",
        help="Launch the browser-based Web Dashboard (Gradio) instead of Desktop GUI.",
    )
    parser.add_argument(
        "--cli",
        "-c",
        action="store_true",
        help="Run in headless Command-Line Interface mode.",
    )
    parser.add_argument(
        "--channel",
        type=str,
        default="durov",
        help="Channel username or URL to scrape (for CLI mode).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of messages to scrape (for CLI mode).",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json", "xlsx", "all"],
        default="all",
        help="Export format for CLI mode (csv, json, xlsx, all).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port for Web Dashboard (default: 7860).",
    )

    args = parser.parse_args()

    if args.web:
        try:
            from ui.web_app import launch_web_app
            print(f"Starting Telegram Scraper Web Dashboard on port {args.port}...")
            launch_web_app(port=args.port)
        except ImportError:
            print("Web Dashboard (Gradio) is not packaged in the standalone Desktop GUI executable.")
            print("To run the Web Dashboard, please run via Python: python main.py --web")
    elif args.cli:
        from cli import run_cli
        run_cli(channel=args.channel, limit=args.limit, export_format=args.format)
    else:
        # Launch modern CustomTkinter Desktop GUI by default
        from ui.desktop_app import launch_desktop_app
        launch_desktop_app()


if __name__ == "__main__":
    main()

