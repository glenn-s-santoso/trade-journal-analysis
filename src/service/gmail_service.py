"""Gmail service for sending trading report emails."""

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.constants.env import EMAIL_FROM
from src.service.google_auth import ALL_SCOPES, GoogleAuthService


class GmailService:
    """Service for sending emails via Gmail API."""

    def __init__(self):
        """Initialize the Gmail Service."""
        self.auth_service = GoogleAuthService(scopes=ALL_SCOPES)
        self.credentials = self.auth_service.get_credentials()
        self.gmail_service = None

        if self.credentials:
            self.gmail_service = build("gmail", "v1", credentials=self.credentials)
        else:
            raise ValueError("Failed to obtain valid Gmail credentials")

    def send_email(
        self,
        to_emails: str,
        subject: str,
        html_content: str,
        cc_emails: Optional[List[str]] = None,
    ) -> Dict:
        """Send HTML email via Gmail API.

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            html_content: HTML content of the email
            cc_emails: Optional list of CC recipients

        Returns:
            Response from Gmail API
        """
        if not self.gmail_service:
            raise ValueError("Gmail service not initialized")

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["To"] = (
            ", ".join(to_emails) if isinstance(to_emails, list) else to_emails
        )

        if cc_emails:
            message["Cc"] = ", ".join(cc_emails)

        # Set the from email if provided
        message["From"] = EMAIL_FROM

        # Attach HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        try:
            # Send the message
            send_message = (
                self.gmail_service.users()
                .messages()
                .send(userId="me", body={"raw": raw_message})
                .execute()
            )

            return send_message

        except HttpError as error:
            print(f"An error occurred: {error}")
            raise

    def send_report_email(
        self,
        to_emails: str,
        subject: str,
        html_report_content: str,
        report_date: str,
        google_drive_links: Optional[Dict[str, str]] = None,
    ) -> Dict:
        """Send a formatted trading report email.

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            html_report_content: HTML content of the trading report
            report_date: Date of the report for display
            google_drive_links: Optional dictionary of Google Drive file links to include

        Returns:
            Response from Gmail API
        """
        # Add a header to the report with Google Drive links if provided
        header = f"<h2>Trading Performance Report - {report_date}</h2>"

        if google_drive_links:
            header += "<p>Report files are available on Google Drive:</p><ul>"
            for name, link in google_drive_links.items():
                header += f'<li><a href="{link}">{name}</a></li>'
            header += "</ul>"

        # Combine header with report content
        full_content = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                }}
                .email-container {{
                    max-width: 800px;
                    margin: 0 auto;
                }}
                .header {{
                    background-color: #f0f0f0;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                a {{
                    color: #0066cc;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    {header}
                </div>
                {html_report_content}
                <p style="margin-top: 30px; color: #666; font-size: 12px;">
                    This is an automated email sent by the Bybit Trading Analysis tool.
                </p>
            </div>
        </body>
        </html>
        """

        return self.send_email(to_emails, subject, full_content)
