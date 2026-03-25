import logging
from celery import Task

from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


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
    ...
