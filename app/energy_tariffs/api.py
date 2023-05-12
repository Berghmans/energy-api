"""Module that represents the API functionality"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
import json
import logging

from dao import IndexingSetting, IndexingSettingTimeframe


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ApiMethod:
    """Class for processing a method"""

    def process(self) -> ApiResult:
        """Process the method"""
        raise NotImplementedError("This method is not implemented")


@dataclass
class ApiResult:
    """The result of the API method"""

    status_code: int
    body: dict = field(default_factory=lambda: {})

    def to_api(self) -> dict:
        """Transform to output for the API"""
        return {"statusCode": 200, "body": json.dumps(self.body, default=str)}


@dataclass
class Api:
    """Class for answering incoming API GW methods"""

    base_path: str
    db_table: object  # Unfortunately not easy typing for boto3

    def parse(self, event: dict) -> ApiMethod:
        """Parse the incoming event through lambda from API Gateway"""

        def has_value(data: dict, key: str, value: str):
            """Check if the data has the key and given value"""
            return key in data and data[key] == value

        if has_value(event, "path", f"{self.base_path}/indexingsetting") and has_value(event, "httpMethod", "POST"):
            return IndexingSettingApiMethod.from_body(self.db_table, json.loads(event.get("body", r"{}")))
        if has_value(event, "path", f"{self.base_path}/endprice") and has_value(event, "httpMethod", "POST"):
            return EndPriceApiMethod.from_body(self.db_table, json.loads(event.get("body", r"{}")))

        logger.warning("Unable to parse event")
        return None


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


@dataclass
class EndPriceApiMethod(ApiMethod):
    """Method for /endprice"""

    db_table: object  # Unfortunately not easy typing for boto3
    index_name: str
    index_source: str
    index_year: int
    index_month: int
    intercept: float
    slope: float
    taxes: float

    def process(self) -> ApiResult:
        indexing_setting = IndexingSetting.load(
            self.db_table, self.index_source, self.index_name, IndexingSettingTimeframe.MONTHLY, datetime(self.index_year, self.index_month, 1)
        )

        if indexing_setting is not None:
            # Using linear regression Y = a + bX
            # a: the intercept, which the base cost of the unit
            # b: the slope of the line, which is the factor to be multiplied with the indexing setting value
            end_price = self.intercept + self.slope * indexing_setting.value
            end_price *= self.taxes
            return ApiResult(200, {"end_price": end_price})
        return ApiResult(400)

    @classmethod
    def from_body(cls, db_table, body: dict):
        """Create the object from a HTTP request body"""
        logger.info(f"Creating the {cls.__name__} method for body {json.dumps(body)}")
        if any(key not in body for key in ["INDEX", "SOURCE", "INTERCEPT", "SLOPE", "TAXES"]):
            return None
        last_month = date.today().replace(day=1) - timedelta(days=1)
        req_index = body["INDEX"]
        req_source = body["SOURCE"]
        req_year = body.get("YEAR", last_month.year)
        req_month = body.get("MONTH", last_month.month)
        intercept = body["INTERCEPT"]
        slope = body["SLOPE"]
        taxes = body["TAXES"]
        return cls(
            db_table=db_table,
            index_name=req_index,
            index_source=req_source,
            index_year=req_year,
            index_month=req_month,
            intercept=intercept,
            slope=slope,
            taxes=taxes,
        )
