import logging
from celery import Task
from pydantic import ValidationError

from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

CHANNEL_REGISTRY: dict[str, dict[str, object]] = {
    # "email": {"schema": EmailNotification, "handler": EmailChannel()},
    # "webhook": {"schema": WebhookNotification, "handler": WebhookChannel()},
}


@celery_app.task(
    bind=True,
    name="app.worker.tasks.send_notification",
    max_retries=3,
    queue="notifications",
)
def send_notification(self: Task, payload: dict) -> None:
    """
    Main task
    """
    channel_name: str = payload.get("channel", "<unknown>")
    attempt: int = self.request.retries + 1

    logger.info(
        "Processing notification | channel=%s attempt=%d/%d",
        channel_name,
        attempt,
        self.max_retries + 1,
    )

    # TODO: move to separate function for better readability
    try:
        channel = CHANNEL_REGISTRY[channel_name]
        event = channel.schema(**payload)
    except KeyError:
        logger.error("Unknown channel '%s' — sending to dead-letter queue", channel_name)
        _send_to_dead_letter(payload, reason=f"unknown channel: {channel_name}")
        return
    except ValidationError as exc:
        logger.error("Payload validation failed: %s", exc)
        _send_to_dead_letter(payload, reason=str(exc))
        return

def _send_to_dead_letter(payload: dict, *, reason: str) -> None:
    ...