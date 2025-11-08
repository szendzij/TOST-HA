#!/usr/bin/env python3
# coding: utf-8
"""
Email notification module for Tesla order status updates.
"""

import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

from app.config import cfg as Config, TODAY
from app.utils.colors import color_text, strip_color
from app.utils.locale import t
from app.utils.params import STATUS_MODE


def is_email_configured() -> bool:
    """Check if email is configured."""
    required_keys = [
        'email_smtp_host',
        'email_smtp_port',
        'email_smtp_user',
        'email_smtp_password',
        'email_from',
        'email_to'
    ]
    return all(Config.has(key) for key in required_keys)


def print_email_configuration_info() -> None:
    """Print information about email configuration file location."""
    if STATUS_MODE:
        return
    
    from app.config import SETTINGS_FILE
    print(color_text(t("Email Configuration"), '93'))
    print(color_text(t("Email notifications require configuration in settings file."), '93'))
    print(color_text(t("Please add the following settings to: {file}").format(file=SETTINGS_FILE), '93'))
    print(color_text(t("Example configuration:"), '93'))
    print(color_text('  "email_smtp_host": "smtp.gmail.com",', '94'))
    print(color_text('  "email_smtp_port": 587,', '94'))
    print(color_text('  "email_smtp_user": "your-email@gmail.com",', '94'))
    print(color_text('  "email_smtp_password": "your-app-password",', '94'))
    print(color_text('  "email_smtp_use_tls": true,', '94'))
    print(color_text('  "email_from": "your-email@gmail.com",', '94'))
    print(color_text('  "email_to": "recipient@example.com"', '94'))


def format_order_status_text(orders: List[dict]) -> str:
    """Format order status as plain text for email."""
    if not orders:
        return t("No active orders found.")
    
    # Capture the output from display_orders function
    import io
    import sys
    from app.utils.orders import display_orders
    
    output_capture = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = output_capture
    
    try:
        display_orders(orders)
    finally:
        sys.stdout = original_stdout
    
    # Get the output and strip color codes
    output = output_capture.getvalue()
    return strip_color(output)


def send_status_email(orders: List[dict]) -> bool:
    """
    Send order status email.
    
    Args:
        orders: List of order dictionaries
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    if not is_email_configured():
        if not STATUS_MODE:
            print(color_text(t("Email not configured. Skipping email notification."), '93'))
        return False
    
    try:
        # Get configuration
        smtp_host = Config.get('email_smtp_host')
        smtp_port = Config.get('email_smtp_port')
        smtp_user = Config.get('email_smtp_user')
        smtp_password = Config.get('email_smtp_password')
        use_tls = Config.get('email_smtp_use_tls', True)
        email_from = Config.get('email_from')
        email_to = Config.get('email_to')
        
        # Format email content
        subject = t("Tesla Order Status Update - {date}").format(date=TODAY)
        body_text = format_order_status_text(orders)
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = email_to
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        
        # Connect to SMTP server and send
        # Port 465 requires SSL/TLS from the start (SMTP_SSL)
        # Port 587 uses STARTTLS (SMTP + starttls())
        timeout = 30  # 30 seconds timeout
        
        if smtp_port == 465:
            # Port 465 always uses SSL/TLS
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=timeout)
        elif use_tls:
            # Port 587 or other ports with TLS enabled
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=timeout)
            server.starttls()
        else:
            # No encryption (not recommended)
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=timeout)
        
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        if not STATUS_MODE:
            print(color_text(t("Email notification sent successfully."), '92'))
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        if not STATUS_MODE:
            print(color_text(t("[ERROR] SMTP Authentication failed. Please check your username and password."), '91'))
            print(color_text(f"Details: {str(e)}", '91'))
        return False
    except smtplib.SMTPConnectError as e:
        if not STATUS_MODE:
            print(color_text(t("[ERROR] Could not connect to SMTP server. Please check host and port."), '91'))
            print(color_text(f"Details: {str(e)}", '91'))
        return False
    except smtplib.SMTPException as e:
        if not STATUS_MODE:
            print(color_text(t("[ERROR] SMTP error occurred: {error}").format(error=str(e)), '91'))
        return False
    except Exception as e:
        if not STATUS_MODE:
            print(color_text(t("[ERROR] Failed to send email: {error}").format(error=str(e)), '91'))
            import traceback
            traceback.print_exc()
        return False

