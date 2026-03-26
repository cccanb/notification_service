from app.models import EmailNotification, WebhookNotification

# Resolving the correct model by "channel" field
NotificationEvent = EmailNotification | WebhookNotification
