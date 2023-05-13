"""Module for the end price method"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import logging
import json

from api.method import ApiMethod
from api.result import ApiResult
from dao import IndexingSetting, IndexingSettingTimeframe


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
