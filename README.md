# ⚡ Telegram Channel Scraper (2026 Edition)

[![CI](https://github.com/placeholder/telegram-channel-scraper/actions/workflows/ci.yml/badge.svg)](https://github.com/placeholder/telegram-channel-scraper/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GUI: CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-0088cc.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![Zero Auth](https://img.shields.io/badge/Auth-Zero%20Login%20Required-success.svg)](https://t.me)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

A high-performance, **100% free**, and **zero-authentication** Telegram scraper featuring a modern **Desktop GUI** (CustomTkinter), a **Web Dashboard** (Gradio), a headless **Terminal CLI**, and a pre-compiled standalone **Windows Executable (`.exe`)**.

Extract messages, reactions, paid Telegram Stars, view counts, media links, and forward metadata from any public Telegram channel **without needing Telegram API credentials, bot tokens, phone numbers, or account logins**.

---

## 🌟 Key Features

- 🔓 **Zero Authentication**: Scrapes via Telegram's public web preview endpoint (`https://t.me/s/{channel}`). Completely free, no account bans or API limits.
- ⚡ **2026 Format Extraction**:
  - Full plain text & structured HTML message preservation
  - Humanized view counter conversion (`5.84M` → `5,840,000`, `12.3K` → `12,300`)
  - Full reaction breakdown (emojis and individual counts)
  - **Telegram Stars (⭐)**: Full extraction of paid star reactions
  - Forwarded source metadata and reply references
  - Media extraction (photos, albums, video previews, documents, audio clips)
- 🔄 **Backward Pagination**: Iteratively crawls historical posts backwards via `?before={id}` until target limit is reached.
- 🖥️ **Triple Interface**:
  - **Modern Desktop GUI**: Native dark-themed window (`CustomTkinter`) with 60fps responsive async threading, live metrics (speed, counts, views, stars), real-time table, search/filters, and a message inspector modal.
  - **Browser Web Dashboard**: Interactive Gradio dashboard (`python main.py --web`) with DataFrames and instant browser downloads.
  - **Headless CLI**: Rich terminal output (`python main.py --cli`) ideal for automation and scheduled cron jobs.
- 📦 **Multi-Format Exports**:
  - **CSV**: Encoded in `utf-8-sig` (UTF-8 with BOM) for clean emoji and foreign alphabet support in Microsoft Excel.
  - **Excel (.xlsx)**: Styled sheets with custom branded headers and auto-adjusted column widths.
  - **JSON**: Comprehensive structured metadata and message records.
- 🚀 **Standalone Executable**: Single-file portable `.exe` with embedded icon, themes, and fonts — no Python installation needed for end users.

---

## 🚀 Quick Start

### Option 1: Run Pre-Compiled Windows Executable (No Python Required)

1. Navigate to the [`dist/`](dist/) folder.
2. Double-click **`TelegramScraper.exe`** to launch the Desktop GUI immediately.

To build the executable yourself:
```powershell
python build_exe.py
```

---

### Option 2: Run From Python Source

#### Prerequisites
- Python 3.10 or higher
- Git

#### Installation
```powershell
# Clone the repository
git clone https://github.com/placeholder/telegram-channel-scraper.git
cd telegram-channel-scraper

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate      # On Windows
# source .venv/bin/activate # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

---

## 🖥️ Running the Application

### 1. Modern Desktop GUI (Default)
```powershell
python main.py
```
- Paste any channel handle or link (`durov`, `@telegram`, `https://t.me/durov`).
- Set your max messages limit and delay.
- Click **▶ Start Scraping**.
- Inspect live metrics (views, reactions, speed).
- Double-click any row to open the **Message Inspector** modal.
- Export to **CSV**, **Excel**, or **JSON** with one click.

### 2. Browser Web Dashboard
```powershell
python main.py --web
```
Open your browser at `http://localhost:7860`.

### 3. Headless Command-Line Interface (CLI)
```powershell
# Scrape 50 messages from @durov and save to all formats:
python main.py --cli --channel durov --limit 50 --format all

# Scrape 100 messages from another channel to CSV:
python main.py --cli --channel telegram --limit 100 --format csv
```

---

## 📁 Project Structure

```
telegram-channel-scraper/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Automated CI tests for Python 3.10-3.12
│       └── build-release.yml      # Automated Windows EXE release builder
├── assets/
│   ├── icon.ico                   # Multi-resolution application icon
│   └── icon.png                   # High-res application preview icon
├── scraper/
│   ├── __init__.py                # Package exports
│   ├── models.py                  # Dataclasses (Message, Reaction, Channel, Media)
│   ├── normalizer.py              # URL & handle parser and validator
│   ├── client.py                  # HTTP client with exponential backoff & jitter
│   ├── parser.py                  # BeautifulSoup web preview parser
│   ├── crawler.py                 # Multi-page backwards crawler
│   ├── exporter.py                # CSV, Excel (.xlsx), and JSON exporters
│   └── media_downloader.py        # Asynchronous media asset downloader
├── ui/
│   ├── __init__.py                # UI module exports with resilient fallbacks
│   ├── desktop_app.py             # CustomTkinter modern dark desktop GUI
│   └── web_app.py                 # Gradio web dashboard
├── tests/
│   ├── __init__.py
│   ├── test_normalizer.py         # Unit tests for input parsing
│   ├── test_parser.py             # Unit tests for HTML parser
│   └── test_crawler_live.py       # Live integration test against public Telegram
├── exports/                       # Default output directory (.gitkeep)
├── downloads/                     # Optional media download directory (.gitkeep)
├── build_exe.py                   # One-click PyInstaller build script
├── TelegramScraper.spec           # PyInstaller build specification
├── pyproject.toml                 # Modern PEP 518/621 packaging spec
├── requirements.txt               # Direct dependencies
├── .gitignore                     # Production Git ignore rules
├── LICENSE                        # MIT Open Source License
└── README.md                      # Documentation
```

---

## 🧪 Testing

Run the automated test suite locally:
```powershell
python -m unittest discover tests
```

---

## 🛡️ Best Practices & Rate Limiting

- **Politeness Delay**: The scraper defaults to a 1.0s delay between page requests. Keeping this between 0.8s and 2.0s ensures Telegram never triggers rate limits.
- **Automatic Backoff**: If Telegram throttles requests (HTTP 429), the built-in HTTP client automatically applies exponential backoff with randomized jitter and retries without crashing.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
