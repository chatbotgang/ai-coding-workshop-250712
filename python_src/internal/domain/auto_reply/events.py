"""Incoming event models for auto-reply trigger validation."""

from pydantic import BaseModel


class IGStoryContext(BaseModel):
    """Context for an Instagram story interaction."""

    id: str


class EventContext(BaseModel):
    """Contextual information for an incoming event."""

    ig_story: IGStoryContext | None = None


class IncomingEvent(BaseModel):
    """Represents an incoming event to be processed for auto-reply."""

    text: str | None = None
    context: EventContext | None = None 