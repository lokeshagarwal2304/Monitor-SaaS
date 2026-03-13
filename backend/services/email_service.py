import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configuration (Load from .env file or environment variables)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "your_email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your_app_password")

def send_alert_email(to_email: str, website_url: str, status: str, error_msg: str = None):
    # Check if SMTP is configured (prevent sending with default values)
    if "your_email" in SMTP_USER or not SMTP_PASSWORD or SMTP_PASSWORD == "your_app_password":
        print(f"[!] Email alert skipped for {website_url}: SMTP not configured in .env")
        return

    subject = f"Alert: {website_url} is {status}"
    if status == "DOWN":
        body = f"MoniFy-Ping has detected that {website_url} is DOWN.\n\nError: {error_msg}\n\nPlease check your server immediately."
    else:
        body = f"Recovery: {website_url} is back UP.\n\nMoniFy-Ping monitoring system detected that your website is now operational."

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        print("[>] EMAIL SENT to", to_email)
    except smtplib.SMTPAuthenticationError:
        print("[x] SMTP AUTH ERROR: Check SMTP_USER and SMTP_PASSWORD in .env")
    except Exception as e:
        print("[x] EMAIL ERROR:", e)


def send_test_notification(to_email: str, user_name: str, monitor_name: str, monitor_url: str, timestamp: str):
    """Send a TEST notification email for a monitor."""
    if "your_email" in SMTP_USER or not SMTP_PASSWORD or SMTP_PASSWORD == "your_app_password":
        print(f"[!] Test notification skipped: SMTP not configured in .env")
        return False, "SMTP not configured"

    subject = f"TEST: Monitor is UP: {monitor_name}"
    body = f"""Hello {user_name},

This is a test alert from MoniFy-Ping.

Monitor Name: {monitor_name}
Checked URL:  {monitor_url}
Status:       UP
Timestamp:    {timestamp}

This is a test message only. No action is required.

-- MoniFy-Ping Monitoring Platform"""

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        print(f"[>] TEST EMAIL SENT to {to_email}")
        return True, "sent"
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication error"
    except Exception as e:
        return False, str(e)