from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class BaseChannel(ABC):
    @property
    @abstractmethod
    def schema(self) -> type[BaseModel]:
        """
        Pydantic model class used for validating incoming payloads for this channel.
        """
        ...

    def validate(self, payload: dict[str, Any]) -> BaseModel:
        """
        Parse and validate raw payload.
        """
        return self.schema(**payload)

    @abstractmethod
    def send(self, event: BaseModel) -> None:
        """
        Send a notification.
        """
        ...
