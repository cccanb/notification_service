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
    entry = CHANNEL_REGISTRY.get(channel_name)
    if entry is None:
        logger.error("Channel '%s' not registered — sending to dead-letter queue", channel_name)
        _send_to_dead_letter(payload, reason=f"channel not registered: {channel_name}")
        return

    try:
        event = entry.validate(payload)
    except ValidationError as e:
        logger.error("Payload validation failed: %s", e)
        _send_to_dead_letter(payload, reason=str(e))
        return
    
    try:
        entry.send(event.model_dump())
        logger.info("Notification sent successfully | channel=%s", channel_name)
    except (IOError, OSError, RuntimeError) as e:
        logger.warning(
            "Attempt %d failed | channel=%s error=%s",
            attempt,
            channel_name,
            e,
        )
        if self.request.retries < self.max_retries:
            # TODO: implement exponential backoff with jitter
            countdown = 10
            logger.info("Retrying in %d s...", countdown)
            raise self.retry(exc=e, countdown=countdown)

        logger.error(
            "All %d attempts failed | channel=%s — moving to dead-letter queue",
            self.max_retries + 1,
            channel_name,
        )
        _send_to_dead_letter(payload, reason=str(e))

def _send_to_dead_letter(payload: dict, *, reason: str) -> None:
    ...