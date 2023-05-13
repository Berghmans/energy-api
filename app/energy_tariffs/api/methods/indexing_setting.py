"""Module for the indexing setting method"""
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
import logging
import json

from api.method import ApiMethod
from api.result import ApiResult
from dao import IndexingSetting, IndexingSettingTimeframe


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class IndexingSettingApiMethod(ApiMethod):
    """Method for /indexingsetting"""

    db_table: object  # Unfortunately not easy typing for boto3
    index_name: str
    index_source: str
    index_year: int
    index_month: int

    def process(self) -> ApiResult:
        indexing_setting = IndexingSetting.load(
            self.db_table, self.index_source, self.index_name, IndexingSettingTimeframe.MONTHLY, datetime(self.index_year, self.index_month, 1)
        )

        if indexing_setting is not None:
            return ApiResult(200, asdict(indexing_setting))
        return ApiResult(400)

    @classmethod
    def from_body(cls, db_table, body: dict):
        """Create the object from a HTTP request body"""
        logger.info(f"Creating the {cls.__name__} method for body {json.dumps(body)}")
        if "INDEX" not in body or "SOURCE" not in body:
            return None
        last_month = date.today().replace(day=1) - timedelta(days=1)
        req_index = body["INDEX"]
        req_source = body["SOURCE"]
        req_year = body.get("YEAR", last_month.year)
        req_month = body.get("MONTH", last_month.month)
        return cls(db_table=db_table, index_name=req_index, index_source=req_source, index_year=req_year, index_month=req_month)
