"""Webhook Event domain models."""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from internal.domain.auto_reply.webhook_trigger import WebhookTriggerEventType


class WebhookEventType(StrEnum):
    """Webhook event type enumeration."""

    MESSAGE = "message"
    POSTBACK = "postback"
    FOLLOW = "follow"
    BEACON = "beacon"


class ChannelType(StrEnum):
    """Channel type enumeration."""

    LINE = "line"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class WebhookEvent(BaseModel, ABC):
    """Abstract base class for webhook events."""

    event_id: str = Field(..., description="Unique event identifier")
    channel_type: ChannelType = Field(..., description="Channel where event originated")
    user_id: str = Field(..., description="User identifier from the channel")
    timestamp: datetime = Field(..., description="Event timestamp")

    @abstractmethod
    def get_event_type(self) -> WebhookEventType:
        """Get the event type."""
        pass

    @abstractmethod
    def get_trigger_event_type(self) -> WebhookTriggerEventType:
        """Get the corresponding trigger event type for matching."""
        pass

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class MessageEvent(WebhookEvent):
    """Message webhook event."""

    content: str = Field(..., description="Message content/text")
    message_id: str = Field(..., description="Unique message identifier")

    def get_event_type(self) -> WebhookEventType:
        """Get the event type."""
        return WebhookEventType.MESSAGE

    def get_trigger_event_type(self) -> WebhookTriggerEventType:
        """Get the corresponding trigger event type for matching."""
        return WebhookTriggerEventType.MESSAGE

    def get_normalized_content(self) -> str:
        """Get normalized message content for keyword matching."""
        return self.content.strip().lower()


class PostbackEvent(WebhookEvent):
    """Postback webhook event."""

    data: str = Field(..., description="Postback data/payload")
    postback_id: str = Field(..., description="Unique postback identifier")

    def get_event_type(self) -> WebhookEventType:
        """Get the event type."""
        return WebhookEventType.POSTBACK

    def get_trigger_event_type(self) -> WebhookTriggerEventType:
        """Get the corresponding trigger event type for matching."""
        return WebhookTriggerEventType.POSTBACK


class FollowEvent(WebhookEvent):
    """Follow webhook event."""

    def get_event_type(self) -> WebhookEventType:
        """Get the event type."""
        return WebhookEventType.FOLLOW

    def get_trigger_event_type(self) -> WebhookTriggerEventType:
        """Get the corresponding trigger event type for matching."""
        return WebhookTriggerEventType.FOLLOW


class BeaconEvent(WebhookEvent):
    """Beacon webhook event."""

    beacon_data: dict[str, object] = Field(..., description="Beacon event data")

    def get_event_type(self) -> WebhookEventType:
        """Get the event type."""
        return WebhookEventType.BEACON

    def get_trigger_event_type(self) -> WebhookTriggerEventType:
        """Get the corresponding trigger event type for matching."""
        return WebhookTriggerEventType.BEACON
