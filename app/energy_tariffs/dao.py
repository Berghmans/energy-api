"""Data access object for indexing settings"""
from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, asdict
from datetime import datetime

from boto3.dynamodb.conditions import Key


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

    def save(self, db_table):
        """Save the object to the dynamodb database"""
        db_table.put_item(Item=self._to_ddb_json())

    @staticmethod
    def save_list(db_table, objects: list[IndexingSetting]):
        with db_table.batch_writer() as batch:
            for object in objects:
                batch.put_item(Item=object._to_ddb_json())

    def _to_ddb_json(self):
        """Convert the current object to a JSON for storing in dynamodb"""
        date_time_str = self.date.strftime("%Y-%m-%d %H:%M:%S")
        return {
            **asdict(self),
            "primary": f"{self.source}#{self.name}",
            "secondary": f"{self.timeframe.name}#{date_time_str}",
            "date": date_time_str,
            "timeframe": self.timeframe.name,
            "origin": self.origin.name,
            "value": str(self.value),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    @classmethod
    def _from_ddb_json(cls, data):
        """Parse the JSON from dynamodb and create the object"""
        return cls(
            name=data.get("name"),
            value=float(data.get("value")),
            timeframe=IndexingSettingTimeframe[data.get("timeframe")],
            date=datetime.strptime(data.get("date"), "%Y-%m-%d %H:%M:%S"),
            source=data.get("source"),
            origin=IndexingSettingOrigin[data.get("origin")],
        )

    @classmethod
    def load(cls, db_table, source: str, name: str, timeframe: IndexingSettingTimeframe, date_time: datetime):
        """Retrieve a single object from the database"""
        date_time_str = date_time.strftime("%Y-%m-%d %H:%M:%S")
        response = db_table.get_item(Key={"primary": f"{source}#{name}", "secondary": f"{timeframe.name}#{date_time_str}"})

        if "Item" in response:
            return cls._from_ddb_json(response["Item"])

    @staticmethod
    def query(db_table, source: str, name: str, timeframe: IndexingSettingTimeframe = None, date_time_prefix: str = None) -> list[IndexingSetting]:
        """Query all objects in the database from the same campaign"""
        key_condition = Key("primary").eq(f"{source}#{name}")
        if timeframe is not None and date_time_prefix is not None:
            key_condition = key_condition & Key("secondary").begins_with(f"{timeframe.name}#{date_time_prefix}")
        elif timeframe is not None and date_time_prefix is None:
            key_condition = key_condition & Key("secondary").begins_with(f"{timeframe.name}")
        elif timeframe is None and date_time_prefix is not None:
            raise ValueError("Cannot query for date time prefix without timeframe")

        response = db_table.query(
            Select="ALL_ATTRIBUTES",
            KeyConditionExpression=key_condition,
        )
        return [IndexingSetting._from_ddb_json(object) for object in response.get("Items", [])]


DAILY = IndexingSettingTimeframe.DAILY
HOURLY = IndexingSettingTimeframe.HOURLY
MONTHLY = IndexingSettingTimeframe.MONTHLY
ORIGINAL = IndexingSettingOrigin.ORIGINAL
DERIVED = IndexingSettingOrigin.DERIVED
