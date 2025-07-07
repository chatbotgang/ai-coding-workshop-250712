"""Auto Reply domain models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from internal.domain.auto_reply.webhook_trigger import WebhookTriggerScheduleSettings, WebhookTriggerScheduleType


class AutoReplyStatus(StrEnum):
    """Auto reply status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AutoReplyEventType(StrEnum):
    """Auto reply event type enumeration."""

    MESSAGE = "message"
    POSTBACK = "postback"
    FOLLOW = "follow"
    BEACON = "beacon"
    TIME = "time"
    KEYWORD = "keyword"
    DEFAULT = "default"


class AutoReply(BaseModel):
    """Auto reply domain model.

    Represents an omnichannel rule that associates several WebhookTriggerSetting instances.
    It defines the high-level auto-reply configuration for an organization.
    """

    id: int
    organization_id: int
    name: str
    status: AutoReplyStatus
    event_type: AutoReplyEventType
    priority: int
    keywords: list[str] | None = None
    ig_story_ids: list[str] | None = None
    trigger_schedule_type: WebhookTriggerScheduleType | None = None
    trigger_schedule_settings: WebhookTriggerScheduleSettings | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(use_enum_values=True)

    def is_active(self) -> bool:
        """Check if the auto reply is active."""
        return self.status == AutoReplyStatus.ACTIVE

    def get_priority_level(self) -> int:
        """Get the priority level for this trigger.

        Returns:
            Priority level (1-4, where 1 is highest priority)
        """
        if self.is_ig_story_specific():
            if self.is_keyword_trigger():
                return 1  # IG Story Keyword (highest priority)
            else:
                return 2  # IG Story General
        else:
            if self.is_keyword_trigger():
                return 3  # General Keyword
            else:
                return 4  # General Time-based (lowest priority)

    def is_ig_story_specific(self) -> bool:
        """Check if this trigger is specific to IG Story contexts."""
        return self.ig_story_ids is not None and len(self.ig_story_ids) > 0

    def matches_ig_story(self, ig_story_id: str | None) -> bool:
        """Check if this trigger matches the given IG Story ID.

        Implements exclusion logic:
        - If IG Story context exists: only IG Story specific triggers match
        - If no IG Story context: only general (non-IG Story) triggers match

        Args:
            ig_story_id: The IG Story ID to check

        Returns:
            True if trigger matches the IG Story context
        """
        # If there's an IG Story context
        if ig_story_id is not None:
            # Only IG Story specific triggers should match
            if not self.is_ig_story_specific():
                return False  # General triggers excluded when IG Story context exists
            # Check if the provided story ID matches any of the trigger's story IDs
            return ig_story_id in (self.ig_story_ids or [])

        # If there's no IG Story context
        else:
            # Only general triggers should match (IG Story specific triggers excluded)
            return not self.is_ig_story_specific()

    def is_keyword_trigger(self) -> bool:
        """Check if this is a keyword-based trigger."""
        return self.event_type == AutoReplyEventType.KEYWORD and self.keywords is not None

    def is_time_trigger(self) -> bool:
        """Check if this is a time-based trigger."""
        return self.event_type == AutoReplyEventType.TIME

    def matches_keyword(self, message_content: str) -> bool:
        """Check if message content matches any of the trigger keywords.

        Args:
            message_content: The message content to check

        Returns:
            True if message content matches any keyword
        """
        if not self.is_keyword_trigger() or not self.keywords:
            return False

        normalized_content = self.normalize_keyword(message_content)

        for keyword in self.keywords:
            normalized_keyword = self.normalize_keyword(keyword)
            if normalized_content == normalized_keyword:
                return True

        return False

    def normalize_keyword(self, keyword: str) -> str:
        """Normalize keyword for matching (case-insensitive, trimmed).

        Args:
            keyword: The keyword to normalize

        Returns:
            Normalized keyword
        """
        return keyword.strip().lower()
