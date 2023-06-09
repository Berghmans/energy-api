"""Module for the indexing setting method"""
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
import json

from pytz import utc, timezone
from pytz.exceptions import UnknownTimeZoneError

from api.method import ApiMethod
from api.result import ApiResult, Success, BadRequest
from dao.indexingsetting import IndexingSetting, IndexingSettingTimeframe, IndexingSettingOrigin


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class IndexingSettingApiMethod(ApiMethod):
    """Method for /indexingsetting"""

    db_table: object  # Unfortunately not easy typing for boto3
    name: str
    source: str
    date: datetime
    timeframe: IndexingSettingTimeframe
    origin: IndexingSettingOrigin

    def __post_init__(self):
        """Post initialization"""
        if self.date.tzinfo is None:
            # If we got a naive date, we assume it is UTC based
            self.date = self.date.replace(tzinfo=utc)

    def process(self) -> ApiResult:
        indexing_setting = IndexingSetting.load(
            db_table=self.db_table,
            source=self.source,
            name=self.name,
            timeframe=self.timeframe,
            date_time=self.date,
            origin=self.origin,
        )

        if indexing_setting is not None:

            def translate_index(index: IndexingSetting) -> dict:
                """Translate the index to output"""
                # Translate enums to their string name
                return {**asdict(index), "timeframe": index.timeframe.name, "origin": index.origin.name}

            return Success(translate_index(indexing_setting))
        return BadRequest("No result found for requested index")

    @staticmethod
    def parse_date(timeframe: IndexingSettingTimeframe, date_str: str, tz: str) -> datetime:
        """Parse the date from the body"""
        tz_date = timezone(tz)
        if date_str is None:
            requested = datetime.now(tz_date)
        else:
            try:
                requested = tz_date.localize(datetime.strptime(date_str, "%Y-%m-%d %H:%M"))
            except ValueError:
                raise ValueError(f"Could not parse date {date_str}")

        if timeframe == IndexingSettingTimeframe.MONTHLY:
            # The indices are calculated for last month so for current month we return last months value
            last_month = requested.replace(day=1) - timedelta(days=1)
            return last_month.replace(day=1, hour=0, minute=0, second=0)

        if timeframe == IndexingSettingTimeframe.HOURLY:
            return requested.replace(minute=0, second=0)

        raise ValueError("Requested timeframe is not supported yet")

    @classmethod
    def from_body(cls, db_table, body: dict):
        """Create the object from a HTTP request body"""
        logger.info(f"Creating the {cls.__name__} method for body {json.dumps(body)}")
        if "INDEX" not in body or "SOURCE" not in body:
            return None
        req_index = body["INDEX"]
        req_source = body["SOURCE"]

        try:
            req_timeframe = IndexingSettingTimeframe[body.get("TIMEFRAME", "MONTHLY")]
            req_origin = IndexingSettingOrigin[body.get("ORIGIN", "ORIGINAL")]
        except KeyError as exc:
            # Timeframe or Origin are not valid enum values
            logger.warning(f"Failed to parse the body {exc.args[0]}")
            return None

        try:
            req_tz = body.get("TZ", "UTC")
            req_date = IndexingSettingApiMethod.parse_date(req_timeframe, body.get("DATE", None), req_tz)
        except ValueError as exc:
            logger.warning(f"Failed to parse the body: {exc.args[0]}")
            return None
        except UnknownTimeZoneError:
            logger.warning("Failed to parse the body: Unknown timezone")
            return None
        return cls(
            db_table=db_table,
            name=req_index,
            source=req_source,
            date=req_date,
            timeframe=req_timeframe,
            origin=req_origin,
        )
