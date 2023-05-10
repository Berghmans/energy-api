from datetime import date, timedelta
from dataclasses import asdict
from functools import cache
import json

from engie import EngieIndexingSetting, GAS_URL, ENERGY_URL


@cache
def get_index_values() -> list[EngieIndexingSetting]:
    """Get the list of values"""
    return EngieIndexingSetting.from_url(GAS_URL) + EngieIndexingSetting.from_url(ENERGY_URL)


def get_indexing_setting(index_name: str, year: int, month: int) -> EngieIndexingSetting:
    """Get the indexing setting"""
    index_values = get_index_values()
    result = [
        index_value
        for index_value in index_values
        if index_value.date.year == year and index_value.date.month == month and index_value.name == index_name
    ]
    if len(result) == 1:
        return result[0]
    raise ValueError("None or more than one found")


def get_end_price(index_name: str, year: int, month: int, slope: float, intercept: float, taxes: float) -> float:
    """Calculate the end price"""
    # Using linear regression Y = a + bX
    # a: the intercept, which the base cost of the unit
    # b: the slope of the line, which is the factor to be multiplied with the indexing setting value
    end_price = intercept + slope * get_indexing_setting(index_name, year, month).value
    return end_price * taxes


def handler(event, _context):
    """The handler"""
    print(json.dumps(event))
    last_month = date.today().replace(day=1) - timedelta(days=1)
    question_type = event["TYPE"]

    if question_type == "index":
        req_index = event["INDEX"]
        req_year = event.get("YEAR", last_month.year)
        req_month = event.get("MONTH", last_month.month)

        indexing_setting = get_indexing_setting(req_index, req_year, req_month)
        return {"statusCode": 200, "body": json.dumps(asdict(indexing_setting), default=str)}
    elif question_type == "end_price":
        req_index = event["INDEX"]
        req_year = event.get("YEAR", last_month.year)
        req_month = event.get("MONTH", last_month.month)
        intercept = event["INTERCEPT"]
        slope = event["SLOPE"]
        taxes = event["TAXES"]
        end_price = get_end_price(req_index, req_year, req_month, slope, intercept, taxes)
        return {"statusCode": 200, "body": json.dumps({"end_price": end_price}, default=str)}
    return {"statusCode": 400}
