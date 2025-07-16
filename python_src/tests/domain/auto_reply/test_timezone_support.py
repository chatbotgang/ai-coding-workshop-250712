"""Tests for timezone support in auto-reply triggers.

These tests verify that timezone-aware datetime handling works correctly
across different timezones as required by Legacy KB specifications.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyEventType, AutoReplyStatus
from internal.domain.auto_reply.validate_trigger import validate_trigger
from internal.domain.auto_reply.webhook_trigger import (
    BusinessHourSchedule,
    DailySchedule,
    MonthlySchedule,
    NonBusinessHourSchedule,
    WebhookTriggerEventType,
    WebhookTriggerScheduleSettings,
    WebhookTriggerSetting,
)


class TestTimezoneAwareness:
    """Test timezone-aware datetime handling."""

    def test_daily_schedule_timezone_conversion_utc_to_taipei(self):
        """Test daily schedule with UTC input converted to Taipei timezone."""
        # Create daily schedule: 09:00-17:00 Taipei time
        daily_schedule = DailySchedule(start_time="09:00", end_time="17:00")

        # UTC time that corresponds to 14:00 Taipei (UTC+8)
        utc_time = datetime(2024, 1, 15, 6, 0, 0, tzinfo=ZoneInfo("UTC"))  # 06:00 UTC

        # Should be active (06:00 UTC = 14:00 Taipei)
        assert daily_schedule.is_active(utc_time, "Asia/Taipei") is True

        # UTC time that corresponds to 08:00 Taipei (before business hours)
        utc_early = datetime(2024, 1, 15, 0, 0, 0, tzinfo=ZoneInfo("UTC"))  # 00:00 UTC

        # Should NOT be active (00:00 UTC = 08:00 Taipei, before 09:00)
        assert daily_schedule.is_active(utc_early, "Asia/Taipei") is False

    def test_daily_schedule_different_timezones(self):
        """Test daily schedule with different organization timezones."""
        daily_schedule = DailySchedule(start_time="09:00", end_time="17:00")

        # Same UTC time, different organization timezones
        utc_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=ZoneInfo("UTC"))  # 10:00 UTC

        # Test Taipei timezone (UTC+8): 10:00 UTC = 18:00 Taipei (outside hours)
        assert daily_schedule.is_active(utc_time, "Asia/Taipei") is False

        # Test New York timezone (UTC-5): 10:00 UTC = 05:00 EST (outside hours)
        assert daily_schedule.is_active(utc_time, "America/New_York") is False

        # Test London timezone (UTC+0): 10:00 UTC = 10:00 London (within hours)
        assert daily_schedule.is_active(utc_time, "Europe/London") is True

    def test_monthly_schedule_timezone_conversion(self):
        """Test monthly schedule with timezone conversion."""
        # Monthly schedule: 15th of month, 14:00-16:00
        monthly_schedule = MonthlySchedule(day=15, start_time="14:00", end_time="16:00")

        # UTC time on 15th that corresponds to 15:00 Taipei
        utc_time = datetime(2024, 3, 15, 7, 0, 0, tzinfo=ZoneInfo("UTC"))  # 07:00 UTC

        # Should be active (07:00 UTC = 15:00 Taipei on 15th)
        assert monthly_schedule.is_active(utc_time, "Asia/Taipei") is True

        # UTC time on 14th that corresponds to 15:00 Taipei on 15th (crosses date)
        utc_cross_date = datetime(2024, 3, 14, 23, 0, 0, tzinfo=ZoneInfo("UTC"))  # 23:00 UTC on 14th

        # Should NOT be active (wrong date in Taipei timezone)
        assert monthly_schedule.is_active(utc_cross_date, "Asia/Taipei") is False

    def test_naive_datetime_assumes_utc(self):
        """Test that naive datetime objects are assumed to be UTC."""
        daily_schedule = DailySchedule(start_time="09:00", end_time="17:00")

        # Naive datetime (no timezone info)
        naive_time = datetime(2024, 1, 15, 6, 0, 0)  # Assumed UTC

        # Should be active (06:00 assumed UTC = 14:00 Taipei)
        assert daily_schedule.is_active(naive_time, "Asia/Taipei") is True


class TestBusinessHourTimezone:
    """Test business hour schedules with timezone support."""

    def test_business_hour_timezone_conversion(self):
        """Test business hours with timezone-aware conversion."""
        # Business hours configuration: Monday 09:00-17:00
        business_hours = [{"day_of_week": 0, "start_time": "09:00", "end_time": "17:00", "is_active": True}]  # Monday

        business_schedule = BusinessHourSchedule(business_hours=business_hours)

        # UTC time on Monday that corresponds to 14:00 Taipei
        utc_monday = datetime(2024, 1, 15, 6, 0, 0, tzinfo=ZoneInfo("UTC"))  # Monday 06:00 UTC

        # Should be active (06:00 UTC = 14:00 Taipei on Monday)
        assert business_schedule.is_active(utc_monday, "Asia/Taipei") is True

        # UTC time on Sunday that corresponds to 14:00 Taipei on Monday (crosses date)
        utc_sunday = datetime(2024, 1, 14, 22, 0, 0, tzinfo=ZoneInfo("UTC"))  # Sunday 22:00 UTC

        # Should NOT be active (wrong day in Taipei timezone)
        assert business_schedule.is_active(utc_sunday, "Asia/Taipei") is False

    def test_non_business_hour_timezone(self):
        """Test non-business hours (inverse of business hours)."""
        business_hours = [{"day_of_week": 0, "start_time": "09:00", "end_time": "17:00", "is_active": True}]  # Monday

        non_business_schedule = NonBusinessHourSchedule(business_hours=business_hours)

        # UTC time on Monday during business hours
        utc_business = datetime(2024, 1, 15, 6, 0, 0, tzinfo=ZoneInfo("UTC"))  # Monday 14:00 Taipei

        # Should NOT be active (within business hours)
        assert non_business_schedule.is_active(utc_business, "Asia/Taipei") is False

        # UTC time on Monday outside business hours
        utc_non_business = datetime(2024, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))  # Monday 20:00 Taipei

        # Should be active (outside business hours)
        assert non_business_schedule.is_active(utc_non_business, "Asia/Taipei") is True


class TestValidateTriggerTimezone:
    """Test validate_trigger function with timezone support."""

    def test_validate_trigger_with_organization_timezone(self):
        """Test validate_trigger respects organization timezone."""
        # Create time-based auto-reply with daily schedule
        daily_schedule = DailySchedule(start_time="09:00", end_time="17:00")
        schedule_settings = WebhookTriggerScheduleSettings(schedules=[daily_schedule])

        time_auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="Timezone Test Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=1,
            keywords=None,
            trigger_schedule_type="daily",
            trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="Timezone Test Trigger",
            event_type=WebhookTriggerEventType.TIME,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # UTC time that corresponds to 14:00 Taipei (within hours)
        utc_time = datetime(2024, 1, 15, 6, 0, 0, tzinfo=ZoneInfo("UTC"))

        result = validate_trigger(
            [trigger_setting], {1: time_auto_reply}, "any message", utc_time, organization_timezone="Asia/Taipei"
        )

        assert result is not None
        assert result.auto_reply_id == 1

        # UTC time that corresponds to 08:00 Taipei (outside hours)
        utc_early = datetime(2024, 1, 15, 0, 0, 0, tzinfo=ZoneInfo("UTC"))

        result_early = validate_trigger(
            [trigger_setting], {1: time_auto_reply}, "any message", utc_early, organization_timezone="Asia/Taipei"
        )

        assert result_early is None

    def test_validate_trigger_different_timezones(self):
        """Test validate_trigger with different organization timezones."""
        daily_schedule = DailySchedule(start_time="09:00", end_time="17:00")
        schedule_settings = WebhookTriggerScheduleSettings(schedules=[daily_schedule])

        time_auto_reply = AutoReply(
            id=1,
            organization_id=1,
            name="Multi-Timezone Reply",
            status=AutoReplyStatus.ACTIVE,
            event_type=AutoReplyEventType.TIME,
            priority=1,
            keywords=None,
            trigger_schedule_type="daily",
            trigger_schedule_settings=schedule_settings,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        trigger_setting = WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="Multi-Timezone Trigger",
            event_type=WebhookTriggerEventType.TIME,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Same UTC time, test different organization timezones
        utc_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=ZoneInfo("UTC"))  # 10:00 UTC

        # Test Taipei timezone (UTC+8): 10:00 UTC = 18:00 Taipei (outside hours)
        result_taipei = validate_trigger(
            [trigger_setting], {1: time_auto_reply}, "any message", utc_time, organization_timezone="Asia/Taipei"
        )
        assert result_taipei is None

        # Test London timezone (UTC+0): 10:00 UTC = 10:00 London (within hours)
        result_london = validate_trigger(
            [trigger_setting], {1: time_auto_reply}, "any message", utc_time, organization_timezone="Europe/London"
        )
        assert result_london is not None
        assert result_london.auto_reply_id == 1


class TestCrossMidnightTimezone:
    """Test midnight crossing scenarios with timezone conversion."""

    def test_daily_schedule_midnight_crossing_with_timezone(self):
        """Test daily schedule midnight crossing with timezone conversion."""
        # Night shift schedule: 22:00-06:00
        night_schedule = DailySchedule(start_time="22:00", end_time="06:00")

        # UTC time corresponding to 23:00 Taipei (during night shift)
        utc_night = datetime(2024, 1, 15, 15, 0, 0, tzinfo=ZoneInfo("UTC"))  # 15:00 UTC = 23:00 Taipei

        assert night_schedule.is_active(utc_night, "Asia/Taipei") is True

        # UTC time corresponding to 03:00 Taipei (during night shift, next day)
        utc_early_morning = datetime(2024, 1, 15, 19, 0, 0, tzinfo=ZoneInfo("UTC"))  # 19:00 UTC = 03:00 Taipei next day

        assert night_schedule.is_active(utc_early_morning, "Asia/Taipei") is True

        # UTC time corresponding to 10:00 Taipei (outside night shift)
        utc_morning = datetime(2024, 1, 15, 2, 0, 0, tzinfo=ZoneInfo("UTC"))  # 02:00 UTC = 10:00 Taipei

        assert night_schedule.is_active(utc_morning, "Asia/Taipei") is False
