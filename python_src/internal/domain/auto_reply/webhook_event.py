"""Webhook Event domain models."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel


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


class WebhookEvent(BaseModel):
    """Unified webhook event model for all channels.

    Represents a webhook event that can trigger auto-replies across
    LINE, Facebook, and Instagram channels.
    """

    event_type: WebhookEventType
    channel_type: ChannelType
    bot_id: int
    user_id: str
    message_content: str | None = None
    ig_story_id: str | None = None
    timestamp: datetime
    reply_token: str | None = None
    raw_event: dict[str, Any] | None = None

    def has_message_content(self) -> bool:
        """Check if event has message content."""
        return self.message_content is not None and self.message_content.strip() != ""

    def has_ig_story_context(self) -> bool:
        """Check if event has IG Story context."""
        return self.ig_story_id is not None and self.ig_story_id.strip() != ""

    def is_message_event(self) -> bool:
        """Check if this is a message event."""
        return self.event_type == WebhookEventType.MESSAGE

    def is_instagram_channel(self) -> bool:
        """Check if this is from Instagram channel."""
        return self.channel_type == ChannelType.INSTAGRAM

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class WebhookEventBuilder:
    """Builder class for creating WebhookEvent instances from different channel formats."""

    @staticmethod
    def from_line_event(bot_id: int, event_data: dict[str, Any]) -> WebhookEvent:
        """Create WebhookEvent from LINE webhook event data.

        Args:
            bot_id: The bot ID
            event_data: Raw LINE webhook event data

        Returns:
            WebhookEvent instance
        """
        event_type = WebhookEventType(event_data.get("type", "message"))
        user_id = event_data.get("source", {}).get("userId", "")
        message_content = None

        if event_type == WebhookEventType.MESSAGE:
            message_content = event_data.get("message", {}).get("text", "")

        return WebhookEvent(
            event_type=event_type,
            channel_type=ChannelType.LINE,
            bot_id=bot_id,
            user_id=user_id,
            message_content=message_content,
            ig_story_id=None,  # LINE doesn't have IG story context
            timestamp=datetime.fromtimestamp(event_data.get("timestamp", 0) / 1000),
            reply_token=event_data.get("replyToken"),
            raw_event=event_data,
        )

    @staticmethod
    def from_facebook_event(bot_id: int, event_data: dict[str, Any]) -> WebhookEvent:
        """Create WebhookEvent from Facebook webhook event data.

        Args:
            bot_id: The bot ID
            event_data: Raw Facebook webhook event data

        Returns:
            WebhookEvent instance
        """
        # Facebook event structure varies, this is a simplified example
        messaging = event_data.get("messaging", [{}])[0]
        event_type = WebhookEventType.MESSAGE if "message" in messaging else WebhookEventType.POSTBACK
        user_id = messaging.get("sender", {}).get("id", "")
        message_content = messaging.get("message", {}).get("text", "")

        return WebhookEvent(
            event_type=event_type,
            channel_type=ChannelType.FACEBOOK,
            bot_id=bot_id,
            user_id=user_id,
            message_content=message_content,
            ig_story_id=None,  # Facebook doesn't have IG story context
            timestamp=datetime.fromtimestamp(messaging.get("timestamp", 0) / 1000),
            reply_token=None,  # Facebook doesn't use reply tokens
            raw_event=event_data,
        )

    @staticmethod
    def from_instagram_event(bot_id: int, event_data: dict[str, Any]) -> WebhookEvent:
        """Create WebhookEvent from Instagram webhook event data.

        Args:
            bot_id: The bot ID
            event_data: Raw Instagram webhook event data

        Returns:
            WebhookEvent instance
        """
        # Instagram event structure varies, this is a simplified example
        messaging = event_data.get("messaging", [{}])[0]
        event_type = WebhookEventType.MESSAGE if "message" in messaging else WebhookEventType.POSTBACK
        user_id = messaging.get("sender", {}).get("id", "")
        message_content = messaging.get("message", {}).get("text", "")

        # Extract IG story ID from message context (if available)
        ig_story_id = None
        message_obj = messaging.get("message", {})
        if "story" in message_obj:
            ig_story_id = message_obj["story"].get("id")

        return WebhookEvent(
            event_type=event_type,
            channel_type=ChannelType.INSTAGRAM,
            bot_id=bot_id,
            user_id=user_id,
            message_content=message_content,
            ig_story_id=ig_story_id,
            timestamp=datetime.fromtimestamp(messaging.get("timestamp", 0) / 1000),
            reply_token=None,  # Instagram doesn't use reply tokens
            raw_event=event_data,
        )
