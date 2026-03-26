import logging
from typing import Any
from app.channels import BaseChannel
from app.models import WebhookNotification

logger = logging.getLogger(__name__)


class WebhookSyncChannel(BaseChannel):
    schema = WebhookNotification

    def send(self, event: dict[str, Any]) -> None:
        ...
