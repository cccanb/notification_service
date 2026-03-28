from fastapi import FastAPI
from app.models import NotificationEvent
from app.worker.tasks import send_notification

app = FastAPI()


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# TODO: Add authentication, rate limiting, source validation
@app.post("/notify", status_code=202)
def notify(event: NotificationEvent):
    task = send_notification.apply_async(
        args=[event.model_dump()], queue="notifications"
    )
    return {"task_id": task.id}

# TODO: Add task status endpoint