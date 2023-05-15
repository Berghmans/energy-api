"""Module for the end price method"""
from dataclasses import dataclass
import logging
import json

from api.method import ApiMethod
from api.methods.indexing_setting import IndexingSettingApiMethod
from api.result import ApiResult


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class EndPriceApiMethod(ApiMethod):
    """Method for /endprice"""

    index: IndexingSettingApiMethod
    intercept: float
    slope: float
    taxes: float

    def process(self) -> ApiResult:
        index_result = self.index.process()

        if index_result.status_code == 200:
            # Using linear regression Y = a + bX
            # a: the intercept, which the base cost of the unit
            # b: the slope of the line, which is the factor to be multiplied with the indexing setting value
            end_price = self.intercept + self.slope * index_result.body["value"]
            end_price *= self.taxes
            return ApiResult(200, {"end_price": end_price})
        return ApiResult(400)

    @classmethod
    def from_body(cls, db_table, body: dict):
        """Create the object from a HTTP request body"""
        logger.info(f"Creating the {cls.__name__} method for body {json.dumps(body)}")
        if any(key not in body for key in ["INTERCEPT", "SLOPE", "TAXES"]):
            return None
        index = IndexingSettingApiMethod.from_body(db_table=db_table, body=body)
        intercept = body["INTERCEPT"]
        slope = body["SLOPE"]
        taxes = body["TAXES"]
        return cls(
            index=index,
            intercept=intercept,
            slope=slope,
            taxes=taxes,
        )
