"""Data access object for indexing settings"""
from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import json

from pytz import utc
from boto3.dynamodb.conditions import Key

from dao.dynamodb import DaoDynamoDB


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
class IndexingSetting(DaoDynamoDB):
    """Class that represents an indexing setting"""

    name: str  # The name of the index
    value: float  # The actual value of the index setting
    timeframe: IndexingSettingTimeframe  # The timeframe that is represented by the value: hourly/daily/monthly
    date: datetime  # The time of the index, combined with timeframe
    source: str  # The source of the data, either directly or whether is was derived from those values: Engie/EEX/...
    origin: IndexingSettingOrigin  # Whether the data is "original" or "derived", i.e. calculated from multiple (original) values

    def __post_init__(self):
        """Post initialization"""
        assert self.date.tzinfo is not None and self.date is not None

    def save(self, db_table):
        """Save the object to the dynamodb database"""
        super().save(db_table)
        self.doc().save(db_table)

    @staticmethod
    def save_list(db_table, objects: list[IndexingSetting]):
        docs = {obj.doc() for obj in objects}
        DaoDynamoDB.save_list(db_table=db_table, objects=objects + list(docs))

    def _to_ddb_json(self):
        """Convert the current object to a JSON for storing in dynamodb"""
        date_time_str = self.date.astimezone(utc).strftime("%Y-%m-%d %H:%M:%S")
        secondary = int(self.date.astimezone(utc).timestamp())
        return {
            **asdict(self),
            "primary": f"{self.source}#{self.origin.name}#{self.timeframe.name}#{self.name}",
            "secondary": secondary,
            "date": date_time_str,
            "timeframe": self.timeframe.name,
            "origin": self.origin.name,
            "value": str(self.value),
            "last_updated": datetime.now(utc).strftime("%Y-%m-%d %H:%M:%S"),
        }

    @classmethod
    def _from_ddb_json(cls, data):
        """Parse the JSON from dynamodb and create the object"""
        return cls(
            name=data.get("name"),
            value=float(data.get("value")),
            timeframe=IndexingSettingTimeframe[data.get("timeframe")],
            date=datetime.strptime(data.get("date"), "%Y-%m-%d %H:%M:%S").replace(tzinfo=utc),
            source=data.get("source"),
            origin=IndexingSettingOrigin[data.get("origin")],
        )

    @classmethod
    def load(
        cls,
        db_table,
        source: str,
        name: str,
        timeframe: IndexingSettingTimeframe,
        date_time: datetime,
        origin: IndexingSettingOrigin = IndexingSettingOrigin.ORIGINAL,
    ):
        """Retrieve a single object from the database"""
        assert date_time.tzinfo is not None and date_time is not None
        secondary = int(date_time.astimezone(utc).timestamp())
        return IndexingSetting.load_key(db_table=db_table, primary=f"{source}#{origin.name}#{timeframe.name}#{name}", secondary=secondary)

    @staticmethod
    def query(
        db_table,
        source: str,
        name: str,
        origin: IndexingSettingOrigin = IndexingSettingOrigin.ORIGINAL,
        timeframe: IndexingSettingTimeframe = IndexingSettingTimeframe.MONTHLY,
        start: datetime = None,
        end: datetime = None,
    ) -> list[IndexingSetting]:
        """Query all objects in the database from the same campaign"""
        key_condition = Key("primary").eq(f"{source}#{origin.name}#{timeframe.name}#{name}")
        if start is not None and end is None:
            key_condition = key_condition & Key("secondary").gte(int(start.astimezone(utc).timestamp()))
        if end is not None and start is None:
            key_condition = key_condition & Key("secondary").lt(int(end.astimezone(utc).timestamp()))
        if start is not None and end is not None:
            key_condition = key_condition & Key("secondary").between(int(start.astimezone(utc).timestamp()), int(end.astimezone(utc).timestamp()))

        return [IndexingSetting._from_ddb_json(object) for object in DaoDynamoDB.query_condition(db_table=db_table, condition=key_condition)]

    def doc(self) -> IndexingSettingDocumentation:
        """Generate the documentation"""
        return IndexingSettingDocumentation(name=self.name, timeframe=self.timeframe, source=self.source, origin=self.origin)


@dataclass(frozen=True, eq=True)
class IndexingSettingDocumentation(DaoDynamoDB):
    """A class representing documentation about the indexing setting in the database"""

    name: str
    timeframe: IndexingSettingTimeframe
    source: str
    origin: IndexingSettingOrigin

    def _to_ddb_json(self):
        """Convert the current object to a JSON for storing in dynamodb"""
        return {
            **asdict(self),
            "timeframe": self.timeframe.name,
            "origin": self.origin.name,
            "primary": "indexingsettingdoc",
            "secondary": self._ddb_hash(),
            "last_updated": datetime.now(utc).strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _ddb_hash(self):
        """Get a hash for dynamodb"""
        data = {
            **asdict(self),
            "timeframe": self.timeframe.name,
            "origin": self.origin.name,
        }
        secondary_int = int(hashlib.sha1(json.dumps(data, sort_keys=True).encode("UTF-8")).hexdigest()[-16:], 16)
        return secondary_int

    @classmethod
    def _from_ddb_json(cls, data):
        """Parse the JSON from dynamodb and create the object"""
        return cls(
            name=data.get("name"),
            timeframe=IndexingSettingTimeframe[data.get("timeframe")],
            source=data.get("source"),
            origin=IndexingSettingOrigin[data.get("origin")],
        )

    @staticmethod
    def query(
        db_table,
    ) -> list[IndexingSettingDocumentation]:
        """Query all objects in the database from the same campaign"""
        key_condition = Key("primary").eq("indexingsettingdoc")
        return [IndexingSettingDocumentation._from_ddb_json(object) for object in DaoDynamoDB.query_condition(db_table=db_table, condition=key_condition)]
