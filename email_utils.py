"""
Email notification utilities for WantAMock application.

This module handles sending email notifications for critical events like
support tickets, payments, and user actions.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import config

logger = logging.getLogger(__name__)

# Admin email for notifications
ADMIN_EMAIL = "alvincheong@u.nus.edu"


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None,
) -> bool:
    """
    Send an email using SMTP.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        body_html: HTML version of email body
        body_text: Plain text version of email body (optional)

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Get SMTP configuration from environment
        smtp_host = config.get_secret("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(config.get_secret("SMTP_PORT", "587"))
        smtp_user = config.get_secret("SMTP_USER", "")
        smtp_password = config.get_secret("SMTP_PASSWORD", "")

        # Skip if SMTP not configured
        if not smtp_user or not smtp_password:
            logger.warning("SMTP not configured - email not sent")
            logger.info(f"Would have sent email to {to_email}: {subject}")
            return False

        # Create message
        msg = MIMEMultipart("alternative")
        msg["From"] = smtp_user
        msg["To"] = to_email
        msg["Subject"] = subject

        # Add plain text version
        if body_text:
            part1 = MIMEText(body_text, "plain")
            msg.attach(part1)

        # Add HTML version
        part2 = MIMEText(body_html, "html")
        msg.attach(part2)

        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())

        logger.info(f"Email sent successfully to {to_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
        return False


def send_support_ticket_notification(
    ticket_id: str,
    user_email: str,
    subject: str,
    category: str,
    priority: str,
    description: str,
) -> bool:
    """
    Send notification to admin when a new support ticket is created.

    Args:
        ticket_id: Unique ticket identifier
        user_email: Email of user who submitted ticket
        subject: Ticket subject/title
        category: Ticket category
        priority: Ticket priority level
        description: Ticket description

    Returns:
        True if notification sent successfully
    """
    # Create HTML email body
    html_body = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 20px;
                    border-radius: 0 0 8px 8px;
                }}
                .field {{
                    margin-bottom: 15px;
                }}
                .label {{
                    font-weight: bold;
                    color: #667eea;
                }}
                .value {{
                    margin-top: 5px;
                    padding: 10px;
                    background: white;
                    border-radius: 4px;
                    border-left: 3px solid #667eea;
                }}
                .priority-high {{
                    border-left-color: #ff4444;
                }}
                .priority-medium {{
                    border-left-color: #ff9800;
                }}
                .priority-low {{
                    border-left-color: #4caf50;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    margin-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🎫 New Support Ticket</h2>
                    <p>A new support ticket has been submitted on WantAMock</p>
                </div>
                <div class="content">
                    <div class="field">
                        <div class="label">Ticket ID:</div>
                        <div class="value">{ticket_id}</div>
                    </div>

                    <div class="field">
                        <div class="label">User Email:</div>
                        <div class="value">{user_email}</div>
                    </div>

                    <div class="field">
                        <div class="label">Subject:</div>
                        <div class="value">{subject}</div>
                    </div>

                    <div class="field">
                        <div class="label">Category:</div>
                        <div class="value">{category}</div>
                    </div>

                    <div class="field">
                        <div class="label">Priority:</div>
                        <div class="value priority-{priority.lower()}">{priority}</div>
                    </div>

                    <div class="field">
                        <div class="label">Description:</div>
                        <div class="value">{description}</div>
                    </div>

                    <a href="https://wantamock.streamlit.app" class="button">
                        View in Admin Dashboard
                    </a>

                    <div class="footer">
                        <p>This is an automated notification from WantAMock Support System.</p>
                    </div>
                </div>
            </div>
        </body>
    </html>
    """

    # Create plain text version
    text_body = f"""
    New Support Ticket Submitted

    Ticket ID: {ticket_id}
    User Email: {user_email}
    Subject: {subject}
    Category: {category}
    Priority: {priority}

    Description:
    {description}

    ---
    View ticket at: https://wantamock.streamlit.app

    This is an automated notification from WantAMock Support System.
    """

    email_subject = f"🎫 New {priority} Priority Support Ticket: {subject}"

    return send_email(
        to_email=ADMIN_EMAIL,
        subject=email_subject,
        body_html=html_body,
        body_text=text_body,
    )
