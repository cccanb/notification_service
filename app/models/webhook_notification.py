from typing import Any, Literal
from pydantic import BaseModel, HttpUrl, Field


class WebhookNotification(BaseModel):
    channel: Literal["webhook"]
    url: HttpUrl
    payload: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)

