from enum import Enum


class EDayCount(Enum):
    DAYS_30 = "30 days"
    DAYS_7 = "7 days"


class EJobType(Enum):
    FULL_SCAN = "full_scan"
    MONITOR = "monitor"
