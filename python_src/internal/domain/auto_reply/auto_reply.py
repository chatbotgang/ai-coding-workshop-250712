"""Auto Reply domain models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

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
    trigger_schedule_type: WebhookTriggerScheduleType | None = None
    trigger_schedule_settings: WebhookTriggerScheduleSettings | None = None
    ig_story_ids: list[str] | None = None  # IG Story specific configuration
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
