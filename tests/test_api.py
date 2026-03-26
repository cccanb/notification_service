from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_notify_email_accepted():
    mock_task = MagicMock()
    mock_task.id = "test-task-id"

    with patch("app.main.send_notification.apply_async", return_value=mock_task):
        response = client.post(
            "/notify",
            json={
                "channel": "email",
                "recipient": "user@example.com",
                "subject": "Hi",
                "body": "Hello",
            },
        )

    assert response.status_code == 202
    assert response.json() == {"task_id": "test-task-id"}


def test_notify_invalid_payload_rejected():
    response = client.post(
        "/notify",
        json={"channel": "email"},
    )
    assert response.status_code == 422
