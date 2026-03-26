import os

from celery import Celery

broker = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery("notification_service", broker=broker, backend=backend)

celery_app.conf.update(

    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    task_default_queue="notifications",
    task_queues={
        "notifications": {},
        "notifications.failed": {},
    },
    task_routes={
        "app.worker.tasks.send_notification": {"queue": "notifications"},
    },

    # ack only after the task completes
    # TODO: implement idempotency
    task_acks_late=True,

    task_reject_on_worker_lost=True,

    # one task per worker
    worker_prefetch_multiplier=1,
)
