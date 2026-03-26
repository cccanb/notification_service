import logging
import os
from typing import Any
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

    def send(self, event: dict[str, Any]) -> None:
        ...
