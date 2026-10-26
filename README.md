<div align="center">

<img src="assets/icon.png" alt="Telegram Channel Scraper Logo" width="120" height="120" />

# Telegram Channel Scraper

**A free, zero-authentication scraper for public Telegram channels with a modern Desktop GUI, Web Dashboard, and CLI.**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

</div>

---

## ⚡ Overview

Extract messages, view counts, reactions, paid **Telegram Stars (⭐)**, and media from any public Telegram channel **without needing API keys, phone numbers, or account logins**.

Run it as a native **Windows Desktop app**, a browser-based **Web Dashboard**, or a **Headless CLI**.

---

## 🚀 Quick Start

### Option 1: Download the Windows App (No Python Required)
1. Download the latest **`TelegramScraper.exe`** from [**Releases**](../../releases).
2. Double-click the file to launch the Desktop GUI directly.

---

### Option 2: Run from Python Source

```powershell
# 1. Clone repository
git clone https://github.com/placeholder/telegram-channel-scraper.git
cd telegram-channel-scraper

# 2. Setup virtual environment
python -m venv .venv
.venv\Scripts\activate      # On Windows
# source .venv/bin/activate # On macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch Desktop GUI
python main.py
```

---

## 🌟 Features

- 🔓 **Zero Login / No API Keys**: Works directly on public Telegram channels (`t.me/s/{channel}`) without risk of account bans.
- ⭐ **Telegram Stars & Reactions**: Extracts all standard emoji reactions and paid Telegram Stars.
- 👁️ **Clean Metrics**: Converts abbreviated views (e.g. `5.8M` → `5,800,000`) to exact numbers.
- 🖥️ **Modern Desktop GUI**: Dark-themed CustomTkinter interface with live scraping speed, search/filter, and a detailed message inspector.
- 🌐 **Web Dashboard**: Run in your browser with Gradio (`python main.py --web`).
- 💻 **Terminal CLI**: Headless runner for automated scripts and cron jobs.
- 📁 **Multi-Format Exports**: Save extracted data to styled **Excel (.xlsx)**, **CSV (UTF-8 with BOM)**, or **JSON**.

---

## 🖥️ Usage

### 1. Desktop GUI (Default)
```powershell
python main.py
```
Paste any channel link or username (e.g. `durov`, `@telegram`, `https://t.me/durov`), choose your message limit, and click **Start Scraping**.

### 2. Browser Web Dashboard
```powershell
python main.py --web
```
Opens an interactive dashboard in your browser at `http://localhost:7860`.

### 3. Headless CLI
```powershell
# Scrape 50 messages from @durov to all formats:
python main.py --cli --channel durov --limit 50 --format all

# Scrape 100 messages from @telegram to Excel:
python main.py --cli --channel telegram --limit 100 --format xlsx
```

---

## 🔨 Build Standalone Executable (.EXE)

To recompile the standalone Windows `.exe`:
```powershell
python build_exe.py
```
The output file will be saved in `dist/TelegramScraper.exe`.

---

## 🧪 Running Tests

```powershell
python -m unittest discover tests
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
