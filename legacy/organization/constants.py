from enum import Enum


class OrganizationReleaseTier(str, Enum):
    FIRST_TIER = "1st_tier"
    SECOND_TIER = "2nd_tier"
    THIRD_TIER = "3rd_tier"


class OrganizationServiceLevel(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"
