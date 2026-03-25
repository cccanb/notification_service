from typing import Any, Literal
from pydantic import BaseModel


class EmailNotification(BaseModel):
    channel: Literal["email"]
    recipient: str
    subject: str
    body: str
    metadata: dict[str, Any] = {}

