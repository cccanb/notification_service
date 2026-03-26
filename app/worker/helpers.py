import logging
from pydantic import BaseModel
from app.channels import EmailChannel, WebhookChannel
from app.channels.base import BaseChannel

logger = logging.getLogger(__name__)


CHANNEL_REGISTRY: dict[str, BaseChannel] = {
    "email": EmailChannel(),
    "webhook": WebhookChannel(),
}


def resolve_channel(channel_name: str) -> BaseChannel | None:
    return CHANNEL_REGISTRY.get(channel_name)


def validate_payload(handler: BaseChannel, payload: dict) -> BaseModel:
    return handler.validate(payload)


def dispatch_notification(handler: BaseChannel, event: BaseModel) -> None:
    handler.send(event.model_dump())


def send_to_dead_letter(payload: dict, *, reason: str) -> None:
    # Lazy import to avoid circular dependency
    from app.worker.tasks import dead_letter_sink

    dead_letter_sink.apply_async(args=[payload, reason], queue="notifications.failed")
