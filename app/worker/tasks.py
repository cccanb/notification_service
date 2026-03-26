import logging
from celery import Task
from pydantic import ValidationError
from app.worker.celery_app import celery_app
from app.worker.helpers import (
    compute_retry_delay,
    dispatch_notification,
    resolve_channel,
    send_to_dead_letter,
    validate_payload,
)

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.worker.tasks.send_notification",
    max_retries=3,
    queue="notifications",
)
def send_notification(self: Task, payload: dict) -> None:
    channel_name: str = payload.get("channel", "<unknown>")
    attempt: int = self.request.retries + 1

    logger.info(
        "Processing notification | channel=%s attempt=%d/%d",
        channel_name,
        attempt,
        self.max_retries + 1,
    )

    handler = resolve_channel(channel_name)
    if handler is None:
        logger.error("Channel '%s' not registered — sending to dead-letter queue", channel_name)
        send_to_dead_letter(payload, reason=f"channel not registered: {channel_name}")
        return

    try:
        event = validate_payload(handler, payload)
    except ValidationError as e:
        logger.error("Payload validation failed: %s", e)
        send_to_dead_letter(payload, reason=str(e))
        return

    try:
        dispatch_notification(handler, event)
        logger.info("Notification sent successfully | channel=%s", channel_name)
    except (IOError, OSError, RuntimeError) as e:
        logger.warning("Attempt %d failed | channel=%s error=%s", attempt, channel_name, e)
        if self.request.retries < self.max_retries:
            delay = compute_retry_delay(self.request.retries)
            logger.info("Retrying in %.1f s...", delay)
            raise self.retry(exc=e, countdown=delay)

        logger.error(
            "All %d attempts failed | channel=%s — moving to dead-letter queue",
            self.max_retries + 1,
            channel_name,
        )
        send_to_dead_letter(payload, reason=str(e))


@celery_app.task(name="app.worker.tasks.dead_letter_sink", queue="notifications.failed")
def dead_letter_sink(payload: dict, reason: str) -> None:
    logger.error(
        "Dead-letter received | channel=%s reason=%s payload=%s",
        payload.get("channel"),
        reason,
        payload,
    )
    # TODO: persist to DB or storage