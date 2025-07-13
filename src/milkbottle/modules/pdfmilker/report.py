import json
import logging
from pathlib import Path
from typing import Any, Dict

from rich.console import Console
from rich.table import Table

logger = logging.getLogger("pdfmilker.report")


def write_report(
    report_data: Dict[str, Any], meta_dir: Path, filename: str = "report.json"
) -> Path:
    """
    Write a summary report as JSON to the meta directory.
    Args:
        report_data (Dict[str, Any]): Data to write to the report.
        meta_dir (Path): Directory to write the report file.
        filename (str): Name of the report file.
    Returns:
        Path: Path to the written report file.
    """
    report_path = meta_dir / filename
    try:
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote report to {report_path}")
    except Exception as e:
        logger.error(f"Failed to write report to {report_path}: {e}")
    return report_path


def print_report(report_data: Dict[str, Any]) -> None:
    """
    Display a Rich summary table in the CLI for the report data.
    Args:
        report_data (Dict[str, Any]): Data to display in the report.
    """
    console = Console()
    table = Table(title="PDFmilker Extraction Report", show_lines=True)
    table.add_column("Key", style="bold cyan")
    table.add_column("Value", style="white")
    for key, value in report_data.items():
        table.add_row(str(key), str(value))
    console.print(table)
