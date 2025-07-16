"""Auto-reply domain services."""
from datetime import datetime

from internal.domain.auto_reply.auto_reply import AutoReply, AutoReplyEventType
from internal.domain.auto_reply.events import IncomingEvent


class TriggerValidationService:
    """Service for validating and finding the best auto-reply trigger."""

    def _is_keyword_matched(self, text: str, keywords: list[str]) -> bool:
        """Checks if the text matches any of the keywords.

        Matching is case-insensitive, space-trimmed, and exact.
        """
        normalized_text = text.strip().lower()
        normalized_keywords = [kw.strip().lower() for kw in keywords]
        return normalized_text in normalized_keywords

    def _is_schedule_active(self, rule: AutoReply, now: datetime) -> bool:
        """Checks if the rule is active based on its schedule."""
        # TODO: This logic will be implemented in a future step.
        # For now, we assume all rules are active.
        return True

    def find_best_trigger(
        self,
        event: IncomingEvent,
        rules: list[AutoReply],
        now: datetime,
    ) -> AutoReply | None:
        """Finds the highest-priority, matching auto-reply rule.

        Args:
            event: The incoming event to be processed.
            rules: A list of active auto-reply rules to check against.
            now: The current time for schedule validation.

        Returns:
            The highest-priority matching rule, or None if no rule matches.
        """
        candidate_rules: dict[AutoReplyEventType, list[AutoReply]] = {
            AutoReplyEventType.IG_STORY_KEYWORD: [],
            AutoReplyEventType.IG_STORY_GENERAL: [],
            AutoReplyEventType.KEYWORD: [],
            AutoReplyEventType.TIME: [],
        }

        for rule in rules:
            if rule.event_type in candidate_rules:
                candidate_rules[rule.event_type].append(rule)

        # Priority 1: IG Story Keyword
        if event.context and event.context.ig_story and event.text:
            ig_story_id = event.context.ig_story.id
            for rule in candidate_rules[AutoReplyEventType.IG_STORY_KEYWORD]:
                if (
                    rule.ig_story_ids
                    and ig_story_id in rule.ig_story_ids
                    and rule.keywords
                    and self._is_keyword_matched(event.text, rule.keywords)
                    and self._is_schedule_active(rule, now)
                ):
                    return rule

        # Priority 2: IG Story General
        if event.context and event.context.ig_story:
            ig_story_id = event.context.ig_story.id
            for rule in candidate_rules[AutoReplyEventType.IG_STORY_GENERAL]:
                if rule.ig_story_ids and ig_story_id in rule.ig_story_ids and self._is_schedule_active(rule, now):
                    return rule

        # Priority 3: General Keyword
        if event.text:
            for rule in candidate_rules[AutoReplyEventType.KEYWORD]:
                if rule.keywords and self._is_keyword_matched(event.text, rule.keywords) and self._is_schedule_active(rule, now):
                    return rule

        # Priority 4: General Time-based
        for rule in candidate_rules[AutoReplyEventType.TIME]:
            if self._is_schedule_active(rule, now):
                return rule

        return None 