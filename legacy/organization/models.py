import uuid

import pytz
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


class Plan(models.Model):
    name = models.CharField(max_length=64, unique=True)
    is_custom = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"


class Organization(models.Model):
    NAMESPACE_REGEX = "[0-9a-z_]{1,5}"  # must same as url patterns

    name = models.CharField(max_length=255, unique=True)
    uuid = models.CharField(max_length=36, unique=True, default=uuid.uuid4)
    url_namespace = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=f"^{NAMESPACE_REGEX}$",
                message="namespace field can only contain numbers or "
                "lowercase letters or the bottom line",
            )
        ],
    )  # deprecated
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    enable_two_factor = models.BooleanField(default=True)
    timezone = models.CharField(
        max_length=63,
        blank=True,
        null=True,
        default="Asia/Taipei",
        choices=[(tz, tz) for tz in pytz.common_timezones],
        help_text="Timezone for the organization, e.g., Asia/Taipei",
    )
    language_code = models.CharField(
        max_length=7,
        default="zh-hant",
        choices=settings.LANGUAGES,
        help_text="Language code for the organization, e.g., zh-hant",
    )
    expired_at = models.DateTimeField(null=True, blank=True)
    enable = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.pk}:{self.name}"

    @property
    def is_new_pricing_plan(self) -> bool:
        return self.plan_id is not None


class BusinessHour(models.Model):
    WEEKDAY_CHOICES = (
        (1, "Monday"),
        (2, "Tuesday"),
        (3, "Wednesday"),
        (4, "Thursday"),
        (5, "Friday"),
        (6, "Saturday"),
        (7, "Sunday"),
    )

    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
