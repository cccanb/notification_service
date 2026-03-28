import logging
from app.channels import BaseChannel
from app.models import WebhookNotification

logger = logging.getLogger(__name__)


class WebhookChannel(BaseChannel):
    schema = WebhookNotification

    def send(self, event: WebhookNotification) -> None:
        ...
