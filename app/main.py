from fastapi import FastAPI
from app.models.notification import EmailNotification
from app.worker.tasks import send_notification

app = FastAPI()


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/notify", status_code=202)
def notify(event: EmailNotification):
    task = send_notification.apply_async(
        args=[event.model_dump()], queue="notifications"
    )
    return {"task_id": task.id}