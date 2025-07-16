"""Organization domain models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class LanguageCode(StrEnum):
    """Language code enumeration."""

    ZH_HANT = "zh-hant"
    ZH_HANS = "zh-hans"
    EN = "en"


class Organization(BaseModel):
    """Organization domain model.

    Represents an organization entity in the system.
    It contains the core business information and settings for an organization.
    """

    id: int
    name: str
    uuid: str
    plan_id: str | None = None
    enable_two_factor: bool
    timezone: str
    language_code: LanguageCode
    enable: bool
    created_at: datetime
    updated_at: datetime
    expired_at: datetime | None = None

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
