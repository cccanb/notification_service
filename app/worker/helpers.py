import logging
import random
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
    handler.send(event)


def compute_retry_delay(
    attempt: int,
    *,
    base: float = 2.0,
    cap: float = 60.0,
    jitter: float = 1.0,
) -> float:
    """
    Exponential backoff with full jitter.
    """
    exponential = min(cap, base * (2 ** attempt))
    return max(0.0, random.uniform(0, exponential) + random.uniform(-jitter, jitter))


def send_to_dead_letter(payload: dict, *, reason: str) -> None:
    # Lazy import to avoid circular dependency
    from app.worker.tasks import dead_letter_sink

    dead_letter_sink.apply_async(args=[payload, reason], queue="notifications.failed")
