"""Utilities for report generation and handling with Google Drive and Gmail support."""

import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.constants import html_templates_gdrive
from src.service.gmail_service import GmailService
from src.service.google_drive import GoogleDriveService
from src.util.generate_report import (
    _create_improvements_section,
    _create_psychology_section,
    _create_rr_section,
    _create_strategy_section,
)
from src.util.llm_report_section import create_llm_analysis_section


def setup_report_directory(
    date: str, use_tempdir: bool = False
) -> Tuple[str, bool, Optional[tempfile.TemporaryDirectory]]:
    """Set up the report directory either locally or in a temporary directory.

    Args:
        date: Date string for directory naming
        use_tempdir: Whether to use a temporary directory

    Returns:
        Tuple of (report_dir_path, is_temp, temp_dir_object or None)
    """
    temp_dir = None

    if use_tempdir:
        # Create a temporary directory
        temp_dir = tempfile.TemporaryDirectory()
        report_dir = os.path.join(temp_dir.name, date)
        plots_dir = os.path.join(report_dir, "report_plots")

        # Create directories
        os.makedirs(report_dir, exist_ok=True)
        os.makedirs(plots_dir, exist_ok=True)

        return report_dir, True, temp_dir
    else:
        # Use local output directory
        output_dir = "output"
        report_dir = os.path.join(output_dir, date)
        plots_dir = os.path.join(report_dir, "report_plots")

        # Create directories
        os.makedirs(report_dir, exist_ok=True)
        os.makedirs(plots_dir, exist_ok=True)

        return report_dir, False, None


def upload_to_google_drive(report_dir: str, date: str) -> Dict[str, str]:
    """Upload report files to Google Drive and return URLs.

    Args:
        report_dir: Path to the report directory
        date: Date string for folder naming

    Returns:
        Dictionary mapping file paths to Google Drive URLs
    """
    try:
        # Initialize Google Drive service
        drive_service = GoogleDriveService()

        # Upload all files in the report directory to Google Drive
        file_metadata_map = drive_service.upload_directory(
            local_dir=report_dir,
            drive_folder_name="Bybit_Trading_Analysis",
            date_subfolder=date,
        )

        # Create a dictionary mapping file paths to webViewLinks
        drive_urls = {}
        for rel_path, metadata in file_metadata_map.items():
            if "webViewLink" in metadata:
                drive_urls[rel_path] = metadata["webViewLink"]

        return drive_urls

    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")
        return {}


def send_report_email(
    to_emails: str,
    html_content: str,
    date: str,
    drive_urls: Optional[Dict[str, str]] = None,
) -> bool:
    """Send the report via email.

    Args:
        to_emails: List of recipient emails
        html_content: HTML content of the report
        date: Report date string
        drive_urls: Optional dictionary of Google Drive URLs

    Returns:
        Boolean indicating success
    """
    try:
        # Initialize Gmail service
        gmail_service = GmailService()

        # Format date for display (assuming format is YYYYMMDD_HHMMSS)
        display_date = date
        if "_" in date:
            parts = date.split("_")
            if len(parts) == 2:
                date_part = parts[0]
                time_part = parts[1]
                # pragma: allowlist next line
                display_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:]}"

        # Prepare a dictionary of file links for the email
        file_links = {}
        if drive_urls:
            for file_path, url in drive_urls.items():
                file_name = os.path.basename(file_path)
                if file_name.endswith(".html"):
                    file_links["Trading Report"] = url
                elif "plots" in file_path:
                    plot_name = os.path.basename(file_path).replace(".png", "")
                    file_links[f"Chart: {plot_name}"] = url

        # Send the email
        gmail_service.send_report_email(
            to_emails=to_emails,
            subject=f"Bybit Trading Performance Report - {display_date}",
            html_report_content=html_content,
            report_date=display_date,
            google_drive_links=file_links,
        )

        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def generate_html_with_drive_urls(
    pnl_data: List[Dict[str, Any]],
    drive_urls: Dict[str, str],
    date: str,
    output_file: Optional[str] = None,
    user_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate HTML report with Google Drive URLs for images.

    This function is similar to the original generate_html_report but uses
    Google Drive URLs for the image sources.

    Args:
        pnl_data: List of PnL data dictionaries
        drive_urls: Dictionary mapping file paths to Google Drive URLs
        date: Date string
        output_file: Optional path to write HTML file
        user_data: Optional user data dictionary

    Returns:
        HTML content as string
    """
    if not pnl_data:
        print("No data available to generate report")
        return ""

    print("Processing closed PnL data for Drive URL report...")

    # Convert to DataFrame
    df = pd.DataFrame(pnl_data)

    # Convert string values to appropriate types
    df["closedPnl"] = df["closedPnl"].astype(float)

    # Fix FutureWarning by explicitly converting to numeric before to_datetime
    df["createdTime"] = pd.to_datetime(pd.to_numeric(df["createdTime"]), unit="ms")
    df["updatedTime"] = pd.to_datetime(pd.to_numeric(df["updatedTime"]), unit="ms")

    # Convert timestamps from UTC to UTC+7 (Southeast Asia timezone)
    df["createdTime"] = (
        df["createdTime"].dt.tz_localize("UTC").dt.tz_convert("Asia/Bangkok")
    )
    df["updatedTime"] = (
        df["updatedTime"].dt.tz_localize("UTC").dt.tz_convert("Asia/Bangkok")
    )

    try:
        df["avgEntryPrice"] = df["avgEntryPrice"].astype(float)
        df["avgExitPrice"] = df["avgExitPrice"].astype(float)
        df["qty"] = df["qty"].astype(float)
        df["closedSize"] = df["closedSize"].astype(float)
        df["cumEntryValue"] = df["cumEntryValue"].astype(float)
        df["cumExitValue"] = df["cumExitValue"].astype(float)
        df["leverage"] = df["leverage"].astype(float)
    except (KeyError, ValueError) as e:
        print(f"Warning: Some fields could not be converted: {e}")

    # Additional columns for analysis
    df["duration_seconds"] = (df["updatedTime"] - df["createdTime"]).dt.total_seconds()
    df["duration_hours"] = df["duration_seconds"] / 3600
    df["date"] = df["createdTime"].dt.date
    df["hour_of_day"] = df["createdTime"].dt.hour
    df["profit_flag"] = df["closedPnl"] > 0
    df["cumulative_pnl"] = df["closedPnl"].cumsum()

    # Calculate symbol statistics
    symbol_stats = {}
    for symbol in df["symbol"].unique():
        symbol_df = df[df["symbol"] == symbol]
        wins = (symbol_df["closedPnl"] > 0).sum()
        total = len(symbol_df)
        win_rate = wins / total if total > 0 else 0
        avg_pnl = symbol_df["closedPnl"].mean()
        symbol_stats[symbol] = {
            "win_rate": win_rate * 100,
            "avg_pnl": avg_pnl,
            "total_trades": total,
            "total_pnl": symbol_df["closedPnl"].sum(),
        }

    # Convert to DataFrame for the HTML report
    symbol_stats_df = pd.DataFrame.from_dict(symbol_stats, orient="index")

    # Calculate overall performance metrics
    total_pnl = df["closedPnl"].sum()
    win_rate = (df["closedPnl"] > 0).mean() * 100
    total_trades = len(df)
    winning_trades = (df["closedPnl"] > 0).sum()
    losing_trades = (df["closedPnl"] < 0).sum()

    avg_win = (
        df.loc[df["closedPnl"] > 0, "closedPnl"].mean()
        if len(df[df["closedPnl"] > 0]) > 0
        else 0
    )
    avg_loss = (
        df.loc[df["closedPnl"] < 0, "closedPnl"].mean()
        if len(df[df["closedPnl"] < 0]) > 0
        else 0
    )

    # Prepare template parameters
    template_params = {
        "period_start": df["createdTime"].min().strftime("%Y-%m-%d"),
        "period_end": df["createdTime"].max().strftime("%Y-%m-%d"),
        "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_pnl": total_pnl,
        "pnl_class": "positive" if total_pnl > 0 else "negative",
        "win_rate": win_rate,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "total_trades": total_trades,
        "avg_win": avg_win,
        "avg_loss_abs": abs(avg_loss),
    }

    # Add image URLs from Google Drive - use the correct URL paths for each image
    # Convert Google Drive URLs to direct image sources
    def convert_to_direct_image_url(url):
        """Convert Google Drive view URL to direct image URL."""
        if not url or "drive.google.com" not in url:
            return url  # Return unchanged if not a Google Drive URL

        # Extract file ID from the URL
        file_id = None
        if "/file/d/" in url:
            # Format: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
            parts = url.split("/file/d/")
            if len(parts) > 1:
                file_id = parts[1].split("/")[0]

        if file_id:
            # Direct image URL format
            return f"https://drive.google.com/uc?export=view&id={file_id}"
        return url

    # Get URLs for each image with correct path separators
    cum_pnl_url = (
        drive_urls.get("report_plots\\cumulative_pnl.png")
        or drive_urls.get("report_plots/cumulative_pnl.png")
        or "report_plots/cumulative_pnl.png"  # Fallback to local path
    )

    daily_pnl_url = (
        drive_urls.get("report_plots\\daily_pnl.png")
        or drive_urls.get("report_plots/daily_pnl.png")
        or "report_plots/daily_pnl.png"
    )

    pnl_dist_url = (
        drive_urls.get("report_plots\\pnl_distribution.png")
        or drive_urls.get("report_plots/pnl_distribution.png")
        or "report_plots/pnl_distribution.png"
    )

    duration_dist_url = (
        drive_urls.get("report_plots\\duration_distribution.png")
        or drive_urls.get("report_plots/duration_distribution.png")
        or "report_plots/duration_distribution.png"
    )

    heatmap_url = (
        drive_urls.get("report_plots\\hourly_heatmap.png")
        or drive_urls.get("report_plots/hourly_heatmap.png")
        or "report_plots/hourly_heatmap.png"
    )

    # Convert all URLs to direct image URLs
    template_params["cumulative_pnl_url"] = convert_to_direct_image_url(cum_pnl_url)
    template_params["daily_pnl_url"] = convert_to_direct_image_url(daily_pnl_url)
    template_params["pnl_distribution_url"] = convert_to_direct_image_url(pnl_dist_url)
    template_params["duration_distribution_url"] = convert_to_direct_image_url(
        duration_dist_url
    )
    template_params["hourly_heatmap_url"] = convert_to_direct_image_url(heatmap_url)

    # Generate symbol stats rows
    symbol_stats_rows = ""
    for symbol, stats in sorted(
        symbol_stats.items(), key=lambda x: x[1]["total_pnl"], reverse=True
    ):
        symbol_stats_rows += html_templates_gdrive.SYMBOL_STATS_ROW_TEMPLATE.format(
            symbol=symbol,
            win_rate=stats["win_rate"],
            avg_pnl=stats["avg_pnl"],
            avg_pnl_class="positive" if stats["avg_pnl"] > 0 else "negative",
            total_pnl=stats["total_pnl"],
            total_pnl_class="positive" if stats["total_pnl"] > 0 else "negative",
            trade_count=stats["total_trades"],
        )
    template_params["symbol_stats_rows"] = symbol_stats_rows

    # Generate recommendations
    recommendation_items = ""

    # Add dynamic recommendations based on data
    if win_rate < 50:
        recommendation_items += "<li>Your win rate is below 50%. Consider reviewing your entry and exit criteria.</li>"

    # Find best performing symbols
    best_symbol = (
        symbol_stats_df["total_pnl"].idxmax() if not symbol_stats_df.empty else "None"
    )
    if best_symbol != "None":
        recommendation_items += f"<li>Your best performing symbol is {best_symbol}. Consider focusing more on this market.</li>"

    # Find best time of day
    hourly_performance = (
        df.groupby("hour_of_day")["closedPnl"]
        .agg(["mean", "sum", "count"])
        .reset_index()
    )
    if not hourly_performance.empty:
        best_hour = hourly_performance.loc[
            hourly_performance["mean"].idxmax(), "hour_of_day"
        ]
        recommendation_items += f"<li>Your most profitable hour appears to be {best_hour}:00. Consider trading more during this time.</li>"

    # Check if holding time for winning trades differs significantly from losing trades
    avg_win_duration = (
        df.loc[df["closedPnl"] > 0, "duration_hours"].mean()
        if len(df[df["closedPnl"] > 0]) > 0
        else 0
    )
    avg_loss_duration = (
        df.loc[df["closedPnl"] < 0, "duration_hours"].mean()
        if len(df[df["closedPnl"] < 0]) > 0
        else 0
    )

    if avg_win_duration > avg_loss_duration * 1.5:
        recommendation_items += (
            "<li>Your winning trades last significantly longer than your losing trades. ",
            "Consider letting your profitable trades run longer.</li>",
        )
    elif avg_loss_duration > avg_win_duration * 1.5:
        recommendation_items += (
            "<li>Your losing trades last significantly longer than your winning trades. ",
            "Consider cutting losses earlier.</li>",
        )

    template_params["recommendation_items"] = recommendation_items

    user_sections = ""
    if user_data:
        user_sections += _create_strategy_section(user_data.get("strategy"))

        user_sections += _create_psychology_section(user_data.get("psychology"))

        standard_risk = user_data.get("RISK_MANAGEMENT", {}).get(
            "standard_risk_per_trade", 9
        )
        user_sections += _create_rr_section(standard_risk, df=df)

        user_sections += _create_improvements_section(user_data.get("improvements"))

        if user_data.get("reflection"):
            user_sections += html_templates_gdrive.USER_REFLECTION_TEMPLATE.format(
                reflection_text=user_data.get("reflection")
            )

        if user_data.get("llm_analysis"):
            user_sections += create_llm_analysis_section(user_data.get("llm_analysis"))

    template_params["user_sections"] = user_sections

    # Print out what URLs we're using for images
    print("Using the following URLs for images in the report:")
    print(f"Cumulative PnL URL: {template_params['cumulative_pnl_url']}")
    print(f"Daily PnL URL: {template_params['daily_pnl_url']}")
    print(f"PnL Distribution URL: {template_params['pnl_distribution_url']}")
    print(f"Duration Distribution URL: {template_params['duration_distribution_url']}")
    print(f"Hourly Heatmap URL: {template_params['hourly_heatmap_url']}")

    html_content = html_templates_gdrive.REPORT_HTML_TEMPLATE.format(**template_params)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

    print("Google Drive HTML report generated with actual data")
    return html_content
