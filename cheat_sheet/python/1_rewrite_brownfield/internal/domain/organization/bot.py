"""Bot domain models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class BotType(StrEnum):
    """Bot type enumeration."""

    LINE = "LINE"
    FACEBOOK = "FB"
    INSTAGRAM = "IG"


class Bot(BaseModel):
    """Bot domain model.

    Represents a channel entity associated with an organization.
    It contains the configuration and credentials for integration across multiple platforms.
    """

    id: int
    organization_id: int
    name: str
    type: BotType
    channel_id: str
    channel_secret: str
    access_token: str
    token_expired_time: datetime
    created_at: datetime
    updated_at: datetime
    expired_at: datetime | None = None
    enable: bool

    def is_active(self) -> bool:
        """Check if the bot is enabled and not expired."""
        if not self.enable:
            return False
        if self.expired_at is not None and datetime.now() > self.expired_at:
            return False
        return True

    def is_token_expired(self) -> bool:
        """Check if the bot's access token has expired."""
        return self.token_expired_time < datetime.now()

    def is_token_valid(self) -> bool:
        """Check if the bot has a valid access token."""
        return self.access_token != "" and not self.is_token_expired()

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
