"""Trigger validation logic for auto-reply system."""

from datetime import datetime, time
from zoneinfo import ZoneInfo

from internal.domain.auto_reply.auto_reply import AutoReply
from internal.domain.auto_reply.webhook_event import WebhookEvent
from internal.domain.auto_reply.webhook_trigger import (
    DailySchedule,
    DateRangeSchedule,
    MonthlySchedule,
    WebhookTriggerScheduleType,
)
from internal.domain.organization.business_hour import BusinessHour


class TriggerValidationResult:
    """Result of trigger validation."""

    def __init__(self, matched_trigger: AutoReply | None = None, is_schedule_match: bool = False):
        self.matched_trigger = matched_trigger
        self.is_schedule_match = is_schedule_match

    def has_match(self) -> bool:
        """Check if validation found a matching trigger."""
        return self.matched_trigger is not None

    def is_valid_match(self) -> bool:
        """Check if validation found a valid trigger that should execute."""
        return self.has_match() and self.is_schedule_match


class TriggerValidator:
    """Validator class for auto-reply triggers with 4-level priority system."""

    def __init__(self, business_hours: list[BusinessHour] | None = None, organization_timezone: str | None = None):
        """Initialize trigger validator.

        Args:
            business_hours: List of business hour configurations for the organization
            organization_timezone: Organization's timezone (e.g., 'Asia/Taipei', 'UTC')
        """
        self.business_hours = business_hours or []
        self.organization_timezone = organization_timezone

    def _convert_to_organization_timezone(self, event_time: datetime) -> datetime:
        """Convert event time to organization's timezone.

        Args:
            event_time: Event timestamp (may be in UTC or other timezone)

        Returns:
            Event time converted to organization's timezone
        """
        if not self.organization_timezone:
            # If no timezone configured, return as-is
            return event_time

        try:
            # If event_time is naive (no timezone), assume UTC
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=ZoneInfo("UTC"))

            # Convert to organization's timezone
            org_tz = ZoneInfo(self.organization_timezone)
            return event_time.astimezone(org_tz)
        except Exception:
            # If timezone conversion fails, return original time
            return event_time

    def validate_trigger(self, triggers: list[AutoReply], event: WebhookEvent) -> TriggerValidationResult:
        """Validate triggers against webhook event with 4-level priority system.

        Priority levels:
        1. IG Story Keyword (highest priority)
        2. IG Story General
        3. General Keyword
        4. General Time-based (lowest priority)

        Args:
            triggers: List of auto-reply triggers to evaluate
            event: Webhook event to match against

        Returns:
            TriggerValidationResult with matched trigger and schedule validation status
        """
        # Only process MESSAGE events
        if not event.is_message_event():
            return TriggerValidationResult()

        # Filter active triggers for this bot
        active_triggers = [t for t in triggers if t.is_active()]
        bot_triggers = [t for t in active_triggers if self._is_trigger_for_bot(t, event.bot_id)]

        # Sort triggers by priority (lowest number = highest priority)
        sorted_triggers = sorted(bot_triggers, key=lambda t: t.get_priority_level())

        # Evaluate triggers in priority order
        for trigger in sorted_triggers:
            result = self._evaluate_single_trigger(trigger, event)
            if result.has_match():
                return result

        return TriggerValidationResult()

    def _is_trigger_for_bot(self, trigger: AutoReply, bot_id: int) -> bool:
        """Check if trigger applies to the given bot.

        This would typically check webhook trigger settings associated with the trigger.
        For now, we assume all triggers apply to all bots in the organization.

        Args:
            trigger: AutoReply trigger to check
            bot_id: Bot ID from the webhook event

        Returns:
            True if trigger applies to bot, False otherwise
        """
        # TODO: Implement bot-specific trigger filtering based on WebhookTriggerSettings
        return True

    def _evaluate_single_trigger(self, trigger: AutoReply, event: WebhookEvent) -> TriggerValidationResult:
        """Evaluate a single trigger against the webhook event.

        Args:
            trigger: AutoReply trigger to evaluate
            event: Webhook event to match against

        Returns:
            TriggerValidationResult with match status
        """
        # Check IG Story context matching
        if not trigger.matches_ig_story(event.ig_story_id):
            return TriggerValidationResult()

        # Check keyword matching (for keyword triggers)
        if trigger.is_keyword_trigger():
            if not event.has_message_content():
                return TriggerValidationResult()

            # At this point we know message_content is not None due to has_message_content() check
            if not trigger.matches_keyword(event.message_content or ""):
                return TriggerValidationResult()

        # Check schedule matching (for time-based triggers)
        schedule_match = True
        if trigger.is_time_trigger():
            schedule_match = self._validate_schedule(trigger, event.timestamp)

        return TriggerValidationResult(matched_trigger=trigger, is_schedule_match=schedule_match)

    def _validate_schedule(self, trigger: AutoReply, event_time: datetime) -> bool:
        """Validate if trigger's schedule matches the event time.

        Args:
            trigger: AutoReply trigger with schedule configuration
            event_time: Timestamp of the webhook event

        Returns:
            True if schedule matches, False otherwise
        """
        if trigger.trigger_schedule_type is None:
            return True

        if trigger.trigger_schedule_type == WebhookTriggerScheduleType.DAILY:
            return self._validate_daily_schedule(trigger, event_time)
        elif trigger.trigger_schedule_type == WebhookTriggerScheduleType.MONTHLY:
            return self._validate_monthly_schedule(trigger, event_time)
        elif trigger.trigger_schedule_type == WebhookTriggerScheduleType.BUSINESS_HOUR:
            return self._validate_business_hour_schedule(trigger, event_time)
        elif trigger.trigger_schedule_type == WebhookTriggerScheduleType.NON_BUSINESS_HOUR:
            return self._validate_non_business_hour_schedule(trigger, event_time)
        elif trigger.trigger_schedule_type == WebhookTriggerScheduleType.DATE_RANGE:
            return self._validate_date_range_schedule(trigger, event_time)

        return False

    def _validate_daily_schedule(self, trigger: AutoReply, event_time: datetime) -> bool:
        """Validate daily schedule against event time.

        Args:
            trigger: AutoReply trigger with daily schedule
            event_time: Timestamp of the webhook event

        Returns:
            True if within daily schedule, False otherwise
        """
        if not trigger.trigger_schedule_settings or not trigger.trigger_schedule_settings.schedules:
            return False

        # Convert event time to organization's timezone for proper schedule comparison
        org_event_time = self._convert_to_organization_timezone(event_time)
        event_time_only = org_event_time.time()

        for schedule in trigger.trigger_schedule_settings.schedules:
            if isinstance(schedule, DailySchedule):
                start_time = time.fromisoformat(schedule.start_time)
                end_time = time.fromisoformat(schedule.end_time)

                # Handle midnight crossing case (e.g., 22:00 to 06:00)
                if start_time > end_time:
                    # Schedule crosses midnight: check if time is after start OR before end
                    if event_time_only >= start_time or event_time_only <= end_time:
                        return True
                else:
                    # Normal case: schedule within same day
                    if start_time <= event_time_only <= end_time:
                        return True

        return False

    def _validate_monthly_schedule(self, trigger: AutoReply, event_time: datetime) -> bool:
        """Validate monthly schedule against event time.

        Args:
            trigger: AutoReply trigger with monthly schedule
            event_time: Timestamp of the webhook event

        Returns:
            True if within monthly schedule, False otherwise
        """
        if not trigger.trigger_schedule_settings or not trigger.trigger_schedule_settings.schedules:
            return False

        # Convert event time to organization's timezone for proper schedule comparison
        org_event_time = self._convert_to_organization_timezone(event_time)
        event_day = org_event_time.day
        event_time_only = org_event_time.time()

        for schedule in trigger.trigger_schedule_settings.schedules:
            if isinstance(schedule, MonthlySchedule):
                if schedule.day == event_day:
                    start_time = time.fromisoformat(schedule.start_time)
                    end_time = time.fromisoformat(schedule.end_time)

                    # Handle midnight crossing case (e.g., 22:00 to 06:00)
                    if start_time > end_time:
                        # Schedule crosses midnight: check if time is after start OR before end
                        if event_time_only >= start_time or event_time_only <= end_time:
                            return True
                    else:
                        # Normal case: schedule within same day
                        if start_time <= event_time_only <= end_time:
                            return True

        return False

    def _validate_business_hour_schedule(self, trigger: AutoReply, event_time: datetime) -> bool:
        """Validate business hour schedule against event time.

        Args:
            trigger: AutoReply trigger with business hour schedule
            event_time: Timestamp of the webhook event

        Returns:
            True if within business hours, False otherwise
        """
        if not self.business_hours:
            return False

        # Convert event time to organization's timezone for proper business hour comparison
        org_event_time = self._convert_to_organization_timezone(event_time)
        weekday = org_event_time.weekday()  # Monday = 0, Sunday = 6
        event_time_only = org_event_time.time()

        for business_hour in self.business_hours:
            if business_hour.is_day_active(weekday):
                # Handle midnight crossing case for business hours
                if business_hour.start_time > business_hour.end_time:
                    # Business hours cross midnight: check if time is after start OR before end
                    if event_time_only >= business_hour.start_time or event_time_only <= business_hour.end_time:
                        return True
                else:
                    # Normal case: business hours within same day
                    if business_hour.start_time <= event_time_only <= business_hour.end_time:
                        return True

        return False

    def _validate_non_business_hour_schedule(self, trigger: AutoReply, event_time: datetime) -> bool:
        """Validate non-business hour schedule against event time.

        Args:
            trigger: AutoReply trigger with non-business hour schedule
            event_time: Timestamp of the webhook event

        Returns:
            True if outside business hours, False otherwise
        """
        # Non-business hours is the inverse of business hours
        return not self._validate_business_hour_schedule(trigger, event_time)

    def _validate_date_range_schedule(self, trigger: AutoReply, event_time: datetime) -> bool:
        """Validate date range schedule against event time.

        Args:
            trigger: AutoReply trigger with date range schedule
            event_time: Timestamp of the webhook event

        Returns:
            True if within date range, False otherwise
        """
        if not trigger.trigger_schedule_settings or not trigger.trigger_schedule_settings.schedules:
            return False

        # Convert event time to organization's timezone for proper date comparison
        org_event_time = self._convert_to_organization_timezone(event_time)
        event_date = org_event_time.date()

        for schedule in trigger.trigger_schedule_settings.schedules:
            if isinstance(schedule, DateRangeSchedule):
                start_date = datetime.fromisoformat(schedule.start_date).date()
                end_date = datetime.fromisoformat(schedule.end_date).date()

                if start_date <= event_date <= end_date:
                    return True

        return False
