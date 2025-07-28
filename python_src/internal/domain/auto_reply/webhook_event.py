"""Webhook Event domain models."""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field


class ChannelType(StrEnum):
    """Channel type enumeration for multi-channel support."""

    LINE = "line"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class WebhookEvent(BaseModel, ABC):
    """Abstract base class for webhook events."""

    event_id: str = Field(..., description="Unique event identifier")
    channel_type: ChannelType = Field(..., description="Channel type")
    user_id: str = Field(..., description="User identifier from the channel")
    timestamp: datetime = Field(..., description="Event timestamp")

    @abstractmethod
    def get_event_type(self) -> str:
        """Get the event type identifier."""
        pass

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class MessageEvent(WebhookEvent):
    """Message webhook event."""

    content: str = Field(..., description="Message content/text")
    message_id: str = Field(..., description="Unique message identifier")
    ig_story_id: Optional[str] = Field(None, description="IG Story ID if message is a reply to story")

    def get_event_type(self) -> str:
        """Get the event type identifier."""
        return "message"
