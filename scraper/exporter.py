"""
Exporters for saving Telegram messages to CSV, JSON, and Excel formats
with full Unicode/Emoji fidelity (UTF-8 with BOM).
"""

import json
import os
import csv
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd

from .models import TelegramMessage, ChannelMetadata


def export_messages(
    messages: List[TelegramMessage],
    export_format: str,
    output_path: str,
    channel_metadata: Optional[ChannelMetadata] = None,
) -> str:
    """
    Exports a list of TelegramMessage objects to the requested format.

    Args:
        messages: List of scraped messages.
        export_format: 'csv', 'json', or 'xlsx' / 'excel'.
        output_path: Filepath where output will be saved.
        channel_metadata: Optional channel header information.

    Returns:
        Absolute filepath of saved file.
    """
    fmt = export_format.lower().strip()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "json":
        return export_to_json(messages, str(out), channel_metadata)
    elif fmt == "csv":
        return export_to_csv(messages, str(out))
    elif fmt in ["xlsx", "excel"]:
        return export_to_excel(messages, str(out), channel_metadata)
    else:
        raise ValueError(f"Unsupported export format: {export_format}. Use 'csv', 'json', or 'xlsx'.")


def export_to_json(
    messages: List[TelegramMessage],
    output_path: str,
    channel_metadata: Optional[ChannelMetadata] = None,
) -> str:
    """Exports messages and metadata to pretty JSON with UTF-8 encoding."""
    data: Dict[str, Any] = {
        "channel": channel_metadata.to_dict() if channel_metadata else {},
        "total_messages": len(messages),
        "exported_at": pd.Timestamp.now().isoformat(),
        "messages": [m.to_dict() for m in messages],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return os.path.abspath(output_path)


def export_to_csv(messages: List[TelegramMessage], output_path: str) -> str:
    """
    Exports messages to CSV using 'utf-8-sig' (UTF-8 with BOM)
    ensuring Microsoft Excel on Windows handles emojis and international characters.
    """
    flat_records = [m.to_flat_dict() for m in messages]
    if not flat_records:
        df = pd.DataFrame(columns=["ID", "Channel", "Date (ISO)", "Views", "Clean Text"])
    else:
        df = pd.DataFrame(flat_records)

    # Use utf-8-sig for Excel compatibility
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return os.path.abspath(output_path)


def export_to_excel(
    messages: List[TelegramMessage],
    output_path: str,
    channel_metadata: Optional[ChannelMetadata] = None,
) -> str:
    """
    Exports messages to a styled Excel (.xlsx) workbook with auto-adjusted columns.
    """
    flat_records = [m.to_flat_dict() for m in messages]
    if not flat_records:
        df = pd.DataFrame(columns=["ID", "Channel", "Date (ISO)", "Views", "Clean Text"])
    else:
        df = pd.DataFrame(flat_records)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Messages", index=False)

        # Style sheet if openpyxl is available
        workbook = writer.book
        worksheet = writer.sheets["Messages"]

        # Header styling
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")

        for col_num, col in enumerate(worksheet.columns, 1):
            col_letter = col[0].column_letter
            header_cell = worksheet[f"{col_letter}1"]
            header_cell.font = header_font
            header_cell.fill = header_fill
            header_cell.alignment = Alignment(horizontal="center", vertical="center")

            # Determine column width
            max_len = max(len(str(cell.value or "")) for cell in col)
            worksheet.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 65)

    return os.path.abspath(output_path)
