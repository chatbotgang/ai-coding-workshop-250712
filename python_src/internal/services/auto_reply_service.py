"""Auto-reply service layer for trigger validation and processing."""

from typing import Any

import structlog

from internal.domain.auto_reply.auto_reply import AutoReply
from internal.domain.auto_reply.trigger_validator import TriggerValidationResult, TriggerValidator
from internal.domain.auto_reply.webhook_event import WebhookEvent, WebhookEventBuilder
from internal.domain.organization.business_hour import BusinessHour


class AutoReplyService:
    """Service for handling auto-reply trigger validation and processing."""

    def __init__(self, business_hours: list[BusinessHour] | None = None, organization_timezone: str | None = None):
        """Initialize the auto-reply service.

        Args:
            business_hours: Organization's business hour configuration
            organization_timezone: Organization's timezone (e.g., 'Asia/Taipei', 'UTC')
        """
        self.validator = TriggerValidator(business_hours=business_hours, organization_timezone=organization_timezone)
        self.logger = structlog.get_logger(__name__)

    def validate_webhook_event(
        self, triggers: list[AutoReply], bot_id: int, event_data: dict[str, Any], channel_type: str = "line"
    ) -> TriggerValidationResult:
        """Validate a webhook event against auto-reply triggers.

        Args:
            triggers: List of auto-reply triggers to evaluate
            bot_id: Bot ID from the webhook event
            event_data: Raw webhook event data
            channel_type: Channel type (line, facebook, instagram)

        Returns:
            TriggerValidationResult with matched trigger and validation status

        Raises:
            ValueError: If event data is invalid or channel type is unsupported
        """
        try:
            # Create webhook event from raw data
            event = self._create_webhook_event(bot_id, event_data, channel_type)

            # Log the validation attempt
            self.logger.info(
                "Starting auto-reply validation",
                bot_id=bot_id,
                event_type=event.event_type,
                channel_type=event.channel_type,
                has_ig_story=event.has_ig_story_context(),
                trigger_count=len(triggers),
            )

            # Validate triggers
            result = self.validator.validate_trigger(triggers, event)

            return result

        except Exception as e:
            self.logger.error(
                "Error during auto-reply validation", error=str(e), bot_id=bot_id, channel_type=channel_type
            )
            raise

    def _create_webhook_event(self, bot_id: int, event_data: dict[str, Any], channel_type: str) -> WebhookEvent:
        """Create a WebhookEvent from raw event data.

        Args:
            bot_id: Bot ID
            event_data: Raw webhook event data
            channel_type: Channel type

        Returns:
            WebhookEvent instance

        Raises:
            ValueError: If channel type is unsupported or event data is invalid
        """
        try:
            if channel_type.lower() == "line":
                return WebhookEventBuilder.from_line_event(bot_id, event_data)
            elif channel_type.lower() == "facebook":
                return WebhookEventBuilder.from_facebook_event(bot_id, event_data)
            elif channel_type.lower() == "instagram":
                return WebhookEventBuilder.from_instagram_event(bot_id, event_data)
            else:
                raise ValueError(f"Unsupported channel type: {channel_type}")
        except Exception as e:
            self.logger.error("Failed to create webhook event", error=str(e), bot_id=bot_id, channel_type=channel_type)
            raise ValueError(f"Invalid event data for {channel_type}: {str(e)}")

    def get_matching_triggers_by_priority(
        self, triggers: list[AutoReply], bot_id: int, event_data: dict[str, Any], channel_type: str = "line"
    ) -> list[AutoReply]:
        """Get all triggers that would match, sorted by priority.

        This is useful for debugging and analytics to see which triggers
        would match without executing the first-match-wins logic.

        Args:
            triggers: List of auto-reply triggers to evaluate
            bot_id: Bot ID from the webhook event
            event_data: Raw webhook event data
            channel_type: Channel type

        Returns:
            List of matching triggers sorted by priority (highest first)
        """
        try:
            event = self._create_webhook_event(bot_id, event_data, channel_type)

            # Filter to only active triggers for this bot
            active_triggers = [t for t in triggers if t.is_active()]

            # Check each trigger individually
            matching_triggers = []
            for trigger in active_triggers:
                result = self.validator._evaluate_single_trigger(trigger, event)
                if result.has_match():
                    matching_triggers.append(trigger)

            # Sort by priority (lowest number = highest priority)
            matching_triggers.sort(key=lambda t: t.get_priority_level())
            return matching_triggers

        except Exception as e:
            self.logger.error("Error getting matching triggers", error=str(e), bot_id=bot_id, channel_type=channel_type)
            return []


class AutoReplyValidationError(Exception):
    """Custom exception for auto-reply validation errors."""

    def __init__(self, message: str, trigger_id: int | None = None, bot_id: int | None = None):
        super().__init__(message)
        self.trigger_id = trigger_id
        self.bot_id = bot_id


# Service factory for dependency injection
def create_auto_reply_service(
    business_hours: list[BusinessHour] | None = None, organization_timezone: str | None = None
) -> AutoReplyService:
    """Create an AutoReplyService instance.

    Args:
        business_hours: Organization's business hour configuration
        organization_timezone: Organization's timezone (e.g., 'Asia/Taipei', 'UTC')

    Returns:
        AutoReplyService instance
    """
    return AutoReplyService(business_hours=business_hours, organization_timezone=organization_timezone)
