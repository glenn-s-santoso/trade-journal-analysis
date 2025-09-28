"""Generate a comprehensive trading report with LLM analysis.

Provide Google Drive/Gmail integration for easy sharing and distribution.
"""
import argparse
import os
from datetime import datetime

from src.constants.env import EMAIL_TO, OPENROUTER_API_KEY
from src.constants.user_input import (
    IMPROVEMENT_GOALS,
    OVERTRADING,
    PERSONAL_REFLECTION,
    RISK_MANAGEMENT,
    THIS_WEEK_STRATEGY,
)
from src.util import (
    generate_html_report,
    generate_html_with_drive_urls,
    get_closed_pnl,
    get_llm_analysis,
    send_report_email,
    setup_report_directory,
    upload_to_google_drive,
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate trading report with Google Drive/Gmail integration"
    )
    parser.add_argument(
        "--tempdir",
        type=str,
        choices=["true", "false"],
        default="false",
        help="Use temporary directory for file generation (useful for CI/CD)",
    )
    parser.add_argument(
        "--upload",
        type=str,
        choices=["true", "false"],
        default="false",
        help="Upload report to Google Drive",
    )
    return parser.parse_args()


def main():
    """Generate a comprehensive trading report with LLM analysis and Google Drive/Gmail integration."""
    # Parse command line arguments
    args = parse_args()
    use_tempdir = args.tempdir.lower() == "true"
    upload_to_drive = args.upload.lower() == "true"

    print(
        f"Configuration: Use tempdir: {use_tempdir}\n"
        f"Upload to Drive: {upload_to_drive}\n"
    )
    if EMAIL_TO and upload_to_drive:
        print(f"Will send email to: {EMAIL_TO}")
    else:
        print("No email recipients configured")

    # Fetch data
    print("Fetching closed PnL data from Bybit...")
    pnl_data = get_closed_pnl()

    if not pnl_data:
        print("No closed PnL data found for the specified period.")
        return

    print(f"Found {len(pnl_data)} closed trades.")

    # Get user input data if available
    try:
        user_data = {
            "strategy": THIS_WEEK_STRATEGY,
            "psychology": OVERTRADING,
            "RISK_MANAGEMENT": RISK_MANAGEMENT,
            "reflection": PERSONAL_REFLECTION,
            "improvements": IMPROVEMENT_GOALS,
        }
        has_user_input = True
    except ImportError:
        user_data = {}
        has_user_input = False

    # Generate date string for folder naming
    date = datetime.now().strftime("%Y%m%d_%H%M%S")

    report_dir, is_temp, temp_dir = setup_report_directory(date, use_tempdir)
    print(f"Using {'temporary' if is_temp else 'local'} directory at {report_dir}")

    if not OPENROUTER_API_KEY:
        print("Warning: OpenRouter API key not found. LLM analysis will be skipped.")
        print("Please set OPENROUTER_API_KEY in your .env file.")
        print("Generating report without LLM analysis...")

        # Generate report without LLM analysis
        output_file = os.path.join(report_dir, "trading_report.html")
        if has_user_input:
            generate_html_report(
                pnl_data, output_file=output_file, date=date, user_data=user_data
            )
        else:
            generate_html_report(pnl_data, output_file=output_file, date=date)
    else:
        print("Getting LLM analysis of your trading performance...")
        llm_analysis = get_llm_analysis(
            pnl_data, date, user_data if has_user_input else None
        )

        if "error" in llm_analysis:
            print(f"Error getting LLM analysis: {llm_analysis['error']}")
            print("Generating report without LLM analysis...")

            output_file = os.path.join(report_dir, "trading_report.html")
            if has_user_input:
                generate_html_report(
                    pnl_data, output_file=output_file, date=date, user_data=user_data
                )
            else:
                generate_html_report(pnl_data, output_file=output_file, date=date)
        else:
            print("LLM analysis complete. Generating enhanced report...")

            if has_user_input:
                user_data["llm_analysis"] = llm_analysis
            else:
                user_data = {"llm_analysis": llm_analysis}

            output_file = os.path.join(report_dir, "trading_report.html")
            generate_html_report(
                pnl_data, output_file=output_file, date=date, user_data=user_data
            )

    print(f"HTML report generated: {output_file}")

    drive_urls = {}
    if upload_to_drive:
        print("Uploading report files to Google Drive...")
        drive_urls = upload_to_google_drive(report_dir, date)

        if drive_urls:
            print(f"Successfully uploaded {len(drive_urls)} files to Google Drive")

            generate_html_with_drive_urls(
                pnl_data,
                drive_urls,
                date,
                os.path.join(report_dir, "trading_report_gdrive.html"),
                user_data,
            )
            print("Generated HTML report with Google Drive URLs")
        else:
            print("Failed to upload files to Google Drive")

    if EMAIL_TO and (drive_urls or not upload_to_drive) and upload_to_drive:
        recipient_count = len(EMAIL_TO.split(","))
        print(
            f"Sending report email to {recipient_count} recipient{'s' if recipient_count > 1 else ''}..."
        )

        email_html_content = ""
        if drive_urls:
            gdrive_html_file = os.path.join(report_dir, "trading_report_gdrive.html")
            if os.path.exists(gdrive_html_file):
                with open(gdrive_html_file, encoding="utf-8") as f:
                    email_html_content = f.read()
                print("Using Google Drive HTML content for email")

        if not email_html_content:
            with open(output_file, encoding="utf-8") as f:
                email_html_content = f.read()
            print("Using standard HTML content for email")

        email_to_str = ",".join(EMAIL_TO) if isinstance(EMAIL_TO, list) else EMAIL_TO

        success = send_report_email(
            to_emails=email_to_str,
            html_content=email_html_content,
            date=date,
            drive_urls=drive_urls if drive_urls else None,
        )

        if success:
            print("Report email sent successfully!")
        else:
            print("Failed to send report email")

    if is_temp and temp_dir:
        print("Cleaning up temporary directory...")
        temp_dir.cleanup()

    print("Report generation process complete!")


if __name__ == "__main__":
    main()
