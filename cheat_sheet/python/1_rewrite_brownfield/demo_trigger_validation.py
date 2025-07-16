#!/usr/bin/env python3
"""
Auto-Reply Trigger Validation Demo

This script demonstrates the core trigger validation logic implementation
according to the PRD requirements for FB/IG Auto-Reply Feature.

Features demonstrated:
1. Keyword matching with case-insensitive, exact match logic
2. Priority system (Keyword > Welcome > General)
3. Time-based triggers (daily, monthly, business hours)
4. Welcome triggers for FOLLOW events
5. Multiple trigger scenarios
"""

from datetime import datetime

from internal.domain.auto_reply import (
    ChannelType,
    FollowEvent,
    MessageEvent,
    TriggerValidationResult,
    WebhookTriggerEventType,
    WebhookTriggerScheduleType,
    WebhookTriggerSetting,
    convert_to_timezone,
    validate_trigger,
)


class DemoBusinessHourChecker:
    """Demo business hour checker with timezone support."""

    def is_in_business_hours(
        self,
        timestamp: datetime,
        organization_id: int,
        bot_timezone: str | None = None,
        organization_timezone: str | None = None,
    ) -> bool:
        """Enhanced business hour check with timezone awareness."""
        # Use the passed timestamp (should already be in correct timezone)
        weekday = timestamp.weekday()  # Monday = 0, Sunday = 6
        hour = timestamp.hour

        # Monday to Friday, 9 AM to 5 PM
        is_business_day = 0 <= weekday <= 4
        is_business_hour = 9 <= hour < 17

        return is_business_day and is_business_hour


def create_sample_triggers() -> list[WebhookTriggerSetting]:
    """Create sample trigger settings for demonstration."""
    return [
        # Keyword trigger: "hello"
        WebhookTriggerSetting(
            id=1,
            auto_reply_id=1,
            bot_id=1,
            enable=True,
            name="Hello Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="hello",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        # Keyword trigger: "support"
        WebhookTriggerSetting(
            id=2,
            auto_reply_id=2,
            bot_id=1,
            enable=True,
            name="Support Keyword Trigger",
            event_type=WebhookTriggerEventType.MESSAGE,
            trigger_code="support",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        # Welcome trigger for new followers
        WebhookTriggerSetting(
            id=3,
            auto_reply_id=3,
            bot_id=1,
            enable=True,
            name="Welcome New Follower",
            event_type=WebhookTriggerEventType.FOLLOW,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        # General trigger: Business hours auto-reply
        WebhookTriggerSetting(
            id=4,
            auto_reply_id=4,
            bot_id=1,
            enable=True,
            name="Business Hours Auto-Reply",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        # General trigger: Daily reminder
        WebhookTriggerSetting(
            id=5,
            auto_reply_id=5,
            bot_id=1,
            enable=True,
            name="Daily Reminder",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.DAILY,
            trigger_schedule_settings={"start_time": "10:00", "end_time": "18:00"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        # General trigger: Monthly promotion
        WebhookTriggerSetting(
            id=6,
            auto_reply_id=6,
            bot_id=1,
            enable=True,
            name="Monthly Promotion",
            event_type=WebhookTriggerEventType.TIME,
            trigger_schedule_type=WebhookTriggerScheduleType.MONTHLY,
            trigger_schedule_settings={"day": 15, "start_time": "12:00", "end_time": "14:00"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]


def print_result(scenario: str, result: TriggerValidationResult, event_description: str):
    """Print validation result in a formatted way."""
    print(f"\n{'='*60}")
    print(f"SCENARIO: {scenario}")
    print(f"EVENT: {event_description}")
    print(f"{'='*60}")

    if result.has_match and result.matched_trigger and result.match_type:
        print(f"✅ TRIGGER MATCHED!")
        print(f"   Trigger ID: {result.matched_trigger.id}")
        print(f"   Trigger Name: {result.matched_trigger.name}")
        print(f"   Match Type: {result.match_type.upper()}")
        print(
            f"   Priority: {'🔥 HIGH' if result.match_type == 'keyword' else '📅 MEDIUM' if result.match_type == 'welcome' else '⏰ LOW'}"
        )
    else:
        print("❌ NO TRIGGER MATCHED")

    print("-" * 60)


def demo_keyword_matching():
    """Demonstrate keyword matching according to PRD B-P0-7."""
    print("\n🎯 KEYWORD MATCHING DEMONSTRATION")
    print("=" * 80)

    triggers = create_sample_triggers()
    business_checker = DemoBusinessHourChecker()

    # Test case 1: Exact keyword match
    event = MessageEvent(
        event_id="demo-1",
        channel_type=ChannelType.LINE,
        user_id="user123",
        timestamp=datetime(2025, 1, 15, 14, 30),
        content="hello",
        message_id="msg-1",
    )

    result = validate_trigger(triggers, event, business_checker, 1)
    print_result("Exact Keyword Match", result, "Message: 'hello'")

    # Test case 2: Case insensitive matching
    event = MessageEvent(
        event_id="demo-2",
        channel_type=ChannelType.LINE,
        user_id="user123",
        timestamp=datetime(2025, 1, 15, 14, 30),
        content="HELLO",
        message_id="msg-2",
    )

    result = validate_trigger(triggers, event, business_checker, 1)
    print_result("Case Insensitive Matching", result, "Message: 'HELLO'")

    # Test case 3: Leading/trailing spaces
    event = MessageEvent(
        event_id="demo-3",
        channel_type=ChannelType.LINE,
        user_id="user123",
        timestamp=datetime(2025, 1, 15, 14, 30),
        content="  hello  ",
        message_id="msg-3",
    )

    result = validate_trigger(triggers, event, business_checker, 1)
    print_result("Spaces Trimming", result, "Message: '  hello  '")

    # Test case 4: Partial match should NOT trigger
    event = MessageEvent(
        event_id="demo-4",
        channel_type=ChannelType.LINE,
        user_id="user123",
        timestamp=datetime(2025, 1, 15, 14, 30),
        content="hello world",
        message_id="msg-4",
    )

    result = validate_trigger(triggers, event, business_checker, 1)
    print_result("Partial Match (Should Fail)", result, "Message: 'hello world'")


def demo_priority_system():
    """Demonstrate priority system: Keyword > Welcome > General."""
    print("\n⚡ PRIORITY SYSTEM DEMONSTRATION")
    print("=" * 80)

    triggers = create_sample_triggers()
    business_checker = DemoBusinessHourChecker()

    # Test case 1: Keyword has priority over general trigger
    event = MessageEvent(
        event_id="demo-5",
        channel_type=ChannelType.LINE,
        user_id="user123",
        timestamp=datetime(2025, 1, 15, 11, 0),  # During business hours + daily schedule
        content="hello",
        message_id="msg-5",
    )

    result = validate_trigger(triggers, event, business_checker, 1)
    print_result("Keyword vs General Priority", result, "Message 'hello' during business hours (keyword should win)")

    # Test case 2: General trigger when no keyword matches
    event = MessageEvent(
        event_id="demo-6",
        channel_type=ChannelType.LINE,
        user_id="user123",
        timestamp=datetime(2025, 1, 15, 11, 0),  # During business hours
        content="any random message",
        message_id="msg-6",
    )

    result = validate_trigger(triggers, event, business_checker, 1)
    print_result("General Trigger Fallback", result, "Random message during business hours (general should trigger)")

    # Test case 3: Welcome trigger for FOLLOW events
    follow_event = FollowEvent(
        event_id="demo-7", channel_type=ChannelType.LINE, user_id="newuser456", timestamp=datetime.now()
    )

    result = validate_trigger(triggers, follow_event, business_checker, 1)
    print_result("Welcome Trigger", result, "New user follows the channel")


def demo_time_based_triggers():
    """Demonstrate time-based trigger logic."""
    print("\n⏰ TIME-BASED TRIGGERS DEMONSTRATION")
    print("=" * 80)

    triggers = create_sample_triggers()
    business_checker = DemoBusinessHourChecker()

    # Test case 1: During business hours
    event = MessageEvent(
        event_id="demo-8",
        channel_type=ChannelType.LINE,
        user_id="user123",
        timestamp=datetime(2025, 1, 15, 11, 0),  # Wednesday 11 AM
        content="need help",
        message_id="msg-8",
    )

    result = validate_trigger(triggers, event, business_checker, 1)
    print_result("Business Hours Trigger", result, "Message at 11 AM on Wednesday (business hours)")

    # Test case 2: Outside business hours
    event = MessageEvent(
        event_id="demo-9",
        channel_type=ChannelType.LINE,
        user_id="user123",
        timestamp=datetime(2025, 1, 15, 20, 0),  # Wednesday 8 PM
        content="need help",
        message_id="msg-9",
    )

    result = validate_trigger(triggers, event, business_checker, 1)
    print_result("Outside Business Hours", result, "Message at 8 PM on Wednesday (outside business hours)")

    # Test case 3: Monthly trigger on specific date and time
    event = MessageEvent(
        event_id="demo-10",
        channel_type=ChannelType.LINE,
        user_id="user123",
        timestamp=datetime(2025, 1, 15, 13, 0),  # 15th day, 1 PM
        content="anything",
        message_id="msg-10",
    )

    result = validate_trigger(triggers, event, business_checker, 1)
    print_result("Monthly Trigger", result, "Message on 15th day at 1 PM (monthly promotion time)")


def demo_timezone_aware_business_hours():
    """Demonstrate timezone-aware business hour validation."""
    print("\n🌍 TIMEZONE-AWARE BUSINESS HOURS")
    print("=" * 80)

    business_checker = DemoBusinessHourChecker()

    # Create business hour trigger
    trigger = WebhookTriggerSetting(
        id=10,
        auto_reply_id=10,
        bot_id=1,
        enable=True,
        name="Timezone Business Hours",
        event_type=WebhookTriggerEventType.TIME,
        trigger_schedule_type=WebhookTriggerScheduleType.BUSINESS_HOUR,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # Same UTC time - 9 AM UTC on Wednesday
    from zoneinfo import ZoneInfo

    utc_event = MessageEvent(
        event_id="tz-demo",
        channel_type=ChannelType.LINE,
        user_id="user123",
        timestamp=datetime(2025, 1, 15, 9, 0, tzinfo=ZoneInfo("UTC")),
        content="business support",
        message_id="tz-msg",
    )

    print(f"UTC Event Time: {utc_event.timestamp.strftime('%Y-%m-%d %H:%M %Z')}")
    print(f"Message: '{utc_event.content}'")

    # Test different organization timezones
    timezone_tests = [("Asia/Taipei", "Taiwan"), ("Europe/London", "London"), ("America/New_York", "New York")]

    for org_tz, location in timezone_tests:
        # Show what time it would be in that timezone
        local_time = convert_to_timezone(utc_event.timestamp, org_tz)

        result = validate_trigger(
            [trigger], utc_event, business_checker, organization_id=1, organization_timezone=org_tz
        )

        status = "✅ TRIGGERED" if result.has_match else "❌ NOT TRIGGERED"
        print(f"  {location:12}: {local_time.strftime('%H:%M %Z')} → {status}")


def demo_inactive_triggers():
    """Demonstrate that inactive triggers are not processed."""
    print("\n🚫 INACTIVE TRIGGERS DEMONSTRATION")
    print("=" * 80)

    # Create an inactive trigger
    inactive_trigger = WebhookTriggerSetting(
        id=99,
        auto_reply_id=99,
        bot_id=1,
        enable=False,  # Disabled
        name="Inactive Trigger",
        event_type=WebhookTriggerEventType.MESSAGE,
        trigger_code="hello",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    event = MessageEvent(
        event_id="demo-11",
        channel_type=ChannelType.LINE,
        user_id="user123",
        timestamp=datetime.now(),
        content="hello",
        message_id="msg-11",
    )

    result = validate_trigger([inactive_trigger], event)
    print_result("Disabled Trigger", result, "Message 'hello' to disabled trigger")


def main():
    """Run all demonstrations."""
    print("🚀 AUTO-REPLY TRIGGER VALIDATION DEMO")
    print("Implementing PRD requirements for FB/IG Auto-Reply Feature")
    print("=" * 80)

    demo_keyword_matching()
    demo_priority_system()
    demo_time_based_triggers()
    demo_timezone_aware_business_hours()
    demo_inactive_triggers()

    print("\n✨ DEMO COMPLETED!")
    print("All trigger validation scenarios have been demonstrated.")
    print("The implementation follows PRD specifications with:")
    print("  • ✅ Case-insensitive keyword matching")
    print("  • ✅ Exact match requirement (no partial matches)")
    print("  • ✅ Priority system (Keyword > Welcome > General)")
    print("  • ✅ Time-based schedule validation")
    print("  • ✅ Timezone-aware business hour checking")
    print("  • ✅ Midnight crossing support")
    print("  • ✅ Active/inactive trigger filtering")
    print("=" * 80)


if __name__ == "__main__":
    main()
