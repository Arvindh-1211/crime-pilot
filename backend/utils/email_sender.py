import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# For testing, you can place these in your .env.local or set them in your environment
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send an email using SMTP.
    
    Returns True if successful, False otherwise.
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("WARNING: SMTP credentials not set. Skipping real email dispatch.")
        return False

    msg = MIMEMultipart()
    msg['From'] = SMTP_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Successfully sent email to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}. Error: {e}")
        return False
