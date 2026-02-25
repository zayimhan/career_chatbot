import os
import smtplib
from email.message import EmailMessage


def send_email(subject: str, body: str, to_email: str | None = None) -> dict:
    """
    Minimal SMTP email sender.
    Env:
      EMAIL_ENABLED=1
      EMAIL_FROM=...
      EMAIL_TO=... (optional default receiver)
      SMTP_HOST=smtp.gmail.com
      SMTP_PORT=587
      SMTP_USER=... (often same as EMAIL_FROM)
      SMTP_PASS=... (Gmail App Password)
    """
    if os.getenv("EMAIL_ENABLED", "0") != "1":
        return {"sent": False, "reason": "EMAIL_ENABLED != 1"}

    email_from = os.getenv("EMAIL_FROM")
    email_to = to_email or os.getenv("EMAIL_TO")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER") or email_from
    smtp_pass = os.getenv("SMTP_PASS")

    if not (email_from and email_to and smtp_user and smtp_pass):
        return {"sent": False, "reason": "Missing EMAIL_FROM/EMAIL_TO/SMTP_USER/SMTP_PASS"}

    msg = EmailMessage()
    msg["From"] = email_from
    msg["To"] = email_to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return {"sent": True}
    except Exception as e:
        return {"sent": False, "reason": str(e)}