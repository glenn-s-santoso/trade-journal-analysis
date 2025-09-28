"""Utility package for trading report generation, analysis, and data handling.

Contains modules for generating HTML reports, analyzing trading data, and managing file operations.
"""

from .generate_report import generate_html_report
from .get_closed_pnl import get_closed_pnl
from .llm_analyzer import get_llm_analysis
from .llm_report_section import create_llm_analysis_section
from .report_utils import (
    generate_html_with_drive_urls,
    send_report_email,
    setup_report_directory,
    upload_to_google_drive,
)

__all__ = [
    "get_closed_pnl",
    "get_llm_analysis",
    "generate_html_report",
    "create_llm_analysis_section",
    "setup_report_directory",
    "upload_to_google_drive",
    "send_report_email",
    "generate_html_with_drive_urls",
]
