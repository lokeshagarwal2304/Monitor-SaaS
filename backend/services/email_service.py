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
    if "your_email" in SMTP_USER:
        print(f"⚠️  Email Alert Skipped (SMTP not configured): {website_url} is {status}")
        return

    subject = f"🚨 Alert: {website_url} is {status}"
    
    if status == "DOWN":
        body = f"MoniFy-Ping has detected that {website_url} is DOWN.\n\nError: {error_msg}\n\nPlease check your server immediately."
    else:
        body = f"✅ Recovery: {website_url} is back UP.\n\nMoniFy-Ping monitoring system detected that your website is now operational."

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        print(f"📧 Email sent to {to_email}: {website_url} is {status}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")