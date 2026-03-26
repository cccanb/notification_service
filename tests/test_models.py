import pytest
from pydantic import ValidationError

from app.models import EmailNotification, WebhookNotification


def test_email_notification_valid():
    notification = EmailNotification(
        channel="email",
        recipient="user@example.com",
        subject="Hello",
        body="Test body",
    )
    assert notification.recipient == "user@example.com"
    assert notification.metadata == {}


def test_email_notification_missing_field():
    with pytest.raises(ValidationError):
        EmailNotification(channel="email", recipient="user@example.com")


def test_webhook_notification_valid():
    notification = WebhookNotification(
        channel="webhook",
        url="https://example.com/hook",
        payload={"event": "test"},
    )
    assert notification.payload == {"event": "test"}


def test_webhook_notification_invalid_url():
    with pytest.raises(ValidationError):
        WebhookNotification(
            channel="webhook",
            url="not-a-url",
            payload={},
        )
