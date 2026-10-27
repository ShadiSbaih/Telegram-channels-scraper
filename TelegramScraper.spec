# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Collect customtkinter themes, fonts, and assets
ctk_datas = collect_data_files('customtkinter')

# Include project assets (application icons)
project_datas = [
    ('assets/icon.ico', 'assets'),
    ('assets/icon.png', 'assets'),
]

datas = ctk_datas + project_datas

hiddenimports = [
    'customtkinter',
    'darkdetect',
    'PIL',
    'PIL._tkinter_finder',
    'pandas',
    'openpyxl',
    'openpyxl.styles',
    'bs4',
    'soupsieve',
    'lxml',
    'httpx',
    'httpcore',
    'rich',
    'rich.console',
    'rich.table',
    'scraper',
    'scraper.models',
    'scraper.crawler',
    'scraper.client',
    'scraper.parser',
    'scraper.normalizer',
    'scraper.exporter',
    'scraper.media_downloader',
    'ui',
    'ui.theme',
    'ui.dialogs',
    'ui.dialogs.message_detail',
    'ui.widgets',
    'ui.widgets.header',
    'ui.widgets.controls',
    'ui.widgets.metrics',
    'ui.widgets.message_table',
    'ui.widgets.footer',
    'ui.desktop_app',
    'cli',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'ui.web_app',
        'gradio',
        'gradio_client',
        'uvicorn',
        'fastapi',
        'starlette',
        'pydantic',
        'jinja2',
        'matplotlib',
        'scipy',
        'torch',
        'IPython',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TelegramScraper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)
