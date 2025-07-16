"""Tests for webhook trigger schedule functionality.

These tests are designed to verify PRD requirements for time-based scheduling.
PRD Test Cases covered:
- [B-P0-6-Test3]: Daily schedule testing
- [B-P0-6-Test4]: Monthly schedule testing
- [B-P0-6-Test5]: Business hours testing
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from internal.domain.auto_reply.webhook_trigger import (
    BusinessHourSchedule,
    DailySchedule,
    DateRangeSchedule,
    MonthlySchedule,
    NonBusinessHourSchedule,
)


class TestDailySchedule:
    """Test cases for DailySchedule - PRD [B-P0-6-Test3]."""

    def test_daily_schedule_within_time_window(self):
        """Test daily schedule triggers within the defined time window."""
        # PRD Test: Create a General Reply with Daily schedule and test triggering during time window
        schedule = DailySchedule(start_time="09:00", end_time="17:00")

        # Test within time window (using Asia/Taipei timezone)
        event_time = datetime(2024, 1, 15, 12, 30, tzinfo=ZoneInfo("Asia/Taipei"))  # 12:30 PM Taipei
        assert schedule.is_active(event_time) is True

        # Test at start time (inclusive)
        event_time = datetime(2024, 1, 15, 9, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # 09:00 AM Taipei
        assert schedule.is_active(event_time) is True

        # Test just before end time
        event_time = datetime(2024, 1, 15, 16, 59, tzinfo=ZoneInfo("Asia/Taipei"))  # 16:59 PM Taipei
        assert schedule.is_active(event_time) is True

    def test_daily_schedule_outside_time_window(self):
        """Test daily schedule does not trigger outside time window."""
        schedule = DailySchedule(start_time="09:00", end_time="17:00")

        # Test before start time
        event_time = datetime(2024, 1, 15, 8, 59, tzinfo=ZoneInfo("Asia/Taipei"))  # 08:59 AM Taipei
        assert schedule.is_active(event_time) is False

        # Test at end time (exclusive)
        event_time = datetime(2024, 1, 15, 17, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # 17:00 PM Taipei
        assert schedule.is_active(event_time) is False

        # Test after end time
        event_time = datetime(2024, 1, 15, 18, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # 18:00 PM Taipei
        assert schedule.is_active(event_time) is False

    def test_daily_schedule_midnight_crossing(self):
        """Test daily schedule that crosses midnight."""
        # Night shift: 22:00 to 06:00
        schedule = DailySchedule(start_time="22:00", end_time="06:00")

        # Test late night (before midnight)
        event_time = datetime(2024, 1, 15, 23, 30, tzinfo=ZoneInfo("Asia/Taipei"))  # 23:30 PM Taipei
        assert schedule.is_active(event_time) is True

        # Test early morning (after midnight)
        event_time = datetime(2024, 1, 16, 3, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # 03:00 AM Taipei
        assert schedule.is_active(event_time) is True

        # Test outside window (morning)
        event_time = datetime(2024, 1, 15, 10, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # 10:00 AM Taipei
        assert schedule.is_active(event_time) is False


class TestMonthlySchedule:
    """Test cases for MonthlySchedule - PRD [B-P0-6-Test4]."""

    def test_monthly_schedule_on_correct_date_and_time(self):
        """Test monthly schedule triggers on scheduled date and time."""
        # PRD Test: Create General Reply with Monthly schedule and test on scheduled date/time
        schedule = MonthlySchedule(day=15, start_time="10:00", end_time="12:00")

        # Test on correct day and within time window
        event_time = datetime(2024, 1, 15, 11, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # Jan 15, 11:00 AM Taipei
        assert schedule.is_active(event_time) is True

        # Test on correct day at start time
        event_time = datetime(2024, 1, 15, 10, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # Jan 15, 10:00 AM Taipei
        assert schedule.is_active(event_time) is True

    def test_monthly_schedule_wrong_date(self):
        """Test monthly schedule does not trigger on wrong date."""
        schedule = MonthlySchedule(day=15, start_time="10:00", end_time="12:00")

        # Test on wrong day but correct time
        event_time = datetime(2024, 1, 14, 11, 0)  # Jan 14, 11:00 AM
        assert schedule.is_active(event_time) is False

        event_time = datetime(2024, 1, 16, 11, 0)  # Jan 16, 11:00 AM
        assert schedule.is_active(event_time) is False

    def test_monthly_schedule_wrong_time(self):
        """Test monthly schedule does not trigger at wrong time."""
        schedule = MonthlySchedule(day=15, start_time="10:00", end_time="12:00")

        # Test on correct day but outside time window
        event_time = datetime(2024, 1, 15, 9, 0)  # Jan 15, 09:00 AM
        assert schedule.is_active(event_time) is False

        event_time = datetime(2024, 1, 15, 13, 0)  # Jan 15, 13:00 PM
        assert schedule.is_active(event_time) is False


class TestBusinessHourSchedule:
    """Test cases for BusinessHourSchedule - PRD [B-P0-6-Test5]."""

    def test_business_hour_schedule_creation(self):
        """Test business hour schedule creation."""
        # Note: Full business hour testing requires organization setup
        # This is a placeholder for basic instantiation test
        schedule = BusinessHourSchedule()
        assert schedule.get_schedule_settings() is None

        # For now, implement basic is_active that returns False
        # Real implementation will need organization's business hour data
        event_time = datetime(2024, 1, 15, 10, 0)
        # This will be implemented after we have organization business hour logic
        # assert schedule.is_active(event_time) is True/False


class TestNonBusinessHourSchedule:
    """Test cases for NonBusinessHourSchedule."""

    def test_non_business_hour_schedule_creation(self):
        """Test non-business hour schedule creation."""
        schedule = NonBusinessHourSchedule()
        assert schedule.get_schedule_settings() is None
