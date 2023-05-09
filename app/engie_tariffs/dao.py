"""Data access object for indexing settings"""
from enum import Enum, auto
from dataclasses import dataclass
from datetime import datetime


class IndexingSettingOrigin(Enum):
    """The possible origins for an indexing setting"""

    ORIGINAL = auto()
    DERIVED = auto()


class IndexingSettingTimeframe(Enum):
    """The timeframe for an indexing setting"""

    DAILY = auto()
    HOURLY = auto()
    MONTHLY = auto()


@dataclass
class IndexingSetting:
    """Class that represents an indexing setting"""

    name: str  # The name of the index
    value: float  # The actual value of the index setting
    timeframe: IndexingSettingTimeframe  # The timeframe that is represented by the value: hourly/daily/monthly
    date: datetime  # The time of the index, combined with timeframe
    source: str  # The source of the data, either directly or whether is was derived from those values: Engie/EEX/...
    origin: IndexingSettingOrigin  # Whether the data is "original" or "derived", i.e. calculated from multiple (original) values


DAILY = IndexingSettingTimeframe.DAILY
HOURLY = IndexingSettingTimeframe.HOURLY
MONTHLY = IndexingSettingTimeframe.MONTHLY
ORIGINAL = IndexingSettingOrigin.ORIGINAL
DERIVED = IndexingSettingOrigin.DERIVED
