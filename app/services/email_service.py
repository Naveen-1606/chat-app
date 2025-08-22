import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import BackgroundTasks
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_verification_email(background_tasks: BackgroundTasks, to_email: str, token: str):
    """
    Send email with verification link pointing to the backend verification endpoint.
    """
    # Backend endpoint for verification
    verification_link = f"{settings.frontend_url}/verify-email?token={token}"

    subject = "Verify your email"
    body = f"""
    <p>Thank you for registering!</p>
    <p>Please verify your email by clicking the link below:</p>
    <p><a href="{verification_link}">Verify Email</a></p>
    <p>After verification, you will be redirected to the login page.</p>
    """

    # Schedule sending email in background
    background_tasks.add_task(send_email, to_email, subject, body)
    logger.info(f"📧 Scheduled verification email to: {to_email}")



def send_email(to_email: str, subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.email_from
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.email_from, to_email, msg.as_string())

        logger.info(f"✅ Email sent to {to_email}")

    except Exception as e:
        logger.exception(f"❌ Failed to send email to {to_email}: {e}")
