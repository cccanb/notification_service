import logging
import os
import smtplib
from email.mime.text import MIMEText
from app.channels.base import BaseChannel
from app.models import EmailNotification

logger = logging.getLogger(__name__)


class EmailChannel(BaseChannel):
    schema = EmailNotification

    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST", "localhost")
        self.port = int(os.getenv("MAILHOG_SMTP_PORT", "1025"))
        self.username = os.getenv("SMTP_USERNAME", "")
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.sender = os.getenv("SMTP_SENDER", "notifications@example.com")
        self.use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"

    def send(self, event: EmailNotification) -> None:
        recipient = event.recipient
        subject = event.subject
        body = event.body

        message = MIMEText(body, "plain", "utf-8")
        message["Subject"] = subject
        message["From"] = self.sender
        message["To"] = recipient

        logger.info("Sending email | to=%s subject=%s", recipient, subject)

        smtp_cls = smtplib.SMTP_SSL if self.use_tls else smtplib.SMTP
        with smtp_cls(self.host, self.port) as smtp:
            if self.username and self.password:
                smtp.login(self.username, self.password)
            smtp.sendmail(self.sender, [recipient], message.as_string())

        logger.info("Email sent | to=%s", recipient)
